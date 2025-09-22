# Project description
This project was created as an assignment for the 1st week of the Coding Bootcamp for Cybersecurity Professionals.</br>

The goal is to provide a whois lookup tool that automates calling the WHOIS database to get the registrars of a list of domains you give as input.

## Input modi

1: Interactive mode 
- This mode is active when the script is run from the command line without an additional input argument.
- It keeps asking you to input domains until you type 'c' for continue for further processing.
- **Example**: `python whois_lookup.py `

2: File mode 
- This mode is active when the script is run from the command line with an additional argument that is the text file name. 
- The domains are read from the file you provided.
- **Example**: `python whois_lookup.py domains_list.txt`

3: Domain mode
- This mode is active when the script is run from the command line with an additional argument that is one or more domains.
- All domain links you type after the script name will be processed.
- **Example**: `python whois_lookup.py python.org python.org blümchen.com`

## Features

1. The `phyton-whois` module is used to query the whois database for domain registrars.
2. Multiple domains requests are processed in parallel, reducing overall runtime.
    - Using the `ThreadpoolExecuter` from the python module `concurrent.futures` a maximum number of worker threads defined by `MAXWORKERS` (=5).
    - Up to 5 requests are executed in parallel as concurrent tasks.
3. The results (domain, registrar) can be saved as CSV or JSON file.
    - A new file named 'output' is created.
    - If the output file already exists, only new entries will be added.

# Set up the virtual environment

## Mac0S
```
pyenv local 3.11.3
python -m venv .venv
source .venv/bin/activate
pip install --upgrade pip
pip install -r requirements.txt --upgrade
```

## WindowsOS git-bash CLI

```
pyenv local 3.11.3
python -m venv .venv
source .venv/Scripts/activate
pip install --upgrade pip
pip install -r requirements.txt --upgrade
```

* Hint: use `--upgrade` to install packages listed in requirements.txt or update existing to pinned versions

# Disclaimer
This is a WIP, I am still learning (September 2025)