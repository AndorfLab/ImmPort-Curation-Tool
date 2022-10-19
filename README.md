# ImmPort-Curation-Tool

## Purpose of this tool
The purpose of the Immport Curation Tool is to easily transform study data files into ImmPort templates for upload and integration into the ImmPort database. 

## Features
* Transform Study Files and Data Dictionary into completed ImmPort template files (Currently limited to Assessments)
* Validate the files during generation
  * Can suggest preferred units that are more consistent within ImmPort


## Installation Instructions

### Steps to Install using Conda
- Clone repo onto local computer
- Setup environment and installation using conda create --name ImmPort_Curation_Tool --file requirements.txt

### Steps to Install without Conda
- Clone repo onto local computer
- Make a virtual environment outside of the folder
  - python3 -m venv ../envs/immport_curation_tool
- Activate the virtual environment
  - source ../envs/immport_curation_tool/bin/activate
- Install dependencies
  - pip3 install -r requirements.txt


## Setup Jupyter Notebooks in VS Code
