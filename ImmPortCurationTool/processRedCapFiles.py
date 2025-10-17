import ImmPortCurationTool.immport_gui as ig

import csv
import regex
import json
from IPython.display import display


def parseCodeListValues(valueString):

    if not valueString:
        return {}
    
    try:
        pairs = regex.split(r',\s*(?=[^,=]+?=)', valueString)
        
        codes = {}

        for p in pairs:
            key_value = p.split("=", 1)
            
            if len(key_value) == 2:
                key, value = key_value
                codes[key.strip()] = value.strip()  
            else:
                codes[key_value[0].strip()] = key_value[0].strip() 

        return codes
    
    except Exception as e:
        return {"__PARSE_ERROR__": str(e)}

def parseDictionaryRow(row, dictionary, formatted_columns):

    ci_formatted_columns = {k.lower(): v for k, v in formatted_columns.items()}

    def get_ci_column(label, default=""):

        return row[ci_formatted_columns.get(label.lower(), -1)] if label.lower() in ci_formatted_columns else default

    table_name = get_ci_column("Table Name").strip()
    values = get_ci_column("Code List Values")
    field_name = get_ci_column("Field Name").strip()

    if table_name not in dictionary["tables"]:
        dictionary["tables"][table_name] = {"fields": {}, "mappings": {}}

    verbatim_question = (
        get_ci_column("Verbatim Question") or
        get_ci_column("Question") or
        get_ci_column("Verbatim Questions") or
        get_ci_column("Questions")
    )

    if verbatim_question.lower() == "[same]":
        verbatim_question = get_ci_column("Field Description")

    dictionary["tables"][table_name]["fields"][field_name] = {
        "question": True,
        "verbatim_question": verbatim_question
    }

    dictionary_to_variable = {
        "description": "field description",
        "unit": "unit",
        "who_is_assessed": "who is assessed",
        "location": "location"
    }

    for key, label in dictionary_to_variable.items():
        dictionary["tables"][table_name]["fields"][field_name][key] = get_ci_column(label)

    age_onset = (
        get_ci_column("age at onset reported") or
        get_ci_column("age reported") or
        get_ci_column("age")
    )

    dictionary["tables"][table_name]["fields"][field_name]["age_onset"] = age_onset

    age_onset_unit = (
        get_ci_column("age at onset unit reported") or
        get_ci_column("age unit reported") or
        get_ci_column("age unit") or
        get_ci_column("age at onset reported unit") or
        get_ci_column("age reported unit")
    )

    dictionary["tables"][table_name]["fields"][field_name]["age_onset_unit"] = age_onset_unit

    col_mapping = (
        get_ci_column("Column Mappings") or
        get_ci_column("Mappings") or
        get_ci_column("Column Mapping") or
        get_ci_column("Mapping")
    )

    map_to_visit = None
    
    if col_mapping and col_mapping.strip().lower() == "visit":
        raw_mapping = get_ci_column("Map To Planned Visit", None) or get_ci_column("Map To Visit", None)
        
        if raw_mapping:
            raw_mapping = raw_mapping.strip()

            try:
                if raw_mapping.startswith("{") and raw_mapping.endswith("}"):
                    map_to_visit = json.loads(raw_mapping)
                else:
                    map_to_visit = raw_mapping
            except Exception as e:
                map_to_visit = raw_mapping

        elif values:
            map_to_visit = parseCodeListValues(values)

        dictionary["tables"][table_name]["fields"][field_name]["map_to_visit"] = map_to_visit

    study_day = (
        get_ci_column("override study day") or
        get_ci_column("study day") or
        get_ci_column("study day override")
    )

    dictionary["tables"][table_name]["fields"][field_name]["study_day"] = study_day

    if study_day and study_day.upper() in ["SELF", "[SELF]"]:
        dictionary["tables"][table_name]["fields"][field_name].update({
            "study_day_ref": field_name,
            "study_day_type": "number"
        })
    elif study_day:
        dictionary["tables"][table_name]["fields"][field_name].update({
            "study_day_ref": study_day,
            "study_day_type": "number"
        })
    elif col_mapping and col_mapping.upper() in ["STUDY DAY", "[STUDY DAY]"]:
        prev = dictionary["tables"][table_name]["mappings"].get("[Study Day]")

        if prev:
            display(f"[DEBUG processRedCapFiles] Duplicate [Study Day] mapping in table='{table_name}': overwriting '{prev}' with '{field_name}'")
        dictionary["tables"][table_name]["mappings"]["[Study Day]"] = field_name

    study_time = (
        get_ci_column("override study time") or
        get_ci_column("study time") or
        get_ci_column("study time override")
    )

    dictionary["tables"][table_name]["fields"][field_name]["study_time"] = study_time

    if study_time and study_time.upper() in ["SELF", "[SELF]"]:
        dictionary["tables"][table_name]["fields"][field_name].update({
            "study_time_ref": field_name,
            "study_time_type": "time"
        })
    elif study_time:
        dictionary["tables"][table_name]["fields"][field_name].update({
            "study_time_ref": study_time,
            "study_time_type": "time"
        })
    elif col_mapping and col_mapping.upper() == "STUDY TIME":
        prev = dictionary["tables"][table_name]["mappings"].get("[Study Time]")
  
        if prev:
            display(f"[DEBUG processRedCapFiles] Duplicate [Study Time] mapping in table='{table_name}': overwriting '{prev}' with '{field_name}'")
 
        dictionary["tables"][table_name]["mappings"]["[Study Time]"] = field_name

    if col_mapping:
        col_mapping_normalized = col_mapping.strip().lower()
        column_mapping_lookup = {
            "visit": "[Visit]",
            "study day": "[Study Day]",
            "study time": "[Study Time]",
            "user defined id": "[User Defined ID]",
            "category": "[Category]"
        }

        standard_mapping = column_mapping_lookup.get(col_mapping_normalized)

        if standard_mapping == "[Category]":
            current_cats = dictionary["tables"][table_name]["mappings"].get("[Category]", [])
  
            if isinstance(current_cats, str):
                current_cats = [current_cats]
  
            if field_name not in current_cats:
                current_cats.append(field_name)
  
            dictionary["tables"][table_name]["mappings"]["[Category]"] = current_cats
   
        elif standard_mapping:
            prev = dictionary["tables"][table_name]["mappings"].get(standard_mapping)
            dictionary["tables"][table_name]["mappings"][standard_mapping] = field_name
            dictionary["tables"][table_name]["fields"][field_name]["question"] = False

        elif col_mapping.strip().upper() == "NA":
            na_fields = dictionary["tables"][table_name]["mappings"].get("NA", [])
            flattened_na = [x for sub in (x if isinstance(x, list) else [x] for x in na_fields) for x in sub]
   
            if field_name not in flattened_na:
                flattened_na.append(field_name)
 
            dictionary["tables"][table_name]["mappings"]["NA"] = flattened_na

    if len(values) > 0:
        dictionary["tables"][table_name]["fields"][field_name]["values"] = parseCodeListValues(values)

    return dictionary

def parseDataDictionary(filename, gui_object):

    selected_template = None
    try:
        selected_template = gui_object.current_template()
     
        if selected_template:
            gui_object.log(f"Processing data dictionary with template: {selected_template}", level="info")
   
    except Exception as e:
        gui_object.log(f"Error getting data dictionary template: {str(e)}", level="error")

    dictionary = {"columns": {}, "tables": {}}
    delimiter = None
    header = []
    all_rows = []

    for enc in ["utf-8-sig", "cp1252"]:
        try:
            with open(filename, encoding=enc) as dictionary_FH:
                first_line = dictionary_FH.readline()
                dictionary_FH.seek(0)

                for possible_delim in [',', '\t']:
              
                    if len(first_line.split(possible_delim)) > 1:
                        delimiter = possible_delim
                        break

                if delimiter is None:
                    gui_object.log(level="Critical", message="Could not determine file delimiter (neither comma nor tab worked)", flush=True)
                    raise ValueError("Could not parse data dictionary - invalid format")

                reader = csv.reader(dictionary_FH, delimiter=delimiter, quotechar='"')
                header = next(reader)

                all_rows = list(reader)
                all_rows = [[cell.strip() if isinstance(cell, str) else cell for cell in row] for row in all_rows]

            break
  
        except UnicodeDecodeError:
            continue
 
    else:
        raise ValueError("Failed to read data dictionary with UTF-8 or CP1252 encoding.")

    formatted_columns = {col.strip().lower(): i for i, col in enumerate(header)}
    dictionary["columns"] = formatted_columns

    required_columns = {
        'assessment': [
            "table name", "field name", "field description",
            "code list values", "unit", "column mappings"
        ],
        'lab test': [
            "table name", "field name", "field description",
            "code list values", "unit", "column mappings"
        ],
        'assessment & lab test': [
            "table name", "field name", "field description",
            "code list values", "unit", "column mappings"
        ]
    }.get(selected_template.lower(), [])

    if "mappings" in formatted_columns and "column mappings" not in formatted_columns:
        formatted_columns["column mappings"] = formatted_columns["mappings"]

    missing_columns = [col for col in required_columns if col not in formatted_columns]
    
    if missing_columns:
        gui_object.log(
            level="Critical",
            message="Data Dictionary is missing the following fields:\n\t" + "\n\t".join(missing_columns),
            flush=True
        )
        raise ValueError("Data Dictionary missing required columns")

    for i, row in enumerate(all_rows, 1):
        try:
            if not any(cell.strip() for cell in row):
                continue

            parseDictionaryRow(row, dictionary, formatted_columns)

        except Exception as e:
            gui_object.log(level="error", message=f"Error processing row {i}: {str(e)}", flush=True)
            continue

    for table_name, table_info in dictionary["tables"].items():
        mappings = table_info.get("mappings", {})
        na_columns = mappings.get("NA", [])

        if isinstance(na_columns, list):
            na_columns = [x for sub in (x if isinstance(x, list) else [x] for x in na_columns) for x in sub]

    return dictionary
