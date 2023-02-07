
# Example Data Dictionary
This example curated data dictionary specifies how specific fields/values work. Read the corresponding footnote for the items for an explanation.

A copy of this curated data dictionary can be [downloaded here](./curated_data_dictionary.csv).


|<sub>Table Name</sub>|<sub>Field Name</sub>|<sub>Field Description</sub>|<sub>Code List Values</sub>|<sub>Unit</sub>|<sub>Map To Planned Visit</sub>|<sub>Column Mappings</sub>|<sub>Verbatim Question</sub>|<sub>Who is Assessed</sub>|<sub>Override Study Day</sub>|<sub>Age At Onset Reported</sub>|<sub>Age At Onset Unit Reported</sub>|<sub>Location</sub>|
|----|----|----|----|----|----|----|----|----|----|----|----|----|
|<sub>DEM</sub>|<sub>HNO</sub>|<sub>Number in household</sub>|<sub></sub>|<sub></sub>|<sub></sub>|<sub></sub>|<sub>Number living in the household?[^1]</sub>|<sub></sub>|<sub></sub>|<sub></sub>|<sub></sub>|<sub></sub>|
|<sub>DEM</sub>|<sub>HINC01</sub>|<sub>Household income</sub>|<sub>0=$0 - $49,999, 1=$50,000 - $99,999, 2=$100,000+, 3=Declined</sub>|<sub></sub>|<sub></sub>|<sub></sub>|<sub>[Same][^2]</sub>|<sub></sub>|<sub></sub>|<sub></sub>|<sub></sub>|<sub></sub>|
|<sub>DEM</sub>|<sub>VISIT</sub>|<sub>Visit</sub>|<sub>0=Baseline, 1=Week 6</sub>|<sub></sub>|<sub></sub>|<sub>Visit[^3]</sub>|<sub></sub>|<sub></sub>|<sub></sub>|<sub></sub>|<sub></sub>|<sub></sub>|
|<sub>DEM</sub>|<sub>PATID</sub>|<sub>Participant ID</sub>|<sub></sub>|<sub></sub>|<sub></sub>|<sub>User Defined ID[^4]</sub>|<sub></sub>|<sub></sub>|<sub></sub>|<sub></sub>|<sub></sub>|<sub></sub>|
|<sub>DEM</sub>|<sub>SITE</sub>|<sub>Center</sub>|<sub>BS=Boston, SD=San Diego, SE=Seattle</sub>|<sub></sub>|<sub></sub>|<sub>[NA][^5]</sub>|<sub></sub>|<sub></sub>|<sub></sub>|<sub></sub>|<sub></sub>|<sub></sub>|
|<sub>DEM</sub>|<sub>PHASE</sub>|<sub>Trial Phase</sub>|<sub></sub>|<sub></sub>|<sub></sub>|<sub>[NA]</sub>|<sub></sub>|<sub></sub>|<sub></sub>|<sub></sub>|<sub></sub>|<sub></sub>|
|<sub>MD</sub>|<sub>PATID</sub>|<sub>Participant ID</sub>|<sub></sub>|<sub></sub>|<sub></sub>|<sub>User Defined ID</sub>|<sub></sub>|<sub></sub>|<sub></sub>|<sub></sub>|<sub></sub>|<sub></sub>|
|<sub>MD</sub>|<sub>VISIT</sub>|<sub>Visit</sub>|<sub>0=Visit 0, 2=Visit 12</sub>|<sub></sub>|<sub>{"Visit 0" : "Baseline", "Visit 12" : "Week 12"}[^6]</sub>|<sub>Visit</sub>|<sub></sub>|<sub></sub>|<sub></sub>|<sub></sub>|<sub></sub>|<sub></sub>|
|<sub>MD</sub>|<sub>HEIGHTCM</sub>|<sub>Height (cm)</sub>|<sub></sub>|<sub>cm[^7]</sub>|<sub></sub>|<sub></sub>|<sub>[Same]</sub>|<sub></sub>|<sub></sub>|<sub></sub>|<sub></sub>|<sub></sub>|
|<sub>MD</sub>|<sub>PREG</sub>|<sub>Pregnant</sub>|<sub>0=No, 1=Yes, 99=NA</sub>|<sub></sub>|<sub></sub>|<sub></sub>|<sub>Is the patient pregnant?</sub>|<sub></sub>|<sub></sub>|<sub></sub>|<sub></sub>|<sub></sub>|
|<sub>MD</sub>|<sub>ALEGG</sub>|<sub>Egg Allergy</sub>|<sub>0=No, 1=Yes, 9=Unknown</sub>|<sub></sub>|<sub></sub>|<sub></sub>|<sub>Is the patient allergic to: Egg</sub>|<sub></sub>|<sub></sub>|<sub>ALEGGAGE[^8]</sub>|<sub>years[^9]</sub>|<sub></sub>|
|<sub>MD</sub>|<sub>DATE</sub>|<sub>Date</sub>|<sub></sub>|<sub></sub>|<sub></sub>|<sub>Study Day[^10]</sub>|<sub></sub>|<sub></sub>|<sub></sub>|<sub></sub>|<sub></sub>|<sub></sub>|
|<sub>MD</sub>|<sub>HIVES</sub>|<sub>Hives</sub>|<sub>0=0, 1=1, 2=2, 3=3, 4=4, 5=5, 6=6</sub>|<sub>USA Score</sub>|<sub></sub>|<sub></sub>|<sub>What was the score of your last hive episode?</sub>|<sub></sub>|<sub>HIVESDT[^11]</sub>|<sub></sub>|<sub></sub>|<sub>HIVESLOC[^12]</sub>|
|<sub>MD</sub>|<sub>HIVESLOC</sub>|<sub>Hives Location</sub>|<sub></sub>|<sub></sub>|<sub></sub>|<sub></sub>|<sub></sub>|<sub></sub>|<sub></sub>|<sub></sub>|<sub></sub>|<sub></sub>|
|<sub>MD</sub>|<sub>HIVESDT</sub>|<sub>Hives Date</sub>|<sub></sub>|<sub></sub>|<sub></sub>|<sub></sub>|<sub></sub>|<sub></sub>|<sub></sub>|<sub></sub>|<sub></sub>|<sub></sub>|
|<sub>MD</sub>|<sub>ALLTEST</sub>|<sub>Allergy Test</sub>|<sub></sub>|<sub></sub>|<sub></sub>|<sub></sub>|<sub>When was your last allergy test?</sub>|<sub></sub>|<sub>ALLTESTDT</sub>|<sub></sub>|<sub></sub>|<sub>Back[^13]</sub>|
|<sub>MD</sub>|<sub>ALLTESTDT </sub>|<sub>Allergy Test Date</sub>|<sub></sub>|<sub></sub>|<sub></sub>|<sub></sub>|<sub></sub>|<sub></sub>|<sub></sub>|<sub></sub>|<sub></sub>|<sub></sub>|
|<sub>MD</sub>|<sub>ALEGGAGE</sub>|<sub>Egg Allergy Onset</sub>|<sub></sub>|<sub></sub>|<sub></sub>|<sub></sub>|<sub></sub>|<sub></sub>|<sub></sub>|<sub></sub>|<sub></sub>|<sub></sub>|
|<sub>MD</sub>|<sub>PATALL</sub>|<sub>Paternal Allergy</sub>|<sub>0=No, 1=Yes, 9=Unknown</sub>|<sub></sub>|<sub></sub>|<sub></sub>|<sub>Does the father have allergies</sub>|<sub>Father[^14]</sub>|<sub></sub>|<sub></sub>|<sub></sub>|<sub></sub>|


Footnotes
[^1]: Value of "Number living in the household?" in column "Verbatim Question": This value specifies the exact, verbatim question that was asked to the participant. 

[^2]: Value of "[Same]" in column "Verbatim Question". This value specifies that the verbatim question text is the same as the value in the "Field Description". Instead of typing or copying the value, a value of "[Same]" can be specified.

[^3]: Value of "Visit" in column "Column Mappings": This value specifies that the "VISIT" field in the DEM study file contains the planned visit information for all records in the DEM study file.

[^4]: Value of "User Defined ID" in column "Column Mappings": This value specifies that the "PATID" field in the DEM study file contains the Subject ID/User Defined ID for each record in the DEM study file.

[^5]: Value of "[NA]" in column "Column Mappings": This special value specifies that this field should be ignored when converting the study file to an ImmPort template. Commonly this could be a PHI field, or operational field that provides no data benefit.

[^6]: JSON dictionary in column "Map To Planned Visit": Only use if the Column Mapping is "Visit"! Used if 1 or multiple values in the "Code List Values" do not match the Planned Visits name. In this case, the values "Visit 0" and "Visit 12", as specified in the "Code List Values" column, are not valid Planned Visits. As such,mappings are given to map "Visit 0" to "Baseline" and "Visit 12" to "Week 12". Baseline and Week 12 are valid planned visit names for this study.

[^7]: Value of "cm" in column "Unit": This value specifies that the field "HEIGHTCM" has a unit of "cm". This value will be used in the "resultUnitReported" column of the ImmPort template

[^8]: Value of "ALEGGAGE" in column "Age At Onset Reported": This value specifies that the field "ALEGGAGE" in the DEM study file contains the "Age At Onset Reported" value for the field "ALEGG". 

[^9]: Value of "years" in column "Age at Onset Unit Reported": This value specifies that "years" is the unit corresponding to the value given in the "Age at Onset Reported" column. The unit will only be used when there is a value in the corresponding field.

[^10]: Value of "Study Day" in column "Column Mappings": This special text specifies that the field "DATE" in the MD study file specifies the study day value that should be applied to all questions in that study file.

[^11]: Value of "HIVESDT" value in column "Override Study Day": This value specifies that the field "HIVESDT" contains the value that should be used for the study day for question "HIVES". 

[^12]: Value of "HIVESLOC" value in column "Location": This value specifies that the field "HIVESLOC" contains the value that should be used for the "Location of Finding Reported" for question "HIVES".

[^13]: Value of "Back" value in column "Location": This value specifies that all ALLTEST questions have a value of "Back" for the "Location of Finding Reported" column in the ImmPort Template.

[^14]: Value of "Father" value in column "Who is Assessed": This value specifies that for all PATALL questions, the value of "Father" is used for the "Who is Assessed" column in the ImmPort Template.










