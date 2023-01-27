# ImmPort-Curation-Tool

## Purpose of this tool
The purpose of the Immport Curation Tool is to easily transform study data files into ImmPort templates for upload and integration into the ImmPort database. 

[TLDR for installation](#tldr-installationsetup) is at bottom.

## Features
* Transform Study Files and Data Dictionary into completed ImmPort template files (Currently limited to Assessments)
* Validate the files during generation
  * Can suggest preferred units that are more consistent within ImmPort


## Setup Jupyter Notebooks in VS Code
- Install jupyter extension: jupyter nbextension install --user --py widgetsnbextension
- Enable juypter extesion: jupyter nbextension enable --py widgetsnbextension


## Pre-install
Depending on your environment, you might need to setup a virtual environment to install this module.

[Python Virtual Environments](https://docs.python.org/3/library/venv.html) help isolate python packages needed for specific tasks.

There are many ways to create a virtual environment. The default way is to run the following command

`python3 -m venv /path/to/new/virtual/environment`

By convention, most users will use "venv" or ".venv" as the "/path/to/new/virtual/environment. This creates the virtual environment in your current working directory.

If you need this tool to be more broadly shared on your computer, you can choose some shared directory that multiple users can access.

After creating the virtual environment, you need to activate it. This activate causes modules to be stalled in this virtual environment, and not the default python environment. Python programs run while using this virtual environment will utilize this set of installed modules.

If the command you ran above looked like:

`python3 -m venv .venv`

To activate the virtual environment on a Unix machine (Linux/Mac):

`source .venv/bin/activate`

To activate the virtual environment on a Windows machine:

`.venv\Scripts\activate`

## Installation Instructions

To install, run the following command. Note, if you are using a virtual environment, make sure you activate the virtual environment

`pip install git+http://git@github.com/JoshuaFortriede/ImmPort-Curation-Tool.git`


## Setup instructions
Once the module has been installed, run the following command in a terminal to create a notebook with a cell to run the Curation GUI.

`ImmPortCurationTool notebook`

The above command will create a Jupyter Notebook filed called "notebook.ipynb". If you want to create the notebook with a specified name, run:

`ImmPortCurationTool notebook --notebook 'my_curation_notebook'`


# TLDR: Installation/Setup

For Unix:

`python3 -m venv .venv`

`source .venv/bin/activate`

`pip install git+http://git@github.com/JoshuaFortriede/ImmPort-Curation-Tool.git`

`ImmPortCurationTool notebook --notebook 'my_curation_notebook'`

For Windows:

`python3 -m venv .venv`

`.venv\Scripts\activate`

`pip install git+http://git@github.com/JoshuaFortriede/ImmPort-Curation-Tool.git`

`ImmPortCurationTool notebook --notebook 'my_curation_notebook'`




