# Installation Guide

This guide explains how to install and run the ImmPort Curation Tool. The instructions are written for users with minimal coding experience.

## Hardware and Software Requirements

This application can be run on a standard computer. It is recommended that a computer with 16 GB of RAM is used, although the app can still be run with more minimal RAM.

This app should be supported on Windows, Mac, and Linux operating systems. Specifically, the app has been tested on the following systems:

- Windows: Windows 11, 23H2
- macOS: Sonoma 14.8.1

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

If your on Windows and your execution policy does not allow this, you can temporarily allow scripts to run with:
```
Set-ExecutionPolicy -Scope Process -ExecutionPolicy Bypass
```


Once activated, you should see (venv) at the beginning of your terminal prompt.  

At this point, packaging tools may need to be installed or upgraded:   
```
python -m pip install --upgrade pip setuptools wheel  
```  

## Download the Tool  

Clone the GitHub repository:  
```
git clone https://github.com/AndorfLab/ImmPort-Curation-Tool.git  
```

Enter the ImmPort-Curation-Tool directory: 
```
cd ImmPort-Curation-Tool  
```

Install all dependencies:
```
pip install -r requirements.txt 
```

## Run the Application  

Use Voilà to launch the interactive tool:  
```
voila forms.ipynb  
```
This will open a browser window with the application interface. On most machines, Voilà can be exited by pressing Ctrl + C in the terminal where it is running.

The tool can also be run on other platforms like Visual Studio Code (https://code.visualstudio.com/Download). 


## Next Steps

Once the application is successfully installed, you can follow the rest of this user guide to learn how to <a href="Preparing-and-Preprocessing-Files.md">prepare the files for upload</a> and <a href="Using-the-Application.md">use the application</a>. You can also test the tool with <a href="Example-Files-Overview.md">example data</a>.
