import pandas as pd
import os

from modules import processRedCapFiles as rc
from modules import curationFunctions as cf
from modules import analysisFunctions as af
from modules import schemaFunctions as sf

import ipywidgets as widgets
from ipyfilechooser import FileChooser

import functools
import logging
logging_buffer_data = {}

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
    logger_instance = logging.getLogger("__name__")

    def __init__(self, *args, **kwargs):
         # Initialize the Handler
         logging.Handler.__init__(self, *args)

         # optional take format
         # setFormatter function is derived from logging.Handler
         for key, value in kwargs.items():
             if "{}".format(key) == "format":
                 self.setFormatter(value)

         # make the logger send data to this class
         self.logger_instance.addHandler(self)
         self.setFormatter(CustomFormatter(self.fmt))

    def emit(self, record):
        """ Overload of logging.Handler method """
        record = self.format(record)
        with output2:
            print(record)


# logging.basicConfig(stream=output2, level=logging.INFO)

main_logger = logging.getLogger(__name__)
main_logger.setLevel(logging.DEBUG)
main_logger.addHandler(log_viewer())
immport_data = {'tab_data':{}}

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
        unique_logging_buffer_flush()

def unique_logging_buffer_flush():
    global logging_buffer_data

    log={
        "info":main_logger.info,
        "warning":main_logger.warning,
        "warn":main_logger.warning,
        "debug":main_logger.debug,
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
    reset_dd_form_row()
    button_change(button=button_data_dictionary_load, style='info', text='Loading',tooltip='hi there',disabled=False, icon='spinner')     # 'success', 'info', 'warning', 'danger' or ''
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
    unique_logging_buffer_load(level="debug",message=f"On data dictionary select:{change}")
    unique_logging_buffer_flush()

def on_study_file_select(value):
    global box_study_file_table
    global file_list_df
    unique_logging_buffer_load(level="debug",message=f"on_study_file_select{value}")


    if value.description == "Change":
        box_study_file_table.children = ([widgets.HTML(r'Generating Study File Table...')])
        generate_study_file_table()
        reset_sf_dir_load_button()
        unique_logging_buffer_load(level="debug",message=f"Generate DF table")
        study_file_table_widget = generate_df_table(dataframe=file_list_df)
        box_study_file_table.children = ([study_file_table_widget])
    unique_logging_buffer_flush()


def process_study_file_directory():
    unique_logging_buffer_load(level="debug",message=fc_study_file_directory)
    unique_logging_buffer_flush()


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

def on_select_study_tab_file(value, fc_field=None):
    global immport_data
    if value.description == "Change":
        immport_data["tab_data"]["planned_visits"] = cf.readFileFromZip(fc_immport_study_tab_file.selected_path,fc_immport_study_tab_file.selected_filename,"planned_visit.txt")
        immport_data["tab_data"]["study_files"] = cf.readFileFromZip(fc_immport_study_tab_file.selected_path,fc_immport_study_tab_file.selected_filename,"study_file.txt")
        study_info = cf.readFileFromZip(fc_immport_study_tab_file.selected_path,fc_immport_study_tab_file.selected_filename,"study.txt")
        immport_data["tab_data"]["study"] = study_info
        immport_data["study_id"]=study_info["STUDY_ACCESSION"][0]
        immport_data["workspace_id"]=study_info["WORKSPACE_ID"][0]
        
        unique_logging_buffer_load(level="debug",message="display visits")
        visit_names = get_planned_visits(nameonly=True, returnType="list")
        unique_logging_buffer_load(level="debug",message=f"visit names: {', '.join(visit_names)}")
        set_visit_dropdown(visit_names)

        unique_logging_buffer_load(level="debug",message=f"display visits - Done")
        unique_logging_buffer_flush()

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


def set_visit_dropdown(visit_data):
    w_study_visit_dropdown.options = visit_data

def generate_tab_study_info():
    global study_data, fc_immport_study_tab_file, w_study_visit_text, w_study_visit_dropdown

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

    w_immport_study_id = widgets.IntText(
        description='Immport Study ID:',
        style=dict(description_width='initial'),
        disabled=True
    )

    w_immport_workspace_id = widgets.IntText(
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
    fc_immport_study_tab_file._select.on_click(functools.partial(on_select_study_tab_file, fc_field=fc_immport_study_tab_file))

    box_immport_study_yes = widgets.VBox([fc_immport_study_tab_file,w_immport_study_tab_file_status])
    box_immport_study_no = widgets.VBox([])
    box_immport_study = widgets.VBox([w_study_immport_boolean,box_immport_study_yes,box_immport_study_no,w_study_visit_dropdown])

    w_study_immport_boolean.observe(functools.partial(toggle_study_immport,show_if_true=[box_immport_study_yes], hide_if_true=[]), names='value')

    return box_immport_study

def get_planned_visits(nameonly=False, returnType=None):
    
    if nameonly:
        unique_logging_buffer_load(level="debug", message="\tName Only", flush=True)
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

























