"""
NightFlow Backend API
Flask REST API for the NightFlow Nightlife Platform
"""

from flask import Flask, jsonify, request, make_response
from datetime import datetime, date
import json
import uuid
import copy
import hashlib
import secrets
import os
from functools import wraps

app = Flask(__name__)

# ── CORS helper ───────────────────────────────────────────────
def cors(response):
    response.headers["Access-Control-Allow-Origin"] = "*"
    response.headers["Access-Control-Allow-Methods"] = "GET,POST,PUT,DELETE,PATCH,OPTIONS"
    response.headers["Access-Control-Allow-Headers"] = "Content-Type,Authorization"
    return response

@app.after_request
def add_cors(resp):
    return cors(resp)

@app.before_request
def handle_options():
    if request.method == "OPTIONS":
        return cors(make_response("", 204))


# ════════════════════════════════════════════════════════════
#  AUTHENTICATION / USERS
#  Demo storage: in-memory. For production use a real DB.
# ════════════════════════════════════════════════════════════

def hash_password(password: str) -> str:
    return hashlib.sha256(password.encode("utf-8")).hexdigest()

USERS = [
    {
        "id": "u_club_1",
        "name": "Μανώλης Owner",
        "email": "club@nightflow.gr",
        "password_hash": hash_password("club123"),
        "role": "club",
        "venue_id": "v1",
        "venue_name": "Fortezza Club",
    },
    {
        "id": "u_customer_1",
        "name": "Νίκος Πελάτης",
        "email": "customer@nightflow.gr",
        "password_hash": hash_password("customer123"),
        "role": "customer",
        "customer_id": "c3",
        "points": 980,
        "tier": "silver",
    },
]

SESSIONS = {}
USERS_FILE = os.path.join(os.path.dirname(__file__), "users.json")

def load_users_from_disk():
    global USERS
    if os.path.exists(USERS_FILE):
        try:
            with open(USERS_FILE, "r", encoding="utf-8") as f:
                USERS = json.load(f)
        except Exception:
            pass

def save_users_to_disk():
    try:
        with open(USERS_FILE, "w", encoding="utf-8") as f:
            json.dump(USERS, f, ensure_ascii=False, indent=2)
    except Exception:
        pass

load_users_from_disk()

def public_user(user):
    data = {k: v for k, v in user.items() if k != "password_hash"}
    return data

def current_user():
    auth = request.headers.get("Authorization", "")
    token = auth.replace("Bearer ", "").strip() if auth.startswith("Bearer ") else ""
    uid = SESSIONS.get(token)
    if not uid:
        return None
    return next((u for u in USERS if u["id"] == uid), None)

def require_auth(role=None):
    def decorator(fn):
        @wraps(fn)
        def wrapper(*args, **kwargs):
            user = current_user()
            if not user:
                return jsonify({"error": "Authentication required"}), 401
            if role and user.get("role") != role:
                return jsonify({"error": "Forbidden for this account type"}), 403
            request.user = user
            return fn(*args, **kwargs)
        return wrapper
    return decorator

# ════════════════════════════════════════════════════════════
#  IN-MEMORY DATABASE
# ════════════════════════════════════════════════════════════

VENUES = [
    {"id":"v1","name":"Fortezza Club","type":"Club","address":"Παλιά Πόλη Ρεθύμνου","capacity":210,"current_guests":156,"image_class":"img-club1","image_emoji":"🏰","rating":4.7,"verified":True,"english_staff":True,"open":True},
    {"id":"v2","name":"Harbor Nights","type":"Bar Club","address":"Ενετικό Λιμάνι","capacity":180,"current_guests":128,"image_class":"img-club2","image_emoji":"⚓","rating":4.6,"verified":True,"english_staff":True,"open":True},
    {"id":"v3","name":"Campus Beat","type":"Student Night","address":"Κέντρο Ρεθύμνου","capacity":160,"current_guests":132,"image_class":"img-club3","image_emoji":"🎓","rating":4.5,"verified":True,"english_staff":False,"open":True},
    {"id":"v4","name":"Old Town Lounge","type":"Cocktail Bar","address":"Πλατεία Ριμόντι","capacity":90,"current_guests":54,"image_class":"img-club4","image_emoji":"🍸","rating":4.8,"verified":True,"english_staff":True,"open":True},
    {"id":"v5","name":"Beach Strip Club","type":"Beach Bar","address":"Παραλιακή Ρεθύμνου","capacity":230,"current_guests":171,"image_class":"img-club6","image_emoji":"🌊","rating":4.6,"verified":True,"english_staff":True,"open":True},
]

EVENTS = [
    {"id":"e1","venue_id":"v1","title":"Greek x Commercial Night","genre":"Greek / Commercial","genre_icon":"🎧","dj":"DJ Manos","date":"2026-06-20","start_time":"23:00","entry_price":10,"min_spend_vip":120,"popularity":82,"badges":["trending","live"],"trending":True,"student_night":False,"tourist_friendly":True,"vip_available":True,"guest_list_open":True,"description":"Το βασικό βράδυ του Fortezza Club. Λίγα τραπέζια, δυνατή λίστα, γρήγορη κράτηση."},
    {"id":"e2","venue_id":"v2","title":"Harbor Latin & Hits","genre":"Latin / Hits","genre_icon":"💃","dj":"DJ Leo","date":"2026-06-20","start_time":"22:30","entry_price":8,"min_spend_vip":90,"popularity":71,"badges":["tourist","live"],"trending":True,"student_night":False,"tourist_friendly":True,"vip_available":True,"guest_list_open":True,"description":"Tourist friendly βραδιά στο λιμάνι με easy booking και verified τιμές."},
    {"id":"e3","venue_id":"v3","title":"Student Thursday List","genre":"Trap / R&B","genre_icon":"🎵","dj":"DJ Nick R","date":"2026-06-20","start_time":"23:30","entry_price":0,"min_spend_vip":0,"popularity":88,"badges":["trending"],"trending":True,"student_night":True,"tourist_friendly":False,"vip_available":False,"guest_list_open":True,"description":"Φοιτητική λίστα, offers και group check-in για παρέες."},
    {"id":"e4","venue_id":"v4","title":"Cocktail After Dark","genre":"Deep / Lounge","genre_icon":"🍸","dj":"Resident Selector","date":"2026-06-20","start_time":"21:00","entry_price":0,"min_spend_vip":60,"popularity":60,"badges":["vip"],"trending":False,"student_night":False,"tourist_friendly":True,"vip_available":True,"guest_list_open":True,"description":"Πιο ήσυχη επιλογή για groups, tourists και γενέθλια."},
    {"id":"e5","venue_id":"v5","title":"Beach Strip Party","genre":"Afro / House","genre_icon":"🌊","dj":"Maria K","date":"2026-06-20","start_time":"20:30","entry_price":12,"min_spend_vip":100,"popularity":74,"badges":["tourist","new"],"trending":True,"student_night":False,"tourist_friendly":True,"vip_available":True,"guest_list_open":True,"description":"Παραλιακό event με tourist mode, χάρτη και γρήγορη επικοινωνία με το μαγαζί."},
]

CUSTOMERS = [
    {
        "id": "c1",
        "name": "Kostas Papadakis",
        "initials": "KP",
        "email": "k.papadakis@gmail.com",
        "phone": "+30 694 123 4567",
        "birthday": "1990-03-15",
        "tier": "black",
        "points": 5800,
        "total_visits": 48,
        "avg_spend_month": 4200,
        "fav_genre": "Progressive House",
        "customer_since": "2022-03-01",
        "last_visit": "2025-06-18",
        "notes": "Always books VIP. Prefers table 1 near stage.",
    },
    {
        "id": "c2",
        "name": "Elena Dimitriou",
        "initials": "ED",
        "email": "elena.d@hotmail.com",
        "phone": "+30 697 234 5678",
        "birthday": "1995-07-22",
        "tier": "black",
        "points": 4650,
        "total_visits": 34,
        "avg_spend_month": 3100,
        "fav_genre": "Deep House",
        "customer_since": "2023-01-10",
        "last_visit": "2025-06-15",
        "notes": "VIP group bookings. Celebrates birthdays here.",
    },
    {
        "id": "c3",
        "name": "Nikos Kritis",
        "initials": "NK",
        "email": "nikos.kritis@gmail.com",
        "phone": "+30 698 345 6789",
        "birthday": "1998-11-08",
        "tier": "gold",
        "points": 2980,
        "total_visits": 22,
        "avg_spend_month": 1850,
        "fav_genre": "R&B / Hip-Hop",
        "customer_since": "2023-06-20",
        "last_visit": "2025-06-10",
        "notes": "Student. Groups of 5-8.",
    },
    {
        "id": "c4",
        "name": "Sofia Manousakis",
        "initials": "SM",
        "email": "sofia.m@yahoo.gr",
        "phone": "+30 693 456 7890",
        "birthday": "1992-12-03",
        "tier": "gold",
        "points": 3420,
        "total_visits": 29,
        "avg_spend_month": 2200,
        "fav_genre": "Techno",
        "customer_since": "2022-09-15",
        "last_visit": "2025-06-12",
        "notes": "Prefers techno nights. Regular Fri/Sat.",
    },
    {
        "id": "c5",
        "name": "Dimitris Petrakis",
        "initials": "DP",
        "email": "dpetrakis@gmail.com",
        "phone": "+30 699 567 8901",
        "birthday": "1997-02-14",
        "tier": "gold",
        "points": 2100,
        "total_visits": 18,
        "avg_spend_month": 1400,
        "fav_genre": "Afro House",
        "customer_since": "2024-02-01",
        "last_visit": "2025-06-05",
        "notes": "Brings tourist friends often.",
    },
    {
        "id": "c6",
        "name": "Anna Papageorgiou",
        "initials": "AP",
        "email": "anna.papa@gmail.com",
        "phone": "+30 696 678 9012",
        "birthday": "2000-08-30",
        "tier": "silver",
        "points": 980,
        "total_visits": 9,
        "avg_spend_month": 680,
        "fav_genre": "Pop / Dance",
        "customer_since": "2024-04-10",
        "last_visit": "2025-05-28",
        "notes": "Student, weekend only.",
    },
]

RESERVATIONS = [
    {
        "id": "r1",
        "customer_id": "c1",
        "customer_name": "Kostas Papadakis",
        "customer_initials": "KP",
        "venue_id": "v1",
        "event_id": "e1",
        "table": "V1",
        "table_type": "vip",
        "guests": 8,
        "arrival_time": "22:00",
        "min_spend": 800,
        "status": "confirmed",
        "created_at": "2025-06-18T14:00:00",
        "notes": "Bottle service + reserved parking",
        "deposit_paid": True,
        "checked_in": False,
    },
    {
        "id": "r2",
        "customer_id": "c2",
        "customer_name": "Maria Konstantinou",
        "customer_initials": "MK",
        "venue_id": "v1",
        "event_id": "e1",
        "table": "V2",
        "table_type": "vip",
        "guests": 6,
        "arrival_time": "23:00",
        "min_spend": 500,
        "status": "confirmed",
        "created_at": "2025-06-19T10:00:00",
        "notes": "Birthday celebration",
        "deposit_paid": True,
        "checked_in": False,
    },
    {
        "id": "r3",
        "customer_id": "c3",
        "customer_name": "Nikos Vardalakis",
        "customer_initials": "NV",
        "venue_id": "v1",
        "event_id": "e1",
        "table": "T1",
        "table_type": "standard",
        "guests": 5,
        "arrival_time": "23:00",
        "min_spend": 0,
        "status": "confirmed",
        "created_at": "2025-06-19T16:00:00",
        "notes": "",
        "deposit_paid": False,
        "checked_in": False,
    },
    {
        "id": "r4",
        "customer_id": "c4",
        "customer_name": "Alex Manoussakis",
        "customer_initials": "AM",
        "venue_id": "v1",
        "event_id": "e1",
        "table": "T2",
        "table_type": "standard",
        "guests": 4,
        "arrival_time": "22:30",
        "min_spend": 0,
        "status": "confirmed",
        "created_at": "2025-06-19T18:00:00",
        "notes": "",
        "deposit_paid": False,
        "checked_in": True,
    },
    {
        "id": "r5",
        "customer_id": None,
        "customer_name": "James Patterson",
        "customer_initials": "JP",
        "venue_id": "v1",
        "event_id": "e1",
        "table": "T3",
        "table_type": "standard",
        "guests": 3,
        "arrival_time": "23:30",
        "min_spend": 0,
        "status": "pending",
        "created_at": "2025-06-20T09:00:00",
        "notes": "Tourist, English only",
        "deposit_paid": False,
        "checked_in": False,
    },
    {
        "id": "r6",
        "customer_id": "c5",
        "customer_name": "Sofia Psaroudaki",
        "customer_initials": "SP",
        "venue_id": "v1",
        "event_id": "e1",
        "table": "T5",
        "table_type": "standard",
        "guests": 6,
        "arrival_time": "00:00",
        "min_spend": 0,
        "status": "confirmed",
        "created_at": "2025-06-18T20:00:00",
        "notes": "Birthday celebration — surprise setup needed",
        "deposit_paid": True,
        "checked_in": False,
    },
]

PROMOTERS = [
    {"id": "p1", "name": "Giorgos Maniatis", "initials": "GM", "guests_brought": 94, "revenue_generated": 3760, "commission": 376, "status": "active"},
    {"id": "p2", "name": "Dimitra Chrysou",  "initials": "DC", "guests_brought": 78, "revenue_generated": 2970, "commission": 297, "status": "active"},
    {"id": "p3", "name": "Stavros Kaloudis", "initials": "SK", "guests_brought": 62, "revenue_generated": 2480, "commission": 248, "status": "active"},
    {"id": "p4", "name": "Ioanna Paterakis", "initials": "IP", "guests_brought": 45, "revenue_generated": 1800, "commission": 180, "status": "top"},
    {"id": "p5", "name": "Manolis Sfakianakis","initials":"MS","guests_brought": 38, "revenue_generated": 1520, "commission": 152, "status": "pending"},
]

ANALYTICS = {
    "monthly_revenue": [42, 38, 56, 84, 148, 284],
    "months": ["Ιαν", "Φεβ", "Μαρ", "Απρ", "Μαι", "Ιουν"],
    "weekly_revenue": [22, 8, 4, 6, 9, 14, 18.4],
    "weekly_occupancy": [88, 42, 22, 28, 45, 68, 94],
    "days": ["Σαβ", "Κυρ", "Δευ", "Τρι", "Τετ", "Πεμ", "Παρ"],
    "arrivals_by_hour": [12, 48, 142, 198, 156, 88, 44, 22, 8],
    "hours": ["21h", "22h", "23h", "00h", "01h", "02h", "03h", "04h", "05h"],
    "genre_split": [34, 26, 18, 12, 7, 3],
    "genres": ["Prog. House", "Deep House", "R&B", "Techno", "Afro House", "Other"],
    "spend_by_tier": [42, 68, 145, 290],
    "tiers": ["Walk-in", "Silver", "Gold", "Black"],
    "retention": {
        "weeks": ["Εβδ 1", "Εβδ 2", "Εβδ 3", "Εβδ 4"],
        "new": [142, 168, 124, 198],
        "returning": [284, 312, 268, 356],
    },
    "best_nights": [3.2, 4.1, 5.8, 9.4, 18.4, 24.2, 7.6],
}

ACTIVITY_FEED = [
    {"id": "f1", "user": "Maria K.", "initials": "M", "action": "μπήκε στη λίστα του Fortezza", "time": "2 min ago", "icon": "🎉", "event_id": "e1"},
    {"id": "f2", "user": "Nikos P.", "initials": "N", "action": "έκανε check-in στο Harbor Nights", "time": "8 min ago", "icon": "🌊", "event_id": "e2"},
    {"id": "f3", "user": "Elena D.", "initials": "E", "action": "earned Black tier status 💎", "time": "15 min ago", "icon": "⭐", "event_id": None},
    {"id": "f4", "user": "Alex M. + 12 others", "initials": "A", "action": "πάνε στο Campus Beat Student List", "time": "23 min ago", "icon": "🎵", "event_id": "e3"},
    {"id": "f5", "user": "Kostas V.", "initials": "K", "action": "κλείδωσε offer στο Beach Strip Club", "time": "31 min ago", "icon": "🍾", "event_id": "e6"},
]

TONIGHT_STATS = {
    "total_guests_tonight": 641,
    "open_venues": 5,
    "trending_events": 5,
    "avg_satisfaction": 92,
}

# ════════════════════════════════════════════════════════════
#  ROUTES
# ════════════════════════════════════════════════════════════

@app.route("/")
def index():
    return jsonify({"service": "NightFlow API", "version": "1.0.0", "status": "running"})


# ── Auth ─────────────────────────────────────────────────────

@app.route("/api/auth/login", methods=["POST"])
def login():
    data = request.get_json() or {}
    email = (data.get("email") or "").strip().lower()
    password = data.get("password") or ""
    user = next((u for u in USERS if u["email"].lower() == email), None)
    if not user or user["password_hash"] != hash_password(password):
        return jsonify({"error": "Λάθος email ή κωδικός"}), 401
    token = secrets.token_urlsafe(32)
    SESSIONS[token] = user["id"]
    return jsonify({"token": token, "user": public_user(user)})

@app.route("/api/auth/register", methods=["POST"])
def register():
    data = request.get_json() or {}
    name = (data.get("name") or "").strip()
    email = (data.get("email") or "").strip().lower()
    password = data.get("password") or ""
    role = data.get("role") or "customer"
    if role not in ["customer", "club"]:
        return jsonify({"error": "Invalid role"}), 400
    if not name or not email or len(password) < 4:
        return jsonify({"error": "Συμπλήρωσε όνομα, email και κωδικό τουλάχιστον 4 χαρακτήρων"}), 400
    if any(u["email"].lower() == email for u in USERS):
        return jsonify({"error": "Υπάρχει ήδη account με αυτό το email"}), 409

    user = {
        "id": "u_" + str(uuid.uuid4())[:8],
        "name": name,
        "email": email,
        "password_hash": hash_password(password),
        "role": role,
    }
    if role == "club":
        user.update({"venue_id": "v1", "venue_name": data.get("venue_name") or "Το μαγαζί μου"})
    else:
        customer = {
            "id": "c" + str(uuid.uuid4())[:8],
            "name": name,
            "initials": "".join([part[0] for part in name.split()[:2]]).upper() or "NF",
            "email": email,
            "phone": data.get("phone", ""),
            "birthday": "",
            "tier": "silver",
            "points": 0,
            "total_visits": 0,
            "avg_spend_month": 0,
            "fav_genre": "",
            "customer_since": str(date.today()),
            "last_visit": "",
            "notes": "Created from signup",
        }
        CUSTOMERS.append(customer)
        user.update({"customer_id": customer["id"], "points": 0, "tier": "silver"})
    USERS.append(user)
    save_users_to_disk()
    token = secrets.token_urlsafe(32)
    SESSIONS[token] = user["id"]
    return jsonify({"token": token, "user": public_user(user)}), 201

@app.route("/api/auth/me")
def me():
    user = current_user()
    if not user:
        return jsonify({"user": None})
    return jsonify({"user": public_user(user)})

@app.route("/api/auth/logout", methods=["POST"])
def logout():
    auth = request.headers.get("Authorization", "")
    token = auth.replace("Bearer ", "").strip() if auth.startswith("Bearer ") else ""
    SESSIONS.pop(token, None)
    return jsonify({"success": True})

# ── Public ────────────────────────────────────────────────────

@app.route("/api/tonight-stats")
def tonight_stats():
    return jsonify(TONIGHT_STATS)

@app.route("/api/events")
def get_events():
    trending = request.args.get("trending")
    student  = request.args.get("student")
    tourist  = request.args.get("tourist")

    result = copy.deepcopy(EVENTS)

    if trending == "true":
        result = [e for e in result if e.get("trending")]
    if student == "true":
        result = [e for e in result if e.get("student_night")]
    if tourist == "true":
        result = [e for e in result if e.get("tourist_friendly")]

    # attach venue name
    venue_map = {v["id"]: v for v in VENUES}
    for ev in result:
        v = venue_map.get(ev["venue_id"], {})
        ev["venue_name"] = v.get("name", "")
        ev["venue_capacity"] = v.get("capacity", 0)
        ev["venue_current"] = v.get("current_guests", 0)
        ev["image_class"]   = v.get("image_class", "")
        ev["image_emoji"]   = v.get("image_emoji", "")

    return jsonify(result)

@app.route("/api/events/<event_id>")
def get_event(event_id):
    ev = next((e for e in EVENTS if e["id"] == event_id), None)
    if not ev:
        return jsonify({"error": "Not found"}), 404
    ev = copy.deepcopy(ev)
    v  = next((x for x in VENUES if x["id"] == ev["venue_id"]), {})
    ev["venue_name"]     = v.get("name", "")
    ev["venue_capacity"] = v.get("capacity", 0)
    ev["venue_current"]  = v.get("current_guests", 0)
    ev["image_class"]    = v.get("image_class", "")
    ev["image_emoji"]    = v.get("image_emoji", "")
    return jsonify(ev)

@app.route("/api/venues")
def get_venues():
    return jsonify(VENUES)

@app.route("/api/venues/<venue_id>")
def get_venue(venue_id):
    v = next((x for x in VENUES if x["id"] == venue_id), None)
    if not v:
        return jsonify({"error": "Not found"}), 404
    return jsonify(v)

@app.route("/api/activity-feed")
def activity_feed():
    return jsonify(ACTIVITY_FEED)

# ── Reservations ──────────────────────────────────────────────

@app.route("/api/reservations")
@require_auth("club")
def get_reservations():
    venue_id = request.args.get("venue_id")
    status   = request.args.get("status")
    result   = copy.deepcopy(RESERVATIONS)
    if venue_id:
        result = [r for r in result if r["venue_id"] == venue_id]
    if status:
        result = [r for r in result if r["status"] == status]
    return jsonify(result)

@app.route("/api/reservations", methods=["POST"])
@require_auth()
def create_reservation():
    data = request.get_json()
    new_res = {
        "id": "r" + str(uuid.uuid4())[:8],
        "customer_id": data.get("customer_id"),
        "customer_name": data.get("customer_name", "Guest"),
        "customer_initials": data.get("customer_name", "G")[:2].upper(),
        "venue_id": data.get("venue_id", "v1"),
        "event_id": data.get("event_id", "e1"),
        "table": data.get("table", "T-NEW"),
        "table_type": data.get("table_type", "standard"),
        "guests": data.get("guests", 2),
        "arrival_time": data.get("arrival_time", "23:00"),
        "min_spend": data.get("min_spend", 0),
        "status": "pending",
        "created_at": datetime.now().isoformat(),
        "notes": data.get("notes", ""),
        "deposit_paid": False,
        "checked_in": False,
    }
    RESERVATIONS.append(new_res)
    return jsonify(new_res), 201

@app.route("/api/reservations/<res_id>", methods=["PATCH"])
@require_auth("club")
def update_reservation(res_id):
    res = next((r for r in RESERVATIONS if r["id"] == res_id), None)
    if not res:
        return jsonify({"error": "Not found"}), 404
    data = request.get_json()
    for k, v in data.items():
        res[k] = v
    return jsonify(res)

@app.route("/api/reservations/<res_id>/checkin", methods=["POST"])
@require_auth("club")
def checkin_reservation(res_id):
    res = next((r for r in RESERVATIONS if r["id"] == res_id), None)
    if not res:
        return jsonify({"error": "Not found"}), 404
    res["checked_in"] = True
    res["status"] = "confirmed"
    res["checkin_time"] = datetime.now().strftime("%H:%M")
    return jsonify(res)

# ── Customers ─────────────────────────────────────────────────

@app.route("/api/customers")
@require_auth("club")
def get_customers():
    tier = request.args.get("tier")
    result = copy.deepcopy(CUSTOMERS)
    if tier:
        result = [c for c in result if c["tier"] == tier]
    return jsonify(result)

@app.route("/api/customers/<cid>")
@require_auth("club")
def get_customer(cid):
    c = next((x for x in CUSTOMERS if x["id"] == cid), None)
    if not c:
        return jsonify({"error": "Not found"}), 404
    return jsonify(c)

@app.route("/api/customers", methods=["POST"])
@require_auth("club")
def create_customer():
    data = request.get_json()
    new_c = {
        "id": "c" + str(uuid.uuid4())[:8],
        "name": data.get("name", "New Customer"),
        "initials": data.get("name", "NC")[:2].upper(),
        "email": data.get("email", ""),
        "phone": data.get("phone", ""),
        "birthday": data.get("birthday", ""),
        "tier": "silver",
        "points": 0,
        "total_visits": 0,
        "avg_spend_month": 0,
        "fav_genre": data.get("fav_genre", ""),
        "customer_since": date.today().isoformat(),
        "last_visit": date.today().isoformat(),
        "notes": data.get("notes", ""),
    }
    CUSTOMERS.append(new_c)
    return jsonify(new_c), 201

# ── Promoters ─────────────────────────────────────────────────

@app.route("/api/promoters")
@require_auth("club")
def get_promoters():
    return jsonify(PROMOTERS)

@app.route("/api/promoters", methods=["POST"])
@require_auth("club")
def create_promoter():
    data = request.get_json()
    new_p = {
        "id": "p" + str(uuid.uuid4())[:8],
        "name": data.get("name", "New Promoter"),
        "initials": data.get("name", "NP")[:2].upper(),
        "guests_brought": 0,
        "revenue_generated": 0,
        "commission": 0,
        "status": "active",
    }
    PROMOTERS.append(new_p)
    return jsonify(new_p), 201

# ── Analytics ─────────────────────────────────────────────────

@app.route("/api/analytics")
@require_auth("club")
def get_analytics():
    return jsonify(ANALYTICS)

@app.route("/api/analytics/overview")
@require_auth("club")
def get_overview():
    checked_in = len([r for r in RESERVATIONS if r.get("checked_in")])
    confirmed  = len([r for r in RESERVATIONS if r["status"] == "confirmed"])
    pending    = len([r for r in RESERVATIONS if r["status"] == "pending"])
    venue = next((v for v in VENUES if v["id"] == "v1"), {})
    cap  = venue.get("capacity", 210)
    curr = venue.get("current_guests", 0)
    occ  = round(curr / cap * 100) if cap else 0
    return jsonify({
        "reservations_tonight": len(RESERVATIONS),
        "confirmed": confirmed,
        "pending": pending,
        "checked_in": checked_in,
        "occupancy_pct": occ,
        "current_guests": curr,
        "capacity": cap,
        "revenue_estimate": 2850,
        "vip_guests": 22,
        "repeat_customers_pct": 74,
        "guest_list_count": 118,
        "peak_hour": "00:00",
    })

# ── Marketing ─────────────────────────────────────────────────

@app.route("/api/marketing/send", methods=["POST"])
@require_auth("club")
def send_campaign():
    data = request.get_json()
    campaign_type = data.get("type", "general")
    return jsonify({
        "success": True,
        "campaign_type": campaign_type,
        "sent_to": data.get("count", 0),
        "message": f"Campaign '{campaign_type}' queued successfully",
        "estimated_open_rate": "68%",
    })

# ── Guest List ────────────────────────────────────────────────

@app.route("/api/guestlist/join", methods=["POST"])
@require_auth()
def join_guest_list():
    data = request.get_json()
    return jsonify({
        "success": True,
        "reference": "NF-" + str(uuid.uuid4())[:6].upper(),
        "message": f"You're on the list for {data.get('event_title', 'tonight')}!",
        "guest_list_position": 284,
    })

if __name__ == "__main__":
    app.run(debug=True, port=5000, host="0.0.0.0")
