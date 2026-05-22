"""
NightFlow Backend API
Flask REST API with SQLAlchemy ORM + JWT Authentication
"""

from flask import Flask, jsonify, request, make_response, g, send_from_directory
from flask_sqlalchemy import SQLAlchemy
from sqlalchemy.orm import DeclarativeBase
from datetime import datetime, date, timedelta
import sqlite3
import json
import uuid
import hashlib
import hmac
import base64
import os
from functools import wraps
from dotenv import load_dotenv

# Load environment variables
load_dotenv()

# Get the project root (parent of backend folder)
PROJECT_ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
FRONTEND_DIR = os.path.join(PROJECT_ROOT, 'frontend')

# SQLAlchemy Base class
class Base(DeclarativeBase):
    pass

db = SQLAlchemy(model_class=Base)

app = Flask(__name__, static_folder=FRONTEND_DIR, static_url_path='')
app.config['SECRET_KEY'] = os.getenv('SECRET_KEY', 'nightflow-secret-key-change-in-production')
app.config['SQLALCHEMY_DATABASE_URI'] = os.getenv('DATABASE_URL', 'sqlite:///nightflow.db')
app.config['SQLALCHEMY_TRACK_MODIFICATIONS'] = False

# Initialize SQLAlchemy with app
db.init_app(app)

# Legacy DB_PATH for backwards compatibility with raw sqlite
DB_PATH = os.path.join(os.path.dirname(__file__), 'nightflow.db')

# ════════════════════════════════════════════════════════════
#  SQLALCHEMY MODELS
# ════════════════════════════════════════════════════════════

class User(db.Model):
    __tablename__ = 'users'

    id = db.Column(db.String(50), primary_key=True)
    name = db.Column(db.String(100), nullable=False)
    email = db.Column(db.String(120), unique=True, nullable=False)
    password_hash = db.Column(db.String(256), nullable=False)
    role = db.Column(db.String(20), default='customer')
    venue_id = db.Column(db.String(50), db.ForeignKey('venues.id'), nullable=True)
    venue_name = db.Column(db.String(100), nullable=True)
    customer_id = db.Column(db.String(50), nullable=True)
    points = db.Column(db.Integer, default=0)
    tier = db.Column(db.String(20), default='silver')
    created_at = db.Column(db.String(50), default=lambda: datetime.utcnow().isoformat())

    def to_dict(self):
        return {
            'id': self.id,
            'name': self.name,
            'email': self.email,
            'role': self.role,
            'venue_id': self.venue_id,
            'venue_name': self.venue_name,
            'customer_id': self.customer_id,
            'points': self.points,
            'tier': self.tier,
            'created_at': self.created_at
        }

class Venue(db.Model):
    __tablename__ = 'venues'

    id = db.Column(db.String(50), primary_key=True)
    name = db.Column(db.String(100), nullable=False)
    type = db.Column(db.String(50))
    category = db.Column(db.String(50))
    address = db.Column(db.String(200))
    phone = db.Column(db.String(50))
    email = db.Column(db.String(120))
    website = db.Column(db.String(200))
    instagram = db.Column(db.String(100))
    capacity = db.Column(db.Integer, default=0)
    current_guests = db.Column(db.Integer, default=0)
    image_class = db.Column(db.String(50))
    image_emoji = db.Column(db.String(10))
    photo_url = db.Column(db.String(500))
    photos = db.Column(db.Text)  # JSON array
    maps_url = db.Column(db.String(500))
    maps_place_id = db.Column(db.String(100))
    lat = db.Column(db.Float)
    lng = db.Column(db.Float)
    rating = db.Column(db.Float, default=0)
    rating_count = db.Column(db.Integer, default=0)
    min_spend = db.Column(db.Float, default=0)
    music_genres = db.Column(db.String(200))
    description = db.Column(db.Text)
    open_days = db.Column(db.String(50))
    open_hours = db.Column(db.String(50))
    has_shisha = db.Column(db.Integer, default=0)
    has_restaurant = db.Column(db.Integer, default=0)
    has_beach = db.Column(db.Integer, default=0)
    verified = db.Column(db.Integer, default=0)
    english_staff = db.Column(db.Integer, default=1)

    events = db.relationship('Event', backref='venue', lazy=True)
    reservations = db.relationship('Reservation', backref='venue', lazy=True)

    def to_dict(self):
        return {c.name: getattr(self, c.name) for c in self.__table__.columns}

class Event(db.Model):
    __tablename__ = 'events'

    id = db.Column(db.String(50), primary_key=True)
    venue_id = db.Column(db.String(50), db.ForeignKey('venues.id'))
    title = db.Column(db.String(200), nullable=False)
    genre = db.Column(db.String(100))
    genre_icon = db.Column(db.String(10))
    dj = db.Column(db.String(100))
    date = db.Column(db.String(20))
    start_time = db.Column(db.String(10))
    entry_price = db.Column(db.Float, default=0)
    min_spend_vip = db.Column(db.Float, default=0)
    popularity = db.Column(db.Integer, default=0)
    badges = db.Column(db.Text)  # JSON array
    trending = db.Column(db.Integer, default=0)
    student_night = db.Column(db.Integer, default=0)
    tourist_friendly = db.Column(db.Integer, default=0)
    vip_available = db.Column(db.Integer, default=1)
    guest_list_open = db.Column(db.Integer, default=1)
    description = db.Column(db.Text)

    def to_dict(self):
        data = {c.name: getattr(self, c.name) for c in self.__table__.columns}
        if data.get('badges'):
            try:
                data['badges'] = json.loads(data['badges'])
            except:
                pass
        return data

class Reservation(db.Model):
    __tablename__ = 'reservations'

    id = db.Column(db.String(50), primary_key=True)
    customer_id = db.Column(db.String(50))
    customer_name = db.Column(db.String(100))
    customer_initials = db.Column(db.String(10))
    venue_id = db.Column(db.String(50), db.ForeignKey('venues.id'))
    event_id = db.Column(db.String(50), db.ForeignKey('events.id'))
    table_number = db.Column(db.String(20))
    table_type = db.Column(db.String(20), default='standard')
    guests = db.Column(db.Integer, default=2)
    arrival_time = db.Column(db.String(10))
    min_spend = db.Column(db.Float, default=0)
    status = db.Column(db.String(20), default='pending')
    created_at = db.Column(db.String(50), default=lambda: datetime.utcnow().isoformat())
    notes = db.Column(db.Text)
    deposit_paid = db.Column(db.Integer, default=0)
    checked_in = db.Column(db.Integer, default=0)
    checkin_time = db.Column(db.String(10))

    def to_dict(self):
        return {c.name: getattr(self, c.name) for c in self.__table__.columns}

class Customer(db.Model):
    __tablename__ = 'customers'

    id = db.Column(db.String(50), primary_key=True)
    name = db.Column(db.String(100), nullable=False)
    initials = db.Column(db.String(10))
    email = db.Column(db.String(120))
    phone = db.Column(db.String(50))
    birthday = db.Column(db.String(20))
    tier = db.Column(db.String(20), default='silver')
    points = db.Column(db.Integer, default=0)
    total_visits = db.Column(db.Integer, default=0)
    avg_spend_month = db.Column(db.Float, default=0)
    fav_genre = db.Column(db.String(100))
    customer_since = db.Column(db.String(20))
    last_visit = db.Column(db.String(20))
    notes = db.Column(db.Text)

    def to_dict(self):
        return {c.name: getattr(self, c.name) for c in self.__table__.columns}

class Favorite(db.Model):
    __tablename__ = 'favorites'

    id = db.Column(db.String(50), primary_key=True)
    user_id = db.Column(db.String(50), db.ForeignKey('users.id'), nullable=False)
    venue_id = db.Column(db.String(50), db.ForeignKey('venues.id'), nullable=False)
    created_at = db.Column(db.String(50), default=lambda: datetime.utcnow().isoformat())

    def to_dict(self):
        return {c.name: getattr(self, c.name) for c in self.__table__.columns}

# ════════════════════════════════════════════════════════════
#  DATABASE (Legacy SQLite connection for backwards compatibility)
# ════════════════════════════════════════════════════════════

def get_db():
    if 'db' not in g:
        g.db = sqlite3.connect(DB_PATH)
        g.db.row_factory = sqlite3.Row
    return g.db

@app.teardown_appcontext
def close_db(exception):
    conn = g.pop('db', None)
    if conn is not None:
        conn.close()

def dict_from_row(row):
    return dict(row) if row else None

def init_db():
    db = sqlite3.connect(DB_PATH)
    db.executescript('''
        CREATE TABLE IF NOT EXISTS users (
            id TEXT PRIMARY KEY,
            name TEXT NOT NULL,
            email TEXT UNIQUE NOT NULL,
            password_hash TEXT NOT NULL,
            role TEXT DEFAULT 'customer',
            venue_id TEXT,
            venue_name TEXT,
            customer_id TEXT,
            points INTEGER DEFAULT 0,
            tier TEXT DEFAULT 'silver',
            created_at TEXT DEFAULT CURRENT_TIMESTAMP
        );

        CREATE TABLE IF NOT EXISTS venues (
            id TEXT PRIMARY KEY,
            name TEXT NOT NULL,
            type TEXT,
            category TEXT,
            address TEXT,
            phone TEXT,
            email TEXT,
            website TEXT,
            instagram TEXT,
            capacity INTEGER DEFAULT 0,
            current_guests INTEGER DEFAULT 0,
            image_class TEXT,
            image_emoji TEXT,
            photo_url TEXT,
            photos TEXT,
            maps_url TEXT,
            maps_place_id TEXT,
            lat REAL,
            lng REAL,
            rating REAL DEFAULT 0,
            rating_count INTEGER DEFAULT 0,
            min_spend REAL DEFAULT 0,
            music_genres TEXT,
            description TEXT,
            open_days TEXT,
            open_hours TEXT,
            has_shisha INTEGER DEFAULT 0,
            has_restaurant INTEGER DEFAULT 0,
            has_beach INTEGER DEFAULT 0,
            verified INTEGER DEFAULT 0,
            english_staff INTEGER DEFAULT 1
        );

        CREATE TABLE IF NOT EXISTS events (
            id TEXT PRIMARY KEY,
            venue_id TEXT,
            title TEXT NOT NULL,
            genre TEXT,
            genre_icon TEXT,
            dj TEXT,
            date TEXT,
            start_time TEXT,
            entry_price REAL DEFAULT 0,
            min_spend_vip REAL DEFAULT 0,
            popularity INTEGER DEFAULT 0,
            badges TEXT,
            trending INTEGER DEFAULT 0,
            student_night INTEGER DEFAULT 0,
            tourist_friendly INTEGER DEFAULT 0,
            vip_available INTEGER DEFAULT 1,
            guest_list_open INTEGER DEFAULT 1,
            description TEXT,
            FOREIGN KEY (venue_id) REFERENCES venues(id)
        );

        CREATE TABLE IF NOT EXISTS customers (
            id TEXT PRIMARY KEY,
            name TEXT NOT NULL,
            initials TEXT,
            email TEXT,
            phone TEXT,
            birthday TEXT,
            tier TEXT DEFAULT 'silver',
            points INTEGER DEFAULT 0,
            total_visits INTEGER DEFAULT 0,
            avg_spend_month REAL DEFAULT 0,
            fav_genre TEXT,
            customer_since TEXT,
            last_visit TEXT,
            notes TEXT
        );

        CREATE TABLE IF NOT EXISTS reservations (
            id TEXT PRIMARY KEY,
            customer_id TEXT,
            customer_name TEXT,
            customer_initials TEXT,
            venue_id TEXT,
            event_id TEXT,
            table_number TEXT,
            table_type TEXT DEFAULT 'standard',
            guests INTEGER DEFAULT 2,
            arrival_time TEXT,
            min_spend REAL DEFAULT 0,
            status TEXT DEFAULT 'pending',
            created_at TEXT DEFAULT CURRENT_TIMESTAMP,
            notes TEXT,
            deposit_paid INTEGER DEFAULT 0,
            checked_in INTEGER DEFAULT 0,
            checkin_time TEXT,
            FOREIGN KEY (venue_id) REFERENCES venues(id),
            FOREIGN KEY (event_id) REFERENCES events(id)
        );

        CREATE TABLE IF NOT EXISTS promoters (
            id TEXT PRIMARY KEY,
            name TEXT NOT NULL,
            initials TEXT,
            guests_brought INTEGER DEFAULT 0,
            revenue_generated REAL DEFAULT 0,
            commission REAL DEFAULT 0,
            status TEXT DEFAULT 'active'
        );

        CREATE TABLE IF NOT EXISTS activity_feed (
            id TEXT PRIMARY KEY,
            user_name TEXT,
            initials TEXT,
            action TEXT,
            time TEXT,
            icon TEXT,
            event_id TEXT,
            created_at TEXT DEFAULT CURRENT_TIMESTAMP
        );

        CREATE TABLE IF NOT EXISTS refresh_tokens (
            id TEXT PRIMARY KEY,
            user_id TEXT NOT NULL,
            token_hash TEXT NOT NULL,
            expires_at TEXT NOT NULL,
            created_at TEXT DEFAULT CURRENT_TIMESTAMP,
            FOREIGN KEY (user_id) REFERENCES users(id)
        );

        CREATE TABLE IF NOT EXISTS favorites (
            id TEXT PRIMARY KEY,
            user_id TEXT NOT NULL,
            venue_id TEXT NOT NULL,
            created_at TEXT DEFAULT CURRENT_TIMESTAMP,
            FOREIGN KEY (user_id) REFERENCES users(id),
            FOREIGN KEY (venue_id) REFERENCES venues(id)
        );

        CREATE INDEX IF NOT EXISTS idx_users_email ON users(email);
        CREATE INDEX IF NOT EXISTS idx_events_venue ON events(venue_id);
        CREATE INDEX IF NOT EXISTS idx_reservations_venue ON reservations(venue_id);
        CREATE INDEX IF NOT EXISTS idx_reservations_status ON reservations(status);
        CREATE INDEX IF NOT EXISTS idx_favorites_user ON favorites(user_id);
    ''')
    db.commit()
    db.close()

def seed_db():
    db = sqlite3.connect(DB_PATH)
    cursor = db.cursor()

    cursor.execute("SELECT COUNT(*) FROM venues")
    if cursor.fetchone()[0] > 0:
        db.close()
        return

    # Real Rethymno venues with accurate data including photos and maps
    # (id, name, type, category, address, phone, email, website, instagram, capacity, current_guests,
    #  image_class, image_emoji, photo_url, photos, maps_url, maps_place_id, lat, lng,
    #  rating, rating_count, min_spend, music_genres, description,
    #  open_days, open_hours, has_shisha, has_restaurant, has_beach, verified, english_staff)
    venues = [
        ("v1", "ICE Club", "Nightclub", "nightclub",
         "Salaminos 22, Rethymno 741 31", None, None, None, None,
         500, 0, "ic1", u"\U0001F9CA",
         "https://images.unsplash.com/photo-1571266028243-d220c6a4b34a?w=1200",
         '["https://images.unsplash.com/photo-1571266028243-d220c6a4b34a?w=1200","https://images.unsplash.com/photo-1571266028243-e4733b0f0bb0?w=800"]',
         "https://maps.google.com/?q=ICE+Club+Rethymno+Salaminos", "ChIJice_club_rethymno",
         35.3662, 24.4731,
         2.9, 150, 0,
         "Commercial, Greek, Electronic",
         "Nightclub experience in Rethymno with full club atmosphere. One of the city's premier nightlife destinations featuring top DJs and an energetic atmosphere.",
         "thu,fri,sat,sun", "00:00-06:00", 0, 0, 0, 1, 1),

        ("v2", "Louvro", "Nightclub", "nightclub",
         "Salaminos 18, Rethymno 74100", "698 3730468", "louvro.bookings@gmail.com", "louvro.club", "louvro.club",
         800, 0, "ic2", u"\U0001F3AD",
         "https://images.unsplash.com/photo-1574391884720-bbc049ec09ad?w=1200",
         '["https://images.unsplash.com/photo-1574391884720-bbc049ec09ad?w=1200","https://images.unsplash.com/photo-1516450360452-9312f5e86fc7?w=800"]',
         "https://maps.google.com/?q=Louvro+Rethymno+Salaminos", "ChIJlouvro_rethymno",
         35.3660, 24.4728,
         4.5, 500, 0,
         "Live singers, Dancers, Commercial",
         "Crete's biggest nightlife destination, inspired by Paris. Live singers, dancers, sheesha, signature cocktails. An unforgettable experience every night.",
         "wed,fri,sat,sun", "23:30-06:00", 1, 0, 0, 1, 1),

        ("v3", "Minibar", "Nightclub", "nightclub",
         "Ioulias Petychaki 6, Rethymno 741 50", "2831 055381", None, None, None,
         300, 0, "ic3", u"\U0001F37E",
         "https://images.unsplash.com/photo-1551024601-bec78aea704b?w=1200",
         '["https://images.unsplash.com/photo-1551024601-bec78aea704b?w=1200","https://images.unsplash.com/photo-1470225620780-dba8ba36b745?w=800"]',
         "https://maps.google.com/?q=Minibar+Rethymno+Beach", "ChIJminibar_rethymno",
         35.3715, 24.4802,
         3.6, 389, 50,
         "Commercial, House, Greek",
         "Located in Rethimnon Beach area. Premium nightclub experience with VIP tables and bottle service. The place to be on weekend nights.",
         "fri,sat", "00:00-06:00", 0, 0, 0, 1, 1),

        ("v4", "Baja Beach Club", "Beach Club", "beach_club",
         "Rethymno Beach, Rethymno 74100", None, None, "bajabeach.gr", "bajabeachclubcrete",
         1000, 0, "ic4", u"\U0001F3D6",
         "https://images.unsplash.com/photo-1507525428034-b723cf961d3e?w=1200",
         '["https://images.unsplash.com/photo-1507525428034-b723cf961d3e?w=1200","https://images.unsplash.com/photo-1519046904884-53103b34b206?w=800"]',
         "https://maps.google.com/?q=Baja+Beach+Club+Rethymno", "ChIJbaja_beach_rethymno",
         35.3680, 24.4850,
         4.7, 800, 0,
         "International DJs, House, Commercial",
         "Sophisticated luxury beach club. Mediterranean cuisine, sunset views, signature cocktails. Large-scale events with international DJs. Beach gazebos, pool, daybeds available.",
         "daily", "10:00-02:00", 0, 1, 1, 1, 1),

        ("v5", "Fraoules", "Coffee House / Bar", "cafeteria",
         "El. Venizelou 62, Rethymno 74100", "2831 024525", None, None, "fraoules_rethymno",
         200, 0, "ic5", u"\U0001F353",
         "https://images.unsplash.com/photo-1572116469696-31de0f17cc34?w=1200",
         '["https://images.unsplash.com/photo-1572116469696-31de0f17cc34?w=1200","https://images.unsplash.com/photo-1559329007-40df8a9345d8?w=800"]',
         "https://maps.google.com/?q=Fraoules+Rethymno+Venizelou", "ChIJfraoules_rethymno",
         35.3695, 24.4765,
         4.6, 2644, 0,
         "Upbeat Indoor Rhythms",
         "Coffee house, bar, and restaurant with party nights on selected dates. Shisha available. Great for day drinks and evening cocktails with friends.",
         "daily", "09:00-03:00", 1, 1, 0, 1, 1),

        ("v6", "Store 311", "All Day Bar", "cafeteria",
         "El. Venizelou 73, Paralia, Rethymno 74100", "694 452 5030", "store311alldaybar@gmail.com", "store311.livemenu.gr", "store_311_alldaybar",
         250, 0, "ic1", u"\U0001F378",
         "https://images.unsplash.com/photo-1470337458703-46ad1756a187?w=1200",
         '["https://images.unsplash.com/photo-1470337458703-46ad1756a187?w=1200","https://images.unsplash.com/photo-1525268323446-0505b6fe7778?w=800"]',
         "https://maps.google.com/?q=Store+311+Rethymno+Paralia", "ChIJstore311_rethymno",
         35.3698, 24.4770,
         4.4, 2570, 0,
         "Coffee to Cocktails",
         "From coffee to cocktails to vibrant night scene. All day bar experience with 19K followers. Perfect for any time of day.",
         "daily", "08:00-03:00", 0, 1, 0, 1, 1),

        ("v7", "LUX All Day Bar", "Cafe Lounge", "cafeteria",
         "El. Venizelou 65-68, Rethymno 74100", "2831 020303", "luxcaferethimno@gmail.com", None, "lux_rethymno",
         300, 0, "ic2", u"✨",
         "https://images.unsplash.com/photo-1566737236500-c8ac43014a67?w=1200",
         '["https://images.unsplash.com/photo-1566737236500-c8ac43014a67?w=1200","https://images.unsplash.com/photo-1552566626-52f8b828add9?w=800"]',
         "https://maps.google.com/?q=LUX+Cafe+Rethymno+Venizelou", "ChIJlux_rethymno",
         35.3692, 24.4762,
         4.8, 1289, 0,
         "Lounge, Cocktail",
         "The place to be on the beach road downtown. Cafe lounge and cocktail bar with party nights. 31K followers can't be wrong. Upscale atmosphere with excellent service.",
         "daily", "08:00-03:00", 0, 1, 0, 1, 1),
    ]
    cursor.executemany("""INSERT INTO venues VALUES (?,?,?,?,?,?,?,?,?,?,?,?,?,?,?,?,?,?,?,?,?,?,?,?,?,?,?,?,?,?,?)""", venues)

    # Events linked to venues - will be dynamically shown based on day
    events = [
        ("e1", "v1", "ICE Club Night", "Commercial / Greek / Electronic", u"\U0001F9CA", "Resident DJ", "2026-06-20", "00:00", 10, 100, 78, '["live"]', 1, 0, 1, 1, 1, "Full club night at ICE Club."),
        ("e2", "v2", "Louvro Live Experience", "Live / Commercial", u"\U0001F3AD", "Live Singers & Dancers", "2026-06-20", "23:30", 15, 150, 92, '["trending","live"]', 1, 0, 1, 1, 1, "Crete's biggest nightlife experience with live performers."),
        ("e3", "v3", "Minibar Weekend", "House / Commercial", u"\U0001F37E", "Guest DJ", "2026-06-20", "00:00", 12, 50, 72, '["vip"]', 1, 0, 1, 1, 1, "Premium nightclub vibes at Minibar."),
        ("e4", "v4", "Baja Sunday Party", "House / International", u"\U0001F3D6", "International DJ", "2026-06-20", "18:00", 20, 100, 88, '["trending","tourist"]', 1, 0, 1, 1, 1, "Sunday beach party at Baja Beach Club."),
        ("e5", "v5", "Fraoules Night", "Upbeat / Commercial", u"\U0001F353", "Resident", "2026-06-20", "22:30", 0, 0, 65, '["new"]', 0, 0, 1, 1, 1, "Party night at Fraoules."),
        ("e6", "v6", "Store 311 Vibes", "Cocktail / Dance", u"\U0001F378", "Resident", "2026-06-20", "22:00", 0, 0, 60, '[]', 0, 0, 1, 1, 1, "Evening vibes at Store 311."),
        ("e7", "v7", "LUX Lounge Night", "Lounge / Cocktail", u"✨", "Resident", "2026-06-20", "21:00", 0, 0, 58, '[]', 0, 0, 1, 1, 1, "Upscale lounge night at LUX."),
    ]
    cursor.executemany("INSERT INTO events VALUES (?,?,?,?,?,?,?,?,?,?,?,?,?,?,?,?,?,?)", events)

    customers = [
        ("c1","Kostas Papadakis","KP","k.papadakis@gmail.com","+30 694 123 4567","1990-03-15","black",5800,48,4200,"Progressive House","2022-03-01","2025-06-18","Always books VIP."),
        ("c2","Elena Dimitriou","ED","elena.d@hotmail.com","+30 697 234 5678","1995-07-22","black",4650,34,3100,"Deep House","2023-01-10","2025-06-15","VIP group bookings."),
        ("c3","Nikos Kritis","NK","nikos.kritis@gmail.com","+30 698 345 6789","1998-11-08","gold",2980,22,1850,"R&B / Hip-Hop","2023-06-20","2025-06-10","Student. Groups of 5-8."),
        ("c4","Sofia Manousakis","SM","sofia.m@yahoo.gr","+30 693 456 7890","1992-12-03","gold",3420,29,2200,"Techno","2022-09-15","2025-06-12","Prefers techno nights."),
        ("c5","Dimitris Petrakis","DP","dpetrakis@gmail.com","+30 699 567 8901","1997-02-14","gold",2100,18,1400,"Afro House","2024-02-01","2025-06-05","Brings tourist friends."),
        ("c6","Anna Papageorgiou","AP","anna.papa@gmail.com","+30 696 678 9012","2000-08-30","silver",980,9,680,"Pop / Dance","2024-04-10","2025-05-28","Student, weekend only."),
    ]
    cursor.executemany("INSERT INTO customers VALUES (?,?,?,?,?,?,?,?,?,?,?,?,?,?)", customers)

    reservations = [
        ("r1","c1","Kostas Papadakis","KP","v1","e1","V1","vip",8,"00:30",100,"confirmed","2025-06-18T14:00:00","Bottle service at ICE Club",1,0,None),
        ("r2","c2","Maria Konstantinou","MK","v2","e2","V2","vip",6,"00:00",150,"confirmed","2025-06-19T10:00:00","Birthday at Louvro",1,0,None),
        ("r3","c3","Nikos Vardalakis","NV","v3","e3","T1","vip",5,"01:00",50,"confirmed","2025-06-19T16:00:00","Minibar VIP",0,0,None),
        ("r4","c4","Alex Manoussakis","AM","v1","e1","T2","standard",4,"00:30",0,"confirmed","2025-06-19T18:00:00","",0,1,"00:45"),
        ("r5",None,"James Patterson","JP","v4","e4","G1","standard",6,"18:00",0,"pending","2025-06-20T09:00:00","Tourist group, Baja Beach Sunday",0,0,None),
        ("r6","c5","Sofia Psaroudaki","SP","v2","e2","T5","standard",8,"23:30",0,"confirmed","2025-06-18T20:00:00","Louvro party group",1,0,None),
        ("r7","c6","Anna Papageorgiou","AP","v5","e5","T3","standard",4,"22:30",0,"pending","2025-06-20T11:00:00","Fraoules chill night",0,0,None),
    ]
    cursor.executemany("INSERT INTO reservations VALUES (?,?,?,?,?,?,?,?,?,?,?,?,?,?,?,?,?)", reservations)

    promoters = [
        ("p1","Giorgos Maniatis","GM",94,3760,376,"active"),
        ("p2","Dimitra Chrysou","DC",78,2970,297,"active"),
        ("p3","Stavros Kaloudis","SK",62,2480,248,"active"),
        ("p4","Ioanna Paterakis","IP",45,1800,180,"top"),
        ("p5","Manolis Sfakianakis","MS",38,1520,152,"pending"),
    ]
    cursor.executemany("INSERT INTO promoters VALUES (?,?,?,?,?,?,?)", promoters)

    activity = [
        ("f1","Maria K.","M","joined Louvro guest list","2 min ago",u"\U0001F3AD","e2",datetime.now().isoformat()),
        ("f2","Nikos P.","N","checked in at ICE Club","8 min ago",u"\U0001F9CA","e1",datetime.now().isoformat()),
        ("f3","Elena D.","E","earned Black tier status","15 min ago",u"\U0001F48E",None,datetime.now().isoformat()),
        ("f4","Alex M. + 8 others","A","heading to Baja Beach Club","23 min ago",u"\U0001F3D6","e4",datetime.now().isoformat()),
        ("f5","Kostas V.","K","booked VIP at Minibar","31 min ago",u"\U0001F37E","e3",datetime.now().isoformat()),
        ("f6","Sofia P.","S","checked in at Fraoules","45 min ago",u"\U0001F353","e5",datetime.now().isoformat()),
        ("f7","George L.","G","joined LUX guest list","52 min ago",u"✨","e7",datetime.now().isoformat()),
    ]
    cursor.executemany("INSERT INTO activity_feed VALUES (?,?,?,?,?,?,?,?)", activity)

    users = [
        ("u_club_1","Manager ICE Club","club@nightflow.gr",hash_password("club123"),"club","v1","ICE Club",None,0,"silver",datetime.now().isoformat()),
        ("u_customer_1","Νίκος Πελάτης","customer@nightflow.gr",hash_password("customer123"),"customer",None,None,"c3",980,"silver",datetime.now().isoformat()),
    ]
    cursor.executemany("INSERT INTO users VALUES (?,?,?,?,?,?,?,?,?,?,?)", users)

    db.commit()
    db.close()

# ════════════════════════════════════════════════════════════
#  JWT AUTHENTICATION
# ════════════════════════════════════════════════════════════

def hash_password(password: str) -> str:
    return hashlib.sha256(password.encode('utf-8')).hexdigest()

def create_jwt(payload: dict, expires_delta: timedelta = timedelta(hours=24)) -> str:
    header = {"alg": "HS256", "typ": "JWT"}
    payload["exp"] = (datetime.utcnow() + expires_delta).timestamp()
    payload["iat"] = datetime.utcnow().timestamp()

    def b64encode(data):
        return base64.urlsafe_b64encode(json.dumps(data).encode()).decode().rstrip('=')

    header_b64 = b64encode(header)
    payload_b64 = b64encode(payload)
    message = f"{header_b64}.{payload_b64}"

    signature = hmac.new(
        app.config['SECRET_KEY'].encode(),
        message.encode(),
        hashlib.sha256
    ).digest()
    signature_b64 = base64.urlsafe_b64encode(signature).decode().rstrip('=')

    return f"{message}.{signature_b64}"

def decode_jwt(token: str) -> dict | None:
    try:
        parts = token.split('.')
        if len(parts) != 3:
            return None

        header_b64, payload_b64, signature_b64 = parts
        message = f"{header_b64}.{payload_b64}"

        expected_sig = hmac.new(
            app.config['SECRET_KEY'].encode(),
            message.encode(),
            hashlib.sha256
        ).digest()
        expected_sig_b64 = base64.urlsafe_b64encode(expected_sig).decode().rstrip('=')

        if not hmac.compare_digest(signature_b64, expected_sig_b64):
            return None

        padding = 4 - len(payload_b64) % 4
        if padding != 4:
            payload_b64 += '=' * padding

        payload = json.loads(base64.urlsafe_b64decode(payload_b64))

        if payload.get('exp', 0) < datetime.utcnow().timestamp():
            return None

        return payload
    except Exception:
        return None

def create_refresh_token(user_id: str) -> str:
    token = uuid.uuid4().hex + uuid.uuid4().hex
    token_hash = hashlib.sha256(token.encode()).hexdigest()
    expires_at = (datetime.utcnow() + timedelta(days=30)).isoformat()

    db = get_db()
    db.execute(
        "INSERT INTO refresh_tokens (id, user_id, token_hash, expires_at) VALUES (?, ?, ?, ?)",
        (uuid.uuid4().hex, user_id, token_hash, expires_at)
    )
    db.commit()
    return token

def verify_refresh_token(token: str) -> str | None:
    token_hash = hashlib.sha256(token.encode()).hexdigest()
    db = get_db()
    row = db.execute(
        "SELECT user_id, expires_at FROM refresh_tokens WHERE token_hash = ?",
        (token_hash,)
    ).fetchone()

    if not row:
        return None
    if datetime.fromisoformat(row['expires_at']) < datetime.utcnow():
        db.execute("DELETE FROM refresh_tokens WHERE token_hash = ?", (token_hash,))
        db.commit()
        return None
    return row['user_id']

def current_user():
    auth = request.headers.get('Authorization', '')
    if not auth.startswith('Bearer '):
        return None
    token = auth[7:]
    payload = decode_jwt(token)
    if not payload:
        return None

    db = get_db()
    row = db.execute("SELECT * FROM users WHERE id = ?", (payload.get('sub'),)).fetchone()
    return dict_from_row(row)

def require_auth(role=None):
    def decorator(fn):
        @wraps(fn)
        def wrapper(*args, **kwargs):
            user = current_user()
            if not user:
                return jsonify({"success": False, "error": "Authentication required"}), 401
            if role and user.get('role') != role:
                return jsonify({"success": False, "error": "Forbidden"}), 403
            request.user = user
            return fn(*args, **kwargs)
        return wrapper
    return decorator

def public_user(user: dict) -> dict:
    return {k: v for k, v in user.items() if k != 'password_hash'}

# ════════════════════════════════════════════════════════════
#  VENUE HELPERS
# ════════════════════════════════════════════════════════════

DAY_MAP = {0: 'mon', 1: 'tue', 2: 'wed', 3: 'thu', 4: 'fri', 5: 'sat', 6: 'sun'}

def is_open_tonight(venue: dict) -> dict:
    """
    Check if venue is open tonight based on category and day of week.
    Returns dict with status info.
    """
    now = datetime.now()
    current_day = DAY_MAP[now.weekday()]
    current_hour = now.hour

    category = venue.get('category', '')
    open_days = venue.get('open_days', 'daily')
    name = venue.get('name', '')

    result = {
        'is_open': False,
        'status': 'closed',
        'status_label': 'Closed',
        'badge': None,
        'opens_at': None
    }

    # Parse open days
    if open_days == 'daily':
        days_open = ['mon', 'tue', 'wed', 'thu', 'fri', 'sat', 'sun']
    else:
        days_open = [d.strip() for d in open_days.split(',')]

    # Check by category
    if category == 'nightclub':
        # Nightclubs: open on their scheduled days, typically after midnight
        if current_day in days_open:
            result['is_open'] = True
            result['status'] = 'open_tonight'
            result['status_label'] = 'Open Tonight'
            result['badge'] = 'OPEN TONIGHT'
        else:
            # Find next open day
            result['status'] = 'closed'
            result['status_label'] = f"Opens {days_open[0].capitalize()}" if days_open else 'Closed'

    elif category == 'beach_club':
        # Baja Beach Club: always open as beach/restaurant, party only on Sundays
        result['is_open'] = True
        if current_day == 'sun':
            result['status'] = 'party_tonight'
            result['status_label'] = 'Party Tonight'
            result['badge'] = 'PARTY TONIGHT'
        else:
            result['status'] = 'open'
            result['status_label'] = 'Beach & Restaurant'
            result['badge'] = 'OPEN'

    elif category == 'cafeteria':
        # Cafeterias: always open, party nights on weekends
        result['is_open'] = True
        result['status'] = 'open'
        result['status_label'] = 'Open'
        result['badge'] = 'OPEN'

        # Party nights on Fri/Sat
        if current_day in ['fri', 'sat']:
            result['badge'] = 'PARTY NIGHT'
            result['status'] = 'party_night'
            result['status_label'] = 'Party Night'

    return result


def get_simulated_crowd(venue: dict) -> int:
    """
    Simulate crowd percentage based on time of day, day of week, and venue type.
    Updates roughly every 5 minutes (based on minute hash).
    """
    import random
    now = datetime.now()
    current_hour = now.hour
    current_day = now.weekday()  # 0=Mon, 6=Sun

    category = venue.get('category', '')
    capacity = venue.get('capacity', 100)
    venue_id = venue.get('id', 'v1')

    # Seed random with venue_id + current 5-min window for consistent updates
    time_seed = now.strftime('%Y%m%d%H') + str(now.minute // 5)
    random.seed(hash(venue_id + time_seed))

    base_pct = 0

    if category == 'nightclub':
        # Nightclubs peak 01:00-03:00
        if current_hour >= 23 or current_hour < 5:
            if current_hour == 0:
                base_pct = random.randint(30, 50)
            elif current_hour == 1:
                base_pct = random.randint(60, 85)
            elif current_hour == 2:
                base_pct = random.randint(70, 95)
            elif current_hour == 3:
                base_pct = random.randint(50, 75)
            elif current_hour == 4:
                base_pct = random.randint(20, 40)
            else:
                base_pct = random.randint(5, 15)
        else:
            base_pct = 0

        # Weekend boost
        if current_day in [4, 5]:  # Fri, Sat
            base_pct = min(100, int(base_pct * 1.2))

    elif category == 'beach_club':
        # Beach clubs peak afternoon/evening
        if 10 <= current_hour <= 20:
            if current_hour < 14:
                base_pct = random.randint(20, 45)
            elif current_hour < 18:
                base_pct = random.randint(50, 80)
            else:
                base_pct = random.randint(60, 90)
        elif 20 < current_hour <= 24:
            base_pct = random.randint(30, 60)
        else:
            base_pct = 0

        # Sunday party boost
        if current_day == 6:  # Sunday
            base_pct = min(100, int(base_pct * 1.3))

    elif category == 'cafeteria':
        # Cafeterias busy throughout day, peak evening
        if 8 <= current_hour < 12:
            base_pct = random.randint(20, 40)
        elif 12 <= current_hour < 17:
            base_pct = random.randint(30, 55)
        elif 17 <= current_hour < 22:
            base_pct = random.randint(50, 80)
        elif 22 <= current_hour or current_hour < 3:
            base_pct = random.randint(40, 70)
            # Weekend party boost
            if current_day in [4, 5]:
                base_pct = min(100, int(base_pct * 1.2))
        else:
            base_pct = 0

    return int(capacity * base_pct / 100)


# ════════════════════════════════════════════════════════════
#  CORS
# ════════════════════════════════════════════════════════════

@app.after_request
def add_cors(resp):
    resp.headers["Access-Control-Allow-Origin"] = "*"
    resp.headers["Access-Control-Allow-Methods"] = "GET,POST,PUT,DELETE,PATCH,OPTIONS"
    resp.headers["Access-Control-Allow-Headers"] = "Content-Type,Authorization"
    return resp

@app.before_request
def handle_options():
    if request.method == "OPTIONS":
        return make_response("", 204)

# ════════════════════════════════════════════════════════════
#  ROUTES - Health Check
# ════════════════════════════════════════════════════════════

@app.route('/health')
def health_check():
    """Health check endpoint for Railway monitoring"""
    try:
        # Test database connection
        conn = get_db()
        conn.execute("SELECT 1").fetchone()
        db_status = 'connected'
    except Exception as e:
        db_status = f'error: {str(e)}'

    return jsonify({
        'status': 'healthy',
        'database': db_status,
        'timestamp': datetime.utcnow().isoformat()
    })

# ════════════════════════════════════════════════════════════
#  ROUTES - Auth
# ════════════════════════════════════════════════════════════

@app.route("/api")
def api_index():
    return jsonify({"service": "NightFlow API", "version": "2.0.0", "status": "running", "auth": "JWT"})

@app.route("/api/auth/login", methods=["POST"])
def login():
    data = request.get_json() or {}
    email = (data.get("email") or "").strip().lower()
    password = data.get("password") or ""

    db = get_db()
    user = db.execute("SELECT * FROM users WHERE LOWER(email) = ?", (email,)).fetchone()

    if not user or user['password_hash'] != hash_password(password):
        return jsonify({"success": False, "error": "Λάθος email ή κωδικός"}), 401

    user_dict = dict_from_row(user)
    access_token = create_jwt({"sub": user['id'], "role": user['role'], "email": user['email']})
    refresh_token = create_refresh_token(user['id'])

    return jsonify({
        "success": True,
        "token": access_token,
        "refresh_token": refresh_token,
        "user": public_user(user_dict),
        "expires_in": 86400
    })

@app.route("/api/auth/register", methods=["POST"])
def register():
    data = request.get_json() or {}
    name = (data.get("name") or "").strip()
    email = (data.get("email") or "").strip().lower()
    password = data.get("password") or ""
    role = data.get("role") or "customer"

    if role not in ["customer", "club"]:
        return jsonify({"success": False, "error": "Invalid role"}), 400
    if not name or not email or len(password) < 4:
        return jsonify({"success": False, "error": "Συμπλήρωσε όνομα, email και κωδικό (4+ χαρακτήρες)"}), 400

    db = get_db()
    existing = db.execute("SELECT id FROM users WHERE LOWER(email) = ?", (email,)).fetchone()
    if existing:
        return jsonify({"success": False, "error": "Υπάρχει ήδη account με αυτό το email"}), 409

    user_id = "u_" + uuid.uuid4().hex[:8]
    customer_id = None
    venue_id = None
    venue_name = None

    if role == "customer":
        customer_id = "c" + uuid.uuid4().hex[:8]
        initials = "".join([p[0] for p in name.split()[:2]]).upper() or "NF"
        db.execute("""
            INSERT INTO customers (id, name, initials, email, phone, tier, points, customer_since)
            VALUES (?, ?, ?, ?, ?, 'silver', 0, ?)
        """, (customer_id, name, initials, email, data.get("phone", ""), date.today().isoformat()))
    else:
        venue_id = "v1"
        venue_name = data.get("venue_name") or "Το μαγαζί μου"

    db.execute("""
        INSERT INTO users (id, name, email, password_hash, role, venue_id, venue_name, customer_id, points, tier)
        VALUES (?, ?, ?, ?, ?, ?, ?, ?, 0, 'silver')
    """, (user_id, name, email, hash_password(password), role, venue_id, venue_name, customer_id))
    db.commit()

    user = db.execute("SELECT * FROM users WHERE id = ?", (user_id,)).fetchone()
    user_dict = dict_from_row(user)

    access_token = create_jwt({"sub": user_id, "role": role, "email": email})
    refresh_token = create_refresh_token(user_id)

    return jsonify({
        "success": True,
        "token": access_token,
        "refresh_token": refresh_token,
        "user": public_user(user_dict)
    }), 201

@app.route("/api/auth/refresh", methods=["POST"])
def refresh():
    data = request.get_json() or {}
    refresh_token = data.get("refresh_token")

    if not refresh_token:
        return jsonify({"success": False, "error": "Refresh token required"}), 400

    user_id = verify_refresh_token(refresh_token)
    if not user_id:
        return jsonify({"success": False, "error": "Invalid or expired refresh token"}), 401

    db = get_db()
    user = db.execute("SELECT * FROM users WHERE id = ?", (user_id,)).fetchone()
    if not user:
        return jsonify({"success": False, "error": "User not found"}), 404

    access_token = create_jwt({"sub": user['id'], "role": user['role'], "email": user['email']})

    return jsonify({
        "success": True,
        "token": access_token,
        "expires_in": 86400
    })

@app.route("/api/auth/me")
def me():
    user = current_user()
    if not user:
        return jsonify({"success": True, "user": None})
    return jsonify({"success": True, "user": public_user(user)})

@app.route("/api/auth/logout", methods=["POST"])
def logout():
    data = request.get_json() or {}
    refresh_token = data.get("refresh_token")
    if refresh_token:
        token_hash = hashlib.sha256(refresh_token.encode()).hexdigest()
        db = get_db()
        db.execute("DELETE FROM refresh_tokens WHERE token_hash = ?", (token_hash,))
        db.commit()
    return jsonify({"success": True})

# ════════════════════════════════════════════════════════════
#  ROUTES - Public
# ════════════════════════════════════════════════════════════

@app.route("/api/tonight-stats")
def tonight_stats():
    db = get_db()
    rows = db.execute("SELECT * FROM venues").fetchall()

    total_guests = 0
    open_count = 0
    party_count = 0

    for row in rows:
        venue = dict_from_row(row)
        status_info = is_open_tonight(venue)
        guests = get_simulated_crowd(venue)
        total_guests += guests

        if status_info['status'] in ['open_tonight', 'party_tonight', 'party_night', 'open']:
            open_count += 1
        if status_info['status'] in ['open_tonight', 'party_tonight', 'party_night']:
            party_count += 1

    return jsonify({
        "success": True,
        "data": {
            "total_guests_tonight": total_guests,
            "open_venues": open_count,
            "venues_with_events": party_count,
            "trending_events": party_count,
            "avg_satisfaction": 94
        }
    })

@app.route("/api/events")
def get_events():
    trending = request.args.get("trending")
    student = request.args.get("student")
    tourist = request.args.get("tourist")
    tonight_only = request.args.get("tonight") == "true"

    query = """
        SELECT e.*, v.name as venue_name, v.capacity as venue_capacity,
               v.current_guests as venue_current, v.image_class, v.image_emoji,
               v.category, v.open_days, v.type as venue_type, v.address as venue_address,
               v.phone as venue_phone, v.rating as venue_rating, v.rating_count as venue_rating_count,
               v.music_genres as venue_music, v.description as venue_description
        FROM events e
        LEFT JOIN venues v ON e.venue_id = v.id
        WHERE 1=1
    """
    params = []

    if trending == "true":
        query += " AND e.trending = 1"
    if student == "true":
        query += " AND e.student_night = 1"
    if tourist == "true":
        query += " AND e.tourist_friendly = 1"

    db = get_db()
    rows = db.execute(query, params).fetchall()
    events = []
    for row in rows:
        event = dict_from_row(row)
        if event.get('badges'):
            event['badges'] = json.loads(event['badges'])

        # Build venue dict for status check
        venue_data = {
            'id': event.get('venue_id'),
            'name': event.get('venue_name'),
            'category': event.get('category'),
            'open_days': event.get('open_days'),
            'capacity': event.get('venue_capacity', 100)
        }

        # Add venue opening status
        status_info = is_open_tonight(venue_data)
        event['venue_status'] = status_info['status']
        event['venue_status_label'] = status_info['status_label']
        event['venue_badge'] = status_info['badge']
        event['venue_is_open'] = status_info['is_open']

        # Update crowd simulation
        event['venue_current'] = get_simulated_crowd(venue_data)
        event['crowd_pct'] = round(event['venue_current'] / event['venue_capacity'] * 100) if event['venue_capacity'] else 0

        # Filter for tonight only if requested
        if tonight_only and not status_info['is_open']:
            continue

        events.append(event)

    return jsonify({"success": True, "data": events})

@app.route("/api/events/<event_id>")
def get_event(event_id):
    db = get_db()
    row = db.execute("""
        SELECT e.*, v.name as venue_name, v.capacity as venue_capacity,
               v.current_guests as venue_current, v.image_class, v.image_emoji
        FROM events e
        LEFT JOIN venues v ON e.venue_id = v.id
        WHERE e.id = ?
    """, (event_id,)).fetchone()

    if not row:
        return jsonify({"success": False, "error": "Not found"}), 404

    event = dict_from_row(row)
    if event.get('badges'):
        event['badges'] = json.loads(event['badges'])

    return jsonify({"success": True, "data": event})

@app.route("/api/venues")
def get_venues():
    db = get_db()
    rows = db.execute("SELECT * FROM venues").fetchall()
    venues = []
    for row in rows:
        venue = dict_from_row(row)
        # Add opening status
        status_info = is_open_tonight(venue)
        venue.update(status_info)
        # Add simulated crowd
        venue['current_guests'] = get_simulated_crowd(venue)
        venue['crowd_pct'] = round(venue['current_guests'] / venue['capacity'] * 100) if venue['capacity'] else 0
        venues.append(venue)
    return jsonify({"success": True, "data": venues})

@app.route("/api/venues/<venue_id>")
def get_venue(venue_id):
    conn = get_db()
    row = conn.execute("SELECT * FROM venues WHERE id = ?", (venue_id,)).fetchone()
    if not row:
        return jsonify({"success": False, "error": "Not found"}), 404
    venue = dict_from_row(row)
    status_info = is_open_tonight(venue)
    venue.update(status_info)
    venue['current_guests'] = get_simulated_crowd(venue)
    venue['crowd_pct'] = round(venue['current_guests'] / venue['capacity'] * 100) if venue['capacity'] else 0
    return jsonify({"success": True, "data": venue})

@app.route("/api/venues/<venue_id>/events")
def get_venue_events(venue_id):
    """Get all events at a specific venue"""
    conn = get_db()
    # Verify venue exists
    venue_row = conn.execute("SELECT * FROM venues WHERE id = ?", (venue_id,)).fetchone()
    if not venue_row:
        return jsonify({"success": False, "error": "Venue not found"}), 404

    venue = dict_from_row(venue_row)

    rows = conn.execute("""
        SELECT e.*, v.name as venue_name, v.capacity as venue_capacity,
               v.current_guests as venue_current, v.image_class, v.image_emoji,
               v.category, v.open_days, v.type as venue_type, v.address as venue_address,
               v.phone as venue_phone, v.rating as venue_rating
        FROM events e
        LEFT JOIN venues v ON e.venue_id = v.id
        WHERE e.venue_id = ?
        ORDER BY e.date ASC, e.start_time ASC
    """, (venue_id,)).fetchall()

    events = []
    for row in rows:
        event = dict_from_row(row)
        if event.get('badges'):
            try:
                event['badges'] = json.loads(event['badges'])
            except:
                pass
        # Add venue status info
        status_info = is_open_tonight(venue)
        event['venue_status'] = status_info['status']
        event['venue_status_label'] = status_info['status_label']
        event['venue_badge'] = status_info['badge']
        event['venue_is_open'] = status_info['is_open']
        events.append(event)

    return jsonify({"success": True, "data": events})

@app.route("/api/venues/tonight")
def get_venues_tonight():
    """Get only venues that are open/have events tonight"""
    db = get_db()
    rows = db.execute("SELECT * FROM venues").fetchall()
    venues = []
    for row in rows:
        venue = dict_from_row(row)
        status_info = is_open_tonight(venue)
        venue.update(status_info)
        venue['current_guests'] = get_simulated_crowd(venue)
        venue['crowd_pct'] = round(venue['current_guests'] / venue['capacity'] * 100) if venue['capacity'] else 0
        # Only include if open tonight or has party
        if status_info['status'] in ['open_tonight', 'party_tonight', 'party_night']:
            venues.append(venue)
    return jsonify({"success": True, "data": venues})

@app.route("/api/activity-feed")
def activity_feed():
    conn = get_db()
    rows = conn.execute("SELECT * FROM activity_feed ORDER BY created_at DESC LIMIT 20").fetchall()
    return jsonify({"success": True, "data": [dict_from_row(r) for r in rows]})

# ════════════════════════════════════════════════════════════
#  ROUTES - Search
# ════════════════════════════════════════════════════════════

@app.route("/api/search")
def search():
    """Search venues and events by query string"""
    q = request.args.get("q", "").strip().lower()
    if not q:
        return jsonify({"success": True, "data": {"venues": [], "events": []}})

    conn = get_db()

    # Search venues
    venue_rows = conn.execute("""
        SELECT * FROM venues
        WHERE LOWER(name) LIKE ? OR LOWER(type) LIKE ? OR LOWER(category) LIKE ?
           OR LOWER(music_genres) LIKE ? OR LOWER(description) LIKE ? OR LOWER(address) LIKE ?
        LIMIT 20
    """, (f"%{q}%", f"%{q}%", f"%{q}%", f"%{q}%", f"%{q}%", f"%{q}%")).fetchall()

    venues = []
    for row in venue_rows:
        venue = dict_from_row(row)
        status_info = is_open_tonight(venue)
        venue.update(status_info)
        venue['current_guests'] = get_simulated_crowd(venue)
        venue['crowd_pct'] = round(venue['current_guests'] / venue['capacity'] * 100) if venue['capacity'] else 0
        venues.append(venue)

    # Search events
    event_rows = conn.execute("""
        SELECT e.*, v.name as venue_name, v.capacity as venue_capacity,
               v.current_guests as venue_current, v.image_class, v.image_emoji,
               v.category, v.open_days
        FROM events e
        LEFT JOIN venues v ON e.venue_id = v.id
        WHERE LOWER(e.title) LIKE ? OR LOWER(e.genre) LIKE ? OR LOWER(e.dj) LIKE ?
           OR LOWER(e.description) LIKE ? OR LOWER(v.name) LIKE ?
        LIMIT 20
    """, (f"%{q}%", f"%{q}%", f"%{q}%", f"%{q}%", f"%{q}%")).fetchall()

    events = []
    for row in event_rows:
        event = dict_from_row(row)
        if event.get('badges'):
            try:
                event['badges'] = json.loads(event['badges'])
            except:
                pass
        events.append(event)

    return jsonify({
        "success": True,
        "data": {
            "venues": venues,
            "events": events,
            "total": len(venues) + len(events)
        }
    })

# ════════════════════════════════════════════════════════════
#  ROUTES - User Reservations
# ════════════════════════════════════════════════════════════

@app.route("/api/user/reservations")
@require_auth()
def get_user_reservations():
    """Get current user's reservations"""
    user = request.user
    customer_id = user.get('customer_id')

    conn = get_db()
    query = """
        SELECT r.*, v.name as venue_name, v.photo_url as venue_photo, v.address as venue_address,
               e.title as event_title, e.date as event_date, e.start_time as event_start_time
        FROM reservations r
        LEFT JOIN venues v ON r.venue_id = v.id
        LEFT JOIN events e ON r.event_id = e.id
        WHERE r.customer_id = ?
        ORDER BY r.created_at DESC
    """
    rows = conn.execute(query, (customer_id,)).fetchall()
    return jsonify({"success": True, "data": [dict_from_row(r) for r in rows]})

# ════════════════════════════════════════════════════════════
#  ROUTES - Favorites
# ════════════════════════════════════════════════════════════

@app.route("/api/favorites")
@require_auth()
def get_favorites():
    """Get user's favorite venues"""
    user = request.user
    conn = get_db()
    rows = conn.execute("""
        SELECT f.*, v.name as venue_name, v.type as venue_type, v.photo_url, v.category,
               v.address, v.rating, v.capacity, v.open_days
        FROM favorites f
        JOIN venues v ON f.venue_id = v.id
        WHERE f.user_id = ?
        ORDER BY f.created_at DESC
    """, (user['id'],)).fetchall()

    favorites = []
    for row in rows:
        fav = dict_from_row(row)
        # Add venue status
        venue_data = {
            'id': fav.get('venue_id'),
            'name': fav.get('venue_name'),
            'category': fav.get('category'),
            'open_days': fav.get('open_days'),
            'capacity': fav.get('capacity', 100)
        }
        status_info = is_open_tonight(venue_data)
        fav['venue_status'] = status_info['status']
        fav['venue_badge'] = status_info['badge']
        favorites.append(fav)

    return jsonify({"success": True, "data": favorites})

@app.route("/api/favorites", methods=["POST"])
@require_auth()
def add_favorite():
    """Add venue to favorites"""
    user = request.user
    data = request.get_json() or {}
    venue_id = data.get("venue_id")

    if not venue_id:
        return jsonify({"success": False, "error": "venue_id is required"}), 400

    conn = get_db()

    # Check if venue exists
    venue = conn.execute("SELECT id FROM venues WHERE id = ?", (venue_id,)).fetchone()
    if not venue:
        return jsonify({"success": False, "error": "Venue not found"}), 404

    # Check if already favorited
    existing = conn.execute(
        "SELECT id FROM favorites WHERE user_id = ? AND venue_id = ?",
        (user['id'], venue_id)
    ).fetchone()
    if existing:
        return jsonify({"success": False, "error": "Venue already in favorites"}), 409

    fav_id = "fav_" + uuid.uuid4().hex[:8]
    conn.execute("""
        INSERT INTO favorites (id, user_id, venue_id, created_at)
        VALUES (?, ?, ?, ?)
    """, (fav_id, user['id'], venue_id, datetime.utcnow().isoformat()))
    conn.commit()

    return jsonify({
        "success": True,
        "data": {"id": fav_id, "user_id": user['id'], "venue_id": venue_id}
    }), 201

@app.route("/api/favorites/<fav_id>", methods=["DELETE"])
@require_auth()
def remove_favorite(fav_id):
    """Remove venue from favorites"""
    user = request.user
    conn = get_db()

    # Check if favorite exists and belongs to user
    existing = conn.execute(
        "SELECT * FROM favorites WHERE id = ? AND user_id = ?",
        (fav_id, user['id'])
    ).fetchone()

    if not existing:
        return jsonify({"success": False, "error": "Favorite not found"}), 404

    conn.execute("DELETE FROM favorites WHERE id = ?", (fav_id,))
    conn.commit()

    return jsonify({"success": True, "message": "Favorite removed"})

# ════════════════════════════════════════════════════════════
#  ROUTES - Reservations
# ════════════════════════════════════════════════════════════

@app.route("/api/reservations")
@require_auth("club")
def get_reservations():
    venue_id = request.args.get("venue_id")
    status = request.args.get("status")

    query = "SELECT * FROM reservations WHERE 1=1"
    params = []

    if venue_id:
        query += " AND venue_id = ?"
        params.append(venue_id)
    if status:
        query += " AND status = ?"
        params.append(status)

    query += " ORDER BY created_at DESC"

    db = get_db()
    rows = db.execute(query, params).fetchall()
    return jsonify({"success": True, "data": [dict_from_row(r) for r in rows]})

@app.route("/api/reservations", methods=["POST"])
@require_auth()
def create_reservation():
    data = request.get_json() or {}
    res_id = "r" + uuid.uuid4().hex[:8]

    db = get_db()
    db.execute("""
        INSERT INTO reservations
        (id, customer_id, customer_name, customer_initials, venue_id, event_id,
         table_number, table_type, guests, arrival_time, min_spend, status, notes)
        VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, 'pending', ?)
    """, (
        res_id,
        data.get("customer_id"),
        data.get("customer_name", "Guest"),
        (data.get("customer_name", "G")[:2]).upper(),
        data.get("venue_id", "v1"),
        data.get("event_id", "e1"),
        data.get("table", "T-NEW"),
        data.get("table_type", "standard"),
        data.get("guests", 2),
        data.get("arrival_time", "23:00"),
        data.get("min_spend", 0),
        data.get("notes", "")
    ))
    db.commit()

    row = db.execute("SELECT * FROM reservations WHERE id = ?", (res_id,)).fetchone()
    return jsonify({"success": True, "data": dict_from_row(row)}), 201

@app.route("/api/reservations/<res_id>", methods=["PATCH"])
@require_auth("club")
def update_reservation(res_id):
    db = get_db()
    row = db.execute("SELECT * FROM reservations WHERE id = ?", (res_id,)).fetchone()
    if not row:
        return jsonify({"success": False, "error": "Not found"}), 404

    data = request.get_json() or {}
    allowed = ['status', 'notes', 'deposit_paid', 'table_number', 'table_type', 'guests', 'arrival_time']
    updates = []
    params = []

    for key in allowed:
        if key in data:
            updates.append(f"{key} = ?")
            params.append(data[key])

    if updates:
        params.append(res_id)
        db.execute(f"UPDATE reservations SET {', '.join(updates)} WHERE id = ?", params)
        db.commit()

    row = db.execute("SELECT * FROM reservations WHERE id = ?", (res_id,)).fetchone()
    return jsonify({"success": True, "data": dict_from_row(row)})

@app.route("/api/reservations/<res_id>/checkin", methods=["POST"])
@require_auth("club")
def checkin_reservation(res_id):
    db = get_db()
    row = db.execute("SELECT * FROM reservations WHERE id = ?", (res_id,)).fetchone()
    if not row:
        return jsonify({"success": False, "error": "Not found"}), 404

    checkin_time = datetime.now().strftime("%H:%M")
    db.execute("""
        UPDATE reservations SET checked_in = 1, status = 'confirmed', checkin_time = ?
        WHERE id = ?
    """, (checkin_time, res_id))
    db.commit()

    row = db.execute("SELECT * FROM reservations WHERE id = ?", (res_id,)).fetchone()
    return jsonify({"success": True, "data": dict_from_row(row)})

# ════════════════════════════════════════════════════════════
#  ROUTES - Customers
# ════════════════════════════════════════════════════════════

@app.route("/api/customers")
@require_auth("club")
def get_customers():
    tier = request.args.get("tier")

    query = "SELECT * FROM customers"
    params = []

    if tier:
        query += " WHERE tier = ?"
        params.append(tier)

    query += " ORDER BY points DESC"

    db = get_db()
    rows = db.execute(query, params).fetchall()
    return jsonify({"success": True, "data": [dict_from_row(r) for r in rows]})

@app.route("/api/customers/<cid>")
@require_auth("club")
def get_customer(cid):
    db = get_db()
    row = db.execute("SELECT * FROM customers WHERE id = ?", (cid,)).fetchone()
    if not row:
        return jsonify({"success": False, "error": "Not found"}), 404
    return jsonify({"success": True, "data": dict_from_row(row)})

@app.route("/api/customers", methods=["POST"])
@require_auth("club")
def create_customer():
    data = request.get_json() or {}
    cid = "c" + uuid.uuid4().hex[:8]
    name = data.get("name", "New Customer")
    initials = "".join([p[0] for p in name.split()[:2]]).upper() or "NC"

    db = get_db()
    db.execute("""
        INSERT INTO customers
        (id, name, initials, email, phone, birthday, tier, points, fav_genre, customer_since, notes)
        VALUES (?, ?, ?, ?, ?, ?, 'silver', 0, ?, ?, ?)
    """, (
        cid, name, initials,
        data.get("email", ""),
        data.get("phone", ""),
        data.get("birthday", ""),
        data.get("fav_genre", ""),
        date.today().isoformat(),
        data.get("notes", "")
    ))
    db.commit()

    row = db.execute("SELECT * FROM customers WHERE id = ?", (cid,)).fetchone()
    return jsonify({"success": True, "data": dict_from_row(row)}), 201

# ════════════════════════════════════════════════════════════
#  ROUTES - Promoters
# ════════════════════════════════════════════════════════════

@app.route("/api/promoters")
@require_auth("club")
def get_promoters():
    db = get_db()
    rows = db.execute("SELECT * FROM promoters ORDER BY revenue_generated DESC").fetchall()
    return jsonify({"success": True, "data": [dict_from_row(r) for r in rows]})

@app.route("/api/promoters", methods=["POST"])
@require_auth("club")
def create_promoter():
    data = request.get_json() or {}
    pid = "p" + uuid.uuid4().hex[:8]
    name = data.get("name", "New Promoter")
    initials = name[:2].upper()

    db = get_db()
    db.execute("""
        INSERT INTO promoters (id, name, initials, guests_brought, revenue_generated, commission, status)
        VALUES (?, ?, ?, 0, 0, 0, 'active')
    """, (pid, name, initials))
    db.commit()

    row = db.execute("SELECT * FROM promoters WHERE id = ?", (pid,)).fetchone()
    return jsonify({"success": True, "data": dict_from_row(row)}), 201

# ════════════════════════════════════════════════════════════
#  ROUTES - Analytics
# ════════════════════════════════════════════════════════════

@app.route("/api/analytics")
@require_auth("club")
def get_analytics():
    return jsonify({
        "success": True,
        "data": {
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
    })

@app.route("/api/analytics/overview")
@require_auth("club")
def get_overview():
    db = get_db()

    checked_in = db.execute("SELECT COUNT(*) as c FROM reservations WHERE checked_in = 1").fetchone()['c']
    confirmed = db.execute("SELECT COUNT(*) as c FROM reservations WHERE status = 'confirmed'").fetchone()['c']
    pending = db.execute("SELECT COUNT(*) as c FROM reservations WHERE status = 'pending'").fetchone()['c']
    total = db.execute("SELECT COUNT(*) as c FROM reservations").fetchone()['c']

    venue = db.execute("SELECT capacity, current_guests FROM venues WHERE id = 'v1'").fetchone()
    cap = venue['capacity'] if venue else 210
    curr = venue['current_guests'] if venue else 0
    occ = round(curr / cap * 100) if cap else 0

    return jsonify({
        "success": True,
        "data": {
            "reservations_tonight": total,
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
        }
    })

# ════════════════════════════════════════════════════════════
#  ROUTES - Marketing & Guest List
# ════════════════════════════════════════════════════════════

@app.route("/api/marketing/send", methods=["POST"])
@require_auth("club")
def send_campaign():
    data = request.get_json() or {}
    campaign_type = data.get("type", "general")
    return jsonify({
        "success": True,
        "data": {
            "campaign_type": campaign_type,
            "sent_to": data.get("count", 0),
            "message": f"Campaign '{campaign_type}' queued successfully",
            "estimated_open_rate": "68%",
        }
    })

@app.route("/api/guestlist/join", methods=["POST"])
@require_auth()
def join_guest_list():
    data = request.get_json() or {}
    return jsonify({
        "success": True,
        "data": {
            "reference": "NF-" + uuid.uuid4().hex[:6].upper(),
            "message": f"You're on the list for {data.get('event_title', 'tonight')}!",
            "guest_list_position": 284,
        }
    })

# ════════════════════════════════════════════════════════════
#  STATIC FILE SERVING (for production deployment)
# ════════════════════════════════════════════════════════════

@app.route('/')
def serve_index():
    return send_from_directory(FRONTEND_DIR, 'index.html')

@app.route('/<path:path>')
def serve_static(path):
    # Serve static files (html, css, js, images)
    if os.path.exists(os.path.join(FRONTEND_DIR, path)):
        return send_from_directory(FRONTEND_DIR, path)
    # For SPA-style routing, fall back to index.html
    return send_from_directory(FRONTEND_DIR, 'index.html')

# ════════════════════════════════════════════════════════════
#  INIT
# ════════════════════════════════════════════════════════════

init_db()
seed_db()

if __name__ == "__main__":
    app.run(debug=True, port=5000, host="0.0.0.0")
