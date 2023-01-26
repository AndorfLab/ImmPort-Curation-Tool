# ImmPort-Curation-Tool

## Purpose of this tool
The purpose of the Immport Curation Tool is to easily transform study data files into ImmPort templates for upload and integration into the ImmPort database. 

## Features
* Transform Study Files and Data Dictionary into completed ImmPort template files (Currently limited to Assessments)
* Validate the files during generation
  * Can suggest preferred units that are more consistent within ImmPort


## Setup Jupyter Notebooks in VS Code
- Install jupyter extension: jupyter nbextension install --user --py widgetsnbextension
- Enable juypter extesion: jupyter nbextension enable --py widgetsnbextension


## Pre-install
Depending on your environment, you might need to setup a virtual environment to install this module.

## Installation Instructions

To install, run the following command

`pip install git+ssh://git@github.com/JoshuaFortriede/ImmPort-Curation-Tool.git@setup_tools`


## Setup instructions
Once the module has been installed, run the following command in a terminal to create a notebook with a cell to run the Curation GUI.

`ImmPortCurationTool notebook`

The above command will create a Jupyter Notebook filed called "notebook.ipynb". If you want to create the notebook with a specified name, run:

`ImmPortCurationTool notebook --notebook 'my_curation_notebook'`
