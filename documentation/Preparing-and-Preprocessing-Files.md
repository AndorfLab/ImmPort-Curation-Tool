# Preparing and Preprocessing Files
The curation application requires 3 different types of files:
1)	ImmPort files 
2)	Curated data dictionary
3)	Study files 

## Generating ImmPort Files
Before generating the *Lab Tests* and *Assessments* templates, you must first gather or create the required ImmPort templates.

The ImmPort files should either be in TXT or CSV format. They can be uploaded separately or in a single ZIP file.

If using a study already published in ImmPort:
- The file that ends with *_Tab.zip* should be downloaded from the public study page.
- That ZIP should already contain the 3 required templates, study_file.txt, planned_visit.txt, and protocol.txt.

If you are the administrator of a study in ImmPort:
- [These instructions](https://github.com/AndorfLab/ImmPort-Curation-Tool/blob/Main/documentation/Load_files_from_immport.md) will walk you through downloading the required files.
- The names of the downloaded files will contain the study ID, followed by _Study_Files.csv, _Planned_Visits.csv, and _Protocols.csv. For example, if the study ID is SDY89765, the protocol file will be called SDY89765_Protocols.csv. 
  
If the study has not yet been deposited in ImmPort:
- Create an ImmPort account and register a new study. The Study Registration Wizard will walk you through filling basic study information, which will encompass details about the protocol(s), study data, and planned visits.
- Alternatively, the basic_study_design.txt and protocols.txt can be completed and uploaded into ImmPort. 

Once the 3 required files are downloaded, they can be uploaded individually into the curation application or together as a ZIP file.

If any of these files contain incomplete or incorrect information, update them directly in ImmPort before generating the filled *Lab Tests* and *Assessments* templates.

### Example ImmPort Files
Below are examples of the ImmPort files that are required by the curation tool. The templates are populated with mock data to showcase the required formatting.

Note: File names and formats differ slightly between public downloads and administrator exports, but both contain the necessary information for the Curation Tool. The primary difference is administrator exports typically do not contain a STUDY_ACCESSION column. As a result, the study accession must be filled in manually in the 'Input the study ID' textbox in the application. 

The examples below show the public download format.

#### *study_file.txt*
| **STUDY_FILE_ACCESSION** | **DESCRIPTION**     | **FILE_NAME**        | **STUDY_ACCESSION** | **STUDY_FILE_TYPE** | **WORKSPACE_ID** |
|--------------------------|---------------------|----------------------|---------------------|---------------------|------------------|
| SFL19620624              | ABC Test            | ABC-Test.txt         | SDY818199           | Lab Test            | 18888            |
| SFL19620625              | XYZ Test            | XYZ-Test.txt         | SDY818199           | Lab Test            | 18888            |
| SFL19620626              | Medical History     | Med-History.txt      | SDY818199           | Assessment          | 18888            |
| SFL19620627              | Family History      | Fam-History.txt      | SDY818199           | Assessment          | 18888            |
| SFL19620628              | Physical Exam       | Physical-Exam.txt    | SDY818199           | Assessment          | 18888            |

#### *protocol.txt*
| **PROTOCOL_ACCESSION** | **DESCRIPTION**        | **FILE_NAME**                    | **NAME**           | **ORIGINAL_FILE_NAME**     | **TYPE** | **WORKSPACE_ID** |
|------------------------|------------------------|----------------------------------|--------------------|-----------------------------|----------|------------------|
| PTL19950818            | ABC Test Protocol      | ABC-protocol.PTL19950818.pdf     | ABC Protocol       | ABC-protocol.pdf           | Assay    | 18888            |
| PTL19950819            | Study Protocol         | Study-protocol.PTL19950819.pdf   | Study Protocol     | Study-protocol.pdf         | Study    | 18888            |

#### *planned_visit.txt*
| **PLANNED_VISIT_ACCESSION** | **END_RULE** | **MAX_START_DAY** | **MIN_START_DAY** | **NAME**  | **ORDER_NUMBER** | **PERIOD_ACCESSION** | **START_RULE** | **STUDY_ACCESSION** | **WORKSPACE_ID** |
|-----------------------------|--------------|--------------------|--------------------|----------|------------------|----------------------|----------------|---------------------|------------------|
| PV8199556                   | NA           | 0                  | 0                  | Enroll   | 1                | P05281998            | NA             | SDY818199           | 18888            |
| PV8199557                   | NA           | 6                  | 1                  | Visit 1  | 2                | P05281998            | NA             | SDY818199           | 18888            |
| PV8199558                   | NA           | 21                 | 15                 | Visit 2  | 3                | P05281998            | NA             | SDY818199           | 18888            |

## Curating the Data Dictionary
The tool also requires a data dictionary that has been curated to conform to certain standards. This data dictionary links variables in the study files to fields in the *Assessments* and *Lab Tests* templates. While many clinical trials already include a data dictionary, some additional curation is required for use with this tool.

The data dictionary should either be a TXT or CSV file. The data dictionary template can be downloaded [here](../Templates/data-dictionary-template.csv). 

### Required Columns
The first six columns are required and must all be present in the curated data dictionary. The first three columns ("Table Name", "Field Name", and "Field Description") should always be filled in. However, the last three ("Code List Values", "Mappings", and "Unit") only need to be filled in when relevant. For example, if a field has no coded values or a unit, those cells can be left blank.

| **Column Name**       | **Purpose**                                                            | **Format**                                                                                                                                      | **Examples**                                                                 |
|-----------------------|------------------------------------------------------------------------|--------------------------------------------------------------------------------------------------------------------------------------------------|-------------------------------------------------------------------------------|
| Table Name            | Identifies the source study file.                                      | A string that represents the study file.                                                                                                          | VIT,<br> MED,<br> CBC                                                                 |
| Field Name            | Specifies the column within that file.                                 | A string that is in the study file.                                                                                                               | BLOPR,<br> HEIG,<br> WEIG                                                             |
| Field Description     | Provides a human-readable description of the variable.                 | Any string that describes the "Field Name".                                                                                                         | Blood pressure,<br> Height,<br> Weight                                               |
| Code List Values      | Defines mappings for coded responses. (e.g., 1 = Yes, 2 = No).         | Format is a=A, b=B, c=C, ... where lowercase letters (values on left) represent the coded values present in the data files and uppercase letters (values on right) are the human-readable values they should be translated into. | 1=Normal, 2=High, 3=Low, 4=Unknown                                           |
| Mappings               | Specifies the variable’s role in the study.                            | 1 of 6 options: `User Defined ID`, `Study Day`, `Study Time`, `Visit`, `Category`, or `NA`.1️⃣                                                      | User Defined ID,<br> Visit,<br> NA.                                                   |
| Unit                  | Defines the unit for the variable.                                     | A string, another "Field Name" that contains the unit, or [SPLIT]2️⃣ if the recorded value contains the unit.                         | Percentage,<br> HEIGHTUNIT,<br> [SPLIT]                                              |

#### Guidelines for Completing the Mappings Column
1️⃣: The "Mappings" column can be filled in with 1 of 6 options or left empty entirely. `User Defined ID` should be used to indicate the "Field Name" that contains the participant ID. `Visit` should be used to indicate the "Field Name" that contains the specific visit information. `Study Day` should be used to indicate the day, while `Study Time` should be used to indicate the time. All of these designations should only be used a maximum of 1 time per "Table Name". If there are multiple study days or times represented within a table, "Override Study Day" and "Override Study Time" should be used (see the "Optional Columns" section below).

The other options, `NA` and `Category`, can be used more than once per "Table Name". `NA` should be used to indicate that the "Field Name" should be ignored entirely from the completed *Lab Tests* or *Assessments* template. For example, if a "Field Name" is only used for internal record keeping and is meaningless to external researchers, then that "Field Name" should be designated as `NA`.

`Category` should be used when that "Field Name" does not contain a result per se, but rather a category that adds specificity to the results. That value will then be added to all of the "Field Descriptions" for that "Table Code" instead of being listed as a result in the final template. For example, consider a "Field Name" that is SKPT with a "Field Description" of skin prick test result and with values in the study file containing those result measurements (e.g., 1, 3, 0, 4). Consider another "Field Name" for that table is ALLER with a "Field Description" of allergens, containing different types of allergens in the study file (e.g., peanut, pollen, milk). The ALLER field might be better designated as `Category`. That would then make the "Field Description" of SKPT peanut skin prick test result, pollen skin prick test result, milk skin prick test, etc. 

`User Defined ID`, `Study Day`, `Visit`, `Category`, and `NA` are all used to propagate both the *Lab Tests* and *Assessments* templates. `Study Time` is only used within the *Assessments* template.

#### Designating SPLIT in the Unit Column 
2️⃣: [SPLIT] or SPLIT can be designated in the "Unit" column if the recorded value contains the unit. Designating SPLIT will split at the first space, placing everything before the space as the value and everything after as the unit. For example, ‘6 feet’ will designate the unit as ‘feet’, while ‘6feet’ will result in no unit designation.  

### Optional Columns
The next eight columns are optional, but filling them in when relevant improves the quality and reusability of the generated data. 

"Map To Visit", "Override Study Day", and "Override Study Time" allow you to override information specified in the mandatory columns for more granular control. "Override Study Time" is only applicable for the *Assessments* template.

The remaining five columns – "Verbatim Question", "Who is Assessed", "Age at Onset Reported", "Age at Onset Unit Reported", and "Location" – are also only used to generate the *Assessments* template. These do not need to be included for study files that will be used exclusively for generating the *Lab Tests* template.

| **Column Name**                 | **Purpose**                                                                                                                                                                                                                                                                                                  | **Format**                                                                                                                                                                                                                                                                      | **Examples**                                                                                                             |
|--------------------------------|--------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------|----------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------|--------------------------------------------------------------------------------------------------------------------------|
| Map To Visit                   | Provides visit information present in the study file but missing from planned_visit.txt. Use this if the visit name from the study file does not match the visit name from the planned visit file.                                                                                                                                        | JSON dictionary where the key (value before the colon) is the decoded visit name and the value (value after the colon) is the name of the visit from the planned visits file.3️⃣                                                                                                 | {"Visit 0":"Baseline", "Visit 12": "Week 12"}                                                                           |
| Override Study Day             | Allows a specific day to be assigned when different columns in the same study file refer to different dates.                                                                                                                                                                                       | An integer or another "Field Name" that contains the study day.4️⃣                                                                                                                                                                                                                      | 15,<br>0,<br>LABDAY                                                                                  |
| Override Study Time            | Allows a specific time to be assigned when different columns in the same study file refer to different times.                                                                                                                                                                                  | A time or another "Field Name" that contains the study time.5️⃣                                                                                                                                                                                                                    | Morning,<br>12:30 PM,<br>LABTIME                                                                                        |
| Verbatim Question              | The exact question from the case report form.                                                                                                                                                                                                                                                                 | Any string.                                                                                                                                                                                                                                                                       | What was the height?,<br>What was the result of the pregnancy test?,<br>Was there a major deviation?                   |
| Who is Assessed                | Identifies the subject assessed.                                                                                                                                                                                                                                                                              | A string or another "Field Name" that contains the person.                                                                                                                                                                                                             | Subject,<br>Mother,<br>FAMMEM                                                                                           |
| Age at Onset Reported          | Numeric age of onset.                                                                                                                                                                                                                                                                                         | A number or another "Field Name" that contains the age.                                                                                                                                                                                                                | 15,<br>4,<br>AGEONSET                                                                                                   |
| Age at Onset Unit Reported     | Unit for age of onset.                                                                                                                                                                                                                                                                                        | A string or another "Field Name" that contains the unit.                                                                                                                                                                                                               | Years,<br>Months,<br>AGEUNIT                                                                                           |
| Location                       | The body location that is relevant to the field.                                                                                                                                                                                                                                                              | A string that represents an anatomical site, organ, or body system, or another "Field Name" that contains the location.                                                                                                                                                            | Back,<br>Skin,<br>Respiratory system                                                                                   |

3️⃣: If the visit value from the study file does not exactly match a visit name in the planned visits file, you can provide a mapping using a JSON dictionary format. The format is: `{"[Study_file_visit_value]": "[Planned_visit_file_value]"}`.

4️⃣: This takes precedence over assigning the study day as the "Field Name" that was designated as `Study Day` in the "Mappings" column. For example, if there was a medical history form with two related questions: *What was the severity of your last latex reaction?* and *What was the date of the latex reaction?* — the second could be specified in the "Override Study Day" column in the same row as the first question's field.

5️⃣: This works in the same manner as "Override Study Day", only with study time. Specifically, it takes precedence over assigning the study time as the "Field Name" that was designated as `Study Time` in the "Mappings" column.

### Example Data Dictionary
Below is an example of a curated data dictionary populated with mock data to illustrate the required formatting.
- Grey shaded columns are required
- Green, blue, and tan cells indicate values that are mapped from entries listed in the "Field Name" column. For example, for the fields “SEVR”, “SKIN”, “ORAL”, and “GIRE”, “Age At Onset Reported” will be filled with values from the “AGE” field.

<img width="698" height="532" alt="image" src="https://github.com/user-attachments/assets/94260c2a-44d1-447e-98ab-b6f4d5165f9c" />

## Gathering Study Files
Finally, the tool requires study files that are specific to each clinical trial. These files should contain participant-level information that was collected during the study. Each file should correspond to a specific domain (e.g., demographics) and typically represent a specific case report form (CRF). All study files should contain columns representing variables (e.g., subject ID, visit date, measurement values) that are also represented in the curated data dictionary. Each row should contain the data collected from a single individual for a specific date/visit. 

Each study file should either be in TXT or CSV format. All study files should be in a single folder, which will be chosen within the application interface. 

### Study File Columns

#### Subject Identifier Column
The column used to identify the subject. This column should be specified in the data dictionary column "Mappings" as `User Defined ID`. 

A subject identifier column is required. 

#### Visit Column
The column used to identify the visit. This column should be specified in the data dictionary column "Mappings" as `Visit`. 

If the study file contains information from multiple visits, a visit column is required. If the study file contains information from only a single visit, then a visit column can be used or a default visit for the entire study file can be specified within the curation tool.

#### Study Day Column
The column used to identify the day of the event. This should be an  integer that is in reference to some day 0 event (e.g., 'day of first visit' or 'day of recruitment'). This column should be specified in the data dictionary column "Mappings" as `Study Day`. 

This column is highly recommended, but not required. If a study day column is not included, then the study day in the completed *Lab Tests* or *Assessments* template will be filled in as the minimum start day that corresponds to the specified visit. Specifically, the value from the *MIN_START_DAY* in the planned_visit.txt file is used. 

#### Study Time Column
The column used to identify the time of the event. This column should be specified in the data dictionary column "Mappings" as `Study Time`. Study time will only be used to propagate the *Assessments* template, not the *Lab Tests* template.

This column is recommended when pertinent, but not required. 

#### Other Data Columns
The other columns in the file are typically data columns that correspond to the questions asked on the CRF. These columns should all be specified in the data dictionary, with additional information (e.g., location, verbatim question) filled in when relevant.

### Example Study Files
Below is an example of a study file that aligns with the [example data dictionary](Preparing-and-Preprocessing-Files.md#Example-Data-Dictionary) above:  

| SUBJ | LOCA     | DATE  | TIME  | VISIT | SEVR | SKIN | ORAL | GIRE | FAM | AGE | PSTR | PSTD | PSTT |
|------|----------|-------|-------|-------|------|------|------|------|-----|-----|------|------|------|
| S1   | Clinic A | 5   | 10:00 | V1    | 1    | 1    | 1    | 1    | 2   | 2   | 3    | 1/5  | 12:00 |
| S2   | Clinic A | 13  | 11:20 | V1    | 2    | 1    | 1    | 1    | 1   | 5   | 2    | 1/13 | 12:30 |
| S3   | Clinic A | 21  | 11:30 | V1    | 2    | 2    | 2    | 1    | 1   | 3   | 3    | 1/21 | 1:15  |
| S4   | Clinic B | 3   | 9:00  | V1    | 2    | 1    | 2    | 2    | 2   | 4   | 0    | 2/3  | 1:30  |
| S5   | Clinic B | 5   | 10:30 | V1    | 3    | 2    | 1    | 2    | 1   | 6   | 0    | 1/5  | 2:00  |
| S6   | Clinic B | 4   | 10:45 | V1    | 1    | 2    | 1    | 1    | 1   | 4   | 1    | 2/4  | 2:00  |
| SY   | Clinic A | 5   | 1:30  | V1    | 3    | 1    | 2    | 1    | 2   | 7   | 2    | 1/5  | 3:30  |
| S8   | Clinic A | 14  | 15:00 | V1    | 2    | 1    | 1    | 1    | 1   | 9   | 2    | 1/14 | 10:45 |
| S9   | Clinic A | 28  | 10:30 | V1    | 1    | 1    | 1    | 1    | 1   | 2   | 5    | 1/28 | 3:45  |
| S10  | Clinic B | 8   | 11:45 | V1    | 1    | 1    | 2    | 2    | 1   | 5   | 3    | 1/8  | 4:30  |


An additional example of a study file (which is not represented in the example data dictionary) is below:

| PATID     | VISIT | GENDER | HEIGHTCM | WEIGHTKG | PREG | ALEGG | ALMILK | ALLATEX | DATE |
| --------- | ----- | ------ | -------- | -------- | ---- | ----- | ------ | ------- | ---- |
| SUB000001 | 1     | 0      | 165      | 77       | 99   | 1     | 1      | 1       | 7    |
| SUB000002 | 1     | 1      | 161      | 65       | 0    | 0     | 1      | 0       | 7    |
| SUB000003 | 1     | 1      | 156      | 62       | 0    | 0     | 0      | 1       | 8    |
| SUB000004 | 1     | 0      | 172      | 83       | 99   | 1     | 0      | 1       | 7    |
| SUB000001 | 2     | 0      | 165      | 75       | 99   | 1     | 1      | 0       | 9    |
| SUB000002 | 2     | 1      | 161      | 66       | 0    | 0     | 1      | 1       | 7    |

<hr>
Once these files are prepared, they are ready for upload into the Curation Tool. Additional details on this process can be found on the <a href="Using-the-Application.md">Using the Application</a> page.

