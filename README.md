# Q-net sim.
The tool needs to use some non-built-in packages. Recommended to use a virtual environment. Using "venv" for the following. venv comes with python 3.4+. Instructions for linux/mac with bash/zsh. 

Ref: https://docs.python.org/3/library/venv.html

## Create a virtual environment first:
```python -m venv <path/env_name>```

e.g. with path './' and environment name as 'venv-netsquid'

```python -m venv ./venv-netsquid```

## Activate the virtual environment:
```source ./<path/env_name>/bin/activate```

e.g. with path './' and environment name as 'venv-netsquid'

```source ./venv-netsquid/bin/activate```

## First install all the required packages (except netsquid which we will do after this):
```pip install -r requirements.txt```

## Install Netsquid (free but requires login credentials to install):
```pip3 install --extra-index-url https://<username>:<password>@pypi.netsquid.org netsquid ```
This command may give an error "ERROR: Could not find a version that satisfies the requirement netsquid ..." especially for Mac. 

If that happens, need to install using a wheel file. Find the correct version for your OS from https://pypi.netsquid.org/netsquid then install as following:

Further instructions on this: https://docs.netsquid.org/latest-release/INSTALL.html

The reason why we need to install Netsquid after requirements.txt file is that Netsquid does not correctly checks the version numbers of its dependencies and at some point some newer version of some dependency started causing issues and the whole tool stopped working (raised some errors especially AttributeErrors where it should not have done that). Therefore, in requirements.txt some specific versions of the dependencies are specified so that Netsquid works as expected.

## To deactivate the venv:
```deactivate```

## Credits:
src/lib/quantinf is from: https://www.dr-qubit.org/matlab.html