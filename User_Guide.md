# ImmPort-Curation-Tool User Guide

The purpose of this user guide is to explain how to use the ImmPort Curation Tool.

## Other documentation
* [Installation Instructions](./README.md#installation-instructions)
* [Purpose of the tool](./README.md#purpose-of-this-tool)
* [Common logging errors](./documentation/Logging%20Errors.md)
* [FAQ](./documentation/FAQ.md)

## Before You Start
Before you start using this tool, you will need to:
- [Install the tool](./README.md#installation-instructions)
- Have the study files you want to convert in a single directory
- [Curate the data dictionary](./documentation/Curated_Data_Dictionary.md)
- Replace dates in study files with Study Day

## General Overview of Steps
1. [Start Tool](#step-1-start-tool)
2. [Specify Study Information](#step-2-specify-study-information)
3. [Select Data Dictionary](#step-3-select-data-dictionary)
4. [Select Directory containing Study Files](#step-4-select-directory-containing-study-files)
5. [Specify Study File Information](#step-5-specify-study-file-information)
6. [Generate completed ImmPort Template](#step-6-generate-completed-immport-template)

## Step 1: Start Tool
Open up the jupyter notebook: i.e. notebook.ipynb

Run the first notebook cell to initiate the tool.

You should not see an output that looks like this.

![dd0](documentation/images/005_Select_Study_from_Immport_raw.png)

## Step 2: Specify Study Information
This step specifies the ImmPort Workspace ID, Study ID, planned visit information, and study file information.

There are 2 methods to specify this information, specified by clicking the buttons next to the text "How do you want to start?".

### Method 1: Download information from ImmPort

If you are the submitter of this dataset, working with the submitter, or have access to the workspace within the [ImmPort Upload Data Portal](https://immport.niaid.nih.gov/upload/data/uploadDataMain#!/uploadData), you will want to use this method. If not, go to [Method 2](#method-2-use-immport-tab-file).

For this method, you will need to download a planned visits file and Study Files file from ImmPort. Use this method if you have private access to the ImmPort study.

1. First, specify the workspace ID and the study ID.

2. Next provide a valid ImmPort Planned Visit file and a valid ImmPort Study Files file. Instructions for obtaining these files are provided in the tool, as well as [here](./documentation/Load_files_from_immport.md)


3. After the planned visit file is processed, the visits will be show in the "Study Visits" dropdown. This is an easy way to check that the planned visit file was processed correctly.


### Method 2: Use ImmPort TAB file
You can only use this method when a study is available in a public ImmPort Release. Additionally, if you do not have access to the workspace within the [ImmPort Upload Data Portal](https://immport.niaid.nih.gov/upload/data/uploadDataMain#!/uploadData), you will want to use this method. 

For this method, you will need to download an ImmPort TAB file. The TAB file is a zip file that contains the current information about the ImmPort study such as study ID, workspace ID, planned visits, and study file information.

1. Download a valid ImmPort TAB file from the [ImmPort Data Browser](https://www.immport.org/browser). Search for the Study ID that you are looking for, click to open the study folder, and download the "SDY####-DR##_Tab.zip" file.  

2. Click on the "Select" button under "Select the ImmPort Study TAB zip file, and browse to where you downloaded the ZIP file.

![Study3](documentation/images/002_Select_Tab.png)

![Study4](documentation/images/006_study_select_with_hands.png)

> Note: The ImmPort TAB file includes study metadata as well as information for the planned visits and study files. If you need to update these click the "Yes" toggle next to the text "Amend Tab file with new planned visits and/or study files?", then [follow these instructions](./documentation/Load_files_from_immport.md).




<!-- ![Dd1](images/007_Data_Dictionary_with_hand.png) -->
## Step 3. Select Data Dictionary
Now switch to the Data Dictionary Tab

First, curate the data dictionary according to [these instructions](./documentation/Curated_Data_Dictionary.md) and save it to your directory.

Click select

![dd2](documentation/images/008_Data_dictionary_select.png)

Next, browse to the correct file, select it, and re-click select.

![dd3](documentation/images/009_DD_clicks.png)

Now click the "Load Data Dictionary" button. If it changes to a red button with the text "Load Failed", go to the logging tab and look for an "[Error loading data dictionary](./documentation/Logging%20Errors.md#error-loading-data-dictionary)" message.



![dd4](documentation/images/009-1_click.png)

If the button turns green with the text "Dictionary Loaded", then specify which column in the data dictionary holds the table name code from the dropdown. Then click the button "Confirm Form Columns". This ensure that we can map the data dictionary entries to the correct table/study file.

![dd6](documentation/images/009-3_clicks.png)
> Note: If the dropdown is empty or lists options that are not the column headers of the data dictionary, something with the data dictionary load went wrong. Re-check that you selected the correct file for the data dictionary. Additionally, open the data dictionary file and confirm that it display correctly, and that it is a CSV file.


## Step 4. Select Directory containing Study Files


Switch to the Study Files Tab and select the folder that contains the study files.

![study](documentation/images/010_StudyFiles_clicks.png)

![study12](documentation/images/012_pick_study_folder_clicks.png)
> Note: This is selecting a folder, not individual files. you should not see any files in this selector.

Once you've selected the correct folder, make sure to click the Load Study Files Directory
![study13](documentation/images/013_pick_study_folder_make_sure_to_push_button_click.png)

The "**Tables Listed in Dictionary**" specify the table codes that were present in the Data Dictionary, corresponding to the values in the column specified on the previous tab.

After selecting a directory, a "Study File Curation Table" will be generated that will allow you to curate necessary information for each study file. Note, if the directory contains a lot of files, this table may take up to 30 seconds to display. Below are examples of incorrect and correct directory selections:

**Correct:** 

![study14](documentation/images/014_study_directory_loaded.png)
> Here several files have been loaded into the Study File Curation Table.

**Incorrect:**

![study101=1](documentation/images/011_if_you_load_the_wrong_study_files_folder.png)
> While a directory was selected, that directory did not contain any valid study files to load.

## Step 5. Specify Study File Information
The generated table includes every file in the selected "Study Files" directory. For each file that you want to process:

1. Assign the table code that correlates this study file with the entries in the Data Dictionary
![study15](documentation/images/015_start_picking_table_files.png)

2. Add an assessment name such as Medical History or Demographics. This assessment name should be a high-level, broad description. This will become the assessment type in the ImmPort Data Model

3. Select the ImmPort Template to into which the data needs transformed. Currently this tool only supports Assessments so pick that for each file to translate

![study16](documentation/images/016_call_them_something_then_select_assessment.png)

4. If the data dictionary does not specific a visit field for this study file, specify the default visit. This default visit will be applied to every record in this study file.
> NOTE: This field is not often used.

![study17](documentation/images/017_add_the_visit.png)

## Step 6. Generate completed ImmPort Template
Once your configuration is set.  Press the gray button to launch the exporter: press the Generate Filled Templates Button.

![study18](documentation/images/018_press_the_run_button_click.png)

Depending on the size of the study files, this step could take a few minutes. The button displays the current table code of the study file that is being processed.

![study19](documentation/images/019_press_go.png)

You can also view the progress by clicking on the "Logging" tab. This tab display information about the process, and more importantly, any errors that occurring. Errors are specified in red and should provide specifics about the error. Common errors are explain on our [errors page](./documentation/Logging%20Errors.md).

![study20](documentation/images/020_check_the_logs_for_critical_errors.png)


## Step 7: Upload files to ImmPort
Separate Assessments templates are generated for each study file.The generated files will be in the results/SDY#### directory, with a naming format of SDY####/[Table Code]. 

Both the ImmPort wide-format txt file, as well as a JSON file is generated. Additionally, the original study file and wide-format text file is included in a ZIP file. This ZIP file is one method of uploading the data to ImmPort, and ensures that the correct study file is uploaded with the correct completed ImmPort Template file.

It is recommended to use the [ImmPort validator](https://data-manager.dev.immport.org/validate/data/validateDataMain) on at least one study file and template to check for any validation errors in the uploads, prior to using the actual uploader.

