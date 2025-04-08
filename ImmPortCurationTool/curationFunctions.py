import pandas as pd
import io
import os
import subprocess
import re
import traceback
import json
import numpy as np
from io import StringIO
from zipfile import ZipFile
import ImmPortCurationTool.immport_gui as ig
import urllib.parse

from IPython.display import display

pd.options.display.max_columns = 400
pd.options.display.max_rows = 200

missingVisits_all = {}

def writePanelComponentTemplate(panel, component, header, filepath, template):
    panel["Result Separator Column"]=""

    if template == "assessments":

        df_temp = panel.merge(component, left_on='Assessment Panel ID', right_on='ASSESSMENT_PANEL_ACCESSION')
        df_temp["Subject ID"]=df_temp["User Defined ID"]
        df_temp["User Defined ID"]=df_temp.index+0
        df_temp.drop(columns=["ASSESSMENT_PANEL_ACCESSION","component_group_id","WORKSPACE_ID"], inplace=True, errors='ignore')

    elif template == "labTests":

        df_temp = panel.merge(component, left_on='Lab Test Panel ID', right_on='LAB_TEST_PANEL_ACCESSION')

        print(f"df_temp {df_temp}")

        if 'Planned Visit ID_y' in df_temp.columns:
            df_temp['Planned Visit ID'] = df_temp['Planned Visit ID_y']
        elif 'Planned Visit ID' in df_temp.columns:
            pass  

        df_temp["Subject ID"]=df_temp["User Defined ID"]
        df_temp["User Defined ID"]=df_temp.index+0
        df_temp.drop(columns=["LAB_TEST_PANEL_ACCESSION","component_group_id","WORKSPACE_ID"], inplace=True, errors='ignore')

    colNames = list(map(lambda s: s.replace("_x","").replace("_y",""),df_temp.columns.to_list()))

    df_temp.columns = colNames

    header.to_csv(filepath, sep="|",index=False, encoding='utf-8')

    df_temp.to_csv(filepath, sep="\t", mode='a',header=False, index=False)


def processStudyFile(table_list,directory,dictionary,planned_visits,study_files,panel_template,study_id,components_template,table_metadata,workspace_id,template):    

    if template == "assessments":

        for table_set in table_list:
            filename = table_metadata.loc[table_metadata.table_name.isin(table_set["tables"])]["table_file"].values[0]
            filepath = directory+"StudyFiles/"+filename

            datafile = readAndModifyStudyFile(filepath,table_set,dictionary,planned_visits)
            [panel_template,panel_id] = getAssessmentPanelID([filename],study_files,panel_template,study_id,table_set["assessment_type"])
            panel=getAssessmentPanelByID(panel_id,panel_template)
            
            components_template=datafileToComponents(datafile,dictionary,table_set["tables"],components_template,template,panel_id,workspace_id)

        components_template.to_csv('processStudyFile_assessment_component_template.csv', index=False)
        panel_template.to_csv('processStudyFile_assessment_panel_template.csv', index=False)

        return [panel_template, components_template]

def readFileFromZip(dir,zip,file):
    if zip.endswith('.zip'):
        zip = zip.replace('.zip','')
    if not dir.endswith('/'):
        dir += "/"
    try:
        with ZipFile(f"{dir}{zip}.zip") as myzip:
            with myzip.open(f"{zip}/Tab/{file}") as myfile:
                myfile_contents = pd.read_csv(io.BytesIO(myfile.read()), encoding='utf8', sep="\t")
                return myfile_contents
            
    except KeyError:
        return None
    except Exception as e:
        raise NotImplementedError("Zip extract went wrong")

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

    dict_visits=dict(zip(planned_visits["NAME"],planned_visits["PLANNED_VISIT_ACCESSION"]))

        # ADD DEBUG PRINT STATEMENTS HERE
    display(f"DEBUG Mapping visits for table: {file_table}")
    display(f"DEBUG Visit column: {visit_col}")
    display(f"DEBUG First 5 visit values: {table[visit_col].head()}")
    display(f"DEBUG Planned visits mapping: {dict_visits}")
        
    if(table_column is None):
        if(default_visit is not None):
            table["PLANNED_VISIT_ID"]=dict_visits.get(default_visit,"")
            table_visit = pd.DataFrame(data={'plannedVisit':['']})
            return table_visit
        else:
            raise ValueError(f"No default visit has been defiled for {file_table}")

    table_visits = table.groupby([visit_col], as_index=False).agg('nunique')

    table_visits.drop(table_visits.columns.difference([visit_col]),axis=1, inplace=True)
    table_visits["plannedVisit"] = ""
    for index, row in table_visits.iterrows():
        for key in dict_visits.keys():
            if(key.startswith(row[visit_col])):
                table_visits.loc[index,"plannedVisit"]=dict_visits[key]
            elif(row[visit_col].isnumeric() & ("Visit "+row[visit_col] in key)):
                table_visits.loc[index,"plannedVisit"]=dict_visits[key]
            elif(row[visit_col].isnumeric() & ("Visit 0"+row[visit_col] in key)):
                table_visits.loc[index,"plannedVisit"]=dict_visits[key]
            elif(row[visit_col][0:-1].isnumeric() & ("Visit "+row[visit_col][0:-1] in key)):
                table_visits.loc[index,"plannedVisit"]=dict_visits[key]
            elif(row[visit_col][0:-2].isnumeric() & ("Visit "+row[visit_col][0:-2] in key)):
                table_visits.loc[index,"plannedVisit"]=dict_visits[key]
            elif(~row[visit_col][0:1].isnumeric() & row[visit_col][1:].isnumeric() & ("Visit "+row[visit_col][1:] in key)):
                table_visits.loc[index,"plannedVisit"]=dict_visits[key]
            # else: #TODO write to log
            #     logging.warn(f"Cannot find planned visit for {key}")
            #     ig.unique_logging_buffer_load(level="warn", message=f"Cannot find planned visit for {key}")
    
        dict_visits2=dict(zip(table_visits[visit_col],table_visits["plannedVisit"]))
    ig.main_logger.flush()

    if "map_to_visit" in dictionary["tables"][file_table]["fields"][visit_col] and len(dictionary["tables"][file_table]["fields"][visit_col]["map_to_visit"])>0:
        #TODO: possible look at this when reading in the dictionary. If the column is not blank, check if its valid JSON and a DICT.
        try:
            visit_map_dict = json.loads(dictionary["tables"][file_table]["fields"][visit_col]["map_to_visit"])
        except Exception as e:
            map_to_visit_str = dictionary["tables"][file_table]["fields"][visit_col]["map_to_visit"]
            ig.main_logger.write(level="error", message=f"Invalid JSON for Map to Planned Visit column on table {table_column}. Try using <a href='https://jsonlint.com?json={urllib.parse.quote(map_to_visit_str)}'>jsonlint.com</a> to find the errors.", flush=True)
            raise e
        #create dictionary of visit_mappings to planned visit IDs
        dict_visits_mapped = dict(map(lambda x: (x[0],dict_visits[x[1]]), visit_map_dict.items()))
        dict_visits2.update(dict_visits_mapped)

    missingVisits = dict(filter(lambda visit: visit[1] == "", dict_visits2.items()))

    if(len(missingVisits)>0):
        sep = "\n\t"
        ig.main_logger.write(level="error",message=f"Unable to find planned visits for the following visit names{sep}{sep.join(list(missingVisits.keys()))}")
        ig.main_logger.write(level="error",message=f"Available Visits{sep}{sep.join(list(dict_visits.keys()))}")

    table["PLANNED_VISIT_ID"]=table[visit_col].apply(lambda v: dict_visits2[v])

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
    # datafile.rename(columns=lambda c: dictionary["tables"][table]["fields"][c]["description"] if c in dictionary["tables"][table]["fields"] else c, inplace=True)
    return datafile

def getAssessmentPanelByID(panel_ID,assessment_panel_df):
    return assessment_panel_df[assessment_panel_df["Assessment Panel ID"]==panel_ID]

def readTemplate(template, template_path="templates/txt-templates/"):

    if template == 'assessments':
        template_file_path = os.path.abspath(os.path.join(template_path, "assessments.txt"))

        assessment_template_header = pd.read_csv(template_file_path, nrows=2)
        assessments = pd.read_csv(template_file_path, sep='\t', skiprows=2, nrows=0)

        split_on_col = assessments.columns.get_loc("Result Separator Column")
        panel_template = assessments.iloc[:, :split_on_col-1]
        components_template = assessments.iloc[:, split_on_col+1:].copy()

        return panel_template, components_template, assessment_template_header
    
    if template == 'labTests':
        template_file_path = os.path.abspath(os.path.join(template_path,"labTests.txt"))

        labTest_template_header = pd.read_csv(template_file_path,nrows=2)

        labTests = pd.read_csv(template_file_path, sep='\t', skiprows=2,nrows=0)
        split_on_col = labTests.columns.get_loc("Result Separator Column")
        labTest_panel_template = labTests.iloc[: , :split_on_col-1]
        labTest_components_template = labTests.iloc[: , split_on_col+1:].copy()

        labTest_components_template.rename(columns={"Name Reported.1":"Name Reported"}, inplace=True)

        return labTest_panel_template,labTest_components_template,labTest_template_header

def createColumnMappingDict(dictionary,table_name):
    mappings={"PLANNED_VISIT_ID":"Planned Visit ID"}
    for mapping, col in dictionary["tables"][table_name]["mappings"].items():
        if(mapping == "[NA]" or mapping == "[Visit]"):
            continue

        mappings[col]=mapping

    return mappings

def datafileToComponents(datafile,dictionary,table_name_array,components_template,template,panel_id=-1,workspace_id=9999,col_units={}):
   
    if template == "assessments":
   
        #Remove any records of this table already loaded into the components table.
        components_template.drop(components_template[components_template["ASSESSMENT_PANEL_ACCESSION"] == panel_id].index, inplace=True)
        for table_name in table_name_array:
            col_mappings = createColumnMappingDict(dictionary,table_name)

            question_id = 0
            datafile.rename(columns=col_mappings,inplace=True)
        
            #Limit to fields that have a "true" value for the "question" field as specified when loading the data dictionary
            question_cols = (dict(filter(lambda col: col[1]["question"],dictionary["tables"][table_name]["fields"].items())))

            display(f"question_cols {question_cols}")
            

            set_columns = list(col_mappings.values())

            display(f"set_columns {set_columns}")

            datacolumns = question_cols.keys()

            display(f"datacolumns {datacolumns}")

            for col in datacolumns:
                df_slim = datafile[set_columns].copy()
                # This is processing entire rows of data files, it is not iterating over each cell
                # Need to check to see if this is an actual question or a property (Age of Onset, Location, Date, etc) of another question.
                col_name= dictionary["tables"][table_name]["fields"][col]["description"]
                if col in datafile:
                    question_id = question_id + 1
                    component_id = f"{panel_id}_{question_id}"

                    try:
                        df_slim["component_group_id"]=component_id
                        df_slim["Name Reported"]=col_name
                        df_slim["Result Value Reported"]=datafile[col]

                        display(f"col {col}")
                        display(f"datafile[col] {datafile[col]}")

                        df_slim["ASSESSMENT_PANEL_ACCESSION"]=panel_id
                        df_slim["WORKSPACE_ID"]=workspace_id
                    except Exception as e:
                        ig.main_logger.write(level="error",message=f"Error with column {col_name} in {table_name}- {str(e)}\n{traceback.format_exc()}", flush=True)
                        raise

                    display(f"df_slim[Result Value Reported] {df_slim["Result Value Reported"]}")

                    df_slim.loc[(df_slim["Result Value Reported"] == "<NA>"), "Result Value Reported"] = np.nan
                
                    if dictionary["tables"][table_name]["fields"][col]["unit"] != "":
                        if dictionary["tables"][table_name]["fields"][col]["unit"].upper() == "[SPLIT]":
                            #Need to split Result Unit Reported into result and unit
                            df_slim.loc[
                                ~df_slim["Result Value Reported"].isna() &
                                df_slim["Result Value Reported"].str.contains(" ")
                                , ["Result Value Reported","Result Unit Reported"]
                            ] = df_slim.loc[
                                ~df_slim["Result Value Reported"].isna() &
                                df_slim["Result Value Reported"].str.contains(" ")
                                , "Result Value Reported"].str.split(" ", n=1, expand=True)
                        elif dictionary["tables"][table_name]["fields"][col]["unit"].startswith("[") and dictionary["tables"][table_name]["fields"][col]["unit"].endswith("]"):
                            lookup_col = dictionary["tables"][table_name]["fields"][col]["unit"][1:-1]  #remove '[' and ']'
                            lookup_col_name = dictionary["tables"][table_name]["fields"][lookup_col]["description"]
        
                            df_slim["Result Unit Reported"]= datafile[lookup_col]

                        else:
                            # Need to see if the value is "[Split]"
                            df_slim.loc[~df_slim["Result Value Reported"].isna(), "Result Unit Reported"] = dictionary["tables"][table_name]["fields"][col]["unit"]

                    df_slim["Verbatim Question"] = dictionary["tables"][table_name]["fields"][col]["verbatim_question"]
                    df_slim["Who Is Assessed"] = dictionary["tables"][table_name]["fields"][col]["who_is_assessed"]

                    if(dictionary["tables"][table_name]["fields"][col]["age_onset"] != ""):
                        # Need to create subset (iloc) where age_onset has value
                        
                        lookup_col = dictionary["tables"][table_name]["fields"][col]["age_onset"]
                        lookup_col_name = dictionary["tables"][table_name]["fields"][lookup_col]["description"]
                        ig.main_logger.write(level='info', message=f"\tUsing field {lookup_col} for 'Age At Onset Reported' for {col} with unit: {dictionary['tables'][table_name]['fields'][col]['age_onset_unit']}")

                        df_slim["Age At Onset Reported"]= datafile[lookup_col]
                        df_slim.loc[~df_slim["Age At Onset Reported"].isna(), "Age At Onset Unit Reported"] = dictionary["tables"][table_name]["fields"][col]["age_onset_unit"]

                    #If location is not empty, and value is a column in the data/study file, then use the value from the corresponding field
                    if(dictionary["tables"][table_name]["fields"][col]["location"] != ""):
                        # Need to create subset (iloc) where age_onset has value
                        
                        lookup_col = dictionary["tables"][table_name]["fields"][col]["location"]

                        if lookup_col in datafile:
                            ig.main_logger.write(level='info', message=f"\tUsing field {lookup_col} for 'Location of Finding Reported' for {col}")
                            df_slim["Location Of Finding Reported"]= datafile[lookup_col]
                        else:
                            ig.main_logger.write(level='info', message=f"\tUsing value {lookup_col} for 'Location of Finding Reported' for {col}")
                            df_slim["Location Of Finding Reported"]= lookup_col
                    
                    if( dictionary["tables"][table_name]["fields"][col]["study_day"] != ""):
                        # Need to create subset (iloc) where age_onset has value
                        
                        lookup_col = dictionary["tables"][table_name]["fields"][col]["study_day"]
                        if lookup_col == "[Self]":
                            lookup_col = col
                        lookup_col_name = dictionary["tables"][table_name]["fields"][lookup_col]["description"]
                        ig.main_logger.write(level='info', message=f"\tUsing field {lookup_col} for 'Study Day' value for {col}")

                        df_slim["Study Day"]= datafile[lookup_col]
                    #Need to take df_slim and remove rows that have no actual data. 
            
                   # assessment_components_template = pd.concat([assessment_components_template, df_slim[~df_slim["Result Value Reported"].isnull()]], ignore_index=True)
                    components_template = pd.concat([components_template, df_slim[~df_slim["Result Value Reported"].isnull()]], ignore_index=True)
  
                else:
                    ig.main_logger.write(level='critical', message=f"Table Field not found in file: {col_name} in {table_name}", flush=True)
 
    elif template == "labTests":
        components_template.drop(
            components_template[components_template["LAB_TEST_PANEL_ACCESSION"] == panel_id].index,
            inplace=True
        )
        
        for table_name in table_name_array:
            # Create column mappings
            col_mappings = createColumnMappingDict(dictionary, table_name)
            datafile.rename(columns=col_mappings, inplace=True)
            
            # Get planned visit ID - prioritize 'Planned Visit ID' column, fall back to 'PLANNED_VISIT_ID'
            planned_visit_col = 'Planned Visit ID' if 'Planned Visit ID' in datafile.columns else 'PLANNED_VISIT_ID'
            planned_visit_id = datafile[planned_visit_col].iloc[0] if planned_visit_col in datafile.columns else "None"
            
            display(f"planned_visit_col! {planned_visit_col}")

            # Get all question fields from dictionary
            question_cols = dict(
                filter(lambda col: col[1]["question"], 
                    dictionary["tables"][table_name]["fields"].items())
            )

           # study_time_collected_col = getColumnMapping(dictionary, table_name, "[Study Day]")
            study_time_collected_col = 'Study Time Collected' if 'Study Time Collected' in datafile.columns else 'STUDY_TIME_COLLECTED'
            study_time_collected_id = datafile[study_time_collected_col].iloc[0] if study_time_collected_col in datafile.columns else "None"
        
            display(f"study_time_collected_col! {study_time_collected_col}")

            # Process each question field
            for col, col_props in question_cols.items():
                if col in datafile:

                    if not pd.api.types.is_numeric_dtype(datafile[col]):
                        try:
                            # Try converting to numeric
                            datafile[col] = pd.to_numeric(datafile[col], errors='coerce')
                        except:
                            # Skip this column if conversion fails
                            ig.main_logger.write(
                                level="warn",
                                message=f"Skipping non-numeric column: {col} with value: {datafile[col].iloc[0]}"
                            )
                            continue

                    # Create slim dataframe with just the needed columns
                    df_slim = datafile[['User Defined ID', planned_visit_col]].copy()
                    df_slim.rename(columns={planned_visit_col: 'Planned Visit ID'}, inplace=True)
                    
                    # Add required columns
                    df_slim['LAB_TEST_PANEL_ACCESSION'] = panel_id
                    df_slim['WORKSPACE_ID'] = workspace_id
                    df_slim['Name Reported'] = col_props["description"]
                    df_slim['Result Value Reported'] = datafile[col]
                    
                    # Handle units
                    unit_info = col_props.get("unit", "")
                    if unit_info:
                        if unit_info.upper() == "[SPLIT]":
                            # Split values like "5 mg" into value and unit
                            split_values = df_slim['Result Value Reported'].str.split(" ", n=1, expand=True)
                            df_slim['Result Value Reported'] = split_values[0]
                            df_slim['Result Unit Reported'] = split_values[1]
                        elif unit_info.startswith("[") and unit_info.endswith("]"):
                            # Unit comes from another column
                            unit_col = unit_info[1:-1]
                            if unit_col in datafile:
                                df_slim['Result Unit Reported'] = datafile[unit_col]
                            else:
                                df_slim['Result Unit Reported'] = ""
                        else:
                            # Static unit value
                            df_slim['Result Unit Reported'] = unit_info
                    
                    # Handle numeric values
                    if pd.api.types.is_numeric_dtype(df_slim['Result Value Reported']):
                        df_slim['Result Value Reported'] = pd.to_numeric(
                            df_slim['Result Value Reported'], errors='coerce'
                        )
                    
                    # Drop NA values
                    df_slim = df_slim[~df_slim['Result Value Reported'].isna()]


                    if study_time_collected_col and study_time_collected_col in datafile.columns:
                        df_slim['Study Time Collected'] = datafile[study_time_collected_col]

                    display(f"df_slim {df_slim}")
                  
                    # Add to components template
                    if not df_slim.empty:
                        components_template = pd.concat(
                            [components_template, df_slim],
                            ignore_index=True
                        )
                else:
                    ig.main_logger.write(
                        level='critical', 
                        message=f"Table Field not found in file: {col_props['description']} in {table_name}",
                        flush=True
                    )
                    
    return components_template

def getColumnMapping(dictionary,table_name,mapping):
    if(mapping in dictionary["tables"][table_name]["mappings"]):
        return dictionary["tables"][table_name]["mappings"][mapping]

def getColumnName(dictionary, table_name, column_id):
    if column_id in dictionary["tables"][table_name]["fields"]:
        return dictionary["tables"][table_name]["fields"][column_id]["description"]

def readAndModifyStudyFile(filepath,file_tables,dictionary,planned_visits):

    full_datafile = pd.DataFrame()

    for file_table in file_tables["tables"]:
        datafile = readStudyFile(filepath,file_table,dictionary)
        visit_col = getColumnMapping(dictionary, file_table,"[Visit]")
        study_date_col = getColumnMapping(dictionary, file_table, "[Study Day]")

        # 2. DEBUG: Print column mapping info
        display(f"DEBUG Processing table: {file_table}")
        display(f"DEBUG Visit column mapping: {visit_col}")
        display(f"DEBUG Study date mapping: {study_date_col}")
        display(f"DEBUG Actual columns in data: {datafile.columns.tolist()}")
        
        if visit_col and visit_col not in datafile.columns:
            available = "\n\t".join(datafile.columns)
            raise ValueError(
                f"CRITICAL: Dictionary requires column '{visit_col}' "
                f"but it's missing in {os.path.basename(filepath)}\n"
                f"Available columns:\n\t{available}"
            )

        table_visits = addVisitAccessionFromName(planned_visits,datafile,visit_col,dictionary,file_table,file_tables.get("visit",None))
        table_visits[table_visits["plannedVisit"] == ""]

        planned_visit_data = datafile["PLANNED_VISIT_ID"]
        datafile=datafile.drop(columns=["PLANNED_VISIT_ID"])
        datafile.insert(loc=3, column="PLANNED_VISIT_ID",value=planned_visit_data)

        if study_date_col and study_date_col in datafile.columns:
            datafile["Study Time Collected"] = datafile[study_date_col]

        
        dd_ID = getColumnMapping(dictionary,file_table,"User Defined ID")
        dd_ID_col = getColumnName(dictionary, file_table,dd_ID)
        
        if dd_ID_col not in datafile.columns:
            if "Accession" in datafile.columns:
                datafile.rename(columns={"Accession":"User Defined ID"},inplace=True)

        full_datafile = pd.concat([full_datafile, datafile], ignore_index=True)

    display(f"full_datafile {full_datafile}")

    return full_datafile

def getAssessmentPanelID(crf_Files,study_files,assessment_panel_df,study_id,assessment_type):
    filename_string = ",".join(crf_Files)
    name_reported = getStudyFileDescription(crf_Files[0],study_files)
    if(assessment_panel_df.empty):
        panelCount=0
        dataframe_rows=0
    else:
        panelCount = assessment_panel_df[assessment_panel_df["CRF File Names"].str.contains(filename_string)].count
        if(assessment_panel_df[assessment_panel_df["CRF File Names"].str.contains(filename_string)].empty):
            panelCount = 0
        dataframe_rows = len(assessment_panel_df)
    
    if(panelCount == 0):
        #We need to create a new panel
        print(f"Create new panel for files: {filename_string}") #TODO change to logging as debug
        new_data={'Assessment Panel ID':f'CCHMC_{dataframe_rows+1}','Study ID':study_id, 'Name Reported':name_reported, 'CRF File Names':filename_string, 'Assessment Type': assessment_type}
        
        assessment_panel_df = pd.concat([assessment_panel_df, new_data], ignore_index=True)

    return [assessment_panel_df, assessment_panel_df[assessment_panel_df["CRF File Names"].str.contains(filename_string)].iloc[0]["Assessment Panel ID"]]
