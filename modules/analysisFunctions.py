import pandas as pd
import json

def updateTable(table,update):
    for index,row in update.iterrows():
        subset = (table[row['IF_COLUMN_NAME']].str.contains(row["IF_COLUMN_VALUE"], na=False))
        table.loc[subset, row['THEN_COLUMN_NAME']]=row["THEN_COLUMN_VALUE"]

def updateTableMultiple(table,update): # processes a 2-row dataset of conditions/values containing key/value pairs of columns/data; with the conditions column being a regex
#TODO: Update to allow value to be a regex with capture group, or some other function i.e. replace
# CONDITIONS	VALUES
# {"Protocol":"^6602$","local_id":"^WSU-75553$"}	{"Participant_id":"105852","local_id":"WSU-75553-0001"}
    for index,row in update.iterrows():
        if_conditions = json.loads(row["CONDITIONS"])

        my_df = pd.DataFrame(table.any(axis='columns'))
        for col,value in if_conditions.items():
            my_df[col] = table[col].astype(str).str.contains(str(value),na=False)

        my_df['all'] = my_df.all(axis='columns')
        
        values = json.loads(row["VALUES"])
        for col,value in values.items():
            table.loc[my_df.all(axis=1),col]=value

def showRelevantColumns(dataframe):
    df=dataframe.copy(deep=True)
    for col in ["RESULT_SCHEMA","WORKSPACE_ID_x","ASSESSMENT_COMPONENT_ACCESSION","SUBJECT_ACCESSION"]:
        df.drop(col,axis=1,inplace=True, errors='ignore')
    column_values = df.any().to_frame().copy()
    column_values.reset_index(level=0, inplace=True)
    column_values.columns=["column","HasValues"]
    my_column_list = column_values[column_values["HasValues"]==True]["column"]

    return dataframe[dataframe.columns.intersection(my_column_list)]
    
