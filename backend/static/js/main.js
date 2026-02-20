// State Management
const state = {
    lang: 'en',
    symptoms: [],
    prediction: null,
    user: null,
    translations: {
        en: {
            title: "RuralHealth AI",
            start: "Start Checkup Now",
            welcome: "Hello! I'm your health assistant. Please describe your symptoms.",
            typing: "AI is thinking...",
            placeholder: "Type your symptoms here...",
            send: "Send",
            disease: "Predicted Disease",
            confidence: "Confidence",
            severity: "Severity",
            precautions: "Precautions",
            download: "Download PDF",
            close: "Close"
        },
        hi: {
            title: "ग्रामीण स्वास्थ्य एआई",
            start: "चेकअप शुरू करें",
            welcome: "नमस्ते! मैं आपका स्वास्थ्य सहायक हूँ। कृपया अपने लक्षण बताएं।",
            typing: "एआई सोच रहा है...",
            placeholder: "अपने लक्षण यहाँ लिखें...",
            send: "भेजें",
            disease: "अनुमानित रोग",
            confidence: "विश्वास",
            severity: "गंभीरता",
            precautions: "सावधानियां",
            download: "पीडीएफ डाउनलोड करें",
            close: "बंद करें"
        },
        ta: {
            title: "கிராமப்புற சுகாதார AI",
            start: "சோதனையைத் தொடங்கவும்",
            welcome: "வணக்கம்! நான் உங்கள் சுகாதார உதவியாளர். உங்கள் அறிகுறிகளை விவரிக்கவும்.",
            typing: "AI சிந்திக்கிறது...",
            placeholder: "உங்கள் அறிகுறிகளை இங்கே தட்டச்சு செய்யவும்...",
            send: "அனுப்பு",
            disease: "கணிக்கப்பட்ட நோய்",
            confidence: "நம்பிக்கை",
            severity: "தீவிரம்",
            precautions: "முன்னெச்சரிக்கைகள்",
            download: "PDF பதிவிறக்கவும்",
            close: "மூடு"
        }
    }
};

// DOM Elements
// DOM Elements - Using getters to ensure elements are found even if script loads early
const dom = {
    get msgContainer() { return document.getElementById('chat-messages'); },
    get form() { return document.getElementById('chat-form'); },
    get input() { return document.getElementById('symptom-input'); },
    get typingIndicator() { return document.getElementById('typing-indicator'); },
    get modal() { return document.getElementById('report-modal'); },
    get langBtn() { return document.getElementById('current-lang'); },
    get themeToggle() { return document.getElementById('theme-toggle'); },
    get themeIcon() { return document.getElementById('theme-icon'); }
};

// API Interactions
const api = {
    async predict(symptoms) {
        try {
            const response = await fetch('/api/predict', {
                method: 'POST',
                headers: { 'Content-Type': 'application/json' },
                body: JSON.stringify({ symptoms })
            });
            if (!response.ok) throw new Error('Prediction failed');
            return await response.json();
        } catch (error) {
            console.error(error);
            return null;
        }
    },

    async downloadReport(user_name, prediction_data) {
        try {
            const response = await fetch('/api/report', {
                method: 'POST',
                headers: { 'Content-Type': 'application/json' },
                body: JSON.stringify({ user_name, prediction_data })
            });
            if (!response.ok) throw new Error('Download failed');
            const blob = await response.blob();
            const url = window.URL.createObjectURL(blob);
            const a = document.createElement('a');
            a.href = url;
            a.download = `HealthReport_${new Date().toISOString()}.pdf`;
            document.body.appendChild(a);
            a.click();
            a.remove();
        } catch (error) {
            console.error(error);
            alert("Failed to download report");
        }
    },

    async sendMessage(message) {
        if (!message) return;

        frontend.addMessage(message, 'user');
        dom.input.value = '';
        dom.input.focus();

        // --- CHAT FLOW LOGIC (3-Symptom Strict) ---

        // 1. Check for "Restart" / "Reset" commands
        if (['restart', 'reset', 'clear'].includes(message.toLowerCase().trim())) {
            window.resetChat();
            return;
        }

        // 2. Validate Symptom
        const loadingId = frontend.showLoading();

        try {
            const valRes = await fetch('/api/validate', {
                method: 'POST',
                headers: { 'Content-Type': 'application/json' },
                body: JSON.stringify({ text: message, lang: state.lang })
            });

            const validation = await valRes.json();
            frontend.removeLoading(loadingId);

            if (validation.valid) {
                const symptom = validation.match;

                // Avoid duplicates
                if (!state.symptoms.includes(symptom)) {
                    state.symptoms.push(symptom);

                    const count = state.symptoms.length;

                    if (count < 3) {
                        // "Noted (1/3)"
                        const reply = `Noted <b>${symptom}</b> (${count}/3). Please tell me symptom ${count + 1}.`;
                        frontend.addMessage(reply, 'bot');
                        await this.saveMessage('bot', reply);
                    } else {
                        // "Noted (3/3)" -> Trigger
                        const reply = `Noted <b>${symptom}</b> (3/3). Analyzing your symptoms...`;
                        frontend.addMessage(reply, 'bot');
                        await this.saveMessage('bot', reply);

                        // Artificial delay
                        await new Promise(r => setTimeout(r, 800));
                        await this.finalizeDiagnosis();
                    }
                } else {
                    frontend.addMessage(`I already have <b>${symptom}</b>. Please give me a different one.`, 'bot');
                }
            } else {
                // Invalid
                frontend.addMessage(`I didn't recognize '<b>${message}</b>'. Please describe a symptom (e.g., headache, fever).`, 'bot');
            }

        } catch (e) {
            console.error(e);
            frontend.removeMessage(loadingId);
            frontend.addMessage(`Error: ${e.message}.`, 'bot');
        }
    },

    async finalizeDiagnosis() {
        if (state.symptoms.length === 0) return;

        const loadingId = frontend.showLoading();
        try {
            const response = await fetch('/api/predict', {
                method: 'POST',
                headers: { 'Content-Type': 'application/json' },
                body: JSON.stringify({ symptoms: state.symptoms })
            });

            frontend.removeLoading(loadingId);
            const result = await response.json();

            if (result.success || result.disease) {
                state.prediction = result;

                // Format precautions as HTML List
                const precautionsHtml = result.precautions.map(p => `<li>${p[state.lang] || p['en']}</li>`).join('');

                const description = result.description[state.lang] || result.description['en'];
                const diseaseName = result.disease;

                // Comparison Table
                let comparisonHtml = '';
                if (result.comparison && result.comparison.length > 0) {
                    const rows = result.comparison.map(c => {
                        const confClass = c.confidence > 80 ? 'text-green-600' : (c.confidence > 50 ? 'text-yellow-600' : 'text-red-600');
                        return `
                            <tr class="border-b border-gray-100 dark:border-slate-700 last:border-0 hover:bg-gray-50 dark:hover:bg-slate-700/50 transition">
                                <td class="py-2 px-2 text-xs font-medium text-gray-700 dark:text-gray-300">${c.model}</td>
                                <td class="py-2 px-2 text-xs text-gray-600 dark:text-gray-400">${c.disease}</td>
                                <td class="py-2 px-2 text-xs font-bold ${confClass} text-right">${c.confidence.toFixed(1)}%</td>
                            </tr>
                        `;
                    }).join('');

                    comparisonHtml = `
                        <div class="mt-3 bg-white dark:bg-slate-800 rounded-lg border border-gray-100 dark:border-slate-700 overflow-hidden">
                            <div class="bg-gray-50 dark:bg-slate-700/50 px-3 py-2 border-b border-gray-100 dark:border-slate-700">
                                <h4 class="text-xs font-bold text-gray-500 dark:text-gray-400 uppercase flex items-center gap-2">
                                    <i class="fa-solid fa-chart-simple"></i> Model Analysis
                                </h4>
                            </div>
                            <table class="w-full text-left">
                                <thead>
                                    <tr class="bg-gray-50/50 dark:bg-slate-800/50 text-xs text-gray-400 uppercase">
                                        <th class="py-1 px-2 font-medium">Model</th>
                                        <th class="py-1 px-2 font-medium">Result</th>
                                        <th class="py-1 px-2 font-medium text-right">Conf.</th>
                                    </tr>
                                </thead>
                                <tbody>
                                    ${rows}
                                </tbody>
                            </table>
                        </div>
                    `;
                }

                // Rich HTML Response
                const replyHtml = `
                    <div class="space-y-3">
                        <div class="border-b border-gray-100 pb-2">
                            <h3 class="font-bold text-lg text-emerald-600 flex items-center gap-2">
                                <i class="fa-solid fa-user-doctor"></i> ${diseaseName}
                            </h3>
                        </div>
                        <p class="text-sm text-gray-700 dark:text-gray-300 leading-relaxed">
                            ${description}
                        </p>
                        <div class="bg-emerald-50 dark:bg-emerald-900/20 p-3 rounded-lg">
                            <strong class="block text-xs font-bold text-emerald-700 dark:text-emerald-400 uppercase mb-2">Precautions</strong>
                            <ul class="list-disc pl-4 text-sm text-gray-600 dark:text-gray-300 space-y-1">
                                ${precautionsHtml}
                            </ul>
                        </div>
                        ${comparisonHtml}
                        <button onclick="frontend.downloadReport()" class="w-full mt-2 bg-primary hover:bg-emerald-600 text-white py-2 rounded-lg text-sm shadow-md transition flex items-center justify-center gap-2">
                            <i class="fa-solid fa-file-pdf"></i> Download Report
                        </button>
                    </div>
                `;

                frontend.addMessage(replyHtml, 'bot');
                await this.saveMessage('bot', replyHtml);

                frontend.updateInfoTab(result);

                // Automatically open the detailed modal as well for a "premium" feel
                if (typeof frontend.openModal === 'function') {
                    frontend.openModal();
                }

                // Reset symptoms for next round
                state.symptoms = [];

            } else {
                frontend.addMessage("I couldn't identify a specific condition. Please consult a doctor.", 'bot');
                state.symptoms = [];
            }
        } catch (e) {
            console.error(e);
            frontend.removeMessage(loadingId);
            frontend.addMessage("Error getting diagnosis.", 'bot');
        }
    },

    async saveMessage(sender, message) {
        try {
            await fetch('/api/chat/message', {
                method: 'POST',
                headers: { 'Content-Type': 'application/json' },
                body: JSON.stringify({
                    sender,
                    message,
                    session_id: null // Disable session association for stability
                })
            });
        } catch (e) {
            console.error("Failed to save message", e);
        }
    },

    async getHistory() {
        // Return empty for now to avoid session complexity
        return [];
    },

    async handleParams(e) {
        e.preventDefault();
        const inputVal = dom.input.value.trim();
        if (!inputVal) return;
        await this.sendMessage(inputVal);
    },

    // Legacy support wrappers
    async createSession(title) { return null; },
    async getSessions() { return []; },
    async deleteSession(id) { return { success: true }; },

    async getInfo() {
        try {
            const response = await fetch('/api/info');
            return await response.json();
        } catch (e) { console.error(e); return {}; }
    }
};

// UI Interactions
const frontend = {
    addMessage(text, sender, save = true) {
        // Ensure container exists
        const container = dom.msgContainer;
        if (!container) return;

        const div = document.createElement('div');
        div.className = `flex ${sender === 'user' ? 'justify-end' : 'justify-start'}`;

        const bubble = document.createElement('div');
        bubble.className = sender === 'user'
            ? 'bg-primary text-white p-4 rounded-2xl rounded-tr-none shadow-md max-w-[80%] animate-fade-in-up'
            : 'bg-white dark:bg-slate-800 p-4 rounded-2xl rounded-tl-none shadow-sm max-w-[80%] text-gray-800 dark:text-gray-200 animate-fade-in-up';

        bubble.innerHTML = text; // Allow HTML for formatted response
        div.appendChild(bubble);
        container.appendChild(div);
        frontend.scrollToBottom();
        if (save) {
            // saveMessage is handled by caller usually, but if independent call:
            // api.saveMessage(sender, text); 
            // We removed recursive save from here to avoid duplication if caller handles it
        }
    },

    async scrollToBottom() {
        if (dom.msgContainer) {
            dom.msgContainer.scrollTop = dom.msgContainer.scrollHeight;
        }
    },

    showLoading() {
        const div = document.createElement('div');
        div.className = `flex w-full mb-4 justify-start`;
        div.innerHTML = `
            <div class="bg-white dark:bg-slate-700 rounded-2xl rounded-bl-none px-4 py-3 shadow-sm border border-gray-100 dark:border-slate-600">
                <div class="flex space-x-1">
                    <div class="w-2 h-2 bg-gray-400 rounded-full animate-bounce"></div>
                    <div class="w-2 h-2 bg-gray-400 rounded-full animate-bounce" style="animation-delay: 0.2s"></div>
                    <div class="w-2 h-2 bg-gray-400 rounded-full animate-bounce" style="animation-delay: 0.4s"></div>
                </div>
            </div>
        `;
        dom.msgContainer.appendChild(div);
        frontend.scrollToBottom();
        return div;
    },

    removeLoading(element) {
        if (element && element.parentNode) {
            element.parentNode.removeChild(element);
        }
    },

    removeMessage(id) {
        this.removeLoading(id);
    },

    async initSidebar() {
        // Revert to Diagnoses List
        const sidebar = document.getElementById('session-list');
        if (!sidebar) return;

        sidebar.innerHTML = '';

        try {
            const response = await fetch('/api/chat/diagnoses');
            const diagnoses = await response.json();

            if (diagnoses.length > 0) {
                const divider = document.createElement('div');
                divider.className = "text-xs text-gray-400 px-3 mt-4 mb-2 uppercase font-bold diagnosis-divider";
                divider.innerText = "Past Diagnoses";
                sidebar.appendChild(divider);

                diagnoses.forEach(d => {
                    const btn = document.createElement('button');
                    btn.className = "w-full text-left px-3 py-2 rounded-lg text-gray-600 dark:text-gray-400 hover:bg-gray-50 dark:hover:bg-slate-700 text-sm transition truncate diagnosis-item";
                    btn.innerHTML = `<i class="fa-solid fa-file-medical mr-2 text-emerald-500"></i> ${d.disease} <span class="text-xs text-gray-400 ml-1">(${d.date})</span>`;
                    btn.onclick = () => frontend.loadDiagnosis(d.id);
                    sidebar.appendChild(btn);
                });
            } else {
                sidebar.innerHTML = '<p class="text-xs text-center text-gray-400 mt-4">No history yet.</p>';
            }
        } catch (e) {
            console.error("Failed to load sidebar", e);
        }
    },

    async startNewSession(clearUI = true) {
        // No-op for rollback
        if (clearUI) {
            dom.msgContainer.innerHTML = '';
            const welcome = state.translations[state.lang].welcome;
            frontend.addMessage(welcome, 'bot', false);
        }
    },

    async loadSession(id) { }, // No-op
    async deleteSession(id) { }, // No-op

    async loadDiagnosis(id) {
        alert("This diagnosis is preserved in your chat history. Scroll up to review the conversation!");
    },

    openModal() {
        if (!state.prediction) return;
        const p = state.prediction;
        document.getElementById('modal-disease').innerText = p.disease;
        document.getElementById('modal-confidence').innerText = `${p.confidence.toFixed(1)}%`;

        const sevEl = document.getElementById('modal-severity');
        sevEl.innerText = p.severity;
        if (p.severity === 'High') sevEl.className = "px-2 py-1 rounded text-xs font-semibold bg-red-100 text-red-800";
        else if (p.severity === 'Medium') sevEl.className = "px-2 py-1 rounded text-xs font-semibold bg-orange-100 text-orange-800";
        else sevEl.className = "px-2 py-1 rounded text-xs font-semibold bg-green-100 text-green-800";

        dom.modal.classList.remove('hidden');
    },

    closeModal() {
        dom.modal.classList.add('hidden');
    },

    downloadReport() {
        if (!state.prediction) return;
        const userName = (typeof CURRENT_USER_NAME !== 'undefined') ? CURRENT_USER_NAME : 'User';
        api.downloadReport(userName, state.prediction);
    },

    async initInfoTab() {
        const info = await api.getInfo();
        const tab = document.getElementById('info-tab-content');
        if (tab && info) {
            // Update info tab
            tab.innerHTML = `
                <div class="flex gap-4 text-xs text-gray-500 dark:text-gray-400">
                    <span><i class="fa-solid fa-microchip"></i> ${info.model}</span>
                    <span><i class="fa-solid fa-database"></i> ${info.diseases} Diseases</span>
                    <span><i class="fa-solid fa-notes-medical"></i> ${info.symptoms} Symptoms</span>
                    <span><i class="fa-solid fa-bullseye"></i> Acc: ${info.accuracy}</span>
                </div>
            `;

            // Also update the welcome message model name if it exists
            const modelDisplay = document.getElementById('model-name-display');
            if (modelDisplay) {
                modelDisplay.innerText = info.model;
            }
        }
    },

    async initAutocomplete() {
        if (!document.getElementById('symptoms-list')) return;
        try {
            const response = await fetch('/api/symptoms');
            const data = await response.json();
            if (data.success && data.symptoms) {
                const datalist = document.getElementById('symptoms-list');
                datalist.innerHTML = ''; // Clear existing
                data.symptoms.forEach(symptom => {
                    const option = document.createElement('option');
                    option.value = symptom;
                    datalist.appendChild(option);
                });
            }
        } catch (e) {
            console.error("Failed to load symptoms for autocomplete", e);
        }
    },

    updateInfoTab(result) {
        const tab = document.getElementById('info-tab-content');
        if (tab && result) {
            tab.innerHTML = `
                <div class="flex gap-4 text-xs text-emerald-600 dark:text-emerald-400 font-medium">
                    <span><i class="fa-solid fa-virus"></i> ${result.disease}</span>
                    <span class="group relative cursor-help">
                        <i class="fa-solid fa-chart-line"></i> Conf: ${result.confidence.toFixed(1)}%
                        <span class="absolute bottom-full left-1/2 transform -translate-x-1/2 mb-2 w-48 bg-gray-900 text-white text-xs rounded py-1 px-2 opacity-0 group-hover:opacity-100 transition-opacity pointer-events-none z-50 text-center">
                            Indicates how likely this prediction is correct based on your symptoms.
                        </span>
                    </span>
                    <span><i class="fa-solid fa-triangle-exclamation"></i> Severity: ${result.severity}</span>
                </div>
            `;
        }
    },

    initTheme() {
        const savedTheme = localStorage.getItem('theme');
        if (savedTheme === 'dark' || (!savedTheme && window.matchMedia('(prefers-color-scheme: dark)').matches)) {
            document.documentElement.classList.add('dark');
            if (dom.themeIcon) dom.themeIcon.className = "fa-solid fa-sun text-lg";
        } else {
            document.documentElement.classList.remove('dark');
            if (dom.themeIcon) dom.themeIcon.className = "fa-solid fa-moon text-lg";
        }

        if (dom.themeToggle) {
            dom.themeToggle.addEventListener('click', () => {
                document.documentElement.classList.toggle('dark');
                const isDark = document.documentElement.classList.contains('dark');
                localStorage.setItem('theme', isDark ? 'dark' : 'light');
                if (dom.themeIcon) dom.themeIcon.className = isDark ? "fa-solid fa-sun text-lg" : "fa-solid fa-moon text-lg";
            });
        }
    }
};

// Global Functions
window.changeLang = (lang) => {
    state.lang = lang;
    if (dom.langBtn) dom.langBtn.innerText = lang.toUpperCase();
    const t = state.translations[lang];
    if (dom.input) dom.input.placeholder = t.placeholder;
};

window.resetChat = async () => {
    state.symptoms = [];
    state.prediction = null;
    dom.msgContainer.innerHTML = '';

    // Clear history on backend?? user probably wants to keep history unless explicitly deleted.
    // For now, reset just clears UI. New session.

    const welcome = state.translations[state.lang].welcome;
    frontend.addMessage(welcome, 'bot', true); // User sees new session start
    await frontend.initInfoTab();
};

window.handleLogin = async (e) => {
    e.preventDefault();
    const formData = new FormData(e.target);
    const data = Object.fromEntries(formData.entries());

    try {
        const res = await fetch('/auth/login', {
            method: 'POST',
            headers: { 'Content-Type': 'application/json' },
            body: JSON.stringify(data)
        });
        const result = await res.json();
        if (result.success) {
            window.location.href = '/chat';
        } else {
            alert(result.error || 'Login failed');
        }
    } catch (err) {
        console.error(err);
        alert('Login failed');
    }
};

window.handleSignup = async (e) => {
    e.preventDefault();
    const formData = new FormData(e.target);
    const data = Object.fromEntries(formData.entries());

    try {
        const res = await fetch('/auth/register', {
            method: 'POST',
            headers: { 'Content-Type': 'application/json' },
            body: JSON.stringify(data)
        });
        const result = await res.json();
        if (result.success) {
            alert('Account created! Please log in.');
            toggleAuth('login');
        } else {
            alert(result.error || 'Signup failed');
        }
    } catch (err) {
        console.error(err);
        alert('Signup failed');
    }
}

window.logout = async () => {
    try {
        await fetch('/auth/logout');
        window.location.href = '/login';
    } catch (e) {
        console.error(e);
        window.location.href = '/login';
    }
};

window.handleGoogleLogin = () => {
    alert("Google Login is a placeholder for this demo.");
};

window.frontend = frontend;
window.api = api;

// Init
document.addEventListener('DOMContentLoaded', async () => {
    frontend.initTheme();
    if (dom.msgContainer) { // Only on chat page
        frontend.initInfoTab();
        frontend.initAutocomplete(); // Load autocomplete data
        frontend.initSidebar(); // Load past diagnoses
        const history = await api.getHistory();
        if (history && history.length > 0) {
            history.forEach(msg => {
                frontend.addMessage(msg.message, msg.sender, false); // Don't re-save history
            });
        } else {
            const welcome = state.translations[state.lang].welcome;
            // Only add welcome if no history, otherwise it's weird
            frontend.addMessage(welcome, 'bot', true);
        }
    }
});
