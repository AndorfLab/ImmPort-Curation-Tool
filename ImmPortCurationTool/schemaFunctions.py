import os
import jsonschema
import json
import ImmPortCurationTool.curationFunctions as cf
import ImmPortCurationTool.immport_gui as ig
from pathlib import Path
import platform
import pandas as pd
import numpy as np 

from IPython.display import display

json_schema_template_path   = "templates/json-templates"
txt_template_path           = "templates/txt-templates"

json_schema_template_path_full = os.path.join(os.path.dirname(cf.__file__), json_schema_template_path)
txt_template_path_full = os.path.join(os.path.dirname(cf.__file__), txt_template_path)

last_error =""

def check_directory_exists(path):
    directory_path = os.path.dirname(path)
    if not os.path.exists(directory_path):
        Path(directory_path).mkdir(parents=True, exist_ok=True)
    return

def get_schema_store(json_schema_template_path):
    schema_store = {}
    fnames = os.listdir(json_schema_template_path)
    for fname in fnames:
        if fname.endswith(".json"):
            with open(os.path.join(json_schema_template_path, fname)) as schema_fd:
                schema = json.load(schema_fd)
                schema_store[fname] = schema
    return schema_store

def validate_data(data, schema_name=None):

    global last_error
    try: 
        schema_store 
    except:
        ig.main_logger.write(
            level="error",
            message=f"Schema store not found", flush=True
        )
        raise NotImplementedError("Schemas have not been loaded")
    
    if schema_name is None:
        ig.main_logger.write(
            level="error",
            message=f"No schema name provided", flush=True
        )
        raise ValueError("Schema name not provided")

    if not schema_name.endswith(".json"):
        schema_name+=".json"
    
    schema = schema_store.get(schema_name)
    if schema is None:
        ig.main_logger.write(
            level="error",
            message=f"schema is none for {schema_name}", flush=True
        )
        raise NotImplementedError("Missing Schema for '%s'" % schema_name)

    # ref_resolver_path = os.path.abspath(os.path.join(os.getcwd(),json_schema_template_path,schema_name))
    ref_resolver_path = os.path.abspath(os.path.join(json_schema_template_path_full,schema_name))
    if platform.system() == 'Windows':
        resolver = jsonschema.RefResolver(ref_resolver_path, schema, store=schema_store)
    else:
        resolver = jsonschema.RefResolver("file://%s" % ref_resolver_path, schema, store=schema_store)

    try:
        jsonschema.Draft4Validator(schema, resolver=resolver).validate(data)
        return True
    except jsonschema.exceptions.ValidationError as error:
        if("properties/data/items/properties/resultData/items/properties/resultUnitReported/enum" == "/".join(list(error.schema_path))):
            ig.main_logger.write(
                level="warn",
                message=f"\tNon-Preferred Unit of '{error.instance}'"
            )
            return True
        elif("properties/data/items/properties/resultData/items/properties/plannedVisitId/type" == "/".join(list(error.schema_path))):

            if error.cause is None:
                last_error=error
                ig.main_logger.write(
                    level="error",
                    message=f"Some records are missing a valid planned visit"
                )
            return True
        else:
            last_error=error
            ig.main_logger.write(
                level="error",
                message=f"Some other Validation Error... {error}",      #TODO: Weird Error here. 
                flush=True
            )
            ig.main_logger.write(
                level="debug",
                message=f"Message: {error.__dict__}",
                flush=True
            )
        return f"ValidationError: {error}"
    except jsonschema.exceptions.SchemaError as error:
        
        ig.main_logger.write(
            level="error",
            message=f"Schema Error {NameError}"
        )
        return f"SchemaError: {error}"
    except Exception as error:
        
        ig.main_logger.write(
            level="error",
            message=f"Exception of {type(error)}:{error}",
            flush=True
        )
        ig.main_logger.write(
            level="error",
            message=f"error:{error.__dict__}",
            flush=True
        )
    return False

def is_same_type(value, field_type):

    if value is None or pd.isna(value):
        return (field_type, True)
    
    if isinstance(value, (np.number, np.integer)):
        value = float(value) if isinstance(value, np.floating) else int(value)
    

    # if field_type == "string" or field_type == str:
    #     return (str, isinstance(value, str))
    # elif field_type == "number" or field_type == float: 
    #     return (float, isinstance(value, (float,int)))
    # elif field_type == 'integer':
    #     return (int, isinstance(value, int))
    # elif field_type == 'array' or field_type == list:
    #     return (list, isinstance(value, list))
    # raise TypeError(f"Type '{field_type}' not handled")

       # Expanded type checking
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
        if not same_type :
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

def check_data_length(value, maxLength, truncate=False, key=None):
    if value is None:  
        return None
    
    if len(value)<=maxLength:
        return None
    
    ig.main_logger.write(message=f"Value of {key} exceeds max length of {maxLength}: {value[0:40]}...", level='critical')
    if truncate and type(value) is str:
        ig.main_logger.write(message=f"\tTruncated value from {len(value)} characters to {maxLength} characters", level='critical')
        try:
            value = "[TRUNCATED]"+value
            return value[0:maxLength]
        except Exception as e:
            ig.main_logger.write(message=f"\tTruncation failed: {e}", level='critical')

    raise ValueError("Value exceeds max length of {maxLength} for field {key}: {maxLength[0:25]}...")

def load_data_fields(validator):
    path = os.path.dirname(cf.__file__)
    # with open(os.path.abspath(os.path.join(json_schema_template_path,validator+".json"))) as fh_json_file:
    with open(os.path.abspath(os.path.join(json_schema_template_path_full,validator+".json"))) as fh_json_file:
        json_data = json.load(fh_json_file)
        return json_data['properties']
class ImmPort_Data: 

    def __init__(self, schemaFile='protocols.json'):
        display("ImmPort_Data initialized")
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
        return validate_data(self.get_obj(), schema_name = self.get_validator())
    
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
        key_properties = self.get_data_key_properties(key)
        if "type" not in key_properties:
            raise AttributeError("{key} has no 'type' property in the schema")
        value = check_data_type(value, key_properties, key)
        if "maxLength" in key_properties:
            truncated_value = check_data_length(value, key_properties["maxLength"], truncate=type(self).truncate_long_fields, key=key)
            if truncated_value is not None:
                self.set_data(key, truncated_value)
                return

        self.set_data(key,value)

    def get_data_key_properties(self, key):
        if key in type(self).data_fields:
            return type(self).data_fields[key]
        raise AttributeError(f"{key} is not a data property of {(type(self))}" )

    def set_schemaVersion(self, schemaFile):
        display(f"Setting schema version for {schemaFile}")
        with open(os.path.abspath(os.path.join(json_schema_template_path_full,schemaFile))) as fh:
            protocols_schema = json.load(fh)
            self.schemaVersion=protocols_schema['properties']['schemaVersion']['enum'][0]

class SchemaEnumExtractor:
    """Extracts enum values from labTests.MetaData.json"""

    def __init__(self, schemaFile='labTests.MetaData.json'):
        self.schemaFile = schemaFile
        self.enums = self.load_enum_values()

    def load_enum_values(self):
        """Reads the labTests.MetaData.json and extracts enum values that will be used in the ui editable table dropdowns"""
        
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
        """Returns enum options"""

        options = self.enums.get(field_name, [])
    
        if "--Select--" not in options:
            options.insert(0, "--Select--")
    
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

        display("DEBUG: Running obj_to_data()...")
        self.data=[]
        display(f"DEBUG: Total records in self.records: {len(self.records)}")
        for record in self.records:
        #    display(f"DEBUG: Record metadata: {record.metaData.get_data()}")
        #    display(f"DEBUG: Record resultData: {record.resultData}")
            this_record_data = {"metaData":record.metaData.get_data(), "resultData":[]}
            for datum in record.resultData:
                this_record_data["resultData"].append(datum.get_data())
            self.data.append(this_record_data)

        display(f"DEBUG: obj_to_data() generated {len(self.data)} records")
        
        
    def process_study_file(self, study_file_info=None, study_file_directory=None, 
                        data_dictionary=None, planned_visits=None, study_id=None, 
                        workspace_id=None, name_reported=None):
        
        display("DEBUG: Running process_study_file()...")

        filename = study_file_info.get("Filename")
        table_code = study_file_info.get("Table Code")
        template = study_file_info.get("Template")
        
        if template == "Assessment":
            template = "assessments"

        assessment_name = study_file_info.get("Assessment Name")
        default_visit = study_file_info.get("Default Visit")

        display(f"DEBUG: Processing file: {filename}")
        display(f"DEBUG: Table Code: {table_code}")
        display(f"DEBUG: Assessment Name: {assessment_name}")
        display(f"DEBUG: Template: {template}")
        display(f"DEBUG: Default Visit: {default_visit}")

        study_file_path = os.path.abspath(os.path.join(study_file_directory, filename))
        display(f"DEBUG: Study file path: {study_file_path}")

        table_data = {
            "tables": [table_code], 
            "assessment_type": assessment_name,
            "template": template,
            "visit": default_visit
        }

        display(f"DEBUG: Table Data: {table_data}")

        if name_reported is None:
            name_reported = ig.getStudyFileReportedName(filename)
        display(f"DEBUG: Name Reported: {name_reported}")

        study_file_panel = Assessment_Panel(
            nameReported=name_reported,
            assessmentType=assessment_name,
            crfFileNames=[filename],
            studyId=study_id
        )

        display(f"DEBUG: Created study_file_panel: {study_file_panel}")

        # Read and modify study file
        datafile = cf.readAndModifyStudyFile(study_file_path, table_data, data_dictionary, planned_visits)

        display(f"DEBUG: Datafile shape: {datafile.shape if datafile is not None else 'None'}")

        display(f"DEBUG: Reading template: {template} from {txt_template_path_full}")
     #   [assessment_panel_template, assessment_components_template, assessment_template_header] = cf.readTemplate(template, template_path=txt_template_path_full)
        [panel_template, components_template, assessment_template_header] = cf.readTemplate(template, template_path=txt_template_path_full)
        
        
        display(f"DEBUG: Assessment Panel Template shape: {panel_template.shape}")
        display(f"DEBUG: Assessment Components Template shape: {components_template.shape}")

        components_template["ASSESSMENT_PANEL_ACCESSION"] = ''

        display(f"DEBUG: Datafile shape before processing: {datafile.shape}")
        display(f"DEBUG: Datafile preview: {datafile.head()}")

        
        # Convert datafile into components
        components_template = cf.datafileToComponents(
            datafile, data_dictionary, [table_code], components_template, template, workspace_id)

        display(f"DEBUG: Components Template shape AFTER processing: {components_template.shape}")
        display(f"DEBUG: Components Template preview: {components_template.head()}")

        if components_template.empty:
            display(f"ERROR: datafileToComponents() returned an empty DataFrame!")

        display(f"DEBUG: Final Components Template shape: {components_template.shape}")

        loaded_assessment = self.load_df(components_template,study_file_panel,
            crfFileNames=[filename],
            studyId=study_id)

        return [study_file_panel, components_template]

    def load_df(self, dataframe, panel, crfFileNames=None, studyId=None):
        assessment_data = {}

        display(f"DEBUG: Processing {len(dataframe)} rows in load_df()")

        for index, row in dataframe.iterrows():
            field_data = self.convert_result_columns_to_fields(row.to_dict())

            userID = field_data.get('userDefinedId')
            
            if userID not in assessment_data:
                assessment_data[userID] = Assessment_Datum(assessment_panel=panel, subject_id=userID)
            
            result_data_obj = Assessment_ResultData(studyId=studyId, crfFileNames=crfFileNames ,**field_data)
            assessment_data[userID].add_result_data(result_data_obj)

        for record in assessment_data.values():
            self.add_record(record)

    # TODO: Look about moving to ImmPort_Data Class
    def export_to_json(self, filename=None):
        valid = self.validate()
        if not valid:
            raise ValueError(f"Assessment data is not valid: {valid}")
        
        check_directory_exists(filename)
        with open(filename, 'w')as fh:
            print(json.dumps(self.get_obj(), indent=4), file=fh)
        return

    # TODO: Look about moving to ImmPort_Data Class
    def export_to_txt(self, filename=None):
        if not self.validate():
            raise ValueError("Assessment data is not valid")
        separator = "\t"
        check_directory_exists(filename)
        with open(filename, 'w') as fh:

            print(self.name, f"Schema Version {self.schemaVersion}", sep=separator, file=fh)
            print('Please do not delete or edit this column', file=fh)

            most_result_data = max(list(map(lambda x: len(x["resultData"]), self.data)))
            print(*Assessment.panel_header_columns,'Result Separator Column', *Assessment.component_header_columns * most_result_data, sep=separator, file=fh)

            for datum in self.data:
                row_data = [''] # For Column Name
                row_data.extend(self.populate_panel_columns(datum["metaData"]))
                row_data.append('') #For separator column
                for result_data in datum["resultData"]:
                    row_data.extend(self.populate_component_column_set(result_data))
            
                print(*row_data, sep=separator, file=fh)
        return 

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
    #    display(f"A Converting columns: {column_dict.keys()}") 

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
      #  display(f"A field_dict {field_dict}")

        filtered_dict = dict(filter(lambda elem: ((type(elem[1]) != float and elem[1] not in ['','userDefinedId']) or str(elem[1]) not in ['nan', '', 'userDefinedId']), field_dict.items()))
  #      display(f"A filtered_dict {filtered_dict}")

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
    iterable_counter = 0
    truncate_long_fields = True

    data_fields={
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

    def __init__(self, nameReported=None, assessmentType=None,studyId=None, crfFileNames=[]):
        Assessment_Panel.iterable_counter +=1
        filename_string = "-".join(crfFileNames)

        self.data={}
        self.set_data_value("assessmentPanelId", f"{studyId}_{filename_string}_Panel{Assessment_Panel.iterable_counter}")
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
        "g":"gm",
        "%":"percentage",
        "mcg":"ug",
        "hr":"Hour",
        "cms":"cm",
        "kgs":"kg",
        "months":"Month",
        "years":"Year"
    }

    enumFields = dict(filter(lambda x: "enum" in x[1], data_fields.items()))

    def __init__(self, plannedVisitId=None, nameReported=None, studyDay=None, studyId=None, crfFileNames=[], **kwargs):
        Assessment_ResultData.iterable_counter +=1
        
        if crfFileNames is not None:
            filename_string = "_".join(crfFileNames)
        else:
            filename_string = "NoCRF"

        self.data={}
        new_user_id = f"{studyId}_{filename_string}_RD{Assessment_ResultData.iterable_counter}"
        
        self.set_data("userDefinedId", new_user_id)
        
        self.set_data("plannedVisitId", plannedVisitId)
        self.set_data("nameReported", nameReported)
        self.set_data("studyDay", studyDay if studyDay is not None else 99999)

        del kwargs["userDefinedId"]
        
        for key, value in kwargs.items():
            # TODO: need a way to identify/report ALL instances, and then allow user to specify mapping in GUI
            if key in self.enumFields and value not in self.enumFields[key]["enum"]:
                if key.endswith("UnitReported"):
                    if value in self.result_unit_reported_synonyms:
                        ig.main_logger.write(
                            level="info",
                            message=f"\tSuggest substituting '{self.result_unit_reported_synonyms[value]}' for '{value}' for field '{key}' - {nameReported}"
                        )
                    else:
                        ig.main_logger.write(
                            level="info",
                            message=f"Value '{value}' for field '{key}' is not a preferred term - {nameReported}"
                        )
                else:
                    ig.main_logger.write(
                        level="warn",
                        message=f"Value '{value}' for field '{key}' is not valid - {nameReported}"
                    )

            self.set_data_value(key, value)

schema_store = get_schema_store(json_schema_template_path_full)

class labTests(ImmPort_Data):
    filename="labTests.json"
    name="labtests"   #"labTests"
    templateType='combined-result'
    validator = "labTests"
  
    panel_header_columns=["Column Name", "Biosample ID", "Lab Test Panel ID", "Study ID", "Protocol ID(s)", "Subject ID", "Planned Visit ID", "Type", "Subtype", "Name", "Description", "Study Time Collected", "Study Time Collected Unit", "Study Time T0 Event", "Study Time T0 Event Specify", "Name Reported"]
    component_header_columns=["User Defined ID","Name Reported","Result Value Reported","Result Unit Reported"]

    def __init__(self):
        display("labTests initialized")
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

        display(f"FULL study_file_info CONTENTS: {study_file_info}")

        display("FULL study_file_info DICTIONARY:")
        for key, value in study_file_info.items():
            display(f"  {key}: {value}")

        filename = study_file_info.get("Filename")
        table_code = study_file_info.get("Table Code")
        template = study_file_info.get("Template")

        display(f"template {template}")

        if template == "Lab Test":
            template = "labTests"

        default_visit = study_file_info.get("Default Visit")

        protocol = study_file_info.get("Protocol")
        name_reported_dropdown = study_file_info.get("Name Reported")
        labTest_type = study_file_info.get("Type")
        labTest_subtype = study_file_info.get("Subtype")

        display(f"CONFIRMED VALUES - Type: {labTest_type}, Subtype: {labTest_subtype}")

        display(f"LP process_study_file protocol 1 {protocol}")

        if protocol == "--Select--" or protocol == "":
            protocol = "Unspecified" 

        if protocol:
            protocol_mapping = dict(zip(protocols_df["NAME"], protocols_df["PROTOCOL_ACCESSION"]))
            if protocol in protocol_mapping:
                protocol = protocol_mapping[protocol]
            else:
                protocol = "Unspecified" 

        study_file_directory = study_file_directory.rstrip("\\/")

        study_file_path = os.path.abspath(os.path.join(study_file_directory,filename))

        display(f"LP study_file_directory: {study_file_directory}")
        display(f"LP filename: {filename}")
        display(f"LP study_file_path: {study_file_path}")

        table_data = {
            "tables":[table_code], 
            "template":template,
            "visit":default_visit,
            "protocol":protocol, 
            "name reported": name_reported_dropdown,
            "type":labTest_type,  
            "subtype":labTest_subtype 
        }

        display(f"LP table_data {table_data}")
        
        crfFileNames = [filename]  

        display(f"LP crfFileNames {crfFileNames}")

        datafile = cf.readAndModifyStudyFile(study_file_path, table_data, data_dictionary, planned_visits)

        planned_visit_id = ""
        if not datafile.empty:
            if 'PLANNED_VISIT_ID' in datafile.columns:
                planned_visit_id = datafile['PLANNED_VISIT_ID'].iloc[0]
            elif 'Planned Visit ID' in datafile.columns:
                planned_visit_id = datafile['Planned Visit ID'].iloc[0]
    
            # Handle NaN/None values
            if pd.isna(planned_visit_id):
                planned_visit_id = "Unspecified"
            planned_visit_id = str(planned_visit_id)

        visit_day_mapping = dict(zip(planned_visits["PLANNED_VISIT_ACCESSION"], planned_visits["MIN_START_DAY"]))

        display(f"planned_visits {planned_visits}")
        display(f"visit_day_mapping {visit_day_mapping}")

        study_time_collected = ""
        if not datafile.empty:
            if 'STUDY_TIME_COLLECTED' in datafile.columns:
                study_time_collected = datafile['STUDY_TIME_COLLECTED'].iloc[0]
            elif 'Study Time Collected' in datafile.columns:
                study_time_collected = datafile['Study Time Collected'].iloc[0]

        if pd.isna(study_time_collected) or study_time_collected == "" or study_time_collected == 99999:
            if planned_visit_id in visit_day_mapping:
                study_time_collected = visit_day_mapping[planned_visit_id]

                display(f"study_time_collected - MIN DAY  {study_time_collected }")

            else:
                study_time_collected = 99999
                display("Warning: No valid study time and no visit mapping available")                

        display(f"study_time_collected  {study_time_collected }")
        display(f"planned_visit_id {planned_visit_id}")

        # Create panel with the visit ID
        study_file_panel = LabTest_Panel(
            labTestNameReported=name_reported_dropdown,
            protocolId=protocol,
            plannedVisitId=planned_visit_id,  
            labTestType=labTest_type, 
            labTestSubtype=labTest_subtype,
            studyTimeCollected=study_time_collected,
            studyId=study_id,
            crfFileNames=crfFileNames
        )
        
        [panel_template,components_template,labTest_template_header] = cf.readTemplate(template, template_path=txt_template_path_full)  # self.text_template_path??
        
        components_template["LAB_TEST_PANEL_ACCESSION"]=''

        display(f"LP components_template 1 {components_template}")

        components_template = cf.datafileToComponents(datafile, data_dictionary, [table_code], components_template, template, workspace_id)

        display(f"LP components_template 2 {components_template}")

        try:
            loaded_lab = self.load_df(components_template, study_file_panel, crfFileNames=[filename], studyId=study_id, planned_visits=planned_visits)
        except Exception as e:
            display(f"ERROR in load_df(): {e}")
            import traceback
            display(traceback.format_exc())
            
        display(f"LP study_file_panel 1 {study_file_panel}")
        display(f"LP load_lab 1 {loaded_lab}")

        return [study_file_panel, components_template]

    def load_df(self, dataframe, panel, crfFileNames=None, studyId=None, planned_visits=None):
        labtest_data = {}

        display(f"dataframe.columns {dataframe.columns}")

        if 'Planned Visit ID' not in dataframe.columns:
            dataframe['Planned Visit ID'] = None         
   
        if 'Study Time Collected' not in dataframe.columns:
            dataframe['Study Time Collected'] = 99999
            study_time_unit = "Not Specified"
        else:
            study_time_unit = "Days"

        file_level_panel_id = panel.get_data().get('labTestPanelId')
        display(f"file_level_panel_id {file_level_panel_id}")

        visit_day_mapping = dict(zip(planned_visits["PLANNED_VISIT_ACCESSION"], planned_visits["MIN_START_DAY"]))
    
        # Group by both subject ID and visit ID to keep visits separate
        grouped = dataframe.groupby(['User Defined ID', 'Planned Visit ID', 'Study Time Collected'])
        
        for (subject_id, visit_id, study_time), group in grouped:
            # Create a new panel COPY for each unique visit

            if study_time == 99999 and visit_id in visit_day_mapping:
                study_time = visit_day_mapping[visit_id]
                study_time_unit = "Days"
                display(f"Using visit {visit_id} max day {study_time} for subject {subject_id}")
        

            panel_copy = LabTest_Panel(
              #  biosampleId = "tbd",
                labTestNameReported=panel.get_data().get('labTestNameReported'),
                protocolId=panel.get_data().get('protocolId'),
                plannedVisitId=str(visit_id),  
                labTestType=panel.get_data().get('labTestType'),
                labTestSubtype=panel.get_data().get('labTestSubtype'),
                studyTimeCollected=study_time,
                studyTimeCollectedUnit=study_time_unit,
                studyTimeT0Event = "Not Specified",
                studyTimeT0EventSpecify = "Not Specified",
                studyId=studyId,
                crfFileNames=crfFileNames
            )

            print(f"panel_copy {panel_copy}")

            panel_copy.set_data_value("labTestPanelId", file_level_panel_id)
        
            
            # Create new LabTest_Datum for this subject+visit combo
            labtest_data[(subject_id, visit_id, study_time)] = LabTest_Datum(
                labTest_panel=panel_copy,  # Uses the visit-specific panel
                subject_id=subject_id
            )
            
            # Process all rows for this subject+visit
            for _, row in group.iterrows():
                field_data = self.convert_result_columns_to_fields(row.to_dict())
                result = LabTest_ResultData(
                    studyId=studyId,
                    crfFileNames=crfFileNames,
                    **field_data
                )
                labtest_data[(subject_id, visit_id, study_time)].add_result_data(result)
        
        # Add all completed records to the main labTests object
        for record in labtest_data.values():
            self.add_record(record)    
  
    # TODO: Look about moving to ImmPort_Data Class
    def export_to_json(self, filename=None):
        valid = self.validate()
        if not valid:
            raise ValueError(f"Lab Test data is not valid: {valid}")
        
        check_directory_exists(filename)
        with open(filename, 'w')as fh:
            print(json.dumps(self.get_obj(), indent=4), file=fh)
        return
    
    
    def export_to_txt(self, filename=None):
        if not self.validate():
            raise ValueError("Lab Test data is not valid")
        
        separator = "\t"
        check_directory_exists(filename)

        display("DEBUG: Starting export_to_txt()")
        display(f"DEBUG: Total records to process: {len(self.data)}")

        with open(filename, 'w') as fh:
            # Header rows
            print(self.name, f"Schema Version {self.schemaVersion}", sep=separator, file=fh)
            print('Please do not delete or edit this column', file=fh)

            # Debug: Show all metadata first
            display("DEBUG: Full metadata inspection:")
            for i, datum in enumerate(self.data):
                display(f"DEBUG: Record {i}:")
                display(f"  Subject ID: {datum['metaData'].get('subjectId', 'MISSING')}")
                display(f"  Visit ID: {datum['metaData'].get('plannedVisitId', 'UNSPECIFIED')}")
                display(f"  Study time collected: {datum['metaData'].get('studyTimeCollected', 'UNSPECIFIED')}")
                display(f"  Results count: {len(datum['resultData'])}")
                for j, result in enumerate(datum['resultData']):
                    display(f"    Result {j}:")
                    display(f"      User ID: {result.get('userDefinedId', '')}")
                    display(f"      Name: {result.get('nameReported', '')}")
                    display(f"      Value: {result.get('resultValueReported', '')}")
                    display(f"      Unit: {result.get('resultUnitReported', '')}")
                    if 'plannedVisitId' in result:
                        display(f"      Result Visit ID: {result.get('plannedVisitId')}")

            # Group by subject AND visit
            grouped = {}
            display("\nDEBUG: Starting grouping process...")
            for i, datum in enumerate(self.data):
                subject = datum["metaData"].get("subjectId", "MISSING_SUBJECT")
                visit = datum["metaData"].get("plannedVisitId", "UNSPECIFIED")
                key = (subject, visit)
                
                display(f"DEBUG: Processing record {i}: Subject='{subject}', Visit='{visit}'")
                
                if key not in grouped:
                    display(f"  New group created for {key}")
                    grouped[key] = {
                        "meta": datum["metaData"], 
                        "results": []
                    }
                else:
                    display(f"  Adding to existing group {key}")
                    
                grouped[key]["results"].extend(datum["resultData"])
                display(f"  Group now has {len(grouped[key]['results'])} results")

            # Debug grouped data
            display("DEBUG: Grouped data structure:")
            for i, (key, group) in enumerate(grouped.items()):
                subject, visit = key
                display(f"Group {i}: Subject='{subject}', Visit='{visit}'")
                display(f"  Metadata keys: {list(group['meta'].keys())}")
                display(f"  Results count: {len(group['results'])}")
                for j, result in enumerate(group['results'][:3]):  # Show first 3 results
                    display(f"    Result {j}: {result.get('nameReported', '')} = {result.get('resultValueReported', '')}")

            # Find max results per visit
            most_result_data = max(len(g["results"]) for g in grouped.values()) if grouped else 0
            display(f"DEBUG: Max results per visit: {most_result_data}")

            # Write headers
            headers = labTests.panel_header_columns + ['Result Separator Column'] + \
                    labTests.component_header_columns * most_result_data
            display(f"DEBUG: Headers ({len(headers)} columns):")
            display(headers)
            print(*headers, sep=separator, file=fh)

            # Write data
            display("DEBUG: Writing data rows...")
            for i, (key, group) in enumerate(grouped.items()):
                subject, visit = key
                display(f"DEBUG: Writing row {i} for Subject='{subject}', Visit='{visit}'")
                
                row = ['']  # Column name
                display(f"  Initial row: {row}")
                
                # Add panel columns
                panel_cols = self.populate_panel_columns(group["meta"])
                display(f"  Panel columns ({len(panel_cols)}): {panel_cols}")
                row.extend(panel_cols)
                
                # Add separator
                row.append('')
                display(f"  After separator: {len(row)} columns")
                
                # Add results
                for j, result in enumerate(group["results"]):
                    result_cols = self.populate_component_column_set(result)
                    display(f"    Adding result {j}: {result_cols}")
                    row.extend(result_cols)
                
                # Pad if needed
                padding_needed = most_result_data - len(group["results"])
                if padding_needed > 0:
                    padding = [''] * len(labTests.component_header_columns) * padding_needed
                    display(f"  Adding padding: {padding_needed} result slots")
                    row.extend(padding)
                
                display(f"  Final row length: {len(row)}")
                display(f"  First 5 elements: {row[:5]}")
                print(*row, sep=separator, file=fh)

        display("DEBUG: Export completed successfully")
        return


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

        field_dict = dict(map(lambda x: (x[1], column_dict.get(x[0],"")), mapping_dict.items()))

        filtered_dict = dict(filter(lambda elem: ((type(elem[1]) != float and elem[1] not in ['','userDefinedId']) or str(elem[1]) not in ['nan', '', 'userDefinedId']), field_dict.items()))

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
        LabTest_Panel.iterable_counter +=1

        filename_string = "-".join(crfFileNames)

        self.data={}

        self.set_data_value("labTestPanelId", f"{studyId}_{filename_string}_Panel{LabTest_Panel.iterable_counter}")
        self.set_data_value("studyId", studyId)
        self.set_data_value("protocolId", protocolId)
        self.set_data_value("plannedVisitId", str(plannedVisitId))
        self.set_data_value("labTestType", labTestType)
        self.set_data_value("labTestSubtype", labTestSubtype)
        self.set_data_value("studyTimeCollected", studyTimeCollected)
        self.set_data_value("studyTimeCollectedUnit", studyTimeCollectedUnit)
        self.set_data_value("studyTimeT0Event", studyTimeT0Event)
        self.set_data_value("studyTimeT0EventSpecify", studyTimeT0EventSpecify)
        self.set_data_value("labTestNameReported", labTestNameReported)

        display(f"DEBUG: Panel initialized with visit ID: {plannedVisitId}")

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

    iterable_counter = 0
    truncate_long_fields = True
    validator = "labTests.ResultData"

    data_fields = load_data_fields(validator)

    result_unit_reported_synonyms = {
        "g":"gm",
        "%":"percentage",
        "mcg":"ug",
        "hr":"Hour",
        "cms":"cm",
        "kgs":"kg",
        "months":"Month",
        "years":"Year"
    }

    enumFields = dict(filter(lambda x: "enum" in x[1], data_fields.items()))
  
    def __init__(self, study_file_info=None, nameReported=None, studyId=None, crfFileNames=[], **kwargs):

        LabTest_ResultData.iterable_counter +=1

        if crfFileNames is not None:
            filename_string = "_".join(crfFileNames)
        else:
            filename_string = "NoCRF"

        self.data={}
        new_user_id = f"{studyId}_{filename_string}_RD{LabTest_ResultData.iterable_counter}"
        
        self.set_data("userDefinedId", new_user_id)
        self.set_data("nameReported", nameReported)

        del kwargs["userDefinedId"]
        
        for key, value in kwargs.items():
            # Pre-process numeric values
            if isinstance(value, (int, float, str)):
                try:
                    if key.endswith("ValueReported") or key in ["studyTimeCollected"]:
                        value = float(value) if '.' in str(value) else int(value)
                except (ValueError, TypeError):
                    pass

            # TODO: need a way to identify/report ALL instances, and then allow user to specify mapping in GUI
            if key in self.enumFields and value not in self.enumFields[key]["enum"]:
                if key.endswith("UnitReported"):
                    if value in self.result_unit_reported_synonyms:
                        ig.main_logger.write(
                            level="info",
                            message=f"\tSuggest substituting '{self.result_unit_reported_synonyms[value]}' for '{value}' for field '{key}' - {nameReported}"
                        )
                    else:
                        ig.main_logger.write(
                            level="info",
                            message=f"Value '{value}' for field '{key}' is not a preferred term - {nameReported}"
                        )
                else:
                    ig.main_logger.write(
                        level="warn",
                        message=f"Value '{value}' for field '{key}' is not valid - {nameReported}"
                    )

            self.set_data_value(key, value)

