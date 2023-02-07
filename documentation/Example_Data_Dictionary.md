
# Example Data Dictionary
This example curated data dictionary specifies how specific fields/values work. Read the corresponding footnote for the items for an explanation.

A copy of this curated data dictionary can be [downloaded here](./curated_data_dictionary.csv).


|Table Name|Field Name|Field Description|Code List Values|Unit|Map To Planned Visit|Column Mappings|Verbatim Question|Who is Assessed|Override Study Day|Age At Onset Reported|Age At Onset Unit Reported|Location|
|-----|-----|-----|-----|-----|-----|-----|-----|-----|-----|-----|-----|-----|
|DEM|HNO|Number in household|||||Number living in the household?[^1]||||||
|DEM|HINC01|Household income|0=$0 - $49,999, 1=$50,000 - $99,999, 2=$100,000+, 3=Declined||||[Same][^2]||||||
|DEM|VISIT|Visit|0=Baseline, 1=Week 6|||Visit[^3]|||||||
|DEM|PATID|Participant ID||||User Defined ID[^4]|||||||
|DEM|SITE|Center|BS=Boston,SD=San Diego,SE=Seattle|||[NA][^5]|||||||
|DEM|PHASE|Trial Phase||||[NA]|||||||
|MD|PATID|Participant ID||||User Defined ID|||||||
|MD|VISIT|Visit|0=Visit 0, 2=Visit 12||{"Visit 0" : "Baseline", "Visit 12" : "Week 12"}[^6]|Visit|||||||
|MD|HEIGHTCM|Height (cm)||cm[^7]|||[Same]||||||
|MD|PREG|Pregnant|0=No, 1=Yes, 99=NA||||Is the patient pregnant?||||||
|MD|ALEGG|Egg Allergy|0=No, 1=Yes, 9=Unknown||||Is the patient allergic to: Egg|||ALEGGAGE[^8]|years[^9]||
|MD|DATE|Date||||Study Day[^10]|||||||
|MD|HIVES|Hives|0=0, 1=1, 2=2, 3=3, 4=4, 5=5, 6=6|USA Score|||What was the score of your last hive episode?||HIVESDT[^11]|||HIVESLOC[^12]|
|MD|HIVESLOC|Hives Location|||||||||||
|MD|HIVESDT|Hives Date|||||||||||
|MD|ALLTEST|Allergy Test|||||When was your last allergy test?||ALLTESTDT|||Back[^13]|
|MD|ALLTESTDT |Allergy Test Date|||||||||||
|MD|ALEGGAGE|Egg Allergy Onset|||||||||||
|MD|PATALL|Paternal Allergy|0=No, 1=Yes, 9=Unknown||||Does the father have allergies|Father[^14]|||||


Footnotes
[^1]: "Number living in the household?": This value specifies the exact, verbatim question that was asked to the participant. 

[^2]: [Same] in "Verbatim Question" column. This value specifies that the verbatim question text is the same as the value in the "Field Description". Instead of typing or copying the value, a value of "[Same]" can be specified.

[^3]: "Visit" in the "Column Mappings" column: This value specifies that the "VISIT" field in the DEM study file contains the planned visit information for all records in the DEM study file.

[^4]: "User Defined ID" in the "Column Mappings" column: This value specifies that the "PATID" field in the DEM study file contains the Subject ID/User Defined ID for each record in the DEM study file.

[^5]: "[NA]" in the "Column Mappings" column: This special value specifies that this field should be ignored when converting the study file to an ImmPort template. Commonly this could be a PHI field, or operational field that provides no data benefit.

[^6]: JSON dictionary in "Map To Planned Visit" column: Only use if the Column Mapping is "Visit"! Used if 1 or multiple values in the "Code List Values" do not match the Planned Visits name. In this case, the values "Visit 0" and "Visit 12", as specified in the "Code List Values" column, are not valid Planned Visits. As such,mappings are given to map "Visit 0" to "Baseline" and "Visit 12" to "Week 12". Baseline and Week 12 are valid planned visit names for this study.

[^7]: "cm" in the "Unit" column: This value specifies that the field "HEIGHTCM" has a unit of "cm". This value will be used in the "resultUnitReported" column of the ImmPort template

[^8]: "ALEGGAGE" in the "Age At Onset Reported" column: This value specifies that the field "ALEGGAGE" in the DEM study file contains the "Age At Onset Reported" value for the field "ALEGG". 

[^9]: "years" in the "Age at Onset Unit Reported" column: This value specifies that "years" is the unit corresponding to the value given in the "Age at Onset Reported" column. The unit will only be used when there is a value in the corresponding field.

[^10]: "Study Day" in the "Column Mappings" column: This special text specifies that the field "DATE" in the MD study file specifies the study day value that should be applied to all questions in that study file.

[^11]: "HIVESDT" value in the "Override Study Day" column: This value specifies that the field "HIVESDT" contains the value that should be used for the study day for question "HIVES". 

[^12]: "HIVESLOC" value in the "Location" column: This value specifies that the field "HIVESLOC" contains the value that should be used for the "Location of Finding Reported" for question "HIVES".

[^13]: "Back" value in the "Location" column: This value specifies that all ALLTEST questions have a value of "Back" for the "Location of Finding Reported" column in the ImmPort Template.

[^14]: "Father" value in the "Who is Assessed" column: This value specifies that for all PATALL questions, the value of "Father" is used for the "Who is Assessed" column in the ImmPort Template.










