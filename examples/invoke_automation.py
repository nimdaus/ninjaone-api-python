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
    "Authorization": "Bearer {access_token}"
}

# Fetch organizations
response = requests.get(f"https://{region}.ninjarmm.com/v2/organizations", headers=headers)
if response.status_code == 200:
    organizations = response.json()
    display_table(organizations, 'id', 'name', "Organizations")
    organization_id = prompt_int("Enter the applicable organization ID", 1)
else:
    throw_error_response_with_result_code(response, "Organization Collection Failed")

# Fetch devices
response = requests.get(f"https://{region}.ninjarmm.com/v2/devices?df=org={organization_id}", headers=headers)
if response.status_code == 200:
    devices = response.json()
    display_table(devices, 'id', 'systemName', "Devices")
    device_id = prompt_int("Enter the Device ID to lookup", 1)
else:
    throw_error_response_with_result_code(response, "Devices Collection Failed")

# Fetch device scripts
response = requests.get(f"https://{region}.ninjarmm.com/v2/device/{device_id}/scripting/options", headers=headers)
if response.status_code == 200:
    device_scripts = response.json().get("scripts", [])
    display_table(device_scripts, 'id', 'name', "Device Scripts")
    device_script_id = prompt_int("Enter the Script ID to select", 1000)
    selected_device_script = next((script for script in device_scripts if script['id'] == device_script_id), None)

    if selected_device_script:
        # Define the parameters for running the script
        run_as = prompt_choice("Choose the identity to run the script as", "loggedonuser", ["system", "SR_MAC_SCRIPT", "SR_LINUX_SCRIPT", "loggedonuser", "SR_LOCAL_ADMINISTRATOR", "SR_DOMAIN_ADMINISTRATOR"])

        # Construct the payload
        payload = {
            "type": selected_device_script["type"],
            "runAs": run_as
        }

        # Add uid only if type equals "action"
        if selected_device_script["type"] == "action":
            payload["uid"] = selected_device_script["uid"]
        else:
            payload["id"] = selected_device_script["id"]

        # Execute the script
        response = requests.post(f"https://{region}.ninjarmm.com/v2/device/{device_id}/script/run", headers={**headers, "Content-Type": "application/json"}, json=payload)
        if response.status_code in [200, 201] and response.content:
            print("Script executed successfully!")
            print(json.dumps(response.json(), indent=4))
        else:
            throw_error_response_with_result_code(response, "Script Execution Failed")
    else:
        print("No script selected. Please verify the script ID.")
else:
    throw_error_response_with_result_code(response, "Device Script Collection Failed")