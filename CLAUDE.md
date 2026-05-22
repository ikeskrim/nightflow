# NightFlow - Project Configuration

> **NightFlow** — A nightclub event discovery and booking platform
> Stack: Flask backend + Vanilla HTML/CSS/JS frontend
> Aesthetic: Dark nightclub theme with neon accents

## Tech Stack

### Backend (Flask)
- **Framework**: Flask with Blueprints for modular routes
- **Data**: JSON file storage (`users.json`, `events.json`)
- **Auth**: Session-based authentication
- **API**: RESTful JSON endpoints at `/api/*`
- **CORS**: Enabled for frontend communication

### Frontend (Vanilla)
- **HTML**: Semantic HTML5, no templating libraries
- **CSS**: Custom CSS with CSS variables for theming
- **JS**: Vanilla ES6+, no frameworks (no React, Vue, etc.)
- **Fetch API**: For all backend communication

## Dark Nightclub Aesthetic

### Color Palette (from main.css :root)
```css
--bg:    #08060F;             /* Deep purple-black */
--bg2:   #0E0B1A;             /* Secondary background */
--bg3:   #130F22;             /* Tertiary background */
--card:  rgba(255,255,255,0.05);  /* Glass cards */
--neon:  #7C3AFF;             /* Primary purple neon */
--neon2: #9B5FFF;             /* Light purple */
--cyan:  #00D4FF;             /* Electric cyan */
--pink:  #FF2D8A;             /* Hot pink accent */
--gold:  #FFB800;             /* VIP gold */
--green: #00E5A0;             /* Success/live indicator */
--text:  #f0ecff;             /* Primary text */
--text2: #a89fd4;             /* Muted text */
```

### Design Patterns
- **Glassmorphism**: Semi-transparent cards with backdrop blur
- **Neon glow**: Box shadows with accent colors on hover
- **Gradients**: Linear gradients using accent colors
- **Animations**: Subtle pulse/glow effects, smooth transitions
- **Typography**: Modern sans-serif (Inter, Poppins, or system)

### UI Components
- Dark cards with subtle borders (`1px solid rgba(255,255,255,0.1)`)
- Rounded corners (`border-radius: 12px` to `20px`)
- Hover states with neon glow effects
- Buttons with gradient backgrounds
- Form inputs with dark backgrounds and accent focus rings

## File Organization

```
/
├── backend/
│   ├── app.py           # Flask app entry point
│   ├── routes/          # API route blueprints
│   └── *.json           # Data storage files
├── frontend/
│   ├── index.html       # Landing page
│   ├── css/
│   │   └── main.css     # Global styles + theme variables
│   └── js/
│       ├── api.js       # Backend API communication
│       └── app.js       # UI logic and interactions
├── *.html               # Page templates (root level)
├── app.py               # Alternative Flask entry
└── start.py             # Dev server launcher
```

## Coding Standards

### Python (Flask)
- Use type hints for function signatures
- Docstrings for route handlers
- Return JSON responses with consistent structure: `{"success": bool, "data": ..., "error": ...}`
- Handle exceptions with try/except, return 500 on errors
- Use `@app.route` decorators, prefer POST for mutations

### JavaScript
- Use `const` by default, `let` only when reassignment needed
- Arrow functions for callbacks
- Async/await for API calls (no `.then()` chains)
- DOM queries: `document.querySelector` / `querySelectorAll`
- Event delegation where possible
- No jQuery or external libraries

### CSS
- Mobile-first responsive design
- CSS variables for all colors and spacing
- BEM-like naming: `.card`, `.card__title`, `.card--featured`
- Flexbox and Grid for layouts
- Transitions: `transition: all 0.3s ease`

### HTML
- Semantic elements: `<header>`, `<main>`, `<section>`, `<article>`
- Accessibility: proper `aria-*` attributes, `alt` text
- Forms with proper `<label>` associations
- Data attributes for JS hooks: `data-*`

## Behavioral Rules

- NEVER add external CSS/JS frameworks (Bootstrap, Tailwind, React, etc.)
- ALWAYS maintain the dark nightclub aesthetic
- NEVER use light/white backgrounds for main UI elements
- ALWAYS use CSS variables for colors (never hardcode hex values inline)
- PREFER editing existing files over creating new ones
- NEVER create README files unless explicitly requested
- ALWAYS test Flask routes work before marking complete
- KEEP JavaScript vanilla — no npm packages for frontend

## API Conventions

### Endpoints
- `GET /api/events` — List events
- `GET /api/events/<id>` — Get single event
- `POST /api/events` — Create event
- `POST /api/auth/login` — User login
- `POST /api/auth/register` — User registration
- `GET /api/user/profile` — Current user profile

### Response Format
```json
{
  "success": true,
  "data": { ... },
  "message": "Optional status message"
}
```

### Error Format
```json
{
  "success": false,
  "error": "Error description",
  "code": "ERROR_CODE"
}
```

## Quick Commands

```bash
# Start development server
python start.py

# Or directly with Flask
cd backend && python app.py

# Run from project root
python -m flask run --debug
```
