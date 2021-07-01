#!/usr/bin/env python

"""
purge_incorrect_env_vars.py

Takes data from monitoring and value to be removed, and removes offending entires.

Usage:
  purge_incorrect_env_vars.py [-m <map_name> | --map_name=<map_name>] [-e <entry_name> | --entry_name=<entry_name>] [-v <value> | --value=<value>] [-t <token> | --token=<token>] (-c | --check)
  purge_incorrect_env_vars.py [-m <map_name> | --map_name=<map_name>] [-e <entry_name> | --entry_name=<entry_name>] [-v <value> | --value=<value>] [-t <token> | --token=<token>]
  purge_incorrect_env_vars.py (-h | --help)

Options:
  -h --help                                     Show this screen.
  -m <map_name> | --map_name=<map_name>         Name of Apigee key-value map to edit
  -e <entry_name> | --entry_name=<entry_name>   Name of KVM entry to edit
  -v <value> | --value=<value>                  String value to be removed
  -t <token> | --token=<token>                  Auth token (get_token)
  -c --check                                    Will show the data due to be deleted
"""
import json
import requests
from docopt import docopt

def find_offending_entires(json_data, offending_str):
	if check_mode:
		print("***************************  Check mode  *****************************")
		print("* The following items would be deleted when run outside of check mode *")
	for api in json_data:
		for env in json_data[api]:
				to_keep = []
				for line in json_data[api][env]:
						if offending_str not in line:
								to_keep.append(line)
						else:
								if check_mode:						
										print(" -", line)				
				json_data[api][env] = to_keep
	return json_data

def post_new_data(new_json_data):
    url = f"https://api.enterprise.apigee.com/v1/organizations/{org_name}/environments/{env_name}/keyvaluemaps/{map_name}/entries/{entry_name}"

    format_new_json = {"name": entry_name, "value": json.dumps(new_json_data)}

    post_new_json_data = requests.post(url, json=format_new_json, headers=auth)

    print(post_new_json_data.text)
            
def main(args):
    global map_name, entry_name, token, check_mode
    input_value = str(args["--value"])
    map_name = str(args["--map_name"])
    entry_name = str(args["--entry_name"])
    token = str(args["--token"])
    check_mode = bool(args["--check"])

    global org_name, env_name, auth
    org_name = "nhsd-nonprod"
    env_name = "internal-dev"
    auth = {"Authorization": f"Bearer {token}"}

    url = f"https://api.enterprise.apigee.com/v1/organizations/{org_name}/environments/{env_name}/keyvaluemaps/{map_name}/entries/{entry_name}"
    resp = requests.get(url, headers=auth)

    json_data = json.loads(json.loads(resp.text).get('value'))

    new_json_data = find_offending_entires(json_data, input_value)

    if not check_mode:
      post_new_data(new_json_data)

if __name__ == "__main__":
     main(docopt(__doc__, version="1"))
