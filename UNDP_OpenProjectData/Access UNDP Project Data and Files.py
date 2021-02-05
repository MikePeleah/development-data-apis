#################################################################################################################
##
## Script for downloadning project data and related files from open.undp.org
## GitHub https://github.com/MikePeleah/development-data-apis
## For comments and suggestions Mike.Peleah@gmail.com
##
#################################################################################################################
import requests
import json
import re
import time, datetime, os
from random import randint
from time import sleep

def mkdir(dir_name, verbose = False):
    # Safe create directory.
    try:
        # Create target Directory
        os.mkdir(dir_name)
        if verbose:
            print("Directory " , dir_name,  " created ")
        return 0
    except FileExistsError:
        if verbose:
            print("Directory " , dir_name,  " already exists")
        return 1
    return


def try_get(url, ntries=3, delay=10, verbose = False):
    """
    Try to get url for ntries, after each unsuccessful attempt delay for delay seconds
    return {'code': result code, "Ok" if Ok, "Error" else
            'result': result of get}
    """
    attempts = ntries

    while attempts>0:
        attempts_try = attempts
        if verbose:
            print("%d attemps left, trying %s" % (attempts, url))
        try:
            result = requests.get(url)
            code = "Ok"
            attempts = 0
            result.raise_for_status()
        except requests.exceptions.HTTPError as errh:
            attempts = 0
            code = "Error"
            result = "Http Error: %s" % errh
            if verbose:
                  print (result)
        except requests.exceptions.ConnectionError as errc:
            attempts = attempts_try - 1
            code = "Error"
            result = "Error Connecting: %s" % errc
            if verbose:
                  print (result)
            sleep(delay)
        except requests.exceptions.Timeout as errt:
            attempts = attempts_try - 1
            code = "Error"
            result = "Timeout Error: %s" % errt
            if verbose:
                  print (result)
            sleep(delay)
        except requests.exceptions.RequestException as err:
            attempts = 0
            code = "Error"
            if verbose:
                  print (result)
            result = "Oops: Something Else %s" % err
        #if verbose:
            #print("  ",code, result if code=="Error" else "")
    return {'code': code, 'result': result}


def get_project_data_file(p, verbose = False):
    """
    Get project data and associated files
    Input:
      p--project data structuire from operation unit json
      verbose--True for all printouts
    Return:
      0 Ok
      Error code if cannot get 
    """
    # Get project data and dump to file
	# Individual Project Data: https://api.open.undp.org/api/projects/{project - id}.json
    r = requests.get(f"https://api.open.undp.org/api/projects/{p['id']}.json")
    if r.status_code != 200:
        return r.status_code
    p_data = r.json()
    with open(f"{p['id']}.json", 'w', encoding='utf-8') as f:
        json.dump(p_data, f, ensure_ascii=False, indent=4)
    # Getting project documents
    if "document_name" in p_data.keys():
        # "document_name" is organized as three lists [0] titles, [1] urls, and [2] formats
        # check if any documnts included, i.e. documents[0] is not empty
        documents = p_data["document_name"]
        if documents[0]:
            # create folder for documents
            mkdir(f"{p['id']}")
            os.chdir(f"{p['id']}")
            # Loop over titles
            for i, title in enumerate(documents[0]):
			    # Skip  Activity Web Page
                if title == "Activity Web Page":
                    print("    Skipping Activity Web Page")
                else:
                    url = documents[1][i]
                    print(f"    Getting document '{title}' from {url}")
                    try_doc = try_get(url, ntries=3, delay=10, verbose = False)
                    if try_doc['code'] == "Ok":
					    # Replace unsafe characters from title by the underscore
                        safe_dir = re.sub("[\t\"\'\\*/\\\\!\\|:?<>]", "_", re.sub("(%22)", "_", title))
                        mkdir(safe_dir)
                        os.chdir(safe_dir)
						# Replace unsafe characters from filename by the underscore
                        fname = re.sub("[\t\"\'\\*/\\\\!\\|:?<>]", "_", re.sub("(%22)", "_", re.split('/', url)[-1]))
                        print(f"      Ok, saving {safe_dir}/{fname}")
                        with open(fname, 'wb') as f:
                            f.write(try_doc['result'].content)
                        os.chdir('..')
                    else:
                        print(f"      Unsuccesful, {try_doc['result']}")
            os.chdir('..')
    return 0

# **** MAIN SCRIPT ****************************************************************

today = datetime.date.today()  
todaystr = today.isoformat()
# Use the folder
mkdir(f"UNDP Projects {todaystr}")
os.chdir(f"UNDP Projects {todaystr}")

# Get index of operational units -- from file if it exists, othervise from web 
if os.path.isfile('operating-unit-index.json'):
    with open('operating-unit-index.json', 'r', encoding='utf-8') as f:
        oui = json.load(f)
else:
    r = requests.get("https://api.open.undp.org/api/units/operating-unit-index.json")
    oui = r.json()
    with open("operating-unit-index.json", 'w', encoding='utf-8') as f:
        json.dump(oui, f, ensure_ascii=False, indent=4)

# This dictionary is used for quick skip to country/project. Set "skip_ou" and "skip_project" to avoid skipping. 
skip_to = {"op_unit": "PAL", "project_id": "00057409",
           "skip_ou": True, "skip_project": True}
    
# Loop over all operational units
for ou in oui:
    # Check if we reached op_unit to skip, then drop skip flag. 
    if ou['id'] == skip_to["op_unit"]:
        skip_to["skip_ou"] = False
    if skip_to["skip_ou"]:
        print(f"Skipping {ou['id']} - {ou['name']}")
        continue
    print(f"Handling {ou['id']} - {ou['name']}")
    mkdir(f"{ou['id']}")
    os.chdir(f"{ou['id']}")
    # Get list of project for an operating unit and dump them to file
	# Operating Unit Data: https://api.open.undp.org/api/units/{operating - unit}.json
    r = requests.get(f"https://api.open.undp.org/api/units/{ou['id']}.json")
    ou_prj = r.json()
    with open(f"{ou['id']}.json", 'w', encoding='utf-8') as f:
        json.dump(ou_prj, f, ensure_ascii=False, indent=4)
    # Loop through projects 
    for p in ou_prj['projects']:
        # Check if we reached project_id to skip, then drop skip flag. 
        if p['id'] == skip_to["project_id"]:
            skip_to["skip_project"] = False
        if skip_to["skip_project"]:
            print(f"  Skipping {p['id']} - {p['title']}")
            continue
        # Now handle the project
        print(f"\n  Project {ou['id']}:{p['id']} - {p['title']}")
        get_project_data_file(p, verbose = True)
    # time.sleep(randint(1,5))
    os.chdir('..')
os.chdir('..')
print("* * *  That's all, Folks!  * * *")
