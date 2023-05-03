# Frequently Asked Questions

## Study Day: What is the difference between using the "Study Day" value in "Column Mappings", using the "Study Day" column, and using the "Age at Onset Reported" columns?

The Immport Assessment Template has two separate "Date" fields: Study Day, Age at Onset Reported/Age at Onset Unit. The Study Day field specifies the study day value for a given question. For most questions/values, this is the day of the study visit. In this case, you want to use the value of "Study Day" in the "Column Mapping" column of the data dictionary that corresponds to the question that holds the study day value. This will ensure that ALL fields from that form/instrument/panel use this value.

There are excepts where the question is asking about prior events. For instance, there might be a question of (HEADACHE)"Have you had a headache since your last visit". This might be accompanied by a follow-up question of (HEADACHE_DT) "What was the date of your last headache?" This value, in study days, can be used to populate the study day value of the first question (HEADACHE) by specifying "HEADACHE_DT" in the "Study Day" column for question "HEADACHE".

Finally, sometimes the questions are (DIABETES) "Do you have type II diabetes?" and (DIABETES_DT) "At what age were you diagnosed with diabetes?" In this case, you would use "DIABETES_DT" in the "Study Day Onset" column to specify the age of onset for this disease/condition.

