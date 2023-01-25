import os
import jsonschema
import json
import ImmPortCurationTool.curationFunctions as cf
import ImmPortCurationTool.immport_gui as ig
from pathlib import Path
import platform

json_schema_template_path   = "templates/json-templates"
txt_template_path           = "templates/txt-templates"

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

    ref_resolver_path = os.path.abspath(os.path.join(os.getcwd(),json_schema_template_path,schema_name))
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
                    message=f"Planned Visit is missing"
                )
            return True
        else:
            last_error=error
            ig.main_logger.write(
                level="error",
                message=f"Some other Validation Error... {error}",
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
    if field_type == "string" or field_type == str:
        return (str, isinstance(value, str))
    elif field_type == "number":
        return (float, isinstance(value, float))
    elif field_type == 'integer':
        return (int, isinstance(value, int))
    elif field_type == 'array' or field_type == list:
        return (list, isinstance(value, list))
    raise TypeError(f"Type '{field_type}' not handled")

def check_data_type(value, key_properties, key):
    field_type = key_properties["type"]
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
    with open(os.path.abspath(os.path.join(json_schema_template_path,validator+".json"))) as fh_json_file:
        json_data = json.load(fh_json_file)
        return json_data['properties']
class ImmPort_Data: 
    #TODO Read in from file
    schemaVersion = "3.36"
    #Stored in schemas as properties.schemaVersion.enum[0]
    #It would be good to read this in rather than hard-coding

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
        
        
    def process_study_file(self, study_file_info=None, study_file_directory=None, data_dictionary=None, planned_visits=None, study_id=None, workspace_id=None, name_reported=None):
        filename = study_file_info.get("Filename")
        table_code = study_file_info.get("Table Code")
        assessment_name = study_file_info.get("Assessment Name")
        template = study_file_info.get("Template")
        if template == "Assessment":
            template = "assessments"
        default_visit = study_file_info.get("Default Visit")

        study_file_path = os.path.abspath(os.path.join(study_file_directory,filename))
        table_data = {
            "tables":[table_code], 
            "assessment_type":assessment_name,
            "template":template,
            "visit":default_visit
        }
        if name_reported is None:
            name_reported=ig.getStudyFileReportedName(filename)

        study_file_panel = Assessment_Panel(
            nameReported=name_reported,
            assessmentType=assessment_name,
            crfFileNames=[filename],
            studyId=study_id
        )

        datafile = cf.readAndModifyStudyFile(study_file_path, table_data, data_dictionary, planned_visits)
        #Read Templates
        [assessment_panel_template,assessment_components_template,assessment_template_header] = cf.readTemplate(template, template_path=txt_template_path)  # self.text_template_path??
        assessment_components_template["ASSESSMENT_PANEL_ACCESSION"]=''
        assessment_components_template=cf.datafileToComponents(datafile,data_dictionary,[table_code],assessment_components_template,workspace_id)
        
        loaded_assessment = self.load_df(assessment_components_template,study_file_panel,
            crfFileNames=[filename],
            studyId=study_id)

        # Iterate through template DF and create Assessment_Datum
        return [study_file_panel, assessment_components_template]

    def load_df(self, dataframe, panel, crfFileNames=None, studyId=None):
        assessment_data = {}

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
        filtered_dict = dict(filter(lambda elem: ((type(elem[1]) != float and elem[1] not in ['','userDefinedId']) or str(elem[1]) not in ['nan', '', 'userDefinedId']), field_dict.items()))
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
    """Class to hold data to go into the Results section of the Assessment template.
       Each instance is equiavlent to a single response to a question. Most likely,
       a single line in a result file.

    Parent Class:
        ImmPort_Data
    
    Attributes:
        plannedVisitId: str
        nameReported: str
        studyDay: number
    
    Variables:
        iterable_counter: int (Init: 0)- used to generate an incremental counter
        truncate_long_fields: Bool (Init: True) - used to truncate strings based on schema
        validator: str (Init: assessments.ResultData) - used to lookup jsonschema for validation
        
        data_fields: dict - used to validate types and string length

    Methods:
    """
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


schema_store = get_schema_store(json_schema_template_path)
