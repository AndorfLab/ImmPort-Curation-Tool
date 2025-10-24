
import ImmPortCurationTool.processRedCapFiles as rc
import ImmPortCurationTool.curationFunctions as cf
import ImmPortCurationTool.schemaFunctions as sf
from ImmPortCurationTool.version import VERSION

import traceback
import pandas as pd
import os
import re
import csv 
import zipfile
import ipywidgets as widgets
import functools
import logging
import asyncio
import json
from urllib.request import urlopen
from ipyfilechooser import FileChooser
from IPython.display import display, HTML, Javascript

custom_css = """
<style>

    .widget-button {
        font-size: 18px !important; 
        font-weight: bold !important;
        color: black !important;
    }

    .widget-container {
        margin-top: 0px !important; /* Override any inherited margin */
        padding: 0px !important; /* Remove extra space */
    }

    select {
        font-size: 18px !important;  /* Change dropdown text size */
    }

    .file-upload-label {
        font-size: 18px !important;
        font-weight: bold !important;
        color: #333 !important;
        padding-left: 10px !important;
    }

    .widget-toggle-buttons {
        display: flex !important;
        flex-wrap: nowrap !important;  /* Prevent stacking */
        gap: 10px !important;  /* Space between buttons */
    }

    .widget-toggle-buttons button {
        font-size: 16px !important;
        font-weight: bold !important;
        padding: 10px 20px !important;
        min-width: 200px !important;
        min-height: 40px !important;
        text-align: center !important;
        align-items: center !important;
        justify-content: center !important;

        line-height: 25px !important;
    }

</style>
"""

display(HTML(custom_css))

main_logger=''

documentation_base_url = "https://github.com/AndorfLab/ImmPort-Curation-Tool/blob/Master"

class Timer:

    def __init__(self, timeout, callback):

        self._timeout = timeout
        self._callback = callback

    async def _job(self):
        await asyncio.sleep(self._timeout)
        self._callback()

    def start(self):

        self._task = asyncio.ensure_future(self._job())

    def cancel(self):

        self._task.cancel()

def debounce(wait):

    def decorator(fn):

        timer = None

        def debounced(*args, **kwargs):

            nonlocal timer

            def call_it():
                fn(*args, **kwargs)

            if timer is not None:
                timer.cancel()

            timer = Timer(wait, call_it)
            timer.start()

        return debounced
    
    return decorator

class CustomFormatter(logging.Formatter):
    """Logging colored formatter, adapted from https://stackoverflow.com/a/56944256/3638629"""

    grey =      '\x1b[38;5;248m'
    blue =      '\x1b[38;5;39m'
    yellow =    '\x1b[48;5;226m'
    red =       '\x1b[38;5;196;3m'
    bold_red =  '\x1b[48;5;196;1m'
    reset =     '\x1b[0m'
    
    colors={
        "debug" : "grey",
        "info" : "blue",
        "warning" : "#FF6700",
        "error" : "red",
        "critical" : "#C11B17"
    }

    def formatTime(self, record, datefmt=None):

        return pd.to_datetime('now').strftime('%H:%M:%S')  

    def __init__(self, fmt):

        super().__init__()
        self.fmt = fmt
        self.datefmt = '%H:%M:%S'
        self.FORMATS = {
            logging.DEBUG: f"{self.format_string('debug')}[%(asctime)s] %(levelname)-8s | %(message)s",
            logging.INFO: f"{self.format_string('info')}[%(asctime)s] %(levelname)-8s | %(message)s",
            logging.WARNING: f"{self.format_string('warning')}[%(asctime)s] %(levelname)-8s | %(message)s",
            logging.ERROR: f"{self.format_string('error')}[%(asctime)s] %(levelname)-8s | %(message)s",
            logging.CRITICAL: f"{self.format_string('critical')}[%(asctime)s] %(levelname)-8s | %(message)s",
        }

    def format_string(self,level):

        if level in ["error","warning"]:
            return f"<font color='{self.colors[level]}' style='white-space: pre; font-size=16px; font-family: Consolas; font-weight: bold'>"
     
        elif level == "critical":
            return f"<font color='white' style='background-color:{self.colors[level]}; white-space: pre; font-size=16px; font-family: Consolas; font-weight: bold'>"

        return f"<font color='{self.colors[level]}' style='white-space: pre; font-size=16px; font-family: Consolas'>"

    def format(self, record):

        log_fmt = self.FORMATS.get(record.levelno)
        self._style._fmt = log_fmt

        return super().format(record)

class log_viewer(logging.Handler):

    fmt = '%(levelname)-8s | %(message)s'

    def __init__(self, *args, **kwargs):
     
        self.logger_instance = logging.getLogger(kwargs.get("name",__name__))
        logging.Handler.__init__(self, *args)

        for key, value in kwargs.items():
            if "{}".format(key) == "format":
                self.setFormatter(value)

        if "parent" in kwargs:
            self.parent = kwargs["parent"]

        if "output" in kwargs:
            self.output = kwargs["output"]
        else:
            self.output = widgets.Output(layout=widgets.Layout(max_height="425px", overflow_y="auto"))

        self.setFormatter(CustomFormatter(self.fmt))

    def emit(self, record):

        if hasattr(self, "parent"):
            self.parent.clear_button.show_hide_element(display="")

        formatted_record = self.format(record)
        print_html2 = HTML(html_text = f"<font color='blue' style='white-space: pre; font-size=16px'>{formatted_record}")

        with self.output:
            display(print_html2.widget)

class GUI_Object():

    def __init__(self, widget):

        self.widget = widget
        self.data={}
    
    def get(self):

        return self.widget
    
    def display(self):

        children=[self.get()]

        if hasattr(self, "loggers") and "console" in self.loggers:
            children.insert(0,widgets.HBox([self.objects["button_clear_console"].get(),self.loggers["console"].get()]))

        if len(children)==1:
            return self.get()
        
        return widgets.VBox([*children])
    
    def set_observe(self, callback_function, callback_data):

        self.widget.observe(functools.partial(callback_function, **callback_data), names='value')

    def toggle_display(self):

        self.widget.layout.display = "" if self.widget.layout.display == "none" else "none"

    def toggle_state(self):

        self.widget.disabled = not self.widget.disabled

    def set_state(self, state):

        self.widget.disabled = state

    def set_attribute(self, attribute, value):

        if hasattr(self.widget, attribute):
            setattr(self.widget, attribute, value)

    def get_type(self):
     
        return self.widget.__class__.__name__

    def get_module_type(self):
  
        return type(self.widget)

    def show_hide_element(self, display):

        if self is None or display is None:
            return
        
        self.widget.layout.display=display

class GUI(GUI_Object):
   
    def __init__(self):
        super().__init__(widgets.Tab(layout=widgets.Layout(min_height="500px")))

        self.template_widgets = {}  
        self.name_reported_widgets = {}  

        self.tabs={}
        self.config={}
        self.objects={}
        self.dictionary={}
        self.loggers={}
        self.main_logger = self.loggers.get("output_logger")
        self.generate_console()
        self.objects["version"]=HTML(html_text=f"<span style='font-size: 16px;'><b>Version:</b> {VERSION}</span>", )
        self.generate_gui()
        self.check_schema_version()


        self.dopdown_style = {
            'width': '220px',          
            'min_width': '220px',     
            'max_width': '220px',      
            'height': '40px',         
            'padding': '0px',        
            'margin': 'auto 5px auto 0', 
            'overflow': 'hidden',    
            'box_sizing': 'border-box', 
            'line_height': '40px',     
            'align_items': 'center',   
            'justify_content': 'center' 
        }

        self.hidden_dropdown_style = {**self.dopdown_style, 'display': 'none'}

        self.textbox_style = {
            'width': '220px',         
            'min_width': '220px',      
            'max_width': '220px',     
            'height': '70px',          
            'padding': '5px',        
            'margin': 'auto 5px auto 0',  
            'overflow': 'hidden',    
            'box_sizing': 'border-box', 
            'line_height': '50px',    
            'align_items': 'center', 
            'justify_content': 'center' 
        }

        self.hidden_textbox_style = {**self.textbox_style, 'display': 'none'}

    def add_tab(self, tab):

        old_tabs_tuple = self.widget.children
        old_tabs_list = list(old_tabs_tuple)
        old_tabs_list.append(tab.get())
        self.widget.children = tuple(old_tabs_list)
        self.set_title(tab.name)

    def set_title(self, title, index=0):

        if not index:
            index = len(self.widget.children)-1

        self.widget.set_title(index, title)

    def go_to_tab(self, tab_index=None, tab_name=None):

        if tab_index is not None:
            self.widget.selected_index=tab_index

        if tab_name is not None and tab_name in self.widget._titles.values():
            tab_index = list(filter(lambda x: x[1] == tab_name, enumerate(self.widget._titles.values())))[0][0]
            self.widget.selected_index=tab_index

        return

    def log(self, message, level="debug", flush=False):

        self.main_logger.write(message, level, flush)

        return

    def flush_log(self):

        highest_level = self.main_logger.flush()

        if highest_level is not None:
            self.loggers['console'].write(level=highest_level[0], message=f"There are {highest_level[1]} level {highest_level[0]} messages.", flush=True)
       
        return

    def create_logger(self, name="main_logger",level="debug"):  

        levels={
            "debug":logging.DEBUG,
            "info":logging.INFO,
            "warning":logging.WARNING,
            "error":logging.ERROR,
            "critical":logging.CRITICAL
        }

        layout = {
            'width': '100%',
            'height': '550px',
            'border': '1px solid black'
        }

        self.loggers[name] = logging.getLogger(name)
        self.loggers[name].setLevel(levels[level])
        self.loggers[name].widget = widgets.Output(layout=layout)
        handler = OutputWidgetHandler(self.loggers[name].widget)
        handler.setFormatter(logging.Formatter('%(asctime)s  - [%(levelname)s] %(message)s'))
        self.loggers[name].addHandler(handler)


    def clean_options(self, options):
      
        if not options:
            return ["--Select--"]
        
        cleaned = sorted({str(o).strip() for o in options if o and str(o).strip()})

        return ["--Select--"] + cleaned


    def reset_tab1(self, b):  

        if "filechooser_study_tab_file" in self.objects:
            self.objects["filechooser_study_tab_file"].reset("", "")  

        if "filechooser_planned_visits" in self.objects:
            self.objects["filechooser_planned_visits"].reset("", "")  

        if "filechooser_study_files" in self.objects:
            self.objects["filechooser_study_files"].reset("", "")  

        if "filechooser_protocol_files" in self.objects:
            self.objects["filechooser_protocol_files"].reset("", "")  

        if "error_message_study_files" in self.objects:
            self.objects["error_message_study_files"].show_hide_element(display="none")

        if "error_message_planned_visits" in self.objects:
            self.objects["error_message_planned_visits"].show_hide_element(display="none")

        if "error_message_study_tab_file" in self.objects:
            self.objects["error_message_study_tab_file"].show_hide_element(display="none")

        if "error_message_protocol_files" in self.objects:
            self.objects["error_message_protocol_files"].show_hide_element(display="none")

        if "text_study_id" in self.objects:
            self.objects["text_study_id"].reset()

        if "dropdown_study_visit_list" in self.objects:
            self.objects["dropdown_study_visit_list"].set_options(["Please upload the planned visit file"])

        if "dropdown_study_file_list" in self.objects:
            self.objects["dropdown_study_file_list"].set_options(["Please upload the study data file"])

        if "dropdown_protocol_list" in self.objects:
            self.objects["dropdown_protocol_list"].set_options(["Please upload the protocol file"])
            
        if "toggle_current_immport_study" in self.objects:
            old_value = self.objects["toggle_current_immport_study"].widget.value
            self.objects["toggle_current_immport_study"].widget.value = 0  

        for key in ["box_study_visit_list", "box_study_file_list", "box_protocol_list"]:
            if key in self.objects:
                self.objects[key].show_hide_element(display="")
                
        self.log("🔄 ImmPort Files tab has been reset", level="info")

    def reset_tab2(self, b):  

        if "filechooser_data_dictionary" in self.objects:
            self.objects["filechooser_data_dictionary"].reset("", "")

        if "dropdown_template_type" in self.objects:
            del self.objects["dropdown_template_type"]

        self.objects["dropdown_template_type"] = Dropdown(
            options=['Assessment', 'Lab Test', 'Assessment & Lab Test'],
            value='Assessment & Lab Test',
            description='<b><span style="font-size:18px;">Choose which template(s) to generate from your data</span></b>',
            tooltip="Select the form or forms you plan on generating in '3. Study Files'",
            style={'description_width': 'initial'}
        )
        
        if "button_filechooser_data_dictionary_load" in self.objects:
            del self.objects["button_filechooser_data_dictionary_load"]

        self.objects["button_filechooser_data_dictionary_load"] = self.objects["filechooser_data_dictionary"].add_load_button(
            description="Load Data Dictionary",
            tooltip="Load a curated data dictionary file",
            callback=self.load_data_dictionary
        )
        
        if "button_form_column_confirm" in self.objects:
            del self.objects["button_form_column_confirm"]

        self.objects["button_form_column_confirm"] = Button(
            text="Confirm", 
            tooltip='Confirm that the selected column from the data dictionary contains the instrument/CRF/form codes', 
            callback=self.load_data_dictionary_columns
        )
        
        if "tab_row_dd_row" in self.objects:
            self.objects["tab_row_dd_row"].children = [
                self.objects["filechooser_data_dictionary"].get()
            ]
        
        if "tab_row_dd_template_row" in self.objects:
            self.objects["tab_row_dd_template_row"].children = [
                self.objects["dropdown_template_type"].get(),
                self.objects["button_filechooser_data_dictionary_load"].get()
            ]

            self.hide_row("tab_row_dd_template_row")
        
        if hasattr(self, 'dictionary'):
            del self.dictionary
        
        if 'data_dictionary' in self.config:
            del self.config['data_dictionary']
        
        self.log("🔄 Data Dictionary tab has been reset", level="info")

    def reset_tab3(self, b):  

        if "filechooser_study_file_directory" in self.objects:
            self.objects["filechooser_study_file_directory"].reset("", "")  

        if "button_filechooser_study_file_directory_load" in self.objects:
            del self.objects["button_filechooser_study_file_directory_load"]

        self.objects["button_filechooser_study_file_directory_load"] = self.objects["filechooser_study_file_directory"].add_load_button(
            description="Load study files directory",
            tooltip="Load the study files directory",
            callback=self.load_study_files
        )

        self.objects["tab_row_study_files_filechooser"].children = [
            self.objects["filechooser_study_file_directory"].get(),
            self.objects["button_filechooser_study_file_directory_load"].get()
        ]

        if "file_list_df" in self.data:
            dropdown_defaults = {
                "Table Code": "--Select--",
                "Default Visit": "--Select--",
                "Template": "--Select--",
                "Protocol": "--Select--",
                "Name Reported": "--Select--",
                "Type": "--Select--",
                "Study Time T0 Event": "--Select--"
            }

            text_fields = [
                "Assessment Name",
                "Subtype",
                "Study Time T0 Event Specify"
            ]

            for col in dropdown_defaults:
                if col in self.data["file_list_df"].columns:
                    self.data["file_list_df"][col] = dropdown_defaults[col]

            for col in text_fields:
                if col in self.data["file_list_df"].columns:
                    self.data["file_list_df"][col] = ""

        if "tables_section" in self.objects:
            self.objects["tables_section"].children = []  
            self.objects["tables_section"].layout.visibility = 'hidden'
 
        spacer = widgets.HTML(value="<div style='height: 10px;'></div>")

        self.objects["tab3_layout"].children = [  
            spacer,
            self.objects["tab_row_study_files_filechooser"], 
            spacer,
            self.objects["bottom_buttons_3"],
            spacer
        ]

        self.log("🔄 Study Files tab has been reset", level="info")

    def generate_gui(self):

        self.objects["title"] = widgets.HTML(value="<h1 style='text-align:center; color:#3E6962; font-size:32px;'>ImmPort Curation Tool</h1>") 

        tab_titles = ["Overview", "1. ImmPort Files", "2. Data Dictionary", "3. Study Files", "Logs"]
        tab_colors = ["#98b3a2", "#F4DAC1", "#ADD5CC", "#dca485", "#D6C097"]  

        tab_contents = {
            "Overview": self.generate_tab_help(),
            "1. ImmPort Files": self.generate_tab_study_info(),
            "2. Data Dictionary": self.generate_tab_data_dictionary(),
            "3. Study Files": self.generate_tab_study_files(),
            "Logs": self.generate_tab_logging(),
        }

        content_area = widgets.Output()

        def on_tab_click(button):

            for btn in tab_buttons:
                btn.style.border = "none"
                btn.layout.border = "none"
            
            button.style.border = "2px solid #3E6962"  
            button.layout.border = "2px solid #3E6962"

            with content_area:
                content_area.clear_output(wait=True)

                if button.description == "Logs" and "output_logger_instance" in self.objects:
                    self.objects["output_logger_instance"].replay()

                display(tab_contents[button.description])

        tab_buttons = []

        for i, title in enumerate(tab_titles):
            button = widgets.Button(
                description=title,
                style={"button_color": tab_colors[i]},
                layout=widgets.Layout(
                    width="auto",
                    flex="1",
                    height="40px",
                    border="none"  
                )
            )
            button.on_click(on_tab_click)
            tab_buttons.append(button)

        if tab_buttons:
            tab_buttons[0].style.border = "2px solid #3E6962"
            tab_buttons[0].layout.border = "2px solid #3E6962"

        button_container = widgets.HBox(
            tab_buttons,
            layout=widgets.Layout(
                width="100%",
                display="flex",
                justify_content="space-between"
            )
        )

        with content_area:
            display(tab_contents[tab_titles[0]])

        ui = widgets.VBox([
            self.objects["title"],
            button_container,
            content_area
        ], layout=widgets.Layout(margin="0px", padding="0px"))

        return ui
    
    def clear_console(self,b):

        self.loggers['console'].widget.clear_output()

    def generate_tab_help(self):

        overview_header = widgets.HTML(value=f"""
            <div style='display: flex; justify-content: space-between; align-items: center; width: 100%;'>
                <h2 style='color:black; margin-top: 15px; margin-bottom: 0px; font-size: 24px;'>🔍 About this Tool</h2>
                <span style='font-size: 18px; color: black;'> {self.objects["version"].get().value} </span>
            </div>

            <p style='font-size:18px; color:black; margin-top: 15px; margin-bottom: 25px;'>
                The purpose of this tool is to transform data files/tables from a study into ImmPort <i>Lab Test</i> or <i>Assessment</i> templates for upload and integration into the ImmPort database.
                The tool has 3 upload sections.
                <br>
                <br>
                <b>1. ImmPort Files:</b> Start the data transformation by uploading specific files from ImmPort.
                <br>
                <br>
                <b>2. Data Dictionary:</b> Next, upload the curated study data dictionary.
                <br>
                <br>
                <b>3. Study Files:</b> Finally, upload the study files folder and choose the files you would like to incorporate into the final template.
                <br>
                <br>
                The last tab, <b>Logs</b>, is where progress and error messages appear.
            </p>
        """)

        def download_example_data(url):
            display(Javascript(f'window.open("{url}", "_blank");'))

        example_data_url = "https://github.com/AndorfLab/ImmPort-Curation-Tool/raw/Master/Example-Data.zip" 

        download_button = widgets.Button(
            description="Download",
            tooltip="Download sample data files to test the tool",
            icon="download",
            layout=widgets.Layout(width="140px")
        )

        download_button.on_click(lambda b: download_example_data(example_data_url))

        example_header_row = widgets.HBox([
            widgets.HTML("<h2 style='color:black; margin-top: 0px; margin-bottom: 0px; font-size: 24px;'>🔢 Example Data</h2>"),
            widgets.Box([download_button], layout=widgets.Layout(margin='0 0 0 20px'))
        ], layout=widgets.Layout(justify_content="flex-start", align_items="center", width="100%"))

        example_paragraph = widgets.HTML(value="""
            <p style='font-size:18px; color:black; margin-top: 15px;'>
             
                The tool's functionality and required data formats can be explored with a sample dataset based on ImmPort study SDY1550 (CoFAR baked egg immunotherapy trial). 
                Files have been anonymized and simplified for demonstration.
                <br>
                <br>
                The sample data includes:
                <ul style='font-size:18px; margin-top: 0px; margin-bottom: 0px; padding-left: 30px;'>
                    <li><strong>ImmPort Template Files</strong> (ZIP):
                        <ul style='padding-left: 20px;'>
                            <li>study_data.txt</li>
                            <li>planned_visit.txt</li>
                            <li>protocol.txt</li>
                        </ul>
                    </li>
                    <br>
                    <li><strong>Curated Data Dictionary</strong></li>
                    <br>                                        
                    <li><strong>Study Specific Data</strong>:
                        <ul style='padding-left: 20px;'>
                            <li>For Assessment Template: Medical History 1, Medical History 2, Oral Food Challenge (OFC), and Skin Prick Test (SPT)</li>
                            <li>For Lab Test Template: Basophil and Immunoglobulin E (IgE)</li>
                        </ul>
                    </li>
                </ul>
                <br>
                <a href='https://github.com/AndorfLab/ImmPort-Curation-Tool/blob/Master/documentation/Example-Files-Overview.md' 
                target='_blank' 
                style='font-size:18px; color:#0077b6; text-decoration:none; font-weight:bold;'>
                Click here for a step-by-step walkthrough of how to use the example data.
                </a>                      
            </p>
        """)

        documentation_header = widgets.HTML(value="""
            <h2 style='color:black; text-align:left; margin-top: 15px; margin-bottom: 0px; font-size: 24px;'>📄 Documentation Links</h2>
            
            <p style='font-size:18px; color:black; margin-top: 15px; margin-bottom: 0px;'>
                The following documents provide additional guidance, FAQs, error troubleshooting, and formatting requirements.
                Use them as needed to better understand how to prepare and use your data with this tool.
            </p>
        """)

        documentation = [
            {"label":"Preparing and Preprocessing Files","text":"Guidance on curating the files required for upload.", "link":"/documentation/Preparing-and-Preprocessing-Files.md"},
            {"label":"Using the Application","text":"Guidance on using the curation tool.", "link":"/documentation/Using-the-Application.md"},
            {"label":"Common Errors","text":"Common errors and how to solve them", "link":"/documentation/Logging Errors.md"},
            {"label":"FAQ","text":"Commonly asked questions", "link":"/documentation/FAQ.md"}
        ]

        documentation_base_url = "https://github.com/AndorfLab/ImmPort-Curation-Tool/blob/Master"

        doc_links = [
            widgets.HTML(value=f"""
                <p style='font-size:18px; margin-bottom:2px;'>
                    <span style='font-weight:bold; color:black;'>•</span>
                    <a href='{documentation_base_url}/{doc['link']}' target='_blank' 
                        style='text-decoration:none; font-weight:bold; color:#0077b6;'>
                        {doc['label']}
                    </a>: {doc['text']}
                </p>
            """)
            for doc in documentation
        ]

        spacer = widgets.HTML(value="<div style='height: 10px;'></div>")
        
        tab_content = widgets.VBox([
            overview_header,
            example_header_row,
            example_paragraph,
            documentation_header, 
            widgets.VBox(doc_links),
            spacer 
        ], layout=widgets.Layout(padding="1px"))

        return tab_content

    def generate_tab_study_info(self):

        try:

            self.objects["toggle_current_immport_study"] = ToggleButtons(description='<b><span style="font-size:18px;">🔘 Choose initial input type</span></b>', options=[('Upload individual ImmPort files',0),('Upload ImmPort Tab ZIP file',1)], value=0, tooltips=['Upload 3 files from ImmPort','Upload 1 ZIP file from ImmPort'], style=dict(description_width='initial',button_width='auto'))

            self.objects["error_message_study_tab_file"] = HTML(html_text="<span style='color: red; font-size: 16px;'>⚠️ Please select a valid ImmPort study Tab ZIP file </span>", description="")
            self.objects["error_message_study_tab_file"].show_hide_element(display="none")  

            self.objects["filechooser_study_tab_file"] = File_Chooser(name="filechooser_study_tab_file", title='<b><span style="font-size:18px;">📁 Select the ImmPort study Tab ZIP file</span></b>', tooltip='Load a study Tab file', multiple=False, filter_pattern=['*.zip'], style=dict(description_width='initial')) # filter_pattern=['SDY*-DR*_Tab.zip']
            self.objects["filechooser_study_tab_file"].set_onclick(self, callback_function=self.on_select_study_tab_file_with_error_handling, callback_data={"gui":self, "fc_name":"filechooser_study_tab_file"})

            file_chooser_with_error = widgets.HBox([self.objects["filechooser_study_tab_file"].get(), self.objects["error_message_study_tab_file"].get()])

            self.objects["filechooser_planned_visits"] = File_Chooser(name="filechooser_planned_visits", title='<b><span style="font-size:18px;">📁 Select the ImmPort planned visit file</span></b>', tooltip='Load a planned visit file', multiple=False, filter_pattern=['*.csv', '*.txt'], style=dict(description_width='initial'))
            self.objects["filechooser_planned_visits"].set_onclick(self, callback_function=self.load_planned_visit_file, callback_data = {})

            self.objects["error_message_planned_visits"] = HTML(html_text="<span style='color: red; font-size: 16px;'>⚠️ Please select a valid planned visits file </span>", description="")
            self.objects["error_message_planned_visits"].show_hide_element(display="none")  

            self.objects["file_chooser_planned_visits_with_error"] = widgets.HBox([self.objects["filechooser_planned_visits"].get(), self.objects["error_message_planned_visits"].get()])
            
            self.objects["filechooser_study_files"] = File_Chooser(name="filechooser_study_files", title='<b><span style="font-size:18px;">📁 Select the ImmPort study file</span></b>', tooltip='Load a study files file',multiple=False, filter_pattern=['*.csv', '*.txt'], style=dict(description_width='initial'))
            self.objects["filechooser_study_files"].set_onclick(self, callback_function=self.load_study_file, callback_data = {})

            self.objects["error_message_study_files"] = HTML(html_text="<span style='color: red; font-size: 16px;'>⚠️ Please select a valid study data file </span>", description="")
            self.objects["error_message_study_files"].show_hide_element(display="none")

            self.objects["file_chooser_study_files_with_error"] = widgets.HBox([self.objects["filechooser_study_files"].get(), self.objects["error_message_study_files"].get()])

            self.objects["filechooser_protocol_files"] = File_Chooser(name="filechooser_protocol_files", title='<b><span style="font-size:18px;">📁 Select the ImmPort protocol file</span></b>', tooltip='Load a protocol file',multiple=False, filter_pattern=['*.csv', '*.txt'], style=dict(description_width='initial'))
            self.objects["filechooser_protocol_files"].set_onclick(self, callback_function=self.load_protocol_file, callback_data = {})

            self.objects["error_message_protocol_files"] = HTML(html_text="<span style='color: red; font-size: 16px;'>⚠️ Please select a valid protocol file </span>", description="")
            self.objects["error_message_protocol_files"].show_hide_element(display="none")

            self.objects["file_chooser_protocol_files_with_error"] = widgets.HBox([self.objects["filechooser_protocol_files"].get(), self.objects["error_message_protocol_files"].get()])

            self.objects["label_study_id"] = widgets.HTML(
                "<b><span style='font-size:18px;'>🆔 Input the study ID</span></b>"
            )

            self.objects["text_study_id"] = TextField(placeholder="SDY9999", regex=r"SDY\d+", layout=widgets.Layout(width="350px"))

            study_id_section = widgets.VBox([
            self.objects["label_study_id"],
            self.objects["text_study_id"].get()
            ])

            self.objects["label_study_visit_list"] = widgets.HTML(
                "<b><span style='font-size:18px;'>🔍 View the loaded planned visits</span></b>"
            )
            
            self.objects["dropdown_study_visit_list"] = Dropdown(options=[''], tooltip='View the loaded planned visits from planned_visit.txt')

            self.objects["dropdown_study_visit_list"].set_options(["Please upload the planned visit file"])

            study_visit_list_section = widgets.VBox([
            self.objects["label_study_visit_list"],
            self.objects["dropdown_study_visit_list"].get()
            ])

            self.objects["box_study_visit_list"] = VBox(name="box_study_visit_list")
            self.objects["box_study_visit_list"].set_children([study_visit_list_section])
            self.objects["box_study_visit_list"].show_hide_element(display="")

            self.objects["label_study_file_list"] = widgets.HTML(
                "<b><span style='font-size:18px;'>🔍 View the loaded study files</span></b>"
            )
            
            self.objects["dropdown_study_file_list"] = Dropdown(options=[''], tooltip='View the loaded study files from study_data.txt')

            self.objects["dropdown_study_file_list"].set_options(["Please upload the study data file"])

            study_file_list_section = widgets.VBox([
            self.objects["label_study_file_list"],
            self.objects["dropdown_study_file_list"].get()
            ])

            self.objects["box_study_file_list"] = VBox(name="box_study_file_list")
            self.objects["box_study_file_list"].set_children([study_file_list_section])
            self.objects["box_study_file_list"].show_hide_element(display="")

            self.objects["label_protocol_list"] = widgets.HTML(
                "<b><span style='font-size:18px;'>🔍 View the loaded protocol</span></b>"
            )
            
            self.objects["dropdown_protocol_list"] = Dropdown(options=[''], tooltip='View the loaded protocols from protocol.txt')

            self.objects["dropdown_protocol_list"].set_options(["Please upload the protocol file"])

            protocol_list_section = widgets.VBox([
            self.objects["label_protocol_list"],
            self.objects["dropdown_protocol_list"].get()
            ])

            self.objects["box_protocol_list"] = VBox(name="box_protocol_list")
            self.objects["box_protocol_list"].set_children([protocol_list_section])
            self.objects["box_protocol_list"].show_hide_element(display="")

            box_immport_study_yes = VBox(name="box_immport_study_yes")
            box_immport_study_no = VBox(name="box_immport_study_no")

            box_immport_study_yes.toggle_display()

            box_planned_visits = VBox(name='box_planned_visits')
            box_planned_visits.set_children([self.objects['file_chooser_planned_visits_with_error']])

            box_study_files = VBox(name='box_study_files')
            box_study_files.set_children([self.objects['file_chooser_study_files_with_error']])

            box_protocol_files = VBox(name='box_protocol_files')
            box_protocol_files.set_children([self.objects['file_chooser_protocol_files_with_error']])

            box_immport_study_yes.set_children([file_chooser_with_error])

            self.objects["reset_tab1_button"] = Button(text="Reset Tab", tooltip="Reset all inputs in Tab 1", style="warning", callback=self.reset_tab1, width="140px", icon="trash")

            self.objects["help_button_1"] = widgets.Button(description='Help', tooltip='Click for help', icon='question-circle')

            self.objects["help_button_1"].style.button_color = '#F7F6BB'

            self.objects["help_text_1"] = widgets.HTML(
                value=f"""
                <div style='color: black; font-family: Arial, sans-serif; font-size: 14px;
                            padding: 5px; border: 1px solid #ccc; background-color: #f9f9f9;
                            border-radius: 5px;'>
                    <h2 style='text-align: center; font-weight: bold; margin: 5px 0;'>File Type</h2>

                    <b>Choose initial input type:</b> Decide if you want to upload the 3 ImmPort files individually or together as a ZIP file. <br>
      
                    <h2 style='text-align: center; font-weight: bold; margin: 5px 0;'>File Upload</h2>

                    <b>Upload individual ImmPort files:</b> Choose this option if you want to upload the ImmPort planned visit file (planned_visit.txt), 
                    the ImmPort study file (study_file.txt), and the ImmPort protocol file (protocol.txt) individually. 
                    After uploading each file, a preview will be shown below the upload area so you can confirm that the correct file was selected. <br>
              
                    <h2 style='text-align: center; font-weight: bold; margin: 5px 0;'>ZIP Upload</h2> 

                    <b>Upload ImmPort Tab ZIP file:</b> Choose this option if you want to upload a ZIP file that contains the 3 required ImmPort files 
                    (planned_visit.txt, study_file.txt, and protocol.txt). <br>

                    <h2 style='text-align: center; font-weight: bold; margin: 5px 0;'>Reset</h2> 

                    <b>Reset Tab:</b> This button will reset everything in the '1. ImmPort Files' tab. <br>

                    <h2 style='text-align: center; font-weight: bold; margin: 5px 0;'>Additional Information</h2>
                        <a title='Information on ImmPort data files' 
                            href='{documentation_base_url}/documentation/Preparing-and-Preprocessing-Files.md#generating-immport-files' 
                            style='font-size: 16px; text-decoration: none; color: #0077b6;'>
                            <b>Click for more information on how to download data from ImmPort</b>
                        </a> <br>

                        <a title='Information on ImmPort data in the app' 
                            href='{documentation_base_url}/documentation/Using-the-Application.md#uploading-immport-files' 
                            style='font-size: 16px; text-decoration: none; color: #0077b6;'>
                            <b>Click for more information on how to upload the ImmPort File</b>
                        </a>
                </div>
                """,
                layout={'width': '600px', 'height': 'auto'}
            )

            self.objects["help_text_1_box"] = widgets.VBox([self.objects["help_text_1"]])
            self.objects["help_text_1_box"].layout.display = 'none' 

            def toggle_help_text_1(b):
                if self.objects["help_text_1_box"].layout.display == 'none':
                    self.objects["help_text_1_box"].layout.display = 'block'  
                else:
                    self.objects["help_text_1_box"].layout.display = 'none'   

            self.objects["help_button_1"].on_click(toggle_help_text_1)

            self.objects["help_section_1"] = widgets.HBox([
                self.objects["help_button_1"],
                self.objects["help_text_1_box"]
            ])

            bottom_buttons_1 = widgets.HBox([
                self.objects["reset_tab1_button"].get(),
                self.objects["help_section_1"]
            ])

            spacer = widgets.HTML(value="<div style='height: 10px;'></div>")

            tab = widgets.VBox([
                spacer,
                self.objects["toggle_current_immport_study"].get(), 
                spacer,
                box_immport_study_yes.get(), 
                spacer,
                box_immport_study_no.get(),
                box_planned_visits.get(),
                self.objects["box_study_visit_list"].get(),
                spacer,
                box_study_files.get(),
                self.objects["box_study_file_list"].get(),
                spacer,
                box_protocol_files.get(),
                self.objects["box_protocol_list"].get(),
                spacer,
                bottom_buttons_1,
                spacer
            ])

            self.objects["toggle_current_immport_study"].set_observe(callback_function=self.toggle_show_hide, callback_data={
                "toggle":{
                    1:[box_immport_study_yes], 
                    0:[box_immport_study_no,box_planned_visits, self.objects["box_study_visit_list"], box_study_files, self.objects["box_study_file_list"], box_protocol_files, self.objects["box_protocol_list"]]
                    }
                })

        except Exception as e:
            self.log(message=f"Error in selecting ImmPort study file: {str(e)}\n{traceback.format_exc()}", level="error", flush=True)
            self.flush_log()

            tab = widgets.VBox([
                widgets.HTML(value="<h2 style='color: red;'>Error: Failed to load the ImmPort study tab.</h2>"),
                widgets.HTML(value=f"<p style='color: red;'>{str(e)}</p>")
            ])

        return tab

    def on_select_study_tab_file_with_error_handling(self, value, gui=None, fc_name=None):

        try:
            if value.description == "Change":
                zip_path = gui.objects[fc_name].widget.selected_path
                zip_file = gui.objects[fc_name].widget.selected_filename
                
                try:
                    with zipfile.ZipFile(os.path.join(zip_path, zip_file), 'r') as z:
                        file_list = z.namelist()
                        gui.log(f"Files in ZIP: {file_list}", level="debug")
                except Exception as zip_err:
                    gui.log(f"ZIP file error: {str(zip_err)}", level="error")
                    raise ValueError("Invalid or corrupted ZIP file")
                
                required_files = {
                    "planned_visit": "planned_visit.txt",
                    "study_files": "study_file.txt",
                    "protocol": "protocol.txt"
                }
                
                missing_files = []
                for data_key, filename in required_files.items():
                    gui.data[data_key] = cf.readFileFromZip(
                        zip_path,
                        zip_file,
                        filename,
                        gui=gui,
                        case_sensitive=False
                    )
                    if gui.data[data_key] is None:
                        missing_files.append(filename)
                
                if missing_files:
                    raise ValueError(f"Missing required files in ZIP: {', '.join(missing_files)}")
 
                visit_names = gui.get_planned_visits(nameonly=True, returnType="list")

                if "dropdown_study_visit_list" in gui.objects:
                    gui.objects["dropdown_study_visit_list"].set_options(visit_names)

                    if "study_visit_list_section" in gui.objects:
                        gui.objects["study_visit_list_section"].children = [
                            gui.objects["label_study_visit_list"],
                            gui.objects["dropdown_study_visit_list"].get()
                        ]

                study_file_names = gui.get_study_files(nameonly=True, returnType="list")

                if "dropdown_study_file_list" in gui.objects:
                    gui.objects["dropdown_study_file_list"].set_options(study_file_names)

                    if "study_file_list_section" in gui.objects:
                        gui.objects["study_file_list_section"].children = [
                            gui.objects["label_study_file_list"],
                            gui.objects["dropdown_study_file_list"].get()
                        ]
                
                
                protocol_names = gui.get_protocols(nameonly=True, returnType="list")

                if "dropdown_protocol_list" in gui.objects:
                    gui.objects["dropdown_protocol_list"].set_options(protocol_names)

                    if "protocol_list_section" in gui.objects:
                        gui.objects["protocol_list_section"].children = [
                            gui.objects["label_protocol_list"],
                            gui.objects["dropdown_protocol_list"].get()
                        ]
                
                gui.log("✅ ImmPort Tab ZIP file successfully uploaded and validated.", level="info", flush=True)

                gui.objects["error_message_study_tab_file"].show_hide_element(display="none")

        except Exception as e:
            gui.objects["error_message_study_tab_file"].show_hide_element(display="")
            gui.log(f"Error loading ImmPort study Tab file: {str(e)}", level="error", flush=True)
            gui.flush_log()

    def load_study_file(self, value):

        try:

            if value.description != "Change":
                return

            filename = self.objects["filechooser_study_files"].get_filepath()

            if not filename or not os.path.isfile(filename):
                self.objects["error_message_study_files"].show_hide_element(display="")
                self.log(message="No file selected or file does not exist.", level="error", flush=True)
                return

            sep = None

            with open(filename, 'r', newline='') as f:
                sample = f.read(2048)
                f.seek(0)
                try:
                    dialect = csv.Sniffer().sniff(sample)
                    sep = dialect.delimiter
                except csv.Error:
                    sep = "\t" if "\t" in sample else ","

            try:
                self.data["study_files"] = pd.read_csv(filename, sep=sep, encoding="utf-8-sig")
            except UnicodeDecodeError:
                self.data["study_files"] = pd.read_csv(filename, sep=sep, encoding="latin1")

            self.data["study_files"].columns = self.data["study_files"].columns.str.strip()

            if self.data["study_files"].shape[1] == 1:

                sep_retry = "\t" if sep == "," else ","

                try:
                    self.data["study_files"] = pd.read_csv(filename, sep=sep_retry, encoding="utf-8-sig")
                except UnicodeDecodeError:
                    self.data["study_files"] = pd.read_csv(filename, sep=sep_retry, encoding="latin1")

                self.data["study_files"].columns = self.data["study_files"].columns.str.strip()

            missing_columns = []

            mandatory_column = next(
                (col for col in ["Study Accession", "STUDY_ACCESSION"]
                if col in self.data["study_files"].columns),
                None
            )

            if not mandatory_column:
                missing_columns.append("'Study Accession' or 'STUDY_ACCESSION'")

            mandatory_column2 = next(
                (col for col in ["File Name", "FILE_NAME"]
                if col in self.data["study_files"].columns),
                None
            )

            if not mandatory_column2:
                missing_columns.append("'File Name' or 'FILE_NAME'")

            if missing_columns:
                self.objects["error_message_study_files"].show_hide_element(display="")
                self.log(
                    message=f"Invalid study file. Columns found: {list(self.data['study_files'].columns)}",
                    level="error", flush=True
                )
                raise ValueError(
                    f"Study file must contain: {', and '.join(missing_columns)}"
                )

            rename_map = {
                "Study File Accession": "STUDY_FILE_ACCESSION",
                "Study Accession": "STUDY_ACCESSION",
                "Study File Type": "STUDY_FILE_TYPE",
                "File Name": "FILE_NAME",
                "Description": "DESCRIPTION"
            }
            rename_map = {k: v for k, v in rename_map.items() if k in self.data["study_files"].columns}

            if rename_map:
                self.data["study_files"].rename(columns=rename_map, inplace=True)

            study_file_names = self.get_study_files(nameonly=True, returnType="list")
            self.objects["dropdown_study_file_list"].set_options(study_file_names)
            self.objects["error_message_study_files"].show_hide_element(display="none")
            self.objects["box_study_file_list"].show_hide_element(display="block")

            self.log("✅ ImmPort study file successfully uploaded and validated.", level="info", flush=True)

        except Exception as e:
            self.objects["error_message_study_files"].show_hide_element(display="")
            self.objects["box_study_file_list"].show_hide_element(display="none")

            self.log(
                message=f"Error loading study file: {str(e)}",
                level="error", flush=True
            )
            self.flush_log()

    def load_planned_visit_file(self, value):

        try:

            if value.description != "Change":
                return

            planned_visit_filename = self.objects["filechooser_planned_visits"].get_filepath()

            if not planned_visit_filename or not os.path.isfile(planned_visit_filename):
                self.objects["error_message_planned_visits"].show_hide_element(display="")
                self.log(message="No file selected or file does not exist.", level="error", flush=True)
                return

            sep = None

            with open(planned_visit_filename, 'r', newline='') as pv:
                sample = pv.read(2048)
                pv.seek(0)
                try:
                    dialect = csv.Sniffer().sniff(sample)
                    sep = dialect.delimiter
                except csv.Error:
                  
                    sep = "\t" if "\t" in sample else ","

            try:
                self.data["planned_visit"] = pd.read_csv(planned_visit_filename, sep=sep, encoding="utf-8-sig")
            except UnicodeDecodeError:
                self.data["planned_visit"] = pd.read_csv(planned_visit_filename, sep=sep, encoding="latin1")

            self.data["planned_visit"].columns = self.data["planned_visit"].columns.str.strip()

            if self.data["planned_visit"].shape[1] == 1:

                sep_retry = "\t" if sep == "," else ","

                try:
                    self.data["planned_visit"] = pd.read_csv(planned_visit_filename, sep=sep_retry, encoding="utf-8-sig")
                except UnicodeDecodeError:
                    self.data["planned_visit"] = pd.read_csv(planned_visit_filename, sep=sep_retry, encoding="latin1")

                self.data["planned_visit"].columns = self.data["planned_visit"].columns.str.strip()

            missing_columns = []

            mandatory_column = next(
                (col for col in ["PV Accession", "PLANNED_VISIT_ACCESSION"]
                if col in self.data["planned_visit"].columns),
                None
            )

            if not mandatory_column:
                missing_columns.append("'PV Accession' or 'PLANNED_VISIT_ACCESSION'")

            mandatory_column2 = next(
                (col for col in ["Name", "NAME"]
                if col in self.data["planned_visit"].columns),
                None
            )

            if not mandatory_column2:
                missing_columns.append("'Name' or 'NAME'")

            if missing_columns:
                self.objects["error_message_planned_visits"].show_hide_element(display="")
                self.log(
                    message=f"Invalid planned visits file. Columns found: {list(self.data['planned_visit'].columns)}",
                    level="error", flush=True
                )
                raise ValueError(
                    f"Planned visits file must contain: {', and '.join(missing_columns)}"
                )

            rename_map = {
                "PV Accession": "PLANNED_VISIT_ACCESSION",
                "Name": "NAME",
                "Min Start Day": "MIN_START_DAY",
                "Max Start Day": "MAX_START_DAY",
                "Start Rule": "START_RULE",
                "End Rule": "END_RULE",
                "Order Number": "ORDER_NUMBER",
            }
            rename_map = {k: v for k, v in rename_map.items()
                        if k in self.data["planned_visit"].columns}

            if rename_map:
                self.data["planned_visit"].rename(columns=rename_map, inplace=True)

            visit_names = get_planned_visits(
                self.data["planned_visit"], nameonly=True, returnType="list"
            )
            self.objects["dropdown_study_visit_list"].set_options(visit_names)
            self.objects["error_message_planned_visits"].show_hide_element(display="none")
            self.objects["box_study_visit_list"].show_hide_element(display="block")

            self.log("✅ ImmPort planned visit file successfully uploaded and validated.", level="info", flush=True)

        except Exception as e:

            self.objects["error_message_planned_visits"].show_hide_element(display="")
            self.objects["box_study_visit_list"].show_hide_element(display="none")

            self.log(
                message=f"Error loading planned visits file: {str(e)}",
                level="error", flush=True
            )
            self.flush_log()

            
    def load_protocol_file(self, value):

        try:
            if value.description != "Change":
                return

            protocol_filename = self.objects["filechooser_protocol_files"].get_filepath()

            if not protocol_filename or not os.path.isfile(protocol_filename):
                self.objects["error_message_protocol_files"].show_hide_element(display="")
                self.log(message="No file selected or file does not exist.", level="error", flush=True)
                return
            
            sep = None

            with open(protocol_filename, 'r', newline='') as pv:
                sample = pv.read(2048)
                pv.seek(0)
                try:
                    dialect = csv.Sniffer().sniff(sample)
                    sep = dialect.delimiter
                except csv.Error:
                    sep = "\t" if "\t" in sample else ","

            try:
                self.data["protocol"] = pd.read_csv(protocol_filename, sep=sep, encoding="utf-8-sig")
            except UnicodeDecodeError:
                self.data["protocol"] = pd.read_csv(protocol_filename, sep=sep, encoding="latin1")

            self.data["protocol"].columns = self.data["protocol"].columns.str.strip()

            if self.data["protocol"].shape[1] == 1:

                sep_retry = "\t" if sep == "," else ","

                try:
                    self.data["protocol"] = pd.read_csv(protocol_filename, sep=sep_retry, encoding="utf-8-sig")
                except UnicodeDecodeError:
                    self.data["protocol"] = pd.read_csv(protocol_filename, sep=sep_retry, encoding="latin1")

                self.data["protocol"].columns = self.data["protocol"].columns.str.strip()

            missing_columns = []

            mandatory_column = next(
                (col for col in ["Protocol Accession", "PROTOCOL_ACCESSION"]
                if col in self.data["protocol"].columns),
                None
            )

            if not mandatory_column:
                missing_columns.append("'Protocol Accession' or 'PROTOCOL_ACCESSION'")

            mandatory_column2 = next(
                (col for col in ["Name", "NAME"]
                if col in self.data["protocol"].columns),
                None
            )

            if not mandatory_column2:
                missing_columns.append("'Name' or 'NAME'")

            if missing_columns:
                self.objects["error_message_protocol_files"].show_hide_element(display="")
                self.log(
                    message=f"Invalid planned visits file. Columns found: {list(self.data['protocol'].columns)}",
                    level="error", flush=True
                )
                raise ValueError(
                    f"Planned visits file must contain: {', and '.join(missing_columns)}"
                )

            rename_map = {
                "Protocol Accession": "PROTOCOL_ACCESSION",
                "Name": "NAME",
                "Description": "DESCRIPTION",
                "File Name": "FILE_NAME",
                "Original File Name": "ORIGINAL_FILE_NAME",
                "Type": "TYPE",
                "Workspace ID": "WORKSPACE_ID"
            }
            rename_map = {k: v for k, v in rename_map.items() if k in self.data["protocol"].columns}

            if rename_map:
                self.data["protocol"].rename(columns=rename_map, inplace=True)

            protocol_names = self.get_protocols(nameonly=True, returnType="list")
            self.objects["dropdown_protocol_list"].set_options(protocol_names)
            self.objects["error_message_protocol_files"].show_hide_element(display="none")
            self.objects["box_protocol_list"].show_hide_element(display="block")

            self.log("✅ ImmPort protocol file successfully uploaded and validated.", level="info", flush=True)

        except Exception as e:
            self.objects["error_message_protocol_files"].show_hide_element(display="")
            self.objects["box_protocol_list"].show_hide_element(display="none")

            self.log(
                message=f"Error loading protocol file: {str(e)}",
                level="error", flush=True
            )
            self.flush_log()

    def load_data_dictionary(self,gui):

        self.objects["button_filechooser_data_dictionary_load"].button_change(button=self.objects["button_filechooser_data_dictionary_load"], style='warning', text='Loading',tooltip='The data dictionary file is being loaded',disabled=False, icon='spinner')

        self.config["data_dictionary"] = {
            "filename": self.objects["filechooser_data_dictionary"].get_filename(),
            "filedir": self.objects["filechooser_data_dictionary"].get_dir(),
            "filepath": self.objects["filechooser_data_dictionary"].get_filepath(),
        }

        try:
            self.dictionary = rc.parseDataDictionary(self.config['data_dictionary']['filepath'], self)
            self.objects["button_filechooser_data_dictionary_load"].button_change(button=self.objects["button_filechooser_data_dictionary_load"], style='success', text='Dictionary Loaded',tooltip='The dictionary file has been loaded',disabled=False, icon='')
            self.log(message="✅ Data dictionary successfully uploaded and validated", level="info", flush=True)

            return

        except NotImplementedError as e:
            pass
        
        except Exception as e:
            print(e)
            print(type(e))
            print(e.__dict__)
            self.log(message=f"Error loading data dictionary: {e}", level="error", flush=True)
            
        self.objects["button_filechooser_data_dictionary_load"].button_change(button=self.objects["button_filechooser_data_dictionary_load"], style='danger', text='Load Failed',tooltip='Something went wrong while loading the Data Dictionary',disabled=False, icon='')
        
    def get_study_file_attribute(self, filename, attribute):

        if attribute.upper() not in list(self.data["study_files"].columns):
            raise NotImplementedError(f"Attribute {attribute} not found in study file { list(self.data['study_files'].columns())}")
        
        return self.data["study_files"][self.data["study_files"]["FILE_NAME"]==filename][attribute].values[0]
    
    def generate_tab_study_files(self):

        self.objects["filechooser_study_file_directory"] = File_Chooser(name="filechooser_study_file_directory", title='<b><span style="font-size:18px;">📁 Select the study files directory</span></b>', tooltip='Load the study files directory',multiple=False,filter_pattern=['*'], style=dict(description_width='initial'),show_only_dirs=True)
        self.objects["button_filechooser_study_file_directory_load"] = self.objects["filechooser_study_file_directory"].add_load_button(description="Load study files directory", tooltip="Load the study files directory", callback=self.load_study_files)
        self.objects["html_data_dictionary_tables"] = HTML(html_text='',description='<b><span style="font-size:18px;">Tables Listed in Dictionary:</span></b>')
        
        self.objects["tables_section"] = widgets.VBox([
            self.objects["html_data_dictionary_tables"].get()
        ])

        self.objects["tables_section"].layout.display = 'none'

        self.objects["tab_row_study_files_filechooser"] = widgets.HBox([self.objects["filechooser_study_file_directory"].get(), self.objects["button_filechooser_study_file_directory_load"].get()])

        self.objects["box_study_files_table"] = VBox(name="box_study_files_table", layout=widgets.Layout(width="100%"))

        self.objects["reset_tab3_button"] = Button(text="Reset Tab", tooltip="Reset all inputs in Tab 3", style="warning", callback=self.reset_tab3, width="140px", icon="trash")

        self.objects["help_button_3"] = widgets.Button(description='Help', tooltip='Click for help', icon='question-circle')

        self.objects["help_button_3"].style.button_color = '#F7F6BB'

        self.objects["help_text_3"] = widgets.HTML(
            value=f"""
            <div style='color: black; font-family: Arial, sans-serif; font-size: 14px;
                        padding: 10px; border: 1px solid #ccc; background-color: #f9f9f9;
                        border-radius: 5px;'>
                <h2 style='text-align: center; font-weight: bold; margin: 5px 0;'>Folder Upload</h2>

                <b>Select the study files directory:</b> Choose the directory/folder that contains the study files in TXT or CSV format.
                In ImmPort, this is the 'StudyFiles' folder. <br>
             
                <h2 style='text-align: center; font-weight: bold; margin: 5px 0;'>Table Completion</h2>   

                <b>Filename:</b> The name of the file in the directory. 
                The file should be specified in the 'FILE_NAME' field from the ImmPort study_file.txt. <br>

                <b>Description:</b> The corresponding 'DESCRIPTION' from the ImmPort study_file.txt. 
                If this field is empty, the exact study file name is not in study_file.txt. 
                This field needs to be filled in to create a template. <br>

                <b>Table Code:</b> Choose the corresponding identifier. This is from the 'Table Name' field of the data dictionary that corresponds to the study file. 
                This field is mandatory.<br>

                <b>Default Visit:</b> Choose the visit type. 
                This is from the 'NAME' field in the ImmPort planned_visit.txt. 
                This should be selected if the visit is not specified in the data dictionary or study file. 
                This field is not mandatory, although it should be used when the study file contains missing planned visits. <br>

                <b>Template:</b> Choose whether the created template should be <i>Lab Test</i> or <i>Assessment</i>. This field is mandatory. <br>

                <b>Assessment Name:</b> If you chose <i>Assessment</i>, specify the name in the textbox. This field is not mandatory, but highly recommended. <br>

                <b>Protocol:</b> If you chose <i>Lab Test</i>,  specify the protocol. 
                This is from the 'NAME' field in the ImmPort protocol.txt.  
                This field is mandatory. <br>

                <b>Name Reported:</b> If you chose <i>Lab Test</i>,  specify the name that best describes the study file. This field is mandatory.<br>

                <b>Type:</b> If you chose <i>Lab Test</i>, specify the sample type that best describes the study file. This field is mandatory. <br>

                <b>Subtype:</b> If the selected Type is 'Other', this textbox can be filled in with a more specific subtype.
                This field is not mandatory, but recommended when the Type is 'Other'. <br>

                <b>Study Time T0 Event:</b> If you chose <i>Lab Test</i>, specify the time 0 event — i.e., what the Day 0 event is. This field is mandatory. <br>

                <b>Study Time T0 Event Specify:</b> If the selected Study Time T0 Event is 'Other', this textbox can be filled in with a more specific study time T0 event.
                This field is not mandatory, but recommended when the Study Time T0 Event is 'Other'.<br>

                <h2 style='text-align: center; font-weight: bold; margin: 5px 0;'>Template Creation</h2>   

                <b>Generate Filled Templates:</b> When the table is completed, click this button above the table to create the filled templates.<br>

                <h2 style='text-align: center; font-weight: bold; margin: 5px 0;'>Reset</h2>   

                <b>Reset Tab:</b> This button will reset everything in the '3. Study Files' tab. <br>

                <h2 style='text-align: center; font-weight: bold; margin: 5px 0;'>Additional Information</h2>
                        <a title='Information on study files' 
                            href='{documentation_base_url}/documentation/Preparing-and-Preprocessing-Files.md#gathering-study-files' 
                            style='font-size: 16px; text-decoration: none; color: #0077b6;'>
                            <b>Click for more information on how to gather study files</b>
                        </a> <br>

                        <a title='Information on study files in the app' 
                            href='{documentation_base_url}/documentation/Using-the-Application.md#uploading-study-files' 
                            style='font-size: 16px; text-decoration: none; color: #0077b6;'>
                            <b>Click for more information on how to upload study files</b>
                        </a>

            </div>
            """,
            layout={'width': '600px', 'height': 'auto'}
        )

        self.objects["help_text_3_box"] = widgets.VBox([self.objects["help_text_3"]])
        self.objects["help_text_3_box"].layout.display = 'none' 

        def toggle_help_text_3(b):

            if self.objects["help_text_3_box"].layout.display == 'none':
                self.objects["help_text_3_box"].layout.display = 'block'  
            else:
                self.objects["help_text_3_box"].layout.display = 'none'   

        self.objects["help_button_3"].on_click(toggle_help_text_3)

        self.objects["help_section_3"] = widgets.HBox([
            self.objects["help_button_3"],
            self.objects["help_text_3_box"]
        ])

        self.objects["bottom_buttons_3"] = widgets.HBox([
            self.objects["reset_tab3_button"].get(),
            self.objects["help_section_3"]
        ])

        spacer = widgets.HTML(value="<div style='height: 10px;'></div>")

        self.objects["tab3_layout"] = widgets.VBox([
            spacer,
            self.objects["tab_row_study_files_filechooser"], 
            spacer, 
            self.objects["tables_section"], 
            spacer,
            self.objects["box_study_files_table"].get(), 
            spacer,
            self.objects["bottom_buttons_3"],
            spacer
            ])
        
        return self.objects["tab3_layout"] 
    
    def generate_zip_file(self, fh_zip, files=[]):

        for file in files:
            fh_zip.write(file, os.path.basename(file))

        return

    def generate_filled_template_files(self, b):

        if not hasattr(self, 'table_code_widgets'):
            self.table_code_widgets = {}

        if not hasattr(self, 'template_widgets'):
            self.template_widgets = {}

        if not hasattr(self, 'assessment_name_widgets'):
            self.assessment_name_widgets = {}

        if not hasattr(self, 'default_visit_widgets'):
            self.default_visit_widgets = {}

        if not hasattr(self, 'protocol_widgets'):
            self.protocol_widgets = {}

        if not hasattr(self, 'name_reported_widgets'):
            self.name_reported_widgets = {}

        if not hasattr(self, 'type_widgets'):
            self.type_widgets = {}

        if not hasattr(self, 'subtype_widgets'):
            self.subtype_widgets = {}

        if not hasattr(self, 'study_time_T0_widgets'):
            self.study_time_T0_widgets = {}

        if not hasattr(self, 'study_time_T0_specify_widgets'):
            self.study_time_T0_specify_widgets = {}

        for index in self.data["file_list_df"].index:

            if index in self.table_code_widgets:
                self.data["file_list_df"].at[index, "Table Code"] = self.table_code_widgets[index].value

            if index in self.template_widgets:
                self.data["file_list_df"].at[index, "Template"] = self.template_widgets[index].value

            if index in self.assessment_name_widgets:
                self.data["file_list_df"].at[index, "Assessment Name"] = self.assessment_name_widgets[index].value

            if index in self.default_visit_widgets:
                self.data["file_list_df"].at[index, "Default Visit"] = self.default_visit_widgets[index].value

            if index in self.protocol_widgets:
                self.data["file_list_df"].at[index, "Protocol"] = self.protocol_widgets[index].value

            if index in self.name_reported_widgets:
                self.data["file_list_df"].at[index, "Name Reported"] = self.name_reported_widgets[index].value

            if index in self.type_widgets:
                self.data["file_list_df"].at[index, "Type"] = self.type_widgets[index].value

            if index in self.subtype_widgets:
                self.data["file_list_df"].at[index, "Subtype"] = self.subtype_widgets[index].value

            if index in self.study_time_T0_widgets:
                self.data["file_list_df"].at[index, "Study Time T0 Event"] = self.study_time_T0_widgets[index].value

            if index in self.study_time_T0_specify_widgets:
                self.data["file_list_df"].at[index, "Study Time T0 Event Specify"] = self.study_time_T0_specify_widgets[index].value
    
    
        my_assessments = {}
        my_labtests = {}

        study_id = self.get_study_id()

        study_files_dir = self.objects["filechooser_study_file_directory"].get_filepath()

        parent_dir = os.path.dirname(study_files_dir)
        parent_dir = os.path.dirname(parent_dir)

        todays_date = pd.to_datetime('today').strftime('%Y-%m-%d')
        study_id_todays_date = study_id + "-" + todays_date
        results_folder = os.path.join(parent_dir, "results", study_id_todays_date)

        if not os.path.exists(results_folder):
            os.makedirs(results_folder, exist_ok=True)

        self.objects["button_generate_files"].button_change(
            button=self.objects["button_generate_files"], 
            style='warning', 
            text='Generating...', 
            tooltip='The files are being generated. This could take a few minutes', 
            disabled=False, 
            icon='spinner'
        )

        errors_occurred = False

        for index, study_file_row in self.data['file_list_df'].iterrows():
            table_code = str(study_file_row["Table Code"]).strip()
            template = str(study_file_row["Template"]).strip()

            name_reported = str(study_file_row["Name Reported"]).strip() 

            labtest_type = str(study_file_row["Type"]).strip() 
            labtest_subtype = str(study_file_row["Subtype"]).strip()

                
            labtest_studytimeT0 = str(study_file_row["Study Time T0 Event"]).strip() 
            labtest_studytimeT0specify = str(study_file_row["Study Time T0 Event Specify"]).strip()

            if table_code not in ['--Select--', ''] and template == '--Select--':
                self.log(
                    message=f"Error in row {index+1}: A 'Template' must be selected for Table Code '{table_code}'", 
                    level='error', 
                    flush=True
                )
                self.flush_log()
                errors_occurred = True

            if template == 'Lab Test' and name_reported == '--Select--' and labtest_type != '--Select--':
                self.log(
                    message=f"Error in row {index+1}: A 'Name Reported' must be selected for the '{template}' template", 
                    level='error', 
                    flush=True
                )
                self.flush_log()
                errors_occurred = True        

            if template == 'Lab Test' and name_reported != '--Select--' and labtest_type == '--Select--':
                self.log(
                    message=f"Error in row {index+1}: A 'Type' must be selected for the '{template}' template", 
                    level='error', 
                    flush=True
                )
                self.flush_log()
                errors_occurred = True        

            if template == 'Lab Test' and name_reported == '--Select--' and labtest_type == '--Select--':
                self.log(
                    message=f"Error in row {index+1}: A 'Type' and a 'Name Reported' must be selected for the '{template}' template", 
                    level='error', 
                    flush=True
                )
                self.flush_log()
                errors_occurred = True   
            
            if template == 'Lab Test' and labtest_type == 'Other' and labtest_subtype == '':
                self.log(
                    message=f"Error in row {index+1}: A 'Subtype' must be included if 'Other' is chosen as 'Type'", 
                    level='error', 
                    flush=True
                )
                self.flush_log()
                errors_occurred = True 

            if template == 'Lab Test' and labtest_studytimeT0 == '--Select--':
                self.log(
                    message=f"Error in row {index+1}: A 'Study Time T0 Event' must be selected for the '{template}' template", 
                    level='error', 
                    flush=True
                )
                self.flush_log()
                errors_occurred = True          

            if template == 'Lab Test' and labtest_studytimeT0 == 'Other' and labtest_studytimeT0specify == '':
                self.log(
                    message=f"Error in row {index+1}: A 'Study Time T0 Event Specify' must be included if 'Other' is chosen as 'Study Time T0 Event'", 
                    level='error', 
                    flush=True
                )
                self.flush_log()
                errors_occurred = True   

            if template == "Assessment" and table_code not in ['--Select--', '']:
                try:
                    filename = study_file_row.to_dict().get("Filename")

                    self.objects["button_generate_files"].button_change(
                        button=self.objects["button_generate_files"], 
                        style='warning', 
                        text=f'Generating... {table_code}', 
                        tooltip='The files are being generated. This could take a few minutes', 
                        disabled=False, 
                        icon='spinner'
                    )

                    assessment_obj = sf.Assessment()
                    if not isinstance(assessment_obj, sf.Assessment):
                        raise TypeError(f"Expected Assessment object, got {type(assessment_obj)}")

                    assessment_obj.process_study_file(
                        study_file_info=study_file_row.to_dict(), 
                        study_file_directory=self.objects["filechooser_study_file_directory"].get_filepath(),
                        data_dictionary=self.dictionary,
                        planned_visits=self.data["planned_visit"],
                        study_id=study_id,
                        name_reported=self.get_study_file_attribute(filename, "DESCRIPTION"),
                    )

                    if not callable(getattr(assessment_obj, "export_to_txt", None)):
                        raise AttributeError(f"Assessment object has no method export_to_txt")

                    assessment_obj.export_to_txt(filename=f"{results_folder}/{study_id}_{table_code}_assessment.txt")
 
                    my_assessments[table_code] = assessment_obj

                except Exception as err:
                    errors_occurred = True
                    self.log(message=f"❌ Error processing {table_code} - {err}", level='error', flush=True)
   
            if template == "Assessment" and table_code not in ['--Select--', '']:
                try:
                    filename = study_file_row.to_dict().get("Filename")

                    self.objects["button_generate_files"].button_change(
                        button=self.objects["button_generate_files"], 
                        style='warning', 
                        text=f'Generating... {table_code}', 
                        tooltip='The files are being generated. This could take a few minutes', 
                        disabled=False, 
                        icon='spinner'
                    )

                    assessment_obj = sf.Assessment()

                    returned_values = assessment_obj.process_study_file(
                        study_file_info=study_file_row.to_dict(), 
                        study_file_directory=self.objects["filechooser_study_file_directory"].get_filepath(),
                        data_dictionary=self.dictionary,
                        planned_visits=self.data["planned_visit"],
                        study_id=study_id,
                        name_reported=self.get_study_file_attribute(filename, "DESCRIPTION"),
                    )

                    assessment_obj.export_to_txt(filename=f"{results_folder}/{study_id}_{table_code}_assessment.txt")

                    my_assessments[table_code] = assessment_obj

                except Exception as err:
                    errors_occurred = True
                    self.log(message=f"❌ Error processing {table_code} - {err}", level='error', flush=True)

                        
            if template == "Lab Test" and table_code not in ['--Select--', '']:
                try:
                    filename = study_file_row.to_dict().get("Filename")

                    self.objects["button_generate_files"].button_change(
                        button=self.objects["button_generate_files"], 
                        style='warning', 
                        text=f'Generating... {table_code}', 
                        tooltip='The files are being generated. This could take a few minutes', 
                        disabled=False, 
                        icon='spinner'
                    )

                    my_labtests[table_code] = sf.labTests()

                    protocols_df = self.get_protocols(nameonly=False, returnType="df")

                    my_labtests[table_code].process_study_file(
                        study_file_info=study_file_row.to_dict(), 
                        study_file_directory=self.objects["filechooser_study_file_directory"].get_filepath(),
                        data_dictionary=self.dictionary,
                        planned_visits=self.data["planned_visit"],
                        study_id=study_id,
                        protocols_df = protocols_df,
                        name_reported=self.get_study_file_attribute(filename, "DESCRIPTION"),
                    )

                    my_labtests[table_code].export_to_txt(filename=f"{results_folder}/{study_id}_{table_code}_labTest.txt")

                except Exception as err:
                    errors_occurred = True
                    self.log(message=f"❌ Error processing {table_code} - {err}", level='error', flush=True)

        if errors_occurred:
            self.log(message="❌ Some files failed to generate.", level='error', flush=True)
            self.objects["button_generate_files"].button_change(
                button=self.objects["button_generate_files"], 
                style='danger', 
                text='Error: Some Files Failed to Generate. Click to Retry.', 
                tooltip='An error occurred during file generation. See log for more details.', 
                disabled=False, 
                icon='warning'
            )
        else:
            self.log(message="✅ All files successfully generated.", level='info', flush=True)
            self.log(message=f"📂 Files are in {results_folder}", level='info', flush=True)
            self.objects["button_generate_files"].button_change(
                button=self.objects["button_generate_files"], 
                style='success', 
                text='Files Generated - Click to Re-Generate', 
                tooltip='Files have been generated in the Results folder. Click to re-generate files.', 
                disabled=False, 
                icon='check'
            )

    def generate_console(self):

        if "output_logger" not in self.loggers:
            self.loggers["output_logger"] = Log_Output(name="output_logger", level=logging.INFO)

        self.main_logger = self.loggers["output_logger"]

        if "console" not in self.loggers:
            self.loggers['console'] = Log_Output(name="console", level=logging.ERROR, max_height="100px")

            self.objects["button_clear_console"] = self.loggers["console"].add_clear_button(
                description="Clear Console",
                tooltip="Clear Console Logger",
                width="120px"
            )
            self.objects["button_clear_console"].show_hide_element(display="none")

        self.loggers['output_logger'].logger.addHandler(self.loggers['console'].log_viewer)

    def generate_tab_logging(self):

        if "output_logger_instance" not in self.objects:
            self.objects["output_logger_instance"] = self.loggers["output_logger"]

        output_logger = self.objects["output_logger_instance"]

        if "button_clear_main_logger" not in self.objects:
            self.objects["button_clear_main_logger"] = output_logger.add_clear_button(
                description="Clear Log",
                tooltip="Clear the main logger",
                width="140px"
            )

        spacer = widgets.HTML(value="<div style='height: 10px;'></div>")

        if "logging_tab" not in self.objects:
            self.objects["logging_tab"] = widgets.VBox([
                output_logger.widget,
                self.objects["button_clear_main_logger"].widget,
                spacer
            ])

        output_logger.replay()

        return self.objects["logging_tab"]
    
    def load_study_files(self, b): 

            missing_files = []

            if not hasattr(self, "dictionary") or not self.dictionary or "tables" not in self.dictionary:
                missing_files.append("⚠️ Please upload a data dictionary before loading study files.")
            if "study_files" not in self.data or self.data["study_files"] is None:
                missing_files.append("⚠️ Please upload the ImmPort study file before loading study files.")
            if "planned_visit" not in self.data or self.data["planned_visit"] is None:
                missing_files.append("⚠️ Please upload the ImmPort planned visits file before loading study files.")
            if "protocol" not in self.data or self.data["protocol"] is None:
                missing_files.append("⚠️ Please upload the ImmPort protocol file before loading study files.")

            if missing_files:
                for msg in missing_files:
                    self.log(message=msg, level="error", flush=True)

                if "button_filechooser_study_file_directory_load" in self.objects:
                    self.objects["button_filechooser_study_file_directory_load"].button_change(
                        button=self.objects["button_filechooser_study_file_directory_load"],
                        style='danger',
                        text='Load Failed',
                        tooltip='Cannot load study files — missing required data dictionary or ImmPort file(s)',
                        disabled=False,
                        icon='times'  
                    )

                return  
    
            if "box_study_files_table" not in self.objects:
                self.objects["box_study_files_table"] = VBox(name="box_study_files_table")

            self.objects["box_study_files_table"].toggle_display()  

            self.objects["button_filechooser_study_file_directory_load"].button_change(
                button=self.objects["button_filechooser_study_file_directory_load"], 
                style='warning', 
                text='Loading Study Files...',
                tooltip='The Study files are loading',
                disabled=False, 
                icon='spinner'
            )

            self.objects["html_study_files_display_text"] = widgets.HTML(
                value='<p style="font-size:18px;">Generating Study File Table...</p>'
            )

            self.objects["box_study_files_table"].set_children([self.objects["html_study_files_display_text"]])

            included_extensions = ['txt','csv', 'tsv']

            if os.path.isdir(self.objects["filechooser_study_file_directory"].get_dir()):
                try:
                    self.log(message='Loading files in study file directory', level='debug', flush=True)
                    study_files = [f for f in os.listdir(self.objects["filechooser_study_file_directory"].get_dir()) 
                                if any(f.endswith(ext) for ext in included_extensions)]
                    study_files.sort()

                    required_columns = [
                        "Filename", "Description", "Table Code", "Assessment Name", 
                        "Template", "Default Visit", "Protocol", "Name Reported",
                        "Type", "Subtype", "Study Time T0 Event", "Study Time T0 Event Specify"
                    ]
                    
                    self.data["file_list_df"] = pd.DataFrame({"Filename": study_files})

                    for col in required_columns:
                        if col not in self.data["file_list_df"].columns:
                            self.data["file_list_df"][col] = ""
                
                    table_code_options = self.clean_options(self.dictionary["tables"].keys()) \
                        if hasattr(self, 'dictionary') and 'tables' in self.dictionary else []

                    visit_options = self.clean_options(
                        self.get_planned_visits(nameonly=True, returnType="list")
                    ) if "planned_visit" in self.data else []
                   
                    template_options = get_immport_template_names()
                    
                    protocol_options = self.clean_options(
                        self.get_protocols(nameonly=True, returnType="list")
                    ) if "protocol" in self.data else []
                                        
                    self.data["file_list_df"]["Table Code"] = pd.Categorical(
                        self.data["file_list_df"]["Table Code"],
                        categories=table_code_options,
                        ordered=True
                    )
                    
                    self.data["file_list_df"]["Template"] = pd.Categorical(
                        self.data["file_list_df"]["Template"],
                        categories=template_options,
                        ordered=True
                    )
                    
                    self.data["file_list_df"]["Default Visit"] = pd.Categorical(
                        self.data["file_list_df"]["Default Visit"],
                        categories=visit_options,
                        ordered=True
                    )
                    
                    self.data["file_list_df"]["Protocol"] = pd.Categorical(
                        self.data["file_list_df"]["Protocol"],
                        categories=protocol_options,
                        ordered=True
                    )

                    if "study_files" in self.data and "FILE_NAME" in self.data["study_files"] and "DESCRIPTION" in self.data["study_files"]:
                        merged_df = self.data["file_list_df"].merge(
                            self.data["study_files"][["FILE_NAME", "DESCRIPTION"]],
                            left_on="Filename",
                            right_on="FILE_NAME",
                            how="left"
                        )

                        if "Description" in merged_df.columns:
                            merged_df.drop(columns=["Description"], inplace=True)

                        merged_df.rename(columns={"DESCRIPTION": "Description"}, inplace=True)

                        for col in ["FILE_NAME", "DESCRIPTION"]:
                            if col in merged_df.columns:
                                merged_df.drop(columns=[col], inplace=True)

                        self.data["file_list_df"] = merged_df

                    column_widths = [
                        "200px",  # Filename
                        "300px",  # Description
                        "250px",  # Table Code
                        "250px",  # Assessment Name
                        "250px",  # Template
                        "200px",  # Default Visit
                        "200px",  # Protocol
                        "250px",  # Name Reported
                        "200px",  # Type
                        "200px",  # Subtype
                        "250px",  # Study Time T0 Event
                        "350px",  # Study Time T0 Event Specify 
                    ]

                    display_columns = self.data["file_list_df"].columns.tolist()

                    if len(display_columns) != len(column_widths):
                        raise ValueError("Mismatch between the number of columns and column widths.")

                    column_widths = ["50px"] + column_widths 
        
                    if len(column_widths) < len(display_columns):
                        column_widths.extend(["150px"] * (len(display_columns) - len(column_widths)))
                    elif len(column_widths) > len(display_columns):
                        column_widths = column_widths[:len(display_columns)]

                    bottom_header_row = {col: col for col in required_columns}
                    bottom_header_row["_is_bottom_header"] = True
                    self.data["file_list_df"]["_is_bottom_header"] = False
                    self.data["file_list_df"] = pd.concat(
                        [self.data["file_list_df"], pd.DataFrame([bottom_header_row])],
                        ignore_index=True
                    )

                    self.objects["study_file_table"] = self.generate_df_table(
                        column_widths=column_widths,
                        readonly=["Filename", "Description"]
                    )

                    self.objects["button_generate_files"] = Button(
                        text="Generate Filled Templates", 
                        tooltip='Generate filled ImmPort Templates for upload into ImmPort', 
                        callback=self.generate_filled_template_files, 
                        width="500px", 
                        margin="auto"
                    )

                    self.objects["box_study_files_table"].set_children([
                        self.objects["button_generate_files"].get(),
                        self.objects["study_file_table"]
                    ])

                    temp = list(self.objects["box_study_files_table"].widget.children)  
                    self.objects["box_study_files_table"].widget.children = []  
                    self.objects["box_study_files_table"].widget.children = temp  

                    self.objects["tab3_layout"].children = [
                        self.objects["tab_row_study_files_filechooser"],  
                        self.objects["box_study_files_table"].get(),  
                        self.objects["bottom_buttons_3"]
                    ]

                    self.objects["box_study_files_table"].toggle_display()

                    self.objects["button_filechooser_study_file_directory_load"].button_change(
                        button=self.objects["button_filechooser_study_file_directory_load"], 
                        style='success', 
                        text='Study Files Loaded',
                        tooltip='The Study files have been loaded',
                        disabled=False, 
                        icon=''
                    )

                    self.log("✅ Study specific files successfully uploaded and validated.", level="info", flush=True)

                except Exception as e:
                    error = widgets.HTML(value='<b>Error:</b> ' + str(e))
                    self.objects["box_study_files_table"].set_children([error])
                    self.log(message="Error processing study files: "+str(e), level='error', flush=True)
                    raise Exception("Error loading study files: {}".format(e))
            else:
                self.log(message='Study File Directory is not a directory', level='error', flush=True)

            return

    def set_study_id_from_textfield(self,value):

        if value.type == 'change':
            self.set_study_id(value["new"])

    def set_study_id(self, study_id):

        if "study" not in self.data:
            self.data["study"]={"STUDY_ACCESSION":[study_id]}
            return
        
        self.data["study"]["STUDY_ACCESSION"]=[study_id]

    def get_study_id(self):

        return self.data["study_files"]["STUDY_ACCESSION"][0]

    def current_template(self):

        try:
            if hasattr(self, 'objects') and 'dropdown_template_type' in self.objects:
                return self.objects['dropdown_template_type'].widget.value
            
            return None
        
        except Exception as e:
            self.log(f"Error getting template: {str(e)}", level="error")

            return None

    def toggle_default_visit_and_template(self, change):

        ind = change.owner.row  
        selected_value = change.new

        if ind in self.default_visit_widgets:
            if selected_value == "--Select--":
                self.default_visit_widgets[ind].layout.display = "none"
            else:
                self.default_visit_widgets[ind].layout.display = None
                for key, value in self.dopdown_style.items():
                    setattr(self.default_visit_widgets[ind].layout, key, value)

        if ind in self.template_widgets:
            if selected_value == "--Select--":
                self.template_widgets[ind].layout.display = "none"
                
                for widget_dict in [
                    self.protocol_widgets,
                    self.name_reported_widgets,
                    self.type_widgets,
                    self.subtype_widgets,
                    self.study_time_T0_widgets,
                    self.study_time_T0_specify_widgets,
                    self.assessment_name_widgets
                ]:
                    
                    if ind in widget_dict:
                        widget_dict[ind].layout.display = "none"
            else:
                self.template_widgets[ind].layout.display = None
                for key, value in self.dopdown_style.items():
                    setattr(self.template_widgets[ind].layout, key, value)

    def toggle_columns(self, change):

        row = change["owner"].row  
        template_value = change["new"]  

        if template_value == "Assessment":

            if row in self.assessment_name_widgets:
                self.assessment_name_widgets[row].layout.display = None
                for key, value in self.dopdown_style.items():
                    setattr(self.assessment_name_widgets[row].layout, key, value)
        elif template_value == "Lab Test":
            for widget_dict in [
                self.protocol_widgets,
                self.name_reported_widgets,
                self.type_widgets,
                self.study_time_T0_widgets
            ]:
                
                if row in widget_dict:
                    widget_dict[row].layout.display = None
                    for key, value in self.dopdown_style.items():
                        setattr(widget_dict[row].layout, key, value)

        if template_value == "Assessment":
            for widget_dict in [
                self.protocol_widgets,
                self.name_reported_widgets,
                self.type_widgets,
                self.subtype_widgets,
                self.study_time_T0_widgets,
                self.study_time_T0_specify_widgets
            ]:
                
                if row in widget_dict:
                    widget_dict[row].layout.display = "none"

        elif template_value == "Lab Test":
            for widget_dict in [
                self.subtype_widgets,
                self.study_time_T0_specify_widgets,
                self.assessment_name_widgets
            ]:
                
                if row in widget_dict:
                    widget_dict[row].layout.display = "none"

        else:  
            for widget_dict in [
                self.protocol_widgets,
                self.name_reported_widgets,
                self.type_widgets,
                self.subtype_widgets,
                self.study_time_T0_widgets,
                self.study_time_T0_specify_widgets,
                self.assessment_name_widgets
            ]:
                if row in widget_dict:
                    widget_dict[row].layout.display = "none"

    def toggle_subtype(self, change):

        row = change["owner"].row  
        type_value = change["new"]  

        if row in self.subtype_widgets:

            if type_value == "Other":
                self.subtype_widgets[row].layout.display = None
                for key, value in self.dopdown_style.items():
                    setattr(self.subtype_widgets[row].layout, key, value)
            else:
                self.subtype_widgets[row].layout.display = "none"

    def toggle_study_time_T0_specify(self, change):

        row = change["owner"].row  
        type_value = change["new"]  

        if row in self.study_time_T0_specify_widgets:

            if type_value == "Other":
                self.study_time_T0_specify_widgets[row].layout.display = None
                for key, value in self.dopdown_style.items():
                    setattr(self.study_time_T0_specify_widgets[row].layout, key, value)
            else:
                self.study_time_T0_specify_widgets[row].layout.display = "none"

    def generate_df_table(self, column_widths=None, readonly=["Filename", "Description"]):

        global box
        schema_extractor = sf.SchemaEnumExtractor()
        
        HEADER_STYLE = {
            'justify_content': 'center',
            'align_items': 'center',
            'height': '55px',
            'width': '100%',
            'margin': 'auto 5px auto 0', 
            'padding': "0", 
            'overflow': 'hidden',
            'text_overflow': 'ellipsis'
        }

        column_widths = [
            "50px",    # Row number
            "300px",   # Filename
            "300px",   # Description
            "220px",   # Table Code 
            "220px",   # Default Visit
            "220px",   # Template
            "220px",   # Assessment Name
            "220px",   # Protocol
            "220px",   # Name Reported
            "220px",   # Type
            "220px",   # Subtype
            "220px",   # Study Time T0 Event
            "220px"    # Study Time T0 Event Specify
        ]
        
        self.table_code_widgets = {}  
        self.default_visit_widgets = {}
        self.template_widgets = {}
        self.assessment_name_widgets = {}
        self.protocol_widgets = {}
        self.name_reported_widgets = {}
        self.type_widgets = {}
        self.subtype_widgets = {}
        self.study_time_T0_widgets = {}
        self.study_time_T0_specify_widgets = {}

        if "file_list_df" not in self.data:
            self.data["file_list_df"] = pd.DataFrame(columns=[
                "Filename", "Description", "Table Code", "Default Visit", 
                "Template", "Assessment Name", "Protocol", "Name Reported", 
                "Type", "Subtype", "Study Time T0 Event", "Study Time T0 Event Specify"
            ])
        else:
            self.data["file_list_df"] = self.data["file_list_df"].copy()
            for col in self.data["file_list_df"].columns:
                if pd.api.types.is_categorical_dtype(self.data["file_list_df"][col]):
                    self.data["file_list_df"][col] = self.data["file_list_df"][col].astype(str)
            self.data["file_list_df"] = self.data["file_list_df"].fillna("")

        required_columns = [
            "Filename", "Description", "Table Code", "Default Visit", 
            "Template", "Assessment Name", "Protocol", "Name Reported", 
            "Type", "Subtype", "Study Time T0 Event", "Study Time T0 Event Specify"
        ]
        for col in required_columns:
            if col not in self.data["file_list_df"].columns:
                self.data["file_list_df"][col] = ""

        dataframe_for_table = self.data["file_list_df"].copy().fillna("")
        display_columns = [""] + required_columns

        if len(column_widths) < len(display_columns):
            column_widths.extend(["150px"] * (len(display_columns) - len(column_widths)))
        elif len(column_widths) > len(display_columns):
            column_widths = column_widths[:len(display_columns)]

        shape = (self.data["file_list_df"].shape[0] + 1, len(display_columns))

        self.grid_body = widgets.GridspecLayout(shape[0], shape[1], grid_gap="0px", padding="0px")

        for idx, title in enumerate(display_columns):
            header_style = {**HEADER_STYLE, 'width': column_widths[idx]}
            
            if title in ["Study Time T0 Event", "Study Time T0 Event Specify"]:
                wrapped_title = title.replace("T0", "<br>T0")
                html_value = f"<div style='font-size:20px; font-weight:bold; text-align:center; align-items: center;  justify-content: center;'>{wrapped_title}</div>"
            else:
                html_value = f"<div style='font-size:20px; font-weight:bold; text-align:center; align-items: center; justify-content: center; padding-top: 15px; white-space:nowrap;'>{title}</div>"
            
            self.grid_body[0, idx] = widgets.HTML(
                value = html_value,
                layout = widgets.Layout(**header_style)
            )

        for df_index in self.data["file_list_df"].index:
            grid_row = df_index + 1  

            is_bottom_header = False
            if "_is_bottom_header" in self.data["file_list_df"].columns:
                is_bottom_header = self.data["file_list_df"].at[df_index, "_is_bottom_header"]

                    
            if df_index != len(self.data["file_list_df"]) - 1:
                self.grid_body[grid_row, 0] = widgets.HTML(
                    f"<span style='font-size:17px; text-align:center; padding-top: 20px;'>{df_index+1}</div>",
                    layout=widgets.Layout(
                        width = column_widths[0],
                        justify_content = "center"
                    )
                )
            else:
                self.grid_body[grid_row, 0] = widgets.HTML(
                    "",  
                    layout=widgets.Layout(
                        width = column_widths[0],
                        justify_content = "center"
                    )
                )

            for col_idx, column_title in enumerate(required_columns, start=1):

                if is_bottom_header:
                    wrapped_title = column_title.replace("T0", "<br>T0")
                    self.grid_body[grid_row, col_idx] = widgets.HTML(
                        value=(
                            f"<div style='font-size:21px; font-weight:bold; "
                            f"text-align:center; line-height:1.4; "
                            f"display:flex; align-items:center; justify-content:center; height:100%;'>"
                            f"{wrapped_title}</div>"
                        ),
                        layout=widgets.Layout(
                            width=column_widths[col_idx],
                            justify_content="center",
                            align_items="center"
                        )
                    )
                    continue

                readonly_bool = column_title in readonly
                cell_value = dataframe_for_table.at[df_index, column_title]
                
                if isinstance(cell_value, pd.Series):
                    cell_value = cell_value.iloc[0] if not cell_value.empty else ""
                
                value = str(cell_value).strip() if pd.notna(cell_value) else ""

                if column_title in ["Filename", "Description"]:
                    self.grid_body[grid_row, col_idx] = widgets.HTML(
                        value = f"<span style='font-size:17px; text-align:center; padding-top: 11px; display:block;'>{value}</span>",
                        layout = widgets.Layout(
                            width = column_widths[col_idx], 
                            justify_content = "center", 
                            align_items = "center"  
                        )
                    )
                    
                elif column_title == "Table Code":
                    description_value = dataframe_for_table.at[df_index, "Description"]

                    if pd.notna(description_value) and str(description_value).strip() != "":
                        table_code_options = self.clean_options(self.dictionary["tables"].keys())
                        initial_value = value if value in table_code_options else "--Select--"
                        table_code_dropdown = widgets.Dropdown(
                            options=table_code_options,
                            value=initial_value,
                            layout=widgets.Layout(**self.dopdown_style),
                            style={'description_width': '0px'}
                        )
                        table_code_dropdown.row = df_index
                        self.grid_body[grid_row, col_idx] = table_code_dropdown
                        self.table_code_widgets[df_index] = table_code_dropdown
                        table_code_dropdown.observe(self.toggle_default_visit_and_template, names="value")
                    else:
                        self.grid_body[grid_row, col_idx] = widgets.HTML(
                            value="",
                            layout=widgets.Layout(width=column_widths[col_idx])
                        )

                elif column_title == "Default Visit":
                    visit_options = self.clean_options(self.get_planned_visits(nameonly=True, returnType="list"))

                    initial_value = value if value in visit_options else "--Select--"

                    default_visit_dropdown = widgets.Dropdown(
                        options = visit_options,
                        value = initial_value,
                        layout = widgets.Layout(**self.hidden_dropdown_style),
                        style = {'description_width': '0px'}
                    )
                    default_visit_dropdown.row = df_index  
                    self.grid_body[grid_row, col_idx] = default_visit_dropdown  
                    self.default_visit_widgets[df_index] = default_visit_dropdown  

                elif column_title == "Template":
                    options = ["--Select--", "Assessment", "Lab Test"]
                    initial_value = value if value in options else "--Select--"

                    template_dropdown = widgets.Dropdown(
                        options = options,
                        value = initial_value,
                        layout = widgets.Layout(**self.hidden_dropdown_style), 
                        style = {'description_width': '0px'}
                    )
                    template_dropdown.row = df_index  
                    self.grid_body[grid_row, col_idx] = template_dropdown  
                    self.template_widgets[df_index] = template_dropdown  
                    template_dropdown.observe(self.toggle_columns, names="value")

                elif column_title == "Assessment Name":
                    assessment_name_text = widgets.Text(
                        value = value,
                        disabled = readonly_bool,
                        layout = widgets.Layout(**self.hidden_textbox_style), 
                    )
                    self.assessment_name_widgets[df_index] = assessment_name_text
                    self.grid_body[grid_row, col_idx] = assessment_name_text

                elif column_title == "Protocol":

                    protocol_options = self.clean_options(self.get_protocols(nameonly=True, returnType="list"))

                    initial_value = value if value in protocol_options else "--Select--"
                
                    protocol_dropdown = widgets.Dropdown(
                        options = protocol_options,
                        value = initial_value,
                        layout = widgets.Layout(**self.hidden_dropdown_style), 
                        style = {'description_width': '0px'}
                    )
                    protocol_dropdown.row = df_index  
                    self.grid_body[grid_row, col_idx] = protocol_dropdown 
                    self.protocol_widgets[df_index] = protocol_dropdown  
                    
                elif column_title == "Name Reported":

                    name_reported_options = self.clean_options(schema_extractor.get_enum("nameReported"))
                
                    name_reported_dropdown = widgets.Dropdown(
                        options = name_reported_options,
                        value = value if value in name_reported_options else name_reported_options[0],
                        layout = widgets.Layout(**self.hidden_dropdown_style), 
                        style = {'description_width': '0px'}
                    )
                    self.grid_body[grid_row, col_idx] = name_reported_dropdown
                    self.name_reported_widgets[df_index] = name_reported_dropdown
                    
                elif column_title == "Type":
                    type_options = self.clean_options(schema_extractor.get_enum("type"))
                    
                    type_dropdown = widgets.Dropdown(
                        options=type_options,
                        value=value if value in type_options else type_options[0],
                        layout = widgets.Layout(**self.hidden_dropdown_style),
                        style={'description_width': '0px'}
                    )
                    type_dropdown.row = df_index  
                    self.type_widgets[df_index] = type_dropdown
                    self.grid_body[grid_row, col_idx] = type_dropdown
                    type_dropdown.observe(self.toggle_subtype, names="value")

                elif column_title == "Subtype":
                    subtype_text = widgets.Text(
                        value = value,
                        layout = widgets.Layout(**self.hidden_textbox_style),
                    )
                    self.grid_body[grid_row, col_idx] = subtype_text
                    self.subtype_widgets[df_index] = subtype_text
                   
                elif column_title == "Study Time T0 Event":
               
                    study_time_options = self.clean_options(schema_extractor.get_enum("studyTimeT0Event"))
                    
                    study_time_dropdown = widgets.Dropdown(
                        options = study_time_options,
                        value = value if value in study_time_options else study_time_options[0],
                        layout = widgets.Layout(**self.hidden_dropdown_style), 
                    )
                    study_time_dropdown.row = df_index  
                    self.study_time_T0_widgets[df_index] = study_time_dropdown
                    self.grid_body[grid_row, col_idx] = study_time_dropdown
                    study_time_dropdown.observe(self.toggle_study_time_T0_specify, names="value")

                elif column_title == "Study Time T0 Event Specify":
                    study_time_specify_text = widgets.Text(
                        value=value,
                        layout = widgets.Layout(**self.hidden_textbox_style), 
                        style={'description_width': 'initial', 'white-space': 'nowrap'}
                    )
                    self.grid_body[grid_row, col_idx] = study_time_specify_text
                    self.study_time_T0_specify_widgets[df_index] = study_time_specify_text
                    
        box_body = widgets.VBox([self.grid_body], layout=widgets.Layout(height="650px", overflow_y="auto"))
        box = widgets.VBox([box_body], layout=widgets.Layout(height="510px"))

        return box

    def load_data_dictionary_columns(self, b):
    
        dictionary_tables = list(self.dictionary['tables'].keys())

        self.objects["button_form_column_confirm"].button_change(button=self.objects["button_form_column_confirm"], style='success', text='Confirmed',tooltip='The form columns have been loaded', disabled=False, icon='')   
        
        if "html_data_dictionary_tables" in self.objects:
            dictionary_tables = list(self.dictionary['tables'].keys())
            self.objects["html_data_dictionary_tables"].set_text(text=f"{', '.join(dictionary_tables)}")

    def generate_tab_data_dictionary(self):

        self.objects["filechooser_data_dictionary"] = File_Chooser(
            name="filechooser_data_dictionary",
            title='<b><span style="font-size:18px;">📁 Select the curated data dictionary</span></b>',
            tooltip='Load a curated data dictionary file',
            multiple=False,
            filter_pattern=['*.csv','*.txt',"*.tsv"],
            style=dict(description_width='initial')
        )
        
        self.objects["filechooser_data_dictionary"].set_onclick(
            self, 
            callback_function=self.on_data_dictionary_selected, 
            callback_data={"gui": self}
        )

        self.objects["dropdown_template_type"] = Dropdown(
            options=['Assessment', 'Lab Test', 'Assessment & Lab Test'],
            value='Assessment & Lab Test',
            description='<b><span style="font-size:18px;">Choose which template(s) to generate from your data</span></b>',
            tooltip="Select the form or forms you plan on generating in '3. Study Files'",
            style={'description_width': 'initial'}
        )

        self.objects["button_filechooser_data_dictionary_load"] = self.objects["filechooser_data_dictionary"].add_load_button(
            description="Load Data Dictionary",
            tooltip="Load a curated data dictionary file",
            callback=self.load_data_dictionary
        )
        
        self.objects["button_form_column_confirm"] = Button(
            text="Confirm Form Columns",
            tooltip='Confirm that the selected column from the data dictionary contains the instrument/CRF/form codes',
            callback=self.load_data_dictionary_columns
        )

        self.objects["reset_tab2_button"] = Button(
            text="Reset Tab",
            tooltip="Reset all inputs in Tab 2",
            style="warning",
            callback=self.reset_tab2,
            width="140px",
            icon="trash"
        )
        
        self.objects["help_button_2"] = widgets.Button(
            description='Help',
            tooltip='Click for help',
            icon='question-circle'
        )
        self.objects["help_button_2"].style.button_color = '#F7F6BB'

        self.objects["help_text_2"] = widgets.HTML(
            value=f"""
            <div style='color: black; font-family: Arial, sans-serif; font-size: 14px;
                        padding: 5px; border: 1px solid #ccc; background-color: #f9f9f9;
                        border-radius: 5px;'>
                <h2 style='text-align: center; font-weight: bold; margin: 5px 0;'>File Upload</h2>

                <b>Select the curated data dictionary:</b> Upload the data dictionary file, 
                which contains information about the specific study files (uploaded in '3. Study Files'). 
                This can be a TXT or CSV file. <br>

                <h2 style='text-align: center; font-weight: bold; margin: 5px 0;'>Template Type</h2>

                <b>Choose which template(s) to generate from your data: </b> Specify whether you plan to generate <i>Lab Test</i>, <i>Assessment</i>, or both templates from your study files. 
                Once you've selected the template type, click "Load Data Dictionary" to proceed. <br>

                <h2 style='text-align: center; font-weight: bold; margin: 5px 0;'>Reset</h2>

                <b>Reset Tab:</b> This button will reset everything in the '2. Data Dictionary' tab. <br>

                <h2 style='text-align: center; font-weight: bold; margin: 5px 0;'>Additional Information</h2>
                        <a title='Information on the data dictionary' 
                            href='{documentation_base_url}/documentation/Preparing-and-Preprocessing-Files.md#curating-the-data-dictionary' 
                            style='font-size: 16px; text-decoration: none; color: #0077b6;'>
                            <b>Click for more information on how to curate the data dictionary</b>
                        </a> <br>

                        <a title='Information on the data dictionary in the app' 
                            href='{documentation_base_url}/documentation/Using-the-Application.md#uploading-the-data-dictionary' 
                            style='font-size: 16px; text-decoration: none; color: #0077b6;'>
                            <b>Click for more information on how to upload the data dictionary</b>
                        </a>
            </div>
            """,
            layout={'width': '600px', 'height': 'auto'}
        )

        self.objects["help_text_2_box"] = widgets.VBox([self.objects["help_text_2"]])
        self.objects["help_text_2_box"].layout.display = 'none'

        def toggle_help_text_2(b):

            if self.objects["help_text_2_box"].layout.display == 'none':
                self.objects["help_text_2_box"].layout.display = 'block'  
            else:
                self.objects["help_text_2_box"].layout.display = 'none'   

        self.objects["help_button_2"].on_click(toggle_help_text_2)

        self.objects["help_section_2"] = widgets.HBox([
            self.objects["help_button_2"],
            self.objects["help_text_2_box"]
        ])

        bottom_buttons_2 = widgets.HBox([
            self.objects["reset_tab2_button"].get(),
            self.objects["help_section_2"]
        ])

        self.objects["tab_row_dd_row"] = widgets.HBox([self.objects["filechooser_data_dictionary"].get()])
        self.objects["tab_row_dd_template_row"] = widgets.HBox([
            self.objects["dropdown_template_type"].get(),
            self.objects["button_filechooser_data_dictionary_load"].get()
        ])
        self.hide_row("tab_row_dd_template_row")  

        spacer = widgets.HTML(value="<div style='height: 10px;'></div>")

        tab = widgets.VBox([
            spacer,
            self.objects["tab_row_dd_row"],
            spacer,
            self.objects["tab_row_dd_template_row"],
            spacer,
            bottom_buttons_2,
            spacer
        ])

        return tab
    
    def on_data_dictionary_selected(self, value, gui=None, fc_name=None):

        if value.description == "Change":

            gui.show_row("tab_row_dd_template_row")

            if "button_filechooser_data_dictionary_load" in gui.objects:
                gui.objects["button_filechooser_data_dictionary_load"].show_hide_element('')
            

    def get_planned_visits(self, nameonly=False, returnType=None):

        if nameonly:
            names = self.data["planned_visit"]["NAME"]

            if returnType == 'list':
                return names.tolist()
            
            return names
        
        return self.data["planned_visit"][["PLANNED_VISIT_ACCESSION","NAME"]]
    
    def get_study_files(self, nameonly=False, returnType=None):

        if nameonly:
            names = self.data["study_files"]["FILE_NAME"]

            if returnType == 'list':
                return names.tolist()
            
            return names
        
        return self.data["study_files"][["FILE_NAME"]]


    def get_protocols(self, nameonly=False, returnType=None):

        if "protocol" not in self.data or self.data["protocol"].empty:
            return [] 
        
        if nameonly:
            names = self.data["protocol"]["NAME"]

            if returnType == 'list':
                return names.tolist()
            
            return names
        
        return self.data["protocol"][["PROTOCOL_ACCESSION","NAME"]]


    def toggle_show_hide(self, value, toggle):

        for (key, element_list) in toggle.items():

            if key == value["new"]:
                for element in element_list:
                    element.show_hide_element('')
            else:
                for element in element_list:
                    element.show_hide_element('none')

    def hide_row(self, row):

        self.objects[row].layout.display = 'none'
        self.objects[row].visible = False
        self.objects[row].disabled = True

    def show_row(self, row):

        self.objects[row].layout.display = ''
        self.objects[row].visible = True
        self.objects[row].disabled = False

    def check_schema_version(self):

        immport_protocol_schema_url = "https://downloads.immport.org/data/upload/templates/json-templates/protocols.json"
        try:
            response = urlopen(immport_protocol_schema_url)
            schema_json = json.loads(response.read())
            immport_schemaVersion = schema_json["properties"]['schemaVersion']['enum'][0]
            tool_schemaVersion = sf.ImmPort_Data().schemaVersion

            if  immport_schemaVersion == tool_schemaVersion:
                return True
            else:
                github_issue_url = f"https://github.com/AndorfLab/ImmPort-Curation-Tool/issues/new?template=request-schema-version-update.md&title=%5BSCHEMA%7D%3A+Update+schema+to+version+{immport_schemaVersion}"
                self.log(level='Critical', flush=True, message=f"Current ImmPort version and Tool Version incompatible. \nImmPort is on schema {immport_schemaVersion}. This tool uses version {tool_schemaVersion}. \nClick <a href='{github_issue_url}''>here to create ticket</a>.")
                return False
            
        except Exception as e:
            self.log(level='Critical', flush=True, message='Something went wrong when checking the Schema Versions.')
            print(type(e))
            print(e)
            return False
        
class Tab(GUI_Object):

    def __init__(self, name, contents=None, callback=None):

        self.name = name
        box_layout = widgets.Layout(overflow='scroll hidden')

        if contents is not None:
            if hasattr(contents, "widget"):
                self.widget = widgets.Box(children = [contents.widget], layout=box_layout)
            else:
                self.widget = widgets.Box(children=[contents], layout=box_layout)
        else:
            self.widget =widgets.Box(children=[], layout=box_layout)

class Button(GUI_Object):

    def __init__(self, text, style=None, icon="", tooltip="", state=False, callback=None, display=True, width="auto", margin=""):
        
        super().__init__(
            widgets.Button(
                description=text,
                icon=icon,
                tooltip=tooltip,
                layout=widgets.Layout(width=width, margin=margin),
                disabled = state
            )
        )
        
        if style is None:
            self.widget.style.button_color = "#F5DAD2"
        elif style == 'warning':
            self.widget.style.button_color = '#F7F6BB'
        else: 
            self.widget.button_style = style

        if callback is not None:
            self.widget.on_click(callback)

        if not display:
            self.widget.layout.display='none'

    def set_callback(self, callback):   

        self.widget.on_click(callback)

    def button_change(self,button=None, style=None, text=None, tooltip=None, icon=None, display=None, disabled=None):

        if self.widget is None:
            return

        if style == '':
            self.widget.style.button_color = "#F5DAD2"
        elif style == 'success':
            self.widget.style.button_color = '#6e9790'
        elif style == 'warning':
            self.widget.style.button_color = '#F7F6BB'
        elif style == 'danger':
            self.widget.style.button_color = '#ac8188'
        else:
            self.widget.style.button_color = None
            self.widget.button_style = style

        if text is not None:
            self.widget.description = text

        if tooltip is not None:
            self.widget.tooltip = tooltip

        if icon is not None:
            self.widget.icon = icon

        if disabled is not None:
            self.widget.disabled = disabled

        if display is not None:
            self.widget.layout.display = display

class ToggleButtons(GUI_Object):
    
    def __init__(self, options, value=None, description="", tooltips=[], style=None):

        super().__init__(
            widgets.ToggleButtons(
                options=options,
                value=value,
                description=description,
                tooltips=tooltips,
                layout=widgets.Layout(width="auto"),
                style=style
            )
        )

class TextField(GUI_Object):

    counter = 0

    def __init__(self, **kwargs):

        super().__init__(
            widgets.Text(
                value=kwargs.get("text", ""),
                placeholder=kwargs.get("placeholder", ""),
                description=kwargs.get("description", ""),
                disabled=False
            )
        )

        self.name = kwargs.get("name", "undefined_textfield_" + str(TextField.counter))
        TextField.counter += 1

        if "regex" in kwargs:
            self.widget.observe(self.check_value, names='value')
            self.regex = kwargs["regex"]
            regex_display = self.regex.replace(r"\d", " numbers (0-9)")

            self.helper = widgets.Output()
            
            with self.helper:
                display(widgets.HTML(f"<span style='color:red; font-size: 16px;'>⚠️ Please use a value that matches the format of {regex_display}</span>"))

            self.helper.layout.display = "none"  

    def get(self):

        if hasattr(self, "helper"):
            return widgets.HBox([self.widget, self.helper])  
        
        return self.widget

    @debounce(1) 

    def check_value(self, change):

        if not self.widget.value.strip():  
            self.helper.layout.display = "none"
            return  

        if not re.match(self.regex, change["new"]):
            self.helper.layout.display = "block"  
        else:
            self.helper.layout.display = "none"  

    def reset(self):

        self.widget.value = ""  

        if hasattr(self, "helper"):  
            self.helper.layout.display = "none"  

class File_Chooser(GUI_Object):

    def __init__(self, name, **kwargs):

        super().__init__(
            FileChooser(**kwargs)
        )
        self.name = name

        self.widget.register_callback(self.on_select)
    
    def set_filter(self, filter=[]):
     
        self.widget.filter_pattern = filter

    def set_onclick(self, gui, callback_function, callback_data):

        self.widget.disabled=False
        self.widget._select.on_click(functools.partial(callback_function, **callback_data))

    def set_path(self, path):

        self.widget.selected_path = path
    
    def set_filename(self, filename):

        self.widget.selected_filename = filename
    
    def reset(self, path, filename):
       
       self.widget.reset(path=path, filename=filename)

    def get_filepath(self):

        path = getattr(self.widget, "selected_path", "")
        fname = getattr(self.widget, "selected_filename", "")

        if not path or not fname:
            return None
        
        return os.path.normpath(os.path.join(path, fname))

    def get_dir(self):

        return self.widget.selected_path

    def get_filename(self):

        return self.widget.selected_filename

    def add_load_button(self, description="Load", style=None, icon="", tooltip="Click to Load the file", callback=None):

        button = Button(
            text=description,
            icon=icon,
            tooltip=tooltip,
            style=style,
            callback=callback
        )
        button.show_hide_element('none')
        
        self.load_button = button
    
        return button

    def on_select(self):   
      
        if hasattr(self, "load_button"):
            if len(self.widget._selected_path)>0:
                self.load_button.show_hide_element('')
                self.load_button.widget.button_style='info'
                self.load_button.widget.disabled=False
            else:
                self.load_button.show_hide_element('none')

class Dropdown(GUI_Object):

    def __init__(self, options, value=None, description='', callback=None, tooltip=None, style=dict(description_width='initial')):
     
        super().__init__(
            widgets.Dropdown(
                options=options,
                value=value,
                layout=widgets.Layout(width="auto"),
                description=description,
                style=style,
                tooltip=tooltip
            )
        )
        if callback is not None:
            self.widget.on_transition(callback)
    
    def set_options(self, option_list):

        try:
            self.widget.options = option_list
        except Exception as err:
            self.log(message="Error loading option list",level='info',flush=True)

class HBox(GUI_Object):

    def __init__(self, *args, **kwargs):

        super().__init__(
            widgets.HBox(*args, **kwargs)
        )
    
    def set_children(self, child_list=[]):

        self.widget.children = child_list

class VBox(GUI_Object):

    def __init__(self, *args, **kwargs):

        super().__init__(
            widgets.VBox(*args, **kwargs)
        )
    
    def set_children(self, child_list=[]):

        self.widget.children = child_list

class HTML(GUI_Object):

    def __init__(self, html_text, placeholder_text='', description=''):

        super().__init__(
            widgets.HTML(
                value=html_text,
                placeholder = placeholder_text,
                description = description,
                layout=widgets.Layout(width="auto"),
                style={'description_width': 'initial'}
            )
        )

    def set_text(self, text):

        self.widget.value = text

class Log_Output(GUI_Object):

    fmt = '%(name)s | %(levelname)8s | %(message)s'

    def __init__(self, level=logging.DEBUG, name=__name__, max_height="525px", handlers=[]):

        super().__init__(
            widgets.Output(layout=widgets.Layout(max_height=max_height, overflow_y="auto"))
        )

        self.name = name
        self.logger = logging.getLogger(name)
        self.logger.setLevel(logging.DEBUG)

        self.log_viewer = log_viewer(output=self.widget, name=name, parent=self)
        self.log_viewer.setLevel(level)
        self.logger.addHandler(self.log_viewer)

        for handler in handlers:
            self.logger.addHandler(handler)

        self.log = {
            "debug": self.logger.debug,
            "info": self.logger.info,
            "warning": self.logger.warning,
            "warn": self.logger.warning,
            "error": self.logger.error,
            "critical": self.logger.critical,
        }

        self.log_levels = {
            "critical": 50,
            "error": 40,
            "warning": 30,
            "warn": 30,
            "info": 20,
            "debug": 10,
        }

        self.buffer = []

        self.clear_button = Button(
            text="Clear Log",
            tooltip="Clear the main logger",
            callback=self.clear_output,
            style="",
            icon="trash",
            width="140px"
        )

    def add_clear_button(self, description="Reset Log", tooltip="Clear the main logger", icon="trash", style="", width="auto"):
        
        self.clear_button.text = description
        self.clear_button.tooltip = tooltip
        self.clear_button.icon = icon
        self.clear_button.width = width
        self.clear_button.callback = self.clear_output

        if style == "":
            self.clear_button.widget.style.button_color = '#F7F6BB'
        else:
            self.clear_button.widget.style.button_color = style

        return self.clear_button

    def write(self, message=None, level="info", flush=False):

        if not message:
            return
        
        level = level.lower()
        self.buffer.append((level, message))

        if flush:
            self.flush()

    def flush(self):

        if not self.buffer:
            return None

        with self.widget:
            for level, message in self.buffer:
                if level in self.log:
                    self.log[level](message)

        self.clear_button.show_hide_element(display="")

        highest_level = sorted(self.buffer, key=lambda x: self.log_levels[x[0]], reverse=True)[0]
        level_name = highest_level[0]
        level_count = sum(1 for l, _ in self.buffer if l == level_name)

        self.buffer.clear()

        return (level_name, level_count)

    def replay(self):

        with self.widget:
            for level, message in self.buffer:
                if level in self.log:
                    self.log[level](message)

    def clear_output(self, *args, **kwargs):

        self.buffer.clear()
        self.widget.clear_output()

class OutputWidgetHandler(logging.Handler): 

    def __init__(self, output_widget, *args, **kwargs):

        super(OutputWidgetHandler, self).__init__(*args, **kwargs)
        layout = {
            'width': '100%',
            'height': '550px',
            'border': '1px solid black'
        }
        self.out = output_widget 

    def emit(self, record):

        formatted_record = self.format(record)

        with self.out:
            print(formatted_record)

        return
        
        new_output = {
            'name': 'stdout',
            'output_type': 'stream',
            'text': formatted_record+'\n'
        }
        self.out.outputs = (new_output, ) + self.out.outputs

    def show_logs(self):

        display(self.out)

    def clear_logs(self):

        self.out.clear_output()

immport_data = {'tab_data':{},'config':{}}


def get_immport_template_names():

    return ['--Select--',"Assessment", "Lab Test"]


def update_dataframe_from_table(value,row=None, column=None, column_name=None, dataframe=None):

    if dataframe is None:
        return
    
    dataframe.at[row,column_name]=value['new']

def create_table_widget(dtype=None, value='', readonly=False, dataframe=None, columnName=None):

    if readonly:
        return widgets.Label(value=value)
    elif dtype == "object":
        return widgets.Text(value=value,
            placeholder='',
            disabled=readonly)
    elif dtype == "category":
        option_list = dataframe[columnName].cat.categories.tolist()
 
        if value=='':
            value = '--Select--'

        return widgets.Dropdown(
            options=option_list,
            value=value,
            description='',
            disabled=False,
        )

def on_select_study_tab_file(value, gui=None, fc_name=None):
  
    if value.description == "Change":

        gui.data["planned_visit"] = cf.readFileFromZip(gui.objects[fc_name].widget.selected_path, gui.objects[fc_name].widget.selected_filename, "planned_visit.txt")   
        gui.data["study_files"] = cf.readFileFromZip(gui.objects[fc_name].widget.selected_path, gui.objects[fc_name].widget.selected_filename, "study_file.txt")
        gui.data["protocol"] = cf.readFileFromZip(gui.objects[fc_name].widget.selected_path, gui.objects[fc_name].widget.selected_filename, "protocol.txt")
        visit_names = get_planned_visits(gui.data["planned_visit"],nameonly=True, returnType="list")
        
        if "dropdown_study_visit_list" in gui.objects:

            gui.objects["dropdown_study_visit_list"].set_options(visit_names)

            if "study_visit_list_section" in gui.objects:

                gui.objects["study_visit_list_section"].children = [
                    gui.objects["label_study_visit_list"], 
                    gui.objects["dropdown_study_visit_list"].get()  
                ]

        study_names = get_study_files(gui.data["study_files"],nameonly=True, returnType="list")
        
        if "dropdown_study_files_list" in gui.objects:

            gui.objects["dropdown_study_files_list"].set_options(study_names)

            if "study_files_list_section" in gui.objects:

                gui.objects["study_files_list_section"].children = [
                    gui.objects["label_study_files_list"], 
                    gui.objects["dropdown_study_files_list"].get()  
                ]

        protocol_names = get_protocols(gui.data["protocol"],nameonly=True, returnType="list")
        
        if "dropdown_protocol_list" in gui.objects:

            gui.objects["dropdown_protocol_list"].set_options(protocol_names)

            if "protocol_list_section" in gui.objects:

                gui.objects["protocol_list_section"].children = [
                    gui.objects["label_protocol_list"], 
                    gui.objects["dropdown_protocol_list"].get()  
                ]

def get_planned_visits(planned_visits, nameonly=False, returnType=None):
  
    if nameonly:
        names = planned_visits["NAME"]
        if returnType == 'list':
            return names.tolist()
        return names
    return planned_visits[["PLANNED_VISIT_ACCESSION","NAME"]]

def get_study_files(self, nameonly=False, returnType=None):

    if nameonly:
        names = self.data["study_files"]["FILE_NAME"]

        if returnType == 'list':
            return names.tolist()
        
        return names
    
    return self.data["study_files"][["FILE_NAME"]]

def get_protocols(self, nameonly=False, returnType=None):
    
    if nameonly:
        names = self.data["protocol"]["NAME"]

        if returnType == 'list':
            return names.tolist()
        
        return names
    
    return self.data["protocol"][["PROTOCOL_ACCESSION","NAME"]]

