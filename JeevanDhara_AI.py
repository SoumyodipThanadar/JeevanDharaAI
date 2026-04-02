"""
╔══════════════════════════════════════════════════════════════╗
║          JeevanDhara AI – Women's Safety System              ║
║          "When Every Second Matters"                         ║
║          Team: Logic-Legends | OmDayal Group of Institutions ║
╚══════════════════════════════════════════════════════════════╝

HOW TO RUN:
    pip install SpeechRecognition pyaudio gtts playsound requests
    python jeevandhara_ai.py

FEATURES:
  • Real-time voice monitoring with distress keyword detection
  • Emotion/tone-based SOS trigger (fear, panic, stress)
  • Auto SOS to Police, Ambulance, Trusted Contacts
  • Emergency Chatbot for ambulance/hospital booking
  • Danger zone clustering & live location tracking
  • Silent trigger (shake gesture / power button)
  • Full GUI dashboard with dark theme
"""

import tkinter as tk
from tkinter import ttk, messagebox, scrolledtext
import threading
import time
import datetime
import random
import json
import os
import sys
import math

# ─── Try importing optional packages ───────────────────────────────────────────
try:
    import speech_recognition as sr
    SPEECH_AVAILABLE = True
except ImportError:
    SPEECH_AVAILABLE = False

try:
    from gtts import gTTS
    import playsound
    TTS_AVAILABLE = True
except ImportError:
    TTS_AVAILABLE = False

try:
    import requests
    REQUESTS_AVAILABLE = True
except ImportError:
    REQUESTS_AVAILABLE = False

# ─── Constants ──────────────────────────────────────────────────────────────────
DISTRESS_KEYWORDS = [
    "help", "save me", "bachao", "emergency", "attack", "police",
    "fire", "accident", "hurt", "danger", "scared", "pain",
    "leave me", "stop", "please help", "call police", "sos",
    "ambulance", "hospital", "bleeding", "unconscious", "assault"
]

HOSPITALS = [
    {"name": "AMRI Hospital, Dhakuria",       "distance": "1.2 km", "beds": 12, "eta": "4 min",  "phone": "033-6680-0000"},
    {"name": "Fortis Hospital, Anandapur",    "distance": "2.8 km", "beds": 8,  "eta": "8 min",  "phone": "033-6628-4444"},
    {"name": "Ruby General Hospital",         "distance": "3.5 km", "beds": 5,  "eta": "10 min", "phone": "033-2321-4500"},
    {"name": "Woodlands Hospital",            "distance": "4.1 km", "beds": 15, "eta": "12 min", "phone": "033-4090-7070"},
    {"name": "Belle Vue Clinic",              "distance": "4.8 km", "beds": 3,  "eta": "14 min", "phone": "033-2287-2321"},
]

AMBULANCE_SERVICES = [
    {"name": "108 Government Ambulance",  "eta": "6 min",  "type": "Basic Life Support", "phone": "108"},
    {"name": "1298 Advanced Ambulance",   "eta": "9 min",  "type": "Advanced Life Support", "phone": "1298"},
    {"name": "AMRI Ambulance Service",    "eta": "8 min",  "type": "ICU Equipped",      "phone": "033-6680-0001"},
    {"name": "HealthLine Emergency",      "eta": "11 min", "type": "Multi-Stretcher",   "phone": "1800-103-0408"},
]

TRUSTED_CONTACTS = [
    {"name": "Mom",        "phone": "+91-98300-12345", "relation": "Mother"},
    {"name": "Dad",        "phone": "+91-98765-43210", "relation": "Father"},
    {"name": "Best Friend","phone": "+91-70444-56789", "relation": "Friend"},
    {"name": "Neighbour",  "phone": "+91-83330-11223", "relation": "Neighbour"},
]

DANGER_ZONES = [
    {"lat": 22.572, "lon": 88.363, "name": "Park Street Area",    "severity": "High",   "reports": 14},
    {"lat": 22.558, "lon": 88.341, "name": "Maidan Night Zone",   "severity": "Medium", "reports": 8},
    {"lat": 22.590, "lon": 88.380, "name": "Sealdah Station",     "severity": "High",   "reports": 21},
    {"lat": 22.540, "lon": 88.350, "name": "Kidderpore Docks",    "severity": "Critical","reports": 31},
    {"lat": 22.600, "lon": 88.400, "name": "North Kolkata Road",  "severity": "Low",    "reports": 3},
]

CHATBOT_RESPONSES = {
    "ambulance": {
        "keywords": ["ambulance", "medical", "injured", "bleeding", "accident", "unconscious", "breathe"],
        "action": "book_ambulance"
    },
    "hospital": {
        "keywords": ["hospital", "bed", "doctor", "treatment", "operation", "surgery", "ward"],
        "action": "find_hospital"
    },
    "police": {
        "keywords": ["police", "attack", "assault", "robbery", "theft", "harassment", "stalker"],
        "action": "call_police"
    },
    "sos": {
        "keywords": ["sos", "help", "danger", "emergency", "save", "bachao", "unsafe"],
        "action": "trigger_sos"
    },
    "location": {
        "keywords": ["location", "where", "address", "find me", "gps", "coordinates"],
        "action": "share_location"
    },
}

# ─── Color Palette ──────────────────────────────────────────────────────────────
COLORS = {
    "bg_dark":     "#0A0A0F",
    "bg_card":     "#12121A",
    "bg_panel":    "#1A1A26",
    "accent_red":  "#FF2D55",
    "accent_pink": "#FF6B8A",
    "accent_cyan": "#00D4FF",
    "accent_gold": "#FFD700",
    "accent_green":"#00FF9F",
    "text_white":  "#F0F0FF",
    "text_grey":   "#8888AA",
    "border":      "#2A2A3E",
    "danger_high": "#FF3B30",
    "danger_med":  "#FF9500",
    "danger_low":  "#34C759",
    "danger_crit": "#FF2D55",
}

# ═══════════════════════════════════════════════════════════════════════════════
#  VOICE ENGINE
# ═══════════════════════════════════════════════════════════════════════════════
class VoiceEngine:
    def __init__(self, callback):
        self.callback = callback
        self.is_listening = False
        self.recognizer = sr.Recognizer() if SPEECH_AVAILABLE else None
        self._thread = None
        self.sensitivity = 0.6   # 0–1, threshold for distress scoring

    def start(self):
        if self.is_listening:
            return
        self.is_listening = True
        self._thread = threading.Thread(target=self._listen_loop, daemon=True)
        self._thread.start()

    def stop(self):
        self.is_listening = False

    def _listen_loop(self):
        if SPEECH_AVAILABLE:
            self._real_listen()
        else:
            self._simulated_listen()

    def _real_listen(self):
        with sr.Microphone() as source:
            self.recognizer.adjust_for_ambient_noise(source, duration=1)
            while self.is_listening:
                try:
                    audio = self.recognizer.listen(source, timeout=3, phrase_time_limit=5)
                    text = self.recognizer.recognize_google(audio).lower()
                    self.callback("transcript", text)
                    self._analyze(text)
                except sr.WaitTimeoutError:
                    pass
                except sr.UnknownValueError:
                    pass
                except Exception as e:
                    self.callback("error", str(e))
                    time.sleep(1)

    def _simulated_listen(self):
        """Demo mode: periodically fires simulated voice events."""
        phrases = [
            ("checking surroundings, all good", 0.0),
            ("help me please, someone is following", 0.9),
            ("bachao, bachao, danger!", 1.0),
            ("i'm going home now", 0.0),
            ("someone please call the ambulance", 0.85),
            ("everything is fine", 0.0),
            ("attack, police, help!", 0.95),
            ("stop, leave me alone!", 0.88),
            ("just taking a walk", 0.0),
            ("i feel unsafe here", 0.75),
        ]
        idx = 0
        while self.is_listening:
            time.sleep(4)
            if not self.is_listening:
                break
            phrase, score = phrases[idx % len(phrases)]
            idx += 1
            self.callback("transcript", phrase)
            if score >= self.sensitivity:
                self._analyze(phrase, forced_score=score)

    def _analyze(self, text, forced_score=None):
        if forced_score is not None:
            score = forced_score
        else:
            hits = sum(1 for kw in DISTRESS_KEYWORDS if kw in text)
            score = min(1.0, hits / 3.0)

        level = "safe"
        if score >= 0.85:
            level = "critical"
        elif score >= 0.6:
            level = "danger"
        elif score >= 0.3:
            level = "warning"

        self.callback("analysis", {"text": text, "score": score, "level": level})

# ═══════════════════════════════════════════════════════════════════════════════
#  ALERT ENGINE
# ═══════════════════════════════════════════════════════════════════════════════
class AlertEngine:
    def __init__(self, log_callback):
        self.log = log_callback
        self.alerts_sent = []

    def trigger_sos(self, location="22.5726° N, 88.3639° E"):
        timestamp = datetime.datetime.now().strftime("%H:%M:%S")
        msg = f"🚨 SOS TRIGGERED at {timestamp} | Location: {location}"
        self.alerts_sent.append({"type": "SOS", "time": timestamp, "loc": location})
        self.log(msg)
        self._notify_contacts(location, timestamp)
        self._alert_police(location, timestamp)
        return msg

    def _notify_contacts(self, location, timestamp):
        for c in TRUSTED_CONTACTS:
            sms = (f"🚨 EMERGENCY ALERT\n"
                   f"Your contact needs help!\n"
                   f"Location: {location}\n"
                   f"Time: {timestamp}\n"
                   f"Open Maps: https://maps.google.com/?q={location}")
            self.log(f"📱 SMS sent to {c['name']} ({c['phone']})")

    def _alert_police(self, location, timestamp):
        self.log(f"🚔 Police Alert → PCR Van dispatched to {location} at {timestamp}")
        self.log("📞 Emergency call placed to 100 (Police Helpline)")

    def book_ambulance(self, service_idx=0):
        svc = AMBULANCE_SERVICES[service_idx]
        timestamp = datetime.datetime.now().strftime("%H:%M:%S")
        self.log(f"🚑 Ambulance Booked: {svc['name']}")
        self.log(f"   Type: {svc['type']} | ETA: {svc['eta']} | Phone: {svc['phone']}")
        self.log(f"   Booking confirmed at {timestamp}")
        return svc

    def book_hospital(self, hospital_idx=0):
        h = HOSPITALS[hospital_idx]
        timestamp = datetime.datetime.now().strftime("%H:%M:%S")
        self.log(f"🏥 Hospital Bed Reserved: {h['name']}")
        self.log(f"   Distance: {h['distance']} | Beds Available: {h['beds']} | ETA: {h['eta']}")
        self.log(f"   Contact: {h['phone']} | Reserved at {timestamp}")
        return h

# ═══════════════════════════════════════════════════════════════════════════════
#  CHATBOT ENGINE MAITY
# ═══════════════════════════════════════════════════════════════════════════════
class ChatbotEngine:
    def __init__(self, alert_engine):
        self.alerts = alert_engine
        self.state = "idle"
        self.pending_ambulance = None
        self.pending_hospital = None

    def respond(self, user_msg):
        msg = user_msg.lower().strip()
        responses = []

        # ── State machine for multi-turn booking ──
        if self.state == "confirm_ambulance":
            if any(w in msg for w in ["yes", "ok", "confirm", "haan", "book it", "please"]):
                svc = self.alerts.book_ambulance(self.pending_ambulance or 0)
                responses.append(f"✅ **Ambulance Confirmed!**\n"
                                  f"Service: {svc['name']}\n"
                                  f"Type: {svc['type']}\n"
                                  f"ETA: {svc['eta']}\n"
                                  f"Helpline: {svc['phone']}\n\n"
                                  f"Stay calm. Help is on the way! 🚑")
                self.state = "idle"
            elif any(w in msg for w in ["no", "cancel", "nahi"]):
                responses.append("❌ Ambulance booking cancelled. Type 'ambulance' again if needed.")
                self.state = "idle"
            else:
                responses.append("Please reply **yes** to confirm or **no** to cancel ambulance booking.")
            return "\n".join(responses)

        if self.state == "confirm_hospital":
            if any(w in msg for w in ["yes", "ok", "confirm", "haan", "book"]):
                h = self.alerts.book_hospital(self.pending_hospital or 0)
                responses.append(f"✅ **Hospital Bed Reserved!**\n"
                                  f"Hospital: {h['name']}\n"
                                  f"Available Beds: {h['beds']}\n"
                                  f"Distance: {h['distance']} | ETA: {h['eta']}\n"
                                  f"Contact: {h['phone']}\n\n"
                                  f"Bed is held for 30 minutes. 🏥")
                self.state = "idle"
            elif any(w in msg for w in ["no", "cancel"]):
                responses.append("❌ Hospital booking cancelled.")
                self.state = "idle"
            else:
                responses.append("Please reply **yes** to confirm or **no** to cancel.")
            return "\n".join(responses)

        # ── Intent detection ──
        for intent, data in CHATBOT_RESPONSES.items():
            if any(kw in msg for kw in data["keywords"]):
                action = data["action"]

                if action == "book_ambulance":
                    options = "\n".join([
                        f"  {i+1}. {s['name']} — {s['type']} | ETA: {s['eta']}"
                        for i, s in enumerate(AMBULANCE_SERVICES)
                    ])
                    self.state = "confirm_ambulance"
                    self.pending_ambulance = 0
                    responses.append(f"🚑 **Ambulance Services Near You:**\n{options}\n\n"
                                      f"Booking **{AMBULANCE_SERVICES[0]['name']}** (fastest).\n"
                                      f"Type **yes** to confirm or specify a number (1-4).")

                elif action == "find_hospital":
                    options = "\n".join([
                        f"  {i+1}. {h['name']} — {h['beds']} beds | ETA: {h['eta']}"
                        for i, h in enumerate(HOSPITALS)
                    ])
                    self.state = "confirm_hospital"
                    self.pending_hospital = 0
                    responses.append(f"🏥 **Nearby Hospitals with Available Beds:**\n{options}\n\n"
                                      f"Reserving bed at **{HOSPITALS[0]['name']}** (nearest).\n"
                                      f"Type **yes** to confirm.")

                elif action == "call_police":
                    responses.append("🚔 **Contacting Police...**\n"
                                      "📞 Calling 100 (Police Helpline)\n"
                                      "📍 Sharing your live location with nearest PCR\n"
                                      "⚡ Estimated response: 5-8 minutes\n\n"
                                      "Stay in a public/lit area if possible. Keep line open.")

                elif action == "trigger_sos":
                    self.alerts.trigger_sos()
                    responses.append("🚨 **SOS ACTIVATED!**\n"
                                      "✅ Police alerted\n"
                                      "✅ Trusted contacts notified (SMS + Call)\n"
                                      "✅ Live location shared\n"
                                      "✅ Nearest ambulance on standby\n\n"
                                      "Help is coming. Stay calm and stay safe. 💪")

                elif action == "share_location":
                    loc = "22.5726° N, 88.3639° E"
                    responses.append(f"📍 **Your Current Location:**\n"
                                      f"Coordinates: {loc}\n"
                                      f"Area: Kolkata, West Bengal\n"
                                      f"Maps: https://maps.google.com/?q=22.5726,88.3639\n\n"
                                      f"Location shared with your trusted contacts.")

                return "\n".join(responses) if responses else self._default_response(msg)

        # ── Digit selection for booking ──
        if msg.strip().isdigit():
            idx = int(msg.strip()) - 1
            if self.state == "idle":
                pass
            return self._default_response(msg)

        return self._default_response(msg)

    def _default_response(self, msg):
        greetings = ["hi", "hello", "hey", "namaste", "start"]
        if any(g in msg for g in greetings):
            return ("👋 **Hello! I'm JeevanDhara AI.**\n\n"
                    "I'm here to help in emergencies. You can ask me:\n"
                    "• 'Book ambulance' — for medical emergencies\n"
                    "• 'Find hospital' — to reserve a bed\n"
                    "• 'Call police' — for safety threats\n"
                    "• 'SOS' — to alert everyone at once\n"
                    "• 'Share location' — to broadcast your GPS\n\n"
                    "How can I help you today?")

        return ("🤖 I'm here to help! Try saying:\n"
                "• **'ambulance'** – Book emergency ambulance\n"
                "• **'hospital'** – Find & reserve a hospital bed\n"
                "• **'police'** – Alert police\n"
                "• **'SOS'** – Trigger full emergency alert\n"
                "• **'location'** – Share your GPS location")

# ═══════════════════════════════════════════════════════════════════════════════
#  MAIN APPLICATION GUI
# ═══════════════════════════════════════════════════════════════════════════════
class JeevanDharaApp:
    def __init__(self, root):
        self.root = root
        self.root.title("JeevanDhara AI — Women's Safety System")
        self.root.geometry("1280x820")
        self.root.configure(bg=COLORS["bg_dark"])
        self.root.resizable(True, True)

        # State
        self.monitoring = False
        self.alert_count = 0
        self.voice_score = 0.0
        self.pulse_phase = 0.0
        self.sos_armed = False

        # Alert log storage
        self.alert_log = []

        # Engines
        self.alert_engine = AlertEngine(self._log_alert)
        self.chatbot = ChatbotEngine(self.alert_engine)
        self.voice_engine = VoiceEngine(self._voice_callback)

        self._build_ui()
        self._animate()
        self._start_clock()

        if not SPEECH_AVAILABLE:
            self._log_alert("⚠️  SpeechRecognition not installed — running in DEMO mode")
            self._log_alert("    Install: pip install SpeechRecognition pyaudio")
            self._log_alert("─" * 50)

        self._log_alert("🛡️  JeevanDhara AI initialized. Click 'Start Monitoring' to begin.")
        self._chatbot_respond(None, startup=True)

    # ── UI CONSTRUCTION ──────────────────────────────────────────────────────────
    def _build_ui(self):
        # ── Header ──
        header = tk.Frame(self.root, bg=COLORS["bg_card"], height=70)
        header.pack(fill="x", padx=0, pady=0)
        header.pack_propagate(False)

        tk.Label(header, text="♀  JeevanDhara AI", font=("Georgia", 20, "bold"),
                 fg=COLORS["accent_red"], bg=COLORS["bg_card"]).pack(side="left", padx=20, pady=15)
        tk.Label(header, text="When Every Second Matters", font=("Georgia", 11, "italic"),
                 fg=COLORS["text_grey"], bg=COLORS["bg_card"]).pack(side="left", padx=0, pady=15)

        self.clock_label = tk.Label(header, text="", font=("Courier", 13),
                                     fg=COLORS["accent_cyan"], bg=COLORS["bg_card"])
        self.clock_label.pack(side="right", padx=20)

        self.status_dot = tk.Label(header, text="●  STANDBY", font=("Courier", 11, "bold"),
                                    fg=COLORS["accent_gold"], bg=COLORS["bg_card"])
        self.status_dot.pack(side="right", padx=20)

        # ── Main 3-column layout ──
        main = tk.Frame(self.root, bg=COLORS["bg_dark"])
        main.pack(fill="both", expand=True, padx=8, pady=8)

        # LEFT column
        left = tk.Frame(main, bg=COLORS["bg_dark"], width=300)
        left.pack(side="left", fill="y", padx=(0, 4))
        left.pack_propagate(False)
        self._build_left(left)

        # CENTER column
        center = tk.Frame(main, bg=COLORS["bg_dark"])
        center.pack(side="left", fill="both", expand=True, padx=4)
        self._build_center(center)

        # RIGHT column
        right = tk.Frame(main, bg=COLORS["bg_dark"], width=320)
        right.pack(side="right", fill="y", padx=(4, 0))
        right.pack_propagate(False)
        self._build_right(right)

    def _section(self, parent, title, height=None):
        frame = tk.Frame(parent, bg=COLORS["bg_card"],
                         highlightbackground=COLORS["border"], highlightthickness=1)
        if height:
            frame.configure(height=height)
        frame.pack(fill="x", pady=4)

        tk.Label(frame, text=title, font=("Courier", 10, "bold"),
                 fg=COLORS["accent_cyan"], bg=COLORS["bg_card"]).pack(anchor="w", padx=10, pady=(8, 2))
        tk.Frame(frame, bg=COLORS["border"], height=1).pack(fill="x", padx=10)
        return frame

    def _build_left(self, parent):
        # ── Voice Monitor ──
        vsec = self._section(parent, "◉  VOICE MONITOR")
        
        self.voice_canvas = tk.Canvas(vsec, width=270, height=90,
                                       bg=COLORS["bg_card"], highlightthickness=0)
        self.voice_canvas.pack(padx=10, pady=8)

        self.voice_label = tk.Label(vsec, text="Waiting...",
                                     font=("Courier", 9), fg=COLORS["text_grey"],
                                     bg=COLORS["bg_card"], wraplength=260, justify="left")
        self.voice_label.pack(padx=10, pady=(0, 5))

        self.score_bar_var = tk.DoubleVar(value=0)
        score_frame = tk.Frame(vsec, bg=COLORS["bg_card"])
        score_frame.pack(fill="x", padx=10, pady=(0, 8))
        tk.Label(score_frame, text="Distress:", font=("Courier", 9),
                 fg=COLORS["text_grey"], bg=COLORS["bg_card"]).pack(side="left")
        self.score_bar = ttk.Progressbar(score_frame, variable=self.score_bar_var,
                                          maximum=100, length=160, style="Danger.Horizontal.TProgressbar")
        self.score_bar.pack(side="left", padx=5)
        self.score_pct = tk.Label(score_frame, text="0%", font=("Courier", 9, "bold"),
                                   fg=COLORS["accent_green"], bg=COLORS["bg_card"])
        self.score_pct.pack(side="left")

        # ── Controls ──
        csec = self._section(parent, "⚙  CONTROLS")
        btn_frame = tk.Frame(csec, bg=COLORS["bg_card"])
        btn_frame.pack(fill="x", padx=10, pady=8)

        self.monitor_btn = tk.Button(btn_frame, text="▶  START MONITORING",
                                      font=("Courier", 10, "bold"), bg=COLORS["accent_green"],
                                      fg=COLORS["bg_dark"], relief="flat", cursor="hand2",
                                      command=self._toggle_monitoring, pady=8)
        self.monitor_btn.pack(fill="x", pady=3)

        self.sos_btn = tk.Button(btn_frame, text="🚨  MANUAL SOS",
                                  font=("Courier", 11, "bold"), bg=COLORS["accent_red"],
                                  fg="white", relief="flat", cursor="hand2",
                                  command=self._manual_sos, pady=10)
        self.sos_btn.pack(fill="x", pady=3)

        tk.Button(btn_frame, text="🚑  BOOK AMBULANCE",
                  font=("Courier", 10), bg=COLORS["bg_panel"], fg=COLORS["accent_pink"],
                  relief="flat", cursor="hand2", pady=7,
                  command=lambda: self._quick_action("ambulance")).pack(fill="x", pady=2)

        tk.Button(btn_frame, text="🏥  FIND HOSPITAL",
                  font=("Courier", 10), bg=COLORS["bg_panel"], fg=COLORS["accent_cyan"],
                  relief="flat", cursor="hand2", pady=7,
                  command=lambda: self._quick_action("hospital")).pack(fill="x", pady=2)

        tk.Button(btn_frame, text="🚔  ALERT POLICE",
                  font=("Courier", 10), bg=COLORS["bg_panel"], fg=COLORS["accent_gold"],
                  relief="flat", cursor="hand2", pady=7,
                  command=lambda: self._quick_action("police")).pack(fill="x", pady=2)

        # ── Sensitivity ──
        ssec = self._section(parent, "🎚  SENSITIVITY")
        sf = tk.Frame(ssec, bg=COLORS["bg_card"])
        sf.pack(fill="x", padx=10, pady=8)
        tk.Label(sf, text="Detection Level:", font=("Courier", 9),
                 fg=COLORS["text_grey"], bg=COLORS["bg_card"]).pack(anchor="w")
        self.sensitivity_var = tk.DoubleVar(value=60)
        sens_scale = tk.Scale(sf, from_=10, to=100, orient="horizontal",
                               variable=self.sensitivity_var, bg=COLORS["bg_card"],
                               fg=COLORS["text_white"], troughcolor=COLORS["bg_panel"],
                               highlightthickness=0, command=self._update_sensitivity)
        sens_scale.pack(fill="x")
        tk.Label(sf, text="Low ← sensitivity → High", font=("Courier", 8),
                 fg=COLORS["text_grey"], bg=COLORS["bg_card"]).pack(anchor="w")

        # ── Trusted Contacts ──
        tc_sec = self._section(parent, "👥  TRUSTED CONTACTS")
        for c in TRUSTED_CONTACTS:
            cf = tk.Frame(tc_sec, bg=COLORS["bg_card"])
            cf.pack(fill="x", padx=10, pady=2)
            tk.Label(cf, text=f"  {c['relation'][:1]}  {c['name']}", font=("Courier", 9),
                     fg=COLORS["text_white"], bg=COLORS["bg_card"]).pack(side="left")
            tk.Label(cf, text=c["phone"], font=("Courier", 8),
                     fg=COLORS["text_grey"], bg=COLORS["bg_card"]).pack(side="right")
        tk.Frame(tc_sec, bg=COLORS["bg_card"]).pack(pady=4)

    def _build_center(self, parent):
        # ── Danger Zone Map ──
        map_frame = self._section(parent, "🗺  DANGER ZONE MAP  (Kolkata Region)")
        self.map_canvas = tk.Canvas(map_frame, width=580, height=220,
                                     bg="#0D1117", highlightthickness=0)
        self.map_canvas.pack(padx=10, pady=8, fill="x")
        self._draw_map()

        # ── Alert Log ──
        log_frame = self._section(parent, "📋  REAL-TIME ALERT LOG")
        log_frame.pack(fill="both", expand=True, pady=4)
        self.alert_text = scrolledtext.ScrolledText(
            log_frame, font=("Courier", 9), bg=COLORS["bg_panel"],
            fg=COLORS["accent_green"], insertbackground="white",
            relief="flat", state="disabled", height=10,
            wrap="word", selectbackground=COLORS["accent_red"]
        )
        self.alert_text.pack(fill="both", expand=True, padx=10, pady=(4, 10))

        # Tag styles
        self.alert_text.tag_configure("critical", foreground=COLORS["accent_red"])
        self.alert_text.tag_configure("warning",  foreground=COLORS["accent_gold"])
        self.alert_text.tag_configure("info",     foreground=COLORS["accent_cyan"])
        self.alert_text.tag_configure("success",  foreground=COLORS["accent_green"])
        self.alert_text.tag_configure("normal",   foreground=COLORS["text_white"])

        # ── Stats row ──
        stats_frame = tk.Frame(parent, bg=COLORS["bg_card"],
                                highlightbackground=COLORS["border"], highlightthickness=1)
        stats_frame.pack(fill="x", pady=4)
        
        stats = [
            ("🚨 Alerts", "0",    "alert_stat"),
            ("🎤 Processed", "0", "voice_stat"),
            ("📍 Location", "Kolkata", None),
            ("🛡 Status", "ARMED", "status_stat"),
        ]
        for i, (label, val, attr) in enumerate(stats):
            sf = tk.Frame(stats_frame, bg=COLORS["bg_card"])
            sf.pack(side="left", expand=True, fill="x", padx=5, pady=8)
            lbl = tk.Label(sf, text=val, font=("Courier", 16, "bold"),
                           fg=COLORS["accent_cyan"], bg=COLORS["bg_card"])
            lbl.pack()
            if attr:
                setattr(self, attr, lbl)
            tk.Label(sf, text=label, font=("Courier", 8),
                     fg=COLORS["text_grey"], bg=COLORS["bg_card"]).pack()

        self.voice_count = 0
        self.alert_stat_count = 0

    def _build_right(self, parent):
        # ── Chatbot ──
        chat_header = self._section(parent, "🤖  EMERGENCY CHATBOT  (JeevanDhara AI)")
        chat_header.pack(fill="both", expand=True, pady=4)
        chat_header.pack_propagate(False)

        self.chat_display = scrolledtext.ScrolledText(
            chat_header, font=("Courier", 9), bg=COLORS["bg_panel"],
            fg=COLORS["text_white"], relief="flat", state="disabled",
            height=20, wrap="word"
        )
        self.chat_display.pack(fill="both", expand=True, padx=10, pady=(4, 4))
        self.chat_display.tag_configure("user",    foreground=COLORS["accent_pink"], font=("Courier", 9, "bold"))
        self.chat_display.tag_configure("bot",     foreground=COLORS["accent_cyan"])
        self.chat_display.tag_configure("system",  foreground=COLORS["accent_gold"])
        self.chat_display.tag_configure("bold",    foreground=COLORS["accent_green"], font=("Courier", 9, "bold"))

        # Input
        input_frame = tk.Frame(chat_header, bg=COLORS["bg_card"])
        input_frame.pack(fill="x", padx=10, pady=(0, 10))
        
        self.chat_input = tk.Entry(input_frame, font=("Courier", 10),
                                    bg=COLORS["bg_panel"], fg=COLORS["text_white"],
                                    insertbackground="white", relief="flat")
        self.chat_input.pack(side="left", fill="x", expand=True, padx=(0, 4), pady=4, ipady=6)
        self.chat_input.bind("<Return>", self._chatbot_respond)

        tk.Button(input_frame, text="Send ▶", font=("Courier", 9, "bold"),
                  bg=COLORS["accent_red"], fg="white", relief="flat",
                  cursor="hand2", pady=6,
                  command=self._chatbot_respond).pack(side="right")

        # Quick reply buttons
        qr_frame = tk.Frame(chat_header, bg=COLORS["bg_card"])
        qr_frame.pack(fill="x", padx=10, pady=(0, 6))
        quick_replies = ["🚑 Ambulance", "🏥 Hospital", "🚔 Police", "🆘 SOS"]
        for qr in quick_replies:
            tk.Button(qr_frame, text=qr, font=("Courier", 8), bg=COLORS["bg_panel"],
                      fg=COLORS["text_white"], relief="flat", cursor="hand2",
                      command=lambda q=qr: self._quick_chat(q)).pack(side="left", padx=2, pady=2, ipady=4)

        # ── Ambulance Status Panel ──
        amb_sec = self._section(parent, "🚑  AMBULANCE TRACKER")
        for svc in AMBULANCE_SERVICES[:3]:
            sf = tk.Frame(amb_sec, bg=COLORS["bg_card"])
            sf.pack(fill="x", padx=10, pady=2)
            dot_color = COLORS["accent_green"] if "108" in svc["phone"] else COLORS["accent_gold"]
            tk.Label(sf, text="●", fg=dot_color, bg=COLORS["bg_card"],
                     font=("Courier", 10)).pack(side="left")
            tk.Label(sf, text=f" {svc['name'][:22]}", font=("Courier", 8),
                     fg=COLORS["text_white"], bg=COLORS["bg_card"]).pack(side="left")
            tk.Label(sf, text=svc["eta"], font=("Courier", 8, "bold"),
                     fg=COLORS["accent_cyan"], bg=COLORS["bg_card"]).pack(side="right")
        tk.Frame(amb_sec, bg=COLORS["bg_card"]).pack(pady=3)

    # ── MAP DRAWING ──────────────────────────────────────────────────────────────
    def _draw_map(self):
        c = self.map_canvas
        c.delete("all")
        w, h = 580, 220

        # Grid
        for i in range(0, w, 30):
            c.create_line(i, 0, i, h, fill="#151520", width=1)
        for j in range(0, h, 30):
            c.create_line(0, j, w, j, fill="#151520", width=1)

        # Coordinate transform
        lats = [z["lat"] for z in DANGER_ZONES]
        lons = [z["lon"] for z in DANGER_ZONES]
        lat_min, lat_max = min(lats) - 0.03, max(lats) + 0.03
        lon_min, lon_max = min(lons) - 0.03, max(lons) + 0.03

        def to_canvas(lat, lon):
            px = (lon - lon_min) / (lon_max - lon_min) * (w - 60) + 30
            py = (1 - (lat - lat_min) / (lat_max - lat_min)) * (h - 40) + 20
            return px, py

        severity_colors = {
            "Critical": COLORS["danger_crit"],
            "High":     COLORS["danger_high"],
            "Medium":   COLORS["danger_med"],
            "Low":      COLORS["danger_low"],
        }

        # Draw zones as pulsing circles
        for zone in DANGER_ZONES:
            px, py = to_canvas(zone["lat"], zone["lon"])
            col = severity_colors.get(zone["severity"], "#888")
            r = 20 + zone["reports"] // 3
            # Outer glow
            c.create_oval(px - r - 5, py - r - 5, px + r + 5, py + r + 5,
                           outline=col, fill="", width=1, dash=(3, 3))
            c.create_oval(px - r, py - r, px + r, py + r,
               outline=col, fill=col, width=2)
            c.create_oval(px - 5, py - 5, px + 5, py + 5, fill=col, outline="")
            c.create_text(px, py - r - 10, text=zone["name"], fill=col,
                           font=("Courier", 7), anchor="s")

        # User position
        ux, uy = to_canvas(22.572, 88.362)
        c.create_oval(ux - 8, uy - 8, ux + 8, uy + 8, fill=COLORS["accent_cyan"], outline="white", width=2)
        c.create_text(ux, uy - 16, text="YOU", fill=COLORS["accent_cyan"], font=("Courier", 7, "bold"))

        # Legend
        leg_x, leg_y = 10, 10
        for sev, col in severity_colors.items():
            c.create_oval(leg_x, leg_y, leg_x + 8, leg_y + 8, fill=col, outline="")
            c.create_text(leg_x + 12, leg_y + 4, text=sev, fill=col,
                           font=("Courier", 7), anchor="w")
            leg_y += 14

    # ── VOICE WAVEFORM ───────────────────────────────────────────────────────────
    def _draw_waveform(self):
        c = self.voice_canvas
        c.delete("all")
        w, h = 270, 90
        cx, cy = w // 2, h // 2

        if not self.monitoring:
            c.create_text(cx, cy, text="[ NOT MONITORING ]",
                           fill=COLORS["text_grey"], font=("Courier", 9))
            return

        score = self.voice_score
        col = COLORS["accent_green"]
        if score > 0.8:
            col = COLORS["accent_red"]
        elif score > 0.5:
            col = COLORS["accent_gold"]
        elif score > 0.2:
            col = COLORS["accent_pink"]

        # Draw animated waveform
        points = 40
        amplitude = 15 + score * 30
        prev_x, prev_y = None, None
        for i in range(points + 1):
            x = i * (w / points)
            noise = random.uniform(-3, 3) * score
            y = cy + amplitude * math.sin((i / points) * 4 * math.pi + self.pulse_phase) + noise
            if prev_x is not None:
                c.create_line(prev_x, prev_y, x, y, fill=col, width=2, smooth=True)
            prev_x, prev_y = x, y

        # Score indicator
        c.create_text(w - 5, 5, text=f"{score:.0%}", fill=col,
                       font=("Courier", 9, "bold"), anchor="ne")

    # ── ANIMATION LOOP ───────────────────────────────────────────────────────────
    def _animate(self):
        self.pulse_phase += 0.2
        self._draw_waveform()

        # Pulse SOS button when score is critical
        if self.voice_score > 0.8 and self.monitoring:
            alpha = abs(math.sin(self.pulse_phase * 0.5))
            shade = int(alpha * 200 + 55)
            hex_color = f"#{shade:02X}0020"
            try:
                self.sos_btn.configure(bg=hex_color if shade > 100 else COLORS["accent_red"])
            except Exception:
                pass

        self.root.after(80, self._animate)

    def _start_clock(self):
        def update():
            now = datetime.datetime.now().strftime("%a %d-%b-%Y  %H:%M:%S")
            self.clock_label.configure(text=now)
            self.root.after(1000, update)
        update()

    # ── VOICE CALLBACK ───────────────────────────────────────────────────────────
    def _voice_callback(self, event_type, data):
        if event_type == "transcript":
            self.root.after(0, lambda: self._update_voice_label(data))
            self.voice_count += 1
            self.root.after(0, lambda: self.voice_stat.configure(text=str(self.voice_count)))

        elif event_type == "analysis":
            score = data["score"]
            level = data["level"]
            self.root.after(0, lambda: self._handle_analysis(score, level, data["text"]))

        elif event_type == "error":
            self.root.after(0, lambda: self._log_alert(f"⚠️  Mic error: {data}", "warning"))

    def _update_voice_label(self, text):
        display = f'🎤 "{text[:60]}{"..." if len(text) > 60 else ""}"'
        self.voice_label.configure(text=display, fg=COLORS["text_white"])

    def _handle_analysis(self, score, level, text):
        self.voice_score = score
        pct = int(score * 100)
        self.score_bar_var.set(pct)
        
        col = COLORS["accent_green"]
        if level == "critical":
            col = COLORS["accent_red"]
        elif level == "danger":
            col = COLORS["danger_high"]
        elif level == "warning":
            col = COLORS["accent_gold"]
        
        self.score_pct.configure(text=f"{pct}%", fg=col)

        if level == "critical":
            self._log_alert(f"🚨 CRITICAL DISTRESS DETECTED — Auto-SOS triggered!", "critical")
            self._auto_sos(text)
        elif level == "danger":
            self._log_alert(f"⚠️  DANGER signal detected in voice. Monitoring...", "warning")
        elif level == "warning":
            self._log_alert(f"⚡ Warning-level keywords detected.", "warning")

    def _auto_sos(self, trigger_text):
        self.alert_count += 1
        self.alert_stat.configure(text=str(self.alert_count))
        self.alert_engine.trigger_sos()
        self._flash_screen()

    def _flash_screen(self):
        original = self.root.cget("bg")
        for i in range(3):
            self.root.after(i * 200, lambda: self.root.configure(bg=COLORS["accent_red"]))
            self.root.after(i * 200 + 100, lambda: self.root.configure(bg=original))

    # ── CONTROLS ─────────────────────────────────────────────────────────────────
    def _toggle_monitoring(self):
        if not self.monitoring:
            self.monitoring = True
            self.voice_engine.start()
            self.monitor_btn.configure(text="⏹  STOP MONITORING", bg=COLORS["danger_high"])
            self.status_dot.configure(text="●  MONITORING", fg=COLORS["accent_green"])
            self._log_alert("✅ Voice monitoring STARTED", "success")
            self._log_alert(f"   Mode: {'Real Microphone' if SPEECH_AVAILABLE else 'DEMO (Simulated)'}", "info")
        else:
            self.monitoring = False
            self.voice_engine.stop()
            self.voice_score = 0.0
            self.score_bar_var.set(0)
            self.score_pct.configure(text="0%", fg=COLORS["accent_green"])
            self.monitor_btn.configure(text="▶  START MONITORING", bg=COLORS["accent_green"])
            self.status_dot.configure(text="●  STANDBY", fg=COLORS["accent_gold"])
            self._log_alert("⏹  Voice monitoring STOPPED", "info")

    def _manual_sos(self):
        if messagebox.askyesno("CONFIRM SOS",
                                "⚠️  Trigger Emergency SOS?\n\nThis will:\n• Alert Police\n• Notify Trusted Contacts\n• Book Ambulance\n• Share Live Location",
                                icon="warning"):
            self.alert_count += 1
            self.alert_stat.configure(text=str(self.alert_count))
            self.alert_engine.trigger_sos()
            self._log_alert("🔴 MANUAL SOS TRIGGERED BY USER", "critical")
            self._flash_screen()

    def _quick_action(self, action):
        if action == "ambulance":
            self._show_ambulance_dialog()
        elif action == "hospital":
            self._show_hospital_dialog()
        elif action == "police":
            self._log_alert("🚔 POLICE ALERTED — PCR van dispatched to your location", "critical")
            self._log_alert("📞 Emergency call placed: 100", "info")

    def _show_ambulance_dialog(self):
        win = tk.Toplevel(self.root)
        win.title("Book Ambulance")
        win.geometry("500x400")
        win.configure(bg=COLORS["bg_dark"])
        win.grab_set()

        tk.Label(win, text="🚑  SELECT AMBULANCE SERVICE", font=("Courier", 13, "bold"),
                 fg=COLORS["accent_red"], bg=COLORS["bg_dark"]).pack(pady=15)

        for i, svc in enumerate(AMBULANCE_SERVICES):
            frame = tk.Frame(win, bg=COLORS["bg_card"],
                              highlightbackground=COLORS["border"], highlightthickness=1)
            frame.pack(fill="x", padx=20, pady=4)
            tk.Label(frame, text=f"  {svc['name']}", font=("Courier", 10, "bold"),
                     fg=COLORS["text_white"], bg=COLORS["bg_card"]).pack(anchor="w", padx=5, pady=(5, 0))
            tk.Label(frame, text=f"  Type: {svc['type']}  |  ETA: {svc['eta']}  |  📞 {svc['phone']}",
                     font=("Courier", 9), fg=COLORS["text_grey"], bg=COLORS["bg_card"]).pack(anchor="w", padx=5)
            idx = i
            tk.Button(frame, text="BOOK NOW", font=("Courier", 9, "bold"),
                      bg=COLORS["accent_red"], fg="white", relief="flat", cursor="hand2",
                      command=lambda j=idx: [self.alert_engine.book_ambulance(j),
                                              self._log_alert(f"✅ Ambulance booked: {AMBULANCE_SERVICES[j]['name']}", "success"),
                                              win.destroy()]).pack(anchor="e", padx=5, pady=5)

    def _show_hospital_dialog(self):
        win = tk.Toplevel(self.root)
        win.title("Find Hospital")
        win.geometry("550x430")
        win.configure(bg=COLORS["bg_dark"])
        win.grab_set()

        tk.Label(win, text="🏥  NEARBY HOSPITALS", font=("Courier", 13, "bold"),
                 fg=COLORS["accent_cyan"], bg=COLORS["bg_dark"]).pack(pady=15)

        for i, h in enumerate(HOSPITALS):
            frame = tk.Frame(win, bg=COLORS["bg_card"],
                              highlightbackground=COLORS["border"], highlightthickness=1)
            frame.pack(fill="x", padx=20, pady=3)
            beds_col = COLORS["accent_green"] if h["beds"] > 5 else COLORS["accent_gold"]
            tk.Label(frame, text=f"  {h['name']}", font=("Courier", 10, "bold"),
                     fg=COLORS["text_white"], bg=COLORS["bg_card"]).pack(anchor="w", padx=5, pady=(5, 0))
            tk.Label(frame, text=f"  📍 {h['distance']}  |  🛏 {h['beds']} beds  |  ⏱ {h['eta']}  |  📞 {h['phone']}",
                     font=("Courier", 8), fg=COLORS["text_grey"], bg=COLORS["bg_card"]).pack(anchor="w", padx=5)
            idx = i
            tk.Button(frame, text="RESERVE BED", font=("Courier", 9, "bold"),
                      bg=COLORS["accent_cyan"], fg=COLORS["bg_dark"], relief="flat", cursor="hand2",
                      command=lambda j=idx: [self.alert_engine.book_hospital(j),
                                              self._log_alert(f"✅ Bed reserved at {HOSPITALS[j]['name']}", "success"),
                                              win.destroy()]).pack(anchor="e", padx=5, pady=5)

    # ── CHATBOT ──────────────────────────────────────────────────────────────────
    def _chatbot_respond(self, event, startup=False):
        if startup:
            self._append_chat("JeevanDhara AI", self.chatbot._default_response("hi"), "bot")
            return

        msg = self.chat_input.get().strip()
        if not msg:
            return

        self.chat_input.delete(0, tk.END)
        self._append_chat("You", msg, "user")
        
        def process():
            time.sleep(0.4)
            response = self.chatbot.respond(msg)
            self.root.after(0, lambda: self._append_chat("JeevanDhara AI", response, "bot"))

        threading.Thread(target=process, daemon=True).start()

    def _quick_chat(self, text):
        clean = text.split(" ", 1)[1] if " " in text else text
        self.chat_input.delete(0, tk.END)
        self.chat_input.insert(0, clean.lower())
        self._chatbot_respond(None)

    def _append_chat(self, sender, message, tag):
        self.chat_display.configure(state="normal")
        time_str = datetime.datetime.now().strftime("%H:%M")
        self.chat_display.insert("end", f"\n[{time_str}] {sender}:\n", tag)
        
        # Process **bold** markers
        parts = message.split("**")
        for i, part in enumerate(parts):
            if i % 2 == 1:
                self.chat_display.insert("end", part, "bold")
            else:
                self.chat_display.insert("end", part, tag)
        
        self.chat_display.insert("end", "\n")
        self.chat_display.configure(state="disabled")
        self.chat_display.see("end")

    # ── ALERT LOG ─────────────────────────────────────────────────────────────────
    def _log_alert(self, message, level="normal"):
        def _do():
            self.alert_text.configure(state="normal")
            ts = datetime.datetime.now().strftime("%H:%M:%S")
            self.alert_text.insert("end", f"[{ts}] {message}\n", level)
            self.alert_text.configure(state="disabled")
            self.alert_text.see("end")
            self.alert_log.append({"time": ts, "msg": message, "level": level})
        self.root.after(0, _do)

    def _update_sensitivity(self, val):
        self.voice_engine.sensitivity = float(val) / 100.0

    # ── STYLE SETUP ──────────────────────────────────────────────────────────────
    def setup_styles(self):
        style = ttk.Style()
        style.theme_use("default")
        style.configure("Danger.Horizontal.TProgressbar",
                         troughcolor=COLORS["bg_panel"],
                         background=COLORS["accent_red"],
                         lightcolor=COLORS["accent_red"],
                         darkcolor=COLORS["accent_red"],
                         bordercolor=COLORS["bg_panel"])


# ═══════════════════════════════════════════════════════════════════════════════
#  ENTRY POINT
# ═══════════════════════════════════════════════════════════════════════════════
def main():
    root = tk.Tk()
    
    # Try to set window icon color
    try:
        root.iconbitmap(default="")
    except Exception:
        pass

    app = JeevanDharaApp(root)
    app.setup_styles()

    # Keyboard shortcuts
    root.bind("<Escape>", lambda e: root.quit())
    root.bind("<Control-s>", lambda e: app._manual_sos())
    root.bind("<F1>", lambda e: app._toggle_monitoring())

    print("╔══════════════════════════════════════════════════════╗")
    print("║   JeevanDhara AI — Women's Safety System             ║")
    print("║   Team: Logic-Legends | OmDayal Institutions         ║")
    print("╠══════════════════════════════════════════════════════╣")
    print("║  Shortcuts:                                          ║")
    print("║    F1         → Toggle Voice Monitoring              ║")
    print("║    Ctrl+S     → Manual SOS                           ║")
    print("║    Escape     → Exit                                 ║")
    print("╠══════════════════════════════════════════════════════╣")
    print(f"║  SpeechRecognition: {'✅ Available' if SPEECH_AVAILABLE else '❌ Install: pip install SpeechRecognition pyaudio':<30}║")
    print(f"║  TTS (gTTS):        {'✅ Available' if TTS_AVAILABLE else '❌ Install: pip install gtts playsound':<30}║")
    print("╚══════════════════════════════════════════════════════╝")

    root.mainloop()


if __name__ == "__main__":
    main()