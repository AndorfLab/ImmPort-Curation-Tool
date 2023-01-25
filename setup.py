#!/usr/bin/env python
"""
Release notes:
* Install wheel, bump2version (requirements_dev.txt)
* Bump version as patch, minor, major
* Commit and push changes
* Push Tags to GitHub: git push --follow-tags
* Create release on GitHub based on tag
"""
from pathlib import Path

from setuptools import find_packages, setup
from ImmPortCurationTool import version

def read(file_name):
    return (Path(__file__).parent / file_name).read_text()

def get_required_packages():
    text_file = open("requirements.txt", "r")
    return text_file.read().splitlines()

package_name = version.PACKAGE_NAME
url = f"https://github.com/JoshuaFortriede/{package_name}"
git_url = f"git@github.com:JoshuaFortriede/{package_name}.git"

setup(
    name=package_name,
    version=version.VERSION,
    author="Joshua Fortriede",
    author_email="Joshua.Fortriede@gmail.com",
    description="A Jupyter Notebook based tool to tranform study files and a data dictionary into filled-out ImmPort Templates",
    long_description=read("README.md"),
    long_description_content_type="text/markdown",
    license="Apache V2.0",
    keywords="ImmPort Curation",
    install_requires=get_required_packages(),
    packages=[package_name],
    data_files=[('ImmPortCurationTool/templates',['ImmPortCurationTool/templates/*'])],
    python_requires=">=3.7",
    zip_safe=False,
    url=git_url,
    project_urls={
        "Bug Tracker": f"{url}/issues",
        "Source Code": url,
    },
    classifiers=[
        "Development Status :: 1 - Planning0",
        "License :: OSI Approved :: GNU General Public License v3 (GPLv3)",
        "Topic :: Software Development",
        "Programming Language :: Python :: 3",
    ]
)