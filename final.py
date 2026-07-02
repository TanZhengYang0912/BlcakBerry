from flask import Flask
import requests
import os
from dotenv import load_dotenv

load_dotenv()

app = Flask(__name__)

# --- Config ---
API_KEY    = os.environ.get("OTX_API_KEY")
OTX_URL    = "https://otx.alienvault.com/api/v1/pulses/subscribed"
OLLAMA_URL = "http://localhost:11434/api/generate"
MODEL      = "phi3"


# ---------- helpers ----------

def fetch_recent_pulses(limit=5):
    headers  = {"X-OTX-API-KEY": API_KEY}
    response = requests.get(OTX_URL, headers=headers, params={"limit": limit}, timeout=10)
    response.raise_for_status()
    pulses = response.json().get("results", [])
    return [{"title": p.get("name", ""), "description": p.get("description", "")} for p in pulses]


def ask_ollama(text):
    prompt = (
        f"Threat information:\n{text}\n\n"
        "Summarize this threat in 2 sentences and assign severity: High, Medium, or Low."
    )
    body     = {"model": MODEL, "prompt": prompt, "stream": False}
    response = requests.post(OLLAMA_URL, json=body, timeout=60)
    response.raise_for_status()
    return response.json().get("response", "").strip()


def extract_severity(text):
    t = text.lower()
    if "high"   in t: return "High"
    if "medium" in t: return "Medium"
    if "low"    in t: return "Low"
    return "Unknown"


def enrich_pulses(pulses):
    results = []
    for pulse in pulses:
        context  = f"Title: {pulse['title']}\nDescription: {pulse['description']}"
        ai_text  = ask_ollama(context)
        severity = extract_severity(ai_text)
        results.append({
            "title":       pulse["title"],
            "description": pulse["description"],
            "ai_summary":  ai_text,
            "severity":    severity,
        })
    return results


# ---------- HTML builder ----------

SEVERITY_COLORS = {
    "High":    ("#ffdde1", "#c0392b"),
    "Medium":  ("#fff8dc", "#d4a017"),
    "Low":     ("#d5f5e3", "#1e8449"),
    "Unknown": ("#f0f0f0", "#888888"),
}

def build_card(threat):
    sev            = threat["severity"]
    bg, badge_bg   = SEVERITY_COLORS.get(sev, SEVERITY_COLORS["Unknown"])
    short_desc     = threat["description"][:300] + ("..." if len(threat["description"]) > 300 else "")

    return f"""
    <div style="background:{bg}; border-left:5px solid {badge_bg};
                border-radius:8px; padding:20px; margin-bottom:18px;
                box-shadow:0 2px 6px rgba(0,0,0,0.08);">

      <div style="display:flex; justify-content:space-between; align-items:flex-start; gap:12px;">
        <h2 style="margin:0; font-size:1.05rem; color:#1a1a2e; flex:1;">{threat["title"]}</h2>
        <span style="background:{badge_bg}; color:#fff; padding:4px 12px;
                     border-radius:20px; font-size:0.8rem; font-weight:bold;
                     white-space:nowrap;">{sev}</span>
      </div>

      <hr style="border:none; border-top:1px solid {badge_bg}33; margin:12px 0;">

      <p style="margin:0 0 6px; font-size:0.78rem; font-weight:700;
                color:{badge_bg}; text-transform:uppercase; letter-spacing:.05em;">AI Summary</p>
      <p style="margin:0 0 14px; color:#333; line-height:1.6;">{threat["ai_summary"]}</p>

      <p style="margin:0 0 6px; font-size:0.78rem; font-weight:700;
                color:{badge_bg}; text-transform:uppercase; letter-spacing:.05em;">Description</p>
      <p style="margin:0; color:#555; font-size:0.9rem; line-height:1.6;">{short_desc}</p>
    </div>
    """


def build_page(threats):
    cards = "".join(build_card(t) for t in threats)
    return f"""<!DOCTYPE html>
<html lang="en">
<head>
  <meta charset="UTF-8">
  <meta name="viewport" content="width=device-width, initial-scale=1.0">
  <title>OTX Threat Intelligence</title>
  <style>
    * {{ box-sizing: border-box; margin: 0; padding: 0; }}
    body {{
      font-family: 'Segoe UI', Arial, sans-serif;
      background: #f4f6fb;
      color: #222;
      padding: 30px 20px;
    }}
    header {{
      display: flex;
      justify-content: space-between;
      align-items: center;
      margin-bottom: 28px;
    }}
    h1 {{ font-size: 1.5rem; color: #1a1a2e; }}
    .subtitle {{ color: #666; font-size: 0.9rem; margin-top: 4px; }}
    .refresh-btn {{
      background: #2980b9;
      color: #fff;
      border: none;
      padding: 10px 22px;
      border-radius: 6px;
      font-size: 0.95rem;
      cursor: pointer;
      text-decoration: none;
    }}
    .refresh-btn:hover {{ background: #1a6fa8; }}
    .container {{ max-width: 860px; margin: 0 auto; }}
  </style>
</head>
<body>
  <div class="container">
    <header>
      <div>
        <h1>OTX Threat Intelligence</h1>
        <p class="subtitle">Showing 5 most recent pulses — AI enriched via Ollama ({MODEL})</p>
      </div>
      <a class="refresh-btn" href="/">&#x21bb; Refresh</a>
    </header>

    {cards}
  </div>
</body>
</html>"""


# ---------- Route ----------

@app.route("/")
def index():
    try:
        pulses  = fetch_recent_pulses(limit=5)
        threats = enrich_pulses(pulses)
        return build_page(threats)
    except Exception as e:
        return f"<h2 style='color:red;font-family:sans-serif;padding:40px'>Error: {e}</h2>", 500


if __name__ == "__main__":
    app.run(debug=True)
