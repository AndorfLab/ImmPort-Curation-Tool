# ImmPort-Curation-Tool User Guide

The purpose of this user guide is to explain how to use the ImmPort Curation Tool.

## Other documentation
* [Installation Instructions](../README.md#installation-instructions)
* [Purpose of the tool](../README.md#purpose-of-this-tool)

## Before You Start
Before you start using this tool, you will need to:
- [Install the tool](../README.md#installation-instructions)
- Have the study files you want to convert in a single directory
- Curate the data dictionary (TODO: Link Needed)


## General Overview of Steps
1. [Start Tool](#step-1:-start-tool)
2. Specify Study Metadata
3. Select Data Dictionary
4. Select Directory containing Study Files
5. Specify Study File metadata
6. Generate completed ImmPort Template

## Step 1: Start Tool
Open up the jupyter notebook: forms.ipynb

Run the first notebook cell to initiate the tool.

You should not see an output that looks like this.

![Study1](images/001_Study_Tab.png)

## Step 2. Specify Study Metadata
There are 2 methods to specify study metadata, specified by clicking the buttons next to the text "How do you want to start?".
### Method 1: Use ImmPort TAB file
A valid ImmPort TAB file can be downloaded from the [ImmPort Data Browser](https://www.immport.org/browser). Search for the Study ID that you are looking for, click to open the study folder, and download the _Tab.zip file.  

Select your file by browsing under the select button
![Study3](images/002_Select_Tab.png)
![Study4](images/006_study_select_with_hands.png)

> Note: The ImmPort TAB file includes study metadata as well as information for the planned visits and study files. If you need to update these, [follow these instructions](./Load_files_from_immport.md).

### Method 2: Download information from ImmPort
If you cannot get a valid TAB file (perhaps this is the intial upload of the study and its not present), then the process is a little more manual.

First, specify the workspace ID and the study ID.

Next provide a valid ImmPort Planned Visit file and a valid ImmPort Study Files file. Instructions for obtaining these files are provided in the tool, as well as [here](./Load_files_from_immport.md)

[Image of Study tab, Download information from ImmPort option]


Now switch to the Data Dictionary Tab
![Dd1](images/007_Data_Dictionary_with_hand.png)
## Step 3. Select Data Dictionary
First, curate the data dictionary according to [these instructions](https://github.com/JoshuaFortriede/ImmPort-Curation-Tool/blob/develop/documentation/Curated_Data_Dictionary.md) ______ and save it to your directory

Then click select, browse to the correct file and re-click select
![dd2](images/008_Data_dictionary_select.png)

Click through, then specify which column in DD holds the table name code
![dd3](images/009_DD_clicks.png)
![dd4](images/009-1_click.png)
![dd6](images/009-3_clicks.png)

## Step 4. Select Directory containing Study Files
Switch to the Study Files Tab and select the folder that contains the study files.
> Note: This is selecting a folder, not individual files. you should not see any files in this selector.
![study](images/010_StudyFiles_clicks.png)
![study12](images/012_pick_study_folder_clicks.png)
Once you've selected the correct folder, make sure to click the Load Study Files Directory
![study13](images/013_pick_study_folder_make_sure_to_push_button_click.png)
The list of tables was already specified in and interpretted throuh the curated data dictionary file previously loaded. The list of tables from the data dictionary will display automatically, but a list of files to curate with those specified table names will only appear if you've selected the correct directory. Below are examples of incorrect and correct directory selections are below:

Incorrect:
![study101=1](images/011_if_you_load_the_wrong_study_files_folder.png)

Correct: 
![study14](images/014_study_directory_loaded.png)



## Step 5. Specify Study File metadata
The generated table includes every file in the selected "Study Files" directory. For each file that you want to process:
1. Assign the table code the coorelates this study file with the entries in the Data Dictionary
2. Add an assessment name such as Medical History or Demographics. This assessment name should be a high-level, broad description.
3. Select the ImmPort Template to which the tool should munge the files. Currently this tool only supports Assessments so pick that for each file to translate
4. If the data dictionary does not specific a visit field for this study file, specify the default visit. This default visit will be applied to every record in this study file.

### 1 Assign the table code the coorelates this study file with the entries in the Data Dictionary
![study15](images/015_start_picking_table_files.png)

### 2 Add an assessment name such as Medical History or Demographics
This will become the assessment type in the ImmPort Data Model

### 3 Select the ImmPort Template to which the tool should munge the files
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