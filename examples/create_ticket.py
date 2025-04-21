import requests
import getpass
import json
import webbrowser

def throw_error_response_with_result_code(response, message):
    result_code_message = f"\nStated reason: {response.json().get('resultCode')}" if 'resultCode' in response.json() else ""
    raise Exception(f"\n{message}\nUnexpected Status Code: {response.status_code}{result_code_message}")

def display_table(data, sort_key, second_column_key, title):
    print(f"\n{title}\n")
    sorted_data = sorted(data, key=lambda x: x[sort_key])
    for item in sorted_data:
        print(f"{item[sort_key]:<20} {item[second_column_key]}")
    print("\n")

def prompt_int(message, default):
    while True:
        user_input = input(f"{message} (Default: {default}): ")
        if not user_input.strip():
            return default
        try:
            return int(user_input)
        except ValueError:
            print("Invalid input. Please enter a valid integer.")

def prompt_choice(message, default, choices):
    print(message)
    for index, choice in enumerate(choices, start=1):
        print(f"{index}: {choice}")
    
    default_index = choices.index(default) + 1
    while True:
        user_input = input(f"Select an option by number (Default: {default_index}): ")
        if not user_input.strip():
            return default
        if user_input.isdigit() and 1 <= int(user_input) <= len(choices):
            return choices[int(user_input) - 1]
        else:
            print("Invalid choice. Please select a valid number.")

region = input("Enter region: ")
client_id = input("Enter client_id: ")
client_secret = getpass.getpass("Enter your client_secret(no visible input): ")
response_type = "code"
redirect_uri = input("Enter redirect_uri: ")
scope = input("Enter *SPACE* separated scope, e.g., control management monitoring: ")

auth_url = (
    f"https://{region}.ninjarmm.com/ws/oauth/authorize?"
    f"response_type={response_type}&"
    f"client_id={client_id}&"
    f"client_secret={client_secret}&"
    f"redirect_uri={redirect_uri}&"
    f"scope={scope}"
)

print("Opening browser for authentication...")
webbrowser.open(auth_url, new=1, autoraise=True)

print(f"\nIf the browser does not open, please navigate to the following URL to authenticate:\n{auth_url}")

code = input("Please enter the NinjaOne authorization code from the redirect URL: ")

url = f"https://{region}.ninjarmm.com/ws/oauth/token"

payload = {
    "grant_type": "authorization_code",
    "client_id": f"{client_id}",
    "client_secret": f"{client_secret}",
    "code": f"{code}",
    "redirect_uri": f"{redirect_uri}"
}

headers = {"Content-Type": "application/x-www-form-urlencoded"}
response = requests.post(url, data=payload, headers=headers)

response_data = response.json()

access_token = response_data["access_token"]

headers = {
    "Accept": "application/json",
    "Authorization": f"Bearer {access_token}"
}

# Fetch Ticket Forms
response = requests.get(f"https://{region}.ninjarmm.com/v2/ticketing/ticket-form", headers=headers)
if response.status_code == 200:
    ticket_forms = response.json()
    display_table(ticket_forms, 'id', 'name', "Ticket Forms")
    form_id = prompt_int("Enter the Ticket Form ID to use", 1)
else:
    throw_error_response_with_result_code(response, "Ticket Form Collection Failed")

# Fetch Statuses
response = requests.get(f"https://{region}.ninjarmm.com/v2/ticketing/statuses", headers=headers)
if response.status_code == 200:
    statuses = response.json()
    display_table(statuses, 'statusId', 'displayName', "Ticket Statuses")
    status_id = prompt_int("Enter the Status ID to assign to the ticket", 1000)
else:
    throw_error_response_with_result_code(response, "Ticket Status Collection Failed")

# Fetch Organizations
response = requests.get(f"https://{region}.ninjarmm.com/v2/organizations", headers=headers)
if response.status_code == 200:
    organizations = response.json()
    display_table(organizations, 'id', 'name', "Organizations")
    client_id = prompt_int("Enter the Organization ID to associate with the ticket", 1)
else:
    throw_error_response_with_result_code(response, "Organization Collection Failed")

# Fetch Ticket Attributes
response = requests.get(f"https://{region}.ninjarmm.com/v2/ticketing/attributes", headers=headers)
if response.status_code == 200:
    ticket_attributes = response.json()
    display_table(ticket_attributes, 'id', 'description', "Ticket Attributes")
    attribute_id = prompt_int("Enter the Ticket Attribute ID to associate with the ticket", None)
    selected_attribute = next((attr for attr in ticket_attributes if attr['id'] == attribute_id), None)
    if selected_attribute:
        attribute_values = selected_attribute['content']['values']
        print(f"\nAvailable Values for Attribute '{selected_attribute['name']}':\n")
        for value in attribute_values:
            print(f"Value ID: {value['id']} | Name: {value['name']} | Active: {value['active']} | System: {value['system']}")
        attribute_value = prompt_int("Enter the Ticket Attribute Value to associate with the ticket attribute", None)
else:
    throw_error_response_with_result_code(response, "Ticket Attribute Collection Failed")

# Collect Ticket Details from User
subject = input("Enter the Subject of the ticket: ")
description = input("Enter the Description of the ticket: ")
description_public = prompt_choice("Is the description public?", True, [True, False])
priority = prompt_choice("Choose the Priority", "NONE", ["NONE", "HIGH", "LOW", "MEDIUM"])
ticket_type = prompt_choice("Choose the Type", "PROBLEM", ["PROBLEM", "QUESTION", "INCIDENT", "TASK"])

# Create the Payload
payload = {
    "clientId": client_id,
    "ticketFormId": form_id,
    "subject": subject,
    "description": {
        "public": description_public,
        "body": description,
        "htmlBody": f"<p>{description}</p>"
    },
    "status": str(status_id),
    "type": ticket_type,
    "priority": priority,
    "attributes": [
        {
            "attributeId": attribute_id,
            "value": attribute_value
        }
    ]
}

# POST Request to Create the Ticket
response = requests.post(f"https://{region}.ninjarmm.com/v2/ticketing/ticket", headers=headers, json=payload)
if response.status_code in [200, 201] and response.content:
    print("Ticket created successfully!")
    print("Ticket contents:")
    print(json.dumps(response.json(), indent=4))
else:
    throw_error_response_with_result_code(response, "Ticket Creation Failed")


<!-- print(json.dumps(response.json(), indent=4)) -->
