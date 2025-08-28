/**
 * SkyRide WordPress Plugin Frontend Loader
 * Loads the SkyRide widget script and initializes it based on block data attributes
 */

(function() {
    'use strict';
    
    // Configuration
    const WIDGET_SCRIPT_URL = 'https://booking.skyride.city/widget.js';
    const LOAD_TIMEOUT = 10000; // 10 seconds
    
    // Track if script is already loaded
    let scriptLoaded = false;
    let scriptLoading = false;
    
    /**
     * Load SkyRide widget script dynamically
     */
    function loadWidgetScript() {
        return new Promise((resolve, reject) => {
            if (scriptLoaded) {
                resolve();
                return;
            }
            
            if (scriptLoading) {
                // Wait for existing load
                const checkLoaded = setInterval(() => {
                    if (scriptLoaded) {
                        clearInterval(checkLoaded);
                        resolve();
                    }
                }, 100);
                
                setTimeout(() => {
                    clearInterval(checkLoaded);
                    if (!scriptLoaded) {
                        reject(new Error('Widget script load timeout'));
                    }
                }, LOAD_TIMEOUT);
                return;
            }
            
            scriptLoading = true;
            
            const script = document.createElement('script');
            script.src = WIDGET_SCRIPT_URL;
            script.defer = true;
            script.async = true;
            
            script.onload = () => {
                scriptLoaded = true;
                scriptLoading = false;
                console.log('SkyRide widget script loaded successfully');
                resolve();
            };
            
            script.onerror = () => {
                scriptLoading = false;
                console.error('Failed to load SkyRide widget script');
                reject(new Error('Failed to load widget script'));
            };
            
            document.head.appendChild(script);
            
            // Timeout fallback
            setTimeout(() => {
                if (!scriptLoaded) {
                    scriptLoading = false;
                    reject(new Error('Widget script load timeout'));
                }
            }, LOAD_TIMEOUT);
        });
    }
    
    /**
     * Initialize SkyRide widgets from data attributes
     */
    function initializeWidgets() {
        const widgetElements = document.querySelectorAll('[data-skyride-widget]');
        
        if (widgetElements.length === 0) {
            return;
        }
        
        console.log(`Found ${widgetElements.length} SkyRide widget(s)`);
        
        widgetElements.forEach((element, index) => {
            try {
                // Parse configuration from data attributes
                const config = {
                    apiUrl: element.getAttribute('data-api-url') || 'https://booking.skyride.city/api',
                    theme: element.getAttribute('data-theme') || 'light',
                    ctaType: element.getAttribute('data-cta-type') || 'hosted_quote',
                    whatsappNumber: element.getAttribute('data-whatsapp-number') || '+507-6000-0000',
                    defaultPassengers: parseInt(element.getAttribute('data-default-passengers')) || 2,
                    autoSubmit: element.getAttribute('data-auto-submit') === 'true'
                };
                
                // Initialize widget
                if (window.SkyRideWidget) {
                    const widget = window.SkyRideWidget.init(element, config);
                    console.log(`SkyRide widget ${index + 1} initialized`);
                    
                    // Store widget reference on element
                    element._skyRideWidget = widget;
                } else {
                    console.error('SkyRideWidget not available');
                }
                
            } catch (error) {
                console.error(`Error initializing SkyRide widget ${index + 1}:`, error);
            }
        });
    }
    
    /**
     * Initialize all widgets after script loads
     */
    function initializeSkyRide() {
        loadWidgetScript()
            .then(() => {
                // Wait a bit for the script to register the global
                setTimeout(initializeWidgets, 100);
            })
            .catch((error) => {
                console.error('Failed to load SkyRide widget:', error);
                
                // Show fallback message in widget containers
                const widgetElements = document.querySelectorAll('[data-skyride-widget]');
                widgetElements.forEach(element => {
                    element.innerHTML = `
                        <div style="padding: 20px; text-align: center; background: #f9fafb; border-radius: 8px; border: 1px solid #e5e7eb;">
                            <p style="margin: 0; color: #6b7280;">Unable to load booking widget.</p>
                            <p style="margin: 10px 0 0 0; font-size: 14px;">
                                <a href="https://skyride.city" target="_blank" style="color: #3b82f6;">Visit SkyRide.city</a> to book directly.
                            </p>
                        </div>
                    `;
                });
            });
    }
    
    /**
     * Re-initialize widgets (useful for dynamic content)
     */
    function reinitialize() {
        if (scriptLoaded) {
            initializeWidgets();
        } else {
            initializeSkyRide();
        }
    }
    
    // Auto-initialize on DOM ready
    if (document.readyState === 'loading') {
        document.addEventListener('DOMContentLoaded', initializeSkyRide);
    } else {
        // DOM already loaded
        initializeSkyRide();
    }
    
    // Expose global reinitialize function for dynamic content
    window.SkyRideReinit = reinitialize;
    
    // Support for WordPress block editor (Gutenberg) preview
    if (window.wp && window.wp.hooks) {
        window.wp.hooks.addAction('block-editor-render', 'skyride/reinit-widgets', reinitialize);
    }
    
})();
