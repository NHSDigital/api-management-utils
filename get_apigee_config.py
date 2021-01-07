"""
get_apigee_config.py

A tool for downloading apigee config files 

Usage:
  get_apigee_config.py --access-token=<APIGEE_TOKEN> --apigee-organization=<APIGEE_ORGANIZATION> --apigee-environment=<APIGEE_ENVIRONMENT>
  get_apigee_config.py (-h | --help)

Options:
  -h --help                        Show this screen
  --access-token=<APIGEE_TOKEN>    Access Token from apigee
  --apigee-organization=<APIGEE_ORGANIZATION>  Apigee organization eg. 'nhsd-nonprod'
  --apigee-environment=<APIGEE_ENVIRONMENT>    Environment to backup config from eg. 'internal-dev'

"""
import requests
import json
import os
from docopt import docopt

# Configuration we want to back-up
apigee_config = ['keystores', 'references', 'virtualhosts', 'caches']

def get_apigee_config(APIGEE_TOKEN: str, APIGEE_ENVIRONMENT: str, APIGEE_ORGANIZATION: str):
    os.mkdir(f'{APIGEE_ENVIRONMENT}')
    
    for conf in apigee_config:
        os.mkdir(f'{APIGEE_ENVIRONMENT}/{conf}')
        url = f'https://api.enterprise.apigee.com/v1/organizations/{APIGEE_ORGANIZATION}/environments/{APIGEE_ENVIRONMENT}/{conf}'
        response = requests.get(url, headers= {"Authorization": "Bearer " + APIGEE_TOKEN})
        list_of_names = response.json()

        for name in list_of_names:
            config = requests.get(f'{url}/{name}', headers= {"Authorization": "Bearer " + APIGEE_TOKEN})
            with open(f'{APIGEE_ENVIRONMENT}/{conf}/{name}.json', 'w') as f:
                json.dump(config.json(), f)

if __name__ == "__main__":
    args = docopt(__doc__)
    get_apigee_config(
        args['--access-token'],
        args['--apigee-environment'], 
        args['--apigee-organization']
        )