from flask import Flask, render_template, request, jsonify
from flask_cors import CORS
import requests
import datetime
import json

app = Flask(__name__)
CORS(app)

FIREBASE_URL = "https://crisisnet-f5b21-default-rtdb.firebaseio.com"
GEMINI_API_KEY = "AIzaSyA8tnKO8KrxkazV4tCFk8HE5G9KHI83tYM"
GEMINI_URL = f"https://generativelanguage.googleapis.com/v1beta/models/gemini-1.5-flash:generateContent?key={GEMINI_API_KEY}"

USERS = {
    "manager":  {"password": "manager123", "role": "Manager", "hotel": "Grand Palace Hotel"},
    "staff":    {"password": "staff123",   "role": "Staff",   "hotel": "Grand Palace Hotel"},
    "security": {"password": "security123","role": "Security","hotel": "Grand Palace Hotel"},
    "manager2": {"password": "manager123", "role": "Manager", "hotel": "Ocean View Resort"},
    "staff2":   {"password": "staff123",   "role": "Staff",   "hotel": "Ocean View Resort"},
}

HOTELS = {
    "Grand Palace Hotel": {"floors": ["Ground Floor","Floor 1","Floor 2","Floor 3","Rooftop"], "locations": ["Main Lobby","Restaurant","Kitchen","Swimming Pool","Conference Hall","Gym","Parking","Floor 1 Rooms","Floor 2 Rooms","Floor 3 Rooms"]},
    "Ocean View Resort":  {"floors": ["Ground Floor","Floor 1","Floor 2","Beachside"], "locations": ["Reception","Beach Area","Pool Deck","Spa","Restaurant","Parking","Floor 1","Floor 2"]},
}

PROTOCOLS = {
    "Fire":     {"protocol": "IMMEDIATE ACTIONS:\n1. Activate fire alarm and call 101 immediately\n2. Evacuate all guests via emergency exits - NO elevators\n3. Account for all staff at assembly point\n\nSTAFF DUTIES:\n- Front Desk: Call 101, log time, notify management\n- Housekeeping: Sweep all floors, guide guests to exits\n- Security: Keep emergency exits clear, control crowd\n\nGUEST COMMUNICATION:\nDear Guests, please calmly proceed to the nearest emergency exit. Staff will guide you.\n\nESCALATION:\nCall 101 if fire spreads beyond one zone.", "guest": "Dear Guests, for your safety, please calmly proceed to the nearest emergency exit. Our trained staff are here to assist you.", "color": "E63946", "icon": "🔥"},
    "Medical":  {"protocol": "IMMEDIATE ACTIONS:\n1. Call 102 (Ambulance) immediately\n2. Send trained first-aider to patient NOW\n3. Clear area around patient\n\nSTAFF DUTIES:\n- Front Desk: Call 102, guide paramedics\n- Concierge: Meet ambulance at entrance\n- Security: Keep crowd away from patient\n\nGUEST COMMUNICATION:\nDear Guests, a medical situation is being handled by our trained staff.\n\nESCALATION:\nBegin CPR if patient unconscious.", "guest": "Dear Guests, our medical response team is handling a situation. Please remain calm.", "color": "F4A261", "icon": "🏥"},
    "Security": {"protocol": "IMMEDIATE ACTIONS:\n1. Alert all security via radio\n2. Lock down affected zone\n3. Call 100 (Police) - do NOT confront threat\n\nSTAFF DUTIES:\n- Security: Secure all entry/exit points\n- Front Desk: Call 100, stay calm\n- Manager: Initiate lockdown protocol\n\nGUEST COMMUNICATION:\nDear Guests, please remain in your current location until further notice.\n\nESCALATION:\nCall 100 immediately if threat confirmed.", "guest": "Dear Guests, as a precaution please remain where you are. Our security team is ensuring your safety.", "color": "457B9D", "icon": "🔒"},
    "Flood":    {"protocol": "IMMEDIATE ACTIONS:\n1. Shut off main water supply immediately\n2. Evacuate ground floor guests to upper floors\n3. Alert maintenance and emergency services\n\nSTAFF DUTIES:\n- Maintenance: Locate and shut water source\n- Housekeeping: Move guests, protect valuables\n- Front Desk: Document affected rooms\n\nGUEST COMMUNICATION:\nDear Guests, ground floor guests please follow staff to upper floors.\n\nESCALATION:\nCall emergency services if water rises rapidly.", "guest": "Dear Guests, we are managing a water situation. Ground floor guests please follow staff to upper floors for safety.", "color": "2A9D8F", "icon": "🌊"},
}

def call_gemini(prompt):
    try:
        payload = {"contents": [{"parts": [{"text": prompt}]}]}
        res = requests.post(GEMINI_URL, json=payload, timeout=15)
        if res.status_code == 200:
            return res.json()["candidates"][0]["content"]["parts"][0]["text"]
        return None
    except:
        return None

def fb_get(path):
    try:
        res = requests.get(f"{FIREBASE_URL}/{path}.json", timeout=5)
        return res.json()
    except:
        return None

def fb_post(path, data):
    try:
        res = requests.post(f"{FIREBASE_URL}/{path}.json", json=data, timeout=5)
        return res.json()
    except:
        return {"name": "local_" + str(datetime.datetime.now().timestamp())}

def fb_patch(path, data):
    try:
        res = requests.patch(f"{FIREBASE_URL}/{path}.json", json=data, timeout=5)
        return res.json()
    except:
        return {}

def fb_put(path, data):
    try:
        res = requests.put(f"{FIREBASE_URL}/{path}.json", json=data, timeout=5)
        return res.json()
    except:
        return {}

# ─── PAGES ───────────────────────────────────────────────────────────────────
@app.route("/")
def login(): return render_template("login.html")

@app.route("/dashboard")
def dashboard():
    role = request.args.get("role", "Manager")
    username = request.args.get("username", "User")
    hotel = request.args.get("hotel", "Grand Palace Hotel")
    return render_template("dashboard.html", role=role, username=username, hotel=hotel)

@app.route("/staff")
def staff_view():
    username = request.args.get("username", "Staff")
    hotel = request.args.get("hotel", "Grand Palace Hotel")
    return render_template("staff.html", username=username, hotel=hotel)

@app.route("/analytics")
def analytics():
    hotel = request.args.get("hotel", "Grand Palace Hotel")
    return render_template("analytics.html", hotel=hotel)

@app.route("/history")
def history():
    hotel = request.args.get("hotel", "Grand Palace Hotel")
    return render_template("history.html", hotel=hotel)

@app.route("/map")
def hotel_map():
    hotel = request.args.get("hotel", "Grand Palace Hotel")
    return render_template("map.html", hotel=hotel)

# ─── API ─────────────────────────────────────────────────────────────────────
@app.route("/api/login", methods=["POST"])
def api_login():
    data = request.json
    username = data.get("username", "").lower()
    password = data.get("password", "")
    user = USERS.get(username)
    if user and user["password"] == password:
        return jsonify({"success": True, "role": user["role"], "username": username, "hotel": user["hotel"]})
    return jsonify({"success": False, "message": "Invalid credentials"}), 401

@app.route("/api/hotels", methods=["GET"])
def get_hotels():
    return jsonify({"hotels": list(HOTELS.keys()), "details": HOTELS})

@app.route("/api/trigger-alert", methods=["POST"])
def trigger_alert():
    data = request.json
    crisis_type = data.get("crisis_type", "Unknown")
    location = data.get("location", "Main Lobby")
    floor = data.get("floor", "Ground Floor")
    triggered_by = data.get("triggered_by", "Manager")
    hotel = data.get("hotel", "Grand Palace Hotel")

    prompt = f"""You are an emergency response AI for a 5-star hotel called {hotel}.
A {crisis_type} emergency at {location} on {floor}.
Generate a structured protocol with:
1. IMMEDIATE ACTIONS (3 steps)
2. STAFF DUTIES (3 tasks)
3. GUEST COMMUNICATION (1 message starting with Dear Guests,)
4. ESCALATION (when to call external services)
Use plain text, no markdown."""

    ai_protocol = call_gemini(prompt)
    ai_source = "Google Gemini AI"
    if not ai_protocol:
        ai_protocol = PROTOCOLS.get(crisis_type, PROTOCOLS["Fire"])["protocol"]
        ai_source = "Built-in Protocol"

    now = datetime.datetime.now()
    alert = {
        "type": crisis_type,
        "location": location,
        "floor": floor,
        "hotel": hotel,
        "triggered_by": triggered_by,
        "time": now.strftime("%H:%M:%S"),
        "date": now.strftime("%d/%m/%Y"),
        "timestamp": now.isoformat(),
        "status": "Active",
        "protocol": ai_protocol,
        "ai_source": ai_source,
        "resolved_by": None,
        "resolved_time": None,
        "response_time_seconds": None,
    }

    result = fb_post(f"hotels/{hotel.replace(' ','_')}/alerts", alert)
    alert["id"] = result.get("name", "unknown")

    # SMS notification log
    sms = {
        "to": "All Staff",
        "message": f"🚨 ALERT: {crisis_type} at {location}, {hotel}. Respond immediately!",
        "time": now.strftime("%H:%M:%S"),
        "hotel": hotel,
        "status": "Sent"
    }
    fb_post(f"hotels/{hotel.replace(' ','_')}/notifications", sms)

    return jsonify({"success": True, "alert": alert})

@app.route("/api/alerts", methods=["GET"])
def get_alerts():
    hotel = request.args.get("hotel", "Grand Palace Hotel")
    data = fb_get(f"hotels/{hotel.replace(' ','_')}/alerts")
    alerts = []
    if data:
        for key, value in data.items():
            value["id"] = key
            # Calculate live response time for active alerts
            if value.get("status") == "Active" and value.get("timestamp"):
                try:
                    start = datetime.datetime.fromisoformat(value["timestamp"])
                    value["live_seconds"] = int((datetime.datetime.now() - start).total_seconds())
                except:
                    value["live_seconds"] = 0
            alerts.append(value)
    alerts.reverse()
    return jsonify({"alerts": alerts})

@app.route("/api/resolve-alert", methods=["POST"])
def resolve_alert():
    data = request.json
    alert_id = data.get("id")
    resolved_by = data.get("resolved_by", "Staff")
    hotel = data.get("hotel", "Grand Palace Hotel")
    hotel_key = hotel.replace(' ', '_')

    alert_data = fb_get(f"hotels/{hotel_key}/alerts/{alert_id}")
    response_time = None
    if alert_data and "timestamp" in alert_data:
        try:
            start = datetime.datetime.fromisoformat(alert_data["timestamp"])
            response_time = int((datetime.datetime.now() - start).total_seconds())
        except:
            response_time = None

    now = datetime.datetime.now()
    fb_patch(f"hotels/{hotel_key}/alerts/{alert_id}", {
        "status": "Resolved",
        "resolved_by": resolved_by,
        "resolved_time": now.strftime("%H:%M:%S"),
        "response_time_seconds": response_time,
    })

    # Generate post-crisis report
    if alert_data:
        report_prompt = f"""Generate a brief post-crisis incident report for a hotel emergency:
Type: {alert_data.get('type')} | Location: {alert_data.get('location')} | Hotel: {hotel}
Triggered by: {alert_data.get('triggered_by')} | Resolved by: {resolved_by}
Response time: {response_time} seconds
Write 3 sentences: what happened, what was done, and recommendation. Professional tone."""
        
        report_summary = call_gemini(report_prompt)
        if not report_summary:
            report_summary = f"A {alert_data.get('type')} emergency was reported at {alert_data.get('location')}. The situation was handled by {resolved_by} within {response_time} seconds following standard protocol. Regular safety drills and equipment checks are recommended to maintain preparedness."

        report = {
            "type": alert_data.get("type"),
            "location": alert_data.get("location"),
            "floor": alert_data.get("floor"),
            "hotel": hotel,
            "triggered_by": alert_data.get("triggered_by"),
            "resolved_by": resolved_by,
            "date": alert_data.get("date"),
            "triggered_time": alert_data.get("time"),
            "resolved_time": now.strftime("%H:%M:%S"),
            "response_time_seconds": response_time,
            "summary": report_summary,
            "protocol_used": alert_data.get("protocol"),
            "ai_source": alert_data.get("ai_source"),
        }
        fb_post(f"hotels/{hotel_key}/reports", report)

    return jsonify({"success": True, "response_time": response_time})

@app.route("/api/guest-message", methods=["POST"])
def guest_message():
    data = request.json
    crisis_type = data.get("crisis_type", "Fire")
    location = data.get("location", "hotel")
    hotel = data.get("hotel", "Grand Palace Hotel")
    prompt = f"Write a calm 2-sentence announcement for hotel guests at {hotel} about a {crisis_type} at {location}. Start with 'Dear Guests,' Be professional and reassuring."
    message = call_gemini(prompt)
    if not message:
        message = PROTOCOLS.get(crisis_type, PROTOCOLS["Fire"])["guest"]
    return jsonify({"message": message})

@app.route("/api/analytics", methods=["GET"])
def get_analytics():
    hotel = request.args.get("hotel", "Grand Palace Hotel")
    hotel_key = hotel.replace(' ', '_')
    alerts = fb_get(f"hotels/{hotel_key}/alerts") or {}
    reports = fb_get(f"hotels/{hotel_key}/reports") or {}

    total = len(alerts)
    active = sum(1 for a in alerts.values() if a.get("status") == "Active")
    resolved = sum(1 for a in alerts.values() if a.get("status") == "Resolved")

    response_times = [a.get("response_time_seconds", 0) for a in reports.values() if a.get("response_time_seconds")]
    avg_response = int(sum(response_times) / len(response_times)) if response_times else 0

    by_type = {"Fire": 0, "Medical": 0, "Security": 0, "Flood": 0}
    by_location = {}
    for a in alerts.values():
        t = a.get("type")
        if t in by_type: by_type[t] += 1
        loc = a.get("location", "Unknown")
        by_location[loc] = by_location.get(loc, 0) + 1

    # By day (last 7 days)
    by_day = {}
    for a in alerts.values():
        d = a.get("date", "Unknown")
        by_day[d] = by_day.get(d, 0) + 1

    return jsonify({
        "total": total, "active": active, "resolved": resolved,
        "avg_response_seconds": avg_response,
        "by_type": by_type, "by_location": by_location,
        "by_day": by_day,
        "recent_reports": list(reports.values())[-5:] if reports else [],
    })

@app.route("/api/history", methods=["GET"])
def get_history():
    hotel = request.args.get("hotel", "Grand Palace Hotel")
    hotel_key = hotel.replace(' ', '_')
    reports = fb_get(f"hotels/{hotel_key}/reports") or {}
    history = []
    for key, value in reports.items():
        value["id"] = key
        history.append(value)
    history.reverse()
    return jsonify({"history": history})

@app.route("/api/map", methods=["GET"])
def get_map():
    hotel = request.args.get("hotel", "Grand Palace Hotel")
    hotel_key = hotel.replace(' ', '_')
    alerts = fb_get(f"hotels/{hotel_key}/alerts") or {}
    active_alerts = {v.get("location"): v for v in alerts.values() if v.get("status") == "Active"}
    return jsonify({"active_locations": active_alerts, "hotel_info": HOTELS.get(hotel, {})})

@app.route("/api/notifications", methods=["GET"])
def get_notifications():
    hotel = request.args.get("hotel", "Grand Palace Hotel")
    hotel_key = hotel.replace(' ', '_')
    notifs = fb_get(f"hotels/{hotel_key}/notifications") or {}
    result = list(notifs.values())[-10:] if notifs else []
    result.reverse()
    return jsonify({"notifications": result})

if __name__ == "__main__":
    app.run(debug=True, port=5000)
