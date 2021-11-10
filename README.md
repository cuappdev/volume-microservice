# volume-microservice

[![Python 3.9.2](https://img.shields.io/badge/python-3.9.2-blue.svg)](https://www.python.org/downloads/release/python-392/)

A project by [Cornell AppDev](http://cornellappdev.com), a project team at Cornell University.

Populates MongoDB collections for use with [volume-backend](https://github.com/cuappdev/volume-backend)

## Installation
Clone the project with
```
$ git clone https://github.com/cuappdev/volume-microservice.git
```
and install dependencies with
```
$ pip install -r requirements.txt
```

## Managing Environment
We recommend using [direnv](https://direnv.net/) and [venv](https://docs.python.org/3/tutorial/venv.html) for managing Python virtual environments.

Set environment variables in the `.envrc` file outlined in the `.envrctemplate` file.

Then follow these steps.
1. `$ pyenv local 3.9.2` to create a `.python-version` file
2. `$ direnv allow .` to enable direnv to use the `.envrc` file

This should automatically enable a virtual environment when opening the directory.