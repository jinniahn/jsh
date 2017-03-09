import os
from setuptools import setup

setup(
    name = "jsh",
    version = "1.0",
    author = "jinsub ahn",
    author_email = "jinniahn@gmail.com",
    description = ("this module allows user to run shell command easily."),
    license = "MIT",
    keywords = "shell, util",
    url = "https://github.com/jinniahn/jsh",
    packages=['curl_parser'],
    install_requires=[
        'jsh',
    ],    
    classifiers=[
        "Topic :: Utilities",
        "Topic :: Networks"
    ]
)
