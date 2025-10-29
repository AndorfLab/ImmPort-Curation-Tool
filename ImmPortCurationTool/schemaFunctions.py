import ImmPortCurationTool.curationFunctions as cf
import ImmPortCurationTool.immport_gui as ig

import os
import jsonschema
import json
import platform
import re
import gc
import pandas as pd
import numpy as np 
from IPython.display import display
from io import StringIO

def sanitize_component(s):

    if s is None:
        s = ""

    s = str(s).strip()
    s = re.sub(r"[^\w\-]", "_", s)      
    s = re.sub(r"_+", "_", s)     

    return s or "NA"

json_schema_template_path   = "json-templates"
txt_template_path           = "txt-templates"

json_schema_template_path_full = os.path.join(os.path.dirname(cf.__file__), json_schema_template_path)
txt_template_path_full = os.path.join(os.path.dirname(cf.__file__), txt_template_path)

try:
    _protocols_file = os.path.join(json_schema_template_path_full, "protocols.json")
    with open(_protocols_file, "r", encoding="utf-8") as fh:
        _protocol_schema = json.load(fh)
    GLOBAL_SCHEMA_VERSION = _protocol_schema["properties"]["schemaVersion"]["enum"][0]
except Exception as e:
    print(f"[DEBUG schemaFunctions] ] Failed to load schemaVersion from {_protocols_file}: {e}")
    GLOBAL_SCHEMA_VERSION = None

last_error =""

def get_schema_store(json_schema_template_path_full):

    schema_store = {}

    for fname in os.listdir(json_schema_template_path_full):
        if fname.endswith(".json"):
            path = os.path.join(json_schema_template_path_full, fname)
            with open(path, "r", encoding="utf-8") as schema_fd:
                schema = json.load(schema_fd)
                schema_store[fname] = schema

    return schema_store

def validate_data(data, schema_name=None, schema_store=None):
    global last_error

    if schema_store is None:
        raise NotImplementedError("Schema store has not been loaded")

    if schema_name is None:
        raise ValueError("Schema name not provided")

    if not schema_name.endswith(".json"):
        schema_name += ".json"

    schema = schema_store.get(schema_name)

    if schema is None:
        raise NotImplementedError(f"Missing Schema for '{schema_name}'")

    ref_resolver_path = os.path.abspath(os.path.join(json_schema_template_path_full, schema_name))

    if platform.system() == 'Windows':
        resolver = jsonschema.RefResolver(ref_resolver_path, schema, store=schema_store)
    else:
        resolver = jsonschema.RefResolver(f"file://{ref_resolver_path}", schema, store=schema_store)

    try:
        jsonschema.Draft4Validator(schema, resolver=resolver).validate(data)
        return True
    
    except jsonschema.exceptions.ValidationError as error:
        path_str = "/".join(map(str, error.schema_path))

        if path_str == "properties/data/items/properties/resultData/items/properties/resultUnitReported/enum":
            return True

        elif path_str == "properties/data/items/properties/resultData/items/properties/plannedVisitId/type":
            if error.cause is None:
                last_error = error
            return True

        else:
            last_error = error
            return f"ValidationError: {error}"
    
    except jsonschema.exceptions.SchemaError as error:
        return f"SchemaError: {error}"

    return False


def is_same_type(value, field_type):

    if value is None or pd.isna(value):
        return (field_type, True)
    
    if isinstance(value, (np.number, np.integer)):
        value = float(value) if isinstance(value, np.floating) else int(value)
    
    if field_type == "string" or field_type == str:

        if isinstance(value, (int, float)):
            return (str, True)
        
        return (str, isinstance(value, str))
    
    elif field_type in ["number", "float"]:
        return (float, isinstance(value, (int, float, np.number)))
    elif field_type == 'integer':
        return (int, isinstance(value, (int, np.integer)))
    elif field_type == 'array' or field_type == list:
        return (list, isinstance(value, list))
    elif field_type == 'boolean':
        return (bool, isinstance(value, bool))
    raise TypeError(f"Type '{field_type}' not handled for value {value} (type: {type(value)})")

def check_data_type(value, key_properties, key):

    field_type = key_properties["type"]

    if field_type in ["number", "integer"] and isinstance(value, str):
        try:
            if field_type == "integer":
                value = int(value)
            else:
                value = float(value)
        except (ValueError, TypeError):
            pass

    if field_type == "array" and isinstance(value, list):
        (field_type, same_type) = is_same_type(value[0], key_properties['items']['type'])

        if not same_type:
            raise TypeError(f"{value} with type {type(value)} given for {key} - expected {field_type}")
        try:
            field_type = key_properties["items"]["type"]
        except:
            raise AttributeError(f"{key} is an array, but the items have no type")
        for idx, item in enumerate(value):
            (field_type, same_type) = is_same_type(item, field_type)

            if not same_type:
                raise TypeError(f"{item} with type {type(item)} given for {key} at index {idx} - expected {field_type}")
    else:
        (field_type, same_type) = is_same_type(value, field_type)

        if not same_type:

            if(field_type is str and not isinstance(value, list)):
                try:
                    (field_type, same_type) = is_same_type(str(value), field_type)

                    if not same_type:
                        raise TypeError(f"{value} with type {type(value)} given for {key} - expected {field_type}, forcing to 'str' failed")
                    return str(value)
                except:
                    raise TypeError(f"{value} with type {type(value)} given for {key} - expected {field_type}, forcing to 'str' failed")     
            else:
                raise TypeError(f"{value} with type {type(value)} given for {key} - expected {field_type}")
            
    return value

def check_data_length(value, maxLength, truncate=True, key=None):

    if value is None or pd.isna(value):
        return None
    
    if not isinstance(value, str):
        return value

    if len(value) <= maxLength:
        return value

    if truncate:
        trunc_tag = "[TRUNCATED]"
        cutoff = maxLength - len(trunc_tag)
        return value[:cutoff] + trunc_tag

    raise ValueError(f"Value exceeds max length of {maxLength} for field {key}: {value[:25]}...")


def load_data_fields(validator_name):

    if not validator_name.endswith(".json"):
        validator_name += ".json"

    schema_path = os.path.abspath(os.path.join(json_schema_template_path_full, validator_name))

    if not os.path.exists(schema_path):
        raise FileNotFoundError(f"Schema file not found: {schema_path}")

    with open(schema_path, "r", encoding="utf-8") as fh_json_file:
        json_data = json.load(fh_json_file)
        return json_data.get("properties", {})

class ImmPort_Data: 

    def __init__(self, schemaFile=None):

        self.schemaFile = schemaFile
        self.schemaVersion = None
        self.set_schemaVersion(schemaFile)

    def print_obj(self):

        print_data = {}

        for attr in self.__dict__:
            if attr.startswith('__'):
                continue

            print_data[attr]=self[attr]

        return print_data

    def validate(self):

        self.obj_to_data()

        return validate_data(self.get_obj(), schema_name=self.get_validator(), schema_store=schema_store)

    def get_data(self):

        return self.data

    def get_obj(self):

        return self.get_data()

    def obj_to_data(self):

        return self.data

    def set_data(self, key, value):

        self.data[key] = value

        return 

    def get_validator(self):

        return self.validator

    def set_data_value(self, key, value):

        try:
            key_properties = self.get_data_key_properties(key)
        except Exception as e:
            ig.main_logger.write(level="critical", message=f"[ERROR] get_data_key_properties failed for {key}: {e}", flush=True)
            return

        if "type" not in key_properties:
            ig.main_logger.write(level="warn", message=f"{key} has no 'type' property in schema; skipping.", flush=True)
            return

        try:
            value_checked = check_data_type(value, key_properties, key)
        except Exception as e:
            ig.main_logger.write(level="critical", message=f"[ERROR] check_data_type failed for {key}: {e}", flush=True)
            value_checked = value

        if "maxLength" in key_properties:
            try:
                truncated_or_none = check_data_length(
                    value_checked,
                    key_properties["maxLength"],
                    truncate=True,  
                    key=key
                )

                if truncated_or_none is not None:
                    self.set_data(key, truncated_or_none)
                    return
            except Exception as e:
                ig.main_logger.write(level="critical", message=f"[ERROR] check_data_length unexpected error for {key}: {e}", flush=True)
                try:
                    safe_val = str(value_checked)[:key_properties.get("maxLength", 250)]
                    self.set_data(key, safe_val)
                except Exception:
                    self.set_data(key, "[ERROR_TRUNC]")
                return

        try:
            self.set_data(key, value_checked)
        except Exception as e:
            ig.main_logger.write(level="critical", message=f"[ERROR] set_data failed for {key}: {e}", flush=True)
            try:
                self.data[key] = str(value_checked)
            except Exception:
                pass

    def get_data_key_properties(self, key):

        if key in type(self).data_fields:
            return type(self).data_fields[key]
        
        raise AttributeError(f"{key} is not a data property of {(type(self))}" )

    def set_schemaVersion(self, schemaFile):

        self.schemaVersion = GLOBAL_SCHEMA_VERSION

class SchemaEnumExtractor:

    def __init__(self, schemaFile='labTests.MetaData.json'):

        self.schemaFile = schemaFile
        self.enums = self.load_enum_values()

    def load_enum_values(self):

        schema_path = os.path.join(json_schema_template_path_full, self.schemaFile)
    
        try:
            with open(schema_path, "r") as file:
                schema = json.load(file)

            extracted_enums = {}
            for key, properties in schema.get("properties", {}).items():
                if "enum" in properties:
                    extracted_enums[key] = properties["enum"]
            
            return extracted_enums

        except Exception as e:
            ig.main_logger.write(
                level="error",
                message=f"Error loading in labTests.MetaData.json file",      
                flush=True)
                
            return {}
    
    def get_enum(self, field_name):

        options = self.enums.get(field_name, [])
        options = [str(opt).strip() for opt in options if str(opt).strip() != ""]
    
        return options
    
class Assessment(ImmPort_Data):

    filename="assessments.json"
    name="assessments"
    templateType='combined-result'
    validator = "assessments"

    panel_header_columns=["Column Name","Subject ID","Assessment Panel ID","Study ID","Name Reported","Assessment Type","Status","CRF File Names"]
    component_header_columns=["User Defined ID","Planned Visit ID","Name Reported","Study Day","Age At Onset Reported","Age At Onset Unit Reported","Is Clinically Significant","Location Of Finding Reported","Organ Or Body System Reported","Result Value Reported","Result Unit Reported","Result Value Category","Subject Position Reported","Time Of Day","Verbatim Question","Who Is Assessed"]

    def __init__(self):

        self.data=[]
        self.records=[]
        super().__init__(schemaFile=self.filename)

    def add_record(self, record):

        self.records.append(record)

    def get_obj(self):

        obj = {
            "fileName":self.filename,
            "name":self.name,
            "schemaVersion":self.schemaVersion,
            "templateType":self.templateType
        }
        obj["data"] = self.get_data()

        return obj
    
    def obj_to_data(self):

        self.data=[]

        for record in self.records:
            this_record_data = {"metaData":record.metaData.get_data(), "resultData":[]}

            for datum in record.resultData:
                this_record_data["resultData"].append(datum.get_data())

            self.data.append(this_record_data)

    def process_study_file(self, study_file_info=None, study_file_directory=None, 
                        data_dictionary=None, planned_visits=None, study_id=None, 
                        workspace_id=None, name_reported=None):

        filename = study_file_info.get("Filename")
        table_code = study_file_info.get("Table Code")
        template = study_file_info.get("Template")
        
        if template == "Assessment":
            template = "assessments"

        assessment_name = study_file_info.get("Assessment Name")
        default_visit = study_file_info.get("Default Visit")

        study_file_path = os.path.abspath(os.path.join(study_file_directory, filename))

        table_data = {
            "tables": [table_code], 
            "assessment_type": assessment_name,
            "template": template,
            "visit": default_visit
        }

        if name_reported is None:
            name_reported = ig.getStudyFileReportedName(filename)

        study_file_panel = Assessment_Panel(
            nameReported=name_reported,
            assessmentType=assessment_name,
            crfFileNames=[filename],
            studyId=study_id
        )

        datafile = cf.readAndModifyStudyFile(study_file_path, table_data, data_dictionary, planned_visits)

        [panel_template, components_template, assessment_template_header] = cf.readTemplate(template, template_path=txt_template_path_full)

        components_template["ASSESSMENT_PANEL_ACCESSION"] = ''

        components_template = cf.datafileToComponents(
            datafile, data_dictionary, [table_code], components_template, template, workspace_id,  planned_visits=planned_visits, default_visit_name=default_visit)

        loaded_assessment = self.load_df(components_template,study_file_panel,
            crfFileNames=[filename],
            studyId=study_id)

        return [study_file_panel, components_template]

    def load_df(self, dataframe, panel, crfFileNames=None, studyId=None):

        Assessment_ResultData.iterable_counters = {}

        assessment_data = {}

        crfFileNames_norm = None

        if crfFileNames:
            if isinstance(crfFileNames, (list, tuple)):
                crfFileNames_norm = ", ".join(map(str, crfFileNames))
            else:
                crfFileNames_norm = str(crfFileNames)

        for index, row in dataframe.iterrows():
            try:
                field_data = self.convert_result_columns_to_fields(row.to_dict())

                subject_id = field_data.get('userDefinedId') or f"Subject{index+1}"
                
                if subject_id not in assessment_data:
                    assessment_data[subject_id] = Assessment_Datum(assessment_panel=panel, subject_id=subject_id)

                result_data_obj = Assessment_ResultData(
                    studyId=studyId,
                    crfFileNames=crfFileNames,
                    **field_data
                )

                assessment_data[subject_id].add_result_data(result_data_obj)

            except Exception as e:
                continue

        for record in assessment_data.values():
            self.add_record(record)

        del assessment_data
        gc.collect()

    def export_to_txt(self, filename=None):

        if not self.validate():
            raise ValueError("Assessment data is not valid")

        if not filename:
            raise ValueError("Filename must be provided")

        os.makedirs(os.path.dirname(filename), exist_ok=True)

        separator = "\t"

        buffer = StringIO()

        buffer.write(f"{self.name}{separator}Schema Version {self.schemaVersion}\n")
        buffer.write("Please do not delete or edit this column\n")

        most_result_data = max(len(x["resultData"]) for x in self.data)

        header = (
            list(Assessment.panel_header_columns)
            + ["Result Separator Column"]
            + list(Assessment.component_header_columns) * most_result_data
        )
        buffer.write(separator.join(header) + "\n")

        for datum in self.data:
            row_data = [""]  
            row_data.extend(self.populate_panel_columns(datum["metaData"]))
            row_data.append("")  

            for result_data in datum["resultData"]:
                row_data.extend(self.populate_component_column_set(result_data))

            buffer.write(separator.join(map(str, row_data)) + "\n")

        with open(filename, "w", encoding="utf-8") as fh:
            fh.write(buffer.getvalue())

        buffer.close()

    def populate_panel_columns(self,metadata):

        return [
            metadata.get('subjectId'),
            metadata.get('assessmentPanelId'),
            metadata.get('studyId'),
            metadata.get('nameReported'),
            metadata.get('assessmentType'),
            '',
            ";".join(metadata.get('crfFileNames',[])),
        ]
        
    def populate_component_column_set(self,result_data):

        return [
            result_data.get('userDefinedId'),
            result_data.get('plannedVisitId'),
            result_data.get('nameReported'),
            result_data.get('studyDay'),
            result_data.get("ageAtOnsetReported",''),
            result_data.get("ageAtOnsetUnitReported",''),
            result_data.get("isClinicallySignificant",''),
            result_data.get("locationOfFindingReported",''),
            result_data.get("organOrBodySystemReported",''),
            result_data.get("resultValueReported",''),
            result_data.get("resultUnitReported",''),
            result_data.get("resultValueCategory",''),
            result_data.get("subjectPositionReported",''),
            result_data.get("timeOfDay",''),
            result_data.get("verbatimQuestion",''),
            result_data.get("whoIsAssessed",'')
        ]

    def convert_result_columns_to_fields(self, column_dict):

        mapping_dict = {
            'User Defined ID': 'userDefinedId',
            'Planned Visit ID': 'plannedVisitId',
            'Name Reported': 'nameReported',
            'Study Day': "studyDay",
            'Age At Onset Reported': "ageAtOnsetReported",
            'Age At Onset Unit Reported': "ageAtOnsetUnitReported",
            'Is Clinically Significant': "isClinicallySignificant",
            'Location Of Finding Reported': "locationOfFindingReported",
            'Organ Or Body System Reported': "organOrBodySystemReported",
            'Result Value Reported': 'resultValueReported',
            'Result Unit Reported': "resultUnitReported",
            'Result Value Category': "resultValueCategory",
            'Subject Position Reported': "subjectPositionReported",
            'Time Of Day': "timeOfDay",
            'Verbatim Question': 'verbatimQuestion',
            'Who Is Assessed': 'whoIsAssessed'
        }

        field_dict = dict(map(lambda x: (x[1], column_dict.get(x[0],"")), mapping_dict.items()))

        filtered_dict = {k: v for k, v in field_dict.items() if v is not None}

        return filtered_dict

class Assessment_Datum(ImmPort_Data):

    def __init__(self, subject_id=None, assessment_panel=None):

        metadata_obj = Assessment_MetaData(subject_id=subject_id, assessment_panel=assessment_panel)
        self.set_metadata(metadata_obj)
        self.resultData = []
    
    def set_metadata(self, metadata_obj):

        self.metaData = metadata_obj

    def add_result_data(self, result_data_obj):

        self.resultData.append(result_data_obj)

    def print_obj(self):

        return self.__dict__

class Assessment_Panel(ImmPort_Data):

    truncate_long_fields = True

    data_fields = {
        "assessmentPanelId": {
            "type": "string",
            "maxLength": 100
        },
        "nameReported": {
            "type": "string",
            "maxLength": 125
        },
        "assessmentType": {
            "type": "string",
            "maxLength": 125
        },
        "studyId": {
            "type": "string"
        },
        "crfFileNames": {
            "type": "array",
            "items": {
                "type": "string",
                "maxLength": 240
            }
        }
    }

    def __init__(self, nameReported=None, assessmentType=None, studyId=None, crfFileNames=[]):

        raw_filename = crfFileNames[0] if crfFileNames else "NoFile"
        base = os.path.splitext(raw_filename)[0]        
        base = base.replace(" ", "_")                  
        base = "".join(c if c.isalnum() or c in "_-" else "_" for c in base)  

        self.data = {}
        self.set_data_value("assessmentPanelId", f"{studyId}_{base}")
        self.set_data_value("nameReported", nameReported)
        self.set_data_value("assessmentType", assessmentType)
        self.set_data_value("studyId", studyId)
        self.set_data_value("crfFileNames", crfFileNames)

class Assessment_MetaData(ImmPort_Data):

    iterable_counter = 0
    truncate_long_fields = True
    validator = "assessments.MetaData"
    data_fields = load_data_fields(validator)

    def __init__(self, subject_id=None, assessment_panel=None):

        if subject_id == None:
            Assessment_MetaData.iterable_counter +=1
            subject_id = "Subject%s" % Assessment_MetaData.iterable_counter

        self.data={}
        self.data.update(assessment_panel.get_data())

        self.set_data("subjectId", subject_id)

class Assessment_ResultData(ImmPort_Data):

    iterable_counter = 0
    truncate_long_fields = True
    validator = "assessments.ResultData"

    data_fields = load_data_fields(validator)

    result_unit_reported_synonyms = {
        "Arbitrary Fluorescence Units": "AFU",
        "Antibody Index": "AI",
        "Antibody concentration": "Antibody titer",
        "Antibody level": "Antibody titer",
        "BPM": "Beats per Minute",
        "Heart rate": "Beats per Minute",
        "BMI": "Body Mass Index Finding",
        "cms": "cm",
        "centimeter": "cm",
        "centimeters": "cm",
        "Frequency": "Count",
        "Number": "Count",
        "d": "Day",
        "days": "Day",
        "Fragments Per Kilobase Million": "FPKM",
        "grams per deciliter": "g/dl",
        "grams per liter": "g/l",
        "g": "gm",
        "gram": "gm",
        "grams": "gm",
        "hr": "Hour",
        "h": "Hour",
        "Hours": "Hour",
        "hours": "Hour",
        "inch": "in",
        "inches": "in",
        "International Units": "IU",
        "kilogram": "kg",
        "kilograms": "kg",
        "kgs": "kg",
        "kg/m²": "kg/m2",
        "liter": "l",
        "liters": "l",
        "liters per second": "L/sec",
        "milligram": "mg",
        "milligrams": "mg",
        "milligrams per deciliter": "mg/dl",
        "milligrams per deciliters": "mg/dl",
        "milligrams per liter": "mg/l",
        "milligrams per liters": "mg/l",
        "milligrams per milliliter": "mg/ml",
        "milligrams per milliliters": "mg/ml",
        "milli-international units per milliliter": "miu/ml",
        "milliliter": "ml",
        "milliliters": "ml",
        "cc": "ml",
        "ml/min": "mL/min",
        "milliliters per minute": "mL/min",
        "milliliters per minutes": "mL/min",
        "months": "Month",
        "mo": "Month",
        "nanogram": "ng",
        "nanograms": "ng",
        "nanograms per deciliter": "ng/dl",
        "nanograms per deciliters": "ng/dl",
        "nanograms per milliliter": "ng/ml",
        "nanograms per milliliters": "ng/ml",
        "nanograms per nanoliter": "ng/nl",
        "nanograms per nanoliters": "ng/nl",
        "nanograms per microliter": "ng/ul",
        "nanograms per microliters": "ng/ul",
        "nanoliter": "nl",
        "nanoliters": "nl",
        "nanomolar": "nM",
        "nanomolars": "nM",
        "Normalized Protein Expression": "NPX",
        "%": "percentage",
        "proportion": "percentage",
        "picogram": "pg",
        "picograms": "pg",
        "picograms per milliliter": "pg/ml",
        "picograms per milliliters": "pg/ml",
        "picograms per nanoliter": "pg/nl",
        "picograms per nanoliters": "pg/nl",
        "picograms per microliter": "pg/ul",
        "picograms per microliters": "pg/ul",
        "picoliter": "pl",
        "picoliters": "pl",
        "picomolar": "pM",
        "picomolars": "pM",
        "Reads Per Kilobase Million": "RPKM",
        "Transcripts Per Million": "TPM",
        "mcg": "ug",
        "microgram": "ug",
        "micrograms": "ug",
        "micrograms per deciliter": "ug/dl",
        "micrograms per deciliters": "ug/dl",
        "micrograms per kilogram": "ug/kg",
        "micrograms per kilograms": "ug/kg",
        "micrograms per liter": "ug/l",
        "micrograms per liters": "ug/l",
        "micrograms per milliliter": "ug/ml",
        "micrograms per milliliters": "ug/ml",
        "micrograms per microliter": "ug/ul",
        "micrograms per microliters": "ug/ul",
        "micro-international units per milliliter": "uiu/ml",
        "microliter": "ul",
        "microliters": "ul",
        "micromolar": "uM",
        "micromolars": "uM",
        "micromoles per liter": "umol/l",
        "Units per milliliter": "units/ml",
        "units per milliliters": "units/ml",
        "wk": "Week",
        "weeks": "Week",
        "year": "Year",
        "years": "Year",
        "yr": "Year",
        "Celsius": "C",
        "Fahrenheit": "F",
        "Kelvin": "K",
        "True/False": "Boolean",
        "T/F": "Boolean",
        "Yes/No": "Boolean",
        "Y/N": "Boolean",
        "0/1": "Boolean"
    }

    enumFields = dict(filter(lambda x: "enum" in x[1], data_fields.items()))

    def __init__(self, plannedVisitId=None, nameReported=None, studyDay=None, studyId=None, crfFileNames=[], **kwargs):
        Assessment_ResultData.iterable_counter +=1

        if crfFileNames:
            base_filename = os.path.splitext(crfFileNames[0])[0]
        else:
            base_filename = "NoFile"

        base_filename = base_filename.replace(" ", "_")
        base_filename = "".join(c for c in base_filename if c.isalnum() or c in "_-")

        key = (studyId, base_filename)
        count = Assessment_ResultData.iterable_counters.get(key, 0) + 1
        Assessment_ResultData.iterable_counters[key] = count

        studyId_safe = sanitize_component(studyId)
        base_filename_safe = sanitize_component(base_filename)
        count_safe = str(count)

        new_user_id = f"{studyId_safe}_{base_filename_safe}_ID{count_safe}"

        self.data={}

        self.set_data("userDefinedId", new_user_id)
        self.set_data("plannedVisitId", plannedVisitId)
        self.set_data("nameReported", nameReported)
        self.set_data("studyDay", studyDay if studyDay is not None else 99999)

        del kwargs["userDefinedId"]
        
        for key_field, value in kwargs.items():

            if key_field == "resultUnitReported":
                value = self.result_unit_reported_synonyms.get(value, value)
                self.set_data_value(key_field, value)
                continue

            try:
                self.set_data_value(key_field, value)
            except Exception as e:
                continue

schema_store = get_schema_store(json_schema_template_path_full)

class labTests(ImmPort_Data):

    filename="labTests.json"
    name="labtests"  
    templateType='combined-result'
    validator = "labTests"
  
    panel_header_columns=["Column Name", "Biosample ID", "Lab Test Panel ID", "Study ID", "Protocol ID(s)", "Subject ID", "Planned Visit ID", "Type", "Subtype", "Name", "Description", "Study Time Collected", "Study Time Collected Unit", "Study Time T0 Event", "Study Time T0 Event Specify", "Name Reported"]
    component_header_columns=["User Defined ID","Name Reported","Result Value Reported","Result Unit Reported"]

    def __init__(self):

        self.data=[]
        self.records=[]
        super().__init__(schemaFile=self.filename)

    def add_record(self, record):

        self.records.append(record)

    def get_obj(self):

        obj = {
            "fileName":self.filename,
            "name":self.name,
            "schemaVersion":self.schemaVersion,
            "templateType":self.templateType
        }
        obj["data"] = self.get_data()

        return obj
    
    def obj_to_data(self):

        self.data=[]

        for record in self.records:
            this_record_data = {"metaData":record.metaData.get_data(), "resultData":[]}

            for datum in record.resultData:
                this_record_data["resultData"].append(datum.get_data())

            self.data.append(this_record_data)
        
    def process_study_file(self, study_file_info=None, study_file_directory=None, data_dictionary=None, planned_visits=None, study_id=None, protocols_df=None, workspace_id=None, name_reported=None):

        filename = study_file_info.get("Filename")
        table_code = study_file_info.get("Table Code")
        template = study_file_info.get("Template")

        if template == "Lab Test":
            template = "labTests"

        default_visit = study_file_info.get("Default Visit")
        protocol = study_file_info.get("Protocol")
        name_reported_dropdown = study_file_info.get("Name Reported")
        labTest_type = study_file_info.get("Type")
        labTest_subtype = study_file_info.get("Subtype")
        labTest_studyT0 = study_file_info.get("Study Time T0 Event")
        labTest_studyT0_specify = study_file_info.get("Study Time T0 Event Specify")

        if protocol == "--Select--" or protocol == "":
            protocol = "Unspecified" 

        if protocol:
            protocol_mapping = dict(zip(protocols_df["NAME"], protocols_df["PROTOCOL_ACCESSION"]))
            if protocol in protocol_mapping:
                protocol = protocol_mapping[protocol]
            else:
                protocol = "Unspecified" 

        study_file_directory = study_file_directory.rstrip("\\/")

        study_file_path = os.path.abspath(os.path.join(study_file_directory, filename))

        table_data = {
            "tables":[table_code], 
            "template":template,
            "visit":default_visit,
            "protocol":protocol, 
            "name reported": name_reported_dropdown,
            "type":labTest_type,  
            "subtype":labTest_subtype, 
            "studyT0": labTest_studyT0,
            "studyT0_specify": labTest_studyT0_specify
        }

        crfFileNames = [filename]  

        datafile = cf.readAndModifyStudyFile(study_file_path, table_data, data_dictionary, planned_visits)

        planned_visit_id = ""
        if not datafile.empty:
            if 'PLANNED_VISIT_ID' in datafile.columns:
                planned_visit_id = datafile['PLANNED_VISIT_ID'].iloc[0]
            elif 'Planned Visit ID' in datafile.columns:
                planned_visit_id = datafile['Planned Visit ID'].iloc[0]
    
            if pd.isna(planned_visit_id):
                planned_visit_id = "Unspecified"
            planned_visit_id = str(planned_visit_id)

        visit_day_mapping = dict(zip(planned_visits["PLANNED_VISIT_ACCESSION"], planned_visits["MIN_START_DAY"]))

        study_time_collected = ""
        if not datafile.empty:
            if 'STUDY_TIME_COLLECTED' in datafile.columns:
                study_time_collected = datafile['STUDY_TIME_COLLECTED'].iloc[0]
            elif 'Study Time Collected' in datafile.columns:
                study_time_collected = datafile['Study Time Collected'].iloc[0]

        if pd.isna(study_time_collected) or study_time_collected == "" or study_time_collected == 99999:
            if planned_visit_id in visit_day_mapping:
                study_time_collected = visit_day_mapping[planned_visit_id]

            else:
                study_time_collected = 99999
    
        study_file_panel = LabTest_Panel(
            labTestNameReported=name_reported_dropdown,
            protocolId=protocol,
            plannedVisitId=planned_visit_id,  
            labTestType=labTest_type, 
            labTestSubtype=labTest_subtype,
            studyTimeCollected=study_time_collected,
            studyTimeT0Event = labTest_studyT0,
            studyTimeT0EventSpecify = labTest_studyT0_specify,
            studyId=study_id,
            crfFileNames=crfFileNames
        )
        
        [panel_template,components_template,labTest_template_header] = cf.readTemplate(template, template_path=txt_template_path_full) 
        
        components_template["LAB_TEST_PANEL_ACCESSION"]=''

        components_template = cf.datafileToComponents(
                datafile, data_dictionary, [table_code], components_template, template, workspace_id,  planned_visits=planned_visits, default_visit_name=default_visit)

        loaded_lab = self.load_df(components_template, study_file_panel, crfFileNames=[filename], studyId=study_id, planned_visits=planned_visits)
   
        return [study_file_panel, components_template]

    def load_df(self, dataframe, panel, crfFileNames=None, studyId=None, planned_visits=None): 

        import traceback
        labtest_data = {}

        try:

            if 'Planned Visit ID' not in dataframe.columns:
                dataframe['Planned Visit ID'] = None

            if 'Study Time Collected' not in dataframe.columns:
                dataframe['Study Time Collected'] = 99999
                study_time_unit = "Not Specified"
            else:
                study_time_unit = "Days"

            file_level_panel_id = panel.get_data().get('labTestPanelId')

            visit_day_mapping = dict(zip(planned_visits["PLANNED_VISIT_ACCESSION"], planned_visits["MIN_START_DAY"]))

            grouped = dataframe.groupby(['User Defined ID', 'Planned Visit ID', 'Study Time Collected'])

            for group_idx, ((subject_id, visit_id, study_time), group) in enumerate(grouped, start=1):
                
                try:
                    if study_time == 99999 and visit_id in visit_day_mapping:
                        study_time = visit_day_mapping[visit_id]
                        study_time_unit = "Days"

                    panel_copy = LabTest_Panel(
                        labTestNameReported=panel.get_data().get('labTestNameReported'),
                        protocolId=panel.get_data().get('protocolId'),
                        plannedVisitId=str(visit_id),  
                        labTestType=panel.get_data().get('labTestType'),
                        labTestSubtype=panel.get_data().get('labTestSubtype'),
                        studyTimeCollected=study_time,
                        studyTimeCollectedUnit=study_time_unit,
                        studyTimeT0Event=panel.get_data().get('studyTimeT0Event'),
                        studyTimeT0EventSpecify=panel.get_data().get('studyTimeT0EventSpecify'),
                        studyId=studyId,
                        crfFileNames=crfFileNames
                    )

                    panel_copy.set_data_value("labTestPanelId", file_level_panel_id)

                    labtest_data[(subject_id, visit_id, study_time)] = LabTest_Datum(
                        labTest_panel=panel_copy,  
                        subject_id=subject_id
                    )

                    for row_idx, (_, row) in enumerate(group.iterrows(), start=1):
                        field_data = self.convert_result_columns_to_fields(row.to_dict())

                        result = LabTest_ResultData(
                            studyId=studyId,
                            crfFileNames=crfFileNames,
                            **field_data
                        )
                        labtest_data[(subject_id, visit_id, study_time)].add_result_data(result)

                except Exception as inner_e:
                    continue

            for rec_idx, record in enumerate(labtest_data.values(), start=1):
                try:
                    self.add_record(record)
                except Exception as add_e:
                    continue

        except Exception as outer_e:

            display(f"[FATAL load_df] Unexpected failure: {outer_e}")
            display(traceback.format_exc())

    def export_to_txt(self, filename=None):

        if not self.validate():
            raise ValueError("Assessment data is not valid")

        if not filename:
            raise ValueError("Filename must be provided")

        os.makedirs(os.path.dirname(filename), exist_ok=True)

        separator = "\t"

        buffer = StringIO()

        buffer.write(f"{self.name}{separator}Schema Version {self.schemaVersion}\n")
        buffer.write("Please do not delete or edit this column\n")

        most_result_data = max(len(x["resultData"]) for x in self.data)

        header = (
            list(labTests.panel_header_columns)
            + ["Result Separator Column"]
            + list(labTests.component_header_columns) * most_result_data
        )
        buffer.write(separator.join(header) + "\n")

        for datum in self.data:
            row_data = [""]  
            row_data.extend(self.populate_panel_columns(datum["metaData"]))
            row_data.append("") 

            for result_data in datum["resultData"]:
                row_data.extend(self.populate_component_column_set(result_data))

            buffer.write(separator.join(map(str, row_data)) + "\n")

        with open(filename, "w", encoding="utf-8") as fh:
            fh.write(buffer.getvalue())

        buffer.close()


    def populate_panel_columns(self,metadata):

        return [
            metadata.get('biosampleId'),
            metadata.get('labTestPanelId'),
            metadata.get('studyId'),
            metadata.get('protocolId'),
            metadata.get('subjectId'),
            metadata.get('plannedVisitId'),
            metadata.get('labTestType'),
            metadata.get('labTestSubtype'),
            "",
            "",
            metadata.get('studyTimeCollected'),
            metadata.get('studyTimeCollectedUnit'),
            metadata.get('studyTimeT0Event'),
            metadata.get('studyTimeT0EventSpecify'),
            metadata.get('labTestNameReported')
        ]
        
    def populate_component_column_set(self,result_data):

        return [
            result_data.get('userDefinedId'),
            result_data.get('nameReported'),
            result_data.get("resultValueReported",''),
            result_data.get("resultUnitReported",'')
        ]

    def convert_result_columns_to_fields(self, column_dict):
        
        mapping_dict = {
            'User Defined ID': 'userDefinedId',
            'Name Reported': 'nameReported',
            'Result Value Reported': 'resultValueReported',
            'Result Unit Reported': "resultUnitReported"
        }

        field_dict = {v: column_dict.get(k,"") for k,v in mapping_dict.items()}

        filtered_dict = {
            k:v
            for k,v in field_dict.items()
            if k != "resultUnitReported" and ((type(v)!=float and v not in ['','userDefinedId']) or str(v) not in ['nan','','userDefinedId'])
        }

        filtered_dict["resultUnitReported"] = field_dict.get("resultUnitReported","")

        return filtered_dict

class LabTest_Datum(ImmPort_Data):

    def __init__(self, subject_id=None, biosample_id=None, labTest_panel=None):

        self.labTest_panel = labTest_panel 

        metadata_obj = LabTest_MetaData(subject_id=subject_id, biosample_id = biosample_id, labTest_panel=labTest_panel)
        self.set_metadata(metadata_obj)
        self.resultData = []
    
    def set_metadata(self, metadata_obj):

        self.metaData = metadata_obj

    def add_result_data(self, result_data_obj):

        self.resultData.append(result_data_obj)

    def get_panel_data(self):

        return self.labTest_panel.get_data() if self.labTest_panel else {}

    def print_obj(self):

        return self.__dict__
    
class LabTest_Panel(ImmPort_Data):

    iterable_counter = 0
    truncate_long_fields = True

    data_fields={
        "labTestPanelId": {
            "type": "string",
            "maxLength": 100
        },
        "studyId": {
            "type": "string",
            "maxLength": 15
        }, 
        "protocolId": {
            "type": "string",
            "maxLength": 15
        },
        "plannedVisitId": {
            "type": "string",
            "maxLength": 15
        },
        "labTestType": {
            "type": "string",
            "maxLength": 50
        }, 
        "labTestSubtype": {
            "type": "string",
            "maxLength": 50
        }, 
        "studyTimeCollected":{
            "type": "float"
        },
        "studyTimeCollectedUnit": {
            "type": "string",
            "maxLength": 25
        },
        "studyTimeT0Event":{
            "type": "string",
            "maxLength": 50
        },
        "studyTimeT0EventSpecify":{
            "type": "string",
            "maxLength": 50
        },
        "labTestNameReported": {
            "type": "string",
            "maxLength": 125
        }
    }

    def __init__(self, labTestNameReported=None, protocolId=None, plannedVisitId=None, labTestType=None, labTestSubtype=None, studyTimeCollected=None, studyTimeCollectedUnit=None, studyTimeT0Event=None, 
                 studyTimeT0EventSpecify=None, studyId=None, crfFileNames=None):
        
        raw_filename = crfFileNames[0] if crfFileNames else "NoFile"
        base = os.path.splitext(raw_filename)[0]        
        base = base.replace(" ", "_")                  
        base = "".join(c if c.isalnum() or c in "_-" else "_" for c in base)  

        LabTest_Panel.iterable_counter +=1

        self.data={}

        self.set_data_value("labTestPanelId", f"{studyId}_{base}")
        self.set_data_value("studyId", studyId)
        self.set_data_value("protocolId", protocolId)
        self.set_data_value("plannedVisitId", str(plannedVisitId))
        self.set_data_value("labTestType", labTestType)
        self.set_data_value("labTestSubtype", labTestSubtype)
        self.set_data_value("studyTimeCollected", studyTimeCollected if studyTimeCollected is not None else 99999)
        self.set_data_value("studyTimeCollectedUnit", studyTimeCollectedUnit)
        self.set_data_value("studyTimeT0Event", studyTimeT0Event)
        self.set_data_value("studyTimeT0EventSpecify", studyTimeT0EventSpecify)
        self.set_data_value("labTestNameReported", labTestNameReported)

class LabTest_MetaData(ImmPort_Data):

    iterable_counter = 0
    truncate_long_fields = True
    validator = "labTests.MetaData"
    data_fields = load_data_fields(validator)

    def __init__(self, subject_id=None, biosample_id=None, labTest_panel=None):
         
        self.data={}
        self.data.update(labTest_panel.get_data())
        
        if subject_id == None:

            LabTest_MetaData.iterable_counter +=1
            subject_id = "Subject%s" % LabTest_MetaData.iterable_counter
     
        if biosample_id == None:

            test_type = self.data.get('labTestType')

            if test_type.upper() == 'OTHER':
                test_type = self.data.get('labTestSubtype', 'UnknownType')
    
            planned_visit = self.data.get('plannedVisitId', 'UnspecifiedVisit')
            biosample_id = f"{subject_id}_{planned_visit}_{test_type}".replace(" ", "_")
  
        self.set_data("subjectId", subject_id)
        self.set_data("biosampleId", biosample_id)

class LabTest_ResultData(ImmPort_Data):

    validator = "labTests.ResultData"
    data_fields = load_data_fields(validator)
    truncate_long_fields = True

    iterable_counters = {}

    result_unit_reported_synonyms = {
        "Arbitrary Fluorescence Units": "AFU",
        "Antibody Index": "AI",
        "Antibody concentration": "Antibody titer",
        "Antibody level": "Antibody titer",
        "BPM": "Beats per Minute",
        "Heart rate": "Beats per Minute",
        "BMI": "Body Mass Index Finding",
        "cms": "cm",
        "centimeter": "cm",
        "centimeters": "cm",
        "Frequency": "Count",
        "Number": "Count",
        "d": "Day",
        "days": "Day",
        "Fragments Per Kilobase Million": "FPKM",
        "grams per deciliter": "g/dl",
        "grams per liter": "g/l",
        "g": "gm",
        "gram": "gm",
        "grams": "gm",
        "hr": "Hour",
        "h": "Hour",
        "Hours": "Hour",
        "hours": "Hour",
        "inch": "in",
        "inches": "in",
        "International Units": "IU",
        "kilogram": "kg",
        "kilograms": "kg",
        "kgs": "kg",
        "kg/m²": "kg/m2",
        "liter": "l",
        "liters": "l",
        "liters per second": "L/sec",
        "milligram": "mg",
        "milligrams": "mg",
        "milligrams per deciliter": "mg/dl",
        "milligrams per deciliters": "mg/dl",
        "milligrams per liter": "mg/l",
        "milligrams per liters": "mg/l",
        "milligrams per milliliter": "mg/ml",
        "milligrams per milliliters": "mg/ml",
        "milli-international units per milliliter": "miu/ml",
        "milliliter": "ml",
        "milliliters": "ml",
        "cc": "ml",
        "ml/min": "mL/min",
        "milliliters per minute": "mL/min",
        "milliliters per minutes": "mL/min",
        "months": "Month",
        "mo": "Month",
        "nanogram": "ng",
        "nanograms": "ng",
        "nanograms per deciliter": "ng/dl",
        "nanograms per deciliters": "ng/dl",
        "nanograms per milliliter": "ng/ml",
        "nanograms per milliliters": "ng/ml",
        "nanograms per nanoliter": "ng/nl",
        "nanograms per nanoliters": "ng/nl",
        "nanograms per microliter": "ng/ul",
        "nanograms per microliters": "ng/ul",
        "nanoliter": "nl",
        "nanoliters": "nl",
        "nanomolar": "nM",
        "nanomolars": "nM",
        "Normalized Protein Expression": "NPX",
        "%": "percentage",
        "proportion": "percentage",
        "picogram": "pg",
        "picograms": "pg",
        "picograms per milliliter": "pg/ml",
        "picograms per milliliters": "pg/ml",
        "picograms per nanoliter": "pg/nl",
        "picograms per nanoliters": "pg/nl",
        "picograms per microliter": "pg/ul",
        "picograms per microliters": "pg/ul",
        "picoliter": "pl",
        "picoliters": "pl",
        "picomolar": "pM",
        "picomolars": "pM",
        "Reads Per Kilobase Million": "RPKM",
        "Transcripts Per Million": "TPM",
        "mcg": "ug",
        "microgram": "ug",
        "micrograms": "ug",
        "micrograms per deciliter": "ug/dl",
        "micrograms per deciliters": "ug/dl",
        "micrograms per kilogram": "ug/kg",
        "micrograms per kilograms": "ug/kg",
        "micrograms per liter": "ug/l",
        "micrograms per liters": "ug/l",
        "micrograms per milliliter": "ug/ml",
        "micrograms per milliliters": "ug/ml",
        "micrograms per microliter": "ug/ul",
        "micrograms per microliters": "ug/ul",
        "micro-international units per milliliter": "uiu/ml",
        "microliter": "ul",
        "microliters": "ul",
        "micromolar": "uM",
        "micromolars": "uM",
        "micromoles per liter": "umol/l",
        "Units per milliliter": "units/ml",
        "units per milliliters": "units/ml",
        "wk": "Week",
        "weeks": "Week",
        "year": "Year",
        "years": "Year",
        "yr": "Year",
        "Celsius": "C",
        "Fahrenheit": "F",
        "Kelvin": "K",
        "True/False": "Boolean",
        "T/F": "Boolean",
        "Yes/No": "Boolean",
        "Y/N": "Boolean",
        "0/1": "Boolean"
    }

    enumFields = dict(filter(lambda x: "enum" in x[1], data_fields.items()))

    def __init__(self, study_file_info=None, nameReported=None, studyId=None, crfFileNames=None, **kwargs):

        if crfFileNames:
            base_filename = os.path.splitext(crfFileNames[0])[0] 
        else:
            base_filename = "NoFile"

        base_filename = base_filename.replace(" ", "_")
        base_filename = "".join(c for c in base_filename if c.isalnum() or c in "_-")

        key = (studyId, base_filename)
        count = LabTest_ResultData.iterable_counters.get(key, 0) + 1
        LabTest_ResultData.iterable_counters[key] = count

        studyId_safe = sanitize_component(studyId)
        base_filename_safe = sanitize_component(base_filename)
        count_safe = str(count)

        new_user_id = f"{studyId_safe}_{base_filename_safe}_ID{count_safe}"

        self.data = {}
        self.set_data("userDefinedId", new_user_id)
        self.set_data("nameReported", nameReported)

    #    self.set_data("nameReported", nameReported)

        kwargs.pop("userDefinedId", None)

        for key, value in kwargs.items():

            if key == "resultUnitReported":
                value = self.result_unit_reported_synonyms.get(value, value)
                self.set_data_value(key, value)
                continue

            try:
                self.set_data_value(key, value)
            except Exception as e:
                continue

