from IPython.display import HTML
import pandas as pd

# Define the CSS to make the header sticky and the table scrollable
sticky_header_css = """
<style>
    .sticky-header th {
        position: sticky;
        top: 0;
        background-color: white;  /* Ensure the header has a background color */
        z-index: 1;  /* Ensure the header stays above the table content */
    }
    .scrollable-table {
        max-height: 300px;  /* Set the maximum height for the scrollable area */
        overflow-y: auto;   /* Enable vertical scrolling */
        display: block;
    }
</style>
"""

# Display the CSS in the notebook
display(HTML(sticky_header_css))

# Example DataFrame
data = {
    "Column 1": [1, 2, 3, 4, 5],
    "Column 2": ["A", "B", "C", "D", "E"],
    "Column 3": [10.5, 20.5, 30.5, 40.5, 50.5]
}
df = pd.DataFrame(data)

# Convert the DataFrame to an HTML table and add the sticky-header class
html_table = df.to_html(classes="sticky-header", index=False)

# Wrap the table in a scrollable container
scrollable_table = f"""
<div class="scrollable-table">
    {html_table}
</div>
"""

# Display the scrollable table in the notebook
display(HTML(scrollable_table))