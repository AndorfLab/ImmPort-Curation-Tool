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
    table_name = row[dictionary["columns"]["Table Name"]]
    values = row[dictionary["columns"]["Code List Values"]]
    field_name = row[dictionary["columns"]["Field Name"]]

    if(table_name not in dictionary["tables"]):
        dictionary["tables"][table_name]={"fields":{},"mappings":{}}
    
    verbatim_question = row[dictionary["columns"]["Verbatim Question"]]
    if(verbatim_question.lower() == "[same]"):
        verbatim_question =row[dictionary["columns"]["Field Description"]]
    col_mapping = row[dictionary["columns"]["Column Mappings"]]

    dictionary["tables"][table_name]["fields"][field_name]={
        "key_field" : row[dictionary["columns"]["Key Field"]],
        "description": row[dictionary["columns"]["Field Description"]],
        "expected" : row[dictionary["columns"]["Expected"]],
        "unit" : row[dictionary["columns"]["Unit"]],
        "verbatim_question" : verbatim_question,
        "note" : row[dictionary["columns"]["Note"]],
        "who_is_assessed" : row[dictionary["columns"]["Who is Assessed"]],
        "age_onset" : row[dictionary["columns"]["Age At Onset Reported"]],
        "age_onset_unit" : row[dictionary["columns"]["Age At Onset Unit Reported"]],
        "location" : row[dictionary["columns"]["Location"]],
        "study_day" : row[dictionary["columns"]["Study Day"]],
        "map_to_visit" : row[dictionary["columns"]["Map To Visit"]]
    }

    if(col_mapping):
        dictionary["tables"][table_name]["mappings"][col_mapping]=field_name

    if(len(values)>0):
        dictionary["tables"][table_name]["fields"][field_name]["values"]=parseCodeListValues(values)     

def parseDataDictionary(filename):
    dictionary={"columns":{},"tables":{}}

    with open(filename, encoding="utf-8-sig") as dictionary_FH:
        reader = csv.reader(dictionary_FH, delimiter=',', quotechar='"')
        header = next(reader)
        for column in header:
            dictionary["columns"][column]=header.index(column)
            
        for row in reader:
            parseDictionaryRow(row, dictionary)

    return dictionary
