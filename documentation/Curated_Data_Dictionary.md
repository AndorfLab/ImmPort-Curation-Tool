# Instructions for Curation of the Data Dictionary

The ImmPort tool uses a curated data dictionary to transform study files into completed ImmPort Templates. The curated data dictionary provides context to the study files such as the verbatim question and units, as well as specifying which fields contain the Subject ID and Visit.


Currently, the curated data dictionary should be a csv file with at least the columns specified in the table below. While additional columns are acceptable, the specified [Data Dictionary Columns](#data-dictionary-columns) below are required exactly as specified.

## [Example Curated Data Dictionary](./Example_Data_Dictionary.md)
An example of a curated data dictionary with explanations of its usage. The data dictionary, without explanations, can be [downloaded here](./curated_data_dictionary.csv)

## Data Dictionary Columns
If a value is not applicable for a row, such as "Unit", leave it blank.


| Column Name | Description | Acceptable Values | Example(s) |
| ----------- | ----------- | ----------------- | ------- |
| Table Name  | Short Code that signifies a unique collection form/eCRF/Instrument. This field specifies to which form a question belongs.| *Any string* | MD1 |
| Field Name | The name/ID of the question/field | *Any unique string within a form* | LATEXAL |
| Field Description | A short, human readable description of the field | *Any unique string within a form* | Latex Allergy |
| Code List Values | A mapping of coded values (0,1,2) to human-readable values (No, Yes, Unknown) | Format is a=A, b=B, c=C, ... where lowercase letters are the coded values present in the data files and uppercase letters are the human-readable values | 0=No, 1=Yes, 9=Unknown |
| Unit | The unit that should be associated with the value. A value of [SPLIT] can be used if the recorded value includes the unit. | [^1]*Any unique string within a form* or [SPLIT]  | years, [SPLIT] |
| Column Mappings | [^3]Specify if the value provides the Study Day, User Defined ID, or Visit information for the records. Can be used to exclude the data from the ImmPort template by using the value of "[NA]" | Study Day, User Defined ID, Visit, [NA] | Study Day |
| Map To Planned Visit | [^2]**Only use if the Column Mapping is "Visit"!** Used if 1 or multiple values in the "Code List Values" do not match the Planned Visits name. | JSON dictionary where the key is the decoded visit name, and the value is the name of the visit from the planned visits file | {"Visit 0":"Baseline", "Visit 12": "Week 12"} |
| Verbatim Question | The actual text used on the physical or electronic form. If the question is a multi-part question (i.e. 4a) then all parts of the text should be present | *Any unique string within a form*. If a value of [Same] is used, the verbatim question text will be copied from the "Field Description" | Do you have any of the following allergies? Latex Allergy |
| Who is Assessed | If the question is about an individual who is not the participant, the relationship of the individual to the participant should be specified | *Any logical familial relationship* | Father, Mother, Sibling, Sibling 1, Brother |
| Override Study Day | [^4]Used to specify a specific field to set the question's Study Day value, instead of using the field that has the value "Study Day" in the "Column Mappings". | *Any string in the "Field Name" column for this form (the value in the "Table Name" column must be the same between this field and field specified)* | LATEX_DATE |
| Age At Onset Reported | Used to specify the field that contains the value specifying the age the individual was at the onset of the condition, event, etc. | *Any string in the "Field Name" column for this form (the value in the "Table Name" column must be the same between this field and field specified)* | LATEX_ONSET |
| Age At Onset Unit Reported | Used to specify the unit for the onset of the condition, event, etc | *Any logical age unit* | Months |
| Location | The anatomical location on the body associated with the question | *Any logical anatomical site* | Skin |

[^1]: Unit [SPLIT]: This special code will split at the first space, placing everything before the space as the field/question value and everything after as the unit.

[^2]: Map To Planned Visit: If the value for a visit, or it's decoded value from the code list values, does not exactly match the name of the visit from the planned visits file, a mapping can be given using a JSON dictionary format. The format is: {"[Study_file_visit_value]":"[Planned_visit_file_value]"}, where [Study_file_visit_value] is the value from the study file (or the decoded value if code list is used), and [Planned_visit_file_value] is the name of the analogous visit that is present in the planned visits file. 

[^3]: Column Mappings: Often a form will contain a few questions that apply to every field. These include the participant ID (User Defined ID), specific visit (Visit), and study day (Study Day). Each of these values would apply to all questions on the form and are not themselves actual questions. By using these special designations, the values of these questions will be pivoted to the appropriate columns in the ImmPort Template. To ignore a question, "[NA]" can be used. This will skip the question when generating the completed templates and can be used for PHI or operational only fields such as Site Name or Completion Status.

[^4]: This will take precedence over using the value from the field with Study Day specified in the Column Mappings column. An instance of this would be a medical history form with two related questions: What was the severity of your last latex reaction. What was the date of the latex reaction. In this example, the second question provides the study day of the first question. 
