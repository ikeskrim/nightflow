/**
 * NightFlow — Main App
 * All UI logic, data rendering, and API integration
 */

/* ═══════════════════════════════════════════════════════════
   STATE
═══════════════════════════════════════════════════════════ */
let state = {
  events: [],
  reservations: [],
  customers: [],
  promoters: [],
  analytics: null,
  overview: null,
  currentFilter: 'all',
  currentCRM: 'overview',
  chartsInited: false,
  analyticsInited: false,
  activeReserveEventId: null,
  authUser: JSON.parse(localStorage.getItem('nightflow_user') || 'null'),
  authMode: 'login',
};

/* ═══════════════════════════════════════════════════════════
   INIT
═══════════════════════════════════════════════════════════ */
document.addEventListener('DOMContentLoaded', async () => {
  setupNav();
  setupAuth();
  renderAuthState();
  setupHeatmap();
  setupFloorPlan();
  spawnParticles();

  // Handle ?page= URL param (e.g. after login redirect)
  const urlPage = new URLSearchParams(location.search).get('page');
  if (urlPage === 'dashboard' && state.authUser?.role === 'club') {
    // show dashboard directly
    document.querySelectorAll('.page').forEach(p => p.classList.remove('active'));
    document.getElementById('page-dashboard')?.classList.add('active');
    document.querySelectorAll('.nav-tab').forEach(t => t.classList.remove('active'));
    document.querySelector('.nav-tab[data-page="dashboard"]')?.classList.add('active');
    await loadDashboard();
    return;
  }

  await loadDiscoverPage();
});

/* ═══════════════════════════════════════════════════════════
   NAVIGATION
═══════════════════════════════════════════════════════════ */
function setupNav() {
  // Tab switching
  document.querySelectorAll('.nav-tab, .mobile-tab').forEach(btn => {
    btn.addEventListener('click', () => {
      const page = btn.dataset.page;
      if (page) switchPage(page);
    });
  });

  // Sidebar nav
  document.querySelectorAll('.sidebar-btn[data-crm]').forEach(btn => {
    btn.addEventListener('click', () => {
      switchCRM(btn.dataset.crm, btn);
    });
  });

  // Filter chips
  document.querySelectorAll('.chip').forEach(chip => {
    chip.addEventListener('click', () => {
      document.querySelectorAll('.chip').forEach(c => c.classList.remove('active'));
      chip.classList.add('active');
      state.currentFilter = chip.dataset.filter;
      renderEvents();
    });
  });

  // Search
  const searchInput = document.getElementById('search-input');
  if (searchInput) {
    searchInput.addEventListener('input', debounce(() => renderEvents(), 300));
  }

  // Customer filter tabs
  document.querySelectorAll('.crm-filter-tabs .crm-tab').forEach(tab => {
    tab.addEventListener('click', async () => {
      document.querySelectorAll('.crm-filter-tabs .crm-tab').forEach(t => t.classList.remove('active'));
      tab.classList.add('active');
      await loadCustomers(tab.dataset.filter === 'all' ? '' : tab.dataset.filter);
    });
  });

  // Avatar → relevant area
  document.getElementById('nav-avatar')?.addEventListener('click', () => {
    if (!state.authUser) return window.location.href='auth.html';
    if (state.authUser.role === 'club') switchPage('dashboard');
    else switchPage('discover');
  });

  // Burger menu
  document.getElementById('nav-burger')?.addEventListener('click', () => {
    const mm = document.getElementById('mobile-menu');
    mm.classList.toggle('open');
  });

  // Close mobile menu on outside click
  document.addEventListener('click', e => {
    const mm = document.getElementById('mobile-menu');
    const burger = document.getElementById('nav-burger');
    if (mm.classList.contains('open') && !mm.contains(e.target) && !burger.contains(e.target)) {
      mm.classList.remove('open');
    }
  });
}

function switchPage(page) {
  if (page === 'dashboard' && (!state.authUser || state.authUser.role !== 'club')) {
    showToast('🔐 Το CRM ανοίγει μόνο με club / owner account.', 'Χρειάζεται σύνδεση');
    window.location.href='auth.html';
    return;
  }
  document.querySelectorAll('.page').forEach(p => p.classList.remove('active'));
  document.getElementById(`page-${page}`)?.classList.add('active');
  document.querySelectorAll('.nav-tab').forEach(t => t.classList.remove('active'));
  document.querySelectorAll(`.nav-tab[data-page="${page}"]`).forEach(t => t.classList.add('active'));
  document.getElementById('mobile-menu')?.classList.remove('open');

  if (page === 'dashboard') loadDashboard();
  if (page === 'discover') loadDiscoverPage();
  window.scrollTo(0, 0);
}

function switchCRM(section, clickedBtn) {
  document.querySelectorAll('.crm-section').forEach(s => s.classList.remove('active-crm'));
  document.getElementById(`crm-${section}`)?.classList.add('active-crm');
  document.querySelectorAll('.sidebar-btn').forEach(b => b.classList.remove('active-side'));
  clickedBtn?.classList.add('active-side');
  state.currentCRM = section;

  if (section === 'overview') loadOverview();
  if (section === 'reservations') loadReservations();
  if (section === 'customers') loadCustomers();
  if (section === 'promoters') loadPromoters();
  if (section === 'analytics') loadAnalytics();
  if (section === 'staff') loadStaff();
  if (section === 'marketing') {} // static
}

/* ═══════════════════════════════════════════════════════════
   DISCOVER PAGE
═══════════════════════════════════════════════════════════ */
async function loadDiscoverPage() {
  await Promise.all([
    loadHeroStats(),
    loadEvents(),
    loadActivityFeed(),
  ]);
}

async function loadHeroStats() {
  const stats = await api.getTonightStats();
  if (!stats) return;

  document.getElementById('open-venues-nav').textContent = stats.open_venues;

  // Animated counters
  animateCounter('stat-guests', stats.total_guests_tonight, '');
  animateCounter('stat-venues', stats.open_venues, '');
  animateCounter('stat-events', stats.trending_events, '');
  animateCounter('stat-sat', stats.avg_satisfaction, '%');
}

async function loadEvents() {
  const events = await api.getEvents();
  if (!events) return;
  state.events = events;
  renderEvents();
}

function renderEvents() {
  const grid = document.getElementById('events-grid');
  if (!grid) return;

  const query = document.getElementById('search-input')?.value.toLowerCase() || '';
  let filtered = [...state.events];

  if (state.currentFilter === 'trending') filtered = filtered.filter(e => e.trending);
  if (state.currentFilter === 'student')  filtered = filtered.filter(e => e.student_night);
  if (state.currentFilter === 'tourist')  filtered = filtered.filter(e => e.tourist_friendly);
  if (state.currentFilter === 'vip')      filtered = filtered.filter(e => e.vip_available);

  if (query) {
    filtered = filtered.filter(e =>
      e.title.toLowerCase().includes(query) ||
      e.venue_name.toLowerCase().includes(query) ||
      e.genre.toLowerCase().includes(query) ||
      e.dj.toLowerCase().includes(query)
    );
  }

  if (filtered.length === 0) {
    grid.innerHTML = `<div style="grid-column:1/-1;text-align:center;padding:60px 0;color:var(--text3);font-size:15px">
      😞 Δεν βρέθηκαν events. Δοκίμασε άλλα φίλτρα.
    </div>`;
    return;
  }

  grid.innerHTML = filtered.map(ev => buildEventCard(ev)).join('');
}

function buildEventCard(ev) {
  const occupancy = ev.venue_capacity ? Math.round((ev.venue_current / ev.venue_capacity) * 100) : 0;
  const priceLabel = ev.entry_price === 0 ? `<span class="card-price" style="color:var(--green)">FREE</span>` : `<span class="card-price">€${ev.entry_price}</span>`;
  const ctaLabel = ev.student_night ? 'Μπες σε λίστα' : ev.vip_available ? 'Αίτημα κράτησης' : 'Δες info';

  const badges = ev.badges.map(b => {
    const map = { trending:'badge-trending', live:'badge-live', vip:'badge-vip', tourist:'badge-tourist', new:'badge-new' };
    const labels = { trending:'🔥 Ανεβαίνει', live:'● LIVE', vip:'💎 Τραπέζι', tourist:'🌍 Tourist', new:'⚡ Νέο' };
    return `<span class="badge ${map[b] || ''}">${labels[b] || b}</span>`;
  }).join('');

  return `
  <div class="event-card" onclick="window.location.href='event.html?id=${ev.id}'">
    <div class="card-img ${ev.image_class}">
      <div class="card-img-bg">${ev.image_emoji}</div>
      <div class="card-overlay"></div>
      <div class="card-badges">${badges}</div>
      <div class="card-pop">
        <div class="pop-track"><div class="pop-fill" style="width:${ev.popularity}%"></div></div>
        <span>${ev.popularity}%</span>
      </div>
    </div>
    <div class="card-body">
      <div class="card-venue">${ev.venue_name}</div>
      <div class="card-title">${ev.title}</div>
      <div class="card-meta">
        <span class="genre-tag">${ev.genre_icon} ${ev.genre}</span>
      </div>
      <div class="card-meta">
        <span class="card-meta-item">🎤 ${ev.dj}</span>
        <span class="card-meta-item">👥 ${ev.venue_current} / ${ev.venue_capacity}</span>
      </div>
      <div class="card-footer">
        <div>
          <span class="card-price-label">${ev.min_spend_vip > 0 ? 'Ελάχιστη κατανάλωση' : 'Είσοδος από'}</span>
          ${ev.min_spend_vip > 0 ? `<span class="card-price">€${ev.min_spend_vip}</span>` : priceLabel}
        </div>
        <button class="card-reserve-btn" onclick="event.stopPropagation();window.location.href='event.html?id=${ev.id}'">${ctaLabel}</button>
      </div>
    </div>
  </div>`;
}

async function loadActivityFeed() {
  const feed = await api.getActivityFeed();
  const container = document.getElementById('activity-feed');
  if (!container) return;

  if (!feed) {
    container.innerHTML = '<div style="color:var(--text3);text-align:center;padding:20px">Δεν υπάρχει δραστηριότητα.</div>';
    return;
  }

  const avatarColors = [
    'linear-gradient(135deg,var(--neon),var(--pink))',
    'linear-gradient(135deg,var(--cyan),var(--neon))',
    'linear-gradient(135deg,var(--gold),var(--pink2))',
    'linear-gradient(135deg,var(--pink),var(--neon))',
    'linear-gradient(135deg,var(--cyan2),var(--cyan))',
  ];

  container.innerHTML = feed.map((item, i) => `
    <div class="feed-item">
      <div class="feed-avatar" style="background:${avatarColors[i % avatarColors.length]}">${item.initials}</div>
      <div>
        <div class="feed-text"><strong>${item.user}</strong> ${item.icon} ${item.action}</div>
        <div class="feed-time">${item.time}</div>
        ${item.event_id ? `<button class="feed-action-btn" onclick="window.location.href='event.html?id=${item.event_id}'">Δες event →</button>` : ''}
      </div>
    </div>
  `).join('');
}

function scrollToEvents() {
  document.getElementById('events-section')?.scrollIntoView({ behavior: 'smooth' });
}

/* ═══════════════════════════════════════════════════════════
   DASHBOARD
═══════════════════════════════════════════════════════════ */
async function loadDashboard() {
  await loadOverview();
}

/* ── OVERVIEW ─────────────────────────────────────────────── */
async function loadOverview() {
  const data = await api.getOverview();
  if (!data) return;
  state.overview = data;
  renderOverviewMetrics(data);
  if (!state.chartsInited) {
    const analytics = await api.getAnalytics();
    state.analytics = analytics;
    renderOverviewCharts(analytics);
    state.chartsInited = true;
  }
}

function renderOverviewMetrics(d) {
  const grid = document.getElementById('overview-metrics');
  if (!grid) return;
  grid.innerHTML = `
    ${metricCard('Αιτήματα', d.reservations_tonight, 'mc-purple', 'mv-purple', '+23 vs Παρ', true)}
    ${metricCard('Occupancy', d.occupancy_pct + '%', 'mc-cyan', 'mv-cyan', `${d.current_guests} / ${d.capacity}`, true)}
    ${metricCard('Εκτιμ. Έσοδα', '€' + (d.revenue_estimate/1000).toFixed(1) + 'K', 'mc-gold', 'mv-gold', '+12% vs avg', true)}
    ${metricCard('VIP Guests', d.vip_guests, 'mc-pink', 'mv-pink', 'Avg spend €290', false)}
    ${metricCard('Επαναλαμβ.', d.repeat_customers_pct + '%', 'mc-green', 'mv-green', '↑ Excellent', true)}
    ${metricCard('Guest List', d.guest_list_count, 'mc-purple', 'mv-gold', d.confirmed + ' confirmed', false)}
  `;
}

function metricCard(label, value, cardClass, valueClass, sub, isUp) {
  return `
  <div class="metric-card ${cardClass}" onclick="showToast('📊 Λεπτομερής ανάλυση...','Drilling Down')">
    <div class="metric-label">${label}</div>
    <div class="metric-value ${valueClass}">${value}</div>
    ${sub ? `<div class="metric-sub">${sub}</div>` : ''}
    ${isUp ? `<span class="metric-trend trend-up">↑ ${typeof isUp === 'string' ? isUp : ''}</span>` : ''}
  </div>`;
}

const CHART_OPTS = {
  plugins: {
    legend: { labels: { color: '#a89fd4', font: { size: 11, family: 'DM Sans' }, boxWidth: 12 } },
    tooltip: {
      backgroundColor: 'rgba(14,11,26,.95)', borderColor: 'rgba(255,255,255,.12)',
      borderWidth: 1, titleColor: '#f0ecff', bodyColor: '#a89fd4',
      titleFont: { family: 'Syne', size: 13 }, bodyFont: { family: 'DM Sans', size: 12 },
    },
  },
  scales: {
    x: { grid: { color: 'rgba(255,255,255,.04)' }, ticks: { color: '#6b5fa3', font: { size: 11, family: 'DM Sans' } } },
    y: { grid: { color: 'rgba(255,255,255,.04)' }, ticks: { color: '#6b5fa3', font: { size: 11, family: 'DM Sans' } } },
  },
  responsive: true, maintainAspectRatio: false,
};

function renderOverviewCharts(a) {
  if (!a) return;

  // Arrivals bar+line
  newChart('chart-arrivals', 'bar', {
    labels: a.hours,
    datasets: [
      { label: 'Αφίξεις', data: a.arrivals_by_hour, backgroundColor: 'rgba(124,58,255,.4)', borderColor: 'rgba(124,58,255,.8)', borderWidth: 1, borderRadius: 4, yAxisID: 'y' },
      { label: 'Έσοδα (€00s)', data: a.arrivals_by_hour.map(v => Math.round(v * 0.82)), borderColor: 'rgba(0,212,255,.8)', backgroundColor: 'rgba(0,212,255,.1)', borderWidth: 2, type: 'line', tension: 0.4, fill: true, yAxisID: 'y1' },
    ],
  }, { ...CHART_OPTS, scales: { ...CHART_OPTS.scales, y1: { position: 'right', grid: { display: false }, ticks: { color: '#6b5fa3', font: { size: 11, family: 'DM Sans' } } } } });

  // Genre donut
  newChart('chart-genres', 'doughnut', {
    labels: a.genres,
    datasets: [{ data: a.genre_split, backgroundColor: ['rgba(124,58,255,.85)','rgba(0,212,255,.75)','rgba(255,45,138,.75)','rgba(255,184,0,.75)','rgba(0,229,160,.75)','rgba(107,95,163,.6)'], borderWidth: 0, hoverOffset: 8 }],
  }, { responsive: true, maintainAspectRatio: false, cutout: '68%', plugins: { ...CHART_OPTS.plugins, legend: { position: 'right', labels: { color: '#a89fd4', font: { size: 11, family: 'DM Sans' }, boxWidth: 10 } } } });

  // Weekly
  newChart('chart-weekly', 'line', {
    labels: a.days,
    datasets: [
      { label: 'Έσοδα (€K)', data: a.weekly_revenue, borderColor: 'rgba(124,58,255,.9)', backgroundColor: 'rgba(124,58,255,.1)', fill: true, tension: 0.4, borderWidth: 2, pointBackgroundColor: 'rgba(124,58,255,1)', pointRadius: 4 },
      { label: 'Occupancy %', data: a.weekly_occupancy, borderColor: 'rgba(0,212,255,.7)', backgroundColor: 'transparent', tension: 0.4, borderWidth: 2, borderDash: [4,3], pointRadius: 4 },
    ],
  }, CHART_OPTS);

  // Retention stacked
  newChart('chart-retention', 'bar', {
    labels: a.retention.weeks,
    datasets: [
      { label: 'Νέοι', data: a.retention.new, backgroundColor: 'rgba(0,212,255,.55)', borderRadius: 4 },
      { label: 'Επαναλαμβ.', data: a.retention.returning, backgroundColor: 'rgba(124,58,255,.55)', borderRadius: 4 },
    ],
  }, { ...CHART_OPTS, scales: { ...CHART_OPTS.scales, x: { ...CHART_OPTS.scales.x, stacked: true }, y: { ...CHART_OPTS.scales.y, stacked: true } } });
}

/* ── RESERVATIONS ─────────────────────────────────────────── */
async function loadReservations() {
  const data = await api.getReservations('?venue_id=v1');
  if (!data) return;
  state.reservations = data;

  const badge = document.getElementById('res-badge');
  if (badge) badge.textContent = data.length;

  renderReservationList(data);
}

function renderReservationList(reservations) {
  const el = document.getElementById('reservation-list');
  if (!el) return;

  const avatarColors = [
    'linear-gradient(135deg,rgba(124,58,255,.3),rgba(0,212,255,.2))',
    'linear-gradient(135deg,rgba(255,45,138,.25),rgba(124,58,255,.15))',
    'linear-gradient(135deg,rgba(255,184,0,.25),rgba(255,45,138,.15))',
    'linear-gradient(135deg,rgba(0,229,160,.2),rgba(0,212,255,.15))',
    'rgba(255,184,0,.2)',
    'linear-gradient(135deg,rgba(0,212,255,.2),rgba(124,58,255,.15))',
  ];

  el.innerHTML = reservations.map((r, i) => {
    const isVip = r.table_type === 'vip';
    const statusEl = r.checked_in
      ? `<span class="res-status s-checkedin">✓ Checked In</span>`
      : r.status === 'confirmed'
        ? `<span class="res-status ${isVip ? 's-vip' : 's-confirmed'}">${isVip ? 'VIP' : 'Confirmed'}</span>`
        : `<div class="res-actions">
             <button class="res-btn btn-confirm" onclick="confirmRes('${r.id}')">Confirm</button>
             <button class="res-btn btn-reject" onclick="rejectRes('${r.id}')">Reject</button>
           </div>`;

    return `
    <div class="res-item" id="res-${r.id}">
      <div class="res-avatar" style="background:${avatarColors[i % avatarColors.length]}">${r.customer_initials}</div>
      <div class="res-info">
        <div class="res-name">${r.customer_name}</div>
        <div class="res-detail">${r.table_type === 'vip' ? 'VIP · ' : ''}Table ${r.table} · ${r.guests} pax · ${r.arrival_time}${r.notes ? ' · ' + r.notes : ''}</div>
      </div>
      ${statusEl}
    </div>`;
  }).join('');
}

async function confirmRes(id) {
  const res = await api.updateReservation(id, { status: 'confirmed' });
  if (res) {
    showToast('✅ Κράτηση επιβεβαιώθηκε!', 'Confirmed');
    await loadReservations();
  }
}

async function rejectRes(id) {
  const res = await api.updateReservation(id, { status: 'rejected' });
  if (res) {
    showToast('❌ Κράτηση απορρίφθηκε.', 'Rejected');
    await loadReservations();
  }
}

/* ── CUSTOMERS ────────────────────────────────────────────── */
async function loadCustomers(tier = '') {
  const data = await api.getCustomers(tier);
  if (!data) return;
  state.customers = data;
  renderCustomers(data);
}

function renderCustomers(customers) {
  const grid = document.getElementById('customers-grid');
  if (!grid) return;

  const tierLabel = { gold: '🥇 Gold', black: '💎 Black', silver: '🥈 Silver' };
  const tierClass = { gold: 'tier-gold', black: 'tier-black', silver: 'tier-silver' };
  const avatarGrads = [
    'linear-gradient(135deg,var(--neon),var(--pink))',
    'linear-gradient(135deg,var(--pink),var(--gold))',
    'linear-gradient(135deg,var(--cyan),var(--neon))',
    'linear-gradient(135deg,var(--gold),var(--pink2))',
    'linear-gradient(135deg,var(--neon2),var(--cyan2))',
    'linear-gradient(135deg,#6b7280,#9ca3af)',
  ];

  grid.innerHTML = customers.map((c, i) => `
    <div class="customer-card" onclick="window.location.href='customer.html?id=${c.id}'">
      <div class="cust-header">
        <div class="cust-avatar" style="background:${avatarGrads[i % avatarGrads.length]}">${c.initials}</div>
        <div>
          <div class="cust-name">${c.name}</div>
          <div class="cust-since">Πελάτης από ${formatDate(c.customer_since)}</div>
        </div>
      </div>
      <span class="cust-tier ${tierClass[c.tier]}">${tierLabel[c.tier]}</span>
      <div class="cust-genre">🎵 ${c.fav_genre}${c.birthday ? ` &nbsp;·&nbsp; 🎂 ${formatBirthday(c.birthday)}` : ''}</div>
      <div class="cust-stats">
        <div class="cust-stat">
          <div class="cust-stat-num" style="color:var(--gold)">€${(c.avg_spend_month/1000).toFixed(1)}K</div>
          <div class="cust-stat-label">Avg/Month</div>
        </div>
        <div class="cust-stat">
          <div class="cust-stat-num">${c.total_visits}</div>
          <div class="cust-stat-label">Επισκέψεις</div>
        </div>
        <div class="cust-stat">
          <div class="cust-stat-num" style="color:var(--neon3)">${c.points.toLocaleString()}</div>
          <div class="cust-stat-label">Points</div>
        </div>
      </div>
    </div>`).join('');
}

/* ── PROMOTERS ────────────────────────────────────────────── */
async function loadPromoters() {
  const data = await api.getPromoters();
  if (!data) return;
  state.promoters = data;

  const totalGuests  = data.reduce((s, p) => s + p.guests_brought, 0);
  const totalRev     = data.reduce((s, p) => s + p.revenue_generated, 0);
  const totalComm    = data.reduce((s, p) => s + p.commission, 0);
  const topPromoter  = [...data].sort((a,b) => b.guests_brought - a.guests_brought)[0];
  const metricsEl    = document.getElementById('promoter-metrics');

  if (metricsEl) {
    metricsEl.innerHTML = `
      ${metricCard('Active Promoters', data.length, 'mc-cyan', 'mv-cyan', '', false)}
      ${metricCard('Κόσμος τώρα', totalGuests, 'mc-gold', 'mv-gold', 'Σύνολο απόψε', false)}
      ${metricCard('Commissions Due', '€' + totalComm.toLocaleString(), 'mc-purple', 'mv-purple', 'Αυτό τον μήνα', false)}
      ${metricCard('Top Promoter', '', 'mc-green', 'mv-green', '', false).replace('></div>', `>${topPromoter?.name.split(' ')[0] || '-'}</div>`)}
    `;
  }

  const table = document.getElementById('promoters-table');
  if (!table) return;

  const maxGuests = Math.max(...data.map(p => p.guests_brought));
  const statusBadge = s => {
    const map = { active: 's-confirmed', top: 's-vip', pending: 's-pending' };
    const lbl = { active: 'Active', top: '⭐ Top', pending: 'Pending' };
    return `<span class="res-status ${map[s]}">${lbl[s] || s}</span>`;
  };

  table.innerHTML = `
    <thead>
      <tr>
        <th>Promoter</th><th>Guests</th><th>Performance</th><th>Revenue</th><th>Commission</th><th>Status</th>
      </tr>
    </thead>
    <tbody>
      ${data.map(p => `
        <tr>
          <td><strong>${p.name}</strong></td>
          <td style="color:var(--cyan)">${p.guests_brought} guests</td>
          <td><div class="promo-bar"><div class="promo-bar-fill" style="width:${Math.round(p.guests_brought/maxGuests*100)}%"></div></div></td>
          <td style="color:var(--gold)">€${p.revenue_generated.toLocaleString()}</td>
          <td style="color:var(--green)">€${p.commission.toLocaleString()}</td>
          <td>${statusBadge(p.status)}</td>
        </tr>`).join('')}
    </tbody>`;
}

/* ── ANALYTICS ────────────────────────────────────────────── */
async function loadAnalytics() {
  if (state.analyticsInited) return;
  const a = state.analytics || await api.getAnalytics();
  if (!a) return;
  state.analytics = a;
  state.analyticsInited = true;

  const metricsEl = document.getElementById('analytics-metrics');
  if (metricsEl) {
    metricsEl.innerHTML = `
      ${metricCard('Μηνιαία Έσοδα', '€284K', 'mc-gold', 'mv-gold', '+28% vs last season', true)}
      ${metricCard('Μέση Πληρότητα', '76%', 'mc-cyan', 'mv-cyan', 'Peak: 97%', true)}
      ${metricCard('Events Hosted', '24', 'mc-purple', 'mv-purple', 'Αυτό τον μήνα', false)}
      ${metricCard('Retention Rate', '67%', 'mc-green', 'mv-green', 'Industry avg: 43%', true)}
    `;
  }

  newChart('chart-monthly', 'bar', {
    labels: a.months,
    datasets: [{ label: 'Έσοδα (€K)', data: a.monthly_revenue, backgroundColor: a.monthly_revenue.map((v,i) => `rgba(124,58,255,${0.35 + i*0.12})`), borderRadius: 6 }],
  }, { ...CHART_OPTS, plugins: { ...CHART_OPTS.plugins, legend: { display: false } } });

  newChart('chart-bestnight', 'bar', {
    labels: a.days,
    datasets: [{ label: 'Avg Revenue (€K)', data: a.best_nights, backgroundColor: a.best_nights.map(v => v > 15 ? 'rgba(0,212,255,.8)' : v > 8 ? 'rgba(124,58,255,.7)' : 'rgba(107,95,163,.5)'), borderRadius: 6 }],
  }, { ...CHART_OPTS, plugins: { ...CHART_OPTS.plugins, legend: { display: false } } });

  newChart('chart-peakhour', 'line', {
    labels: a.hours,
    datasets: [{ label: 'Αφίξεις', data: a.arrivals_by_hour, borderColor: 'rgba(255,45,138,.85)', backgroundColor: 'rgba(255,45,138,.12)', fill: true, tension: 0.4, borderWidth: 2, pointRadius: 4 }],
  }, { ...CHART_OPTS, plugins: { ...CHART_OPTS.plugins, legend: { display: false } } });

  newChart('chart-spend', 'bar', {
    labels: a.tiers,
    datasets: [{ label: 'Avg Spend (€)', data: a.spend_by_tier, backgroundColor: ['rgba(107,95,163,.55)','rgba(156,163,175,.65)','rgba(255,184,0,.75)','rgba(124,58,255,.85)'], borderRadius: 8 }],
  }, { ...CHART_OPTS, plugins: { ...CHART_OPTS.plugins, legend: { display: false } } });
}

/* ── STAFF ────────────────────────────────────────────────── */
async function loadStaff() {
  const overview = await api.getOverview();
  const reservations = state.reservations.length ? state.reservations : await api.getReservations('?venue_id=v1');

  const metricsEl = document.getElementById('staff-metrics');
  if (metricsEl && overview) {
    const checkedIn = reservations.filter(r => r.checked_in).length;
    metricsEl.innerHTML = `
      ${metricCard('Checked In', checkedIn, 'mc-green', 'mv-green', `of ${overview.guest_list_count} expected`, false)}
      ${metricCard('Occupancy', overview.occupancy_pct + '%', 'mc-cyan', 'mv-cyan', '', false)}
      ${metricCard('Queue Length', '42', 'mc-pink', 'mv-pink', 'Est. 18 min wait', false)}
      ${metricCard('No-Shows', '8', 'mc-gold', 'mv-gold', 'Released 4 tables', false)}
    `;
  }

  const queueEl = document.getElementById('checkin-queue');
  if (!queueEl) return;

  const avatarColors = [
    'linear-gradient(135deg,rgba(124,58,255,.3),rgba(0,212,255,.2))',
    'linear-gradient(135deg,rgba(255,45,138,.25),rgba(124,58,255,.15))',
    'linear-gradient(135deg,rgba(0,229,160,.2),rgba(0,212,255,.15))',
    'rgba(255,184,0,.2)',
    'linear-gradient(135deg,rgba(0,212,255,.2),rgba(124,58,255,.15))',
  ];

  const notCheckedIn = reservations.filter(r => !r.checked_in);
  queueEl.innerHTML = notCheckedIn.slice(0, 6).map((r, i) => `
    <div class="res-item">
      <div class="res-avatar" style="background:${avatarColors[i % avatarColors.length]}">${r.customer_initials}</div>
      <div class="res-info">
        <div class="res-name">${r.customer_name}</div>
        <div class="res-detail">${r.table_type === 'vip' ? 'VIP · ' : ''}Table ${r.table} · ${r.guests} pax</div>
      </div>
      <button class="res-btn btn-checkin" onclick="doCheckin('${r.id}','${r.customer_name}')">Check In</button>
    </div>`).join('');
}

async function doCheckin(id, name) {
  const res = await api.checkinReservation(id);
  if (res) {
    showToast(`✅ ${name} — checked in!`, 'Check In');
    state.reservations = state.reservations.map(r => r.id === id ? { ...r, checked_in: true } : r);
    loadStaff();
  }
}


/* ═══════════════════════════════════════════════════════════
   AUTH
═══════════════════════════════════════════════════════════ */
function setupAuth() {
  document.getElementById('btn-signin')?.addEventListener('click', () => window.location.href='auth.html');
  document.getElementById('btn-join')?.addEventListener('click', () => window.location.href='auth.html?tab=signup');
  document.getElementById('mobile-join')?.addEventListener('click', () => window.location.href='auth.html?tab=signup');
  document.getElementById('btn-logout')?.addEventListener('click', logout);
  document.getElementById('auth-toggle')?.addEventListener('click', () => openAuthModal(state.authMode === 'login' ? 'register' : 'login'));
  document.getElementById('auth-submit')?.addEventListener('click', submitAuth);
  document.getElementById('auth-role')?.addEventListener('change', e => {
    document.getElementById('auth-venue-wrap').style.display = e.target.value === 'club' ? 'block' : 'none';
  });
}

function fillDemoLogin(type) {
  window.location.href='auth.html';
  document.getElementById('auth-email').value = type === 'club' ? 'club@nightflow.gr' : 'customer@nightflow.gr';
  document.getElementById('auth-password').value = type === 'club' ? 'club123' : 'customer123';
}

function openAuthModal(mode='login') {
  state.authMode = mode;
  const register = mode === 'register';
  document.getElementById('auth-title').textContent = register ? 'Δημιουργία account' : 'Σύνδεση στο NightFlow';
  document.getElementById('auth-submit').textContent = register ? 'Δημιουργία' : 'Σύνδεση';
  document.getElementById('auth-toggle').textContent = register ? 'Έχω ήδη account' : 'Δεν έχω account';
  document.getElementById('auth-name-wrap').style.display = register ? 'block' : 'none';
  document.getElementById('auth-role-wrap').style.display = register ? 'block' : 'none';
  document.getElementById('auth-venue-wrap').style.display = register && document.getElementById('auth-role').value === 'club' ? 'block' : 'none';
  document.getElementById('auth-error').textContent = '';
  document.getElementById('modal-auth').classList.add('open');
}

async function submitAuth() {
  const email = document.getElementById('auth-email').value.trim();
  const password = document.getElementById('auth-password').value;
  const error = document.getElementById('auth-error');
  error.textContent = '';
  let result;
  if (state.authMode === 'login') {
    result = await api.login(email, password);
  } else {
    result = await api.register({
      name: document.getElementById('auth-name').value.trim(),
      email,
      password,
      role: document.getElementById('auth-role').value,
      venue_name: document.getElementById('auth-venue').value.trim(),
    });
  }
  if (!result || result.error) {
    error.textContent = result?.error || 'Δεν έγινε σύνδεση. Έλεγξε τα στοιχεία.';
    return;
  }
  localStorage.setItem('nightflow_token', result.token);
  localStorage.setItem('nightflow_user', JSON.stringify(result.user));
  state.authUser = result.user;
  renderAuthState();
  closeModal('modal-auth');
  showToast(`✅ Καλωσήρθες, ${result.user.name}`, result.user.role === 'club' ? 'Owner account' : 'Customer account');
  if (result.user.role === 'club') switchPage('dashboard');
}

async function logout() {
  await api.logout();
  localStorage.removeItem('nightflow_token');
  localStorage.removeItem('nightflow_user');
  state.authUser = null;
  renderAuthState();
  switchPage('discover');
  showToast('Έγινε αποσύνδεση.', 'NightFlow');
}

function renderAuthState() {
  const signed = !!state.authUser;
  document.getElementById('btn-signin').style.display = signed ? 'none' : 'inline-flex';
  document.getElementById('btn-join').style.display = signed ? 'none' : 'inline-flex';
  document.getElementById('btn-logout').style.display = signed ? 'inline-flex' : 'none';
  const avatar = document.getElementById('nav-avatar');
  if (avatar) {
    avatar.textContent = signed ? initials(state.authUser.name) : '?';
    avatar.title = signed ? `${state.authUser.name} (${state.authUser.role})` : 'Σύνδεση';
    avatar.classList.toggle('authed', signed);
  }
  document.querySelectorAll('.nav-tab[data-page="dashboard"], .mobile-tab[data-page="dashboard"]').forEach(el => {
    el.style.display = signed && state.authUser.role === 'club' ? '' : 'none';
  });
}

function initials(name='') {
  return name.split(' ').filter(Boolean).slice(0,2).map(x => x[0]).join('').toUpperCase() || 'NF';
}

function requireLoginForAction(actionName='αυτή την ενέργεια') {
  if (state.authUser) return true;
  showToast(`🔐 Κάνε σύνδεση για ${actionName}.`, 'Χρειάζεται account');
  window.location.href='auth.html';
  return false;
}

/* ═══════════════════════════════════════════════════════════
   MODALS
═══════════════════════════════════════════════════════════ */
function openReserveModal(eventId) {
  if (!requireLoginForAction('κράτηση ή guest list')) return;
  state.activeReserveEventId = eventId;
  const ev = state.events.find(e => e.id === eventId);
  if (ev) {
    document.getElementById('reserve-modal-title').textContent = `Αίτημα — ${ev.title}`;
  }
  document.getElementById('modal-reserve').classList.add('open');
}

function openNewResModal() {
  if (!state.authUser || state.authUser.role !== 'club') return window.location.href='auth.html';
  document.getElementById('modal-reserve').classList.add('open');
}

function openNewCustomerModal() {
  if (!state.authUser || state.authUser.role !== 'club') return window.location.href='auth.html';
  document.getElementById('modal-customer').classList.add('open');
}

function openNewPromoterModal() {
  if (!state.authUser || state.authUser.role !== 'club') return window.location.href='auth.html';
  document.getElementById('modal-promoter').classList.add('open');
}

function closeModal(id) {
  document.getElementById(id).classList.remove('open');
}

// Close on overlay click
document.querySelectorAll('.modal-overlay').forEach(overlay => {
  overlay.addEventListener('click', e => {
    if (e.target === overlay) overlay.classList.remove('open');
  });
});

async function submitReservation() {
  if (!requireLoginForAction('να στείλεις κράτηση')) return;
  const name  = document.getElementById('res-name').value.trim();
  const email = document.getElementById('res-email').value.trim();
  if (!name) { showToast('⚠️ Συμπλήρωσε το όνομά σου', 'Validation Error'); return; }

  const data = {
    customer_name: name,
    email,
    guests:       parseInt(document.getElementById('res-guests').value),
    arrival_time: document.getElementById('res-time').value,
    table_type:   document.getElementById('res-type').value,
    notes:        document.getElementById('res-notes').value,
    venue_id:     'v1',
    event_id:     state.activeReserveEventId || 'e1',
    table:        'T-NEW',
  };

  const result = await api.createReservation(data);
  if (result) {
    showToast(`🎉 Κράτηση επιβεβαιώθηκε για ${name}!`, 'Κράτηση');
    closeModal('modal-reserve');
    // Reset form
    ['res-name','res-email','res-notes'].forEach(id => { const el = document.getElementById(id); if(el) el.value = ''; });

    // If on dashboard, reload
    if (state.currentCRM === 'reservations') await loadReservations();
    else if (state.currentCRM === 'staff') await loadStaff();
  } else {
    showToast('❌ Σφάλμα κράτησης. Δοκίμασε ξανά.', 'Error');
  }
}

async function submitNewCustomer() {
  const name = document.getElementById('cust-name').value.trim();
  if (!name) { showToast('⚠️ Συμπλήρωσε το όνομα', 'Validation'); return; }

  const data = {
    name,
    email:    document.getElementById('cust-email').value,
    phone:    document.getElementById('cust-phone').value,
    birthday: document.getElementById('cust-birthday').value,
    fav_genre:document.getElementById('cust-genre').value,
    notes:    document.getElementById('cust-notes').value,
  };

  const result = await api.createCustomer(data);
  if (result) {
    showToast(`👤 ${name} προστέθηκε!`, 'Νέος Πελάτης');
    closeModal('modal-customer');
    await loadCustomers();
  }
}

async function submitNewPromoter() {
  const name = document.getElementById('promo-name').value.trim();
  if (!name) { showToast('⚠️ Συμπλήρωσε το όνομα', 'Validation'); return; }

  const result = await api.createPromoter({ name });
  if (result) {
    showToast(`📣 ${name} προστέθηκε ως promoter!`, 'Νέος Promoter');
    closeModal('modal-promoter');
    await loadPromoters();
  }
}

async function sendCampaign(type, count) {
  const result = await api.sendCampaign(type, count);
  if (result && result.success) {
    const labels = { birthday: '🎂 Birthday campaign', vip_invite: '💎 VIP invitations', push: '📲 Push notifications', winback: '💌 Winback campaign' };
    showToast(`${labels[type] || type} sent to ${count} contacts!`, 'Campaign Sent');
  }
}

/* ═══════════════════════════════════════════════════════════
   HEATMAP INTERACTIONS
═══════════════════════════════════════════════════════════ */
function setupHeatmap() {
  const tooltip = document.getElementById('hm-tooltip');
  document.querySelectorAll('.hm-pin').forEach(pin => {
    pin.addEventListener('mouseenter', e => {
      if (!tooltip) return;
      tooltip.textContent = pin.dataset.venue;
      tooltip.style.display = 'block';
      const rect = pin.getBoundingClientRect();
      const map  = document.getElementById('heatmap').getBoundingClientRect();
      tooltip.style.left = (rect.left - map.left + 20) + 'px';
      tooltip.style.top  = (rect.top  - map.top  - 36) + 'px';
    });
    pin.addEventListener('mouseleave', () => { if (tooltip) tooltip.style.display = 'none'; });
  });
}

/* ═══════════════════════════════════════════════════════════
   FLOOR PLAN INTERACTIONS
═══════════════════════════════════════════════════════════ */
function setupFloorPlan() {
  const tooltip = document.getElementById('floor-tooltip');
  document.querySelectorAll('.floor-table').forEach(table => {
    table.addEventListener('mouseenter', e => {
      if (!tooltip) return;
      tooltip.textContent = table.dataset.info;
      tooltip.style.display = 'block';
      const rect   = table.getBoundingClientRect();
      const parent = document.getElementById('floor-plan').getBoundingClientRect();
      tooltip.style.left = (rect.left - parent.left + 22) + 'px';
      tooltip.style.top  = (rect.top  - parent.top  - 38) + 'px';
    });
    table.addEventListener('mouseleave', () => { if (tooltip) tooltip.style.display = 'none'; });
  });
}

/* ═══════════════════════════════════════════════════════════
   TOAST
═══════════════════════════════════════════════════════════ */
let toastTimer;
function showToast(msg, title) {
  const t  = document.getElementById('toast');
  const tt = document.getElementById('toast-title');
  const tm = document.getElementById('toast-msg');
  if (!t) return;
  if (tt) tt.textContent = title || 'NightFlow';
  if (tm) tm.textContent = msg;
  t.classList.add('show');
  clearTimeout(toastTimer);
  toastTimer = setTimeout(() => t.classList.remove('show'), 3500);
}

/* ═══════════════════════════════════════════════════════════
   CHART HELPER
═══════════════════════════════════════════════════════════ */
const chartInstances = {};
function newChart(id, type, data, options) {
  const canvas = document.getElementById(id);
  if (!canvas) return;
  if (chartInstances[id]) { chartInstances[id].destroy(); }
  chartInstances[id] = new Chart(canvas, { type, data, options });
}

/* ═══════════════════════════════════════════════════════════
   PARTICLES
═══════════════════════════════════════════════════════════ */
function spawnParticles() {
  const container = document.getElementById('hero-particles');
  if (!container) return;
  for (let i = 0; i < 30; i++) {
    const p = document.createElement('div');
    p.className = 'particle';
    p.style.cssText = `
      left: ${Math.random() * 100}%;
      top:  ${50 + Math.random() * 50}%;
      animation-delay: ${Math.random() * 4}s;
      animation-duration: ${3 + Math.random() * 3}s;
      width: ${1 + Math.random() * 3}px;
      height: ${1 + Math.random() * 3}px;
    `;
    container.appendChild(p);
  }
}

/* ═══════════════════════════════════════════════════════════
   UTILITIES
═══════════════════════════════════════════════════════════ */
function animateCounter(id, target, suffix) {
  const el = document.getElementById(id);
  if (!el) return;
  let current = 0;
  const step = target / 60;
  const timer = setInterval(() => {
    current = Math.min(current + step, target);
    el.textContent = Math.round(current).toLocaleString() + suffix;
    if (current >= target) clearInterval(timer);
  }, 16);
}

function debounce(fn, delay) {
  let timer;
  return (...args) => { clearTimeout(timer); timer = setTimeout(() => fn(...args), delay); };
}

function formatDate(dateStr) {
  if (!dateStr) return '';
  const d = new Date(dateStr);
  return d.toLocaleDateString('el-GR', { month: 'short', year: 'numeric' });
}

function formatBirthday(dateStr) {
  if (!dateStr) return '';
  const d = new Date(dateStr);
  return d.toLocaleDateString('el-GR', { day: 'numeric', month: 'long' });
}
