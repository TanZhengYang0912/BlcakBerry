import tkinter as tk
from tkinter import ttk
import threading
import requests

# --- Config ---
API_KEY = "f2a9c2bee14b64b3345866f5661ce5741b9af760757c48678c980240403966c2"
OTX_URL = "https://otx.alienvault.com/api/v1/pulses/subscribed"
OLLAMA_URL = "http://localhost:11434/api/generate"
OLLAMA_MODEL = "phi3"

# --- Colors ---
BG       = "#1e1e2e"
CARD_BG  = "#2a2a3e"
FG       = "#cdd6f4"
ACCENT   = "#89b4fa"
HIGH     = "#f38ba8"
MEDIUM   = "#fab387"
LOW      = "#a6e3a1"
UNKNOWN  = "#6c7086"
BTN_BG   = "#313244"


# ---------- API helpers ----------

def fetch_recent_pulses(limit=5):
    headers = {"X-OTX-API-KEY": API_KEY}
    response = requests.get(OTX_URL, headers=headers, params={"limit": limit}, timeout=10)
    response.raise_for_status()
    pulses = response.json().get("results", [])
    return [{"title": p.get("name", ""), "description": p.get("description", "")} for p in pulses]


def ask_ollama(text):
    prompt = (
        f"Threat information:\n{text}\n\n"
        "Summarize this threat in 2 sentences and assign severity: High, Medium, or Low."
    )
    body = {"model": OLLAMA_MODEL, "prompt": prompt, "stream": False}
    response = requests.post(OLLAMA_URL, json=body, timeout=60)
    response.raise_for_status()
    return response.json().get("response", "").strip()


def extract_severity(text):
    t = text.lower()
    if "high"   in t: return "High"
    if "medium" in t: return "Medium"
    if "low"    in t: return "Low"
    return "Unknown"


# ---------- GUI ----------

class App(tk.Tk):
    def __init__(self):
        super().__init__()
        self.title("OTX Threat Intelligence")
        self.geometry("860x700")
        self.configure(bg=BG)
        self.resizable(True, True)
        self._build_ui()

    def _build_ui(self):
        # Header
        header = tk.Frame(self, bg=BG)
        header.pack(fill="x", padx=20, pady=(20, 10))

        tk.Label(header, text="OTX Threat Intelligence", font=("Segoe UI", 18, "bold"),
                 bg=BG, fg=ACCENT).pack(side="left")

        self.btn = tk.Button(header, text="Fetch & Analyze",
                             font=("Segoe UI", 11), bg=ACCENT, fg=BG,
                             relief="flat", padx=14, pady=6, cursor="hand2",
                             command=self._start)
        self.btn.pack(side="right")

        # Status bar
        self.status_var = tk.StringVar(value="Ready. Click 'Fetch & Analyze' to start.")
        tk.Label(self, textvariable=self.status_var, font=("Segoe UI", 10),
                 bg=BG, fg=UNKNOWN).pack(anchor="w", padx=22)

        # Progress bar
        self.progress = ttk.Progressbar(self, mode="determinate")
        style = ttk.Style()
        style.theme_use("clam")
        style.configure("TProgressbar", troughcolor=CARD_BG, background=ACCENT, thickness=6)
        self.progress.pack(fill="x", padx=20, pady=(4, 10))

        # Scrollable card area
        container = tk.Frame(self, bg=BG)
        container.pack(fill="both", expand=True, padx=20, pady=(0, 20))

        self.canvas = tk.Canvas(container, bg=BG, highlightthickness=0)
        scrollbar = tk.Scrollbar(container, orient="vertical", command=self.canvas.yview)
        self.canvas.configure(yscrollcommand=scrollbar.set)

        scrollbar.pack(side="right", fill="y")
        self.canvas.pack(side="left", fill="both", expand=True)

        self.card_frame = tk.Frame(self.canvas, bg=BG)
        self.canvas_window = self.canvas.create_window((0, 0), window=self.card_frame, anchor="nw")

        self.card_frame.bind("<Configure>", self._on_frame_resize)
        self.canvas.bind("<Configure>", self._on_canvas_resize)
        self.canvas.bind_all("<MouseWheel>", self._on_mousewheel)

    def _on_frame_resize(self, event):
        self.canvas.configure(scrollregion=self.canvas.bbox("all"))

    def _on_canvas_resize(self, event):
        self.canvas.itemconfig(self.canvas_window, width=event.width)

    def _on_mousewheel(self, event):
        self.canvas.yview_scroll(int(-1 * (event.delta / 120)), "units")

    def _start(self):
        self.btn.config(state="disabled")
        self._clear_cards()
        self.status_var.set("Fetching pulses from OTX...")
        self.progress["value"] = 0
        threading.Thread(target=self._run, daemon=True).start()

    def _run(self):
        try:
            pulses = fetch_recent_pulses(limit=5)
            total = len(pulses)
            self.progress["maximum"] = total

            for i, pulse in enumerate(pulses, start=1):
                self._set_status(f"Analyzing [{i}/{total}]: {pulse['title'][:55]}...")
                context = f"Title: {pulse['title']}\nDescription: {pulse['description']}"
                ai_response = ask_ollama(context)
                severity = extract_severity(ai_response)

                self.after(0, self._add_card, pulse["title"], pulse["description"], ai_response, severity)
                self.after(0, self._set_progress, i)

            self._set_status(f"Done — {total} threats analyzed.")
        except Exception as e:
            self._set_status(f"Error: {e}")
        finally:
            self.after(0, lambda: self.btn.config(state="normal"))

    def _set_status(self, msg):
        self.after(0, lambda: self.status_var.set(msg))

    def _set_progress(self, val):
        self.progress["value"] = val

    def _clear_cards(self):
        for widget in self.card_frame.winfo_children():
            widget.destroy()

    def _add_card(self, title, description, ai_summary, severity):
        sev_color = {"High": HIGH, "Medium": MEDIUM, "Low": LOW}.get(severity, UNKNOWN)

        card = tk.Frame(self.card_frame, bg=CARD_BG, padx=16, pady=14)
        card.pack(fill="x", pady=6)

        # Top row: title + severity badge
        top = tk.Frame(card, bg=CARD_BG)
        top.pack(fill="x")

        tk.Label(top, text=title, font=("Segoe UI", 12, "bold"),
                 bg=CARD_BG, fg=FG, wraplength=640, justify="left",
                 anchor="w").pack(side="left", fill="x", expand=True)

        tk.Label(top, text=f"  {severity}  ", font=("Segoe UI", 10, "bold"),
                 bg=sev_color, fg=BG, padx=6, pady=2).pack(side="right", padx=(8, 0))

        tk.Frame(card, bg="#3a3a5e", height=1).pack(fill="x", pady=8)

        # AI Summary
        tk.Label(card, text="AI Summary", font=("Segoe UI", 9, "bold"),
                 bg=CARD_BG, fg=ACCENT).pack(anchor="w")
        tk.Label(card, text=ai_summary, font=("Segoe UI", 10),
                 bg=CARD_BG, fg=FG, wraplength=780, justify="left",
                 anchor="w").pack(anchor="w", pady=(2, 8))

        # Description (truncated)
        tk.Label(card, text="Description", font=("Segoe UI", 9, "bold"),
                 bg=CARD_BG, fg=ACCENT).pack(anchor="w")
        short_desc = description[:300] + "..." if len(description) > 300 else description
        tk.Label(card, text=short_desc, font=("Segoe UI", 9),
                 bg=CARD_BG, fg=UNKNOWN, wraplength=780, justify="left",
                 anchor="w").pack(anchor="w")


if __name__ == "__main__":
    App().mainloop()
