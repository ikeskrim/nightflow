/**
 * NightFlow API Client
 * JWT Authentication with refresh token support
 */

// Auto-detect API base URL (works locally and in production)
const API_BASE = window.location.hostname === 'localhost'
    ? 'http://localhost:5000'
    : '';

const NightFlowAPI = {
    // Token management
    getToken() {
        return localStorage.getItem('nightflow_token');
    },

    getRefreshToken() {
        return localStorage.getItem('nightflow_refresh_token');
    },

    setTokens(accessToken, refreshToken) {
        localStorage.setItem('nightflow_token', accessToken);
        if (refreshToken) {
            localStorage.setItem('nightflow_refresh_token', refreshToken);
        }
    },

    clearTokens() {
        localStorage.removeItem('nightflow_token');
        localStorage.removeItem('nightflow_refresh_token');
        localStorage.removeItem('nightflow_user');
    },

    getUser() {
        const user = localStorage.getItem('nightflow_user');
        return user ? JSON.parse(user) : null;
    },

    setUser(user) {
        localStorage.setItem('nightflow_user', JSON.stringify(user));
    },

    authHeaders() {
        const token = this.getToken();
        return token ? { 'Authorization': `Bearer ${token}` } : {};
    },

    // Core fetch wrapper with auto-refresh
    async request(endpoint, options = {}) {
        const url = `${API_BASE}${endpoint}`;
        const config = {
            headers: {
                'Content-Type': 'application/json',
                ...this.authHeaders(),
                ...options.headers
            },
            ...options
        };

        let response = await fetch(url, config);

        // If 401 and we have a refresh token, try to refresh
        if (response.status === 401 && this.getRefreshToken()) {
            const refreshed = await this.refreshAccessToken();
            if (refreshed) {
                config.headers = {
                    ...config.headers,
                    ...this.authHeaders()
                };
                response = await fetch(url, config);
            }
        }

        const data = await response.json();

        if (!response.ok) {
            throw new Error(data.error || 'Request failed');
        }

        return data;
    },

    async refreshAccessToken() {
        try {
            const response = await fetch(`${API_BASE}/api/auth/refresh`, {
                method: 'POST',
                headers: { 'Content-Type': 'application/json' },
                body: JSON.stringify({ refresh_token: this.getRefreshToken() })
            });

            if (!response.ok) {
                this.clearTokens();
                return false;
            }

            const data = await response.json();
            if (data.success && data.token) {
                localStorage.setItem('nightflow_token', data.token);
                return true;
            }
            return false;
        } catch {
            this.clearTokens();
            return false;
        }
    },

    // ─── Auth ────────────────────────────────────────────────
    async login(email, password) {
        const data = await this.request('/api/auth/login', {
            method: 'POST',
            body: JSON.stringify({ email, password })
        });

        if (data.success) {
            this.setTokens(data.token, data.refresh_token);
            this.setUser(data.user);
        }
        return data;
    },

    async register(userData) {
        const data = await this.request('/api/auth/register', {
            method: 'POST',
            body: JSON.stringify(userData)
        });

        if (data.success) {
            this.setTokens(data.token, data.refresh_token);
            this.setUser(data.user);
        }
        return data;
    },

    async me() {
        try {
            const data = await this.request('/api/auth/me');
            if (data.success && data.user) {
                this.setUser(data.user);
            }
            return data;
        } catch {
            return { success: true, user: null };
        }
    },

    async logout() {
        try {
            await this.request('/api/auth/logout', {
                method: 'POST',
                body: JSON.stringify({ refresh_token: this.getRefreshToken() })
            });
        } finally {
            this.clearTokens();
        }
        return { success: true };
    },

    isAuthenticated() {
        return !!this.getToken();
    },

    // ─── Public ──────────────────────────────────────────────
    async getTonightStats() {
        const data = await this.request('/api/tonight-stats');
        return data.data || data;
    },

    async getEvents(params = '') {
        const data = await this.request(`/api/events${params ? '?' + params : ''}`);
        return data.data || data;
    },

    async getEvent(id) {
        const data = await this.request(`/api/events/${id}`);
        return data.data || data;
    },

    async getVenues() {
        const data = await this.request('/api/venues');
        return data.data || data;
    },

    async getVenue(id) {
        const data = await this.request(`/api/venues/${id}`);
        return data.data || data;
    },

    async getActivityFeed() {
        const data = await this.request('/api/activity-feed');
        return data.data || data;
    },

    // ─── Reservations ────────────────────────────────────────
    async getReservations(params = '') {
        const data = await this.request(`/api/reservations${params ? '?' + params : ''}`);
        return data.data || data;
    },

    async createReservation(reservationData) {
        const data = await this.request('/api/reservations', {
            method: 'POST',
            body: JSON.stringify(reservationData)
        });
        return data.data || data;
    },

    async updateReservation(id, updates) {
        const data = await this.request(`/api/reservations/${id}`, {
            method: 'PATCH',
            body: JSON.stringify(updates)
        });
        return data.data || data;
    },

    async checkinReservation(id) {
        const data = await this.request(`/api/reservations/${id}/checkin`, {
            method: 'POST'
        });
        return data.data || data;
    },

    // ─── Customers ───────────────────────────────────────────
    async getCustomers(tier = '') {
        const params = tier ? `?tier=${tier}` : '';
        const data = await this.request(`/api/customers${params}`);
        return data.data || data;
    },

    async getCustomer(id) {
        const data = await this.request(`/api/customers/${id}`);
        return data.data || data;
    },

    async createCustomer(customerData) {
        const data = await this.request('/api/customers', {
            method: 'POST',
            body: JSON.stringify(customerData)
        });
        return data.data || data;
    },

    // ─── Promoters ───────────────────────────────────────────
    async getPromoters() {
        const data = await this.request('/api/promoters');
        return data.data || data;
    },

    async createPromoter(promoterData) {
        const data = await this.request('/api/promoters', {
            method: 'POST',
            body: JSON.stringify(promoterData)
        });
        return data.data || data;
    },

    // ─── Analytics ───────────────────────────────────────────
    async getAnalytics() {
        const data = await this.request('/api/analytics');
        return data.data || data;
    },

    async getOverview() {
        const data = await this.request('/api/analytics/overview');
        return data.data || data;
    },

    // ─── Marketing ───────────────────────────────────────────
    async sendCampaign(type, count) {
        const data = await this.request('/api/marketing/send', {
            method: 'POST',
            body: JSON.stringify({ type, count })
        });
        return data.data || data;
    },

    // ─── Guest List ──────────────────────────────────────────
    async joinGuestList(guestData) {
        const data = await this.request('/api/guestlist/join', {
            method: 'POST',
            body: JSON.stringify(guestData)
        });
        return data.data || data;
    }
};

// Export for use in other scripts
window.NightFlowAPI = NightFlowAPI;
window.API = NightFlowAPI;
