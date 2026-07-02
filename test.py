import requests
import json

API_KEY = "f2a9c2bee14b64b3345866f5661ce5741b9af760757c48678c980240403966c2"
BASE_URL = "https://otx.alienvault.com/api/v1"


def fetch_recent_pulses(limit=5):
    url = f"{BASE_URL}/pulses/subscribed"
    headers = {"X-OTX-API-KEY": API_KEY}
    params = {"limit": limit}

    response = requests.get(url, headers=headers, params=params, timeout=10)
    response.raise_for_status()

    pulses = response.json().get("results", [])
    return [
        {
            "title": p.get("name", ""),
            "description": p.get("description", ""),
        }
        for p in pulses
    ]


if __name__ == "__main__":
    results = fetch_recent_pulses()
    print(json.dumps(results, indent=2))
