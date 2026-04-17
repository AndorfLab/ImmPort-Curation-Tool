# Using the Application
The application runs as a Jupyter Notebook (notebook.ipynb), which can be launched on various platforms. For details on installing the curation tool and setting up the environment to run the notebook, please refer to the [installation guide](Installation.md).

Once the notebook is launched, you’ll see an interface with several tabs that looks like this:
 
- *Overview*: Provides general information about the tool. Much of this content is also covered in greater detail throughout this user guide.
- *1. ImmPort Files*, *2. Data Dictionary*, and *3. Study Files*: These tabs are where you upload files and input parameters.
- *Logs*: Displays status updates, warnings, and error messages.
  
Each of the functional tabs (*ImmPort Files*, *Data Dictionary*, *Study Files*, and *Logs*) includes two buttons at the bottom:
- *Reset*: Clears all inputs and resets the tab – useful when switching files or modifying parameters.
- *Help*: Offers detailed guidance specific to each tab, including explanations of upload requirements and parameter options.

If you have any difficulties with uploading files or if the outputted template is incorrect, please go to [Issues](https://github.com/AndorfLab/ImmPort-Curation-Tool/issues), select 'New Issue', and write about the problem with as much detail as possible. 

## Uploading ImmPort Files
The *1. ImmPort Files* tab is where the previously completed ImmPort templates should be uploaded. The tool allows the user to either upload each template separately (planned_visit.txt, study_file.txt, and protocol.txt) or upload them combined within a zip file. 

If you choose to 'Upload individual ImmPort files', then 3 separate file upload boxes will appear. Upload the planned visit file in the top box, the study data file in the middle box, and the protocol file in the bottom box. If uploaded correctly, the interface will not display any confirmation message.
<br><br>
<img width="493" height="380" alt="image" src="https://github.com/user-attachments/assets/03fc437a-5348-4f7a-82cf-b60c57d8ee6b" />
<hr>

If there was an issue with the upload, a warning message telling the user to select a different file will appear. Please review the logs and ensure your file is in a valid format (TXT or CSV), has standard encoding, and contains all required column names. 
<br><br>
<img width="495" height="146" alt="image" src="https://github.com/user-attachments/assets/d19a6bbe-ad91-4229-8109-ec32c5dd36df" />
<hr>
Alternatively, you can choose the 'Upload ImmPort Tab ZIP file' option. Select the ZIP file that contains the planned visit, study data, and protocol files. If uploaded correctly, the interface will not display any confirmation message.
<br><br>
<img width="492" height="320" alt="image" src="https://github.com/user-attachments/assets/f21c9cfd-0b64-4288-a7c4-e250c2cb82e0" />
<hr>
If there was an issue with the upload, a warning message telling the user to select a different ZIP file will appear.  Please review the logs and ensure the files within the ZIP are each in a valid format (TXT or CSV), have standard encoding, and contain all required column names. 
<br><br>
<img width="491" height="175" alt="image" src="https://github.com/user-attachments/assets/99f3e25a-5514-4805-89a4-3a122856cde7" />
<hr>

Please find more information about the required file formats in the [Generating ImmPort Files](Preparing-and-Preprocessing-Files.md#Generating-ImmPort-Files) section. 

## Uploading the Data Dictionary
The middle tab, *2. Data Dictionary*, is where the curated data dictionary should be uploaded. 

First, select the curated data dictionary that aligns with your study files. Once that is selected, decide if your study files should be inserted into the *Lab Test*, *Assessment*, or into both templates. Click 'Load Data Dictionary'.
<br><br>
<img width="493" height="163" alt="image" src="https://github.com/user-attachments/assets/4a07b2fa-f4a7-49aa-af05-8943a9da281c" />
<hr>
If the data dictionary successfully loaded, the button will change to 'Dictionary Loaded'.
<br><br>
<img width="494" height="163" alt="image" src="https://github.com/user-attachments/assets/b076564f-402f-492f-a556-a96b0e2b9833" />
<hr>
If the data dictionary did not successfully load, the button will change to 'Load Failed'. Please review the logs and ensure the data dictionary is in the correct format and contains the required columns before trying to reupload.
<br>
<br><br>
<img width="493" height="157" alt="image" src="https://github.com/user-attachments/assets/3cb7e7e4-10e5-4e6d-acc7-d75fd5b04a1c" />
<hr>

Please find more information about how to curate the data dictionary in the [Curating the Data Dictionary](Preparing-and-Preprocessing-Files.md#Curating-the-Data-Dictionary) section. 

## Uploading Study Files
The next tab, *3. Study Files*, is where the study-specific files are uploaded. 

First, choose the directory/folder that contains all of the study files. 
<br><br>
<img width="496" height="290" alt="image" src="https://github.com/user-attachments/assets/5c4658ae-b573-4d39-9d9e-8cc63853bab3" />
<hr>
Once the folder is selected, click 'Load Study Files Directory'. 
<br><br>
<img width="491" height="153" alt="image" src="https://github.com/user-attachments/assets/0bed103d-2745-42b9-9f87-08d00249a08d" />
<hr>
A table showing the files in the directory will appear. If the exact file name is also in the ImmPort study file (study_file.txt), a 'Description' will appear here.
Next, select the 'Table Code' from the data dictionary that matches the study file. 
<br><br>
<img width="491" height="329" alt="image" src="https://github.com/user-attachments/assets/ea66c579-b085-4472-a123-e891646fb5ce" />
<hr>
Select a 'Default Visit' if there is no study visit in the study file or data dictionary. This box is populated from the planned_visit.txt.
<br><br>
<img width="491" height="322" alt="image" src="https://github.com/user-attachments/assets/aa987156-7d55-4de1-8f2a-439c1d09d4ec" />
<hr>
Next, select the 'Template'. This should be either *Lab Test* or *Assessment*.
<br><br>
<img width="491" height="184" alt="image" src="https://github.com/user-attachments/assets/ff03cbb7-5fb3-4eee-af40-4b458595dfdf" />
<hr>
If *Lab Test* was chosen, additional selection boxes will appear. The first box, 'Protocol', is populated from the protocol.txt file that was uploaded in Tab 1. The protocol that best aligns with the study file should be selected.
<br><br>
<img width="492" height="185" alt="image" src="https://github.com/user-attachments/assets/19ea61c2-2dad-4381-886d-62f41806e12d" />
<hr>
The next box, 'Name Reported', contains lab test descriptions. Select the description that best aligns with the study file. 
<br><br>
<img width="491" height="187" alt="image" src="https://github.com/user-attachments/assets/e29f36f8-96c1-4ca0-9649-4ea44acbd078" />
<hr>
The 'Type' box contains sample types. Select the sample type that best aligns with the study file. 
<br><br>
<img width="490" height="188" alt="image" src="https://github.com/user-attachments/assets/1dd552c9-0601-4f32-947c-26cd6695cbe6" />
<hr>
Finally, the 'Study Time T0 Event' dropdown contains options for what the event 0 day is. Select the time T0 event that corresponds to the study day in the file.
<br><br>
<img width="493" height="185" alt="image" src="https://github.com/user-attachments/assets/f0434c91-ce04-4dbb-93dd-c971d3c7681d" />
<hr>
If the options for 'Type' and/or 'Study Time T0 Event' are not accurate to your data, choose 'Other'. A textbox will appear where you can write a more specific description. 
<br><br>
<img width="491" height="191" alt="image" src="https://github.com/user-attachments/assets/b2c8bdff-dd7d-4ee3-a036-b438d4e73245" />
<hr>
Alternatively, the *Assessment* template can be selected.
<br><br> 
<img width="491" height="325" alt="image" src="https://github.com/user-attachments/assets/c9022763-df1b-4d4c-a69b-c8abdab1556b" />
<hr>
If *Assessment* was chosen, a textbox will appear. A short description of the study file should be inputted into 'Assessment Name'.
<br><br>
<img width="491" height="253" alt="image" src="https://github.com/user-attachments/assets/d67424b2-71bc-4aa5-a8e1-fb7f68225a09" />
<hr>
After completing the table with your selections, click the 'Generate Filled Templates' button above the table. The tables will begin generating. Please be patient—this process may take a few minutes.
<br><br>
<img width="488" height="349" alt="image" src="https://github.com/user-attachments/assets/4c996ab8-40b3-4759-9ccc-e60dd7c7c0f6" />
<hr>
If all the templates were successfully outputted, the button will say 'Files Generated - Click to Re-Generate'. The created templates will be in the directory the study files were in, within a 'Results' folder. 
<br><br>
At this point you can now make any edits to the table and click the button again. If you do this, ensure the templates you are regenerating are not open on your computer, as this will cause an error. 
<br><br>
<img width="492" height="350" alt="image" src="https://github.com/user-attachments/assets/8af85d73-8237-4967-aa99-13eb0bc4beb8" />
<hr>
If there was an error creating one or more templates, the button will say 'Error: Some files failed to generate. Click to retry'. Please examine the logs and double check your inputs across Tabs 1, 2, and 3 to determine why the upload failed and what needs to be fixed prior to trying again.
<br><br>
<img width="494" height="352" alt="image" src="https://github.com/user-attachments/assets/91b0666c-2e83-4495-9616-2c6de3b91fe5" />
<hr>

Please find more information about the study files in the [Gathering Study Files](Preparing-and-Preprocessing-Files.md#Gathering-Study-Files) section.

