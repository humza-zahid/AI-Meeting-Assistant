// Google Calendar OAuth 2.0 Simple Authentication
class GoogleCalendarAuth {
    constructor() {
        this.apiBaseUrl = 'http://localhost:8000';
        this.isAuthenticated = false;
        this.userEmail = null;
        this.calendarEvents = [];
        
        this.init();
    }

    async init() {
        console.log('🚀 Initializing Google Calendar Auth...');
        
        // Setup event listeners
        this.setupEventListeners();
        
        // Check if already authenticated
        await this.checkAuthStatus();
        
        // Handle OAuth callback
        this.handleOAuthCallback();
        
        console.log('✅ Google Calendar Auth initialized');
    }

    setupEventListeners() {
        // Google Auth button
        const googleAuthBtn = document.getElementById('google-auth-btn');
        if (googleAuthBtn) {
            googleAuthBtn.addEventListener('click', () => this.startOAuthFlow());
        }

        // View calendar button
        const viewCalendarBtn = document.getElementById('view-calendar-btn');
        if (viewCalendarBtn) {
            viewCalendarBtn.addEventListener('click', () => this.showCalendarDetails());
        }

        // Refresh calendar button
        const refreshCalendarBtn = document.getElementById('refresh-calendar-btn');
        if (refreshCalendarBtn) {
            refreshCalendarBtn.addEventListener('click', () => this.loadCalendarEvents());
        }

        // Logout button
        const logoutBtn = document.getElementById('logout-btn');
        if (logoutBtn) {
            logoutBtn.addEventListener('click', () => this.logout());
        }
    }

    handleOAuthCallback() {
        const urlParams = new URLSearchParams(window.location.search);
        const authStatus = urlParams.get('auth');
        const code = urlParams.get('code');
        
        if (authStatus === 'success') {
            this.showAlert('✅ Authentication successful!', 'success');
            setTimeout(() => this.checkAuthStatus(), 1000);
        } else if (authStatus === 'error') {
            const errorMessage = urlParams.get('message') || 'Authentication failed';
            this.showAlert(`❌ Authentication error: ${errorMessage}`, 'error');
        } else if (code) {
            // Handle OAuth callback with code
            this.showAlert('🔄 Processing authentication...', 'info');
            setTimeout(() => this.checkAuthStatus(), 2000);
        }
    }

    async checkAuthStatus() {
        try {
            console.log('🔍 Checking authentication status...');
            const response = await this.apiCall('/auth/status');
            
            if (response.authenticated) {
                this.isAuthenticated = true;
                this.userEmail = response.user_email;
                
                console.log('✅ User authenticated:', this.userEmail);
                this.showAuthenticatedState();
            } else {
                console.log('❌ User not authenticated');
                this.showUnauthenticatedState();
            }
        } catch (error) {
            console.error('❌ Auth status check failed:', error);
            this.showAlert('Failed to check authentication status', 'error');
        }
    }

    async startOAuthFlow() {
        try {
            console.log('🔄 Starting Google OAuth flow...');
            
            // Show loading state
            this.showLoadingState();
            
            // Get OAuth URL from backend
            const response = await this.apiCall('/auth/connect', 'POST');
            
            if (response.auth_url) {
                console.log('🔗 Redirecting to OAuth URL...');
                // Redirect to Google OAuth
                window.location.href = response.auth_url;
            } else {
                throw new Error('No authorization URL received');
            }
        } catch (error) {
            console.error('❌ OAuth flow failed:', error);
            this.showAlert(`Authentication failed: ${error.message}`, 'error');
            this.hideLoadingState();
        }
    }

    async loadCalendarEvents() {
        try {
            console.log('📅 Loading calendar events...');
            
            const calendarLoading = document.getElementById('calendar-loading');
            const calendarEvents = document.getElementById('calendar-events');
            const noEvents = document.getElementById('no-events');
            
            if (calendarLoading) calendarLoading.style.display = 'block';
            if (calendarEvents) calendarEvents.style.display = 'none';
            if (noEvents) noEvents.style.display = 'none';
            
            // Load events for next 7 days
            const response = await this.apiCall('/calendar/events?days=7');
            this.calendarEvents = response.events || [];
            
            console.log(`✅ Loaded ${this.calendarEvents.length} events`);
            this.displayCalendarEvents();
            this.updateCalendarStats();
            
        } catch (error) {
            console.error('❌ Failed to load calendar events:', error);
            this.showAlert('Failed to load calendar events', 'error');
        }
    }

    displayCalendarEvents() {
        const calendarLoading = document.getElementById('calendar-loading');
        const calendarEvents = document.getElementById('calendar-events');
        const noEvents = document.getElementById('no-events');
        
        if (calendarLoading) calendarLoading.style.display = 'none';
        
        if (this.calendarEvents.length === 0) {
            if (noEvents) noEvents.style.display = 'block';
            if (calendarEvents) calendarEvents.style.display = 'none';
            return;
        }
        
        if (calendarEvents) calendarEvents.style.display = 'block';
        if (noEvents) noEvents.style.display = 'none';
        
        const eventsHtml = this.calendarEvents.map(event => {
            const startTime = new Date(event.start);
            const endTime = new Date(event.end);
            const now = new Date();
            
            let statusClass = 'upcoming';
            let statusText = 'Upcoming';
            let statusIcon = '⏰';
            
            if (startTime <= now && endTime > now) {
                statusClass = 'active';
                statusText = 'Active Now';
                statusIcon = '🔴';
            } else if (endTime <= now) {
                statusClass = 'completed';
                statusText = 'Completed';
                statusIcon = '✅';
            }
            
            return `
                <div class="event-card card">
                    <div class="event-header">
                        <h3 class="event-title">${event.title || 'Untitled Event'}</h3>
                        <span class="event-status status-${statusClass}">
                            ${statusIcon} ${statusText}
                        </span>
                    </div>
                    <div class="event-details">
                        <div class="event-time">
                            <strong>📅 ${startTime.toLocaleDateString()}</strong><br>
                            🕐 ${startTime.toLocaleTimeString()} - ${endTime.toLocaleTimeString()}
                        </div>
                        ${event.location ? `
                            <div class="event-location">
                                <strong>📍 Location:</strong><br>
                                ${event.location}
                            </div>
                        ` : ''}
                        ${event.meeting_url ? `
                            <div class="event-meeting">
                                <strong>🔗 Meeting Link:</strong><br>
                                <a href="${event.meeting_url}" target="_blank" class="meeting-link">
                                    Join Meeting
                                </a>
                            </div>
                        ` : ''}
                        ${event.description ? `
                            <div class="event-description">
                                <strong>📝 Description:</strong><br>
                                ${event.description}
                            </div>
                        ` : ''}
                        ${event.attendees && event.attendees.length > 0 ? `
                            <div class="event-attendees">
                                <strong>👥 Attendees (${event.attendees.length}):</strong><br>
                                ${event.attendees.slice(0, 3).join(', ')}${event.attendees.length > 3 ? '...' : ''}
                            </div>
                        ` : ''}
                    </div>
                </div>
            `;
        }).join('');
        
        calendarEvents.innerHTML = eventsHtml;
    }

    updateCalendarStats() {
        const now = new Date();
        let upcomingCount = 0;
        let activeCount = 0;
        let meetingCount = 0;
        
        this.calendarEvents.forEach(event => {
            const startTime = new Date(event.start);
            const endTime = new Date(event.end);
            
            if (startTime > now) {
                upcomingCount++;
            } else if (startTime <= now && endTime > now) {
                activeCount++;
            }
            
            if (event.meeting_url) {
                meetingCount++;
            }
        });
        
        // Update stat displays
        const totalEventsEl = document.getElementById('total-events');
        const upcomingEventsEl = document.getElementById('upcoming-events');
        const activeEventsEl = document.getElementById('active-events');
        const meetingEventsEl = document.getElementById('meeting-events');
        
        if (totalEventsEl) totalEventsEl.textContent = this.calendarEvents.length;
        if (upcomingEventsEl) upcomingEventsEl.textContent = upcomingCount;
        if (activeEventsEl) activeEventsEl.textContent = activeCount;
        if (meetingEventsEl) meetingEventsEl.textContent = meetingCount;
    }

    showAuthenticatedState() {
        const authSection = document.getElementById('auth-section');
        const loadingState = document.getElementById('loading-state');
        const successState = document.getElementById('success-state');
        const userEmailDisplay = document.getElementById('user-email-display');
        
        if (authSection) authSection.style.display = 'none';
        if (loadingState) loadingState.style.display = 'none';
        if (successState) successState.style.display = 'block';
        if (userEmailDisplay) userEmailDisplay.textContent = `Connected as: ${this.userEmail}`;
        
        this.showAlert(`✅ Successfully connected to Google Calendar as: ${this.userEmail}`, 'success');
    }

    showUnauthenticatedState() {
        const authSection = document.getElementById('auth-section');
        const loadingState = document.getElementById('loading-state');
        const successState = document.getElementById('success-state');
        const calendarSection = document.getElementById('calendar-section');
        
        if (authSection) authSection.style.display = 'block';
        if (loadingState) loadingState.style.display = 'none';
        if (successState) successState.style.display = 'none';
        if (calendarSection) calendarSection.style.display = 'none';
    }

    showLoadingState() {
        const authSection = document.getElementById('auth-section');
        const loadingState = document.getElementById('loading-state');
        const googleAuthBtn = document.getElementById('google-auth-btn');
        
        if (authSection) authSection.style.display = 'none';
        if (loadingState) loadingState.style.display = 'block';
        if (googleAuthBtn) googleAuthBtn.disabled = true;
    }

    hideLoadingState() {
        const authSection = document.getElementById('auth-section');
        const loadingState = document.getElementById('loading-state');
        const googleAuthBtn = document.getElementById('google-auth-btn');
        
        if (authSection) authSection.style.display = 'block';
        if (loadingState) loadingState.style.display = 'none';
        if (googleAuthBtn) googleAuthBtn.disabled = false;
    }

    showCalendarDetails() {
        // Navigate to dashboard.html instead of showing inline calendar
        console.log('🔄 Navigating to dashboard...');
        window.location.href = 'dashboard.html';
    }

    async logout() {
        try {
            await this.apiCall('/auth/logout', 'POST');
            this.isAuthenticated = false;
            this.userEmail = null;
            this.calendarEvents = [];
            this.showUnauthenticatedState();
            this.showAlert('✅ Successfully logged out', 'success');
        } catch (error) {
            console.error('❌ Logout failed:', error);
            this.showAlert('Logout failed', 'error');
        }
    }

    async apiCall(endpoint, method = 'GET', data = null) {
        const url = `${this.apiBaseUrl}${endpoint}`;
        const options = {
            method,
            headers: {
                'Content-Type': 'application/json',
            },
            credentials: 'include',
        };
        
        if (data && method !== 'GET') {
            options.body = JSON.stringify(data);
        }
        
        console.log(`🌐 API Call: ${method} ${url}`);
        
        const response = await fetch(url, options);
        
        if (!response.ok) {
            const errorText = await response.text();
            throw new Error(`HTTP ${response.status}: ${errorText}`);
        }
        
        return await response.json();
    }

    showAlert(message, type = 'info') {
        const alertContainer = document.getElementById('alert-container');
        if (!alertContainer) {
            console.log(`Alert (${type}): ${message}`);
            return;
        }
        
        const alertClass = {
            'success': 'alert-success',
            'error': 'alert-error',
            'warning': 'alert-warning',
            'info': 'alert-info'
        }[type] || 'alert-info';
        
        const alertHtml = `
            <div class="alert ${alertClass}" style="margin-bottom: 1rem;">
                ${message}
            </div>
        `;
        
        alertContainer.innerHTML = alertHtml;
        
        // Auto-hide success messages after 5 seconds
        if (type === 'success') {
            setTimeout(() => {
                if (alertContainer) alertContainer.innerHTML = '';
            }, 5000);
        }
    }
}

// Initialize the app when DOM is loaded
document.addEventListener('DOMContentLoaded', () => {
    window.googleCalendarAuth = new GoogleCalendarAuth();
});
