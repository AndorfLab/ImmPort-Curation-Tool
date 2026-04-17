# Example Data
To help users explore the tool’s functionality and understand the required data formats, we provide a sample dataset based on the ImmPort study SDY1550 (CoFAR 7: baked egg or egg oral immunotherapy trial). This dataset has been anonymized and simplified for demonstration purposes.

## 📁 Included Files
### ImmPort ZIP Files
The ZIP archive (Example-ImmPort-Tab.zip) contains 3 completed ImmPort files, representing the minimal required files to use the application. 
- study_file.txt
- planned_visit.txt
- protocol.txt
  
### Curated Data Dictionary 
A structured data dictionary (Data-Dictionary-Example.txt) is included, with all mandatory and optional columns populated when relevant.

### Study-Specific Data Files
These files (in the StudyFiles folder) represent real-world clinical data and are aligned with both the ZIP file and the curated data dictionary. 
- For the *Lab Tests* Template:
  - Basophil-Example.txt
  - IgE-Example.txt
- For the *Assessments* Template:
  - Med-History-1-Example.txt
  - Med-History-2-Example.txt
  - OFC-Example.txt
  - SPT-Example.txt

## Usage
To test the tool, download the [Example-Data](https://github.com/AndorfLab/ImmPort-Curation-Tool/tree/Main/Example-Data) folder from GitHub. Alternatively, [Example-Data.zip](https://github.com/AndorfLab/ImmPort-Curation-Tool/blob/Main/Example-Data.zip) can be downloaded, but the files must be extracted before uploading them into the application.

After the curation tool is [installed](Installation.md) and opened, you will see 5 tabs. The three middle tabs — *1. ImmPort Files*, *2. Data Dictionary* , and *3. Study Files* — are where the example files are uploaded. 

### *1. ImmPort Files*
- Set the initial input type as 'Upload ImmPort Tab ZIP file'.

- Press 'Select' and locate the Example-ImmPort-Tab.zip file. Press 'Select' again.

- Alternatively, upload study_file.txt, planned_visit.txt, protocol.txt individually with the input type set as 'Upload individual ImmPort files'.

### *2. Data Dictionary* 
- Press 'Select' and locate the Data-Dictionary-Example.txt file. Press 'Select' again.

- For 'Choose which template(s) to generate from your data', select 'Assessment and Lab Test' and click 'Load Data Dictionary'. 

###  *3. Study Files*
- Press 'Select' and locate the StudyFiles folder. Press 'Select' again. Click 'Load study files directory'.
  - Note: The upload box will only display folders, so you will not see the individual study files in the box. Make sure to select the StudyFiles folder itself.
  
- Once the files have been loaded, you should see a table. Choose the corresponding 'Table Code' for each file.
  - BAS = Basophil-Example.txt
  - IGE = IgE-Example.txt
  - MH1 = Med-History-1-Example.txt
  - MH2 = Med-History-2-Example.txt
  - OFC = OFC-Example.txt
  - SPT = SPT-Example.txt
    
- For the 'Template' dropdown, select *Lab Test* for Basophil-Example.txt and IgE-Example.txt. Select *Assessment* for the remaining files.

- The 'Default Visit' only needs to be used for the oral food challenge (OFC) data. This table does not include a visit, so a default visit should be chosen here. In this case, the data actually represents multiple visits, so 'Unknown visit' should be chosen.
  
- For *Assessment*, type a name into the 'Assessment Name' textbox.
  
- For *Lab Test*, chose an option from the 'Protocol', 'Name Reported', 'Type', and 'Study Time T0 Event' dropdowns.
  - If you do not think any of the predefined options for 'Type' or 'Study Time T0 Event' sufficently describes the data, select 'Other' from those dropdowns. This will automatically reveal a 'Subtype' textbox for 'Type' and a 'Study Time T0 Event Specify' textbox for 'Study Time T0 Event', allowing you to manually enter a more specific description.
 
- Finally, once all the input boxes have been filled in, click the 'Generate Filled Templates' button located above the table. The tool will begin producing the templates, which may take a few minutes to complete.

- The outputted templates will be saved in a newly created *results* folder inside the Example-Data directory. Within *results*, a subfolder named with the current date will contain all templates generated on that day.





