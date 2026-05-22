# 🌙 NightFlow — Nightlife Operating System

> Full-stack nightlife discovery & CRM platform for Rethymno, Crete

---

## 🏗 Architecture

```
nightflow/
├── backend/
│   └── app.py          ← Flask REST API (Python)
├── frontend/
│   ├── index.html      ← Main SPA
│   ├── css/
│   │   └── main.css    ← Full stylesheet (dark luxury theme)
│   └── js/
│       ├── api.js      ← API client module
│       └── app.js      ← Frontend logic & rendering
└── start.py            ← Dev launcher (runs both servers)
```

---

## 🚀 Quick Start

### Requirements
- Python 3.10+
- Flask (`pip install flask`)

### Run

```bash
cd nightflow
python3 start.py
```

Opens automatically at **http://localhost:3000**

---

## 🔌 REST API Endpoints

### Public
| Method | Endpoint | Description |
|--------|----------|-------------|
| GET | `/api/tonight-stats` | Live stats (venues, guests) |
| GET | `/api/events` | All tonight's events |
| GET | `/api/events?trending=true` | Trending events only |
| GET | `/api/events?tourist=true` | Tourist-friendly events |
| GET | `/api/events/<id>` | Single event detail |
| GET | `/api/venues` | All venues |
| GET | `/api/activity-feed` | FOMO social feed |

### CRM
| Method | Endpoint | Description |
|--------|----------|-------------|
| GET | `/api/reservations` | All reservations |
| GET | `/api/reservations?venue_id=v1` | Filter by venue |
| POST | `/api/reservations` | Create reservation |
| PATCH | `/api/reservations/<id>` | Update status |
| POST | `/api/reservations/<id>/checkin` | Check in guest |
| GET | `/api/customers` | All customers |
| GET | `/api/customers?tier=gold` | Filter by tier |
| POST | `/api/customers` | Add customer |
| GET | `/api/promoters` | All promoters |
| POST | `/api/promoters` | Add promoter |
| GET | `/api/analytics` | Charts data |
| GET | `/api/analytics/overview` | Tonight's KPIs |
| POST | `/api/marketing/send` | Send campaign |
| POST | `/api/guestlist/join` | Join guest list |

---

## 🎨 Features

### Public App (Discover)
- 🌙 Hero with animated counters & live badge
- 🎆 Tonight's Events — 6 venue cards with filters
- 🗺️ Live Crowd Heatmap — interactive venue pins
- ⭐ Loyalty System — Silver / Gold / Black tiers
- 🔥 FOMO Activity Feed — friends' check-ins
- ✈️ Tourist Mode — verified venues & easy booking
- 🔍 Real-time search & filter by genre/type

### Club CRM Dashboard
- 📊 Overview — 6 live KPI cards + 4 Chart.js charts
- 📋 Reservations — floor plan map + reservation list with approve/reject/checkin
- 👥 Customers — CRM cards filterable by tier
- 📣 Promoters — commission tracking table
- 📈 Analytics — 4 deep-dive charts
- 📨 Marketing — 6 campaign tools
- 🚪 Staff Interface — check-in queue + occupancy zones

---

## 🛠 Tech Stack

| Layer | Technology |
|-------|-----------|
| Backend | Python 3 + Flask |
| Frontend | Vanilla JS (ES2022) |
| Styling | CSS Variables + Custom Design System |
| Charts | Chart.js 4 |
| Fonts | Syne (headings) + DM Sans (body) |
| Data | In-memory (upgradeable to SQLite/PostgreSQL) |

---

## 📦 Production Upgrade Path

1. **Database**: Replace in-memory lists with SQLAlchemy + PostgreSQL
2. **Auth**: Add JWT authentication (Flask-JWT-Extended)
3. **Payments**: Integrate Stripe for deposits & VIP reservations
4. **Real-time**: Add WebSockets for live occupancy updates
5. **Deploy**: Gunicorn + Nginx + Docker

---

*NightFlow — Built for the nights of Rethymno* 🌊
