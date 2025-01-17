"""

proofpoint trap - run workflow for incident

this script was created to deal with executing a PTR workflow since its not possible (or not clear) with the api

pre-reqs:
- prior to this the analyst or playbook needs to determine what workflow should be ran, providing the workflow id to the script
- login credentials for trap

steps:
1. establishes an authenticated session (i created a service account in trap for this)
2. loads the 'run custom workflow' form
3. submits the form with the default values

args:
- "base_url": the url for the trap instance
- "username": for a trap user
- "password": for the trap user
- "workflow_id": ID for the custom workflow to run
- "trap_inc_id": ID for the trap incident 

note: there are security considerations that need to be evaluated for each scenario, use at your own risk.

"""

import demistomock as demisto
from CommonServerPython import *
from CommonServerUserPython import *

def login_to_service(base_url, username, password):

    # establish session

    client = Client(
        base_url=base_url,
        verify=False,  # verify cert? 
        proxy=False  
    )

    login_data = {
        'username': username,
        'password': password
    }

    login_response = client.post(
        url='/login',
        json=login_data
    )

    login_response.raise_for_status()  # raise an error if the login failed

    return client

def submit_form(client, trap_inc_id):
    # submits the form

    form_response = client.post(
        url=f'/incidents/{trap_inc_id}/custom_workflow_executions'
    )

    form_response.raise_for_status()

    return form_response

def main():
    try:
        base_url = demisto.args().get('base_url')
        username = demisto.args().get('username')
        password = demisto.args().get('password')
        workflow_id = demist.args().get('workflow_id')
        trap_inc_id = demisto.args().get('trap_inc_id')

        # step 1 - establish session
        client = login_to_service(base_url, username, password, workflow_id)

        # step 3 - submit the form
        form_response = submit_form(client, trap_inc_id)

        demisto.results(form_response.json())

    except Exception as e:
        demisto.error(traceback.format_exc())  # print the full traceback
        return_error(f"Error: {str(e)}")

if __name__ in ('__main__', '__builtin__', 'builtins'):
    main()