
import traceback

import pandas as pd
import os
import re

import ImmPortCurationTool.processRedCapFiles as rc
import ImmPortCurationTool.curationFunctions as cf
import ImmPortCurationTool.schemaFunctions as sf

from ImmPortCurationTool.version import VERSION

import zipfile
import ipywidgets as widgets
from ipyfilechooser import FileChooser

import functools
import logging
import asyncio

from urllib.request import urlopen
import json

from IPython.display import display, HTML


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

#TODO potentially move to external file
documentation_base_url = "https://github.com/JoshuaFortriede/ImmPort-Curation-Tool/blob/master"


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
    """ Decorator that will postpone a function's
        execution until after `wait` seconds
        have elapsed since the last time it was invoked. """
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

    def __init__(self, fmt):
        super().__init__()
        self.fmt = fmt
        self.FORMATS = {

            logging.DEBUG: f"{self.format_string('debug')}{self.fmt}",
            logging.INFO: f"{self.format_string('info')}{self.fmt}",
            logging.WARNING: f"{self.format_string('warning')}{self.fmt}",
            logging.ERROR: f"{self.format_string('error')}{self.fmt}",
            logging.CRITICAL: f"{self.format_string('critical')}{self.fmt}",
        }

    def format_string(self,level):
        if level in ["error","warning"]:
            return f"<font color='{self.colors[level]}' style='white-space: pre; font-size=16px; font-family: Consolas; font-weight: bold'>"
        elif level == "critical":
            return f"<font color='white' style='background-color:{self.colors[level]}; white-space: pre; font-size=16px; font-family: Consolas; font-weight: bold'>"

        return f"<font color='{self.colors[level]}' style='white-space: pre; font-size=16px; font-family: Consolas'>"

    def format(self, record):
        log_fmt = self.FORMATS.get(record.levelno)
        formatter = logging.Formatter(log_fmt)
        return formatter.format(record)

class log_viewer(logging.Handler):
    """ Class to redistribute python logging data """
    # fmt = '%(name)s | %(levelname)8s | %(message)s'
    fmt = '%(levelname)-8s | %(message)s'

    def __init__(self, *args, **kwargs):
        # Initialize the Handler
        self.logger_instance = logging.getLogger(kwargs.get("name",__name__))
        logging.Handler.__init__(self, *args)

        # setFormatter function is derived from logging.Handler
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

        """ Overload of logging.Handler method """
        formatted_record = self.format(record)
        print_html2 = HTML(html_text = f"<font color='blue' style='white-space: pre; font-size=16px'>{formatted_record}")

        with self.output:
            display(print_html2.widget)

class GUI_Object():
    """Class to hold GUI object methods"""
    def __init__(self, widget):
        self.widget = widget
        self.data={}
    
    def get(self):
        """Return the widget"""
        return self.widget
    
    def display(self):
        """Display the widget"""
        children=[self.get()]
        if hasattr(self, "loggers") and "console" in self.loggers:
            children.insert(0,widgets.HBox([self.objects["button_clear_console"].get(),self.loggers["console"].get()]))
            # return widgets.VBox([widgets.HBox([self.objects["button_clear_console"].get(),self.loggers["console"].get()]),self.get()])
        # if "footer" in self.objects:
        #     children.insert(0,self.objects['footer'].get())
        if len(children)==1:
            return self.get()
        return widgets.VBox([*children])
    
    def set_observe(self, callback_function, callback_data):
        self.widget.observe(functools.partial(callback_function, **callback_data), names='value')

    def toggle_display(self):
        self.widget.layout.display = "" if self.widget.layout.display == "none" else "none"

    def toggle_state(self):
        """Toggle the widget"""
        self.widget.disabled = not self.widget.disabled

    def set_state(self, state):
        """Set the widget state"""
        self.widget.disabled = state

    def set_attribute(self, attribute, value):
        """Set the widget attribute"""
        if hasattr(self.widget, attribute):
            setattr(self.widget, attribute, value)

    def get_type(self):
        """Return the widget type"""
        return self.widget.__class__.__name__

    def get_module_type(self):
        """Return the module type"""
        return type(self.widget)

    def show_hide_element(self, display):
        """Helper function to show or hide an element

        Args:
            element (widget.*, required): widget element. Defaults to None.
            display (text, optional): ['','none','inline']. Defaults to None.
        """
        if self is None or display is None:
            return
        self.widget.layout.display=display


class GUI(GUI_Object):
    """Main interface class"""
    def __init__(self):
        super().__init__(widgets.Tab(layout=widgets.Layout(min_height="500px")))
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

    def create_logger(self, name="main_logger",level="debug"):  #Not Used
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

    def reset_tab1(self, b):  

        if "filechooser_study_tab_file" in self.objects:
            self.objects["filechooser_study_tab_file"].reset("", "")  

        if "filechooser_planned_visits" in self.objects:
            self.objects["filechooser_planned_visits"].reset("", "")  

        if "filechooser_study_files" in self.objects:
            self.objects["filechooser_study_files"].reset("", "")  

        if "error_message_study_files" in self.objects:
            self.objects["error_message_study_files"].show_hide_element(display="none")

        if "error_message_planned_visits" in self.objects:
            self.objects["error_message_planned_visits"].show_hide_element(display="none")

        if "error_message_study_tab_file" in self.objects:
            self.objects["error_message_study_tab_file"].show_hide_element(display="none")

        if "text_study_id" in self.objects:
            self.objects["text_study_id"].reset()
  
        if "text_workspace_id" in self.objects:
            self.objects["text_workspace_id"].reset()

        if "dropdown_study_visit_list" in self.objects:
            self.objects["dropdown_study_visit_list"].set_options([""]) 
            
        if "toggle_current_immport_study" in self.objects:
            old_value = self.objects["toggle_current_immport_study"].widget.value
            self.objects["toggle_current_immport_study"].widget.value = 0  

        if "toggle_non_tab_files" in self.objects:
            old_value = self.objects["toggle_non_tab_files"].widget.value
            self.objects["toggle_non_tab_files"].widget.value = 0  
    
    def reset_tab2(self, b):  

        if "filechooser_data_dictionary" in self.objects:
            self.objects["filechooser_data_dictionary"].reset("", "")  

        if "dropdown_table_form_column" in self.objects:
            del self.objects["dropdown_table_form_column"]
        if "button_form_column_confirm" in self.objects:
            del self.objects["button_form_column_confirm"]

        self.objects["dropdown_table_form_column"] = Dropdown(
            options=['No selection'], 
            description='<b><span style="font-size:18px;">Select the column that specifies the form/instrument</span></b>', 
            tooltip='Select the column from the data dictionary that contains the form codes', 
            style={'description_width': 'initial'}
        )

        self.objects["button_form_column_confirm"] = Button(
            text="Confirm", 
            tooltip='Confirm that the selected column from the data dictionary contains the instrument/CRF/form codes', 
            callback=self.load_data_dictionary_columns
        )

        if "tab_row_dd_form_row" in self.objects:
            self.objects["tab_row_dd_form_row"].children = []

            self.objects["tab_row_dd_form_row"].children = [
                self.objects["dropdown_table_form_column"].get(),
                self.objects["button_form_column_confirm"].get()
            ]
            self.hide_row("tab_row_dd_form_row")

        self.objects["button_filechooser_data_dictionary_load"] = self.objects["filechooser_data_dictionary"].add_load_button(
            description="Load Data Dictionary",
            tooltip="Load a curated data dictionary file",
            callback=self.load_data_dictionary
        )

        self.objects["tab_row_dd_row"].children = [
            self.objects["filechooser_data_dictionary"].get(), 
            self.objects["button_filechooser_data_dictionary_load"].get()
        ]

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

        if "tables_section" in self.objects:
            self.objects["tables_section"].children = []  
            self.objects["tables_section"].layout.visibility = 'hidden'
 
        spacer = widgets.HTML(value="<div style='height: 10px;'></div>")

        self.objects["tab3_layout"].children = [  
            spacer,
            self.objects["tab_row_study_files_filechooser"], 
            spacer,
         #   self.objects["reset_tab3_button"].get(),
            self.objects["bottom_buttons_3"],
            spacer
        ]

    def generate_gui(self):

        self.objects["title"] = widgets.HTML(value="<h1 style='text-align:center; color:#3E6962; font-size:30px;'>ImmPort Curation Tool</h1>") 

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
            with content_area:
                content_area.clear_output(wait=True)
                display(tab_contents[button.description])

        tab_buttons = []
        for i, title in enumerate(tab_titles):
            button = widgets.Button(
                description=title,
                style={"button_color": tab_colors[i]},  
                layout=widgets.Layout(width="auto",flex="1", height="40px") 
            )
            button.on_click(on_tab_click)
            tab_buttons = tab_buttons + [button]

        button_container = widgets.HBox(tab_buttons, layout=widgets.Layout(
            width="100%",  
            display="flex",
            justify_content="space-between" 
        ))

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

        documentation = [
            {"label":"User Guide","text":"A step-by-step guide on using this tool", "link":"User_Guide.md"},
            {"label":"FAQ","text":"Commonly asked questions", "link":"/documentation/FAQ.md"},
            {"label":"Errors","text":"Common errors and how to solve them", "link":"/documentation/Logging Errors.md"},
            {"label":"Data Dictionary","text":"How to curate the data dictionary", "link":"/documentation/Curated_Data_Dictionary.md"},
            {"label":"Study File","text":"Required format for study files", "link":"/documentation/Study_File_format.md"},
            {"label":"Load ImmPort Files","text":"How to get files from ImmPort for this tool", "link":"/documentation/Load_files_from_immport.md"}
            ]
        
        documentation_header = widgets.HTML(value="""
            <h2 style='color:black; text-align:left; margin-bottom: 2px;'>📄 Documentation Links</h2>
        """)
        
        overview_header = widgets.HTML(value=f"""
            <div style='display: flex; justify-content: space-between; align-items: center; width: 100%;'>
                <h2 style='color:black; margin-bottom: 0px;'>🔍 About this Tool</h2>
                <span style='font-size: 18px; color: black;'> {self.objects["version"].get().value} </span>
            </div>

            <p style='font-size:18px; color:black; margin-top: 0px;'>
                <br>
                The purpose of this tool is to transform data files/tables from a study into ImmPort templates for upload and integration into the ImmPort database
                <br>
                <br>
                <b>1. ImmPort Files:</b> Start the data transformation by uploading study data in the first tab
                <br>
                <br>
                <b>2. Data Dictionary:</b> Next, upload the study data dictionary
                <br>
                <br>
                <b>3. Study Files:</b> Finally, upload the study files folder and choose the files you would like to incorporate into the final template
                <br>
                <br>
                <b>Logging:</b> Progress and error messages appear here
            </p>
        """)

        doc_links = []
        doc_links = doc_links + [
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

        tab_content = widgets.VBox([
            overview_header,
            documentation_header, 
            widgets.VBox(doc_links)
        ], layout=widgets.Layout(padding="1px"))

        return tab_content

    def generate_tab_study_info(self):

        try:

            self.objects["toggle_current_immport_study"] = ToggleButtons(description='<b><span style="font-size:18px;">🔘 Choose initial input type</span></b>', options=[('Download information from ImmPort',0),('Use ImmPort Tab file',1)], value=0, tooltips=['Downloaded from the public area of ImmPort','Downloaded from the private area of ImmPort'], style=dict(description_width='initial',button_width='auto'))

            self.objects["error_message_study_tab_file"] = HTML(html_text="<span style='color: red; font-size: 16px;'>⚠️ Please select a valid ImmPort study Tab ZIP file </span>", description="")
            self.objects["error_message_study_tab_file"].show_hide_element(display="none")  

            self.objects["filechooser_study_tab_file"] = File_Chooser(name="filechooser_study_tab_file", title='<b><span style="font-size:18px;">📁 Select the ImmPort study Tab ZIP file</span></b>', tooltip='Load a study Tab file',multiple=False,filter_pattern=['SDY*-DR*_Tab.zip'], style=dict(description_width='initial'))
            self.objects["filechooser_study_tab_file"].set_onclick(self, callback_function=self.on_select_study_tab_file_with_error_handling, callback_data={"gui":self, "fc_name":"filechooser_study_tab_file"})

            file_chooser_with_error = widgets.HBox([self.objects["filechooser_study_tab_file"].get(), self.objects["error_message_study_tab_file"].get()])

            self.objects["filechooser_planned_visits"] = File_Chooser(name="filechooser_planned_visits", title='<b><span style="font-size:18px;">📁 Select the ImmPort planned visit file</span></b>', tooltip='Load a planned visit file',multiple=False,filter_pattern=['*.csv'], style=dict(description_width='initial'))
            self.objects["filechooser_planned_visits"].set_onclick(self, callback_function=self.load_planned_visit_file, callback_data = {})

            self.objects["error_message_planned_visits"] = HTML(html_text="<span style='color: red; font-size: 16px;'>⚠️ Please select a valid planned visits file </span>", description="")
            self.objects["error_message_planned_visits"].show_hide_element(display="none")  

            self.objects["file_chooser_planned_visits_with_error"] = widgets.HBox([self.objects["filechooser_planned_visits"].get(), self.objects["error_message_planned_visits"].get()])
            
            self.objects["filechooser_study_files"] = File_Chooser(name="filechooser_study_files", title='<b><span style="font-size:18px;">📁 Select the ImmPort study file</span></b>', tooltip='Load a study files file',multiple=False,filter_pattern=['*.csv'], style=dict(description_width='initial'))
            self.objects["filechooser_study_files"].set_onclick(self, callback_function=self.load_study_file, callback_data = {})

            self.objects["error_message_study_files"] = HTML(html_text="<span style='color: red; font-size: 16px;'>⚠️ Please select a valid study files file </span>", description="")
            self.objects["error_message_study_files"].show_hide_element(display="none")

            self.objects["file_chooser_study_files_with_error"] = widgets.HBox([self.objects["filechooser_study_files"].get(), self.objects["error_message_study_files"].get()])

            self.objects["label_study_id"] = widgets.HTML(
                "<b><span style='font-size:18px;'>🆔 Input the study ID</span></b>"
            )

            self.objects["text_study_id"] = TextField(placeholder="SDY9999", regex=r"SDY\d+", layout=widgets.Layout(width="350px"))

            study_id_section = widgets.VBox([
            self.objects["label_study_id"],
            self.objects["text_study_id"].get()
            ])

            self.objects["label_workspace_id"] = widgets.HTML(
                "<b><span style='font-size:18px;'>🆔 Input the workspace ID</span></b>"
            )
            
            self.objects["text_workspace_id"] = TextField(placeholder="9999", regex=r"\d+", layout=widgets.Layout(width="350px", description_width="200px") ) 

            workspace_id_section = widgets.VBox([
            self.objects["label_workspace_id"],
            self.objects["text_workspace_id"].get()
            ])

            self.objects["label_study_visit_list"] = widgets.HTML(
                "<b><span style='font-size:18px;'>🔍 View the loaded study visits</span></b>"
            )
            
            self.objects["dropdown_study_visit_list"] = Dropdown(options=[''], tooltip='View the loaded study visits')

            study_visit_list_section = widgets.VBox([
            self.objects["label_study_visit_list"],
            self.objects["dropdown_study_visit_list"].get()
            ])

            self.objects["text_study_id"].set_observe(callback_function=self.set_study_id_from_textfield, callback_data = {})
            self.objects["text_workspace_id"].set_observe(callback_function=self.set_workspace_id_from_textfield, callback_data = {})

            box_immport_study_yes = VBox(name="box_immport_study_yes")
            box_immport_study_no = VBox(name="box_immport_study_no")

            box_immport_study_yes.toggle_display()

            box_planned_visits = VBox(name='box_planned_visits')
            box_planned_visits.set_children([self.objects['file_chooser_planned_visits_with_error']])

            box_study_files = VBox(name='box_study_files')
            box_study_files.set_children([self.objects['file_chooser_study_files_with_error']])

            self.objects["toggle_non_tab_files"] = ToggleButtons(description='<b><span style="font-size:18px;">Do you want to amend the Tab file with new planned visits and/or study files?</span></b>', options=[('Yes',1),('No',0)], value=0, tooltips=[], style=dict(description_width='initial',button_width='auto'))

            spacer_before_toggle = widgets.HTML(value="<div style='height: 20px;'></div>")

            toggle_with_spacing = widgets.VBox([
                spacer_before_toggle,
                self.objects["toggle_non_tab_files"].get()
            ])

            box_immport_study_yes.set_children([file_chooser_with_error, toggle_with_spacing])

            box_immport_study_no.set_children([workspace_id_section, study_id_section])

            self.objects["reset_tab1_button"] = Button(text="Reset Tab", tooltip="Reset all inputs in Tab 1", style="warning", callback=self.reset_tab1, width="140px", icon="trash")

            self.objects["help_button_1"] = widgets.Button(description='Help', tooltip='Click for help', icon='question-circle')

            self.objects["help_button_1"].style.button_color = '#F7F6BB'

            self.objects["help_text_1"] = widgets.HTML(
                value="""
                <div style='color: black; font-family: Arial, sans-serif; font-size: 14px;
                            padding: 5px; border: 1px solid #ccc; background-color: #f9f9f9;
                            border-radius: 5px;'>
                    <h2 style='text-align: center; font-weight: bold; margin: 5px 0;'>Inputs</h2>
                    <b>Input the workspace ID:</b> This should be a numeric identifier, listed as the 'Workspace ID' in ImmPort. Example: 3366. <br>
                    <b>Input the study ID:</b> This should be an identifier that begins with SDY followed by a number, listed as the 'Study Accession' in ImmPort. Example: SDY1550. <br>
                    <b>Select the ImmPort planned visit file:</b> This should be a file that contains information about the planned visits, listed as planned_visit in ImmPort. This information should include the names of the visits, start days, and planned visit accessions. <br>
                    <b>Select the ImmPort study file:</b> This should be a file that contains basic information about the study-specific study files (which are uploaded in '3. Study Files'), listed as study_file in ImmPort. This information should include the study file names, brief descriptions, study file types, and study file accessions. <br>
                    <b>View the loaded study visits:</b> This shows the names of the study visits that were listed in the ImmPort planned_visit file. <br>
                    <h2 style='text-align: center; font-weight: bold; margin: 5px 0;'>Additional Information</h2>
                        <a title='Information on ImmPort downloads' 
                            href='{0}/documentation/Load_files_from_immport.md' 
                            style='font-size: 16px; text-decoration: none; color: #0077b6;'>
                            <b>Click for information on how to download data from ImmPort</b>
                        </a>
                </div>
                """.format(documentation_base_url),
                layout={'width': '600px', 'height': 'auto'}
            )

            self.objects["toggle_current_immport_study"].set_observe(callback_function=self.update_help_text, callback_data={})

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
                spacer,
                box_planned_visits.get(),
                spacer,
                box_study_files.get(),
                spacer,
                study_visit_list_section,
                spacer, 
                bottom_buttons_1, 
                spacer
            ])

            self.objects["toggle_current_immport_study"].set_observe(callback_function=self.toggle_show_hide, callback_data={
                "toggle":{
                    1:[box_immport_study_yes], 
                    0:[box_immport_study_no,box_planned_visits,box_study_files] #,box_immport_download_instructions]
                    }
                })

            self.objects["toggle_non_tab_files"].set_observe(callback_function=self.toggle_show_hide, callback_data={
                "toggle":{
                    1:[box_planned_visits,box_study_files], #,box_immport_download_instructions], 
                    0:[]
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
    
    def update_help_text(self, event):
        """Dynamically updates the help text based on the toggle selection."""
        toggle_value = event["new"] 

        if toggle_value == 1:
            new_help_text = """
            <div style='color: black; font-family: Arial, sans-serif; font-size: 14px;
                        padding: 5px; border: 1px solid #ccc; background-color: #f9f9f9;
                        border-radius: 5px;'>
                <h2 style='text-align: center; font-weight: bold; margin: 5px 0;'>Inputs</h2>
                <b>Select the ImmPort study Tab ZIP file:</b> This should be a ZIP file that contains multiple ImmPort-specific files, listed as 'SDY(#)-DR(#)_Tab.zip' in ImmPort. <br>
                <b>Do you want to amend the Tab file with new planned visits and/or study files?:</b> This should be used if you want to use a different planned_visit.txt and/or study_file.txt then the ones that are currently in the Tab zip file. <br>
                <b>Select the ImmPort planned visit file:</b> This will appear if 'Yes' is chosen from the 'Do you want to amend the Tab file with new planned visits and/or study files?' question. This should be a file that contains information about the planned visits, listed as planned_visit in ImmPort. This information should include the names of the visits, start days, and planned visit accessions. <br>
                <b>Select the ImmPort study file:</b> This will appear if 'Yes' is chosen from the 'Do you want to amend the Tab file with new planned visits and/or study files?' question.  This should be a file that contains basic information about the study-specific study files (which are uploaded in '3. Study Files'), listed as study_file in ImmPort. This information should include the study file names, brief descriptions, study file types, and study file accessions. <br>
                <b>View the loaded study visits:</b> This shows the names of the study visits that were listed in the ImmPort planned_visit file. <br>
            </div>
            """.format(documentation_base_url)
        else: 
            new_help_text = """
            <div style='color: black; font-family: Arial, sans-serif; font-size: 14px;
                        padding: 5px; border: 1px solid #ccc; background-color: #f9f9f9;
                        border-radius: 5px;'>
                <h2 style='text-align: center; font-weight: bold; margin: 5px 0;'>Inputs</h2>
                <b>Input the workspace ID:</b> This should be a numeric identifier, listed as the 'Workspace ID' in ImmPort. Example: 3366. <br>
                <b>Input the study ID:</b> This should be an identifier that begins with SDY followed by a number, listed as the 'Study Accession' in ImmPort. Example: SDY1550. <br>
                <b>Select the ImmPort planned visit file:</b> This should be a file that contains information about the planned visits, listed as planned_visit in ImmPort. This information should include the names of the visits, start days, and planned visit accessions. <br>
                <b>Select the ImmPort study file:</b> This should be a file that contains basic information about the study-specific study files (which are uploaded in '3. Study Files'), listed as study_file in ImmPort. This information should include the study file names, brief descriptions, study file types, and study file accessions. <br>
                <b>View the loaded study visits:</b> This shows the names of the study visits that were listed in the ImmPort planned_visit file. <br>
                <h2 style='text-align: center; font-weight: bold; margin: 5px 0;'>Additional Information</h2>
                    <a title='Information on ImmPort downloads' 
                        href='{0}/documentation/Load_files_from_immport.md' 
                        style='font-size: 16px; text-decoration: none; color: #0077b6;'>
                        <b>Click for information on how to download data from ImmPort</b>
                    </a>
                </div>
                """.format(documentation_base_url)
            
        self.objects["help_text_1"].value = new_help_text

    def on_select_study_tab_file_with_error_handling(self, value, gui=None, fc_name=None):
        try:
            if value.description == "Change":
                gui.data["planned_visit"] = cf.readFileFromZip(
                    gui.objects[fc_name].widget.selected_path,
                    gui.objects[fc_name].widget.selected_filename,
                    "planned_visit.txt"
                )

                if gui.data["planned_visit"] is None:
                    raise ValueError("Missing required file 'planned_visit.txt' in the Tab ZIP file.")

                gui.data["study_files"] = cf.readFileFromZip(
                    gui.objects[fc_name].widget.selected_path,
                    gui.objects[fc_name].widget.selected_filename,
                    "study_file.txt"
                )

                if gui.data["study_files"] is None:
                    raise ValueError("Missing required file 'study_file.txt' in the Tab ZIP file.")

                gui.data["study"] = cf.readFileFromZip(
                    gui.objects[fc_name].widget.selected_path,
                    gui.objects[fc_name].widget.selected_filename,
                    "study.txt"
                )

                if gui.data["study"] is None:
                    raise ValueError("Missing required file 'study.txt' in the Tab ZIP file.")

                visit_names = get_planned_visits(gui.data["planned_visit"], nameonly=True, returnType="list")

                if "dropdown_study_visit_list" in gui.objects:
                    gui.objects["dropdown_study_visit_list"].set_options(visit_names)

                    if "study_visit_list_section" in gui.objects:
                        gui.objects["study_visit_list_section"].children = [
                            gui.objects["label_study_visit_list"],
                            gui.objects["dropdown_study_visit_list"].get()
                        ]

                gui.objects["error_message_study_tab_file"].show_hide_element(display="none")

        except Exception as e:
            gui.objects["error_message_study_tab_file"].show_hide_element(display="")
            gui.log(message=f"Error loading ImmPort study Tab file: {str(e)}", level="error", flush=True)
            gui.flush_log()

    def load_study_file(self, value):
        try:

            if value.description == "Change":
                filename = self.objects["filechooser_study_files"].get_filepath()
                with open(filename, 'r') as pv:
                    if filename.endswith(".csv"):
                        sep = ","
                    else:
                        sep = "\t"

                    self.data["study_files"] = pd.read_csv(pv, sep=sep)

                    mandatory_column = [
                        "Study File Accession"
                    ]

                    missing_column = [col for col in mandatory_column if col not in self.data["study_file"].columns]

                    if missing_column:
                        raise ValueError(f"The following mandatory columns are missing: {', '.join(missing_column)}")

                    rename_map={
                        "Study File Accession":"STUDY_FILE_ACCESSION",
                        "Study File Type":"STUDY_FILE_TYPE",
                        "File Name":"FILE_NAME",
                        "Description":"DESCRIPTION"
                    }

                    for col in list(rename_map.keys()):
                        if col not in self.data["study_files"].columns:
                            del rename_map[col]

                    self.data["study_files"].rename(columns=rename_map, inplace=True)

                self.objects["error_message_study_files"].show_hide_element(display="none")

        except Exception as e:
            self.objects["error_message_study_files"].show_hide_element(display="")
            self.log(message=f"Error loading study file: {str(e)}", level="error", flush=True)
            self.flush_log()


    def load_planned_visit_file(self, value):
        try:
            if value.description == "Change":
                planned_visit_filename = self.objects["filechooser_planned_visits"].get_filepath()
                with open(planned_visit_filename, 'r') as pv:
                    if planned_visit_filename.endswith(".csv"):
                        sep = ","
                    else:
                        sep = "\t"

                    self.data["planned_visit"] = pd.read_csv(pv, sep=sep)

                    mandatory_column = [
                        "PV Accession"
                    ]

                    missing_column = [col for col in mandatory_column if col not in self.data["planned_visit"].columns]

                    if missing_column:
                        raise ValueError(f"The following mandatory columns are missing: {', '.join(missing_column)}")

                    rename_map={
                        "PV Accession":"PLANNED_VISIT_ACCESSION",
                        "Name":"NAME",
                        "Min Start Day":"MIN_START_DAY",
                        "Max Start Day":"MAX_START_DAY",
                        "Start Rule":"START_RULE",
                        "End Rule":"END_RULE",
                        "Order Number":"ORDER_NUMBER",
                        "Test Delete":"Not Present"
                    }

                    for col in list(rename_map.keys()):
                        if col not in self.data["planned_visit"].columns:
                            del rename_map[col]

                    self.data["planned_visit"].rename(columns=rename_map, inplace=True)
            
                visit_names = get_planned_visits(self.data["planned_visit"],nameonly=True, returnType="list")
                self.objects["dropdown_study_visit_list"].set_options(visit_names)

                self.objects["error_message_planned_visits"].show_hide_element(display="none")

        except Exception as e:
            self.objects["error_message_planned_visits"].show_hide_element(display="")
            self.log(message=f"Error loading planned visits file: {str(e)}", level="error", flush=True)
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
            self.log(message="Dictionary Parsed",level='debug',flush=True)
            self.objects["button_filechooser_data_dictionary_load"].button_change(button=self.objects["button_filechooser_data_dictionary_load"], style='success', text='Dictionary Loaded',tooltip='The dictionary file has been loaded',disabled=False, icon='')

            self.objects["dropdown_table_form_column"].set_options(option_list=list(self.dictionary['columns'].items()))
            self.show_row("tab_row_dd_form_row")
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
        """Get the study file attribute"""
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
        self.objects["box_study_files_table"]=VBox(name="box_study_files_table")

        self.objects["reset_tab3_button"] = Button(text="Reset Tab", tooltip="Reset all inputs in Tab 3", style="warning", callback=self.reset_tab3, width="140px", icon="trash")

        self.objects["help_button_3"] = widgets.Button(description='Help', tooltip='Click for help', icon='question-circle')

        self.objects["help_button_3"].style.button_color = '#F7F6BB'

        self.objects["help_text_3"] = widgets.HTML(
            value="""
            <div style='color: black; font-family: Arial, sans-serif; font-size: 14px;
                        padding: 10px; border: 1px solid #ccc; background-color: #f9f9f9;
                        border-radius: 5px;'>
                <h2 style='text-align: center; font-weight: bold; margin: 5px 0;'>Input</h2>
                <b>Select the study files directory:</b> This should be a directory that contain the study-specific files that contain the forms and results of the study. In ImmPort, this is the 'StudyFiles' folder. <br>
                <h2 style='text-align: center; font-weight: bold; margin: 5px 0;'>Table</h2>    
                <b>Table Code:</b> Add stuff here. This field is mandatory. <br>
                <b>Assessment Name:</b> Add stuff here. This field is not mandatory. <br>
                <b>Template:</b> Add stuff here. This field is mandatory. <br>
                <b>Default Visit:</b> Add stuff here. This field is not mandatory. <br>
                When this table is completed, click the 'Generate Filled Templates' button.
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
        my_assessments={}
        study_id = self.get_study_id()

        study_files_dir = self.objects["filechooser_study_file_directory"].get_filepath()

        parent_dir = os.path.dirname(study_files_dir)
        parent_dir = os.path.dirname(parent_dir)

        todays_date = pd.to_datetime('today').strftime('%Y-%m-%d')
        
        study_id_todays_date = study_id + "-" + todays_date

        results_folder = os.path.join(parent_dir, "results", study_id_todays_date)

        if not os.path.exists(results_folder):
            os.makedirs(results_folder, exist_ok=True)

        self.objects["button_generate_files"].button_change(button=self.objects["button_generate_files"], style='warning', text='Generating...',tooltip='The files are being generated. This could take a few minutes',disabled=False, icon='spinner')

        errors_occurred = False

        for index, study_file_row in self.data['file_list_df'].iterrows():

            table_code = str(study_file_row["Table Code"]).strip() if pd.notna(study_file_row["Table Code"]) else ""
            template = str(study_file_row["Template"]).strip() if pd.notna(study_file_row["Template"]) else ""
            default_visit = str(study_file_row["Default Visit"]).strip() if pd.notna(study_file_row["Default Visit"]) else ""
            assessment_name = str(study_file_row["Assessment Name"]).strip() if pd.notna(study_file_row["Assessment Name"]) else ""

            if table_code == '' and template == '' and assessment_name != '' :
                self.log(
                    message=f"Error in row {index+1}: A Template and Table Code must be selected", 
                    level='error', 
                    flush=True
                )
                self.flush_log()
                errors_occurred = True
            
            if table_code == '' and template == '' and default_visit != '' :
                self.log(
                    message=f"Error in row {index+1}: A Template and Table Code must be selected", 
                    level='error', 
                    flush=True
                )
                self.flush_log()
                errors_occurred = True

            if table_code != '' and template == '':
                self.log(
                    message=f"Error in row {index+1}: A Template must be selected for Table Code '{table_code}'", 
                    level='error', 
                    flush=True
                )
                self.flush_log()
                errors_occurred = True

            if table_code == '' and template != '':
                self.log(
                    message=f"Error in row {index+1}: A Table Code must be selected for '{template}'", 
                    level='error', 
                    flush=True
                )
                self.flush_log()
                errors_occurred = True
                
            if study_file_row["Template"] == "Assessment" and table_code != '':
                try:
                    
                    table_code = study_file_row["Table Code"]
                    filename = study_file_row.to_dict().get("Filename")
                    self.log(message=f"Processing filename {filename} ({table_code})",level='info', flush=True)
                    self.objects["button_generate_files"].button_change(button=self.objects["button_generate_files"], style='warning', text=f'Generating... {table_code}',tooltip='The files are being generated. This could take a few minutes',disabled=False, icon='spinner')
                    
                    my_assessments[table_code]=sf.Assessment()
                    
                    my_assessments[table_code].process_study_file(
                        study_file_info = study_file_row.to_dict(), 
                        study_file_directory = self.objects["filechooser_study_file_directory"].get_filepath(),
                        data_dictionary = self.dictionary,
                        planned_visits = self.data["planned_visit"],
                        study_id = study_id,
                        workspace_id = self.get_workspace_id(),
                        name_reported = self.get_study_file_attribute(filename, "DESCRIPTION"),
                    )

                    my_assessments[table_code].export_to_txt( filename=f"{results_folder}/{study_id}_{table_code}.txt")
                    my_assessments[table_code].export_to_json(filename=f"{results_folder}/{study_id}_{table_code}.json")
                    
            #        fh_zip_file = zipfile.ZipFile(f"results/{study_id}/{table_code}.zip", 'w', zipfile.ZIP_DEFLATED)
            #        self.generate_zip_file(fh_zip=fh_zip_file, files=[
            #            f"results/{study_id}/{study_id}_{table_code}.txt", 
            #            os.path.relpath(self.objects["filechooser_study_file_directory"].get_filepath()+filename)
            #        ])
            #        fh_zip_file.close()
            #        self.flush_log()

                except Exception as err:
                    errors_occurred = True
                    self.log(message=f"Error processing {table_code} - {err}", level='error', flush=True)

        if errors_occurred:
            self.log(message="Some files failed to generate.", level='error', flush=True)
            self.objects["button_generate_files"].button_change(
                button=self.objects["button_generate_files"], style='danger', 
                text='Error: Some files failed to generate. Click to retry.', 
                tooltip='An error occurred during file generation. See log for more details.', 
                disabled=False, icon='warning'
            )
        else:
            self.log(message="✅ All files successfully generated.", level='info', flush=True)
            self.log(message=f"Files are in {results_folder}", level='info', flush=True)
            self.objects["button_generate_files"].button_change(
                button=self.objects["button_generate_files"], style='success', 
                text='Files Generated - Click to Re-Generate', 
                tooltip='Files have been generated in the Results folder. Click to re-generate files.', 
                disabled=False, icon='check'
            )

    # def generate_console(self):
    #     self.loggers['console'] = Log_Output(name="console", level=logging.ERROR, max_height="100px")
    #     self.loggers['output_logger'].logger.addHandler(self.loggers['console'].log_viewer)

    #     self.objects["button_clear_console"] = self.loggers["console"].add_clear_button(description="", icon="ban", style="", tooltip="Clear Console Logger")
    #     self.objects["button_clear_console"].show_hide_element(display='none')

    def generate_console(self):

        if 'output_logger' not in self.loggers:
            self.loggers["output_logger"] = Log_Output(name="output_logger", level=logging.INFO)

        self.main_logger = self.loggers["output_logger"]

        self.loggers['console'] = Log_Output(name="console", level=logging.ERROR, max_height="100px")

        self.loggers['output_logger'].logger.addHandler(self.loggers['console'].log_viewer)

        self.objects["button_clear_console"] = self.loggers["console"].add_clear_button(
            description="", icon="ban", style="", tooltip="Clear Console Logger"
        )
        self.objects["button_clear_console"].show_hide_element(display='none')


    def generate_tab_logging(self):
        """Generate the logging tab"""
        global main_logger  #Hack until fixed properly
        self.loggers["output_logger"] = Log_Output(name="output_logger", level=logging.INFO)

        self.objects["button_clear_main_logger"] = self.loggers["output_logger"].add_clear_button(description="Clear Log", tooltip="Clear the main logger", width="140px")

        self.main_logger=self.loggers["output_logger"]
        main_logger=self.main_logger

        spacer = widgets.HTML(value="<div style='height: 10px;'></div>")

        tab = widgets.VBox([self.loggers["output_logger"].get(), 
                           self.objects["button_clear_main_logger"].get(),
                            spacer])

        return tab
    
    def load_study_files(self, b): 

        if "box_study_files_table" not in self.objects:
            self.objects["box_study_files_table"] = VBox(name="box_study_files_table")

        self.objects["box_study_files_table"].toggle_display()  

        self.objects["button_filechooser_study_file_directory_load"].button_change(button=self.objects["button_filechooser_study_file_directory_load"], style='warning', text='Loading Study Files...',tooltip='The Study files are loading',disabled=False, icon='spinner')
        self.objects["html_study_files_display_text"] = HTML(html_text='<p style="font-size:18px;">Generating Study File Table...</p>')

        self.objects["box_study_files_table"].set_children([self.objects["html_study_files_display_text"].get()])
        included_extensions = ['txt','csv', 'tsv']
        if os.path.isdir(self.objects["filechooser_study_file_directory"].get_dir()):
            try:
                self.log(message='Loading files in study file directory',level='debug',flush=True)
                study_files = [f for f in os.listdir(self.objects["filechooser_study_file_directory"].get_dir()) if any(f.endswith(ext) for ext in included_extensions)]
                study_files.sort()

                self.data['file_list_df'] = pd.DataFrame(columns=['Filename','Table Code', 'Assessment Name','Template','Default Visit'])
                
                table_code_categories = list(self.dictionary["tables"].keys())
                table_code_categories.insert(0,'--Select--')
                self.data['file_list_df']["Table Code"] = pd.Categorical([], ordered=True, categories=table_code_categories)
                self.data["file_list_df"]["Template"] = pd.Categorical([],ordered=True,categories=get_immport_template_names())
                self.data["file_list_df"]["Default Visit"] = pd.Categorical([],ordered=True,categories=self.get_planned_visits(nameonly=True, returnType="list"))
                self.data["file_list_df"]["Filename"] = study_files
                self.data['file_list_df'] = self.data['file_list_df'].merge(self.data["study_files"][["FILE_NAME","DESCRIPTION"]], left_on="Filename", right_on="FILE_NAME", how="left")
                self.data['file_list_df'].rename(columns={"DESCRIPTION":"Description"}, inplace=True)
                self.data['file_list_df'] = self.data['file_list_df'][["Filename","Description","Table Code","Assessment Name","Template","Default Visit"]]

                self.log(message="Generating DF Table", level='debug',flush=True)

                self.objects["study_file_table"] = self.generate_df_table(column_widths =  ["300px","250px","100px","150px","125px","175px"], readonly=["Filename","Description"])
                
                self.objects["button_generate_files"]= Button(text="Generate Filled Templates", tooltip='Generate filled ImmPort Templates for upload into ImmPort', callback=self.generate_filled_template_files, width = "500px", margin="auto") #, style=dict(description_width='initial'))
              
                self.objects["box_study_files_table"].set_children([ self.objects["button_generate_files"].get(), self.objects["study_file_table"]])

                temp = list(self.objects["box_study_files_table"].widget.children)  
                self.objects["box_study_files_table"].widget.children = []  
                self.objects["box_study_files_table"].widget.children = temp  

                self.objects["tab3_layout"].children = [
                    self.objects["tab_row_study_files_filechooser"],  
                    self.objects["box_study_files_table"].get(),  
                #    self.objects["reset_tab3_button"].get()
                    self.objects["bottom_buttons_3"]
                ]

                self.objects["box_study_files_table"].toggle_display()

                self.objects["button_filechooser_study_file_directory_load"].button_change(button=self.objects["button_filechooser_study_file_directory_load"], style='success', text='Study Files Loaded',tooltip='The Study files have been loaded',disabled=False, icon='')
            except Exception as e:
                error = HTML(html_text='<b>Error:</b> ' + str(e))
                self.objects["box_study_files_table"].set_children([ error])
                self.log(message="Error processing study files: "+str(e), level='error', flush=True)

                raise Exception("Error loading study files: {}".format(e))
        else:
            self.log(message='Study File Directory is not a directory', level='error', flush=True)

        return
    
    def set_study_id_from_textfield(self,value):
        if value.type == 'change':
            self.set_study_id(value["new"])

    def set_workspace_id_from_textfield(self,value):
        if value.type == 'change':
            self.set_workspace_id(value["new"])

    def set_study_id(self, study_id):
        if "study" not in self.data:
            self.data["study"]={"STUDY_ACCESSION":[study_id]}
            return
        self.data["study"]["STUDY_ACCESSION"]=[study_id]

    def set_workspace_id(self, workspace_id):
        if "study" not in self.data:
            self.data["study"]={"WORKSPACE_ID":[workspace_id]}
            return
        self.data["study"]["WORKSPACE_ID"]=[workspace_id]

    def get_study_id(self):
        return self.data["study"]["STUDY_ACCESSION"][0]

    def get_workspace_id(self):
        return self.data["study"]["WORKSPACE_ID"][0]


    def generate_df_table(self, column_widths =  ["300px","100px","150px","125px","175px"], readonly=["Filename"]):
        global box, grid_body
        header_names =  self.data["file_list_df"].columns

        shape =  self.data["file_list_df"].shape
        grid_body = widgets.GridspecLayout(shape[0]+1, shape[1])

        for idx, title in enumerate(header_names):
            grid_body[0, idx] = widgets.HTML(f"<div style='font-size:16px; font-weight:bold;'>{title}</div>")
            grid_body[0,idx].layout = widgets.Layout(width=column_widths[idx])
        
        dataframe_for_table =  self.data["file_list_df"].copy()
        dataframe_for_table = dataframe_for_table.astype('string')
        dataframe_for_table.fillna('', inplace=True)

        for ind in  self.data["file_list_df"].index:
            ind2 = ind+1
            for idx, column_title in enumerate(header_names):
                readonly_bool = (True if column_title in readonly else False)
                grid_body[ind2, idx] = create_table_widget(dtype= self.data["file_list_df"][column_title].dtype, value=dataframe_for_table[column_title][ind], readonly= readonly_bool, dataframe= self.data["file_list_df"],columnName=column_title)
               
                grid_body[ind2, idx].layout = widgets.Layout(width=column_widths[idx], text_align='center')

                grid_body[ind2, idx].description_tooltip=f"{{'row':{ind},'col':{idx}','title':'{column_title}'}}"
                grid_body[ind2,idx].observe(functools.partial(update_dataframe_from_table, dataframe= self.data["file_list_df"], column_name=column_title,column=idx,row=ind), names='value')

        box_body = widgets.VBox([grid_body], layout=widgets.Layout(height='450px', overflow_y='auto'))
        box = widgets.VBox([box_body], layout=widgets.Layout(height='510px'))
        return box
    
    def load_data_dictionary_columns(self, b):
    
        dictionary_tables = list(self.dictionary['tables'].keys())

        self.objects["button_form_column_confirm"].button_change(button=self.objects["button_form_column_confirm"], style='success', text='Confirmed',tooltip='The form columns have been loaded', disabled=False, icon='')   
        
        if "html_data_dictionary_tables" in self.objects:
            dictionary_tables = list(self.dictionary['tables'].keys())
            self.objects["html_data_dictionary_tables"].set_text(text=f"{', '.join(dictionary_tables)}")

    def generate_tab_data_dictionary(self):

      #  self.objects["html_documentation_curated_dd"] = HTML(
      #      html_text=f"<h2><a title='Information on creating a curated data dictionary' href='{documentation_base_url}/documentation/Curated_Data_Dictionary.md' style='font-size: 18px; text-decoration: none; color: #0077b6;'><b>Click for the curated data dictionary user guide</b></a></h2>",description="")
        
        self.objects["filechooser_data_dictionary"] = File_Chooser(name="filechooser_data_dictionary", title='<b><span style="font-size:18px;">📁 Select the curated data dictionary</span></b>', tooltip='Load a curated data dictionary file',multiple=False,filter_pattern=['*.csv','*.txt',"*.tsv"], style=dict(description_width='initial'))

        self.objects["button_filechooser_data_dictionary_load"]= self.objects["filechooser_data_dictionary"].add_load_button(description="Load Data Dictionary", tooltip="Load a curated data dictionary file", callback=self.load_data_dictionary)
        self.objects["button_form_column_confirm"]= Button(text="Confirm Form Columns", tooltip='Confirm that the selected column from the data dictionary contains the instrument/CRF/form codes', callback=self.load_data_dictionary_columns) #, style=dict(description_width='initial'))

        self.objects["dropdown_table_form_column"] = Dropdown(options=['No selection'], description='<b><span style="font-size:18px;">Select the column that specifies the form/instrument</span></b>', tooltip='Select the column from the data dictionary that contains the form codes', style={'description_width': 'initial'})

        self.objects["reset_tab2_button"] = Button(text="Reset Tab", tooltip="Reset all inputs in Tab 2", style="warning", callback=self.reset_tab2, width="140px", icon="trash")
        
        self.objects["help_button_2"] = widgets.Button(description='Help', tooltip='Click for help', icon='question-circle')

        self.objects["help_button_2"].style.button_color = '#F7F6BB'

        self.objects["help_text_2"] = widgets.HTML(
            value="""
            <div style='color: black; font-family: Arial, sans-serif; font-size: 14px;
                        padding: 5px; border: 1px solid #ccc; background-color: #f9f9f9;
                        border-radius: 5px;'>
                <h2 style='text-align: center; font-weight: bold; margin: 5px 0;'>Inputs</h2>
                <b>Select the curated data dictionary:</b> This file should contain the data dictionary, which contains metadata about the study-specific study files (which are uploaded in '3. Study Files').  <br>
                <b>Select the column that specifies the form/instrument:</b> This will appear after the data dictionary is successfully loaded in. The dropdown should show the columns in the data dictionary. The column that contains the form/instrument identifier information should be chosen. This is likely the 'Table Name' column. <br>
                <h2 style='text-align: center; font-weight: bold; margin: 5px 0;'>Additional Information</h2>
                        <a title='Information on creating a curated data dictionary' 
                            href='{0}/documentation/Curated_Data_Dictionary.md' 
                            style='font-size: 16px; text-decoration: none; color: #0077b6;'>
                            <b>Click for the curated data dictionary user guide</b>
                        </a> 
                        <br>
                        <a title='An example data dictionary' 
                            href='{0}/documentation/Example_Data_Dictionary.md' 
                            style='font-size: 16px; text-decoration: none; color: #0077b6;'>
                            <b>Click for an example data dictionary</b>
                        </a>
            </div>
            """.format(documentation_base_url),
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
    

        self.objects["tab_row_dd_row"] = widgets.HBox([self.objects["filechooser_data_dictionary"].get(),self.objects["button_filechooser_data_dictionary_load"].get()])
        self.objects["tab_row_dd_form_row"] = widgets.HBox([self.objects["dropdown_table_form_column"].get(),self.objects["button_form_column_confirm"].get()])
        self.hide_row("tab_row_dd_form_row")

        spacer = widgets.HTML(value="<div style='height: 10px;'></div>")

        tab = widgets.VBox([
            spacer,
            self.objects["tab_row_dd_row"],
            spacer,
            self.objects["tab_row_dd_form_row"],
            spacer,
            bottom_buttons_2,
            spacer
        ])

        return tab
    
    def get_planned_visits(self, nameonly=False, returnType=None):
        
        if nameonly:
            names = self.data["planned_visit"]["NAME"]
            if returnType == 'list':
                return names.tolist()
            return names
        return self.data["planned_visit"][["PLANNED_VISIT_ACCESSION","NAME"]]


    def toggle_show_hide(self, value, toggle):
        """Toggle the study immport tab"""
        ## Need to cycle through all elements in all keys to hide if not present.
        for (key, element_list) in toggle.items():
            if key == value["new"]:
                for element in element_list:
                    element.show_hide_element('')
            else:
                for element in element_list:
                    element.show_hide_element('none')

    def hide_row(self, row):
        """Hide a row"""
        self.objects[row].layout.display = 'none'
        self.objects[row].visible = False
        self.objects[row].disabled = True

    def show_row(self, row):
        """Show a row"""
        self.objects[row].layout.display = ''
        self.objects[row].visible = True
        self.objects[row].disabled = False


    def set_data(self, key, value):
        """Set the data"""
        self.data["key"] = value

    def set_config(self, key, value):
        """Set the config value"""
        self.config[key] = value

    def write_config(sef):
        """Write the config file"""
        pass

    def read_config(self):
        """Read the config file"""
        pass

    def check_schema_version(self):
        #Get current Schema version from ImmPort:
        immport_protocol_schema_url = "https://downloads.immport.org/data/upload/templates/json-templates/protocols.json"
        try:
            response = urlopen(immport_protocol_schema_url)
            schema_json = json.loads(response.read())
            immport_schemaVersion = schema_json["properties"]['schemaVersion']['enum'][0]
            tool_schemaVersion = sf.ImmPort_Data().schemaVersion
            if  immport_schemaVersion == tool_schemaVersion:
                return True
            else:
                github_issue_url = f"https://github.com/JoshuaFortriede/ImmPort-Curation-Tool/issues/new?template=request-schema-version-update.md&title=%5BSCHEMA%7D%3A+Update+schema+to+version+{immport_schemaVersion}"
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

        # if callback is not None:
        #     self.widget.on_click(callback)
        
class Button(GUI_Object):
    """Button class"""
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

    def set_callback(self, callback):   #Note, the callback function must include an open parameter that receives the button element
        self.widget.on_click(callback)

        
    def button_change(self,button=None, style=None, text=None, tooltip=None, icon=None, display=None, disabled=None):
        """Change button properties

        Args:
            button (_type_, optional): _description_. Defaults to None.
            style (_type_, optional): _description_. Defaults to None.
            text (_type_, optional): _description_. Defaults to None.
            tooltip (_type_, optional): _description_. Defaults to None.
            icon (_type_, optional): _description_. Defaults to None.
            display (_type_, optional): _description_. Defaults to None.
            disabled (_type_, optional): _description_. Defaults to None.
        """
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
    """ToggleButtons class"""
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
    """FileChooser class"""
    def __init__(self, name, **kwargs):
        super().__init__(
            FileChooser(**kwargs)
        )
        self.name = name

        self.widget.register_callback(self.on_select)
    
    def set_filter(self, filter=[]):
        """filter: list of file types [".txt", ".csv"]"""
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
        return self.widget.selected_path +"/"+ self.widget.selected_filename
    
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

    def on_select(self):        #If this is a directory only, then need different logic to show the button
        if hasattr(self, "load_button"):
            if len(self.widget._selected_path)>0:
                self.load_button.show_hide_element('')
                self.load_button.widget.button_style='info'
                self.load_button.widget.disabled=False
            # if hasattr(self, "on_file_change_callback"):
            #     self.on_file_change_callback()
            else:
                self.load_button.show_hide_element('none')

class Dropdown(GUI_Object):
    """Dropdown class"""
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
    """HBox class"""
    def __init__(self, *args, **kwargs):
        super().__init__(
            widgets.HBox(*args, **kwargs)
        )
    
    def set_children(self, child_list=[]):
        self.widget.children = child_list

class VBox(GUI_Object):
    """VBox class"""
    def __init__(self, *args, **kwargs):
        super().__init__(
            widgets.VBox(*args, **kwargs)
        )
    
    def set_children(self, child_list=[]):
        self.widget.children = child_list

class HTML(GUI_Object):
    """HTML class"""
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
    """Log_Output class"""

    fmt = '%(name)s | %(levelname)8s | %(message)s'

    def __init__(self, level=logging.DEBUG, name=__name__, max_height="525px", handlers=[]):
        super().__init__(
            widgets.Output(layout=widgets.Layout(max_height=max_height, overflow_y="auto"))
        )
        self.messages={}
        self.name = name
        self.logger = logging.getLogger(name)
        self.logger.setLevel(logging.DEBUG)
        self.log_viewer = log_viewer(output=self.widget,name=name, parent=self)
        # self.log_viewer.parent = self
        self.log_viewer.setLevel(level)
        self.logger.addHandler(self.log_viewer)
        for handler in handlers:
            self.logger.addHandler(handler)

        self.log={
            "debug":self.logger.debug,
            "info":self.logger.info,
            "warning":self.logger.warning,
            "warn":self.logger.warning,
            "error":self.logger.error,
            "critical":self.logger.critical,
        }

        self.log_levels = {
            "critical":50,
            "error":40,
            "warning":30,
            "warn":30,
            "info":20,
            "debug":10
            }
        
          # ✅ Ensure `clear_button` always exists
        self.clear_button = Button(
            text="Clear Log",
            tooltip="Clear the main logger",
            callback=self.clear_output,
            style="",
            icon="trash",
            width="120px"
        )
        self.clear_button.show_hide_element(display="none")

    ##Add history to the log output
    ##Add a button to write from history with certain level

    def write(self,message=None, level=None, flush=False):
        level = level.lower()
        if level not in self.messages:
            self.messages[level]={message:1}
        else:
            if message not in self.messages[level]:
                self.messages[level][message]=1
            else:
                self.messages[level][message]+=1
        if flush:
            self.flush()

    # def write(self, message=None, level=None, flush=True):  
    #     level = level.lower()
        
    #     if level in self.log:
    #         self.log[level](message)

    #     if flush:
    #         self.flush()


    def flush(self):
        if len(self.messages.keys())==0:
            return None
        # level_counts={}
        levels = sorted(self.messages, key=lambda x: self.log_levels[x], reverse=True)
        for level in levels:
            # level_counts[level]=sum(self.messages[level].vlaues())
            for message, count in self.messages[level].items():
                # return
                if count == 1:
                    self.log[level](f"{message}")
                else:
                    self.log[level](f"({count}) {message}")
                    
        try:
            highest_level = [levels[0] , sum(self.messages[levels[0]].values())]
        except Exception as e:
            pass

        self.messages={}

          # ✅ Fix: Check if `clear_button` exists before using it
        if hasattr(self, "clear_button"):
            self.clear_button.show_hide_element(display="")


        return highest_level

    def clear_output(self,b):
        self.widget.clear_output()
        self.clear_button.show_hide_element(display="none")

    def add_clear_button(self, description="Clear Log", tooltip="Clear the main logger", icon="trash", style="", width="auto"):
        button = Button(
            text=description,
            tooltip=tooltip,
            callback=self.clear_output,
            style=style,
            icon=icon,
            width=width
        )

        if style == "":
            button.widget.style.button_color = '#F7F6BB' 

        self.clear_button = button
        return button

########################################################################################################################
class OutputWidgetHandler(logging.Handler):  #Archive
    """ Custom logging handler sending logs to an output widget """

    def __init__(self, output_widget, *args, **kwargs):
        super(OutputWidgetHandler, self).__init__(*args, **kwargs)
        layout = {
            'width': '100%',
            'height': '550px',
            'border': '1px solid black'
        }
        self.out = output_widget #widgets.Output(layout=layout)

    def emit(self, record):
        """ Overload of logging.Handler method """
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
        """ Show the logs """
        display(self.out)

    def clear_logs(self):
        """ Clear the current logs """
        self.out.clear_output()


immport_data = {'tab_data':{},'config':{}}

####Keep

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
        if "--Select--" not in option_list:
            option_list.insert(0,"--Select--")
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

        gui.data["study"] = cf.readFileFromZip(gui.objects[fc_name].widget.selected_path, gui.objects[fc_name].widget.selected_filename, "study.txt")

        visit_names = get_planned_visits(gui.data["planned_visit"],nameonly=True, returnType="list")
        
        if "dropdown_study_visit_list" in gui.objects:
            gui.objects["dropdown_study_visit_list"].set_options(visit_names)

            if "study_visit_list_section" in gui.objects:
                gui.objects["study_visit_list_section"].children = [
                    gui.objects["label_study_visit_list"], 
                    gui.objects["dropdown_study_visit_list"].get()  
                ]

def get_planned_visits(planned_visits, nameonly=False, returnType=None):
    #TODO move into gui and wrap try/except with logging
    if nameonly:
        names = planned_visits["NAME"]
        if returnType == 'list':
            return names.tolist()
        return names
    return planned_visits[["PLANNED_VISIT_ACCESSION","NAME"]]






















