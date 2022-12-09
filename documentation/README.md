# ImmPort-Curation-Tool User Guide

The purpose of this user guide is to explain how to use the ImmPort Curation Tool.

## Other documentation
* [Installation Instructions](../README.md#installation-instructions)
* [Purpose of the tool](../README.md#purpose-of-this-tool)
## General Overview of Steps
0. Run the notebook cell to initiate the tool
1. Specify the ImmPort study you are working on
2. Specify the [curated Data Dictionary](./Curated_Data_Dictionary.md) for this study.
3. Specify the directory containing the study files.
4. Curate the generated table with necessary data
5. Generate filled template files
6. You're now done with the tool, use the outputs on the ImmPort site
7. Login to Immport and try to validate them
8. If validation comes back OK, goto the upload

## List of Necessary files and the steps that require them
1. zipped study tab file (Step 1)
    (only relevant if this is curation upon a previously submitted dataset)
2. study visits file (Step 1)
3. ImmPort Study Files (Step 1)

Run the notebook cell to initiate the tool

## 1. Study
Here is an image of the study tab as it first appears. 

![Study1](images/001_Study_Tab.png)

The application needs a source of study data which can be one of two things:

### 1. a zipped TAB file already present in your directories (default)...
    here's documentation about how to get the tab file _____

### 2. if the data is not already submitted and published fully, a tab file is not availaable, and you will certainly the accessed by specifying it's location in ImmPort
    if b) you'll need your workspace name: This can be found by  ______ 

Select your file by browsing under the select button
![Study3](images/002_Select_Tab.png)
![Study4](images/006_study_select_with_hands.png)

First, download the study visits file with the instructions here: [More Instructions](https://github.com/JoshuaFortriede/ImmPort-Curation-Tool/blob/develop/documentation/Load_files_from_immport.md)

Modify the visits table then select it from the appropriate location
(this may require communication with the ImmPort DB admins to create the visit entity)

Download ImmPort Study Files file using the same instructions [More Instructions](https://github.com/JoshuaFortriede/ImmPort-Curation-Tool/blob/develop/documentation/Load_files_from_immport.md) and select the correct file

____ josh the above two files weren't in it when I worked with this before

Now switch to the Data Dictionary Tab
![Dd1](images/007_Data_Dictionary_with_hand.png)
## 2 Data Dictionary
First, curate the data dictionary according to [these instructions](https://github.com/JoshuaFortriede/ImmPort-Curation-Tool/blob/develop/documentation/Curated_Data_Dictionary.md) ______ and save it to your directory

Then click select, browse to the correct file and re-click select
![dd2](images/008_Data_dictionary_select.png)

Click through, then specify which column in DD holds the table name code
![dd3](images/009_DD_clicks.png)
![dd4](images/009-1_click.png)
![dd6](images/009-3_clicks.png)

## 3 Specify Directory
Switch to the Study Files Tab and select the folder that contains the study files.
![study](images/010_StudyFiles_clicks.png)
![study12](images/012_pick_study_folder_clicks.png)
Once you've selected the correct folder, make sure to click the Load Study Files Directory
![study13](images/013_pick_study_folder_make_sure_to_push_button_click.png)
The list of tables was already specified in and interpretted throuh the curated data dictionary file previously loaded. The list of tables from the data dictionary will display automatically, but a list of files to curate with those specified table names will only appear if you've selected the correct directory. Below are examples of incorrect and correct directory selections are below:

Incorrect:
![study101=1](images/011_if_you_load_the_wrong_study_files_folder.png)

Correct: 
![study14](images/014_study_directory_loaded.png)
## 4 Fill out the table. 
Use the resulting table to perform these annotations
1. Assign table codes from the Data Dictionary to the files containing the data for each
2. Add an assessment name such as Medical History or Demographics relevant for each table
3. Select the ImmPort Template to which the tool should munge the files. Currently this tool only supports Assessments so pick that for each file to translate
4. Select the default visit for each table

### 1 Assign table codes from the Data Dictionary to the files containing the data for each
![study15](images/015_start_picking_table_files.png)

### 2 Add an assessment name such as Medical History or Demographics relevant for each table
This will become the assessment type in the ImmPort Data Model

### 3 Select the ImmPort Template to which the tool should munge the files. Currently this tool only supports Assessments so pick that for each file to translate
![study16](images/016_call_them_something_then_select_assessment.png)

### 4 Select the default visit for each table

![study17](images/017_add_the_visit.png)
## 5 Run to create files
Once your configuration is set.  Press the gray button to launch the exporter: press the Generate Filled Templates Button
![study18](images/018_press_the_run_button_click.png)
For a moment you'll see
![study19](images/019_press_go.png)
Once Complete, check the errors log for critical errors. _____red is bad, check your work
![study20](images/020_check_the_logs_for_critical_errors.png)
good, move on
![study21](images/021_check_the_logs_ok.png)

## 6 You're now done with the tool, use the outputs on the ImmPort site
Login to Immport and try to validate them

If validation comes back OK, goto the upload




Further Edits and questions
____ kevin needs to smudge out his children's ID


I don't think it will benefit the user, but the documenter really wants "clear" functionality akin to a "back" button. once you click something it's really hard to screen cap


are the assessment type text, visit type etc. required?
s
Check for any critical errors in the logging tab

Check that these files have been created _______



I still think the default visit column header doesn't make a lot of sense