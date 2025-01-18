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

import requests
from bs4 import BeautifulSoup


def submit_form(base_url, username, password, inc_id, workflow_id):
    """
    Authenticates to a site and submits a form with default values.
    Modify this function as needed to match the actual login and form submission flow.
    """

    # create a session
    session = requests.Session()
    session.verify = False  # not recommended for production, but can be used if needed

    # authentication step
    login_endpoint = f"{base_url}/login"
    login_payload = {
        "username": username,
        "password": password
    }
    # perform the POST to log in
    response = session.post(login_endpoint, data=login_payload)

    # check if login was successful
    if response.status_code != 200:
        raise ValueError(f"Login failed with status code {response.status_code}.")

    # retrieve the form page
    form_page_url = f"{base_url}/forms/myForm"
    form_page = session.get(form_page_url)
    if form_page.status_code != 200:
        raise ValueError(f"Form page retrieval failed with status code {form_page.status_code}.")

    # parse the form to retrieve default form fields (if you need hidden values, tokens, etc.)
    soup = BeautifulSoup(form_page.text, "html.parser")
    form = soup.find("form", {"name": "new_custom_workflow_execution"})
    if not form:
        raise ValueError("Could not find form 'new_custom_workflow_execution' on the page.")

    # collect default form inputs (including hidden fields)
    form_data = {}
    for input_tag in form.find_all("input"):
        name = input_tag.get("name")
        value = input_tag.get("value", "")
        # populate the dictionary
        if name:
            form_data[name] = value

    # form_data['inc_id'] = inc_id
    # form_data['workflow_id'] = workflow_id

    # submit the form
    action = form.get("action")
    if not action.startswith("http"):
        # build the absolute URL if it's a relative action
        # (this might just be `f"{base_url}/{action}"` depending on how your site is structured)
        action = requests.compat.urljoin(form_page_url, action)

    # now POST the form data
    submit_response = session.post(action, data=form_data)
    if submit_response.status_code not in [200, 302]:
        raise ValueError(
            f"Form submission failed with status code {submit_response.status_code}."
        )

    return "Form submitted successfully."


def main():

    # get conn/auth parameters
    base_url = demisto.args().get('base_url')
    username = demisto.args().get('username')
    password = demisto.args().get('password')

    # get incident arguments
    inc_id = demisto.args().get('inc_id')
    workflow_id = demisto.args().get('workflow_id')

    try:
        result_message = submit_form(
            base_url=base_url,
            username=username,
            password=password,
            inc_id=inc_id,
            workflow_id=workflow_id
        )

        return_results(result_message)
    except Exception as e:
        return_error(f"Error submitting form: {str(e)}")

if __name__ in ("__builtin__", "builtins", "__main__"):
    main()