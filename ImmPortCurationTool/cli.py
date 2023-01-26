# from ImmPortCurationTool.version import VERSION, PACKAGE_NAME
import os
import click
from random import randrange

@click.group()
def cli():
    pass

@cli.command(name='notebook')
@click.option("-n","--notebook", 'filename', help="Name of the Jupyter Notebook")
def notebook(filename):
    """Creates a Jupyter Notebook with a cell to run the Curation GUI"""
    number = randrange(100,1_000_000)
    if not filename:
        filename = "notebook.ipynb"
    elif not filename.endswith(".ipynb"):
        filename += ".ipynb"
    python_script = f".temp_{number}.py"
    with open(python_script, 'w') as f:
        f.write(
"""from ImmPortCurationTool import immport_gui as ig
my_gui = ig.GUI()
my_gui.display()""")

    os.system(f"jupytext --quiet --to notebook {python_script} --output {filename}")
    os.remove(python_script)

if __name__ == '__main__':
    help()