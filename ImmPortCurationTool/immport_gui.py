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
        # self.generate_console()
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

    # def generate_error_header(self): #TODO refactor into a "Banner Output"
    #     self.objects["box_errors"] = HBox(name="box_errors")
    #     self.objects["html_errors"] = HTML()
    #     self.objects["button_errors_clear"] = Button(description="Clear")
    #     self.objects["box_errors"].set_children(self.objects["html_errors"].get(),self.objects["button_errors_clear"].get())
    #     return

    def generate_gui(self):

        self.objects["title"] = widgets.HTML(value="<h1 style='text-align:center; color:#3E6962; font-size:36px;'>ImmPort Curation Tool</h1>")

        tab_titles = ["1. Study", "2. Data Dictionary", "3. Study Files", "Logging", "Help"]
        tab_colors = ["#98b3a2", "#F4DAC1", "#ADD5CC", "#dca485", "#D6C097"]  # Custom colors

        tab_contents = {
            "1. Study": self.generate_tab_study_info(),
            "2. Data Dictionary": self.generate_tab_data_dictionary(),
            "3. Study Files": self.generate_tab_study_files(),
            "Logging": self.generate_tab_logging(),
            "Help": self.generate_tab_help(),
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
                <h2 style='color:black; margin-bottom: 0px;'>🔍 Overview</h2>
                <span style='font-size: 18px; color: black;'> {self.objects["version"].get().value} </span>
            </div>

            <p style='font-size:18px; color:black; margin-top: 0px;'>
                <br>
                The purpose of this tool is to transform data files/tables from a study into ImmPort templates for upload and integration into the ImmPort database
                <br>
                <br>
                <b>1. Study:</b> Start the data transformation by uploading study data in the first tab
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

        self.objects["toggle_current_immport_study"] = ToggleButtons(description='<b><span style="font-size:18px;">🔘 Choose initial input type</span></b>', options=[('Download information from ImmPort',0),('Use ImmPort TAB file',1)], value=0, tooltips=['Downloaded from the public area of ImmPort','Downloaded from the private area of ImmPort'], style=dict(description_width='initial',button_width='auto'))
        self.objects["filechooser_study_tab_file"] = File_Chooser(name="filechooser_study_tab_file", title='<b><span style="font-size:18px;">📁 Select the ImmPort study TAB ZIP file</span></b>', tooltip='Load a study tab file',multiple=False,filter_pattern=['SDY*-DR*_Tab.zip'], style=dict(description_width='initial'))
        self.objects["filechooser_study_tab_file"].set_onclick(self, callback_function=on_select_study_tab_file, callback_data = {"gui":self, "fc_name":"filechooser_study_tab_file"})

        self.objects["filechooser_planned_visits"] = File_Chooser(name="filechooser_planned_visits", title='<b><span style="font-size:18px;">📁 Select the ImmPort planned visit file</span></b>', tooltip='Load a planned visit file',multiple=False,filter_pattern=['*.csv'], style=dict(description_width='initial'))
        self.objects["filechooser_planned_visits"].set_onclick(self, callback_function=self.load_planned_visit_file, callback_data = {})

        self.objects["filechooser_study_files"] = File_Chooser(name="filechooser_study_files", title='<b><span style="font-size:18px;">📁 Select the ImmPort study file</span></b>', tooltip='Load a study files file',multiple=False,filter_pattern=['*.csv'], style=dict(description_width='initial'))
        self.objects["filechooser_study_files"].set_onclick(self, callback_function=self.load_study_file, callback_data = {})

        self.objects["html_non_Immport"] = HTML(
            html_text=f"<h2><a title='Information on ImmPort downloads' href='{documentation_base_url}/documentation/Load_files_from_immport.md' style='font-size: 18px; text-decoration: none; color: #0077b6;'><b>Click for information on how to download data from ImmPort</b></a></h2>",description="")

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

        box_immport_download_instructions = VBox(name='box_immport_download_instructions')
        box_immport_download_instructions.set_children([self.objects['html_non_Immport'].get()])

        box_planned_visits = VBox(name='box_planned_visits')
        box_planned_visits.set_children([self.objects['filechooser_planned_visits'].get()])

        box_study_files = VBox(name='box_study_files')
        box_study_files.set_children([self.objects['filechooser_study_files'].get()])

        self.objects["toggle_non_tab_files"] = ToggleButtons(description='<b><span style="font-size:18px;">Do you want to amend the TAB file with new planned visits and/or study files?</span></b>', options=[('Yes',1),('No',0)], value=0, tooltips=[], style=dict(description_width='initial',button_width='auto'))

        spacer_before_toggle = widgets.HTML(value="<div style='height: 20px;'></div>")

        toggle_with_spacing = widgets.VBox([
            spacer_before_toggle,
            self.objects["toggle_non_tab_files"].get()
        ])

        box_immport_study_yes.set_children([self.objects["filechooser_study_tab_file"].get(), toggle_with_spacing])

        box_immport_study_no.set_children([workspace_id_section, study_id_section])

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
            box_immport_download_instructions.get(),
            spacer
        ])

        self.objects["toggle_current_immport_study"].set_observe(callback_function=self.toggle_show_hide, callback_data={
            "toggle":{
                1:[box_immport_study_yes], 
                0:[box_immport_study_no,box_planned_visits,box_study_files,box_immport_download_instructions]
                }
            })

        self.objects["toggle_non_tab_files"].set_observe(callback_function=self.toggle_show_hide, callback_data={
            "toggle":{
                1:[box_planned_visits,box_study_files,box_immport_download_instructions], 
                0:[]
                }
            })
        return tab

    def load_study_file(self, value):
        if value.description == "Change":
            filename = self.objects["filechooser_study_files"].get_filepath()
            with open(filename, 'r') as pv:
                if filename.endswith(".csv"):
                    sep = ","
                else:
                    sep = "\t"

                self.data["study_files"] = pd.read_csv(pv, sep=sep)

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

    def load_planned_visit_file(self, value):
        if value.description == "Change":
            planned_visit_filename = self.objects["filechooser_planned_visits"].get_filepath()
            with open(planned_visit_filename, 'r') as pv:
                if planned_visit_filename.endswith(".csv"):
                    sep = ","
                else:
                    sep = "\t"

                self.data["planned_visit"] = pd.read_csv(pv, sep=sep)

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
            self.objects["button_filechooser_data_dictionary_load"].button_change(button=self.objects["button_filechooser_data_dictionary_load"], style='success', text='Dictionary Loaded',tooltip='The dictionary file has been loaded',disabled=True, icon='')

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
        
    def on_file_change(self):

        self.objects["button_filechooser_data_dictionary_load"].button_change(
            button=self.objects["button_filechooser_data_dictionary_load"], 
            style='',  
            text='Load Data Dictionary',  
            tooltip='Load a curated data dictionary file', 
            disabled=False,  
            icon='upload'  
        )
        
        display(self.objects["button_filechooser_data_dictionary_load"].widget)

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

        spacer = widgets.HTML(value="<div style='height: 10px;'></div>")

        tab = widgets.VBox([
            spacer,
            self.objects["tab_row_study_files_filechooser"], 
            spacer, 
            self.objects["tables_section"], 
            spacer,
            self.objects["box_study_files_table"].get(), 
            spacer])
        return tab

    def generate_zip_file(self, fh_zip, files=[]):
        for file in files:
            fh_zip.write(file, os.path.basename(file))
        return

    def generate_filled_template_files(self, b):
        my_assessments={}
        study_id = self.get_study_id()
        self.objects["button_generate_files"].button_change(button=self.objects["button_generate_files"], style='warning', text='Generating...',tooltip='The files are being generated. This could take a few minutes',disabled=False, icon='spinner')
        for index, study_file_row in self.data['file_list_df'].iterrows():
            if study_file_row["Template"] == "Assessment":
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
                        study_id =study_id,
                        workspace_id = self.get_workspace_id(),
                        name_reported = self.get_study_file_attribute(filename, "DESCRIPTION"),
                    )

                    my_assessments[table_code].export_to_txt( filename=f"results/{study_id}/{study_id}_{table_code}.txt")
                    my_assessments[table_code].export_to_json(filename=f"results/{study_id}/{study_id}_{table_code}.json")
                    
                    fh_zip_file = zipfile.ZipFile(f"results/{study_id}/{table_code}.zip", 'w', zipfile.ZIP_DEFLATED)
                    self.generate_zip_file(fh_zip=fh_zip_file, files=[
                        f"results/{study_id}/{study_id}_{table_code}.txt", 
                        os.path.relpath(self.objects["filechooser_study_file_directory"].get_filepath()+filename)
                    ])
                    fh_zip_file.close()
                    self.flush_log()
                except Exception as err:
                    self.log(message=f"Error processing {table_code} - {err}", level='error', flush=True)
                    pass
        self.objects["button_generate_files"].button_change(button=self.objects["button_generate_files"], style='success', text='Files Generated - Click to Re-Generate',tooltip='Files have been generated in the Results folder. Click to re-generate files.',disabled=False, icon='')

    def generate_console(self):
        self.loggers['console'] = Log_Output(name="console", level=logging.ERROR, max_height="100px")
        self.loggers['output_logger'].logger.addHandler(self.loggers['console'].log_viewer)

        self.objects["button_clear_console"] = self.loggers["console"].add_clear_button(description="", icon="ban", style="", tooltip="Clear Console Logger")
        self.objects["button_clear_console"].show_hide_element(display='none')

    def generate_tab_logging(self):
        """Generate the logging tab"""
        global main_logger  #Hack until fixed properly
        self.loggers["output_logger"] = Log_Output(name="output_logger", level=logging.INFO)

        self.objects["button_clear_main_logger"] = self.loggers["output_logger"].add_clear_button(description="Clear", tooltip="Clear the main logger", width="120px")

        self.main_logger=self.loggers["output_logger"]
        main_logger=self.main_logger

        tab = widgets.VBox([self.objects["button_clear_main_logger"].get(),self.loggers["output_logger"].get()])

        return tab
    
    def load_study_files(self, b): #HERE
        """Load the study files"""

        self.objects["button_filechooser_study_file_directory_load"].button_change(button=self.objects["button_filechooser_study_file_directory_load"], style='warning', text='Loading Study Files...',tooltip='The Study files are loading',disabled=False, icon='spinner')
        self.objects["html_study_files_display_text"] = HTML(html_text='Generating Study File Table...')
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
                #TODO Set width so it is not 100% wide
                self.objects["button_generate_files"]= Button(text="Generate Filled Templates", tooltip='Generate filled ImmPort Templates for upload into ImmPort', callback=self.generate_filled_template_files) #, style=dict(description_width='initial'))
                #generate_filled_template_files
                self.objects["box_study_files_table"].set_children([ self.objects["button_generate_files"].get(), self.objects["study_file_table"]])
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
            grid_body[0,idx] = widgets.HTML(f"<b>{title}</b>")
            grid_body[0,idx].layout = widgets.Layout(width=column_widths[idx])
        
        dataframe_for_table =  self.data["file_list_df"].copy()
        dataframe_for_table = dataframe_for_table.astype('string')
        dataframe_for_table.fillna('', inplace=True)

        for ind in  self.data["file_list_df"].index:
            ind2 = ind+1
            for idx, column_title in enumerate(header_names):
                readonly_bool = (True if column_title in readonly else False)
                grid_body[ind2, idx] = create_table_widget(dtype= self.data["file_list_df"][column_title].dtype, value=dataframe_for_table[column_title][ind], readonly= readonly_bool, dataframe= self.data["file_list_df"],columnName=column_title)
                grid_body[ind2, idx].layout = widgets.Layout(width=column_widths[idx])

                grid_body[ind2, idx].description_tooltip=f"{{'row':{ind},'col':{idx}','title':'{column_title}'}}"
                grid_body[ind2,idx].observe(functools.partial(update_dataframe_from_table, dataframe= self.data["file_list_df"], column_name=column_title,column=idx,row=ind), names='value')

        box_body = widgets.VBox([grid_body], layout=widgets.Layout(height='450px', overflow_y='auto'))
        box = widgets.VBox([box_body], layout=widgets.Layout(height='510px'))
        return box

        
    def load_data_dictionary_columns(self, b):
        self.objects["button_form_column_confirm"].button_change(button=self.objects["button_form_column_confirm"], style='success', text='Confirmed',tooltip='The form columns have been loaded',disabled=True, icon='')
        
        dictionary_tables = list(self.dictionary['tables'].keys())
        self.objects["html_data_dictionary_tables"].set_text(text=f"{', '.join(dictionary_tables)}")
        
        return
    
    def generate_tab_data_dictionary(self):
        self.objects["html_documentation_curated_dd"] = HTML(
            html_text=f"<h2><a title='Information on creating a curated data dictionary' href='{documentation_base_url}/documentation/Curated_Data_Dictionary.md' style='font-size: 18px; text-decoration: none; color: #0077b6;'><b>Click for the curated data dictionary user guide</b></a></h2>",description="")
        
        self.objects["filechooser_data_dictionary"] = File_Chooser(name="filechooser_data_dictionary", title='<b><span style="font-size:18px;">📁 Select the curated data dictionary</span></b>', tooltip='Load a curated data dictionary file',multiple=False,filter_pattern=['*.csv','*.txt',"*.tsv"], style=dict(description_width='initial'))
                
        self.objects["filechooser_data_dictionary"].on_file_change_callback = self.on_file_change

        self.objects["button_filechooser_data_dictionary_load"]= self.objects["filechooser_data_dictionary"].add_load_button(description="Load Data Dictionary", tooltip="Load a curated data dictionary file", callback=self.load_data_dictionary)
        self.objects["button_form_column_confirm"]= Button(text="Confirm Form Columns", tooltip='Confirm that the selected column from the data dictionary contains the instrument/CRF/form codes', callback=self.load_data_dictionary_columns) #, style=dict(description_width='initial'))

        self.objects["dropdown_table_form_column"] = Dropdown(options=['No selection'], description='<b><span style="font-size:18px;">Select the column that specifies the form/instrument</span></b>', tooltip='Select the column from the data dictionary that contains the form codes', style={'description_width': 'initial'})

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
            self.objects["html_documentation_curated_dd"].get()
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
    """Tab class"""
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
    def __init__(self, text, style=None, icon="", tooltip="", state=False, callback=None, display=True, width="auto"):
        super().__init__(
            widgets.Button(
                description=text,
                icon=icon,
                tooltip=tooltip,
                layout=widgets.Layout(width=width),
                disabled = state
            )
        )
        if style is not None:
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

        if style is not None:
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
                value=kwargs.get("text",""),
                placeholder=kwargs.get("placeholder",""),
                description=kwargs.get("description",""),
                disabled=False
            )
        )

        self.name = kwargs.get("name","undefined_textfield_"+str(TextField.counter))
        TextField.counter+=1

        if "regex" in kwargs:
            self.widget.observe(self.check_value, names='value')
            self.regex = kwargs["regex"]
            self.helper = HTML(html_text=f"<span style='color:red'>Invalid Value! Please use a value that matches the format of {self.regex}</span>")
            self.helper.toggle_display()
    
    def get(self):
        """Return the widget"""
        if hasattr(self, "helper"):
            return widgets.HBox([self.widget,self.helper.get()])
        return self.widget

    @debounce(1)    #Wait 1 second
    def check_value(self, value):
        if value["type"]=="change":
            if re.fullmatch(self.regex, self.widget.value.upper()) is None:
                self.helper.show_hide_element(display='')
                return
            self.helper.show_hide_element(display='none')

class File_Chooser(GUI_Object):
    """FileChooser class"""
    def __init__(self, name, **kwargs):
        super().__init__(
            FileChooser(**kwargs)
            # FileChooser()
        )
        self.name = name

        #Register an on select callback
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
            if hasattr(self, "on_file_change_callback"):
                self.on_file_change_callback()
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
        return highest_level

    def clear_output(self,b):
        self.widget.clear_output()
        self.clear_button.show_hide_element(display="none")

    def add_clear_button(self, description="Clear Log", tooltip="Clear the main logger", icon="trash", style="info", width="auto"):
        button = Button(
            text=description,
            tooltip=tooltip,
            callback=self.clear_output,
            style=style,
            icon=icon,
            width=width
        )

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
    return ['--Select--',"Assessment"]


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
        gui.data["planned_visit"] = cf.readFileFromZip( gui.objects[fc_name].widget.selected_path, gui.objects[fc_name].widget.selected_filename, "planned_visit.txt")
        gui.data["study_files"] = cf.readFileFromZip(   gui.objects[fc_name].widget.selected_path, gui.objects[fc_name].widget.selected_filename, "study_file.txt")
        gui.data["study"] = cf.readFileFromZip(         gui.objects[fc_name].widget.selected_path, gui.objects[fc_name].widget.selected_filename, "study.txt")

        visit_names = get_planned_visits(gui.data["planned_visit"],nameonly=True, returnType="list")
        
        gui.objects["dropdown_study_visit_list"].set_options(visit_names)


def get_planned_visits(planned_visits, nameonly=False, returnType=None):
    #TODO move into gui and wrap try/except with logging
    if nameonly:
        names = planned_visits["NAME"]
        if returnType == 'list':
            return names.tolist()
        return names
    return planned_visits[["PLANNED_VISIT_ACCESSION","NAME"]]























