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
| Unit | The unit that should be associated with the value | [^1]*Any unique string within a form*. A value of [SPLIT] can be used if the recorded value includes the unit. | years, kg, [SPLIT] |
| Map To Visit | [^2]Used to map a decoded visit name to the name used in the planned visits file | JSON dictionary where the key is the decoded visit name, and the value is the name of the visit from the planned visits file | {"Visit 0":"Baseline", "Visit 12": "Week 12"} |
| Column Mappings | [^3]Used to pivot the corresponding value to a specific column for every question, or to specify that the question should be skipped. | [NA], Study Day, User Defined ID, [VISIT] | [NA], Study Day, User Defined ID, [VISIT] |
| Verbatim Question | The actual text used on the physical or electronic form. If the question is a multi-part question (i.e. 4a) then all parts of the text should be present | *Any unique string within a form* | Do you have any of the following allergies? Latex Allergy |
| Who is Assessed | If the question is about an individual who is not the participant, the relationship of the individual to the participant should be specified | *Any logical familial relationship* | Father, Mother, Sibling, Sibling 1, Brother |
| Study Day | [^4]Used to specify the field that contains the value of the study day for this question. | *Any string in the "Field Name" column for this form (the value in the "Table Name" column must be the same between this field and field specified)* | LATEX_DATE |
| Age At Onset Reported | Used to specify the field that contains the value specifying the age the individual was at the onset of the condition, event, etc. | *Any string in the "Field Name" column for this form (the value in the "Table Name" column must be the same between this field and field specified)* | LATEX_ONSET |
| Age At Onset Unit Reported | Used to specify the unit for the onset of the condition, event, etc | *Any logical age unit* | Months |
| Location | The anatomical location on the body associated with the question | *Any logical anatomical site* | Skin |

[^1]: Unit [SPLIT]: This special code will split at the first space, placing everything before the space as the field/question value and everything after as the unit.

[^2]: Map to Visit: If the value for a visit, or it's decoded value from the code list values, does not exactly match the name of the visit from the planned visits file, a mapping can be given using a JSON dictionary format. The format is: {"[Study_file_visit_value]":"[Planned_visit_file_value]"}, where [Study_file_visit_value] is the value from the study file (or the decoded value if code list is used), and [Planned_visit_file_value] is the name of the analogous visit that is present in the planned visits file. 

[^3]: Column Mappings: Often a form will contain a few questions that apply to every field. These include the participant ID (User Defined ID), specific visit ([Visit]), and study day (Study Day). Each of these values would apply to all questions on the form and are not themselves actual questions. By using these special designations, the values of these questions will be pivoted to the appropriate columns in the ImmPort Template. To ignore a question, "[NA]" can be used. This will skip the question when generating the completed templates and can be used for PHI or operational only fields such as Site Name or Completion Status.

[^4]: This will take precidence over using the value from the field with [VISIT] specified in the Column Mappings column.



## Data Dictionary Validation
A data dictionary validator is scheduled for future work.

## Example Data Dictionary
|Table Name|Field Name|Field Description|Code List Values|Unit|Map To Visit|Column Mappings|Verbatim Question|Who is Assessed|Study Day|Age At Onset Reported|Age At Onset Unit Reported|Location|
|---|---|---|---|---|---|---|---|---|---|---|---|---|
|DEM|HINC01|Household income|0=$0 - $24,999, 1=$25,000 - $49,999, 2=$50,000 - $74,999, 3=$75,000 - $99,999, 4=$100,000+, 5=Declined||||[Same]||||||
|DEM|HNO|Number in household|||||Number living in the household?||||||
|DEM|PATID|Participant ID||||User Defined ID|||||||
|DEM|SITE|Center|BS=Boston,SD=San Diego,SE=Seattle|||[NA]|||||||
|MD|PATID|Participant ID||||User Defined ID|||||||
|MD|VISIT|Visit|0=Visit 0, 1=Visit 6, 2=Visit 12||{"Visit 0" : "Baseline", "Visit 6" : "Week 6", "Visit 12" : "Week 12"}|[Visit]|||||||
|MD|GENDER|Gender|0=Male, 1=Female||||[Same]||||||
|MD|HEIGHTCM|Height (cm)||cm|||[Same]||||||
|MD|WEIGHTKG|Weight (kg)||kg|||[Same]||||||
|MD|PREG|Pregnant|0=No, 1=Yes, 9=Unknown, 99=Not Applicable||||Is the patient pregnant?||||||
|MD|ALEGG|Egg Allergy|0=No, 1=Yes, 9=Unknown||||Is the patient allergic to: Egg|||ALEGGAGE|years||
|MD|ALMILK|Milk Allergy|0=No, 1=Yes, 9=Unknown||||Is the patient allergic to: Milk|||ALMILKAGE|years||
|MD|ALLATEX|Latex Allergy|0=No, 1=Yes, 9=Unknown||||Is the patient allergic to: Latex|||ALLATEXAGE|years||
|MD|DATE|Date||||Study Day|||||||
|MD|ALEGGAGE|Egg Allergy Onset|||||||||||
|MD|ALMILKAGE|Milk Allergy Onset|||||||||||
|MD|ALLATEXAGE|Latex Allergy Onset|||||||||||
|MD|PATALL|Paternal Allergy|0=No, 1=Yes, 9=Unknown||||Does the father have allergies|Father|||||
|MD|MATALL|Maternal Allergy|0=No, 1=Yes, 9=Unknown||||Does the mother have allergies|Mother|||||
