# Instructions for Curation the Data Dictionary

The ImmPort tool uses a curated data dictionary to transform study files into completed ImmPort Templates. The data dictionary adds extra information such as verbatim question text and units. It also allows the specification of fields that should pivot into a column for every field on the form, such as the subject ID or visit number. 

Currently, the curated data dictionary should be a csv file with at least the columns specified in the table below. While additional columns are acceptible, the specified columns below are required.

## Data Dictionary Columns
| Column Name | Description | Acceptable Values | Example |
| ----------- | ----------- | ----------------- | ------- |
| Table Name  | Short Code that signifies a unique collection form/eCRF/Instrument. This field specifies to which form a question belongs.| *Any string* | MD1 |
| Field Name | The name/ID of the question/field | *Any unique string within a form* | LATEXAL |
| Field Description | A short, human readable description of the field | *Any unique string within a form* | Latex Allergy |
| Code List Values | A mapping of coded values (0,1,2) to human-readable values (No, Yes, Unknown) | Format is a=A, b=B, c=C, ... where lowercase letters are the coded values present in the data files and uppercase letters are the human-readable values | 0=No, 1=Yes, 9=Unknown |
| Unit | The unit that should be associated with the value | *Any unique string within a form*. A value of [SPLIT] can be used if the recorded value includes the unit.[^1] | years, kg, [SPLIT] |
| Map To Visit |  |  |  |
| Column Mappings | Used to pivot the corresponding value to a specific column for every question, or to specify that the question should be skipped.[^2] | [NA], Study Day, User Defined ID, [VISIT] | [NA], Study Day, User Defined ID, [VISIT] |
| Verbatim Question | The actual text used on the physical or electronic form. If the question is a multi-part question (i.e. 4a) then all parts of the text should be present | *Any unique string within a form* | Do you have any of the following allergies? Latex Allergy |
| Who is Assessed | If the question is about an individual who is not the participant, the relationship of the individual to the participant should be specified | *Any logical familial relationship* | Father, Mother, Sibling, Sibling 1, Brother |
| Study Day | Used to specify the field that contains the value of the study day for this question.[^3] | *Any string in the "Field Name" column for this form (the value in the "Table Name" column must be the same between this field and field specified)* | LATEX_DATE |
| Age At Onset Reported | Used to specify the field that contains the value specifying the age the individual was at the onset of the condition, event, etc. | *Any string in the "Field Name" column for this form (the value in the "Table Name" column must be the same between this field and field specified)* | LATEX_ONSET |
| Age At Onset Unit Reported | Used to specify the unit for the onset of the condition, event, etc | *Any logical age unit* | Months |
| Location | The anatomical location on the body associated with the question | *Any logical anatomical site* | Skin |

[^1]: Unit [SPLIT]: This special code will split at the first space, placing everything before the space as the field/question value and everything after as the unit.

[^2]: Column Mappings: Often a form will contain a few questions that apply to every field. These include the participant ID (User Defined ID), specific visit ([Visit]), and study day (Study Day). Each of these values would apply to all questions on the form and are not themselves actual questions. By using these special designations, the values of these questions will be pivoted to the appropriate columns in the ImmPort Template. To ignore a question, "[NA]" can be used. This will skip the question when generating the completed templates and can be used for PHI or operational only fields such as Site Name or Completion Status.

[^3]: This will take precidence over using the value from the field with [VISIT] specified in the Column Mappings column.



## Data Dictionary Validation
A data dictionary validator is scheduled for future work.

