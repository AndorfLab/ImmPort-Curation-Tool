# Study File format
This tool accepts a common format exported by most Clinical or Research data collection systems. This format is a tab separated, record table where each row is the data collected from a single assessment for an individual at a given event. 

## An example of a study file:
| Accession | VISIT | GENDER | HEIGHTCM | WEIGHTKG | PREG | ALEGG | ALMILK | ALLATEX |
| --------- | ----- | ------ | -------- | -------- | ---- | ----- | ------ | ------- | 
| SUB000001 | 2     | 0      | 165      | 77       | 99   | 1     | 1      | 1       |
| SUB000002 | 2     | 1      | 161      | 65       | 0    | 0     | 1      | 0       |
| SUB000003 | 2     | 1      | 156      | 62       | 0    | 0     | 0      | 1       |
| SUB000004 | 2     | 0      | 172      | 83       | 99   | 1     | 0      | 1       |
| SUB000001 | 3     | 0      | 165      | 75       | 99   | 1     | 1      | 0       |
| SUB000002 | 3     | 1      | 161      | 66       | 0    | 0     | 1      | 1       |


## Subject Identifier Column
The column used to identify the subject should have a column heading of "User Defined ID" or "Accession".

## Visit Column
Often a visit column is present to specify which study visit the data should be attributed to. If this is not present, a default visit for the entire study file can be specified in the curation tool. If the study file contains information from multiple visits, a visit column is required.

## Data Columns
The other columns in the file are often data columns that correspond to the questions asked on the eCRF.


