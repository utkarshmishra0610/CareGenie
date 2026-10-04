/**
 * Main Application Logic (Vanilla JavaScript - No Frameworks).
 * Controls Single Page Application views, interactive chat, ML results, and map.
 */

const App = {
  state: {
    user: null,
    language: 'en',
    activeView: 'landing',
    activeSession: null,
    symptoms: [],
    candidateConditions: [],
    lastAssessment: null,
    map: null,
    mapMarkers: [],
    liveOsmFacilities: [],
    providers: [
      {
        id: 29,
        name: 'Medanta Super Speciality Hospital, Indore',
        specialty: 'General Physician',
        lat: 22.7533,
        lng: 75.8937,
        dist: '2.5 km',
        rating: '4.8 ★',
        phone: '+91 731 4747 000',
        address: 'Sector B, Scheme No 54, Vijay Nagar, Indore',
        is24_7: true,
      },
      {
        id: 30,
        name: 'Bombay Hospital, Indore',
        specialty: 'Cardiologist',
        lat: 22.7601,
        lng: 75.9004,
        dist: '3.1 km',
        rating: '4.8 ★',
        phone: '+91 731 4771 111',
        address: 'Eastern Ring Road, Tulsi Nagar, Indore',
        is24_7: true,
      },
      {
        id: 31,
        name: 'Care CHL Hospitals, Indore',
        specialty: 'General Physician',
        lat: 22.7363,
        lng: 75.8885,
        dist: '1.8 km',
        rating: '4.7 ★',
        phone: '+91 731 4774 444',
        address: 'A.B. Road, Near LIG Square, Indore',
        is24_7: true,
      },
      {
        id: 32,
        name: 'Apollo Hospitals, Indore',
        specialty: 'Cardiologist',
        lat: 22.7554,
        lng: 75.8978,
        dist: '2.8 km',
        rating: '4.8 ★',
        phone: '+91 731 244 5566',
        address: 'Scheme No. 74C, Sector D, Vijay Nagar, Indore',
        is24_7: true,
      },
      {
        id: 34,
        name: 'Maharaja Yeshwantrao Hospital (MY Hospital)',
        specialty: 'Emergency Medicine',
        lat: 22.7161,
        lng: 75.8744,
        dist: '1.2 km',
        rating: '4.6 ★',
        phone: '+91 731 252 7383',
        address: 'MYH Square, A.B. Road, Sanyogitaganj, Indore',
        is24_7: true,
      },
      {
        id: 36,
        name: 'Choithram Hospital & Research Centre',
        specialty: 'Cardiologist',
        lat: 22.6936,
        lng: 75.8488,
        dist: '3.5 km',
        rating: '4.8 ★',
        phone: '+91 731 247 2301',
        address: '14 Manik Bagh Road, Indore',
        is24_7: true,
      },
    ],
  },

  async init() {
    console.log('CareGenie Frontend Initializing...');
    await this.checkAuthStatus();
    await this.loadLocalization('en');
    this.initMap();
  },

  // Authentication State Checker
  isAuthenticated() {
    return !!API.getToken() && !!this.state.user;
  },

  promptLoginForFeature(action, title, message) {
    this.state.pendingRedirectAction = action;
    const banner = document.getElementById('auth-gate-banner');
    const titleEl = document.getElementById('auth-gate-title');
    const msgEl = document.getElementById('auth-gate-message');

    if (banner) {
      if (titleEl) titleEl.textContent = title || 'Sign In Required';
      if (msgEl) msgEl.textContent = message || 'Please log in or register to access this clinical feature.';
      banner.classList.remove('hidden');
    }
    this.openAuthModal('login', true);
  },

  // Navigation Router (Gated for Unauthenticated Visitors)
  navigateTo(viewName) {
    const GATED_VIEWS = {
      'chat': {
        title: 'AI Symptom Checker',
        msg: 'Please sign in or create an account to start an AI symptom consultation.'
      },
      'assessment': {
        title: 'Disease Risk Assessment',
        msg: 'Please sign in or create an account to view condition risk evaluations.'
      },
      'map': {
        title: 'Healthcare Locator & Map',
        msg: 'Please sign in or create an account to locate verified hospitals and specialists near you.'
      },
      'history': {
        title: 'Patient Consultation History',
        msg: 'Please sign in or create an account to review your past health assessments.'
      }
    };

    if (GATED_VIEWS[viewName] && !this.isAuthenticated()) {
      this.promptLoginForFeature(
        { type: 'view', view: viewName },
        GATED_VIEWS[viewName].title,
        GATED_VIEWS[viewName].msg
      );
      return;
    }

    this.state.activeView = viewName;
    document.querySelectorAll('.view-panel').forEach(p => p.classList.remove('active'));
    document.querySelectorAll('.nav-link').forEach(l => {
      l.classList.toggle('active', l.dataset.view === viewName);
    });

    const targetView = document.getElementById(`view-${viewName}`);
    if (targetView) {
      targetView.classList.add('active');
    }

    if (viewName === 'map') {
      if (!this.state.map) {
        this.initMap();
      } else {
        setTimeout(() => this.state.map.invalidateSize(), 200);
      }
    }
    if (viewName === 'history') {
      this.loadHistoryView();
    }
  },

  // Authentication Management
  async checkAuthStatus() {
    const token = API.getToken();
    if (!token) {
      this.state.user = null;
      this.renderAuthState(null);
      return;
    }
    try {
      const user = await API.getCurrentUser();
      this.state.user = user;
      this.renderAuthState(user);
    } catch {
      API.logout();
      this.state.user = null;
      this.renderAuthState(null);
    }
  },

  renderAuthState(user) {
    const unauthGroup = document.getElementById('auth-unauthenticated');
    const authGroup = document.getElementById('auth-authenticated');
    const avatar = document.getElementById('user-avatar-initials');
    const nameSpan = document.getElementById('user-display-name');

    if (user) {
      unauthGroup.classList.add('hidden');
      authGroup.classList.remove('hidden');
      const initials = (user.full_name || user.username).substring(0, 2).toUpperCase();
      avatar.textContent = initials;
      nameSpan.textContent = user.full_name || user.username;
    } else {
      unauthGroup.classList.remove('hidden');
      authGroup.classList.add('hidden');
    }
  },

  openAuthModal(tab = 'login', preserveBanner = false) {
    const banner = document.getElementById('auth-gate-banner');
    if (!preserveBanner && banner) {
      banner.classList.add('hidden');
    }
    document.getElementById('modal-auth').classList.remove('hidden');
    this.switchAuthTab(tab);
  },

  closeAuthModal() {
    document.getElementById('modal-auth').classList.add('hidden');
    const banner = document.getElementById('auth-gate-banner');
    if (banner) banner.classList.add('hidden');
  },

  handleModalBackdropClick(event) {
    if (event.target.id === 'modal-auth') {
      this.closeAuthModal();
    }
  },

  switchAuthTab(tab) {
    const isLogin = tab === 'login';
    document.getElementById('tab-login').classList.toggle('active', isLogin);
    document.getElementById('tab-register').classList.toggle('active', !isLogin);
    document.getElementById('form-login').classList.toggle('hidden', !isLogin);
    document.getElementById('form-register').classList.toggle('hidden', isLogin);
    document.getElementById('login-error-msg').classList.add('hidden');
    document.getElementById('register-error-msg').classList.add('hidden');
  },

  async handleLogin(e) {
    e.preventDefault();
    const u = document.getElementById('login-username').value.trim();
    const p = document.getElementById('login-password').value;
    const errBox = document.getElementById('login-error-msg');
    errBox.classList.add('hidden');

    try {
      await API.login(u, p);
      await this.checkAuthStatus();
      const pendingAction = this.state.pendingRedirectAction;
      this.state.pendingRedirectAction = null;
      this.closeAuthModal();

      if (pendingAction) {
        if (pendingAction.type === 'startConsultation') {
          await this.startNewConsultation();
        } else if (pendingAction.type === 'view') {
          this.navigateTo(pendingAction.view);
        }
      }
    } catch (err) {
      errBox.textContent = err.message || 'Login failed.';
      errBox.classList.remove('hidden');
    }
  },

  async handleRegister(e) {
    e.preventDefault();
    const u = document.getElementById('reg-username').value.trim();
    const em = document.getElementById('reg-email').value.trim();
    const p = document.getElementById('reg-password').value;
    const fn = document.getElementById('reg-full-name').value.trim();
    const errBox = document.getElementById('register-error-msg');
    errBox.classList.add('hidden');

    try {
      await API.register(u, em, p, fn);
      await API.login(u, p);
      await this.checkAuthStatus();
      const pendingAction = this.state.pendingRedirectAction;
      this.state.pendingRedirectAction = null;
      this.closeAuthModal();

      if (pendingAction) {
        if (pendingAction.type === 'startConsultation') {
          await this.startNewConsultation();
        } else if (pendingAction.type === 'view') {
          this.navigateTo(pendingAction.view);
        }
      }
    } catch (err) {
      errBox.textContent = err.message || 'Registration failed.';
      errBox.classList.remove('hidden');
    }
  },

  logout() {
    API.logout();
    this.state.user = null;
    this.renderAuthState(null);
    this.navigateTo('landing');
  },

  // Multilingual Regional Localization
  async setLanguage(lang) {
    this.state.language = lang;
    const selectEl = document.getElementById('global-lang-select');
    if (selectEl) selectEl.value = lang;

    const btnEn = document.getElementById('lang-btn-en');
    const btnHi = document.getElementById('lang-btn-hi');
    if (btnEn) btnEn.classList.toggle('active', lang === 'en');
    if (btnHi) btnHi.classList.toggle('active', lang === 'hi');

    await this.loadLocalization(lang);
  },

  async loadLocalization(lang) {
    try {
      const bundle = await API.getLocalizationBundle(lang);
      if (bundle) {
        if (bundle.disclaimer) {
          const prefix = {
            hi: 'प्रारंभिक मार्गदर्शन अस्वीकरण:',
            mr: 'प्राथमिक मार्गदर्शन अस्वीकरण:',
            bn: 'প্রাথমিক নির্দেশিকা দাবিত্যাগ:',
            te: 'ప్రాథమిక మార్గదర్శక నిరాకరణ:',
            ta: 'ஆரம்ப வழிகாட்டுதல் மறுப்பு:',
            gu: 'પ્રારંભિક માર્ગદર્શન અસ્વીકરણ:',
            kn: 'ಪ್ರಾಥಮಿಕ ಮಾರ್ಗದರ್ಶನ ಹಕ್ಕುತ್ಯಾಗ:',
            pa: 'ਮੁਢਲਾ ਮਾਰਗਦਰਸ਼ਨ ਬੇਦਾਅਵਾ:',
          }[lang] || 'Preliminary Clinical Guidance Prototype:';
          document.getElementById('global-disclaimer-text').innerHTML = `<strong>${prefix}</strong> ${bundle.disclaimer}`;
        }
        if (bundle.app_tagline) {
          document.getElementById('landing-hero-subtitle').textContent = bundle.app_tagline;
        }
        if (bundle.ui) {
          const chatInput = document.getElementById('chat-user-input');
          if (chatInput && bundle.ui.describe_symptoms) {
            chatInput.placeholder = bundle.ui.describe_symptoms;
          }
          const sendBtn = document.getElementById('btn-chat-send');
          if (sendBtn && bundle.ui.send) {
            const sendSpan = sendBtn.querySelector('span');
            if (sendSpan) sendSpan.textContent = bundle.ui.send;
          }
        }
      }
    } catch (e) {
      console.warn('Localization load error:', e);
    }
  },

  // Conversational Chatbot Flow
  async startNewConsultation() {
    if (!this.isAuthenticated()) {
      this.promptLoginForFeature(
        { type: 'startConsultation' },
        'AI Symptom Consultation',
        'Please sign in or create an account to start an AI symptom consultation.'
      );
      return;
    }

    try {
      const sessionTitles = {
        hi: 'स्वास्थ्य परामर्श',
        mr: 'आरोग्य सल्ला',
        bn: 'স্বাস্থ্য পরামর্শ',
        te: 'ఆరోగ్య సంప్రదింపులు',
        ta: 'சுகாதார ஆலோசனை',
        gu: 'આરોગ્ય પરામર્શ',
        kn: 'ಆರೋಗ್ಯ ಸಮಾಲೋಚನೆ',
        pa: 'ਸਿਹਤ ਸਲਾਹ',
      };
      const session = await API.createChatSession(
        this.state.language,
        sessionTitles[this.state.language] || 'Health Consultation'
      );
      this.state.activeSession = session;
      this.state.symptoms = [];
      this.state.candidateConditions = [];

      this.navigateTo('chat');
      this.resetChatInterface();

      const GREETINGS = {
        hi: 'नमस्ते! मैं आपका व्यक्तिगत एआई स्वास्थ्य सहायक हूँ। कृपया बताएं कि आप वर्तमान में कौन से लक्षण या शारीरिक परेशानी महसूस कर रहे हैं?',
        mr: 'नमस्कार! मी तुमचा वैयक्तिकृत एआय आरोग्य सहाय्यक आहे. कृपया सांगा की सध्या तुम्हाला कोणती लक्षणे किंवा शारीरिक त्रास जाणवत आहे?',
        bn: 'নমস্কার! আমি আপনার ব্যক্তিগত এআই স্বাস্থ্য সহায়ক। দয়া করে বলুন যে আপনি বর্তমানে কী ধরণের শারীরিক সমস্যা বা অস্বস্তি অনুভব করছেন?',
        te: 'నమస్కారం! నేను మీ వ్యక్తిగతీకరించిన AI ఆరోగ్య సహాయకుడిని. దయచేసి మీరు ప్రస్తుతం ఎదుర్కొంటున్న ఆరోగ్య సమస్యలు లేదా లక్షణాలను వివరించండి.',
        ta: 'வணக்கம்! நான் உங்கள் தனிப்பயனாக்கப்பட்ட AI சுகாதார உதவியாளர். தற்போது நீங்கள் அனுபவிக்கும் அறிகுறிகள் அல்லது உடல்நலப் பிரச்சனைகளை விவரிக்கவும்.',
        gu: 'નમસ્તે! હું તમારો વ્યક્તિગત AI આરોગ્ય સહાયક છું. કૃપા કરીને જણાવો કે તમે હાલમાં કયા લક્ષણો અથવા શારીરિક તકલીફ અનુભવી રહ્યા છો?',
        kn: 'ನಮಸ್ಕಾರ! ನಾನು ನಿಮ್ಮ ವೈಯಕ್ತಿಕಗೊಳಿಸಿದ AI ಆರೋಗ್ಯ ಸಹಾಯಕ. ದಯವಿಟ್ಟು ನೀವು ಪ್ರಸ್ತುತ ಅನುಭವಿಸುತ್ತಿರುವ ಅನಾರೋಗ್ಯದ ಲಕ್ಷಣಗಳನ್ನು ವಿವರಿಸಿ.',
        pa: 'ਸਤਿ ਸ੍ਰੀ ਅਕਾਲ! ਮੈਂ ਤੁਹਾਡਾ ਨਿੱਜੀ ਏਆਈ ਸਿਹਤ ਸਹਾਇਕ ਹਾਂ। ਕਿਰਪਾ ਕਰਕੇ ਦੱਸੋ ਕਿ ਤੁਸੀਂ ਵਰਤਮਾਨ ਵਿੱਚ ਕਿਹੜੇ ਲੱਛਣ ਜਾਂ ਤਕਲੀਫ਼ ਮਹਿਸੂਸ ਕਰ ਰਹੇ ਹੋ?',
        en: 'Hello! I am your personalized AI Health Assistant. Please describe any symptoms or health discomforts you are currently experiencing.',
      };
      const initialGreeting = GREETINGS[this.state.language] || GREETINGS.en;

      this.appendChatMessage('assistant', initialGreeting);
    } catch (err) {
      alert('Please sign in or register to start a consultation session.');
      this.openAuthModal('login');
    }
  },

  resetChatInterface() {
    document.getElementById('chat-messages-container').innerHTML = '';
    document.getElementById('detected-symptoms-list').innerHTML = '<span class="tag-placeholder">No symptoms reported yet. Describe your condition in the chat.</span>';
    document.getElementById('candidate-conditions-preview').innerHTML = '<span class="tag-placeholder">Condition candidates will appear as symptoms are analyzed.</span>';
    document.getElementById('quick-reply-container').classList.add('hidden');
    document.getElementById('btn-finalize-chat-assessment').disabled = true;
    document.getElementById('chat-turn-indicator').textContent = 'Turn: 1 / 4';
  },

  appendChatMessage(sender, text, subtext = '') {
    const container = document.getElementById('chat-messages-container');
    const bubble = document.createElement('div');
    bubble.className = `chat-bubble ${sender}`;

    const senderName = sender === 'assistant' ? 'CareGenie' : (this.state.user ? (this.state.user.full_name || this.state.user.username) : 'Patient');
    bubble.innerHTML = `
      <div class="chat-bubble-header">
        <span>${senderName}</span>
      </div>
      <div class="chat-bubble-text">${text}</div>
      ${subtext ? `<div class="chat-disclaimer-subtext">${subtext}</div>` : ''}
    `;

    container.appendChild(bubble);
    container.scrollTop = container.scrollHeight;
  },

  async handleChatMessageSubmit(e) {
    e.preventDefault();
    const input = document.getElementById('chat-input-text');
    const text = input.value.trim();
    if (!text || !this.state.activeSession) return;

    input.value = '';
    this.appendChatMessage('user', text);

    try {
      const res = await API.interactWithAI(this.state.activeSession.id, text);
      this.appendChatMessage('assistant', res.reply_text, res.disclaimer);

      // Check emergency
      if (res.detected_emergency) {
        this.triggerEmergencyModal(res.structured_symptoms.emergency_reasons, res.emergency_advice);
      }

      // Update symptom tags
      const allSyms = (res.structured_symptoms.symptoms || []).concat(res.structured_symptoms.additionalSymptoms || []);
      if (res.structured_symptoms.duration) allSyms.push(`Duration: ${res.structured_symptoms.duration}`);
      if (res.structured_symptoms.severity) allSyms.push(`Severity: ${res.structured_symptoms.severity}`);
      this.renderSymptomTags(allSyms);

      // Update turn indicator
      document.getElementById('chat-turn-indicator').textContent = `Turn: ${res.question_turn || 1} / 4`;

      // Update candidate conditions preview
      if (res.candidate_conditions && res.candidate_conditions.length > 0) {
        this.renderCandidatePreview(res.candidate_conditions);
      }

      // Enable finalize button if ready
      if (res.is_ready_for_prediction || (res.question_turn && res.question_turn >= 3)) {
        document.getElementById('btn-finalize-chat-assessment').disabled = false;
      }

      // Render follow up chips if any
      if (res.follow_up_question) {
        this.renderQuickReplyChips(res.follow_up_question);
      } else {
        document.getElementById('quick-reply-container').classList.add('hidden');
      }
    } catch (err) {
      console.error(err);
      this.appendChatMessage('assistant', 'I apologize, but I encountered an issue processing your response. Please try again.');
    }
  },

  renderSymptomTags(symptoms) {
    const container = document.getElementById('detected-symptoms-list');
    if (!symptoms || symptoms.length === 0) {
      container.innerHTML = '<span class="tag-placeholder">No symptoms reported yet.</span>';
      return;
    }
    container.innerHTML = symptoms.map(s => `<span class="symptom-tag-pill">✓ ${s}</span>`).join('');
  },

  renderCandidatePreview(candidates) {
    const container = document.getElementById('candidate-conditions-preview');
    container.innerHTML = candidates.slice(0, 3).map(c => `
      <div class="candidate-mini-item">
        <span>${c.disease}</span>
        <span class="condition-prob">${c.score ? Math.round(c.score * 100) : 60}%</span>
      </div>
    `).join('');
  },

  renderQuickReplyChips(question) {
    const container = document.getElementById('quick-reply-container');
    let chips = [];
    if (question.includes('intensity') || question.includes('तीव्रता')) {
      chips = ['Mild (हल्का)', 'Moderate (मध्यम)', 'Severe (गंभीर)'];
    } else if (question.includes('How long') || question.includes('कितने समय')) {
      chips = ['Less than 24 hours', '2-3 days', 'Over a week'];
    } else {
      chips = ['Yes, definitely', 'No, not present', 'Only mild'];
    }

    container.innerHTML = chips.map(c => `
      <button class="quick-reply-chip" onclick="App.sendQuickReply('${c}')">${c}</button>
    `).join('');
    container.classList.remove('hidden');
  },

  sendQuickReply(text) {
    document.getElementById('chat-input-text').value = text;
    document.getElementById('chat-form').dispatchEvent(new Event('submit'));
  },

  // Finalize Assessment & View Results
  async finalizeActiveAssessment() {
    if (!this.state.activeSession) return;
    try {
      const result = await API.finalizeAssessment(this.state.activeSession.id);
      this.state.lastAssessment = result;
      this.renderAssessmentResults(result.prediction);
      this.navigateTo('assessment');
    } catch (err) {
      alert(`Could not complete assessment: ${err.message}`);
    }
  },

  renderAssessmentResults(prediction) {
    if (!prediction) return;
    document.getElementById('res-risk-score').textContent = Math.round(prediction.risk_score);
    
    const badge = document.getElementById('res-risk-tier-badge');
    badge.className = `risk-tier-pill ${prediction.risk_level.toLowerCase()}`;
    badge.textContent = `${prediction.risk_level} RISK`;

    document.getElementById('res-risk-rationale').textContent = prediction.risk_rationale;
    document.getElementById('res-recommended-specialty').textContent = prediction.recommended_specialty;

    // Render conditions list
    const condList = document.getElementById('res-candidate-conditions-list');
    condList.innerHTML = (prediction.top_conditions || []).map(c => `
      <div class="condition-result-item">
        <div class="cond-title-row">
          <span>${c.disease}</span>
          <span class="cond-conf-badge">${c.confidence_score}% Match</span>
        </div>
        <div class="cond-bar-bg">
          <div class="cond-bar-fill" style="width: ${c.confidence_score}%;"></div>
        </div>
        <div class="cond-specialty-sub">Recommended Department: ${c.specialty}</div>
      </div>
    `).join('');

    // Precautions list
    const precList = document.getElementById('res-precautions-list');
    precList.innerHTML = (prediction.general_precautions || []).map(p => `<li>${p}</li>`).join('');
  },

  searchNearbySpecialty() {
    const spec = document.getElementById('res-recommended-specialty').textContent;
    document.getElementById('map-specialty-filter').value = spec.includes('Cardio') ? 'Cardiologist' : (spec.includes('Pulmo') ? 'Pulmonologist' : 'General Physician');
    this.navigateTo('map');
    this.filterMapProviders();
  },

  // Emergency Modal
  triggerEmergencyModal(reasons, advice) {
    document.getElementById('emergency-modal-reasons').textContent = (reasons && reasons.length > 0)
      ? `Identified Warning Signs: ${reasons.join(', ')}`
      : 'Urgent red-flag emergency symptoms have been detected in your presentation.';
    if (advice) {
      document.getElementById('emergency-modal-advice').textContent = advice;
    }
    document.getElementById('modal-emergency').classList.remove('hidden');
  },

  closeEmergencyModal() {
    document.getElementById('modal-emergency').classList.add('hidden');
  },

  CITY_PRESETS: {
    delhi: { name: 'Delhi NCR', lat: 28.6139, lng: 77.2090 },
    mumbai: { name: 'Mumbai', lat: 19.0760, lng: 72.8777 },
    pune: { name: 'Pune', lat: 18.5204, lng: 73.8567 },
    bengaluru: { name: 'Bengaluru', lat: 12.9716, lng: 77.5946 },
    hyderabad: { name: 'Hyderabad', lat: 17.3850, lng: 78.4867 },
    chennai: { name: 'Chennai', lat: 13.0827, lng: 80.2707 },
    kolkata: { name: 'Kolkata', lat: 22.5726, lng: 88.3639 },
    ahmedabad: { name: 'Ahmedabad', lat: 23.0225, lng: 72.5714 },
    jaipur: { name: 'Jaipur', lat: 26.9124, lng: 75.7873 },
    lucknow: { name: 'Lucknow', lat: 26.8467, lng: 80.9462 },
    chandigarh: { name: 'Chandigarh / Mohali', lat: 30.7333, lng: 76.7794 },
    kanpur: { name: 'Kanpur', lat: 26.4499, lng: 80.3319 },
    varanasi: { name: 'Varanasi', lat: 25.3176, lng: 82.9739 },
    indore: { name: 'Indore', lat: 22.7196, lng: 75.8577 },
    bhopal: { name: 'Bhopal', lat: 23.2599, lng: 77.4126 },
    patna: { name: 'Patna', lat: 25.5941, lng: 85.1376 },
    kochi: { name: 'Kochi', lat: 9.9312, lng: 76.2673 },
  },

  // Healthcare Map & Exact Geolocation
  async initMap() {
    if (this.state.map) {
      setTimeout(() => { if (this.state.map) this.state.map.invalidateSize(); }, 200);
      return;
    }
    const mapEl = document.getElementById('leaflet-map');
    if (!mapEl) return;

    // Start with a general view
    this.state.map = L.map('leaflet-map', {
      zoomControl: true,
    }).setView([20.5937, 78.9629], 5);

    L.tileLayer('https://{s}.tile.openstreetmap.org/{z}/{x}/{y}.png', {
      attribution: '© OpenStreetMap contributors',
      maxZoom: 19
    }).addTo(this.state.map);

    // Interactive Map Click: Click anywhere on map to set your exact location
    this.state.map.on('click', async (e) => {
      await this.setUserExactLocation(e.latlng.lat, e.latlng.lng, 'Pinned by Map Click', 15);
    });

    // Detect location on load
    await this.detectUserLocation(false);
  },

  async setUserExactLocation(lat, lng, labelHint = null, zoom = 14, isGps = false) {
    this.state.userCoords = { lat, lng };
    const statusEl = document.getElementById('current-location-status');
    const pulseEl = document.getElementById('location-pulse-indicator');

    if (pulseEl) pulseEl.className = 'location-pulse-dot active';
    if (statusEl) statusEl.textContent = 'Updating exact address...';

    // Reverse-geocode to get exact street / neighborhood name
    let exactName = labelHint || `Lat: ${lat.toFixed(4)}, Lng: ${lng.toFixed(4)}`;
    try {
      const rev = await fetch(`https://nominatim.openstreetmap.org/reverse?format=json&lat=${lat}&lon=${lng}&zoom=16`, {
        headers: { 'Accept': 'application/json' }
      });
      if (rev.ok) {
        const d = await rev.json();
        const a = d.address || {};
        const parts = [
          a.road || a.pedestrian || a.suburb || a.neighbourhood || a.residential,
          a.city || a.town || a.county || a.state_district,
          a.state
        ].filter(Boolean);
        if (parts.length > 0) {
          exactName = parts.slice(0, 3).join(', ');
        } else if (d.display_name) {
          exactName = d.display_name.split(',').slice(0, 3).join(',');
        }
      }
    } catch (_) {}

    this.state.userLocationLabel = exactName;
    if (statusEl) {
      statusEl.innerHTML = `<strong>📍 Exact Pin:</strong> ${exactName}`;
      if (pulseEl) pulseEl.className = 'location-pulse-dot ready';
    }

    if (this.state.map) {
      this.state.map.flyTo([lat, lng], zoom, { duration: 0.9 });

      if (this.state.userLocationMarker) {
        this.state.map.removeLayer(this.state.userLocationMarker);
      }
      if (this.state.userAccuracyCircle) {
        this.state.map.removeLayer(this.state.userAccuracyCircle);
      }

      const userIcon = L.divIcon({
        className: 'user-pulse-marker-wrapper',
        html: `<div class="pulse-ring"></div><div class="user-pulse-core">📍</div>`,
        iconSize: [36, 36],
        iconAnchor: [18, 18],
        popupAnchor: [0, -18]
      });

      this.state.userLocationMarker = L.marker([lat, lng], {
        icon: userIcon,
        draggable: true,
        title: 'Drag to adjust your exact location'
      }).addTo(this.state.map);

      this.state.userLocationMarker.bindPopup(`
        <strong>📍 Your Exact Location</strong><br>
        <span>${exactName}</span><br>
        <small style="color:var(--color-teal); font-weight:600;">(Tip: Drag this pin or click anywhere to adjust)</small>
      `).openPopup();

      // Drag event on user pin
      this.state.userLocationMarker.on('dragend', async (ev) => {
        const pos = ev.target.getLatLng();
        await this.setUserExactLocation(pos.lat, pos.lng, 'Pinned by Dragged Pin', 15);
      });

      this.state.userAccuracyCircle = L.circle([lat, lng], {
        radius: isGps ? 300 : 1500,
        color: '#0D9488',
        fillColor: '#0D9488',
        fillOpacity: 0.12,
        weight: 1.5
      }).addTo(this.state.map);
    }

    await this.filterMapProviders();
  },

  async searchExactAddress() {
    const input = document.getElementById('exact-address-input');
    const query = (input.value || '').trim();
    if (!query) return;

    const statusEl = document.getElementById('current-location-status');
    if (statusEl) statusEl.textContent = `Searching "${query}"...`;

    try {
      const res = await fetch(`https://nominatim.openstreetmap.org/search?format=json&q=${encodeURIComponent(query)}&limit=1`);
      if (res.ok) {
        const data = await res.json();
        if (data && data.length > 0) {
          const lat = parseFloat(data[0].lat);
          const lng = parseFloat(data[0].lon);
          const name = data[0].display_name.split(',').slice(0, 3).join(',');
          await this.setUserExactLocation(lat, lng, name, 15, true);
          return;
        }
      }
      alert(`Location "${query}" could not be found. Try adding city name, e.g. "${query}, Indore".`);
    } catch (e) {
      console.warn('Geocoding search error:', e);
      alert('Error searching for address. Please check your internet connection.');
    }
  },

  async triggerGpsLocate() {
    const helpEl = document.getElementById('gps-permission-help');
    const statusEl = document.getElementById('current-location-status');
    const pulseEl = document.getElementById('location-pulse-indicator');
    if (helpEl) helpEl.classList.add('hidden');
    if (statusEl) statusEl.textContent = 'Requesting GPS signal...';
    if (pulseEl) pulseEl.className = 'location-pulse-dot active';

    if (!('geolocation' in navigator)) {
      if (helpEl) {
        helpEl.innerHTML = '<span>⚠️ Geolocation is not supported by your browser. Please type your area or click on the map.</span>';
        helpEl.classList.remove('hidden');
      }
      return;
    }

    const showGpsError = (err) => {
      console.warn('GPS locate error:', err);
      if (statusEl) statusEl.textContent = 'GPS blocked or unavailable';
      if (pulseEl) pulseEl.className = 'location-pulse-dot error';
      if (helpEl) {
        let msg = '';
        if (err.code === 1) {
          msg = '⚠️ <strong>Location access blocked:</strong><br>' +
            '• <strong>In Browser:</strong> Click the settings icon (or 🔒) next to <code>localhost:8000</code> in your URL bar and set <strong>Location</strong> to <strong>Allow</strong>.<br>' +
            '• <strong>On Mac:</strong> Open <em>System Settings &gt; Privacy &amp; Security &gt; Location Services</em> and toggle your browser <strong>ON</strong>.<br>' +
            '• <em>Alternatively:</em> Type your area/landmark in the search box below or click anywhere on the map!';
        } else if (err.code === 2) {
          msg = '⚠️ <strong>Location unavailable:</strong> Positioning signal could not be determined. Turn on Wi-Fi or search your area below.';
        } else if (err.code === 3) {
          msg = '⚠️ <strong>Location request timed out:</strong> Try clicking GPS Pinpoint again with Wi-Fi on, or type your area below.';
        } else {
          msg = `⚠️ <strong>GPS Notice:</strong> ${err.message || 'Unable to retrieve location.'} You can type your location below or click on the map.`;
        }
        helpEl.innerHTML = `<span>${msg}</span>`;
        helpEl.classList.remove('hidden');
      }
    };

    navigator.geolocation.getCurrentPosition(
      async (position) => {
        const lat = position.coords.latitude;
        const lng = position.coords.longitude;
        if (helpEl) helpEl.classList.add('hidden');
        await this.setUserExactLocation(lat, lng, 'GPS Pinpoint', 16, true);
      },
      (err) => {
        if (err.code === 2 || err.code === 3) {
          navigator.geolocation.getCurrentPosition(
            async (pos) => {
              const lat = pos.coords.latitude;
              const lng = pos.coords.longitude;
              if (helpEl) helpEl.classList.add('hidden');
              await this.setUserExactLocation(lat, lng, 'GPS Approximate', 15, true);
            },
            (err2) => {
              showGpsError(err2);
            },
            { enableHighAccuracy: false, timeout: 10000, maximumAge: 60000 }
          );
        } else {
          showGpsError(err);
        }
      },
      { enableHighAccuracy: true, timeout: 8000, maximumAge: 0 }
    );
  },

  async detectUserLocation(userInitiated = false) {
    // 1. Immediately get location from backend (guaranteed, not blocked)
    let initialDetected = false;
    try {
      const serverLoc = await API.getMyLocation();
      if (serverLoc && serverLoc.latitude && serverLoc.longitude) {
        const cityLabel = `${serverLoc.city}, ${serverLoc.region}`;
        await this.setUserExactLocation(serverLoc.latitude, serverLoc.longitude, cityLabel, 13, false);
        initialDetected = true;
      }
    } catch (e) {
      console.warn('Backend location fetch notice:', e);
    }

    // 2. Refine with GPS if available and permitted
    if ('geolocation' in navigator) {
      navigator.geolocation.getCurrentPosition(
        async (position) => {
          const lat = position.coords.latitude;
          const lng = position.coords.longitude;
          await this.setUserExactLocation(lat, lng, 'GPS Pinpoint', 15, true);
        },
        (err) => {
          console.warn('GPS refine notice:', err.message);
          if (!initialDetected) {
            this.setUserExactLocation(22.7179, 75.8333, 'Indore, Madhya Pradesh', 13, false);
          }
        },
        { enableHighAccuracy: true, timeout: 6000, maximumAge: 30000 }
      );
    } else if (!initialDetected) {
      await this.setUserExactLocation(22.7179, 75.8333, 'Indore, Madhya Pradesh', 13, false);
    }
  },

  async handleCityChange(selectedKey) {
    const customGroup = document.getElementById('custom-city-group');
    if (selectedKey === 'auto') {
      if (customGroup) customGroup.classList.add('hidden');
      await this.detectUserLocation(true);
      return;
    }
    if (selectedKey === 'custom') {
      if (customGroup) {
        customGroup.classList.remove('hidden');
        document.getElementById('custom-city-input').focus();
      }
      return;
    }
    if (customGroup) customGroup.classList.add('hidden');

    const preset = this.CITY_PRESETS[selectedKey];
    if (preset) {
      this.state.userCoords = { lat: preset.lat, lng: preset.lng };
      this.state.userLocationLabel = preset.name;

      const statusEl = document.getElementById('current-location-status');
      const pulseEl = document.getElementById('location-pulse-indicator');
      if (statusEl) statusEl.innerHTML = `<strong>📍 Region:</strong> ${preset.name}`;
      if (pulseEl) pulseEl.className = 'location-pulse-dot ready';

      if (this.state.map) {
        this.state.map.flyTo([preset.lat, preset.lng], 13, { duration: 1.0 });

        if (this.state.userLocationMarker) {
          this.state.map.removeLayer(this.state.userLocationMarker);
        }
        if (this.state.userAccuracyCircle) {
          this.state.map.removeLayer(this.state.userAccuracyCircle);
        }

        const userIcon = L.divIcon({
          className: 'user-pulse-marker-wrapper',
          html: `<div class="pulse-ring"></div><div class="user-pulse-core">📍</div>`,
          iconSize: [36, 36],
          iconAnchor: [18, 18],
          popupAnchor: [0, -18]
        });

        this.state.userLocationMarker = L.marker([preset.lat, preset.lng], { icon: userIcon })
          .addTo(this.state.map)
          .bindPopup(`<strong>📍 Selected Region</strong><br><span>${preset.name}</span>`)
          .openPopup();
      }

      await this.filterMapProviders();
    }
  },

  async applyCustomCity() {
    const input = document.getElementById('custom-city-input');
    const query = (input.value || '').trim();
    if (!query) return;

    const statusEl = document.getElementById('current-location-status');
    if (statusEl) statusEl.textContent = `Searching "${query}"...`;

    try {
      const res = await fetch(`https://nominatim.openstreetmap.org/search?format=json&q=${encodeURIComponent(query)}&limit=1`);
      if (res.ok) {
        const data = await res.json();
        if (data && data.length > 0) {
          const lat = parseFloat(data[0].lat);
          const lng = parseFloat(data[0].lon);
          const name = data[0].display_name.split(',').slice(0, 2).join(',');

          this.state.userCoords = { lat, lng };
          this.state.userLocationLabel = name;

          if (statusEl) statusEl.innerHTML = `<strong>📍 Location:</strong> ${name}`;
          if (this.state.map) {
            this.state.map.flyTo([lat, lng], 13, { duration: 1.0 });

            if (this.state.userLocationMarker) this.state.map.removeLayer(this.state.userLocationMarker);
            if (this.state.userAccuracyCircle) this.state.map.removeLayer(this.state.userAccuracyCircle);

            const userIcon = L.divIcon({
              className: 'user-pulse-marker-wrapper',
              html: `<div class="pulse-ring"></div><div class="user-pulse-core">📍</div>`,
              iconSize: [36, 36],
              iconAnchor: [18, 18],
              popupAnchor: [0, -18]
            });

            this.state.userLocationMarker = L.marker([lat, lng], { icon: userIcon })
              .addTo(this.state.map)
              .bindPopup(`<strong>📍 ${name}</strong>`)
              .openPopup();
          }

          await this.filterMapProviders();
          return;
        }
      }
      alert(`Location "${query}" could not be found. Please try another city.`);
    } catch (e) {
      console.warn('Geocoding error:', e);
      alert('Error searching for city. Please check internet connection.');
    }
  },

  haversineKm(lat1, lon1, lat2, lon2) {
    const R = 6371;
    const dLat = (lat2 - lat1) * Math.PI / 180;
    const dLon = (lon2 - lon1) * Math.PI / 180;
    const a = Math.sin(dLat / 2) * Math.sin(dLat / 2) +
              Math.cos(lat1 * Math.PI / 180) * Math.cos(lat2 * Math.PI / 180) *
              Math.sin(dLon / 2) * Math.sin(dLon / 2);
    const c = 2 * Math.atan2(Math.sqrt(a), Math.sqrt(1 - a));
    return Math.round(R * c * 10) / 10;
  },

  async discoverAllLocalClinics() {
    const btn = document.getElementById('btn-discover-osm');
    const btnText = document.getElementById('btn-discover-osm-text');
    if (!this.state.userCoords) {
      alert('Please set your location on the map first.');
      return;
    }

    const { lat, lng } = this.state.userCoords;
    const radiusVal = parseFloat(document.getElementById('map-radius-filter').value) || 25.0;
    const radiusMeters = Math.min(Math.round(radiusVal * 1000), 25000);

    if (btnText) btnText.textContent = 'Scanning live OpenStreetMap for clinics...';
    if (btn) btn.disabled = true;

    try {
      const query = `[out:json][timeout:10];(node["amenity"="hospital"](around:${radiusMeters},${lat},${lng});node["amenity"="clinic"](around:${radiusMeters},${lat},${lng});node["healthcare"="clinic"](around:${radiusMeters},${lat},${lng});way["amenity"="hospital"](around:${radiusMeters},${lat},${lng}););out center 40;`;
      const url = `https://overpass-api.de/api/interpreter?data=${encodeURIComponent(query)}`;
      
      const controller = new AbortController();
      const timer = setTimeout(() => controller.abort(), 9000);
      const resp = await fetch(url, { signal: controller.signal });
      clearTimeout(timer);

      if (resp.ok) {
        const data = await resp.json();
        const elements = data.elements || [];
        const newClinics = [];
        
        elements.forEach((el, i) => {
          const elLat = el.lat || (el.center && el.center.lat);
          const elLng = el.lon || (el.center && el.center.lon);
          const tags = el.tags || {};
          const name = tags.name || tags['name:en'];
          if (!name || !elLat || !elLng) return;

          const dist = this.haversineKm(lat, lng, elLat, elLng);
          newClinics.push({
            id: 20000 + i,
            name: name,
            facility_type: tags.amenity === 'hospital' ? 'Hospital' : 'Community Clinic',
            specialties: [tags['healthcare:speciality'] || tags.healthcare || 'General Medicine'],
            latitude: elLat,
            longitude: elLng,
            address: tags['addr:street'] ? `${tags['addr:street']}, ${tags['addr:city'] || ''}` : `${name}, Local Vicinity`,
            phone: tags.phone || tags['contact:phone'] || 'Call Reception / Inquiry',
            is_emergency_24x7: tags.emergency === 'yes',
            rating: 4.5,
            distance_km: dist,
            is_osm_live: true,
          });
        });

        this.state.liveOsmFacilities = newClinics;
        await this.filterMapProviders();
        if (btnText) btnText.textContent = `✅ Added ${newClinics.length} Live OpenStreetMap Clinics`;
      } else {
        if (btnText) btnText.textContent = 'All 40+ Verified Hospitals Loaded (OSM busy)';
      }
    } catch (e) {
      console.warn('Live OSM scan notice:', e);
      if (btnText) btnText.textContent = 'All 40+ Verified Hospitals Active';
    } finally {
      if (btn) btn.disabled = false;
      setTimeout(() => {
        if (btnText) btnText.textContent = 'Scan Community Clinics & Dispensaries (Live OSM)';
      }, 5000);
    }
  },

  async filterMapProviders() {
    const query = (document.getElementById('map-search-query').value || '').trim();
    const spec = document.getElementById('map-specialty-filter').value;
    const radius = parseFloat(document.getElementById('map-radius-filter').value) || 25.0;

    const params = {
      radius_km: radius,
      specialty: spec || null,
      q: query || null,
    };

    if (this.state.userCoords) {
      params.lat = this.state.userCoords.lat;
      params.lng = this.state.userCoords.lng;
    } else {
      params.city = 'Indore';
    }

    try {
      const data = await API.getNearbyFacilities(params);
      let facilities = (data && data.facilities) ? [...data.facilities] : [];

      // Merge dynamic OpenStreetMap facilities if available
      if (this.state.liveOsmFacilities && this.state.liveOsmFacilities.length > 0) {
        const existingNames = new Set(facilities.map(f => f.name.toLowerCase().replace(/[^a-z0-9]/g, '')));
        const extra = this.state.liveOsmFacilities.filter(osmFac => {
          const cleanName = osmFac.name.toLowerCase().replace(/[^a-z0-9]/g, '');
          const isDuplicate = Array.from(existingNames).some(n => cleanName.includes(n) || n.includes(cleanName));
          const matchRadius = osmFac.distance_km <= radius;
          const matchQuery = !query || osmFac.name.toLowerCase().includes(query.toLowerCase()) || osmFac.address.toLowerCase().includes(query.toLowerCase());
          return !isDuplicate && matchRadius && matchQuery;
        });
        facilities = [...facilities, ...extra];
        facilities.sort((a, b) => (a.distance_km || 0) - (b.distance_km || 0));
      }

      this.renderMapProviders(facilities);
    } catch (err) {
      console.warn('API provider search error, using local fallback:', err);
      const filtered = this.state.providers.filter(p => {
        const matchQuery = !query || p.name.toLowerCase().includes(query.toLowerCase()) || p.address.toLowerCase().includes(query.toLowerCase());
        const matchSpec = !spec || p.specialty === spec;
        return matchQuery && matchSpec;
      });
      this.renderMapProviders(filtered);
    }
  },

  focusProvider(id) {
    const marker = this.state.mapMarkers.find(m => m._facilityId === id);
    if (marker && this.state.map) {
      this.state.map.setView(marker.getLatLng(), 15, { animate: true });
      marker.openPopup();
    }
  },

  renderMapProviders(providers) {
    const listEl = document.getElementById('providers-list-container');
    const countEl = document.getElementById('providers-count-text');
    if (!listEl) return;

    countEl.textContent = `Showing ${providers.length} healthcare facilities nearby`;

    // Clear existing facility markers
    this.state.mapMarkers.forEach(m => this.state.map.removeLayer(m));
    this.state.mapMarkers = [];

    if (providers.length === 0) {
      listEl.innerHTML = '<div style="padding: 1.5rem; text-align: center; color: var(--color-text-muted);">No matching facilities found within this radius. Try selecting "All Specialties" or expanding search radius to 50 km / 100 km.</div>';
      return;
    }

    listEl.innerHTML = providers.map(p => `
      <div class="provider-card" onclick="App.focusProvider(${p.id})">
        <div class="provider-header">
          <span class="provider-name">${p.name}</span>
          <span class="provider-dist">${p.distance_km !== undefined ? p.distance_km + ' km' : (p.dist || '')}</span>
        </div>
        <div class="provider-specialty">
          ${(p.specialties || [p.specialty]).slice(0, 2).join(', ')} • ${p.rating} ★
          ${p.is_osm_live ? '<span class="pill" style="background:#e0f2fe; color:#0284c7; font-size:0.65rem; margin-left:4px;">OSM Live</span>' : ''}
        </div>
        <div class="provider-address" style="font-size: 0.78rem; color: var(--color-text-muted);">${p.address}</div>
        <div class="provider-footer">
          <a href="tel:${p.phone}" class="provider-phone" onclick="App.recordFacilityAction(${p.id}, 'call')">📞 ${p.phone}</a>
          <span class="pill ${p.is_emergency_24x7 ? 'critical' : ''}">${p.is_emergency_24x7 ? '24/7 ER' : 'Day Clinic'}</span>
        </div>
      </div>
    `).join('');

    // Add map markers
    if (this.state.map) {
      providers.forEach(p => {
        const lat = p.latitude || p.lat;
        const lng = p.longitude || p.lng;
        if (lat && lng) {
          const marker = L.marker([lat, lng]).addTo(this.state.map);
          marker._facilityId = p.id;
          marker.bindPopup(`
            <strong>${p.name}</strong><br>
            ${(p.specialties || [p.specialty]).slice(0, 2).join(', ')}<br>
            ${p.address}<br>
            ${p.distance_km !== undefined ? '<em>Distance: ' + p.distance_km + ' km</em><br>' : ''}
            <a href="tel:${p.phone}">Call: ${p.phone}</a>
          `);
          this.state.mapMarkers.push(marker);
        }
      });
    }
  },

  async recordFacilityAction(providerId, actionType) {
    if (this.state.lastAssessment && this.state.lastAssessment.assessment) {
      const p = this.state.providers.find(x => x.id === providerId);
      if (p) {
        try {
          await API.addHealthcareSearch(this.state.lastAssessment.assessment.id, {
            facility_name: p.name,
            specialty: p.specialty || (p.specialties && p.specialties[0]),
            location: p.address,
            distance: p.dist || (p.distance_km ? `${p.distance_km} km` : 'Near user'),
            phone: p.phone,
          });
        } catch (e) {
          console.warn('Failed to record search:', e);
        }
      }
    }
  },


  // Patient History View
  async loadHistoryView() {
    const user = this.state.user;
    if (!user) {
      document.getElementById('history-profile-username').textContent = 'Guest Patient';
      document.getElementById('history-profile-email').innerHTML = 'Sign in or register to persist your assessments across devices. <button class="btn btn-teal btn-sm" onclick="App.openAuthModal(\'login\')">Sign In</button>';
      document.getElementById('history-assessments-list').innerHTML = '<span class="tag-placeholder">Sign in to view your saved consultation history.</span>';
      return;
    }

    document.getElementById('history-profile-username').textContent = user.full_name || user.username;
    document.getElementById('history-profile-email').textContent = user.email;

    try {
      const history = await API.getHistory();
      document.getElementById('history-stat-count').textContent = history.length;
      if (history.length > 0) {
        document.getElementById('history-stat-last').textContent = new Date(history[0].created_at).toLocaleDateString();
      }

      const listContainer = document.getElementById('history-assessments-list');
      if (history.length === 0) {
        listContainer.innerHTML = '<span class="tag-placeholder">No past assessments found. Complete a consultation to record an assessment.</span>';
        return;
      }

      listContainer.innerHTML = history.map(item => `
        <div class="timeline-card">
          <div class="timeline-card-header">
            <div>
              <span class="timeline-title">${item.predicted_condition || 'Clinical Assessment'}</span>
              <span class="risk-tier-badge ${item.risk_level.toLowerCase()}">${item.risk_level} RISK</span>
            </div>
            <span class="timeline-date">${new Date(item.created_at).toLocaleDateString()}</span>
          </div>
          <p><strong>Symptoms:</strong> ${(item.symptoms || []).join(', ')} (Duration: ${item.duration || 'N/A'}, Severity: ${item.severity || 'N/A'})</p>
          <p><strong>Specialty:</strong> ${item.suggested_specialty || 'General Physician'}</p>
          <div style="margin-top: 0.5rem; display: flex; justify-content: flex-end;">
            <button class="btn btn-ghost btn-sm" onclick="App.deleteHistoryItem(${item.id})">Delete</button>
          </div>
        </div>
      `).join('');
    } catch (err) {
      console.error(err);
    }
  },

  async deleteHistoryItem(id) {
    if (confirm('Are you sure you want to delete this assessment record?')) {
      try {
        await API.deleteAssessment(id);
        this.loadHistoryView();
      } catch (err) {
        alert(err.message);
      }
    }
  },
};

// Initialize on DOMContentLoaded
window.addEventListener('DOMContentLoaded', () => App.init());
