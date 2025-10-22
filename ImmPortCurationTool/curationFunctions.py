import ImmPortCurationTool.immport_gui as ig

import pandas as pd
import io
import os
import re
import json
import numpy as np
import zipfile 
import gc
from IPython.display import display

pd.options.display.max_columns = 400
pd.options.display.max_rows = 200

missingVisits_all = {}


def apply_visit_mapping(df_column, planned_visit_map=None, default_visit=None):

    df_column = df_column.fillna("").astype(str)
    if planned_visit_map is None:
        planned_visit_map = {}

    def mapper(val):

        val_strip = val.strip()

        if val_strip in planned_visit_map:
            return planned_visit_map[val_strip]
        elif default_visit is not None:
            return default_visit
        else:
            return np.nan  

    return df_column.map(mapper)

def readFileFromZip(dir, zip, file, gui=None, case_sensitive=False):

    from itertools import islice

    if zip.endswith('.zip'):
        zip = zip[:-4]
    dir = os.path.normpath(dir) + os.sep
    zip_path = f"{dir}{zip}.zip"

    ENCODINGS = ['utf-8', 'utf-16', 'cp1252']

    try:
        with zipfile.ZipFile(zip_path) as myzip:
         
            target_file = None
            for actual_path in myzip.namelist():
                actual_file = os.path.basename(actual_path)

                if (case_sensitive and actual_file == file) or \
                   (not case_sensitive and actual_file.lower() == file.lower()):
                    target_file = actual_path
                    break

            if not target_file:

                if gui:
                    gui.log(f"File '{file}' not found in ZIP", level="error")

                return None

            with myzip.open(target_file) as myfile:
                raw_content = myfile.read()

                content_str = None
                for encoding in ENCODINGS:
                    try:
                        content_str = raw_content.decode(encoding)
                        break
                    except UnicodeDecodeError:
                        continue

                if content_str is None:

                    if gui:
                        gui.log(f"Failed to decode {file} with common encodings", level="error")

                    return None

                sample = '\n'.join(list(islice(io.StringIO(content_str), 5)))
                tab_count = sample.count('\t')
                comma_count = sample.count(',')

                delimiter = '\t' if tab_count > 0 else ','

                if gui:
                    gui.log(f"Reading {file} with delimiter={repr(delimiter)}", level="debug")

                return pd.read_csv(
                    io.StringIO(content_str),
                    sep=delimiter,
                    engine='python',
                    on_bad_lines='warn'
                )

    except zipfile.BadZipFile:
        if gui:
            gui.log(f"Invalid ZIP file: {zip_path}", level="error")
        return None
    
    except Exception as e:
        if gui:
            gui.log(f"Error reading {file}: {str(e)}", level="error")
        return None

def addVisitAccessionFromName(planned_visits, table, visit_col, dictionary, file_table, default_visit):

    global missingVisits_all

    dict_visits = dict(zip(
        planned_visits["NAME"].astype(str).str.strip().str.lower(),
        planned_visits["PLANNED_VISIT_ACCESSION"].astype(str)
    ))

    if visit_col not in table.columns:
        raise ValueError(f"'{visit_col}' not found in table {file_table}")

    table_visits = table[[visit_col]].drop_duplicates().copy()
    table_visits["plannedVisit"] = ""

    dict_field = dictionary["tables"].get(file_table, {}).get("fields", {}).get(visit_col, {})
    visit_map = dict_field.get("map_to_visit") or {}
    code_values = dict_field.get("values") or {}

    if isinstance(visit_map, str):
        try:
            visit_map = json.loads(visit_map)
        except Exception as e:
            visit_map = {}

    for idx, row in table_visits.iterrows():
        raw_value = str(row[visit_col]).strip()
        mapped_value = raw_value

        seen = set()
        
        while mapped_value in visit_map and mapped_value not in seen:
            seen.add(mapped_value)
            mapped_value = visit_map[mapped_value]

        if mapped_value not in dict_visits and raw_value in code_values:
            intermediate = code_values.get(raw_value, raw_value)
            mapped_value = visit_map.get(intermediate, intermediate)

        planned_visit_accession = dict_visits.get(mapped_value.lower())
        
        if not planned_visit_accession and default_visit:
            planned_visit_accession = dict_visits.get(default_visit.lower())
        if not planned_visit_accession:
            planned_visit_accession = "UnknownVisit"

        table_visits.at[idx, "plannedVisit"] = planned_visit_accession

    visit_lookup = dict(zip(
        table_visits[visit_col].astype(str).str.strip().str.lower(),
        table_visits["plannedVisit"]
    ))
    
    table["PLANNED_VISIT_ID"] = table[visit_col].astype(str).str.strip().str.lower().map(visit_lookup).fillna("UnknownVisit")

    return table_visits

def readStudyFile(filepath, file_table, dictionary):

    raw_mappings = dictionary["tables"][file_table].get("mappings", {})

    mappings = {}
    for k, v in raw_mappings.items():
        if isinstance(k, list):
            k_str = ",".join(str(x) for x in k)
        else:
            k_str = str(k)

        if isinstance(v, list):
            v_safe = [str(item) for item in v]  
        else:
            v_safe = str(v)

        mappings[k_str] = v_safe

    if filepath.lower().endswith(".txt"):
        datafile = pd.read_csv(filepath, sep="\t")
    elif filepath.lower().endswith(".csv"):
        datafile = pd.read_csv(filepath)
    elif filepath.lower().endswith(".xlsx"):
        datafile = pd.read_excel(filepath)
    else:
        raise ValueError(f"Unsupported file type: {filepath}")

    return datafile

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

def createColumnMappingDict(dictionary, table_name):

    mappings = {
        "PLANNED_VISIT_ID": "Planned Visit ID"
    }

    if table_name not in dictionary["tables"]:
        
        return mappings

    table_data = dictionary["tables"][table_name]
    dd_mappings = table_data.get("mappings", {})

    for key, original_col in dd_mappings.items():

        if not original_col or str(original_col).strip().upper() == "NA":
            continue 

        if isinstance(original_col, list):
            if len(original_col) > 0:
                original_col = original_col[0]
            else:
                continue

        clean_key = key.strip("[]")
        clean_key_upper = clean_key.upper()

        if clean_key_upper == "STUDY DAY":
            mappings[str(original_col)] = "Study Day"
        elif clean_key_upper == "VISIT":
            mappings[str(original_col)] = "Visit"
        elif clean_key_upper == "CATEGORY":
            continue  
        elif clean_key_upper == "USER DEFINED ID":
            mappings[str(original_col)] = "User Defined ID"
        elif clean_key_upper == "STUDY TIME":
            mappings[str(original_col)] = "Study Time"
        else:
            mappings[str(original_col)] = clean_key

    return mappings

def datafileToComponents(datafile, dictionary, table_name_array, components_template, template, panel_id=-1, workspace_id=9999, planned_visits=None, col_units={}, default_visit_name=None):

    def is_valid_date(date_str):
        date_patterns = [
            r'^\d{1,2}-\d{1,2}-\d{2,4}$',
            r'^\d{1,2}/\d{1,2}/\d{2,4}$',
            r'^\d{1,2}\.\d{1,2}\.\d{2,4}$',
            r'^\d{1,2} \d{1,2} \d{2,4}$',
            r'^\d{4}-\d{1,2}-\d{1,2}$',
            r'^\d{4}/\d{1,2}/\d{1,2}$',
            r'^\d{1,2}-[A-Za-z]{3,9}-\d{2,4}$',
            r'^\d{1,2}/[A-Za-z]{3,9}/\d{2,4}$',
            r'^[A-Za-z]{3,9}-\d{1,2}-\d{2,4}$',
            r'^[A-Za-z]{3,9} \d{1,2}, \d{4}$',
            r'^\d{6}$',
            r'^\d{8}$',
            r'^\d{1,2}-[A-Za-z]{3,9}$',
            r'^[A-Za-z]{3,9}-\d{4}$',
            r'^\d{4}$',
            r'^\d{1,2}-\d{1,2}-\d{2,4} \d{1,2}:\d{2}$',
            r'^\d{4}-\d{1,2}-\d{1,2}T\d{2}:\d{2}:\d{2}$'
        ]
        return any(re.match(pattern, date_str) for pattern in date_patterns)
    
    def normalize_for_mapping(val):

        if pd.isna(val):
            return val
        
        if isinstance(val, float) and val.is_integer():
            return str(int(val))
        
        return str(val).strip()
    
    def extract_candidates(val):

        if val is None:
            return []
        
        if isinstance(val, list):
            candidates = []

            for v in val:
                candidates.extend(extract_candidates(v))

            return candidates
        
        if isinstance(val, dict):
            candidates = []

            for k, v in val.items():
                candidates.extend(extract_candidates(k))
                candidates.extend(extract_candidates(v))

            return candidates
       
        s = str(val).strip()

        if not s:
            return []
      
        s = s.strip()
   
        if s.startswith("[") and s.endswith("]"):
            s = s[1:-1].strip()

        parts = re.split(r'[,\;\|/]', s)
        candidates = []

        for p in parts:
            p2 = p.strip()

            if not p2:
                continue

            candidates.append(p2)

        return candidates

    if template == "assessments":

        components_template.drop(
            components_template[components_template["ASSESSMENT_PANEL_ACCESSION"] == panel_id].index,
            inplace=True
        )

        datafile = datafile.replace(['<NA>', 'NA', 'N/A', 'nan', 'NaN'], np.nan)

        for table_name in table_name_array:

            df_slim_list = [] 
            valid_columns = set(dictionary["tables"][table_name]["fields"].keys())

            fields_dict = dictionary["tables"][table_name]["fields"]

            referenced_fields = set()

            prop_keys_to_check = [
                "unit",
                "study_day",
                "study_day_ref",
                "study_time",
                "study_time_ref",
                "verbatim_question",
                "who_is_assessed",
                "age_onset",
                "age_onset_unit",
                "location"
            ]

            for fname, fprops in fields_dict.items():
                if not isinstance(fprops, dict):
                    continue

                for prop_key in prop_keys_to_check:
                    val = fprops.get(prop_key) or fprops.get(prop_key.lower()) or fprops.get(prop_key.upper())
                    if val is None:
                        continue

                    for cand in extract_candidates(val):
                        cand_norm = cand.strip().lower()
                        if cand_norm.startswith("[") and cand_norm.endswith("]"):
                            cand_norm = cand_norm[1:-1].strip()

                        if cand_norm in {c.lower() for c in fields_dict}:
                            referenced_fields.add(cand_norm)

            raw_category_fields = dictionary["tables"][table_name]["mappings"].get("[Category]", [])

            if isinstance(raw_category_fields, str):
                raw_category_fields = [raw_category_fields]
            elif not isinstance(raw_category_fields, list):
                raw_category_fields = []

            category_fields = {}
            for cat_field in raw_category_fields:
                if cat_field in dictionary["tables"][table_name]["fields"]:
                    cat_meta = dictionary["tables"][table_name]["fields"][cat_field]
                    values_dict = {str(k): v for k, v in cat_meta.get("values", {}).items()}
                    category_fields[cat_field] = {'description': cat_meta["description"], 'values': values_dict}

            col_mappings = createColumnMappingDict(dictionary, table_name)
            for cat_field in category_fields:
                if cat_field in col_mappings:
                    del col_mappings[cat_field]

            renamed_datafile = datafile.rename(columns=col_mappings)

            if "Planned Visit ID" in renamed_datafile.columns and planned_visits is not None:
             
                def normalize_visit_name(name):
                    
                    if pd.isna(name):
                        return None
                    
                    return str(name).strip().lower()

                renamed_datafile["Planned Visit ID"] = renamed_datafile["Planned Visit ID"].astype(str)

                visit_col_props = dictionary["tables"][table_name]["fields"].get("event", {})
                value_map = visit_col_props.get("map_to_visit", {})

                if value_map:
                    mapped_visits = renamed_datafile["Planned Visit ID"].map(value_map).fillna(renamed_datafile["Planned Visit ID"])
                else:
                    mapped_visits = renamed_datafile["Planned Visit ID"]

                def is_accession(val):
                    
                    if pd.isna(val):
                        return False
                    
                    return re.match(r"^PV\d+$", str(val)) is not None

                planned_visit_map = {normalize_visit_name(k): v for k, v in zip(planned_visits["NAME"], planned_visits["PLANNED_VISIT_ACCESSION"])}

                final_pv = []
                
                for val in mapped_visits:
                    if is_accession(val):
                        final_pv.append(val)
                    else:
                        final_pv.append(planned_visit_map.get(normalize_visit_name(val), "UnknownVisit"))

                renamed_datafile["Planned Visit ID"] = final_pv

            na_mapped_columns = set()
            raw_na = dictionary["tables"][table_name]["mappings"].get("NA", [])
            
            def flatten_to_str_list(x):
                
                if isinstance(x, list):
                    result = []
                    for item in x:
                        result.extend(flatten_to_str_list(item))
                    return result
                else:
                    return [str(x).strip().upper()]
                
            for item in flatten_to_str_list(raw_na):
                na_mapped_columns.add(item)

            # Question field 
            question_cols = {field: props for field, props in dictionary["tables"][table_name]["fields"].items()
                            if props.get("question", False)}

            for col, col_props in question_cols.items():
                col_upper = col.strip().upper()
                
                if col_upper in na_mapped_columns:
                    continue

                if col.strip().lower() in referenced_fields:
                    continue
    
                if col in renamed_datafile and col not in category_fields:

                    required_cols = ['User Defined ID', 'Planned Visit ID', col] + list(category_fields.keys())
                    required_cols = [str(x) for x in required_cols]

                    df_slim = renamed_datafile[required_cols].copy()

                    df_slim.rename(columns={'Planned Visit ID': 'Planned Visit ID'}, inplace=True)

                    if col in df_slim.columns:
                        series = df_slim[col]
                        
                        try:
                            series_str = series.astype("string")
                        except Exception as e:
                            continue
                        
                        try:
                            stripped = series_str.str.strip()
                        except Exception as e:
                            continue
                        
                        stripped = stripped.replace(
                            {"nan": pd.NA, "NaN": pd.NA, "None": pd.NA, "<NA>": pd.NA}
                        )
                        
                        non_empty = stripped.dropna()
                        
                        if non_empty.empty:
                            continue
                    else:
                        continue
                        
                    # Map to Planned Visit
                    map_to_visit_val = col_props.get("map_to_visit")

                    if not map_to_visit_val or str(map_to_visit_val).strip() == "":
                        planned_visit_map = {}
                    else:
                        try:
                            planned_visit_map = json.loads(map_to_visit_val)
                    
                        except json.JSONDecodeError:
                            planned_visit_map = {}

                    value_map = col_props.get("values", {})

                    if value_map and planned_visit_map and col in df_slim.columns:
                        intermediate_series = df_slim[col].astype(str).map(value_map).fillna(df_slim[col])
                        remapped = intermediate_series.map(planned_visit_map)
                        
                        if remapped.notna().any():
                            df_slim["Planned Visit ID"] = remapped.combine_first(df_slim["Planned Visit ID"])

                    # Study time
                    override_study_time = col_props.get("study_time", "").strip()
                    study_time_ref = col_props.get("study_time_ref", "").strip()
                    study_time_value = None

                    if override_study_time.lower() in ["same", "self"]:
                        mapped_col = dictionary["tables"][table_name]["mappings"].get("[Study Time]", "")
                        resolved_col = col_mappings.get(mapped_col, mapped_col)
                        
                        if resolved_col in renamed_datafile.columns:
                            study_time_value = renamed_datafile[resolved_col]
                            
                    elif override_study_time in renamed_datafile.columns:
                        study_time_value = renamed_datafile[override_study_time]
                    elif override_study_time:
                        study_time_value = override_study_time
                    elif study_time_ref:
                        resolved_col = col_mappings.get(study_time_ref, study_time_ref)
                        
                        if resolved_col in renamed_datafile.columns:
                            study_time_value = renamed_datafile[resolved_col]
                            
                    elif "[Study Time]" in dictionary["tables"][table_name]["mappings"]:
                        mapped_col = dictionary["tables"][table_name]["mappings"]["[Study Time]"]
                        
                        if mapped_col in datafile.columns:
                            study_time_value = datafile[mapped_col]

                    if isinstance(study_time_value, pd.Series):
                        df_slim["Time Of Day"] = study_time_value
                    elif isinstance(study_time_value, str) and study_time_value.strip():
                        df_slim["Time Of Day"] = study_time_value

                    # Study day
                    planned_visits_ids = planned_visits["PLANNED_VISIT_ACCESSION"].astype(str).str.strip().str.upper()
                    visit_map = dict(zip(planned_visits_ids, planned_visits["MIN_START_DAY"]))
                    default_min_day = planned_visits["MIN_START_DAY"].min()

                    df_slim["Study Day"] = np.nan

                    override_study_day = str(col_props.get("study_day", "")).strip()
                    if override_study_day:
                        if override_study_day in renamed_datafile.columns:
                            df_slim.loc[renamed_datafile[override_study_day].notna(), "Study Day"] = renamed_datafile[override_study_day]
                        elif re.match(r"^-?\d*\.?\d+$", override_study_day):
                            df_slim["Study Day"] = float(override_study_day)
                        else:
                            df_slim["Study Day"] = override_study_day

                    if "[Study Day]" in dictionary["tables"][table_name]["mappings"]:
                        mapped_col = dictionary["tables"][table_name]["mappings"]["[Study Day]"]
                        resolved_col = col_mappings.get(mapped_col, mapped_col)
                        if resolved_col in renamed_datafile.columns:
                            df_slim.loc[df_slim["Study Day"].isna(), "Study Day"] = renamed_datafile[resolved_col]

                    if "[Visit]" in dictionary["tables"][table_name]["mappings"]:
                        visit_cols = [c for c in renamed_datafile.columns if c.upper() in ["PLANNED VISIT ID","PLANNED_VISIT_ID","VISIT_ID","VISIT"]]
                        if visit_cols:
                            visit_col = visit_cols[0]
                            df_slim.loc[df_slim["Study Day"].isna(), "Study Day"] = (
                                renamed_datafile.loc[df_slim.index, visit_col]
                                .map(lambda x: visit_map.get(str(x).strip().upper(), default_min_day))
                            )

                    df_slim["Study Day"] = df_slim["Study Day"].fillna(99999)
       
                    col_props = dictionary["tables"][table_name]["fields"][col]

                    def normalize_key_for_codelist(k):
                        try:
                            f = float(k)
                            
                            if f.is_integer():
                                return str(int(f))
                            else:
                                return str(f).rstrip('0').rstrip('.') if '.' in str(f) else str(f)
                     
                        except Exception:
                            return str(k).strip()

                    codelist_raw = col_props.get("values", {}) or {}
                    
                    if not isinstance(codelist_raw, dict):
                        try:
                            codelist_raw = dict(codelist_raw)
                        except Exception:
                            codelist_raw = {}

                    codelist = { normalize_key_for_codelist(k): str(v).strip() for k, v in codelist_raw.items() }

                    def normalize_for_mapping(val):

                        if pd.isna(val):
                            return None

                        if isinstance(val, float) and val.is_integer():
                            return str(int(val))
                        
                        try:
                            s = str(val).strip()
                            f = float(s)
                            if f.is_integer():
                                return str(int(f))
                            s2 = str(f)
                            
                            if '.' in s2:
                                s2 = s2.rstrip('0').rstrip('.')
                                
                            return s2
                        
                        except Exception:
                            return str(val).strip()

                    norm_series = df_slim[col].apply(normalize_for_mapping)

                    mapped = norm_series.map(codelist)  

                    fallback = norm_series.apply(lambda x: str(x).strip() if x is not None else x)

                    df_slim["Result Value Reported"] = mapped.fillna(fallback)

                    df_slim["Result Value Reported"] = df_slim["Result Value Reported"].astype(object)  

                    df_slim = df_slim[~df_slim["Result Value Reported"].isna()]                  
                    df_slim = df_slim[df_slim["Result Value Reported"].apply(lambda x: str(x).strip() != "")]  

                    df_slim["Result Value Reported"] = df_slim["Result Value Reported"].astype(str)

                    if not df_slim.empty:

                        # Name Reported
                        name_parts = []
                        for cat_field, cat_data in category_fields.items():
                            code_values = df_slim[cat_field].apply(lambda x: cat_data["values"].get(str(x), str(x)))
                            name_parts.append(code_values.astype(str).str.lower())

                        field_desc = col_props["description"].lower().replace(" ", "-")
                        name_parts.append(field_desc)

                        df_slim["Name Reported"] = df_slim.index.map(
                            lambda i: "-".join([str(part[i]) if isinstance(part, pd.Series) else str(part) for part in name_parts])
                        )

                        # Verbatim Question
                        verbatim_q = (col_props.get("verbatim_question", "") or col_props.get("verbatim question", ""))
                        verbatim_q = verbatim_q.strip() if isinstance(verbatim_q, str) else ""

                        if verbatim_q:
                            
                            if verbatim_q.lower() == "same":
                                df_slim["Verbatim Question"] = col_props["description"]
                            else:
                                match = next((c for c in renamed_datafile.columns if c.lower() == verbatim_q.lower()), None)

                                if match:
                                    raw_values = renamed_datafile[match]

                                    fields_dict = dictionary["tables"][table_name]["fields"]
                                    referenced_col_props = next(
                                        (props for field_name, props in fields_dict.items() if field_name.lower() == verbatim_q.lower()),
                                        {}
                                    )

                                    values_dict = {str(k).strip().lower(): v for k, v in referenced_col_props.get("values", {}).items()}

                                    if values_dict:
                                        normalized_raw = (
                                            raw_values.astype(str)
                                            .str.replace(r"\.0$", "", regex=True)
                                            .str.strip()
                                            .str.lower()
                                        )
                                        
                                        mapped_values = normalized_raw.map(values_dict).fillna(raw_values)
                                        df_slim["Verbatim Question"] = mapped_values
            
                                    else:
                                        df_slim["Verbatim Question"] = raw_values
    
                                else:
                      
                                    df_slim["Verbatim Question"] = verbatim_q
            
                        # Who is Assessed
                        who_assessed = (col_props.get("who_is_assessed", "") or col_props.get("who is assessed", ""))
                        who_assessed = who_assessed.strip() if isinstance(who_assessed, str) else ""

                        if who_assessed:
             
                            match = next((c for c in renamed_datafile.columns if c.lower() == who_assessed.lower()), None)

                            if match:
                                raw_values = renamed_datafile[match]

                                fields_dict = dictionary["tables"][table_name]["fields"]
                                referenced_col_props = next(
                                    (props for field_name, props in fields_dict.items() if field_name.lower() == who_assessed.lower()),
                                    {}
                                )

                                values_dict = {str(k).strip().lower(): v for k, v in referenced_col_props.get("values", {}).items()}

                                if values_dict:
                                    normalized_raw = (
                                        raw_values.astype(str)
                                        .str.replace(r"\.0$", "", regex=True)
                                        .str.strip()
                                        .str.lower()
                                    )
                                    mapped_values = normalized_raw.map(values_dict).fillna(raw_values)
                                    df_slim["Who Is Assessed"] = mapped_values
                                else:
                                    df_slim["Who Is Assessed"] = raw_values
                            else:
                                df_slim["Who Is Assessed"] = who_assessed

                        # Location
                        location_field = col_props.get("location", "").strip()

                        if location_field:
            
                            match = next((col for col in renamed_datafile.columns if col.lower() == location_field.lower()), None)

                            if match:
                                raw_values = renamed_datafile[match]

                                fields_dict = dictionary["tables"][table_name]["fields"]
                                referenced_col_props = next(
                                    (props for field_name, props in fields_dict.items() if field_name.lower() == location_field.lower()),
                                    {}
                                )

                                values_dict = {str(k).strip().lower(): v for k, v in referenced_col_props.get("values", {}).items()}

                                if values_dict:
                                    normalized_raw = (
                                        raw_values.astype(str)
                                        .str.replace(r"\.0$", "", regex=True)
                                        .str.strip()
                                        .str.lower()
                                    )
                                    mapped_values = normalized_raw.map(values_dict).fillna(raw_values)
                                    df_slim["Organ Or Body System Reported"] = mapped_values
                                else:
                                    df_slim["Organ Or Body System Reported"] = raw_values
                            else:
                                df_slim["Organ Or Body System Reported"] = location_field

                        # Age At Onset 
                        age_onset_field = col_props.get("age_onset", "").strip()
   
                        if age_onset_field:
                            match = next((c for c in renamed_datafile.columns if c.lower() == age_onset_field.lower()), None)

                            if match:
                                raw_values = renamed_datafile[match]

                                fields_dict = dictionary["tables"][table_name]["fields"]
                                referenced_col_props = next(
                                    (props for field_name, props in fields_dict.items() if field_name.lower() == age_onset_field.lower()),
                                    {}
                                )

                                values_dict = {str(k).strip().lower(): v for k, v in referenced_col_props.get("values", {}).items()}

                                if values_dict:
                                    normalized_raw = (
                                        raw_values.astype(str)
                                        .str.replace(r"\.0$", "", regex=True)
                                        .str.strip()
                                        .str.lower()
                                    )
                                    mapped_values = normalized_raw.map(values_dict).fillna(raw_values)
                                    df_slim["Age At Onset Reported"] = mapped_values
        
                                else:
                                    df_slim["Age At Onset Reported"] = raw_values
            
                            else:
                                df_slim["Age At Onset Reported"] = age_onset_field
              
                        # Age At Onset Unit
                        age_onset_unit_field = col_props.get("age_onset_unit", "").strip()
   
                        if age_onset_unit_field:
               
                            match = next((c for c in renamed_datafile.columns if c.lower() == age_onset_unit_field.lower()), None)

                            if match:
                                raw_values = renamed_datafile[match]

                                fields_dict = dictionary["tables"][table_name]["fields"]
                                referenced_col_props = next(
                                    (props for field_name, props in fields_dict.items() if field_name.lower() == age_onset_unit_field.lower()),
                                    {}
                                )

                                values_dict = {str(k).strip().lower(): v for k, v in referenced_col_props.get("values", {}).items()}

                                if values_dict:
                                    normalized_raw = (
                                        raw_values.astype(str)
                                        .str.replace(r"\.0$", "", regex=True)
                                        .str.strip()
                                        .str.lower()
                                    )
                                    mapped_values = normalized_raw.map(values_dict).fillna(raw_values)
                                    df_slim["Age At Onset Unit Reported"] = mapped_values
                                else:
                                    df_slim["Age At Onset Unit Reported"] = raw_values
                            else:
                            
                                df_slim["Age At Onset Unit Reported"] = age_onset_unit_field

                        # Unit
                        unit_info = col_props.get("unit", "").strip()
                        
                        if unit_info:
                            if unit_info in valid_columns:
                                df_slim['Result Unit Reported'] = renamed_datafile[unit_info]
                            elif unit_info.upper().strip("[]") == "SPLIT":
                                split_values = df_slim['Result Value Reported'].str.split(" ", n=1, expand=True)
                                df_slim['Result Value Reported'] = split_values[0]
                                df_slim['Result Unit Reported'] = split_values[1]
                            elif unit_info.startswith("[") and unit_info.endswith("]"):
                                unit_col = unit_info[1:-1]
                                
                                if unit_col in renamed_datafile:
                                    df_slim['Result Unit Reported'] = renamed_datafile[unit_col]
                                else:
                                    df_slim['Result Unit Reported'] = ""
                            else:
                                df_slim['Result Unit Reported'] = unit_info
                        else:
                            code_mapping = col_props.get("values", {})
                         
                            code_descriptions = set(str(v).upper() for v in code_mapping.values())
                            
                            if {'YES', 'NO'}.issubset(code_descriptions):
                                df_slim['Result Unit Reported'] = 'Yes, No, or Unknown Response'
                            elif {'MALE', 'FEMALE'}.issubset(code_descriptions):
                                df_slim['Result Unit Reported'] = 'Gender'
                            elif len(code_descriptions) == 2:
                                df_slim['Result Unit Reported'] = 'Boolean'
                            elif code_descriptions:
                                df_slim['Result Unit Reported'] = 'categorical'
                            else:
                                df_slim['Result Unit Reported'] = ''

                        if "User Defined ID" in df_slim.columns:
                            df_slim = df_slim[
                                df_slim["User Defined ID"]
                                .astype(str)
                                .str.strip()
                                .replace({"nan": "", "None": "", "NONE": ""})
                                != ""
                            ]

                        for col in components_template.columns:
                            if col not in df_slim.columns:
                                df_slim[col] = ""  
                        
                        df_slim_list.append(df_slim)

                        del df_slim
                        gc.collect()

            if df_slim_list:
                components_template = pd.concat([components_template] + df_slim_list, ignore_index=True)

                exclude_cols = ['Result Value Reported']
                columns_to_clean = [c for c in components_template.columns if c not in exclude_cols]

                components_template[columns_to_clean] = components_template[columns_to_clean].replace(
                    ['<NA>', 'NA', 'N/A', 'nan', 'NaN', 'None', 'NONE', np.nan],
                    ''
                )

                if "Age At Onset Reported" in components_template.columns and "Age At Onset Unit Reported" in components_template.columns:
                    mask = components_template["Age At Onset Reported"].astype(str).str.strip() == ''
                    components_template.loc[mask, "Age At Onset Unit Reported"] = ''

                components_template = components_template.loc[
                    ~(components_template.apply(lambda row: all(str(v).strip() == '' for v in row), axis=1))
                ].reset_index(drop=True)

    if template == "labTests":

        components_template.drop(
            components_template[components_template["LAB_TEST_PANEL_ACCESSION"] == panel_id].index,
            inplace=True
        )

        datafile = datafile.replace(['<NA>', 'NA', 'N/A', '', 'nan', 'NaN'], np.nan)

        for table_name in table_name_array:

            raw_category_fields = dictionary["tables"][table_name]["mappings"].get("[Category]", [])

            if isinstance(raw_category_fields, str) and raw_category_fields:
                raw_category_fields = [raw_category_fields]
            elif not isinstance(raw_category_fields, list):
                raw_category_fields = []

            category_fields = {}
            for cat_field in raw_category_fields:
                
                if cat_field in dictionary["tables"][table_name]["fields"]:
                    cat_meta = dictionary["tables"][table_name]["fields"][cat_field]
                    values_dict = {str(k): v for k, v in cat_meta.get("values", {}).items()}
                    category_fields[cat_field] = {
                        'description': cat_meta["description"],
                        'values': values_dict
                    }

            col_mappings = createColumnMappingDict(dictionary, table_name)

            for cat_field in category_fields:
                if cat_field in col_mappings:
                    del col_mappings[cat_field]

            datafile.rename(columns=col_mappings, inplace=True)
  
            cols_to_drop = [col for col in datafile.columns if col.strip().upper() == 'NA']
            
            if cols_to_drop:
                datafile.drop(columns=cols_to_drop, inplace=True)

            planned_visit_col = 'Planned Visit ID' if 'Planned Visit ID' in datafile.columns else 'PLANNED_VISIT_ID'

            raw_na = dictionary["tables"][table_name]["mappings"].get("NA", [])

            def flatten_to_str_list(x):
                
                if isinstance(x, list):
                    result = []
                    for item in x:
                        result.extend(flatten_to_str_list(item))
                    return result
                else:
                    return [str(x).strip().upper()]

            na_mapped_fields = set(flatten_to_str_list(raw_na))

            table_fields = dictionary["tables"].get(table_name, {}).get("fields", {})
            
            if not isinstance(table_fields, dict):
                ig.main_logger.write(level="error", message=f"❌ 'fields' missing or not a dict for table {table_name}")
                continue  

            prop_keys_to_check = [
                "unit",
                "study_day",
                "study_day_ref",
                "study_time",
                "study_time_ref"
            ]

            valid_cols_lc = {c.strip().lower() for c in table_fields.keys()}
            referenced_fields = set()
            
            for fname, fprops in table_fields.items():
                
                if not isinstance(fprops, dict):
                    continue
                
                for prop_key in prop_keys_to_check:
                    if prop_key in fprops:
                        val = fprops.get(prop_key)
                    else:
                        val = None
                        
                    if val is None:
                        continue
                    
                    for cand in extract_candidates(val):
                        
                        cand_norm = cand.strip().lower()
                        
                        if cand_norm.startswith("[") and cand_norm.endswith("]"):
                            cand_norm = cand_norm[1:-1].strip()
                            
                        if cand_norm in valid_cols_lc:
                            referenced_fields.add(cand_norm)

            question_cols = {
                field: props
                for field, props in table_fields.items()
                if props.get("question", False) and field.strip().upper() not in na_mapped_fields
            }

            for col, col_props in question_cols.items():

                col_upper = col.strip().upper()
     
                if col_upper in na_mapped_fields:
                    continue        

                if col.strip().lower() in referenced_fields:
                    continue
                    
                if col in datafile and col not in category_fields:
                    
                    required_cols = ['User Defined ID', planned_visit_col, col] + list(category_fields.keys())

                    required_cols = [str(x) for x in required_cols]

                    df_slim = datafile[required_cols].copy()
                    df_slim.rename(columns={'Planned Visit ID': 'Planned Visit ID'}, inplace=True)

                    if col in df_slim.columns:
                        
                        series = df_slim[col]
                        
                        try:
                            series_str = series.astype("string")
                        except Exception as e:
                            continue
                        
                        try:
                            stripped = series_str.str.strip()
                        except Exception as e:
                            continue
                        
                        stripped = stripped.replace(
                            {"nan": pd.NA, "NaN": pd.NA, "None": pd.NA, "<NA>": pd.NA}
                        )
                        
                        non_empty = stripped.dropna()
                        
                        if non_empty.empty:
                            continue
                    else:
                        continue

                    df_slim['LAB_TEST_PANEL_ACCESSION'] = panel_id
                    df_slim['WORKSPACE_ID'] = workspace_id

                    col_props = dictionary["tables"][table_name]["fields"][col]

                    def normalize_key_for_codelist(k):
                        try:
                            f = float(k)
                            
                            if f.is_integer():
                                return str(int(f))
                            else:
                                return str(f).rstrip('0').rstrip('.') if '.' in str(f) else str(f)
                     
                        except Exception:
                            return str(k).strip()

                    codelist_raw = col_props.get("values", {}) or {}
                    
                    if not isinstance(codelist_raw, dict):
                        try:
                            codelist_raw = dict(codelist_raw)
                        except Exception:
                            codelist_raw = {}

                    codelist = { normalize_key_for_codelist(k): str(v).strip() for k, v in codelist_raw.items() }

                    def normalize_for_mapping(val):

                        if pd.isna(val):
                            return None
                        
                        if isinstance(val, float) and val.is_integer():
                            return str(int(val))
                        
                        try:
                            s = str(val).strip()
                            f = float(s)

                            if f.is_integer():
                                return str(int(f))
                            
                            s2 = str(f)
                            
                            if '.' in s2:
                                s2 = s2.rstrip('0').rstrip('.')

                            return s2
                        
                        except Exception:
                            return str(val).strip()

                    norm_series = df_slim[col].apply(normalize_for_mapping)

                    mapped = norm_series.map(codelist)  

                    fallback = norm_series.apply(lambda x: str(x).strip() if x is not None else x)

                    df_slim["Result Value Reported"] = mapped.fillna(fallback)

                    df_slim["Result Value Reported"] = df_slim["Result Value Reported"].astype(object) 

                    df_slim = df_slim[~df_slim["Result Value Reported"].isna()]                   
                    df_slim = df_slim[df_slim["Result Value Reported"].apply(lambda x: str(x).strip() != "")]  

                    df_slim["Result Value Reported"] = df_slim["Result Value Reported"].astype(str)

                    if not df_slim.empty:

                        # Name Reported
                        name_parts = []
                        for cat_field, cat_data in category_fields.items():
                            code_values = df_slim[cat_field].apply(lambda x: cat_data["values"].get(str(x), str(x)))
                            name_parts.append(code_values.astype(str).str.lower())

                        field_desc = col_props["description"].lower().replace(" ", "-")
                        name_parts.append(field_desc)

                        df_slim["Name Reported"] = df_slim.index.map(
                            lambda i: "-".join([str(part[i]) if isinstance(part, pd.Series) else str(part) for part in name_parts])
                        )

                    # Map To Planned Visit
                    map_to_visit_col_raw = dictionary["tables"][table_name]["mappings"].get("[Map To Planned Visit]", "")

                    if map_to_visit_col_raw:
                        map_to_visit_cols = [map_to_visit_col_raw] if isinstance(map_to_visit_col_raw, str) else map_to_visit_col_raw

                        for map_col in map_to_visit_cols:
     
                            if map_col in datafile.columns:
                                visit_name_to_accession = dict(zip(
                                    planned_visits["VISIT_NAME"].astype(str).str.upper().str.strip(),
                                    planned_visits["PLANNED_VISIT_ACCESSION"].astype(str).str.upper().str.strip()
                                ))

                                mapped_visit_ids = datafile[map_col].astype(str).str.upper().str.strip().map(visit_name_to_accession)
    
                                df_slim['Planned Visit ID'] = mapped_visit_ids.fillna(df_slim['Planned Visit ID'])

                    override_study_time = str(col_props.get("study_time", "")).strip()

                    values_raw = col_props.get("values", None)

                    code_mapping = values_raw if isinstance(values_raw, dict) else {}

                    code_descriptions = set(str(v).upper() for v in code_mapping.values())

                    # Study time collected
                    df_slim["Study Time Collected"] = np.nan

                    override_study_day = str(col_props.get("study_day", "")).strip()
                    if override_study_day:
                        if override_study_day in datafile.columns:
                            df_slim.loc[datafile[override_study_day].notna(), "Study Time Collected"] = datafile[override_study_day]
                        elif re.match(r'^-?\d*\.?\d+$', override_study_day):
                            df_slim.loc[df_slim["Study Time Collected"].isna(), "Study Time Collected"] = float(override_study_day)
                        else:
                            df_slim.loc[df_slim["Study Time Collected"].isna(), "Study Time Collected"] = override_study_day

                    if "[Study Day]" in dictionary["tables"][table_name]["mappings"]:
                        mapped_col = dictionary["tables"][table_name]["mappings"]["[Study Day]"]
                        resolved_col = col_mappings.get(mapped_col, mapped_col)
                        if resolved_col in datafile.columns:
                            df_slim.loc[df_slim["Study Time Collected"].isna(), "Study Time Collected"] = datafile[resolved_col]

                    planned_visit_col = 'Planned Visit ID' if 'Planned Visit ID' in datafile.columns else 'PLANNED_VISIT_ID'
                    visit_day_mapping = dict(zip(
                        planned_visits["PLANNED_VISIT_ACCESSION"].astype(str).str.strip().str.upper(),
                        planned_visits["MIN_START_DAY"]
                    ))
                    df_slim.loc[df_slim["Study Time Collected"].isna(), "Study Time Collected"] = (
                        datafile[planned_visit_col].astype(str).str.strip().str.upper().map(visit_day_mapping)
                    )

                    df_slim["Study Time Collected"] = df_slim["Study Time Collected"].fillna(99999)

                    if pd.api.types.is_numeric_dtype(df_slim["Study Time Collected"]):
                        df_slim["Study Time Collected Unit"] = "Days"
                    else:
                        df_slim["Study Time Collected Unit"] = "Not Specified"

                    unit_assigned = False

                    unit_info = col_props.get("unit", "")

                    if unit_info:

                        if unit_info.upper().strip("[]") == "SPLIT":
                            split_values = df_slim['Result Value Reported'].str.split(" ", n=1, expand=True)
                            df_slim['Result Value Reported'] = split_values[0]
                            df_slim['Result Unit Reported'] = split_values[1]
                            unit_assigned = True

                        elif unit_info.startswith("[") and unit_info.endswith("]"):
                            unit_col = unit_info[1:-1]

                            if unit_col in datafile:
                                df_slim['Result Unit Reported'] = datafile[unit_col]
                                unit_assigned = True

                            else:
                                df_slim['Result Unit Reported'] = ""

                        else:
                            df_slim['Result Unit Reported'] = unit_info
                            unit_assigned = True

                    if not unit_assigned:

                        col_props = dictionary["tables"][table_name]["fields"].get(col, {})

                        code_mapping = col_props.get("values", {})

                        code_descriptions = set(str(v).upper() for v in code_mapping.values())
    
                        if {'YES', 'NO'}.issubset(code_descriptions) and code_descriptions.issubset(
                            {'YES', 'NO', 'UNKNOWN', 'NA', "N/A", 'NOT APPLICABLE', 
                            'NOTAPPLICABLE', 'NOT AVAILABLE', 'NOTAVAILABLE', ''}):
                            df_slim['Result Unit Reported'] = 'Yes, No, or Unknown Response'
                        
                        elif {'MALE', 'FEMALE'}.issubset(code_descriptions) and code_descriptions.issubset(
                            {'MALE', 'FEMALE', 'NONBINARY', 'NON-BINARY', 
                            'TRANSGENDER', 'UNKNOWN', 'OTHER', ''}):
                            df_slim['Result Unit Reported'] = 'Gender'

                        elif len(code_descriptions) == 2:
                            df_slim['Result Unit Reported'] = 'Boolean'
                        
                        elif code_descriptions:
                            df_slim['Result Unit Reported'] = 'categorical'

                    df_slim = df_slim[~df_slim['Result Value Reported'].isna()]

                    if "User Defined ID" in df_slim.columns:
                        df_slim = df_slim[
                            df_slim["User Defined ID"]
                            .astype(str)
                            .str.strip()
                            .replace({"nan": "", "None": "", "NONE": ""})
                            != ""
                        ]

                    if not df_slim.empty:

                        if 'Result Unit Reported' not in components_template.columns:
                            components_template['Result Unit Reported'] = ''

                        df_slim = df_slim.fillna('')
                
                        components_template = pd.concat([components_template, df_slim], ignore_index=True, sort=False)

                        exclude_cols = ['Result Value Reported']
                        columns_to_clean = [c for c in components_template.columns if c not in exclude_cols]

                        components_template[columns_to_clean] = components_template[columns_to_clean].replace(
                            ['<NA>', 'NA', 'N/A', 'nan', 'NaN', 'None', 'NONE', np.nan],
                            ''
                        )
                        components_template = components_template.loc[
                            components_template['Result Value Reported'].astype(str).str.strip() != ''
                        ].reset_index(drop=True)

    return components_template
        
def readAndModifyStudyFile(filepath, file_tables, dictionary, planned_visits, ig=None):

    full_datafile = pd.DataFrame()

    for file_table in file_tables["tables"]:

        datafile = readStudyFile(filepath, file_table, dictionary)

        dd_ID = dictionary["tables"][file_table]["mappings"].get("User Defined ID")

        if isinstance(dd_ID, list):
            dd_ID = dd_ID[0] if len(dd_ID) > 0 else None

        if dd_ID and dd_ID in datafile.columns:
            datafile.rename(columns={dd_ID: "User Defined ID"}, inplace=True)

        visit_col = dictionary["tables"][file_table]["mappings"].get("[Visit]")

        if isinstance(visit_col, list):
            visit_col = visit_col[0] if len(visit_col) > 0 else None

        default_visit = file_tables.get("visit", None)

        if visit_col and visit_col in datafile.columns:
    
            table_visits = addVisitAccessionFromName(planned_visits, datafile, visit_col,
                                                     dictionary, file_table, default_visit)
            if "PLANNED_VISIT_ID" in datafile.columns:
                pv = datafile["PLANNED_VISIT_ID"]
                datafile.drop(columns=["PLANNED_VISIT_ID"], inplace=True)
                datafile.insert(loc=3, column="PLANNED_VISIT_ID", value=pv)
        else:
            if default_visit:
                datafile["Default_Visit_Temp"] = default_visit
                table_visits = addVisitAccessionFromName(planned_visits, datafile, "Default_Visit_Temp",
                                                         dictionary, file_table, default_visit=None)
                if "PLANNED_VISIT_ID" in datafile.columns:
                    pv = datafile["PLANNED_VISIT_ID"]
                    datafile.drop(columns=["PLANNED_VISIT_ID"], inplace=True)
                    datafile.insert(loc=3, column="PLANNED_VISIT_ID", value=pv)
                datafile.drop(columns=["Default_Visit_Temp"], inplace=True)
            else:
                if ig is not None and getattr(ig, "main_logger", None):
                    ig.main_logger.write(level="error", message=f"No visit mapping and no default visit for table {file_table}")

        study_time_col = dictionary["tables"][file_table]["mappings"].get("[Study Time]")
  
        if study_time_col and study_time_col in datafile.columns:
            datafile["Study Time"] = datafile[study_time_col]

        full_datafile = pd.concat([full_datafile, datafile], ignore_index=True)

    return full_datafile
