import pandas as pd
import io
import subprocess
import re
import logging
import sys
import csv
import json
import numpy as np
from io import StringIO
from zipfile import ZipFile


pd.options.display.max_columns = 400
pd.options.display.max_rows = 200

missingVisits_all = {}


def writePanelComponentTemplate(panel, component,header, filepath):
    panel["Result Separator Column"]=""
    df_temp = panel.merge(component, left_on='Assessment Panel ID', right_on='ASSESSMENT_PANEL_ACCESSION')
    df_temp["Subject ID"]=df_temp["User Defined ID"]
    df_temp["User Defined ID"]=df_temp.index+0
    df_temp.drop(columns=["ASSESSMENT_PANEL_ACCESSION","component_group_id","WORKSPACE_ID"],axis=1,inplace=True, errors='ignore')
    colNames = list(map(lambda s: s.replace("_x","").replace("_y",""),df_temp.columns.to_list()))

    #Need separator as | as it is not in string and allows correct output of data.
    header.to_csv(filepath, sep="|",index=False, encoding='utf-8')


    df_temp.to_csv(filepath, sep="\t", mode='a',header=False, index=False)


def processStudyFile(table_list,directory,dictionary,planned_visits,study_files,assessment_panel_template,study_id,assessment_components_template,table_metadata,workspace_id):    
    for table_set in table_list:
        filename = table_metadata.loc[table_metadata.table_name.isin(table_set["tables"])]["table_file"].values[0]
        filepath = directory+"StudyFiles/"+filename

        # datafile = readAndModifyStudyFile(filepath,table_set["tables"],dictionary,planned_visits)
        datafile = readAndModifyStudyFile(filepath,table_set,dictionary,planned_visits)
        [assessment_panel_template,panel_id] = getAssessmentPanelID([filename],study_files,assessment_panel_template,study_id,table_set["assessment_type"])
        panel=getAssessmentPanelByID(panel_id,assessment_panel_template)
        
        assessment_components_template=datafileToComponents(datafile,dictionary,table_set["tables"],panel_id,assessment_components_template,workspace_id)


    return [assessment_panel_template,assessment_components_template]

def readFileFromZip(dir,zip,file):
    with ZipFile(f"{dir}{zip}.zip") as myzip:
        with myzip.open(f"{zip}/Tab/{file}") as myfile:
            myfile_contents = pd.read_csv(io.BytesIO(myfile.read()), encoding='utf8', sep="\t")
            return myfile_contents

def getColumnNumber(df,col_name):  #legacy?
    try:
        return df.columns.get_loc(col_name)
    except:
        return False

def get_studyfile_line_count(directory):
    result = pd.read_csv(StringIO(subprocess.getoutput(f"wc --lines {directory}/*.txt")),encoding='utf8',header=None,names=["wc result"])

    df = result["wc result"].str.split("\s+", expand=True)
    df.columns=["blank","line_count","FILE_NAME"]
    df["FILE_NAME"].replace(to_replace=f'{directory}/',value="",regex=True, inplace=True)
    df.drop(columns=["blank"], inplace=True)

    return df

def addVisitAccessionFromName(planned_visits, table, visit_col,dictionary,file_table,default_visit):
    global missingVisits_all    
    
    table_column = getColumnName(dictionary, file_table,visit_col)

    #dict_visits is a dictionary of planned visits. Keys are names, values are IDs
    dict_visits=dict(zip(planned_visits["NAME"],planned_visits["PLANNED_VISIT_ACCESSION"]))
    
    if(table_column is None):
        logging.warn("No visit column in table, using default: {}")
        if(default_visit is not None):
            table["PLANNED_VISIT_ID"]=dict_visits.get(default_visit,"")
            table_visit = pd.DataFrame(data={'plannedVisit':['']})
            return table_visit
        else:
            logging.error("No default visit has been defined")
            raise ValueError(f"No default visit has been defiled for {file_table}")

    table_visits = table.groupby([table_column], as_index=False).agg('nunique')

    table_visits.drop(table_visits.columns.difference([table_column]),1, inplace=True)
    table_visits["plannedVisit"] = ""
    #table_visits has values from visit column and empty "plannedVisit" column

    # if len(dictionary["tables"][file_table]["fields"][visit_col]["map_to_visit"])>0:
    #     visit_map_dict = json.loads(dictionary["tables"][file_table]["fields"][visit_col]["map_to_visit"])
    #     #create dictionary of visit_mappings to planned visit IDs
    #     dict_visits2 = dict(map(lambda x: (x[0],dict_visits[x[1]]), visit_map_dict.items()))
    # else:
    #     for index, row in table_visits.iterrows():
    #         for key in dict_visits.keys():
    #             # logging.info(key)
    #             if(key.startswith(row[table_column])):
    #                 table_visits.loc[index,"plannedVisit"]=dict_visits[key]
    #             elif(row[table_column].isnumeric() & ("Visit "+row[table_column] in key)):
    #                 table_visits.loc[index,"plannedVisit"]=dict_visits[key]
    #             elif(row[table_column].isnumeric() & ("Visit 0"+row[table_column] in key)):
    #                 table_visits.loc[index,"plannedVisit"]=dict_visits[key]
    #             elif(row[table_column][0:-1].isnumeric() & ("Visit "+row[table_column][0:-1] in key)):
    #                 table_visits.loc[index,"plannedVisit"]=dict_visits[key]
    #             elif(row[table_column][0:-2].isnumeric() & ("Visit "+row[table_column][0:-2] in key)):
    #                 table_visits.loc[index,"plannedVisit"]=dict_visits[key]
    #             elif(~row[table_column][0:1].isnumeric() & row[table_column][1:].isnumeric() & ("Visit "+row[table_column][1:] in key)):
    #                 table_visits.loc[index,"plannedVisit"]=dict_visits[key]
    #             # else:
    #                 # logging.warn(f"Cannot find planned visit for {key}")
    for index, row in table_visits.iterrows():
        for key in dict_visits.keys():
            # logging.info(key)
            if(key.startswith(row[table_column])):
                table_visits.loc[index,"plannedVisit"]=dict_visits[key]
            elif(row[table_column].isnumeric() & ("Visit "+row[table_column] in key)):
                table_visits.loc[index,"plannedVisit"]=dict_visits[key]
            elif(row[table_column].isnumeric() & ("Visit 0"+row[table_column] in key)):
                table_visits.loc[index,"plannedVisit"]=dict_visits[key]
            elif(row[table_column][0:-1].isnumeric() & ("Visit "+row[table_column][0:-1] in key)):
                table_visits.loc[index,"plannedVisit"]=dict_visits[key]
            elif(row[table_column][0:-2].isnumeric() & ("Visit "+row[table_column][0:-2] in key)):
                table_visits.loc[index,"plannedVisit"]=dict_visits[key]
            elif(~row[table_column][0:1].isnumeric() & row[table_column][1:].isnumeric() & ("Visit "+row[table_column][1:] in key)):
                table_visits.loc[index,"plannedVisit"]=dict_visits[key]
            # else:
                # logging.warn(f"Cannot find planned visit for {key}")

        dict_visits2=dict(zip(table_visits[table_column],table_visits["plannedVisit"]))
    if len(dictionary["tables"][file_table]["fields"][visit_col]["map_to_visit"])>0:
        visit_map_dict = json.loads(dictionary["tables"][file_table]["fields"][visit_col]["map_to_visit"])
        #create dictionary of visit_mappings to planned visit IDs
        dict_visits_mapped = dict(map(lambda x: (x[0],dict_visits[x[1]]), visit_map_dict.items()))
        dict_visits2.update(dict_visits_mapped)
  
    missingVisits = dict(filter(lambda visit: visit[1] == "", dict_visits2.items()))

    # logging.info("dict_visits2")
    # logging.info(dict_visits2)
    if(len(missingVisits)>0):
        logging.error("Missing Visits")
        logging.error(missingVisits)

        missingVisits_all[file_table]=list(missingVisits.keys())

        logging.info(missingVisits_all)


    table["PLANNED_VISIT_ID"]=table[table_column].apply(lambda v: dict_visits2[v])
    # return dict_visits

    return table_visits

def addVisitAccessionFromName_old(planned_visits, table, table_column):
    dict_visits=dict(zip(planned_visits["NAME"],planned_visits["PLANNED_VISIT_ACCESSION"]))

    table["PLANNED_VISIT_ID"]=table[table_column].apply(lambda v: dict_visits[[ key for key in dict_visits.keys() if key.startswith(v) ][0]])

def getStudyFileDescription(crf,study_files):
    return list(study_files[study_files["FILE_NAME"]==crf]["DESCRIPTION"])[0]

def readStudyFile(filepath, table, dictionary, sep="\t"):
    #Read in datafile
    datafile = pd.read_csv(filepath, sep=sep)

    #get the columns that utlize a key/value schema
    dictionary_columns = list(filter(lambda x: x in dictionary["tables"][table]["fields"] and "values" in dictionary["tables"][table]["fields"][x], datafile.columns.tolist()))

    #For columns that have dictionary values
    for column in dictionary_columns:
        # If float or int, need to convert to string. Also, if its a float, go to int first to remove any decimals (1.0 -> 1)
        if(datafile[column].dtypes == "float64" or datafile[column].dtypes == "int64"):
            datafile[column]=datafile[column].astype('Int64').astype(str)
        #For each key in the dictionary
        for key,value in dictionary["tables"][table]["fields"][column]["values"].items():
            subset = (datafile[column] == key)  #525
            
            #get the dictionary key value, and set it to the subset of the column that has the key as the cell value
            datafile.loc[subset, column]= value
            key_no_leading_zeros = re.sub(r"^0+(\d+)$",r"\1",key)

            subset = (datafile[column] == key_no_leading_zeros)  #525
            
            #get the dictionary key value, and set it to the subset of the column that has the key as the cell value
            datafile.loc[subset, column]= value

    #Rename columns with the description that is in the data dictionary
    datafile.rename(columns=lambda c: dictionary["tables"][table]["fields"][c]["description"] if c in dictionary["tables"][table]["fields"] else c, inplace=True)


    return datafile

def getAssessmentPanelByID(panel_ID,assessment_panel_df):
    return assessment_panel_df[assessment_panel_df["Assessment Panel ID"]==panel_ID]

def readTemplate(template):
    if(template == 'assessments'):
        assessment_template_header = pd.read_csv("templates/txt-templates/assessments.txt",nrows=2)
        # logging.info(assessment_template_header)
        assessments = pd.read_csv("templates/txt-templates/assessments.txt", sep='\t', skiprows=2,nrows=0)
        split_on_col = assessments.columns.get_loc("Result Separator Column")
        assessment_panel_template = assessments.iloc[: , :split_on_col-1]
        assessment_components_template = assessments.iloc[: , split_on_col+1:].copy()
        assessment_components_template.rename(columns={"Name Reported.1":"Name Reported"}, inplace=True)

        return assessment_panel_template,assessment_components_template,assessment_template_header

def createColumnMappingDict(dictionary,table_name):
    mappings={"PLANNED_VISIT_ID":"Planned Visit ID"}
    for mapping, col in dictionary["tables"][table_name]["mappings"].items():
        if(mapping == "[NA]" or mapping == "[Visit]"):
            continue
        col_description = dictionary["tables"][table_name]["fields"][col]["description"]
        mappings[col_description]=mapping
    return mappings

def datafileToComponents(datafile,dictionary,table_name_array,panel_id,assessment_components_template,workspace_id=9999,col_units={}):
    #Remove any records of this table already loaded into the components table.
    assessment_components_template.drop(assessment_components_template[assessment_components_template["ASSESSMENT_PANEL_ACCESSION"] == panel_id].index, inplace=True)
    for table_name in table_name_array:
        col_mappings = createColumnMappingDict(dictionary,table_name)
        
        question_id = 0
        datafile.rename(columns=col_mappings,inplace=True)
    
        question_cols = (dict(filter(lambda col: col[1]["verbatim_question"] != "",dictionary["tables"][table_name]["fields"].items())))
        
        set_columns = list(col_mappings.values())

        datacolumns = question_cols.keys()

        for col in datacolumns:
            df_slim = datafile[set_columns].copy()
            # This is processing entire rows of data files, it is not iterating over each cell
            # if property, need to 
            # Need to check to see if this is an actual question or a property (Age of Onset, Location, Date, etc) of another question.
            col_name= dictionary["tables"][table_name]["fields"][col]["description"]
            if col_name in datafile:
                question_id = question_id + 1
                component_id = f"{panel_id}_{question_id}"

                try:

                    df_slim["component_group_id"]=component_id
                    df_slim["Name Reported"]=col_name
                    df_slim["Result Value Reported"]=datafile[col_name]
                    df_slim["ASSESSMENT_PANEL_ACCESSION"]=panel_id
                    df_slim["WORKSPACE_ID"]=workspace_id
                    
                except:
                    logging.error("col_name")
                    logging.error(col_name)
                    raise

                df_slim.loc[(df_slim["Result Value Reported"] == "<NA>"), "Result Value Reported"] = np.NaN
            
                if dictionary["tables"][table_name]["fields"][col]["unit"] != "":
                    if dictionary["tables"][table_name]["fields"][col]["unit"].upper() == "[SPLIT]":
                        #Need to split Result Unit Reported into result and unit
                        logging.info(f"Split column {col} into result and unit")
                    else:

                        # Need to see if the value is "[Split]"
                        df_slim.loc[~df_slim["Result Value Reported"].isna(), "Result Unit Reported"] = dictionary["tables"][table_name]["fields"][col]["unit"]

                df_slim["Verbatim Question"] = dictionary["tables"][table_name]["fields"][col]["verbatim_question"]
                df_slim["Who Is Assessed"] = dictionary["tables"][table_name]["fields"][col]["who_is_assessed"]

                if(dictionary["tables"][table_name]["fields"][col]["age_onset"] != ""):
                    # Need to create subset (iloc) where age_onset has value
                    
                    lookup_col = dictionary["tables"][table_name]["fields"][col]["age_onset"]
                    lookup_col_name = dictionary["tables"][table_name]["fields"][lookup_col]["description"]
                    # logging.info(f"Lookup Column: {lookup_col}, {lookup_col_name}")
                    logging.debug(f"Age Onset Lookup col: {lookup_col}, {lookup_col_name} for {col}")

                    df_slim["Age At Onset Reported"]= datafile[lookup_col_name]
                    df_slim.loc[~df_slim["Age At Onset Reported"].isna(), "Age At Onset Unit Reported"] = dictionary["tables"][table_name]["fields"][col]["age_onset_unit"]

                
                if( dictionary["tables"][table_name]["fields"][col]["study_day"] != ""):
                    # Need to create subset (iloc) where age_onset has value
                    
                    lookup_col = dictionary["tables"][table_name]["fields"][col]["study_day"]
                    if lookup_col == "[Self]":
                        lookup_col = col
                    lookup_col_name = dictionary["tables"][table_name]["fields"][lookup_col]["description"]
                    logging.debug(f"Study Day Lookup col: {lookup_col}, {lookup_col_name} for {col}")
                    # logging.info(f"Lookup Column: {lookup_col}, {lookup_col_name}")

                    df_slim["Study Day"]= datafile[lookup_col_name]
                #Need to take df_slim and remove rows that have no actual data. 
        
                assessment_components_template=assessment_components_template.append(df_slim[~df_slim["Result Value Reported"].isnull()], ignore_index=True)
                # assessment_components_template=assessment_components_template.append(df_slim, ignore_index=True)
            else:
                logging.warn("Table Field not found in file: %s", col_name)
        
    return assessment_components_template


# def datafileToComponents(datafile,startCol,panel_id,assessment_components_template,workspace_id=9999,col_mappings={},col_units={}):
def datafileToComponents_old(datafile,dictionary,table_name,panel_id,assessment_components_template,workspace_id=9999,col_units={}):
    #Remove any records of this table already loaded into the components table.
    assessment_components_template.drop(assessment_components_template[assessment_components_template["ASSESSMENT_PANEL_ACCESSION"] == panel_id].index, inplace=True)
    col_mappings = createColumnMappingDict(dictionary,table_name)

    question_id = 0
    datafile.rename(columns=col_mappings,inplace=True)
    datacolumns = datafile.columns[startCol:]
    set_columns = list(col_mappings.values())

    df_slim = datafile[set_columns].copy()

    for col in datacolumns:
        question_id = question_id + 1
        component_id = f"{panel_id}_{question_id}"
        
        df_slim["component_group_id"]=component_id
        df_slim["Name Reported"]=col
        df_slim["Result Value Reported"]=datafile[col]
        df_slim["ASSESSMENT_PANEL_ACCESSION"]=panel_id
        df_slim["WORKSPACE_ID"]=workspace_id
        
        df_slim["Result Unit Reported"] = dictionary["tables"][table_name]["fields"][col]["unit"]
        df_slim["Verbatim Question"] = dictionary["tables"][table_name]["fields"][col]["unit"]

        
        # if(col in col_units):
            # df_slim["Result Unit Reported"] = col_units[col]

        assessment_components_template=assessment_components_template.append(df_slim, ignore_index=True)
    
    return assessment_components_template

def getColumnMapping(dictionary,table_name,mapping):
    if(mapping in dictionary["tables"][table_name]["mappings"]):
        return dictionary["tables"][table_name]["mappings"][mapping]
        mapping_col = dictionary["tables"][table_name]["mappings"][mapping]
        return dictionary["tables"][table_name]["fields"][mapping_col]["description"]

def getColumnName(dictionary, table_name, column_id):
    if column_id in dictionary["tables"][table_name]["fields"]:
        return dictionary["tables"][table_name]["fields"][column_id]["description"]


def readAndModifyStudyFile(filepath,file_tables,dictionary,planned_visits):
    full_datafile = pd.DataFrame()

    for file_table in file_tables["tables"]:
        datafile = readStudyFile(filepath,file_table,dictionary)
        visit_col = getColumnMapping(dictionary, file_table,"[Visit]")

        table_visits = addVisitAccessionFromName(planned_visits,datafile,visit_col,dictionary,file_table,file_tables.get("visit",None))
        table_visits[table_visits["plannedVisit"] == ""]

        planned_visit_data = datafile["PLANNED_VISIT_ID"]
        datafile=datafile.drop(columns=["PLANNED_VISIT_ID"])
        datafile.insert(loc=3, column="PLANNED_VISIT_ID",value=planned_visit_data)

        dd_ID = getColumnMapping(dictionary,file_table,"User Defined ID")
        dd_ID_col = getColumnName(dictionary, file_table,dd_ID)

        if(dd_ID_col not in datafile.columns):
            if("Accession" in datafile.columns):
                datafile.rename(columns={"Accession":dd_ID_col},inplace=True)
        full_datafile = full_datafile.append(datafile)
        
    return full_datafile

def getAssessmentPanelID(crf_Files,study_files,assessment_panel_df,study_id,assessment_type):
    filename_string = ",".join(crf_Files)
    name_reported = getStudyFileDescription(crf_Files[0],study_files)
    # print(f"Name Reported:{name_reported}")
    if(assessment_panel_df.empty):
        panelCount=0
        dataframe_rows=0
    else:
        panelCount = assessment_panel_df[assessment_panel_df["CRF File Names"].str.contains(filename_string)].count
        if(assessment_panel_df[assessment_panel_df["CRF File Names"].str.contains(filename_string)].empty):
            panelCount = 0
        dataframe_rows = len(assessment_panel_df)
    
    # print("Row count")
    # print(dataframe_rows)

    if(panelCount == 0):
        #We need to create a new panel
        print(f"Create new panel for files: {filename_string}")
        new_data={'Assessment Panel ID':f'CCHMC_{dataframe_rows+1}','Study ID':study_id, 'Name Reported':name_reported, 'CRF File Names':filename_string, 'Assessment Type': assessment_type}
        assessment_panel_df=assessment_panel_df.append(new_data, ignore_index=True)
    
    return [assessment_panel_df, assessment_panel_df[assessment_panel_df["CRF File Names"].str.contains(filename_string)].iloc[0]["Assessment Panel ID"]]
