# Q-net sim.
The tool needs to use some non-built-in packages. Recommended to use a virtual environment. Using "venv" for the following. venv comes with python 3.4+. Instructions for linux/mac with bash/zsh. 

Ref: https://docs.python.org/3/library/venv.html

## Create a virtual environment first:
```python -m venv <path/env_name>```

e.g. with path './' and environment name as 'venv'

```python -m venv ./venv```

## Activate the virtual environment:
```source ./venv/bin/activate```

## Install Netsquid (free but requires login credentials to install):
```pip3 install --extra-index-url https://<username>:<password>@pypi.netsquid.org netsquid ```
This command may give an error "ERROR: Could not find a version that satisfies the requirement netsquid ..." especially for Mac. 

If that happens, need to install using a wheel file. Find the correct version for your OS from https://pypi.netsquid.org/netsquid then install as following:

Further instructions on this: https://docs.netsquid.org/latest-release/INSTALL.html

## Install Netsquid (free but requires login credentials to install):
```pip3 install --extra-index-url https://<username>:<password>@pypi.netsquid.org netsquid ```
This command may give an error "ERROR: Could not find a version that satisfies the requirement netsquid ..." especially for Mac. 
If that happens, need to install using a wheel file. 
Further instructions on installation: https://docs.netsquid.org/latest-release/INSTALL.html

## Install the rest of the required packages:
```pip install -r requirements.txt```

## To deactivate the venv:
```deactivate```

## directory structure (for now):
- initial-exploration-code: contains old code when i first first exploring the library. its mostly useless now.
- linear-chain: also not useful now. simple linear network that teleports qubits. uses a simplified slmp algorithm
- qpass-qcast: this is the main one. will probably make it super generalized later to include slmp (and possibly others later).
- slmp: implementation of slmp using entities. another implementation of slmp without entities (used yield statements) is in initial-exploration-code