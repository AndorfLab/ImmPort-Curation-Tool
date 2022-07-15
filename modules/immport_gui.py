import pandas as pd
import os
import shutil

from modules import processRedCapFiles as rc
from modules import curationFunctions as cf
from modules import analysisFunctions as af
from modules import schemaFunctions as sf

import zipfile
import ipywidgets as widgets
from ipyfilechooser import FileChooser

import functools
import logging
logging_buffer_data = {}
main_logger=""
output2 = widgets.Output(layout=widgets.Layout(max_height="425px", overflow_y="auto"))

class CustomFormatter(logging.Formatter):
    """Logging colored formatter, adapted from https://stackoverflow.com/a/56944256/3638629"""

    grey =      '\x1b[38;5;248m'
    blue =      '\x1b[38;5;39m'
    yellow =    '\x1b[48;5;226m'
    red =       '\x1b[38;5;196;3m'
    bold_red =  '\x1b[48;5;196;1m'
    reset =     '\x1b[0m'
    

    def __init__(self, fmt):
        super().__init__()
        self.fmt = fmt
        self.FORMATS = {
            logging.DEBUG: self.grey + self.fmt + self.reset,
            logging.INFO: self.blue + self.fmt + self.reset,
            logging.WARNING: self.yellow + self.fmt + self.reset,
            logging.ERROR: self.red + self.fmt + self.reset,
            logging.CRITICAL: self.bold_red + self.fmt + self.reset
        }

    def format(self, record):
        log_fmt = self.FORMATS.get(record.levelno)
        formatter = logging.Formatter(log_fmt)
        return formatter.format(record)

class log_viewer(logging.Handler):
    """ Class to redistribute python logging data """
    fmt = '%(name)s | %(levelname)8s | %(message)s'

    # have a class member to store the existing logger

    def __init__(self, *args, **kwargs):
        # Initialize the Handler
        self.logger_instance = logging.getLogger(kwargs.get("name",__name__))
        # print("Name",kwargs.get("name",__name__))
        logging.Handler.__init__(self, *args)

        # optional take format
        # setFormatter function is derived from logging.Handler
        for key, value in kwargs.items():
            # print(f"{key}:{value}")
            if "{}".format(key) == "format":
                self.setFormatter(value)
        # print(kwargs.items())

        if "output" in kwargs:
            # print("use widget")
            self.output = kwargs["output"]
        else:
            # print("use output2")
            self.output = output2

        # make the logger send data to this class
        self.logger_instance.addHandler(self)
        self.setFormatter(CustomFormatter(self.fmt))
        # print(f"output: {self.output}")

    def emit(self, record):
        """ Overload of logging.Handler method """
        record = self.format(record)
        # print(self.output)
        with self.output:
            print(record)

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
        return self.widget
    
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
        # self.widget.set_attribute(attribute, value)

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
        # self.logger = logging.getLogger("__name__")
        # self.logger.setLevel(logging.DEBUG)
        # self.logger.addHandler(log_viewer())
        super().__init__(widgets.Tab(layout=widgets.Layout(min_height="500px")))
        self.tabs={}
        self.config={}
        self.objects={}
        self.dictionary={}
        self.loggers={}
        self.generate_gui()

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

    def log(self, message, level="debug", flush=False):
        self.main_logger.write(message, level, flush)
        return
    
    def flush_log(self):
        self.main_logger.flush()
        return

    def create_logger(self, name="main_logger",level="debug"):
        layout = {
            'width': '100%',
            'height': '550px',
            'border': '1px solid black'
        }

        self.loggers[name] = logging.getLogger(name)
        self.loggers[name].setLevel(logging.DEBUG)
        self.loggers[name].widget = widgets.Output(layout=layout)
        handler = OutputWidgetHandler(self.loggers[name].widget)
        handler.setFormatter(logging.Formatter('%(asctime)s  - [%(levelname)s] %(message)s'))
        self.loggers[name].addHandler(handler)
        # self.loggers[name].setLevel(level)

    def generate_gui(self):
        """Generate the GUI"""
        self.add_tab(Tab("Study",self.generate_tab_study_info()))
        self.add_tab(Tab("Data Dictionary",self.generate_tab_data_dictionary()))
        self.add_tab(Tab("Study Files",self.generate_tab_study_files()))
        self.add_tab(Tab("Logging",self.generate_tab_logging()))
        # self.main_logger = self.objects["output_logger"]
        self.log(message="GUI generated", level="info")
        self.flush_log()
        return self.widget
    
    def generate_tab_study_info(self):
        """Generate the study info tab"""
        # tab = widgets.VBox(layout=widgets.Layout(min_height="500px"))

        self.objects["toggle_current_immport_study"] = ToggleButtons(description="Is this a current Immport study?", options=[('Yes',1),('No',0)], value=1, tooltip='Has this study been registered in ImmPort?', style=dict(description_width='initial'))
        self.objects["dropdown_study_visit_list"] = Dropdown(options=[''], description='<b>Study Visits:</b>', tooltip='View the loaded study visits')
        self.objects["filechooser_study_tab_file"] = File_Chooser(name="filechooser_study_tab_file", title='<b>Select the ImmPort Study Tab zip file</b>', tooltip='Load a study tab file',multiple=False,filter_pattern=['SDY*-DR*_Tab.zip'], style=dict(description_width='initial'))

        self.objects["filechooser_study_tab_file"].set_onclick(self, callback_function=on_select_study_tab_file2, callback_data = {"gui":self, "fc_name":"filechooser_study_tab_file"})

        box_immport_study_yes = widgets.VBox([self.objects["filechooser_study_tab_file"].get()])
        box_immport_study_no = widgets.VBox([])
        tab = widgets.VBox([
            self.objects["toggle_current_immport_study"].get(), 
            box_immport_study_yes, 
            box_immport_study_no,
            self.objects["dropdown_study_visit_list"].get()
        ])

        self.objects["toggle_current_immport_study"].set_observe(callback_function=self.toggle_show_hide, callback_data={"toggle":{1:[box_immport_study_yes], 0:[box_immport_study_no]}})
        return tab

    def load_data_dictionary(self,gui):
        # unique_logging_buffer_load(message=self,level='info',flush=True)
        # unique_logging_buffer_load(message=self.objects["button_filechooser_data_dictionary_load"],level='info',flush=True)
        self.objects["button_filechooser_data_dictionary_load"].button_change(button=self.objects["button_filechooser_data_dictionary_load"], style='warning', text='Loading',tooltip='The data dictionary file is being loaded',disabled=False, icon='spinner')
        self.show_row("tab_row_dd_form_row")

#        unique_logging_buffer_load(message='test me',level='info',flush=True)  # Check
#        unique_logging_buffer_load(message=self,level='info',flush=True)  # Check
#        unique_logging_buffer_load(message=self.objects["filechooser_data_dictionary"],level='info',flush=True)  # Check
        # unique_logging_buffer_load(message=self.objects["filechooser_data_dictionary"].__dict__,level='info',flush=True)
#        unique_logging_buffer_load(message=self.objects["filechooser_data_dictionary"].get_filename(),level='info',flush=True)  # Check
#        unique_logging_buffer_load(message=self.objects["filechooser_data_dictionary"].get_dir(),level='info',flush=True)  # Check

        self.config["data_dictionary"] = {
            "filename": self.objects["filechooser_data_dictionary"].get_filename(),
            "filedir": self.objects["filechooser_data_dictionary"].get_dir(),
            "filepath": self.objects["filechooser_data_dictionary"].get_filepath(),
        }

        # dictionary_path = f"{self.config['data_dictionary']['filepath']}/{self.config['data_dictionary']['filename']}"
#        unique_logging_buffer_load(message=self.config['data_dictionary']['filepath'],level='info',flush=True)  # Check
        try:

            self.dictionary = rc.parseDataDictionary(self.config['data_dictionary']['filepath'])
#            unique_logging_buffer_load(message="Dictionary Parsed",level='info',flush=True)  # Check
#            unique_logging_buffer_load(message=type(self.dictionary),level='info',flush=True)  # Check
            self.objects["button_filechooser_data_dictionary_load"].button_change(button=self.objects["button_filechooser_data_dictionary_load"], style='success', text='Dictionary Loaded',tooltip='The dictionary file has been loaded',disabled=True, icon='')
#            unique_logging_buffer_load(message="Button changed to success",level='info',flush=True)  # Check

            self.objects["dropdown_table_form_column"].set_options(option_list=list(self.dictionary['columns'].items()))
#            unique_logging_buffer_load(message="Options set",level='info',flush=True)  # Check

        except:
            self.objects["button_filechooser_data_dictionary_load"].button_change(button=self.objects["button_filechooser_data_dictionary_load"], style='danger', text='Load Failed',tooltip='Something went wrong while loading the Data Dictionary',disabled=False, icon='')
#            unique_logging_buffer_load(message="failed",level='error',flush=True)  # Check
        
    def get_study_file_attribute(self, filename, attribute):
        """Get the study file attribute"""
        if attribute.upper() not in list(self.data["study_files"].columns):
            raise NotImplementedError(f"Attribute {attribute} not found in study file { list(self.data['study_files'].columns())}")
        return self.data["study_files"][self.data["study_files"]["FILE_NAME"]==filename][attribute].values[0]

    def generate_tab_study_files(self):
        """Generate the study files tab"""
        
        self.objects["filechooser_study_file_directory"] = File_Chooser(name="filechooser_study_file_directory", title='<b>Select the Study Files Directory</b>', tooltip='Load the study files directory',multiple=False,filter_pattern=['*'], style=dict(description_width='initial'),show_only_dirs=True)
        # self.objects["button_filechooser_study_file_directory_load"] = self.objects["filechooser_study_file_directory"].add_load_button(description="Load Study Files Directory", tooltip="Load the study files directory")  #callback=self.process_study_file_directory
        self.objects["button_filechooser_study_file_directory_load"] = self.objects["filechooser_study_file_directory"].add_load_button(description="Load Study Files Directory", tooltip="Load the study files directory", callback=self.load_study_files)
        
        self.objects["html_data_dictionary_tables"] = HTML(html_text='',description="<b>Tables Listed in Dictionary:</b>")

        self.objects["tab_row_study_files_filechooser"] = widgets.HBox([self.objects["filechooser_study_file_directory"].get(), self.objects["button_filechooser_study_file_directory_load"].get()])

        self.objects["box_study_files_table"]=VBox(name="box_study_files_table")

        tab = widgets.VBox([self.objects["tab_row_study_files_filechooser"], self.objects["html_data_dictionary_tables"].get(),self.objects["box_study_files_table"].get()])
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
        self.objects["button_generate_files"].button_change(button=self.objects["button_generate_files"], style='success', text='Files Generated',tooltip='Files have been generated in the Results folder. Click to re-generate files.',disabled=False, icon='')
        # return fh_zip_file

    def generate_tab_logging(self):
        """Generate the logging tab"""
        global main_logger
        self.loggers["output_logger"] = Log_Output(name="output_logger")
        self.main_logger=self.loggers["output_logger"]
        main_logger = self.loggers["output_logger"]
        
        tab = widgets.VBox([self.loggers["output_logger"].get()])

        return tab

    def load_study_files(self, b): #HERE
        """Load the study files"""
        # self.objects["button_filechooser_study_file_directory_load"].button_change(button=self.objects["button_filechooser_study_file_directory_load"], style='success', text='Study Files Loaded',tooltip='The Study files have been loaded',disabled=False, icon='')

        # unique_logging_buffer_load(message='load_study_files-before isdir',level='info',flush=True)
        self.objects["button_filechooser_study_file_directory_load"].button_change(button=self.objects["button_filechooser_study_file_directory_load"], style='warning', text='Loading Study Files...',tooltip='The Study files are loading',disabled=False, icon='spinner')
        self.objects["html_study_files_display_text"] = HTML(html_text='Generating Study File Table...')
        self.objects["box_study_files_table"].set_children([self.objects["html_study_files_display_text"].get()])
        included_extensions = ['txt','csv', 'tsv']
        # return
        # unique_logging_buffer_load(message='load_study_files-before isdir',level='info',flush=True)
        if os.path.isdir(self.objects["filechooser_study_file_directory"].get_dir()):
            try:
                # unique_logging_buffer_load(message='load_study_files-in isdir',level='info',flush=True)
                study_files = [f for f in os.listdir(self.objects["filechooser_study_file_directory"].get_dir()) if any(f.endswith(ext) for ext in included_extensions)]
                study_files.sort()
                # self.data
                # unique_logging_buffer_load(message='study_files',level='info',flush=True)
                
                self.data['file_list_df'] = pd.DataFrame(columns=['Filename','Table Code', 'Assessment Name','Template','Default Visit'])
                # unique_logging_buffer_load(message='DF created',level='info',flush=True)
                
                table_code_categories = list(self.dictionary["tables"].keys())
                table_code_categories.insert(0,'--Select--')
                self.data['file_list_df']["Table Code"] = pd.Categorical([], ordered=True, categories=table_code_categories)
                self.data["file_list_df"]["Template"] = pd.Categorical([],ordered=True,categories=get_immport_template_names())
                self.data["file_list_df"]["Default Visit"] = pd.Categorical([],ordered=True,categories=self.get_planned_visits(nameonly=True, returnType="list"))
                # unique_logging_buffer_load(message='categories created',level='info',flush=True)
                self.data["file_list_df"]["Filename"] = study_files
                # unique_logging_buffer_load(message='study_files loaded',level='info',flush=True)


                self.objects["study_file_table"] = self.generate_df_table()
                # unique_logging_buffer_load(message='Table Generated',level='info',flush=True)
                self.objects["button_generate_files"]= Button(text="Generate Filled Templates", tooltip='Generate filled ImmPort Templates for upload into ImmPort', callback=self.generate_filled_template_files) #, style=dict(description_width='initial'))
                #generate_filled_template_files
                self.objects["box_study_files_table"].set_children([ self.objects["button_generate_files"].get(), self.objects["study_file_table"]])
                self.objects["button_filechooser_study_file_directory_load"].button_change(button=self.objects["button_filechooser_study_file_directory_load"], style='success', text='Study Files Loaded',tooltip='The Study files have been loaded',disabled=False, icon='')
            except Exception as e:
                error = HTML(html_text='<b>Error:</b> ' + str(e))
                self.objects["box_study_files_table"].set_children([ error])

                raise Exception("Error loading study files: {}".format(e))

        return
    
    def on_select_study_tab_file(self, value, fc_field=None): 
        # global immport_data
        self.data["immport_data"]= {'tab_data':{},'config':{}}
        if value.description == "Change":
            immport_data["config"]["tabfile"]={
                "directory":self.objects["filechooser_study_tab_file"].selected_path,
                "file":self.objects["filechooser_study_tab_file"].selected_filename
            }
            self.data["immport_data"]["tab_data"]["planned_visits"] = cf.readFileFromZip(self.objects["filechooser_study_tab_file"].selected_path,self.objects["filechooser_study_tab_file"].selected_filename,"planned_visit.txt")
            self.data["immport_data"]["tab_data"]["study_files"] = cf.readFileFromZip(self.objects["filechooser_study_tab_file"].selected_path,self.objects["filechooser_study_tab_file"].selected_filename,"study_file.txt")
            study_info = cf.readFileFromZip(self.objects["filechooser_study_tab_file"].selected_path,self.objects["filechooser_study_tab_file"].selected_filename,"study.txt")
            self.data["immport_data"]["tab_data"]["study"] = study_info
            self.data["immport_data"]["study_id"]=study_info["STUDY_ACCESSION"][0]
            self.data["immport_data"]["workspace_id"]=study_info["WORKSPACE_ID"][0]
            
#            unique_logging_buffer_load(level="debug",message="display visits")  # Check
            visit_names = get_planned_visits(nameonly=True, returnType="list")
#            unique_logging_buffer_load(level="debug",message=f"visit names: {', '.join(visit_names)}")  # Check
            set_visit_dropdown(visit_names)

#            unique_logging_buffer_load(level="debug",message=f"display visits - Done")  # Check
#            unique_logging_buffer_flush()  # Check

    def get_study_id(self):
        return self.data["study"]["STUDY_ACCESSION"][0]

    def get_workspace_id(self):
        return self.data["study"]["WORKSPACE_ID"][0]


    def generate_df_table(self):
        global box, grid_body
        header_names =  self.data["file_list_df"].columns

        shape =  self.data["file_list_df"].shape

        column_widths = ["300px","100px","150px","125px","175px"]

        grid_header = widgets.GridspecLayout(shape[0], shape[1])
        grid_body = widgets.GridspecLayout(shape[0], shape[1])

        for idx, title in enumerate(header_names):
            grid_header[0,idx] = widgets.HTML(f"<b>{title}</b>")

            grid_header[0,idx].layout = widgets.Layout(width=column_widths[idx])
        
        dataframe_for_table =  self.data["file_list_df"].copy()
        dataframe_for_table = dataframe_for_table.astype('string')
        dataframe_for_table.fillna('', inplace=True)

        for ind in  self.data["file_list_df"].index:
            for idx, column_title in enumerate(header_names):
                readonly = (True if column_title == "Filename" else False)
                grid_body[ind, idx] = create_table_widget(dtype= self.data["file_list_df"][column_title].dtype, value=dataframe_for_table[column_title][ind], readonly= readonly, dataframe= self.data["file_list_df"],columnName=column_title)
                grid_body[ind, idx].layout = widgets.Layout(width=column_widths[idx])

                grid_body[ind, idx].description_tooltip=f"{{'row':{ind},'col':{idx}','title':'{column_title}'}}"

                grid_body[ind,idx].observe(functools.partial(update_dataframe_from_table, dataframe= self.data["file_list_df"], column_name=column_title,column=idx,row=ind), names='value')


        box_head = widgets.VBox([grid_header], layout=widgets.Layout(height='50px'))
        box_body = widgets.VBox([grid_body], layout=widgets.Layout(height='350px', overflow_y='auto'))
        box = widgets.VBox([box_head,box_body], layout=widgets.Layout(height='460px'))
        return box

        
    def load_data_dictionary_columns(self, b):
        # self.objects["button_form_column_confirm"].button_change(button=self.objects["button_form_column_confirm"], text='Confirmed')
        self.objects["button_form_column_confirm"].button_change(button=self.objects["button_form_column_confirm"], style='success', text='Confirmed',tooltip='The form columns have been loaded',disabled=True, icon='')
        
        dictionary_tables = list(self.dictionary['tables'].keys())
        self.objects["html_data_dictionary_tables"].set_text(text=f"{', '.join(dictionary_tables)}")
        
        return

    def generate_tab_data_dictionary(self):
        """Generate the data dictionary tab"""
        
        self.objects["filechooser_data_dictionary"] = File_Chooser(name="filechooser_data_dictionary", title='<b>Select the curated data dictionary</b>', tooltip='Load a curated data dictionary file',multiple=False,filter_pattern=['*.csv','*.txt',"*.tsv"], style=dict(description_width='initial'))
        
        #TODO work on Callback function
        self.objects["button_filechooser_data_dictionary_load"]= self.objects["filechooser_data_dictionary"].add_load_button(description="Load Data Dictionary", tooltip="Load a curated data dictionary file", callback=self.load_data_dictionary)
        # self.objects["button_filechooser_data_dictionary_load"].widget.on_click(self.load_data_dictionary)
        # self.objects["button_filechooser_data_dictionary_load"].widget.on_click(functools.partial(self.load_data_dictionary, self))
        # set on click function to load data dictionary
        # self.objects["button_filechooser_data_dictionary_load"]

        # self.objects["button_filechooser_data_dictionary_load"] = Button(text="Load Data Dictionary", tooltip='Load a curated data dictionary file', display=False) #, style=dict(description_width='initial'))
        # self.objects["button_data_dictionary_load"].toggle_display()
        # self.objects["button_data_dictionary_load"].set_onclick(self, callback_function=loadDataDictionary, callback_data = {})

        
        self.objects["button_form_column_confirm"]= Button(text="Confirm Form Columns", tooltip='Confirm that the selected column from the data dictionary contains the instrument/CRF/form codes', callback=self.load_data_dictionary_columns) #, style=dict(description_width='initial'))
        # self.objects["button_form_column_confirm"].widget.on_click(self.load_data_dictionary_columns)
        # self.objects["button_form_column_confirm"].set_callback(callback=self.load_data_dictionary_columns)

        self.objects["dropdown_table_form_column"] = Dropdown(options=[''], description='<b>Column specifying form/instrument:</b>', tooltip='Select the column from the data dictionary that contains the form codes', style=dict(description_width='initial'))

        self.objects["tab_row_dd_row"] = widgets.HBox([self.objects["filechooser_data_dictionary"].get(),self.objects["button_filechooser_data_dictionary_load"].get()])
        self.objects["tab_row_dd_form_row"] = widgets.HBox([self.objects["dropdown_table_form_column"].get(),self.objects["button_form_column_confirm"].get()])
        self.hide_row("tab_row_dd_form_row")

        # tab = widgets.VBox(layout=widgets.Layout(min_height="500px"))
        tab = widgets.VBox([self.objects["tab_row_dd_row"],self.objects["tab_row_dd_form_row"]])

        return tab
    
    def get_planned_visits(self, nameonly=False, returnType=None):
        
        if nameonly:
            # unique_logging_buffer_load(level="debug", message="\tName Only", flush=True)
            names = self.data["planned_visit"]["NAME"]
            if returnType == 'list':
                return names.tolist()
            return names
        return self.data["planned_visit"][["PLANNED_VISIT_ACCESSION","NAME"]]


    def toggle_show_hide(self, value, toggle):
        """Toggle the study immport tab"""
        for (key, element_list) in toggle.items():
            if key == value["new"]:
                for element in element_list:
                    self.show_hide_element(element, '')
            else:
                for element in element_list:
                    self.show_hide_element(element, 'none')

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

class Tab(GUI_Object):
    """Tab class"""
    def __init__(self, name, contents=None):
        self.name = name
        if contents is not None:
            if hasattr(contents, "widget"):
                self.widget = widgets.VBox([contents.widget])
            else:
                self.widget = widgets.VBox([contents])
        else:
            self.widget =widgets.VBox([])

class Button(GUI_Object):
    """Button class"""
    def __init__(self, text, style=None, icon="", tooltip="", state=False, callback=None, display=True):
        super().__init__(
            widgets.Button(
                description=text,
                icon=icon,
                tooltip=tooltip,
                layout=widgets.Layout(width="auto"),
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
    def __init__(self, options, value=None, description="", tooltip="", style=None):
        super().__init__(
            widgets.ToggleButtons(
                options=options,
                value=value,
                description=description,
                tooltip=tooltip,
                layout=widgets.Layout(width="auto"),
                style=style
            )
        )
    
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
        
        # self.widget.register_callback(button.show_hide_element('none'))
        self.load_button = button
        return button

    def on_select(self):        #If this is a directory only, then need different logic to show the button
        if hasattr(self, "load_button"):
            # if len(self.widget._filename.value)>0:
            if len(self.widget._selected_path)>0:
                self.load_button.show_hide_element('')
                self.load_button.widget.button_style='info'
            else:
                self.load_button.show_hide_element('none')

class Dropdown(GUI_Object):
    """Dropdown class"""
    def __init__(self, options, value=None, description='', callback=None, tooltip=None, style=dict(description_width='initial')):
        super().__init__(
            widgets.Dropdown(
                options=options,
                value=value,
                layout=widgets.Layout(width="auto"), #TODO
                description=description,
                style=style,
                tooltip=tooltip
            )
        )
        if callback is not None:
            self.widget.on_transition(callback)
    
    def set_options(self, option_list):
#        unique_logging_buffer_load(message="Setting Options",level='info',flush=True)  # Check
        # unique_logging_buffer_load(message=option_list,level='info',flush=True)
        try:
            self.widget.options = option_list
        except Exception as err:
            self.log(message="Error loading option list",level='info',flush=True)
#            unique_logging_buffer_load(message="Error loading option list",level='info',flush=True)  # Check
            # unique_logging_buffer_load(message=err,level='info',flush=True)

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

    def __init__(self, level=logging.DEBUG, name=__name__):
        super().__init__(
            widgets.Output(layout=widgets.Layout(max_height="525px", overflow_y="auto"))
        )
        self.messages={}
        # logging.basicConfig(stream=self.widget, level=level)

        self.logger = logging.getLogger(name)
        self.logger.setLevel(level)
        # self.logger.StreamHandler(handler=self.widget)
        self.logger.addHandler(log_viewer(output=self.widget,name=name))
        
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
    ##Add a button to clear the log
    ##Add a button to write from history with certain level

    def write(self,message=None, level=None, flush=False):
        
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

        for level in sorted(self.messages, key=lambda x: self.log_levels[x], reverse=True):
            for message, count in self.messages[level].items():
                # return
                if count == 1:
                    self.log[level](f"{message}")
                else:
                    self.log[level](f"({count}) {message}")

        self.messages={}

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


# logger = logging.getLogger(__name__)
# handler = OutputWidgetHandler()
# handler.setFormatter(logging.Formatter('%(asctime)s  - [%(levelname)s] %(message)s'))
# logger.addHandler(handler)
# logger.setLevel(logging.INFO)

########################################################################################################################

# widgets.Output(layout={'border': '1px solid black'})
# logging.basicConfig(stream=output2, level=logging.INFO)

# main_logger = logging.getLogger(__name__)
# main_logger.setLevel(logging.DEBUG)
# main_logger.addHandler(log_viewer())
immport_data = {'tab_data':{},'config':{}}

def unique_logging_buffer_load(message=None, level=None, flush=False):

    global logging_buffer_data
    if level not in logging_buffer_data:
        logging_buffer_data[level]={message:1}
    else:
        if message not in logging_buffer_data[level]:
            logging_buffer_data[level][message]=1
        else:
            logging_buffer_data[level][message]=logging_buffer_data[level][message]+1
    if flush:
        return
#        unique_logging_buffer_flush()  # Check

def unique_logging_buffer_flush():
    global logging_buffer_data

    log={
        "debug":main_logger.debug,
        "info":main_logger.info,
        "warning":main_logger.warning,
        "warn":main_logger.warning,
        "error":main_logger.error,
        "critical":main_logger.critical,
    }

    for level in logging_buffer_data.keys():
        for message, count in logging_buffer_data[level].items():
            log[level](f"({count}) - {message}")

    logging_buffer_data={}

def button_change(button=None, style=None, text=None, tooltip=None, icon=None, display=None, disabled=None):
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
    if button is None:
        return

    if style is not None:
        button.button_style = style
    if text is not None:
        button.description = text
    if tooltip is not None:
        button.tooltip = tooltip
    if icon is not None:
        button.icon = icon
    if disabled is not None:
        button.disabled = disabled
    if display is not None:
        button.layout.display = display

def reset_dd_form_row():
    button_change(button=button_confirm_form_column, text='Confirm Selection',style='',icon='',tooltip='Click to store values')
    show_hide_element(element=dd_form_row, display='none')

def reset_dd_load_button():
    button_change(button=button_data_dictionary_load, text='Load', style='',tooltip='Load Data Dictionary',display='')

def reset_sf_dir_load_button():
    button_change(button=button_study_file_directory_load, text='Confirm Selection', style='',tooltip='',display='')

def test_function_notify(value):
    """Helper function to test actions

    Args:
        value (any): Anything to echo out
    """
    with output2:
        print("test notification",value)

def show_hide_element(element=None, display=None):
    """Helper function to show or hide an element

    Args:
        element (widget.*, required): widget element. Defaults to None.
        display (text, optional): ['','none','inline']. Defaults to None.
    """
    if element is None or display is None:
        return
    element.layout.display=display

def change_notify_text(element=None, text=None):
    """Helper function to change notification text - archive?

    Args:
        element (_type_, optional): _description_. Defaults to None.
        text (_type_, optional): _description_. Defaults to None.
    """
    if element is not None and text is not None:
        element.value = text

def loadDataDictionary(value):
    global dictionary
    global immport_data

    reset_dd_form_row()
    button_change(button=button_data_dictionary_load, style='info', text='Loading',tooltip='hi there',disabled=False, icon='spinner')     # 'success', 'info', 'warning', 'danger' or ''
    
    immport_data["config"]["data_dictionary"]={
        "directory":fc_data_dictionary._pathlist.value,
        "filename":fc_data_dictionary._filename.value
    }
    data_dictionary_path = f'{fc_data_dictionary._pathlist.value}/{fc_data_dictionary._filename.value}'
    try: #This is not adequately catching errors in parsing the data dictionary
        dictionary = rc.parseDataDictionary(data_dictionary_path)
    except:
        button_change(button=button_data_dictionary_load, style='danger', text='Load Failed',tooltip='',disabled=False, icon='')     # 'success', 'info', 'warning', 'danger' or ''
        show_hide_element(element=dd_form_row, display='none')
        change_notify_text(element=text_study_files_notify_dd_selection, text='Load Dictionary File to continue...')

    change_notify_text(element=text_study_files_notify_dd_selection, text='Select Table/Form Column from Data Dictionary...')

    button_change(button=button_data_dictionary_load, style='success', text='Dictionary Loaded',tooltip='Click to Reload Dictionary',disabled=False, icon='')     # 'success', 'info', 'warning', 'danger' or ''
    table_columns = dictionary['columns']
    table_column_titles = list(map(lambda x: x.lower(), table_columns.keys()))
    dropdown_table_form_column.options = list(table_columns.items())
    for field in ['form','table name','table','form name']:
        if field in table_column_titles:
            dropdown_table_form_column.value = dropdown_table_form_column.options[table_column_titles.index(field)][1]
            break
    show_hide_element(element=dd_form_row, display='')

    return dictionary

def loadDDColumnNames(value): 
    button_change(button=value, text='Confirmed',icon='check',style='success')
    dictionary_tables = get_data_dictionary_tables()
    if dictionary_tables[0] == '--Select--':
        dictionary_tables.pop(0)
    change_notify_text(element=text_study_files_notify_dd_selection, text=f"<b>Tables Listed in Dictionary:</b> {', '.join(dictionary_tables)}")

def on_data_dictionary_select(change):
    if change['new'] and len(change['new'])>0:
        reset_dd_load_button()
    else:
        show_hide_element(element=button_data_dictionary_load,display='none')
#    unique_logging_buffer_load(level="debug",message=f"On data dictionary select:{change}")  # Check
#    unique_logging_buffer_flush()  # Check

def on_study_file_select(value):
    global box_study_file_table
    global file_list_df
#    unique_logging_buffer_load(level="debug",message=f"on_study_file_select{value}")  # Check


    if value.description == "Change":
        box_study_file_table.children = ([widgets.HTML(r'Generating Study File Table...')])
        generate_study_file_table()
        reset_sf_dir_load_button()
#        unique_logging_buffer_load(level="debug",message=f"Generate DF table")  # Check
        study_file_table_widget = generate_df_table(dataframe=file_list_df)
        box_study_file_table.children = ([study_file_table_widget])
#    unique_logging_buffer_flush()  # Check


def process_study_file_directory():
    return
#    unique_logging_buffer_load(level="debug",message=fc_study_file_directory)  # Check
#    unique_logging_buffer_flush()  # Check


def generate_tab_study_files():
    global text_study_files_notify_dd_selection, fc_study_file_directory, box_study_file_table,button_study_file_directory_load
    
    fc_study_file_directory = FileChooser('./',)
    fc_study_file_directory.layout=widgets.Layout(width='700px')

    fc_study_file_directory.show_only_dirs = True
    button_study_file_directory_load = widgets.Button()
    reset_sf_dir_load_button()
    button_study_file_directory_load.on_click(process_study_file_directory)

    dataFiles_row = widgets.HBox([widgets.HTML(value = f"<b>Study File Directory:</b>"), fc_study_file_directory])

    text_study_files_notify_dd_selection = widgets.HTML(value = f"Load Dictionary File to continue...")
    box_study_file_table =widgets.HBox()
    box = widgets.VBox([dataFiles_row,text_study_files_notify_dd_selection,box_study_file_table])
    box.layout = widgets.Layout(width='925px')
    fc_study_file_directory._select.on_click(on_study_file_select)

    return box

def generate_tab_data_dictionary():
    global fc_data_dictionary, button_data_dictionary_load, button_confirm_form_column, dropdown_table_form_column, dd_row, dd_form_row, box

    fc_data_dictionary = FileChooser('./')
    fc_data_dictionary.layout=widgets.Layout(width='700px')
    fc_data_dictionary.filter_pattern = ['*.txt', '*.csv', '*.tsv']

    button_data_dictionary_load = widgets.Button()
    reset_dd_load_button()

    button_confirm_form_column = widgets.Button()

    dropdown_table_form_column = widgets.Dropdown(
        options=[''],
        value='',
        description='',
        disabled=False,
    )

    show_hide_element(element=button_data_dictionary_load, display='none')

    dd_row = widgets.HBox([widgets.HTML(value = f"<b>Data Dictionary:</b>"), fc_data_dictionary,button_data_dictionary_load])
    dd_form_row = widgets.HBox([widgets.HTML(value = f"<b>Table/Form Column:</b>"), dropdown_table_form_column,button_confirm_form_column])
    
    
    button_data_dictionary_load.on_click(loadDataDictionary)
    button_confirm_form_column.on_click(loadDDColumnNames)

    reset_dd_form_row()

    #todo: to implement dd_form_row, parsing of the data dictionary needs to change as it assumes the table/form column name is "Table Name"
    box = widgets.VBox([dd_row,dd_form_row])

    fc_data_dictionary._filename.observe(on_data_dictionary_select, 'value')
    return box

def get_immport_template_names():
    return ['--Select--',"Assessment"]

def get_data_dictionary_tables():
    my_list = list(dictionary["tables"].keys())
    my_list.insert(0,'--Select--')
    return my_list

def generate_study_file_table():
    global study_file_list, file_list_df
    study_file_list = []
    file_list_df=""

    included_extensions = ['txt','csv', 'tsv']
    if os.path.isdir(fc_study_file_directory.value):
        study_file_list = [fn for fn in os.listdir(fc_study_file_directory.value)
                if any(fn.endswith(ext) for ext in included_extensions)]

        study_file_list.sort()
        file_list_df = pd.DataFrame(columns=['Filename','Table Code','Assessment Name','Template','Default Visit'])
        file_list_df["Table Code"] = pd.Categorical([], ordered=True, categories=get_data_dictionary_tables())
        file_list_df["Template"] = pd.Categorical([], ordered=True, categories=get_immport_template_names())
        planned_visit_list = get_planned_visits(nameonly=True, returnType="list")
        file_list_df["Default Visit"]=pd.Categorical([],ordered=True, categories=planned_visit_list)
        file_list_df["Filename"]=study_file_list

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

def generate_df_table(dataframe=None):
    global box, grid_body
    header_names = dataframe.columns

    shape = dataframe.shape

    column_widths = ["300px","100px","150px","125px","175px"]

    grid_header = widgets.GridspecLayout(shape[0], shape[1])
    grid_body = widgets.GridspecLayout(shape[0], shape[1])

    for idx, title in enumerate(header_names):
        grid_header[0,idx] = widgets.HTML(f"<b>{title}</b>")

        grid_header[0,idx].layout = widgets.Layout(width=column_widths[idx])
    
    dataframe_for_table = dataframe.copy()
    dataframe_for_table = dataframe_for_table.astype('string')
    dataframe_for_table.fillna('', inplace=True)

    for ind in dataframe.index:
        for idx, column_title in enumerate(header_names):
            readonly = (True if column_title == "Filename" else False)
            grid_body[ind, idx] = create_table_widget(dtype=dataframe[column_title].dtype, value=dataframe_for_table[column_title][ind], readonly= readonly, dataframe=dataframe,columnName=column_title)
            grid_body[ind, idx].layout = widgets.Layout(width=column_widths[idx])

            grid_body[ind, idx].description_tooltip=f"{{'row':{ind},'col':{idx}','title':'{column_title}'}}"

            grid_body[ind,idx].observe(functools.partial(update_dataframe_from_table, dataframe=dataframe, column_name=column_title,column=idx,row=ind), names='value')


    box_head = widgets.VBox([grid_header], layout=widgets.Layout(height='50px'))
    box_body = widgets.VBox([grid_body], layout=widgets.Layout(height='350px', overflow_y='auto'))
    box = widgets.VBox([box_head,box_body], layout=widgets.Layout(height='460px'))
    return box

def generate_gui():
    global output2
    tab_contents = ['Study','Data Dictionary', 'Study Files',"Debug"]
    output2 = widgets.Output(layout=widgets.Layout(max_height="425px", overflow_y="auto"))
    children = [generate_tab_study_info(),generate_tab_data_dictionary(),generate_tab_study_files(),output2]
    tab = widgets.Tab(layout=widgets.Layout(min_height="500px"))
    tab.children = children
    for idx, title in enumerate(tab_contents):
        tab.set_title(idx, title)
    return tab

def toggle_study_immport(value,show_if_true=[],hide_if_true=[]):
    if value["new"]:
        elements_to_show = show_if_true
        elements_to_hide = hide_if_true
    else:
        elements_to_show = hide_if_true
        elements_to_hide = show_if_true

    for element in elements_to_show:
        show_hide_element(element=element, display='')

    for element in elements_to_hide:
        show_hide_element(element=element, display='none')

def on_select_study_tab_file2(value, gui=None, fc_name=None):
    if value.description == "Change":
        # gui.data["path"]=gui.objects[fc_name].widget.selected_path
        # gui.data["filename"]=gui.objects[fc_name].widget.selected_filename
        gui.data["planned_visit"] = cf.readFileFromZip( gui.objects[fc_name].widget.selected_path, gui.objects[fc_name].widget.selected_filename, "planned_visit.txt")
        gui.data["study_files"] = cf.readFileFromZip(   gui.objects[fc_name].widget.selected_path, gui.objects[fc_name].widget.selected_filename, "study_file.txt")
        gui.data["study"] = cf.readFileFromZip(         gui.objects[fc_name].widget.selected_path, gui.objects[fc_name].widget.selected_filename, "study.txt")

        # # unique_logging_buffer_load(level="debug",message="display visits")
        visit_names = get_planned_visits2(gui.data["planned_visit"],nameonly=True, returnType="list")
        # # unique_logging_buffer_load(level="debug",message=f"visit names: {', '.join(visit_names)}")
        
        # ## TODO
        gui.objects["dropdown_study_visit_list"].set_options(visit_names)

        # # unique_logging_buffer_load(level="debug",message=f"display visits - Done")
        # # unique_logging_buffer_flush()

#Refactored: Can remove at end of refactoring
def on_select_study_tab_file(value, fc_field=None): 
    global immport_data
    if value.description == "Change":
        immport_data["config"]["tabfile"]={
            "directory":fc_immport_study_tab_file.selected_path,
            "file":fc_immport_study_tab_file.selected_filename
        }
        immport_data["tab_data"]["planned_visits"] = cf.readFileFromZip(fc_immport_study_tab_file.selected_path,fc_immport_study_tab_file.selected_filename,"planned_visit.txt")
        immport_data["tab_data"]["study_files"] = cf.readFileFromZip(fc_immport_study_tab_file.selected_path,fc_immport_study_tab_file.selected_filename,"study_file.txt")
        study_info = cf.readFileFromZip(fc_immport_study_tab_file.selected_path,fc_immport_study_tab_file.selected_filename,"study.txt")
        immport_data["tab_data"]["study"] = study_info
        immport_data["study_id"]=study_info["STUDY_ACCESSION"][0]
        immport_data["workspace_id"]=study_info["WORKSPACE_ID"][0]
        
#        unique_logging_buffer_load(level="debug",message="display visits")  # Check
        visit_names = get_planned_visits(nameonly=True, returnType="list")
#        unique_logging_buffer_load(level="debug",message=f"visit names: {', '.join(visit_names)}")  # Check
        set_visit_dropdown(visit_names)

#        unique_logging_buffer_load(level="debug",message=f"display visits - Done")  # Check
#        unique_logging_buffer_flush()  # Check

def getStudyFileReportedName(studyfileName):
    global immport_data
    return immport_data["tab_data"]["study_files"][immport_data["tab_data"]["study_files"]["FILE_NAME"] == studyfileName]["DESCRIPTION"].values[0]

def display_visits(visit_data):
    w_study_visit_text.value = visit_data

def create_visit_dropdown(data=None, add_select=False):
    options = data;
    if add_select:
        if(type(options[0]) == str):
            options.insert(0,"--Select--")
        else:
            options.insert(0,("--Select--",""))

#Refactored: Can remove at end of refactoring
def set_visit_dropdown(visit_data): 
    w_study_visit_dropdown.options = visit_data

def generate_tab_study_info():
    global study_data, fc_immport_study_tab_file, w_study_visit_text, w_study_visit_dropdown

    ## Not Needed
    w_study_visit_text = widgets.HTML(
        layout=widgets.Layout(width='700px'),
        description='<b>Visit List:</b>',
    )

    w_study_visit_dropdown = create_visit_dropdown(data=[''], description = "<b> Visit List:</b>")

    w_study_visit_dropdown.layout=widgets.Layout(width='700px')

    w_study_immport_boolean = widgets.ToggleButtons(
        options=[('Yes',1),('No',0)],
        description='Current ImmPort Study:',
        description_tooltip='Is this study a current ImmPort study?',
        style=dict(description_width='initial')
    )

    w_immport_study_id = widgets.IntText(   #TODO: Delete this
        description='Immport Study ID:',
        style=dict(description_width='initial'),
        disabled=True
    )

    w_immport_workspace_id = widgets.IntText(      #TODO: Delete this
        description='Immport Workspace ID:',
        style=dict(description_width='initial'),
        disabled=True
    )

    fc_immport_study_tab_file = FileChooser(
        './',
        title='<b>Select the ImmPort Study Tab zip file:</b>'
    )
    
    fc_immport_study_tab_file.layout=widgets.Layout(width='700px')
    fc_immport_study_tab_file.filter_pattern = ['*.zip']
    w_immport_study_tab_file_status = widgets.HTML()
    fc_immport_study_tab_file._select.on_click(functools.partial(self.on_select_study_tab_file, fc_field=fc_immport_study_tab_file))

    box_immport_study_yes = widgets.VBox([fc_immport_study_tab_file,w_immport_study_tab_file_status])
    box_immport_study_no = widgets.VBox([])
    box_immport_study = widgets.VBox([w_study_immport_boolean,box_immport_study_yes,box_immport_study_no,w_study_visit_dropdown])

    #Need to add this
    w_study_immport_boolean.observe(functools.partial(toggle_study_immport,show_if_true=[box_immport_study_yes], hide_if_true=[]), names='value')

    return box_immport_study

def get_planned_visits2(planned_visits, nameonly=False, returnType=None):
    
    if nameonly:
#        unique_logging_buffer_load(level="debug", message="\tName Only", flush=True)  # Check
        names = planned_visits["NAME"]
        if returnType == 'list':
            return names.tolist()
        return names
    return planned_visits[["PLANNED_VISIT_ACCESSION","NAME"]]

def get_planned_visits(nameonly=False, returnType=None):
    
    if nameonly:
#        unique_logging_buffer_load(level="debug", message="\tName Only", flush=True)  # Check
        names = immport_data['tab_data']["planned_visits"]["NAME"]
        if returnType == 'list':
            return names.tolist()
        return names
    return immport_data['tab_data']["planned_visits"][["PLANNED_VISIT_ACCESSION","NAME"]]


def create_visit_dropdown(data=None, add_select=False,description=None):
    options = data;
    if add_select:
        if(type(options[0]) == str):
            options.insert(0,"--Select--")
        else:
            options.insert(0,("--Select--",""))
    
    if(type(options[0]) == str):
        value = options[0]
    else:
        value = options[0][1]

    v_dropdown = widgets.Dropdown(
        options=options,
        value=value
    )

    if description is not None:
        v_dropdown.description=description
        v_dropdown.style=style=dict(description_width='initial')

    return v_dropdown

























