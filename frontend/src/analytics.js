/**
 * Google Analytics 4 (GA4) Helper for SkyRide
 * Tracks booking funnel events and user interactions
 */

// GA4 Events Configuration
const GA4_EVENTS = {
    // Core booking funnel events
    VIEW_ITEM: 'view_item',
    ADD_TO_CART: 'add_to_cart', 
    BEGIN_CHECKOUT: 'begin_checkout',
    ADD_PAYMENT_INFO: 'add_payment_info',
    PURCHASE: 'purchase',
    
    // Lead generation events
    GENERATE_LEAD: 'generate_lead',
    
    // Custom SkyRide events
    QUOTE_VIEWED: 'quote_viewed',
    HOLD_CREATED: 'hold_created',
    WHATSAPP_CLICK: 'whatsapp_click'
};

/**
 * Analytics helper class
 */
class SkyRideAnalytics {
    constructor(measurementId) {
        this.measurementId = measurementId;
        this.isInitialized = false;
        this.init();
    }

    /**
     * Initialize GA4 if not already loaded
     */
    init() {
        if (this.isInitialized || !this.measurementId) {
            return;
        }

        // Check if gtag is already loaded
        if (window.gtag) {
            this.isInitialized = true;
            return;
        }

        // Load GA4 script
        const script = document.createElement('script');
        script.async = true;
        script.src = `https://www.googletagmanager.com/gtag/js?id=${this.measurementId}`;
        document.head.appendChild(script);

        // Initialize gtag
        window.dataLayer = window.dataLayer || [];
        window.gtag = function() {
            dataLayer.push(arguments);
        };

        gtag('js', new Date());
        gtag('config', this.measurementId, {
            // Enhanced ecommerce settings
            currency: 'USD',
            country: 'PA',
            // Cross-domain tracking for skyride.city/booking.skyride.city
            linker: {
                domains: ['skyride.city', 'booking.skyride.city']
            }
        });

        this.isInitialized = true;
        console.log('SkyRide Analytics initialized');
    }

    /**
     * Track generic event
     */
    track(eventName, parameters = {}) {
        if (!this.isInitialized || !window.gtag) {
            console.warn('Analytics not initialized');
            return;
        }

        // Add default parameters
        const enrichedParams = {
            event_category: 'SkyRide',
            ...parameters
        };

        gtag('event', eventName, enrichedParams);
        console.log('Analytics event:', eventName, enrichedParams);
    }

    /**
     * Track hosted quote view
     */
    trackQuoteView(quoteData) {
        this.track(GA4_EVENTS.VIEW_ITEM, {
            item_id: quoteData.token,
            item_name: `Flight Quote - ${quoteData.origin} to ${quoteData.destination}`,
            item_category: 'Charter Flight',
            item_variant: quoteData.aircraftType,
            value: quoteData.totalPrice,
            currency: 'USD',
            quantity: 1,
            // Custom dimensions
            flight_origin: quoteData.origin,
            flight_destination: quoteData.destination,
            aircraft_type: quoteData.aircraftType,
            passenger_count: quoteData.passengers
        });
    }

    /**
     * Track hold creation (add to cart)
     */
    trackHoldCreated(holdData) {
        this.track(GA4_EVENTS.ADD_TO_CART, {
            item_id: holdData.quoteToken,
            item_name: `Flight Hold - ${holdData.origin} to ${holdData.destination}`,
            item_category: 'Charter Flight',
            value: holdData.totalPrice,
            currency: 'USD',
            quantity: 1,
            // Custom dimensions
            hold_id: holdData.holdId,
            deposit_amount: holdData.depositAmount,
            expires_at: holdData.expiresAt
        });
    }

    /**
     * Track checkout initiation (Wompi button click)
     */
    trackCheckoutBegin(checkoutData) {
        this.track(GA4_EVENTS.BEGIN_CHECKOUT, {
            item_id: checkoutData.quoteToken,
            value: checkoutData.totalPrice,
            currency: 'USD',
            payment_type: checkoutData.provider || 'WOMPI',
            // Custom dimensions
            booking_id: checkoutData.orderId
        });
    }

    /**
     * Track payment info addition (redirect to Wompi)
     */
    trackPaymentInfo(paymentData) {
        this.track(GA4_EVENTS.ADD_PAYMENT_INFO, {
            value: paymentData.amount,
            currency: 'USD',
            payment_type: paymentData.provider || 'WOMPI',
            // Custom dimensions
            payment_link: paymentData.paymentLinkUrl ? 'generated' : 'failed'
        });
    }

    /**
     * Track successful purchase (webhook confirmation)
     */
    trackPurchase(purchaseData) {
        this.track(GA4_EVENTS.PURCHASE, {
            transaction_id: purchaseData.bookingNumber,
            value: purchaseData.totalAmount,
            currency: 'USD',
            items: [{
                item_id: purchaseData.quoteToken,
                item_name: `Charter Flight - ${purchaseData.origin} to ${purchaseData.destination}`,
                item_category: 'Charter Flight',
                quantity: 1,
                price: purchaseData.totalAmount
            }],
            // Custom dimensions
            booking_id: purchaseData.bookingId,
            payment_provider: 'WOMPI'
        });
    }

    /**
     * Track lead generation (WhatsApp click, widget quote)
     */
    trackLeadGeneration(leadData) {
        this.track(GA4_EVENTS.GENERATE_LEAD, {
            value: leadData.estimatedValue || 0,
            currency: 'USD',
            // Custom dimensions
            lead_source: leadData.source || 'website',
            lead_type: leadData.type || 'quote_request',
            origin: leadData.origin,
            destination: leadData.destination,
            whatsapp_number: leadData.whatsappNumber
        });
    }

    /**
     * Track WhatsApp click-to-chat
     */
    trackWhatsAppClick(clickData) {
        this.track(GA4_EVENTS.WHATSAPP_CLICK, {
            click_text: clickData.buttonText || 'Contact via WhatsApp',
            // Custom dimensions
            page_location: window.location.href,
            quote_token: clickData.quoteToken,
            whatsapp_number: clickData.whatsappNumber
        });
    }

    /**
     * Track widget interactions
     */
    trackWidgetInteraction(interactionData) {
        this.track('widget_interaction', {
            widget_type: interactionData.widgetType || 'booking_form',
            interaction_type: interactionData.type || 'field_change',
            field_name: interactionData.fieldName,
            // Custom dimensions
            widget_location: interactionData.location || 'wordpress_block'
        });
    }

    /**
     * Set user properties
     */
    setUserProperties(properties) {
        if (!this.isInitialized || !window.gtag) {
            return;
        }

        gtag('config', this.measurementId, {
            user_properties: properties
        });
    }

    /**
     * Track conversion events for marketing
     */
    trackConversion(conversionData) {
        this.track('conversion', {
            value: conversionData.value,
            currency: 'USD',
            conversion_type: conversionData.type,
            // Custom dimensions
            conversion_source: conversionData.source
        });
    }
}

// Global analytics instance
let skyRideAnalytics = null;

/**
 * Initialize analytics with measurement ID
 */
function initAnalytics(measurementId) {
    if (!measurementId) {
        console.warn('No GA4 measurement ID provided');
        return null;
    }

    skyRideAnalytics = new SkyRideAnalytics(measurementId);
    return skyRideAnalytics;
}

/**
 * Get or initialize analytics instance
 */
function getAnalytics() {
    if (!skyRideAnalytics) {
        // Try to get measurement ID from common sources
        const measurementId = 
            window.GA_MEASUREMENT_ID || 
            (window.skyRideConfig && window.skyRideConfig.ga4MeasurementId) ||
            'G-XXXXXXXXXX'; // Default/placeholder
            
        return initAnalytics(measurementId);
    }
    return skyRideAnalytics;
}

/**
 * Convenience functions for common events
 */
const analytics = {
    init: initAnalytics,
    get: getAnalytics,
    
    // Booking funnel
    viewQuote: (data) => getAnalytics()?.trackQuoteView(data),
    createHold: (data) => getAnalytics()?.trackHoldCreated(data),
    beginCheckout: (data) => getAnalytics()?.trackCheckoutBegin(data),
    addPaymentInfo: (data) => getAnalytics()?.trackPaymentInfo(data),
    completePurchase: (data) => getAnalytics()?.trackPurchase(data),
    
    // Lead generation
    generateLead: (data) => getAnalytics()?.trackLeadGeneration(data),
    clickWhatsApp: (data) => getAnalytics()?.trackWhatsAppClick(data),
    
    // Interactions
    widgetInteraction: (data) => getAnalytics()?.trackWidgetInteraction(data),
    
    // Generic tracking
    track: (event, params) => getAnalytics()?.track(event, params)
};

// Auto-initialize if measurement ID is available
if (typeof window !== 'undefined') {
    // Try to auto-initialize from various sources
    const autoInit = () => {
        const measurementId = 
            window.GA_MEASUREMENT_ID || 
            (window.skyRideConfig && window.skyRideConfig.ga4MeasurementId) ||
            (document.querySelector('[data-ga4-id]') && document.querySelector('[data-ga4-id]').dataset.ga4Id);
            
        if (measurementId && measurementId !== 'G-XXXXXXXXXX') {
            initAnalytics(measurementId);
        }
    };

    if (document.readyState === 'loading') {
        document.addEventListener('DOMContentLoaded', autoInit);
    } else {
        autoInit();
    }
}

// Export for different module systems
if (typeof module !== 'undefined' && module.exports) {
    module.exports = analytics;
} else if (typeof window !== 'undefined') {
    window.SkyRideAnalytics = analytics;
}
