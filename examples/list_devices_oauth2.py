import requests
import getpass
import json
import webbrowser

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

url = f"https://{region}.ninjarmm.com/v2/devices"

headers = {
    "Accept": "application/json",
    "Authorization": "Bearer {access_token}"
}

response = requests.get(url, headers=headers)
print(json.dumps(response.json(), indent=4))