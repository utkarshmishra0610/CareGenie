/**
 * Vanilla JavaScript API Client using Fetch API.
 * Connects frontend UI to FastAPI backend endpoints.
 */

const API_BASE = '/api';

const API = {
  // Token management
  getToken() {
    return localStorage.getItem('caregenie_jwt_token') || localStorage.getItem('healthpulse_jwt_token');
  },

  setToken(token) {
    if (token) {
      localStorage.setItem('caregenie_jwt_token', token);
      localStorage.setItem('healthpulse_jwt_token', token);
    } else {
      localStorage.removeItem('caregenie_jwt_token');
      localStorage.removeItem('healthpulse_jwt_token');
    }
  },

  async ensureGuestSession() {
    let token = this.getToken();
    if (token) return token;
    try {
      const res = await fetch(`${API_BASE}/auth/guest`, {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' }
      });
      if (res.ok) {
        const data = await res.json();
        if (data.access_token) {
          this.setToken(data.access_token);
          return data.access_token;
        }
      }
    } catch (e) {
      console.warn('Could not auto-provision guest session:', e);
    }
    return null;
  },

  getAuthHeaders() {
    const headers = { 'Content-Type': 'application/json' };
    const token = this.getToken();
    if (token) {
      headers['Authorization'] = `Bearer ${token}`;
    }
    return headers;
  },

  async request(endpoint, options = {}) {
    if (!this.getToken() && !endpoint.startsWith('/auth')) {
      await this.ensureGuestSession();
    }
    const url = `${API_BASE}${endpoint}`;
    const defaultHeaders = this.getAuthHeaders();
    const config = {
      ...options,
      headers: {
        ...defaultHeaders,
        ...(options.headers || {}),
      },
    };

    try {
      const response = await fetch(url, config);
      if (response.status === 204) {
        return null;
      }
      const data = await response.json().catch(() => ({}));
      if (!response.ok) {
        const errorMsg = data.detail || `Request failed with status ${response.status}`;
        throw new Error(errorMsg);
      }
      return data;
    } catch (err) {
      console.error(`API Error on ${url}:`, err);
      throw err;
    }
  },

  // Auth Endpoints
  async register(username, email, password, fullName = '') {
    return this.request('/auth/register', {
      method: 'POST',
      body: JSON.stringify({
        username,
        email,
        password,
        full_name: fullName,
      }),
    });
  },

  async login(username, password) {
    const data = await this.request('/auth/login', {
      method: 'POST',
      body: JSON.stringify({ username, password }),
    });
    if (data.access_token) {
      this.setToken(data.access_token);
    }
    return data;
  },

  async getCurrentUser() {
    return this.request('/users/me');
  },

  logout() {
    this.setToken(null);
  },

  // Localization Endpoints
  async getLanguages() {
    return this.request('/languages');
  },

  async getLocalizationBundle(lang = 'en') {
    return this.request(`/localization/${lang}`);
  },

  // Chat Endpoints
  async createChatSession(language = 'en', title = 'Health Consultation') {
    return this.request('/chat/sessions', {
      method: 'POST',
      body: JSON.stringify({ title, language }),
    });
  },

  async getChatSessions() {
    return this.request('/chat/sessions');
  },

  async getChatSession(sessionId) {
    return this.request(`/chat/sessions/${sessionId}`);
  },

  async interactWithAI(sessionId, content) {
    return this.request(`/chat/sessions/${sessionId}/interact`, {
      method: 'POST',
      body: JSON.stringify({ content }),
    });
  },

  async finalizeAssessment(sessionId) {
    return this.request(`/chat/sessions/${sessionId}/finalize-assessment`, {
      method: 'POST',
    });
  },

  // ML Risk Prediction Endpoint
  async predictRisk(symptoms, severity = null, duration = null, age = null, gender = null, language = 'en') {
    return this.request('/assessment/predict', {
      method: 'POST',
      body: JSON.stringify({
        symptoms,
        severity,
        duration,
        age,
        gender,
        language,
      }),
    });
  },

  // History Endpoints
  async getHistory() {
    return this.request('/history');
  },

  async getAssessmentById(id) {
    return this.request(`/history/${id}`);
  },

  async deleteAssessment(id) {
    return this.request(`/history/${id}`, {
      method: 'DELETE',
    });
  },

  async addHealthcareSearch(assessmentId, searchItem) {
    return this.request(`/history/${assessmentId}/searches`, {
      method: 'POST',
      body: JSON.stringify(searchItem),
    });
  },

  // Healthcare Provider Locator Endpoints
  async getNearbyFacilities(params = {}) {
    const query = new URLSearchParams();
    if (params.lat !== undefined && params.lat !== null) query.append('lat', params.lat);
    if (params.lng !== undefined && params.lng !== null) query.append('lng', params.lng);
    if (params.city) query.append('city', params.city);
    if (params.specialty) query.append('specialty', params.specialty);
    if (params.radius_km) query.append('radius_km', params.radius_km);
    if (params.emergency_only) query.append('emergency_only', params.emergency_only);
    if (params.q) query.append('q', params.q);

    const queryString = query.toString() ? `?${query.toString()}` : '';
    return this.request(`/healthcare/nearby${queryString}`);
  },

  async getSpecialties() {
    return this.request('/healthcare/specialties');
  },

  async getMyLocation() {
    return this.request('/healthcare/my-location');
  },
};

