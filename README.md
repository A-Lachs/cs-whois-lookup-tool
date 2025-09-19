# Project description
This project was started as the first weeks assignment for the Coding Bootcamp for Cybersecurity Professionals.</br>

**This is not a finsihed project, but a WIP!** (not running atm)

The goal is to provide a tool that automates calling the WHOIS server to look up the Registrar of a list of domains you give as input.

## The program has 3 modi for input

1: Interactive mode 
- this mode is active when the script is run from the command line without additional input argument
- it keeps asking you to input domains until you type 'exit'
- **Example**: `python whois_lookup.py `

2: File mode 
- this mode is active when the script is run from the command line with an additional argument that is text file name 
- in this mode the domains are read from the file you provided
- **Example**: `python whois_lookup.py domains_list.txt`

3: Domain mode
- this mode is active when the script is run from the command line with an additional argument that is one or more domains
- all domains links you type after the script name will be processed
- **Example**: `python whois_lookup.py python.org python.org blümchen.com`

The results (domain, registrar) are saved as output in csv or json format. 

# Features

- python libraries used...

# Set up the virtual environment

## Mac0S
```
pyenv local 3.11.3
python -m venv .venv
source .venv/bin/activate
pip install --upgrade pip
pip install -r requirements.txt
```

## WindowsOS git-bash CLI

```
pyenv local 3.11.3
python -m venv .venv
source .venv/Scripts/activate
pip install --upgrade pip
pip install -r requirements.txt
```