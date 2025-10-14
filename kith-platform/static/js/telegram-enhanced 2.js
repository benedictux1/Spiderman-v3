/**
 * Enhanced Telegram Integration JavaScript
 * Provides UI for the new hybrid Telegram sync system
 */

class EnhancedTelegramManager {
    constructor() {
        this.apiBase = '/api/telegram/enhanced';
        this.statusInterval = null;
        this.currentStatus = null;
    this.autoReconnectAttempted = false;
    }

    /**
     * Initialize the enhanced Telegram manager
     */
    async init() {
        console.log('Initializing Enhanced Telegram Manager');
        
        // Check if we're on the settings page
        if (document.getElementById('telegram-enhanced-section')) {
            await this.loadStatus();
            this.setupEventListeners();
            this.startStatusPolling();
        }
    }

    /**
     * Setup event listeners for enhanced Telegram controls
     */
    setupEventListeners() {
        // Authentication button (for phone/OTP flow)
        const authBtn = document.getElementById('telegram-auth-start-enhanced');
        if (authBtn) {
            authBtn.addEventListener('click', () => this.startPhoneAuthFlow());
        }

        // Connect button
        const connectBtn = document.getElementById('telegram-connect-enhanced');
        if (connectBtn) {
            connectBtn.addEventListener('click', () => this.connect());
        }

        // Disconnect button
        const disconnectBtn = document.getElementById('telegram-disconnect-enhanced');
        if (disconnectBtn) {
            disconnectBtn.addEventListener('click', () => this.disconnect());
        }

        // Sync all button
        const syncAllBtn = document.getElementById('telegram-sync-all-enhanced');
        if (syncAllBtn) {
            syncAllBtn.addEventListener('click', () => this.syncAll());
        }

        // Sync contact button
        const syncContactBtn = document.getElementById('telegram-sync-contact-enhanced');
        if (syncContactBtn) {
            syncContactBtn.addEventListener('click', () => this.syncContact());
        }

        // Migration buttons
        const migrateToCloudBtn = document.getElementById('telegram-migrate-to-cloud');
        if (migrateToCloudBtn) {
            migrateToCloudBtn.addEventListener('click', () => this.migrateToCloud());
        }

        const migrateToLocalBtn = document.getElementById('telegram-migrate-to-local');
        if (migrateToLocalBtn) {
            migrateToLocalBtn.addEventListener('click', () => this.migrateToLocal());
        }

        const syncStoragesBtn = document.getElementById('telegram-sync-storages');
        if (syncStoragesBtn) {
            syncStoragesBtn.addEventListener('click', () => this.syncStorages());
        }

        // Prefer phone/OTP/password flow: wire to existing buttons
        const relinkBtn = document.getElementById('telegram-relink-btn');
        if (relinkBtn) {
            relinkBtn.style.display = 'inline-block';
            relinkBtn.addEventListener('click', () => this.startPhoneAuthFlow());
        }
        const configureBtn = document.getElementById('telegram-configure-btn');
        if (configureBtn) {
            configureBtn.addEventListener('click', () => this.toggleCredentialsForm(true));
        }
    }

    /**
     * Load current status
     */
    async loadStatus() {
        try {
            const response = await fetch(`${this.apiBase}/status`);
            const data = await response.json();
            
            if (data.success) {
                this.currentStatus = data.status;
                this.updateStatusDisplay(data.status);

        // Auto-reconnect on page load if we have a saved session but no active connection
        if (
          this.currentStatus &&
          this.currentStatus.has_session &&
          !this.currentStatus.is_connected &&
          !this.autoReconnectAttempted
        ) {
          this.autoReconnectAttempted = true;
          // Attempt a silent reconnect
          this.connect();
        }
            } else {
                console.error('Failed to load status:', data.message);
                this.showError('Failed to load status: ' + data.message);
            }
        } catch (error) {
            console.error('Error loading status:', error);
            this.showError('Error loading status: ' + error.message);
        }
    }

    /**
     * Update status display
     */
    updateStatusDisplay(status) {
        // Update connection status
        const statusIndicator = document.getElementById('telegram-status-enhanced');
        if (statusIndicator) {
            if (status.is_connected) {
                statusIndicator.innerHTML = '<span class="status-connected">🟢 Connected</span>';
                statusIndicator.className = 'status-connected';
            } else if (status.has_session) {
                statusIndicator.innerHTML = '<span class="status-session">🟡 Session Available</span>';
                statusIndicator.className = 'status-session';
            } else {
                statusIndicator.innerHTML = '<span class="status-disconnected">🔴 Not Connected - Please authenticate using phone/OTP below</span>';
                statusIndicator.className = 'status-disconnected';
            }
        }

        // Update environment info
        const envInfo = document.getElementById('telegram-environment-info');
        if (envInfo) {
            envInfo.innerHTML = `
                <div class="env-info">
                    <strong>Environment:</strong> ${status.environment || 'Unknown'}<br>
                    <strong>Storage Backend:</strong> ${status.storage_backend || 'Unknown'}<br>
                    <strong>Session Exists:</strong> ${status.has_session ? 'Yes' : 'No'}
                </div>
            `;
        }

        // Update Telegram user info
        const userInfo = document.getElementById('telegram-user-info');
        if (userInfo && status.telegram_user) {
            userInfo.innerHTML = `
                <div class="user-info">
                    <strong>Telegram User:</strong> ${status.telegram_user.first_name || 'Unknown'}<br>
                    <strong>Username:</strong> @${status.telegram_user.username || 'N/A'}<br>
                    <strong>Phone:</strong> ${status.telegram_user.phone || 'N/A'}
                </div>
            `;
        } else if (userInfo) {
            userInfo.innerHTML = '<div class="user-info">No Telegram user connected. Use "🔗 Relink Account" below to authenticate.</div>';
        }

        // Show/hide buttons based on session status
        const authBtn = document.getElementById('telegram-auth-start-enhanced');
        const relinkBtn = document.getElementById('telegram-relink-btn');
        const configureBtn = document.getElementById('telegram-configure-btn');
        const connectBtn = document.getElementById('telegram-connect-enhanced');
        const disconnectBtn = document.getElementById('telegram-disconnect-enhanced');
        
        if (status.has_session) {
            // Session exists: show Connect, and also show Authenticate as a fallback
            if (connectBtn) connectBtn.style.display = 'inline-block';
            if (authBtn) authBtn.style.display = status.is_connected ? 'none' : 'inline-block';
            if (disconnectBtn) disconnectBtn.style.display = status.is_connected ? 'inline-block' : 'none';
            if (relinkBtn) relinkBtn.style.display = 'none';
        } else {
            // No saved session: only show Authenticate
            if (authBtn) authBtn.style.display = 'inline-block';
            if (connectBtn) connectBtn.style.display = 'none';
            if (disconnectBtn) disconnectBtn.style.display = 'none';
            if (relinkBtn) relinkBtn.style.display = 'inline-block';
        }

        // Hide API credential form by default when a session exists
        const apiForm = document.getElementById('telegram-credentials-form');
        if (apiForm) {
            if (status.has_session) {
                apiForm.style.display = 'none';
                if (configureBtn) configureBtn.style.display = 'inline-block';
            }
        }

        // Update sync status
        const syncStatus = document.getElementById('telegram-sync-status');
        if (syncStatus) {
            if (status.sync_in_progress) {
                syncStatus.innerHTML = '<span class="sync-in-progress">🔄 Sync in progress...</span>';
            } else if (status.last_sync) {
                const lastSync = new Date(status.last_sync);
                syncStatus.innerHTML = `<span class="sync-completed">✅ Last sync: ${lastSync.toLocaleString()}</span>`;
            } else {
                syncStatus.innerHTML = '<span class="sync-pending">⏳ No sync performed yet</span>';
            }
        }
    }

    /**
     * Toggle the legacy API credential form
     */
    toggleCredentialsForm(show) {
        const apiForm = document.getElementById('telegram-credentials-form');
        if (apiForm) apiForm.style.display = show ? 'block' : 'none';
    }

    /**
     * Start status polling
     */
    startStatusPolling() {
        this.statusInterval = setInterval(() => {
            this.loadStatus();
        }, 5000); // Poll every 5 seconds
    }

    /**
     * Stop status polling
     */
    stopStatusPolling() {
        if (this.statusInterval) {
            clearInterval(this.statusInterval);
            this.statusInterval = null;
        }
    }

    /**
     * Connect to Telegram
     */
    async connect() {
        // Check if user has a session first
        if (!this.currentStatus || !this.currentStatus.has_session) {
            this.showError('No session found. Please authenticate first using the "🔗 Relink Account" button below to enter your phone number and OTP code.');
            return;
        }
        
        this.showLoading('Connecting to Telegram...');
        
        try {
            const response = await fetch(`${this.apiBase}/connect`, {
                method: 'POST',
                headers: {
                    'Content-Type': 'application/json'
                }
            });
            
            const data = await response.json();
            
            if (data.success) {
                this.showSuccess('Successfully connected to Telegram!');
                await this.loadStatus();
            } else {
                this.showError('Failed to connect: ' + data.message + ' Please use the "📱 Authenticate with Phone/OTP" button to authenticate.');
            }
        } catch (error) {
            console.error('Connection error:', error);
            this.showError('Connection error: ' + error.message);
        }
    }

    /**
     * Disconnect from Telegram
     */
    async disconnect() {
        this.showLoading('Disconnecting from Telegram...');
        
        try {
            const response = await fetch(`${this.apiBase}/disconnect`, {
                method: 'POST',
                headers: {
                    'Content-Type': 'application/json'
                }
            });
            
            const data = await response.json();
            
            if (data.success) {
                this.showSuccess('Successfully disconnected from Telegram!');
                await this.loadStatus();
            } else {
                this.showError('Failed to disconnect: ' + data.message);
            }
        } catch (error) {
            console.error('Disconnection error:', error);
            this.showError('Disconnection error: ' + error.message);
        }
    }

    /**
     * Phone → OTP → Password flow (no API prompts in UI)
     */
    async startPhoneAuthFlow() {
        try {
            const phone = prompt('Enter your phone number (e.g., +6584XXXXXX):');
            if (!phone) return;

            // Send code
            const sendRes = await fetch('/api/telegram/auth/start', {
                method: 'POST',
                headers: { 'Content-Type': 'application/json' },
                body: JSON.stringify({ phone })
            });
            const sendData = await sendRes.json();
            if (!sendData.success) {
                this.showError(sendData.message || 'Failed to send code.');
                return;
            }

            const code = prompt('Enter the code sent to your Telegram app:');
            if (!code) return;

            // Verify code
            const verifyRes = await fetch('/api/telegram/auth/verify', {
                method: 'POST',
                headers: { 'Content-Type': 'application/json' },
                body: JSON.stringify({ phone, code })
            });
            const verifyData = await verifyRes.json();
            if (verifyData.password_required) {
                const password = prompt('Enter your Telegram 2FA password:');
                if (!password) return;
                const pwRes = await fetch('/api/telegram/auth/password', {
                    method: 'POST',
                    headers: { 'Content-Type': 'application/json' },
                    body: JSON.stringify({ phone, password })
                });
                const pwData = await pwRes.json();
                if (!pwData.success) {
                    this.showError(pwData.message || 'Failed to complete authentication.');
                    return;
                }
                this.showSuccess('Authenticated successfully. Session saved.');
                await this.loadStatus();
                return;
            }

            if (!verifyData.success) {
                this.showError(verifyData.message || 'Invalid code.');
                return;
            }

            this.showSuccess('Authenticated successfully. Session saved.');
            await this.loadStatus();
        } catch (e) {
            console.error(e);
            this.showError('Authentication failed: ' + (e?.message || e));
        }
    }

    /**
     * Sync all chat history
     */
    async syncAll() {
        // Check if user is authenticated first
        if (!this.currentStatus || !this.currentStatus.has_session) {
            this.showError('❌ Not authenticated! Please click "📱 Authenticate with Phone/OTP" first to login to Telegram.');
            return;
        }
        
        // Best-effort auto-connect; don't block sync if it fails (backend will try too)
        if (!this.currentStatus.is_connected) {
            try {
                await this.connect();
                await this.loadStatus();
            } catch (_) {}
        }
        
        const daysBack = prompt('How many days back to sync? (default: 30)', '30');
        if (daysBack === null) return;
        
        this.showLoading('Syncing all chat history...');
        
        try {
            const response = await fetch(`${this.apiBase}/sync-all`, {
                method: 'POST',
                headers: {
                    'Content-Type': 'application/json'
                },
                body: JSON.stringify({
                    days_back: parseInt(daysBack) || 30
                })
            });
            
            const data = await response.json();
            
            if (data.success) {
                this.showSuccess(`✅ Sync completed! ${data.contacts_count} contacts, ${data.conversations_count} conversations. Check the Contacts page to view.`);
                await this.loadStatus();
            } else {
                this.showError('❌ Sync failed: ' + data.message);
            }
        } catch (error) {
            console.error('Sync error:', error);
            this.showError('Sync error: ' + error.message);
        }
    }

    /**
     * Sync specific contact
     */
    async syncContact() {
        // Check if user is authenticated first
        if (!this.currentStatus || !this.currentStatus.has_session) {
            this.showError('❌ Not authenticated! Please click "📱 Authenticate with Phone/OTP" first to login to Telegram.');
            return;
        }
        
        // Best-effort auto-connect; don't block sync if it fails
        if (!this.currentStatus.is_connected) {
            try {
                await this.connect();
                await this.loadStatus();
            } catch (_) {}
        }
        
        const contactIdentifier = prompt('Enter contact username (without @) or phone number (with country code, e.g., +6584XXXXXX):');
        if (!contactIdentifier) return;
        
        const daysBack = prompt('How many days back to sync? (default: 30)', '30');
        if (daysBack === null) return;
        
        this.showLoading(`Syncing contact: ${contactIdentifier}...`);
        
        try {
            const response = await fetch(`${this.apiBase}/sync-contact`, {
                method: 'POST',
                headers: {
                    'Content-Type': 'application/json'
                },
                body: JSON.stringify({
                    contact_identifier: contactIdentifier,
                    days_back: parseInt(daysBack) || 30
                })
            });
            
            const data = await response.json();
            
            if (data.success) {
                const messageCount = data.message_count || 0;
                if (messageCount > 0) {
                    this.showSuccess(`✅ Contact sync completed! ${messageCount} messages synced. Check the Contacts page to view.`);
                } else {
                    this.showSuccess(`ℹ️ ${data.message || 'No messages found for this contact in the specified time period.'}`);
                }
                await this.loadStatus();
            } else {
                this.showError('❌ Contact sync failed: ' + data.message + '\n\nTip: Use username without @ (e.g., "johndoe") or phone with country code (e.g., "+6584XXXXXX")');
            }
        } catch (error) {
            console.error('Contact sync error:', error);
            this.showError('Contact sync error: ' + error.message);
        }
    }

    /**
     * Migrate to cloud storage
     */
    async migrateToCloud() {
        this.showLoading('Migrating to cloud storage...');
        
        try {
            const response = await fetch(`${this.apiBase}/migration/to-cloud`, {
                method: 'POST',
                headers: {
                    'Content-Type': 'application/json'
                }
            });
            
            const data = await response.json();
            
            if (data.success) {
                this.showSuccess('Successfully migrated to cloud storage!');
                await this.loadStatus();
            } else {
                this.showError('Migration failed: ' + data.message);
            }
        } catch (error) {
            console.error('Migration error:', error);
            this.showError('Migration error: ' + error.message);
        }
    }

    /**
     * Migrate to local storage
     */
    async migrateToLocal() {
        this.showLoading('Migrating to local storage...');
        
        try {
            const response = await fetch(`${this.apiBase}/migration/to-local`, {
                method: 'POST',
                headers: {
                    'Content-Type': 'application/json'
                }
            });
            
            const data = await response.json();
            
            if (data.success) {
                this.showSuccess('Successfully migrated to local storage!');
                await this.loadStatus();
            } else {
                this.showError('Migration failed: ' + data.message);
            }
        } catch (error) {
            console.error('Migration error:', error);
            this.showError('Migration error: ' + error.message);
        }
    }

    /**
     * Sync between storages
     */
    async syncStorages() {
        this.showLoading('Syncing between storages...');
        
        try {
            const response = await fetch(`${this.apiBase}/migration/sync`, {
                method: 'POST',
                headers: {
                    'Content-Type': 'application/json'
                }
            });
            
            const data = await response.json();
            
            if (data.success) {
                this.showSuccess('Successfully synced between storages!');
                await this.loadStatus();
            } else {
                this.showError('Storage sync failed: ' + data.message);
            }
        } catch (error) {
            console.error('Storage sync error:', error);
            this.showError('Storage sync error: ' + error.message);
        }
    }

    /**
     * Show loading message
     */
    showLoading(message) {
        this.showMessage(message, 'loading');
    }

    /**
     * Show success message
     */
    showSuccess(message) {
        this.showMessage(message, 'success');
    }

    /**
     * Show error message
     */
    showError(message) {
        this.showMessage(message, 'error');
    }

    /**
     * Show message with type
     */
    showMessage(message, type) {
        const messageDiv = document.getElementById('telegram-message-enhanced');
        if (messageDiv) {
            messageDiv.innerHTML = `<div class="message message-${type}">${message}</div>`;
            messageDiv.style.display = 'block';
            
            // Auto-hide after 5 seconds
            setTimeout(() => {
                messageDiv.style.display = 'none';
            }, 5000);
        }
    }
}

// Initialize when DOM is loaded
document.addEventListener('DOMContentLoaded', () => {
    const telegramManager = new EnhancedTelegramManager();
    telegramManager.init();
});
