import requests
import json
import urllib3
# Define your Wazuh API credentials and URL
WAZUH_API_URL = "https://199.200.240.249"
WAZUH_USERNAME = "admin"
WAZUH_PASSWORD = "9VDeqBcu76Eby?7rEJ2Aw6U3d*mbStKl"

def wazuh_authenticate():
    """Authenticate with Wazuh API and return the auth token."""
    auth_url = f"{WAZUH_API_URL}/security/user/authenticate"
    response = requests.get(auth_url, auth=(WAZUH_USERNAME, WAZUH_PASSWORD), verify=False)
    if response.status_code == 200:
        auth_token = response.json()['data']['token']
        return auth_token
    else:
        print("Failed to authenticate with Wazuh API.")
        return None
urllib3.disable_warnings(urllib3.exceptions.InsecureRequestWarning)
def fetch_failed_login_counts(auth_token):
    """Fetch count of failed logins using authenticated session."""
    query_url = f"{WAZUH_API_URL}/elastic/alerts/_search"
    query_headers = {"Authorization": f"Bearer {auth_token}"}
    query_payload = {
        "index": "wazuh-alerts-*",
        "body": {
            "query": {
                "bool": {
                    "must": [],
                    "filter": [
                        {"match_phrase": {"rule.groups": "authentication_failed"}},
                        # Add other filters as necessary
                    ]
                }
            },
            "size": 0,  # We only want the count
            "aggs": {
                "failed_logins": {"value_count": {"field": "agent.id"}}
            }
        }
    }
    response = requests.post(query_url, headers=query_headers, json=query_payload, verify=False)
    if response.status_code == 200:
        failed_logins_count = response.json()['aggregations']['failed_logins']['value']
        return failed_logins_count
    else:
        print("Failed to fetch failed login counts.")
        return None

# Authenticate with Wazuh
auth_token = wazuh_authenticate()
if auth_token:
    # Fetch and print failed login counts
    failed_logins_count = fetch_failed_login_counts(auth_token)
    print(f"Failed login attempts: {failed_logins_count}")
else:
    print("Authentication failed. Cannot fetch failed login attempts.")
