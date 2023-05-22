import csv
import regex

# TODO
# Reports
#   Compare columns in datafile with data dictionary
        # For instance, the DD has fields (6) that do not appear in the SPT study file.
        # Conviently there are other fields that have the same name that are in the
        # study file. 

#TODO Create Class DataDictionary
#TODO Create Class DataFile

def parseCodeListValues(valueString):
    #regex : split on ", " where the next characters are either digits or a "word" followed by a =
    #Now, we have an array where of elements where the key is everything prior to the first "=", and the value is everything after this first "="
    #As such, not we split on ONLY the first "=" as the value might have "=" in it.
    try:
        codes = dict(x.split("=", 1) for x in regex.split(r"(?:, )(?=\d+=|\w+=)",valueString))
    except Exception as e:
        return "Error parsing code list values: " + str(e)
    return codes

def getColumnMapping(dictionary,table_name,mapping):
    if(mapping in dictionary["tables"][table_name]["mappings"]):
        mapping_col = dictionary["tables"][table_name]["mappings"][mapping]
        return dictionary["tables"][table_name]["fields"][mapping_col]["description"]

def parseDictionaryRow(row, dictionary):
    # print(row)
    # print(dictionary['columns'])

    table_name = row[dictionary["columns"]["Table Name"]]
    values = row[dictionary["columns"]["Code List Values"]]
    field_name = row[dictionary["columns"]["Field Name"]]

    if(table_name not in dictionary["tables"]):
        dictionary["tables"][table_name]={"fields":{},"mappings":{}}
    
    dictionary["tables"][table_name]["fields"][field_name]={}

    verbatim_question = row[dictionary["columns"]["Verbatim Question"]]
    if(verbatim_question.lower() == "[same]"):
        verbatim_question =row[dictionary["columns"]["Field Description"]]


    # dictionary["tables"][table_name]["fields"][field_name]={"question":True,"verbatim_question" : verbatim_question}
    # dictionary["tables"][table_name]["fields"][field_name]={
    #     "key_field" : row[dictionary["columns"]["Key Field"]],
    #     "description": row[dictionary["columns"]["Field Description"]],
    #     "expected" : row[dictionary["columns"]["Expected"]],
    #     "unit" : row[dictionary["columns"]["Unit"]],
    #     "verbatim_question" : verbatim_question,
    #     "note" : row[dictionary["columns"]["Note"]],
    #     "who_is_assessed" : row[dictionary["columns"]["Who is Assessed"]],
    #     "age_onset" : row[dictionary["columns"]["Age At Onset Reported"]],
    #     "age_onset_unit" : row[dictionary["columns"]["Age At Onset Unit Reported"]],
    #     "location" : row[dictionary["columns"]["Location"]],
    #     "study_day" : row[dictionary["columns"]["Study Day"]],
    #     "map_to_visit" : row[dictionary["columns"]["Map To Planned Visit"]],
    #     "question":True
    # }

    ## TODO Possibly log which fields are not found in data dictionary

    dictionary_to_variable = {"key_field":"Key Field", "description":"Field Description","expected":"Expected","unit":"Unit","note":"Note","who_is_assessed":"Who is Assessed","age_onset":"Age at Onset Reported","age_onset_unit":"Age At Onset Unit Reported","location":"Location","study_day":"Study Day"}

    if "Map to Planned Visit" in dictionary["columns"]:
        dictionary_to_variable['map_to_visit']="Map To Planned Visit"
    elif "Map to Visit" in dictionary["columns"]:
        dictionary_to_variable['map_to_visit']="Map To Visit"

    for key, label in dictionary_to_variable.items():
        if label in dictionary["columns"]:
            dictionary["tables"][table_name]["fields"][field_name][key]=row[dictionary["columns"][label]]
        else:
            dictionary["tables"][table_name]["fields"][field_name][key]=""

    col_mapping = row[dictionary["columns"]["Column Mappings"]]
    if col_mapping.upper() == "VISIT":
        col_mapping = "[Visit]"

    if(col_mapping):
        dictionary["tables"][table_name]["mappings"][col_mapping]=field_name
        dictionary["tables"][table_name]["fields"][field_name]['question']=False

    if(len(values)>0):
        dictionary["tables"][table_name]["fields"][field_name]["values"]=parseCodeListValues(values)

def parseDataDictionary(filename, gui_object):
    dictionary={"columns":{},"tables":{}}

    with open(filename, encoding="utf-8-sig") as dictionary_FH:
        reader = csv.reader(dictionary_FH, delimiter=',', quotechar='"')
        header = next(reader)
        for column in header:
            dictionary["columns"][column]=header.index(column)
        
        required_dictionary_columns=[
            "Table Name",
            "Code List Values",
            "Field Name",
            "Verbatim Question",
            "Field Description",
            "Unit",
            "Who is Assessed",
            "Age at Onset Reported",
            "Age at Onset Unit Reported",
            "Location",
            "Study Day"
        ]

        missing_required_columns = list(filter(lambda c: c not in dictionary["columns"].keys(), required_dictionary_columns))

        if len(missing_required_columns):
            gui_object.log(level="Critical", flush=True, message=f"Data Dictionary is missing the following fields:\n\t"+"\n\t".join(missing_required_columns))
            # return
            raise NotImplementedError("Data Dictionary missing column")

        for i, row in enumerate(reader):
            try:
                parseDictionaryRow(row, dictionary)
            except KeyError as e:
                gui_object.log(level="critical", message=f"Data Dictionary missing column{e}", flush=True)
            except Exception as e:
                gui_object.log(level="critical", message=f"Error processing Data Dictionary row {i}. {e}", flush=True)
                raise NotImplementedError("")

        #Iterate through fields, and check if the field is used in other mappings:

        for table_name in dictionary["tables"].keys():
            for field in dictionary["tables"][table_name]["fields"].keys():
                possible_fields = []
                for col in ["unit","who_is_assessed","age_onset","age_onset_unit","location","study_day"]:
                    if col in  dictionary["tables"][table_name]["fields"][field]:
                        possible_fields.append(col)
                for pf in possible_fields:
                    if pf in dictionary["tables"][table_name]["fields"]:
                        dictionary["tables"][table_name]["fields"][pf]["question"]=False


    return dictionary
