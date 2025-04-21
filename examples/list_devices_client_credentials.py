import requests
import getpass
import json

region = input("Enter region: ")
client_id = input("Enter client_id: ")
client_secret = getpass.getpass("Enter your client_secret: ")
grant_type = "client_credentials"
scope = input("Enter *SPACE* separated scope, e.g., control management monitoring: ")

url = f"https://{region}.ninjarmm.com/ws/oauth/token"

payload = {
    "grant_type": f"{grant_type}",
    "client_id": f"{client_id}",
    "client_secret": f"{client_secret}",
    "scope": f"{scope}"
}
headers = {"Content-Type": "application/x-www-form-urlencoded"}

response = requests.post(url, data=payload, headers=headers)
client_secret = None

response = response.json()
access_token = response["access_token"]

url = f"https://{region}.ninjarmm.com/v2/devices"

headers = {
    "Accept": "application/json",
    "Authorization": f"Bearer {access_token}"
}

response = requests.get(url, headers=headers)

print(json.dumps(response.json(), indent=4))