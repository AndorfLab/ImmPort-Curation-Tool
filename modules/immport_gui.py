import pandas as pd
import os

from modules import processRedCapFiles as rc
from modules import curationFunctions as cf
from modules import analysisFunctions as af

import ipywidgets as widgets
from ipyfilechooser import FileChooser

import functools


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

    # dd_form_row.layout.display=''
    with output2:
        print(data_dictionary_path)
        print(dictionary)
        print(value)
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
    test_function_notify(f"On data dictionary select:{change}")



def on_study_file_select(value):
    global box_study_file_table
    global file_list_df
    test_function_notify(f"on_study_file_select{value}")
    # test_function_notify("Study File Directory:")
    # if value["description"] == "Change":
    if value.description == "Change":
        box_study_file_table.children = ([widgets.HTML(r'Generating Study File Table...')])

        # test_function_notify(value)
        # test_function_notify(f"Study File Directory:{fc_study_file_directory.selected}")

        # test_function_notify("Generate Study File Table")
        generate_study_file_table()
        # test_function_notify("Reset DD load Button")
        reset_sf_dir_load_button()
        test_function_notify("Generate DF table")
        study_file_table_widget = generate_df_table(dataframe=file_list_df)
        test_function_notify(box_study_file_table)
        test_function_notify(box_study_file_table.children)
        test_function_notify("Generate DF table2")
        box_study_file_table.children = ([study_file_table_widget])
        test_function_notify(box_study_file_table.children)

    # else:
        # show_hide_element(element=button_data_dictionary_load,display='none')
    # test_function_notify(change)

def process_study_file_directory():
    test_function_notify(fc_study_file_directory.value)


def generate_tab_study_files():
    global text_study_files_notify_dd_selection, fc_study_file_directory, box_study_file_table,button_study_file_directory_load
    
    fc_study_file_directory = FileChooser('./',)
    fc_study_file_directory.show_only_dirs = True
    button_study_file_directory_load = widgets.Button()
    reset_sf_dir_load_button()
    # show_hide_element(element=button_study_file_directory_load, display='none')
    button_study_file_directory_load.on_click(process_study_file_directory)

    dataFiles_row = widgets.HBox([widgets.HTML(value = f"<b>Study File Directory:</b>"), fc_study_file_directory])
    # dataFiles_row = widgets.HBox([widgets.HTML(value = f"<b>Study File Directory:</b>"), fc_study_file_directory,button_study_file_directory_load])

    text_study_files_notify_dd_selection = widgets.HTML(value = f"Load Dictionary File to continue...")
    # box_study_file_table =widgets.HBox([widgets.HTML(value='Placeholder')])
    box_study_file_table =widgets.HBox()
    box = widgets.VBox([dataFiles_row,text_study_files_notify_dd_selection,box_study_file_table])
    box.layout = widgets.Layout(width='925px')
    # fc_study_file_directory._select.on_click(test_function_notify)
    fc_study_file_directory._select.on_click(on_study_file_select)

    return box

# box = generate_tab_study_files()
# display(box)

def generate_tab_data_dictionary():
    global fc_data_dictionary, button_data_dictionary_load, button_confirm_form_column, dropdown_table_form_column, dd_row, dd_form_row, box

    fc_data_dictionary = FileChooser('./')
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

# box = generate_tab_data_dictionary()
# display(box)

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
    # test_function_notify("a")
    if os.path.isdir(fc_study_file_directory.value):
        # test_function_notify("b")
        study_file_list = [fn for fn in os.listdir(fc_study_file_directory.value)
                if any(fn.endswith(ext) for ext in included_extensions)]

        # test_function_notify("c")

        study_file_list.sort()
        file_list_df = pd.DataFrame(columns=['Filename','Table Code','Assessment Name','Template','Default Visit'])
        file_list_df["Table Code"] = pd.Categorical([], ordered=True, categories=get_data_dictionary_tables())
        file_list_df["Template"] = pd.Categorical([], ordered=True, categories=get_immport_template_names())
        file_list_df["Filename"]=study_file_list

def update_dataframe_from_table(value,row=None, column=None, column_name=None, dataframe=None):
    if dataframe is None:
        return
    dataframe.at[row,column_name]=value['new']
    # with output2:
        # print(str(column), str(row), column_name, value['new'])

def create_table_widget(dtype=None, value='', readonly=False, dataframe=None, columnName=None):
    if readonly:
        return widgets.Label(value=value)
    elif dtype == "object":
        return widgets.Text(value=value,
            placeholder='',
            disabled=readonly)
        # template_data_row..append(my_cell_widget)
    elif dtype == "category":
        if value=='':
            value = '--Select--'
        return widgets.Dropdown(
            options=dataframe[columnName].cat.categories,
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
        # grid_header[0,idx] = widgets.Label(title)
        grid_header[0,idx] = widgets.HTML(f"<b>{title}</b>")

        grid_header[0,idx].layout = widgets.Layout(width=column_widths[idx])
    
    dataframe_for_table = dataframe.copy()
    dataframe_for_table = dataframe_for_table.astype('string')
    dataframe_for_table.fillna('', inplace=True)

    for ind in dataframe.index:
    # for ind in range(5):
        # this_row = template_data_row.copy()
        for idx, column_title in enumerate(header_names):
            readonly = (True if column_title == "Filename" else False)
            grid_body[ind, idx] = create_table_widget(dtype=dataframe[column_title].dtype, value=dataframe_for_table[column_title][ind], readonly= readonly, dataframe=dataframe,columnName=column_title)
            grid_body[ind, idx].layout = widgets.Layout(width=column_widths[idx])

            grid_body[ind, idx].description_tooltip=f"{{'row':{ind},'col':{idx}','title':'{column_title}'}}"

            grid_body[ind,idx].observe(functools.partial(update_dataframe_from_table, dataframe=dataframe, column_name=column_title,column=idx,row=ind), names='value')
            # grid_body[row,column].observe(functools.partial(update_dataframe_from_table, dataframe=dataframe, column_name=title,column=idx,row=ind), names='value')


    box_head = widgets.VBox([grid_header], layout=widgets.Layout(height='50px'))
    box_body = widgets.VBox([grid_body], layout=widgets.Layout(height='350px', overflow_y='auto'))
    box = widgets.VBox([box_head,box_body], layout=widgets.Layout(height='460px'))
    # display(box)
    return box
    #Create Template Row


def generate_gui():
    global output2
    tab_contents = ['Data Dictionary', 'Study Files',"Debug"]
    output2 = widgets.Output(layout=widgets.Layout(max_height="425px", overflow_y="auto"))
    children = [generate_tab_data_dictionary(),generate_tab_study_files(),output2]
    tab = widgets.Tab(layout=widgets.Layout(min_height="500px"))
    tab.children = children
    for idx, title in enumerate(tab_contents):
        # print(idx,title)
        tab.set_title(idx, title)
    return tab































