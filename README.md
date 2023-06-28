# QON Simulator
The tool needs to use some non-built-in packages. Recommended to use a virtual environment. Using "venv" for the following. venv comes with python 3.4+. Instructions for linux/mac with bash/zsh. 

Ref: https://docs.python.org/3/library/venv.html

## Create a virtual environment first:
```python -m venv <path/env_name>```

e.g. with path './' and environment name as 'venv'

```python -m venv ./venv```

## Activate the virtual environment:
```source ./venv/bin/activate```
## Now install the required packages:
```pip install -r requirements.txt```
## To deactivate the venv:
```deactivate```