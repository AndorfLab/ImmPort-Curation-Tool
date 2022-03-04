import os
from attr import field
import jsonschema
import json

schema_search_path="ImmPort_Curation_Tool/templates/json-templates"


def get_schema_store(schema_search_path):
    schema_store = {}
    fnames = os.listdir(schema_search_path)
    for fname in fnames:
        if fname.endswith(".json"):
            with open(os.path.join(schema_search_path, fname)) as schema_fd:
                schema = json.load(schema_fd)
                schema_store[fname] = schema
    return schema_store

def validate_data(data, schema_name=None):
    try: 
        schema_store 
    except:
        raise NotImplementedError("Schemas have not been loaded")
    
    if schema_name is None:
        raise ValueError("Schema name not provided")
    if not schema_name.endswith(".json"):
        schema_name+=".json"
    
    schema = schema_store.get(schema_name)
    if schema is None:
        raise NotImplementedError("Missing Schema for '%s'" % schema_name)

    ref_resolver_path = os.path.abspath(os.path.join(os.getcwd(),schema_search_path,schema_name))
    resolver = jsonschema.RefResolver("file://%s" % ref_resolver_path, schema, store=schema_store)
    try:
        jsonschema.Draft4Validator(schema, resolver=resolver).validate(data)
        return True
    except jsonschema.ValidationError as error:
        print("Validation Error")
        print(error)
        pass
    except jsonschema.SchemaError as error:
        print("Schema Error")
        print(error)
        pass
    
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
                raise TypeError(f"{value[idx]} with type {type(value[idx])} given for {key} at index {idx} - expected {field_type}")
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
    if len(value)>=maxLength:
        return True
    if truncate:
        return value[0:maxLength]

    raise ValueError("Value exceeds max length of {maxLength} for field {key}: {maxLength[0:25]}...")

    
class ImmPort_Data: 
   
    def print_obj(self):
        print_data = {}
        for attr in self.__dict__:
            if attr.startswith('__'):
                continue
            print_data[attr]=self[attr]
        return print_data


    def validate(self):
        return validate_data(self.get_data(), schema_name = self.get_validator())
    
    def get_data(self):
        return self.data

    def set_data(self, key, value):
        self.data[key] = value
        return 

    def get_validator(self):
        return self.validator

    def set_data_value(self, key, value):
        key_properties = self.get_data_key_properties(key)
        # print(key, value)
        if "type" not in key_properties:
            raise AttributeError("{key} has no 'type' property in the schema")
        value = check_data_type(value, key_properties, key)
        # print(f"Value after check: {value}")
        if "maxLength" in key_properties:
            check_data_length(value, key_properties["maxLength"], truncate=type(self).truncate_long_fields, key=key)
        
        self.set_data(key,value)

    def get_data_key_properties(self, key):
        if key in type(self).data_fields:
            return type(self).data_fields[key]
        raise AttributeError(f"{key} is not a data property of {(type(self))}" )

class Assessment(ImmPort_Data):
    filename="assessments.json"
    name="assessments"
    schemaVersion = "3.34"
    templateType='combined-result'
    validator = "assessments"

    panel_header_columns=["Column Name","Subject ID","Assessment Panel ID","Study ID","Name Reported","Assessment Type","Status","CRF File Names"]
    component_header_columns=["User Defined ID","Planned Visit ID","Name Reported","Study Day","Age At Onset Reported","Age At Onset Unit Reported","Is Clinically Significant","Location Of Finding Reported","Organ Or Body System Reported","Result Value Reported","Result Unit Reported","Result Value Category","Subject Position Reported","Time Of Day","Verbatim Question","Who Is Assessed"]

    def __init__(self):
        self.data=[]

    def add_record(self, record):
        self.data.append(record.__dict__)

    def get_obj(self):
        obj = {
            "fileName":self.filename,
            "name":self.name,
            "schemaVersion":self.schemaVersion,
            "templateType":self.templateType
        }
        obj["data"] = self.get_data()
        return obj
    
    def validate(self):
        return validate_data(self.get_obj(), schema_name = self.get_validator())

    def export_to_json(self, filename=None):
        if not self.validate():
            raise ValueError("Assessment data is not valid")
        with open(filename, 'w')as fh:
            print(json.dumps(self.get_obj(), indent=4), file=fh)
        return

    def export_to_txt(self, filename=None):
        separator = "\t"
        with open(filename, 'w') as fh:

            print(self.name, f"Schema Version {self.schemaVersion}", sep=separator, file=fh)
            print('Please do not delete or edit this column', file=fh)

            most_result_data = max(list(map(lambda x: len(x["resultData"]), self.data)))
            print(*Assessment.panel_header_columns,'Result Separator Column', (*Assessment.component_header_columns * most_result_data), sep=separator, file=fh)

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




class Assessment_Datum(ImmPort_Data):

    def __init__(self, assessment_panel=None):
        metadata_obj = Assessment_MetaData(assessment_panel=assessment_panel)
        self.set_metadata(metadata_obj)
        self.resultData = []
    
    def set_metadata(self, metadata_obj):
        self.metaData = metadata_obj.get_data()

    def add_result_data(self, result_data_obj):
        self.resultData.append(result_data_obj.get_data())

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

        self.data={}
        self.set_data_value("assessmentPanelId", "Panel%s" % Assessment_Panel.iterable_counter)
        self.set_data_value("nameReported", nameReported)
        self.set_data_value("assessmentType", assessmentType)
        self.set_data_value("studyId", studyId)
        self.set_data_value("crfFileNames", crfFileNames)

class Assessment_MetaData(ImmPort_Data):
    iterable_counter = 0
    truncate_long_fields = True
    validator = "assessments.MetaData"

    data_fields={
        "subjectId": {
            "type": "string",
            "maxLength": 100
        },
        "assessmentPanelId": {
            "type": "string",
            "maxLength": 100
        },
        "studyId": {
            "type": "string"
        },
        "nameReported": {
            "type": "string",
            "maxLength": 125
        },
        "assessmentType": {
            "type": "string",
            "maxLength": 125
        },
        "status": {
            "type": "string",
            "maxLength": 40
        },
        "crfFileNames": {
            "type": "array",
            "items": {
                "type": "string",
                "maxLength": 240
            }
        }
    }
    
    def __init__(self, assessment_panel=None):
        Assessment_MetaData.iterable_counter +=1

        self.data={}
        self.data.update(assessment_panel.get_data())

        self.set_data("subjectId", "Subject%s" % Assessment_MetaData.iterable_counter)

class Assessment_ResultData(ImmPort_Data):
    iterable_counter = 0
    truncate_long_fields = True
    validator = "assessments.ResultData"

    data_fields={
            "userDefinedId": {
                "type": "string",
                "maxLength": 200
            },
            "plannedVisitId": {
                "type": "string"
            },
            "nameReported": {
                "type": "string",
                "maxLength": 150
            },
            "studyDay": {
                "type": "number"
            },
            "ageAtOnsetReported": {
                "type": "number"
            },
            "ageAtOnsetUnitReported": {
                "type": "string",
                "enum": [
                    "d.p.c.",
                    "Days",
                    "Hours",
                    "Minutes",
                    "Months",
                    "Not Specified",
                    "Seconds",
                    "Weeks",
                    "Years"
                ]
            },
            "isClinicallySignificant": {
                "type": "string",
                "maxLength": 1
            },
            "locationOfFindingReported": {
                "type": "string",
                "maxLength": 256
            },
            "organOrBodySystemReported": {
                "type": "string",
                "maxLength": 100
            },
            "resultValueReported": {
                "type": "string"
            },
            "resultUnitReported": {
                "type": "string",
                "enum": [
                    "AFU",
                    "AI",
                    "Antibody titer",
                    "AU/ml",
                    "BCLC Stage",
                    "Beats per Minute",
                    "Body Mass Index Finding",
                    "Boolean",
                    "Breaths per Minute",
                    "C",
                    "Capsule Dosing Unit",
                    "categorical",
                    "cells",
                    "cells/ml",
                    "cells/ul",
                    "cm",
                    "Count",
                    "Cq",
                    "Ct",
                    "Day",
                    "Delta Ct",
                    "Delta Delta Ct",
                    "DK units/ml",
                    "Donor Information",
                    "Dose",
                    "F",
                    "FPKM",
                    "g/dl",
                    "g/l",
                    "Gender",
                    "gm",
                    "Grade",
                    "HAU",
                    "Hour",
                    "in",
                    "IU",
                    "iu/l",
                    "IU/ml",
                    "K",
                    "Kallikrein Inactivator Unit per Milliliter",
                    "kg",
                    "kg/m2",
                    "l",
                    "L/sec",
                    "M",
                    "MFI at 90th percentile",
                    "mg",
                    "mg/dl",
                    "mg/l",
                    "mg/ml",
                    "miu/ml",
                    "ml",
                    "mL/min",
                    "mL/min/(173/100).m2",
                    "mL/min/mmHg",
                    "mM",
                    "mmHg",
                    "MOI",
                    "Month",
                    "Multidimensional Fatigue Inventory",
                    "ng",
                    "ng/dl",
                    "ng/ml",
                    "ng/nl",
                    "ng/ul",
                    "nl",
                    "nM",
                    "Not Specified",
                    "NPX",
                    "Number of Episodes",
                    "optical density",
                    "percentage",
                    "PFU",
                    "PFUe",
                    "pg",
                    "pg/mg creatinine",
                    "pg/ml",
                    "pg/nl",
                    "pg/ul",
                    "pl",
                    "pM",
                    "Point",
                    "Pound",
                    "RPKM",
                    "Scale",
                    "Schirmer Test Wetting",
                    "Score",
                    "stim/unstim fold change",
                    "TCID50",
                    "titer",
                    "TPM",
                    "ug",
                    "ug/dl",
                    "ug/kg",
                    "ug/l",
                    "ug/ml",
                    "ug/ul",
                    "ugEq/g",
                    "uiu/ml",
                    "ul",
                    "uM",
                    "umol/l",
                    "units/ml",
                    "Week",
                    "Year",
                    "Yes, No, or Unknown Response"
                ]
            },
            "resultValueCategory": {
                "type": "string",
                "maxLength": 40
            },
            "subjectPositionReported": {
                "type": "string",
                "maxLength": 40
            },
            "timeOfDay": {
                "type": "string",
                "maxLength": 40
            },
            "verbatimQuestion": {
                "type": "string",
                "maxLength": 250
            },
            "whoIsAssessed": {
                "type": "string",
                "maxLength": 40
            }
        }

    def __init__(self, plannedVisitId=None, nameReported=None, studyDay=None):
        Assessment_ResultData.iterable_counter +=1
        
        self.data={}
        self.set_data("userDefinedId", "RD%s" % Assessment_ResultData.iterable_counter)
        self.set_data("plannedVisitId", plannedVisitId)
        self.set_data("nameReported", nameReported)
        self.set_data("studyDay", studyDay if studyDay is not None else 99999) 



schema_store = get_schema_store(schema_search_path)






