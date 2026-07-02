import requests
import json
import os
from dotenv import load_dotenv

load_dotenv()

# --- OTX Config ---
API_KEY = os.environ.get("OTX_API_KEY")
OTX_URL = "https://otx.alienvault.com/api/v1/pulses/subscribed"

# --- Ollama Config ---
OLLAMA_URL = "http://localhost:11434/api/generate"
OLLAMA_MODEL = "phi3"


def fetch_recent_pulses(limit=5):
    """Fetch the 5 most recent threat pulses from OTX."""
    headers = {"X-OTX-API-KEY": API_KEY}
    params = {"limit": limit}

    response = requests.get(OTX_URL, headers=headers, params=params, timeout=10)
    response.raise_for_status()

    pulses = response.json().get("results", [])
    return [
        {
            "title": p.get("name", ""),
            "description": p.get("description", ""),
        }
        for p in pulses
    ]


def ask_ollama(text):
    """Send text to Ollama and return the AI's response."""
    prompt = (
        f"Threat information:\n{text}\n\n"
        "Summarize this threat in 2 sentences and assign severity: High, Medium, or Low."
    )

    body = {
        "model": OLLAMA_MODEL,
        "prompt": prompt,
        "stream": False,
    }

    response = requests.post(OLLAMA_URL, json=body, timeout=60)
    response.raise_for_status()

    return response.json().get("response", "").strip()


def extract_severity(ai_text):
    """Pull out the severity level from the AI response."""
    text_lower = ai_text.lower()
    if "high" in text_lower:
        return "High"
    elif "medium" in text_lower:
        return "Medium"
    elif "low" in text_lower:
        return "Low"
    else:
        return "Unknown"


def enrich_pulses(pulses):
    """Add ai_summary and severity fields to each pulse."""
    enriched = []

    for i, pulse in enumerate(pulses, start=1):
        print(f"[{i}/{len(pulses)}] Analyzing: {pulse['title'][:60]}...")

        # Combine title + description as context for the AI
        context = f"Title: {pulse['title']}\nDescription: {pulse['description']}"
        ai_response = ask_ollama(context)

        enriched.append({
            "title": pulse["title"],
            "description": pulse["description"],
            "ai_summary": ai_response,
            "severity": extract_severity(ai_response),
        })

    return enriched


if __name__ == "__main__":
    print("Fetching threat pulses from OTX...\n")
    pulses = fetch_recent_pulses(limit=5)

    print("Enriching with AI analysis via Ollama...\n")
    results = enrich_pulses(pulses)

    print("\n--- Results ---\n")
    print(json.dumps(results, indent=2))
