# Installation Guide

This guide explains how to install and run the ImmPort Curation Tool. The instructions are written for users with minimal coding experience and support Windows, macOS, and Linux.  

## Prerequisites  

Before installing the tool, you will need:  

- Python (version 3.10 to 3.13 recommended)  
- Git (for downloading the tool from GitHub)  

To check if Python and Git are installed, open a terminal or command prompt and run:  
```
python --version  
git --version  
```

If both commands return version numbers, you're ready to continue.  

If Python is not installed, download Python from https://www.python.org/downloads. During installation:  
- Select a version between 3.10 and 3.13  
- Check the box that says "Add Python to PATH"  

If Git is not installed, download Git from: https://git-scm.com/downloads. During installation (on Windows), choose the option: "Git from the command line and also from 3rd-party software".  

After installing either one, close and reopen the terminal and run:  
```
python --version  
git --version  
```

## Set Up a Virtual Environment 

It is recommended that you use a virtual environment to keep dependencies isolated and avoid conflicts.  

First, create the environment:  
```
python -m venv venv  
```  
This creates a folder called venv in your current directory.  

Next, activate the environment:  

On Windows:  
```
venv\Scripts\activate 
```

On macOS or Linux:  
```
source venv/bin/activate  
```  

Once activated, you should see (venv) at the beginning of your terminal prompt.  

At this point, packaging tools may need to be installed or upgraded:   
```
python -m pip install --upgrade pip setuptools wheel  
```  

## Download the Tool  

Clone the GitHub repository:  
```
git clone https://github.com/JoshuaFortriede/ImmPort-Curation-Tool.git  
cd ImmPort-Curation-Tool  
```
Install all dependesises:
```
pip install -r requirements.txt 
```

## Run the Application  

Use Voilà to launch the interactive tool:  
```
voila forms.ipynb  
```
This will open a browser window with the application interface.  

The tool can also be run on other platforms. If you want to stay within the Jupyter environment, type:
```
jupyter lab
```

The tool can also be run in external applications like Visual Studio Code (https://code.visualstudio.com/Download). 
