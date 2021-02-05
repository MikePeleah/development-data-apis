#################################################################################################################
##
## Script for getting project results from open.undp.org
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

# Folder with project files 
projects_folder = "UNDP Projects 2020-12-03"
os.chdir(projects_folder) #  Go to projects folder

big_results_list = []
indicators_list = []

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
skip_to = {"op_unit": "CHN", "project_id": "00032987",
           "skip_ou": True, "skip_project": True}

n_outputs = 0
n_outputs_results = 0

log_file = open("grab-project-results.log", 'w', encoding='utf-8')

# Loop through all operational units 
for ou in oui:
    if ou['id'] == skip_to["op_unit"]:
        skip_to["skip_ou"] = False
    if skip_to["skip_ou"]:
        print(f"Skipping {ou['id']} - {ou['name']}")
        continue
    print(f"\nHandling {ou['id']} - {ou['name']}")
    os.chdir(ou['id']) # Go to folder for op unit
    # Load list of projects and loop through them. If opunit file with projects doesn't exists--load it from web
	if os.path.isfile(f"{ou['id']}.json"):
        with open(f"{ou['id']}.json", 'r', encoding='utf-8') as f:
            ou_lop = json.load(f)
	else:
	    r = requests.get(f"https://api.open.undp.org/api/units/{ou['id']}.json")
		ou_lop = r.json()
        with open(f"{ou['id']}.json", 'w', encoding='utf-8') as f:
            json.dump(ou_lop, f, ensure_ascii=False, indent=4)
		
    for project in ou_lop['projects']:
        if project['id'] == skip_to['project_id']:
            skip_to['skip_project'] = False
        if skip_to['skip_project']:
            print(f"  Skipping {ou['id']}:{project['id']} - {project['title']}")
            continue
        project_results = []
        print(f"  Project {ou['id']}:{project['id']} - {project['title']}")
        # Check if project .json file exists, if yes--load it; if no--get it from web 
        if os.path.isfile(f"{project['id']}.json"):
            with open(f"{project['id']}.json", 'r', encoding='utf-8') as f:
                project_data = json.load(f)
        else:
            print(f"    Geeting project {ou['id']}:{project['id']} data from site")
            project_data = get_project_data_file (project, verbose = True)
        # Loop through outputs
        for output in project_data['outputs']:
            n_outputs += 1
            # Try to get results. If not status code 200--some error happened, skip it
            # Use undocumented API call 
            # https://api.open.undp.org/api/v1/output/{output_id}/results
            res_req = requests.get(f"https://api.open.undp.org/api/v1/output/{output['output_id']}/results")
            if res_req.status_code == 200:
                # So we got data, let's handle them
                results_json = res_req.json()
                if 'data' in results_json.keys():
                    results_data = results_json['data']
                    for r_data in results_data:
                        n_outputs_results += 1
                        # Save results to big results list and individual project results
                        big_results_list.append(r_data)
                        project_results.append(r_data)
                        # Generate list of indicators and append it to main list of indicators
                        # Keep indicators #
                        # inds = [re.sub('^[0-9+]\. ', '', i) for i in re.split('\n', r_data['indicator_description'])]
                        inds = re.split('\n', r_data['indicator_description'])
                        indicators_list.append({'operating_unit_id': ou['id'], 
                                                'project': r_data['project'],
                                                'output': r_data['output'], 
                                                'indicator_title': r_data['indicator_title'],
                                                'indicators': inds})
                else:
                    print(f"    x {output['output_id']} - No successful results")
                    print(f"    x {output['output_id']} - No successful results", file = log_file)
            else:
                print(f"    x {output['output_id']} - No results")
                print(f"    x {output['output_id']} - No results", file = log_file)
        if project_results:
            print(f"    V {output['output_id']} - Got results")
            print(f"    V {output['output_id']} - Got results", file = log_file)
            with open(f"results {project['id']}.json", 'w', encoding='utf-8') as f:
                json.dump(project_results, f, ensure_ascii=False, indent=4)
        else:
            print(f"    x {output['output_id']} - Empty results")
            print(f"    x {output['output_id']} - Empty results", file = log_file)
    os.chdir('..') # Go .. folder for op unit

# Save everything
with open("big-results-file.json", 'w', encoding='utf-8') as f:
    json.dump(oui, f, ensure_ascii=False, indent=4)
with open("big-results-file.json", 'w', encoding='utf-8') as f:
    json.dump(oui, f, ensure_ascii=False, indent=4)
os.chdir('..') #  Go .. projects folder
print(f"\nProcessed {n_outputs} outputs, identified {n_outputs_results} with results")
print(f"\nProcessed {n_outputs} outputs, identified {n_outputs_results} with results", file = log_file)
log_file.close()

print("\n* * *  That's all, Folks!  * * *")
