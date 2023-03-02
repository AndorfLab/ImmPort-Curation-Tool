# Study File format
This tool accepts a common format exported by most Clinical or Research data collection systems. This format is a tab separated, record table where each row is the data collected from a single assessment for an individual at a given event. 

## An example of a study file:
| PATID     | VISIT | GENDER | HEIGHTCM | WEIGHTKG | PREG | ALEGG | ALMILK | ALLATEX | DATE |
| --------- | ----- | ------ | -------- | -------- | ---- | ----- | ------ | ------- | ---- |
| SUB000001 | 1     | 0      | 165      | 77       | 99   | 1     | 1      | 1       | 7    |
| SUB000002 | 1     | 1      | 161      | 65       | 0    | 0     | 1      | 0       | 7    |
| SUB000003 | 1     | 1      | 156      | 62       | 0    | 0     | 0      | 1       | 8    |
| SUB000004 | 1     | 0      | 172      | 83       | 99   | 1     | 0      | 1       | 7    |
| SUB000001 | 2     | 0      | 165      | 75       | 99   | 1     | 1      | 0       | 9    |
| SUB000002 | 2     | 1      | 161      | 66       | 0    | 0     | 1      | 1       | 7    |


## Subject Identifier Column
The column used to identify the subject. This column will be specified in the Data Dictionary column "Column Mappings" as "User Defined ID"

## Visit Column
Often a visit column is present to specify which study visit the data should be attributed to. If this is not present, a default visit for the entire study file can be specified in the curation tool. If the study file contains information from multiple visits, a visit column is required.

## Data Columns
The other columns in the file are often data columns that correspond to the questions asked on the eCRF.

## Study Days
If you have a column that contains dates, for instance the date of the visit or date of an event, these need to be transformed to a "Study Day". The Study Day is normally calculated based on a participants enrollment, screening visit, or first treatment, as defined in the study protocol. The value is the number of days since a given event (e.g. enrollment), and can be positive or negative numbers.
