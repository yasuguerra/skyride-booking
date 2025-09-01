/**
 * SkyRide Booking Widget
 * Embeddable UMD module for WordPress and other websites
 */

(function (root, factory) {
    if (typeof define === 'function' && define.amd) {
        // AMD
        define([], factory);
    } else if (typeof module === 'object' && module.exports) {
        // CommonJS
        module.exports = factory();
    } else {
        // Browser globals
        root.SkyRideWidget = factory();
    }
}(typeof self !== 'undefined' ? self : this, function () {
    'use strict';

    // Widget configuration
    const DEFAULT_CONFIG = {
        apiUrl: 'https://booking.skyride.city/api',
        theme: 'light',
        showRoutes: true,
        showAircraft: true,
        defaultPassengers: 2,
        autoSubmit: false,
        ctaType: 'hosted_quote', // 'hosted_quote' or 'whatsapp'
        whatsappNumber: '+507-6000-0000'
    };

    // Widget HTML template
    const WIDGET_TEMPLATE = `
        <div class="skyride-widget" data-theme="{theme}">
            <div class="skyride-widget-header">
                <h3>Get Your Flight Quote</h3>
                <p>Charter flights across Panama</p>
            </div>
            <form class="skyride-widget-form">
                <div class="skyride-form-group">
                    <label for="skyride-origin">From</label>
                    <select id="skyride-origin" name="origin" required>
                        <option value="">Select departure city</option>
                        <option value="PTY">Panama City</option>
                        <option value="BLB">Bocas del Toro</option>
                        <option value="DAV">David</option>
                        <option value="COL">Colon</option>
                    </select>
                </div>
                <div class="skyride-form-group">
                    <label for="skyride-destination">To</label>
                    <select id="skyride-destination" name="destination" required>
                        <option value="">Select destination</option>
                        <option value="SCA">San Carlos</option>
                        <option value="BLB">Bocas del Toro</option>
                        <option value="DAV">David</option>
                        <option value="COL">Colon</option>
                        <option value="PTY">Panama City</option>
                    </select>
                </div>
                <div class="skyride-form-row">
                    <div class="skyride-form-group">
                        <label for="skyride-date">Date</label>
                        <input type="date" id="skyride-date" name="date" required>
                    </div>
                    <div class="skyride-form-group">
                        <label for="skyride-passengers">Passengers</label>
                        <select id="skyride-passengers" name="passengers">
                            <option value="1">1 passenger</option>
                            <option value="2" selected>2 passengers</option>
                            <option value="3">3 passengers</option>
                            <option value="4">4 passengers</option>
                            <option value="5">5 passengers</option>
                            <option value="6">6+ passengers</option>
                        </select>
                    </div>
                </div>
                <div class="skyride-form-group">
                    <label for="skyride-email">Email</label>
                    <input type="email" id="skyride-email" name="email" required placeholder="your@email.com">
                </div>
                <button type="submit" class="skyride-submit-btn">
                    <span class="skyride-btn-text">Get Quote</span>
                    <span class="skyride-btn-loading" style="display: none;">Getting quote...</span>
                </button>
            </form>
            <div class="skyride-widget-footer">
                <p>Powered by <a href="https://skyride.city" target="_blank">SkyRide</a></p>
            </div>
        </div>
    `;

    // Widget CSS styles
    const WIDGET_STYLES = `
        .skyride-widget {
            max-width: 400px;
            background: white;
            border-radius: 12px;
            box-shadow: 0 4px 20px rgba(0, 0, 0, 0.1);
            font-family: -apple-system, BlinkMacSystemFont, 'Segoe UI', Roboto, sans-serif;
            overflow: hidden;
        }
        .skyride-widget-header {
            background: linear-gradient(135deg, #1e40af 0%, #3b82f6 100%);
            color: white;
            padding: 20px;
            text-align: center;
        }
        .skyride-widget-header h3 {
            margin: 0 0 5px 0;
            font-size: 20px;
            font-weight: 600;
        }
        .skyride-widget-header p {
            margin: 0;
            opacity: 0.9;
            font-size: 14px;
        }
        .skyride-widget-form {
            padding: 20px;
        }
        .skyride-form-group {
            margin-bottom: 16px;
        }
        .skyride-form-row {
            display: flex;
            gap: 12px;
        }
        .skyride-form-row .skyride-form-group {
            flex: 1;
        }
        .skyride-form-group label {
            display: block;
            margin-bottom: 6px;
            font-weight: 500;
            color: #374151;
            font-size: 14px;
        }
        .skyride-form-group input,
        .skyride-form-group select {
            width: 100%;
            padding: 10px 12px;
            border: 1px solid #d1d5db;
            border-radius: 6px;
            font-size: 14px;
            box-sizing: border-box;
        }
        .skyride-form-group input:focus,
        .skyride-form-group select:focus {
            outline: none;
            border-color: #3b82f6;
            box-shadow: 0 0 0 2px rgba(59, 130, 246, 0.1);
        }
        .skyride-submit-btn {
            width: 100%;
            background: #1e40af;
            color: white;
            border: none;
            padding: 12px 24px;
            border-radius: 6px;
            font-size: 16px;
            font-weight: 600;
            cursor: pointer;
            transition: background-color 0.2s;
        }
        .skyride-submit-btn:hover {
            background: #1d4ed8;
        }
        .skyride-submit-btn:disabled {
            background: #9ca3af;
            cursor: not-allowed;
        }
        .skyride-widget-footer {
            padding: 12px 20px;
            background: #f9fafb;
            text-align: center;
            border-top: 1px solid #e5e7eb;
        }
        .skyride-widget-footer p {
            margin: 0;
            font-size: 12px;
            color: #6b7280;
        }
        .skyride-widget-footer a {
            color: #3b82f6;
            text-decoration: none;
        }
        .skyride-widget-footer a:hover {
            text-decoration: underline;
        }
        .skyride-success-message {
            background: #10b981;
            color: white;
            padding: 12px 20px;
            text-align: center;
            font-weight: 500;
        }
        .skyride-error-message {
            background: #ef4444;
            color: white;
            padding: 12px 20px;
            text-align: center;
            font-weight: 500;
        }
    `;

    // Analytics helper
    function trackEvent(eventName, parameters = {}) {
        // GA4 tracking
        if (window.gtag) {
            window.gtag('event', eventName, {
                event_category: 'SkyRide Widget',
                ...parameters
            });
        }

        // Custom tracking hook
        if (window.skyRideTrack) {
            window.skyRideTrack(eventName, parameters);
        }
    }

    // API helper
    async function apiCall(config, endpoint, data) {
        try {
            const response = await fetch(`${config.apiUrl}${endpoint}`, {
                method: 'POST',
                headers: {
                    'Content-Type': 'application/json',
                },
                body: JSON.stringify(data)
            });

            if (!response.ok) {
                throw new Error(`HTTP ${response.status}: ${response.statusText}`);
            }

            return await response.json();
        } catch (error) {
            console.error('SkyRide Widget API Error:', error);
            throw error;
        }
    }

    // Widget class
    class SkyRideWidget {
        constructor(element, options = {}) {
            this.element = element;
            this.config = { ...DEFAULT_CONFIG, ...options };
            this.init();
        }

        init() {
            // Inject styles
            this.injectStyles();
            
            // Render widget
            this.render();
            
            // Bind events
            this.bindEvents();
            
            // Set default date (tomorrow)
            this.setDefaultDate();

            // Track widget view
            trackEvent('widget_view', {
                widget_type: 'booking_form'
            });
        }

        injectStyles() {
            if (document.getElementById('skyride-widget-styles')) return;

            const style = document.createElement('style');
            style.id = 'skyride-widget-styles';
            style.textContent = WIDGET_STYLES;
            document.head.appendChild(style);
        }

        render() {
            this.element.innerHTML = WIDGET_TEMPLATE.replace('{theme}', this.config.theme);
        }

        bindEvents() {
            const form = this.element.querySelector('.skyride-widget-form');
            form.addEventListener('submit', (e) => this.handleSubmit(e));

            // Track form interactions
            const inputs = form.querySelectorAll('input, select');
            inputs.forEach(input => {
                input.addEventListener('change', () => {
                    trackEvent('widget_interaction', {
                        field: input.name,
                        value: input.type === 'email' ? '[email]' : input.value
                    });
                });
            });
        }

        setDefaultDate() {
            const dateInput = this.element.querySelector('#skyride-date');
            const tomorrow = new Date();
            tomorrow.setDate(tomorrow.getDate() + 1);
            dateInput.value = tomorrow.toISOString().split('T')[0];
        }

        async handleSubmit(e) {
            e.preventDefault();
            
            const submitBtn = this.element.querySelector('.skyride-submit-btn');
            const btnText = submitBtn.querySelector('.skyride-btn-text');
            const btnLoading = submitBtn.querySelector('.skyride-btn-loading');
            
            // Get form data
            const formData = new FormData(e.target);
            const data = Object.fromEntries(formData.entries());

            // Validate required fields
            if (!data.origin || !data.destination || !data.date || !data.email) {
                this.showError('Please fill in all required fields');
                return;
            }

            // Show loading state
            submitBtn.disabled = true;
            btnText.style.display = 'none';
            btnLoading.style.display = 'inline';

            try {
                // Track quote request
                trackEvent('generate_lead', {
                    origin: data.origin,
                    destination: data.destination,
                    passengers: data.passengers
                });

                // Create quote
                const quoteData = {
                    origin: data.origin,
                    destination: data.destination,
                    date: data.date,
                    passengers: parseInt(data.passengers),
                    customer: {
                        email: data.email
                    }
                };

                const response = await apiCall(this.config, '/quotes', quoteData);

                if (response.token) {
                    // Handle successful quote creation
                    if (this.config.ctaType === 'whatsapp') {
                        this.handleWhatsAppCTA(response, data);
                    } else {
                        this.handleHostedQuoteCTA(response);
                    }
                } else {
                    throw new Error('No quote token received');
                }

            } catch (error) {
                console.error('Quote creation error:', error);
                this.showError('Unable to create quote. Please try again.');
                
                // Track error
                trackEvent('widget_error', {
                    error: error.message
                });
            } finally {
                // Reset button state
                submitBtn.disabled = false;
                btnText.style.display = 'inline';
                btnLoading.style.display = 'none';
            }
        }

        handleHostedQuoteCTA(response) {
            // Redirect to hosted quote page
            const quoteUrl = `${this.config.apiUrl.replace('/api', '')}/q/${response.token}`;
            window.open(quoteUrl, '_blank');
            
            this.showSuccess('Quote created! Opening in new window...');
            
            trackEvent('view_item', {
                item_id: response.token,
                value: response.totalPrice,
                currency: 'USD'
            });
        }

        handleWhatsAppCTA(response, formData) {
            // Create WhatsApp message
            const message = `Hi! I'd like a quote for a flight from ${formData.origin} to ${formData.destination} on ${formData.date} for ${formData.passengers} passengers. Quote ID: ${response.token}`;
            const whatsappUrl = `https://wa.me/${this.config.whatsappNumber.replace(/[^0-9]/g, '')}?text=${encodeURIComponent(message)}`;
            
            window.open(whatsappUrl, '_blank');
            
            this.showSuccess('Quote created! Continue on WhatsApp...');
            
            trackEvent('generate_lead', {
                method: 'whatsapp',
                quote_id: response.token
            });
        }

        showSuccess(message) {
            this.showMessage(message, 'success');
        }

        showError(message) {
            this.showMessage(message, 'error');
        }

        showMessage(message, type) {
            // Remove existing messages
            const existingMessage = this.element.querySelector('.skyride-success-message, .skyride-error-message');
            if (existingMessage) {
                existingMessage.remove();
            }

            // Create new message
            const messageEl = document.createElement('div');
            messageEl.className = `skyride-${type}-message`;
            messageEl.textContent = message;

            // Insert message
            const header = this.element.querySelector('.skyride-widget-header');
            header.insertAdjacentElement('afterend', messageEl);

            // Auto-remove after 5 seconds
            setTimeout(() => {
                if (messageEl.parentNode) {
                    messageEl.remove();
                }
            }, 5000);
        }
    }

    // Public API
    return {
        init: function(selector, options = {}) {
            const elements = typeof selector === 'string' 
                ? document.querySelectorAll(selector)
                : [selector];

            const widgets = [];
            elements.forEach(element => {
                if (element) {
                    widgets.push(new SkyRideWidget(element, options));
                }
            });

            return widgets.length === 1 ? widgets[0] : widgets;
        },

        version: '2.0.0'
    };
}));
