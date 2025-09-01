<?php
/**
 * Plugin Name: SkyRide Booking Blocks
 * Plugin URI: https://booking.skyride.city
 * Description: Gutenberg blocks for SkyRide charter booking integration
 * Version: 1.0.0
 * Author: SkyRide Team
 */

// Prevent direct access
if (!defined('ABSPATH')) {
    exit;
}

class SkyRideGutenbergBlocks {
    
    public function __construct() {
        add_action('init', [$this, 'register_blocks']);
        add_action('wp_enqueue_scripts', [$this, 'enqueue_scripts']);
    }
    
    public function register_blocks() {
        // Register Quote CTA Block
        register_block_type('skyride/quote-cta', [
            'editor_script' => 'skyride-block-editor',
            'editor_style' => 'skyride-block-editor',
            'style' => 'skyride-block',
            'render_callback' => [$this, 'render_quote_cta_block'],
            'attributes' => [
                'buttonText' => [
                    'type' => 'string',
                    'default' => 'Cotiza ahora'
                ],
                'buttonStyle' => [
                    'type' => 'string',
                    'default' => 'primary'
                ],
                'embedMode' => [
                    'type' => 'string',
                    'default' => 'button' // 'button', 'iframe', 'script'
                ]
            ]
        ]);
        
        // Register Hot Deals Block
        register_block_type('skyride/hot-deals', [
            'editor_script' => 'skyride-block-editor',
            'editor_style' => 'skyride-block-editor',
            'style' => 'skyride-block',
            'render_callback' => [$this, 'render_hot_deals_block'],
            'attributes' => [
                'limit' => [
                    'type' => 'number',
                    'default' => 6
                ],
                'showImages' => [
                    'type' => 'boolean',
                    'default' => true
                ],
                'layout' => [
                    'type' => 'string',
                    'default' => 'grid' // 'grid', 'list'
                ]
            ]
        ]);
    }
    
    public function enqueue_scripts() {
        // Enqueue the SkyRide frontend loader (v2.0)
        wp_enqueue_script(
            'skyride-frontend',
            plugins_url('assets/skyride-frontend.js', __FILE__),
            [],
            '2.0.0',
            true
        );
        
        // Enqueue CSS from assets directory
        wp_enqueue_style(
            'skyride-blocks',
            plugins_url('assets/skyride-blocks.css', __FILE__),
            [],
            '2.0.0'
        );
        
        // Pass configuration to frontend (v2.0)
        wp_localize_script('skyride-frontend', 'skyRideConfig', [
            'apiUrl' => 'https://booking.skyride.city/api',
            'widgetUrl' => 'https://booking.skyride.city/widget.js',
            'version' => '2.0.0',
            'ga4_measurement_id' => get_option('skyride_ga4_id', ''),
            'cross_domain' => true
        ]);
        
        // Legacy support for existing blocks
        wp_enqueue_script(
            'skyride-block-frontend',
            plugins_url('assets/skyride-frontend.js', __FILE__),
            ['jquery'],
            '2.0.0',
            true
        );
        
        wp_localize_script('skyride-block-frontend', 'skyride_config', [
            'api_base' => 'https://booking.skyride.city/api',
            'booking_base' => 'https://booking.skyride.city',
            'ga4_measurement_id' => get_option('skyride_ga4_id', ''),
            'cross_domain' => true
        ]);
    }
    
    public function render_quote_cta_block($attributes) {
        $button_text = $attributes['buttonText'] ?? 'Cotiza ahora';
        $button_style = $attributes['buttonStyle'] ?? 'primary';
        $embed_mode = $attributes['embedMode'] ?? 'button';
        
        // Get CTA configuration from API
        $cta_config = $this->get_cta_config();
        
        if ($embed_mode === 'iframe') {
            return sprintf(
                '<div class="skyride-quote-embed">
                    <iframe src="%s" width="100%%" height="600" frameborder="0" style="border: 1px solid #e1e5e9; border-radius: 8px;"></iframe>
                </div>',
                esc_url($cta_config['iframe_url'] ?? 'https://booking.skyride.city/embed/quote')
            );
        }
        
        if ($embed_mode === 'script') {
            return sprintf(
                '<div class="skyride-quote-script">
                    %s
                </div>',
                $cta_config['embed_script'] ?? ''
            );
        }
        
        // Default button mode
        $button_class = 'skyride-cta-button skyride-cta-' . esc_attr($button_style);
        
        return sprintf(
            '<div class="skyride-quote-cta">
                <a href="%s" target="_blank" class="%s" onclick="skyride_track_cta_click();">
                    %s
                </a>
            </div>',
            esc_url($cta_config['button_url'] ?? 'https://booking.skyride.city/'),
            esc_attr($button_class),
            esc_html($button_text)
        );
    }
    
    public function render_hot_deals_block($attributes) {
        $limit = intval($attributes['limit'] ?? 6);
        $show_images = $attributes['showImages'] ?? true;
        $layout = $attributes['layout'] ?? 'grid';
        
        // Get hot deals from API
        $deals = $this->get_hot_deals($limit);
        
        if (empty($deals)) {
            return '<div class="skyride-hot-deals-empty">
                        <p>No hay ofertas especiales disponibles en este momento.</p>
                     </div>';
        }
        
        $layout_class = 'skyride-hot-deals skyride-layout-' . esc_attr($layout);
        
        ob_start();
        ?>
        <div class="<?php echo esc_attr($layout_class); ?>">
            <h3 class="skyride-deals-title">Ofertas Especiales</h3>
            <div class="skyride-deals-grid">
                <?php foreach ($deals as $deal): ?>
                    <div class="skyride-deal-card" onclick="skyride_track_deal_click('<?php echo esc_js($deal['id']); ?>');">
                        <?php if ($show_images && !empty($deal['image'])): ?>
                            <div class="skyride-deal-image">
                                <img src="<?php echo esc_url($deal['image']); ?>" alt="<?php echo esc_attr($deal['title']); ?>">
                            </div>
                        <?php endif; ?>
                        
                        <div class="skyride-deal-content">
                            <h4 class="skyride-deal-title"><?php echo esc_html($deal['title']); ?></h4>
                            <p class="skyride-deal-route"><?php echo esc_html($deal['route']); ?></p>
                            <p class="skyride-deal-operator">Operado por: <?php echo esc_html($deal['operator']); ?></p>
                            <p class="skyride-deal-passengers">Hasta <?php echo esc_html($deal['passengers']); ?> pasajeros</p>
                        </div>
                        
                        <div class="skyride-deal-footer">
                            <div class="skyride-deal-price">
                                <span class="skyride-price-amount">$<?php echo number_format($deal['price']); ?></span>
                                <span class="skyride-price-currency"><?php echo esc_html($deal['currency']); ?></span>
                            </div>
                            <a href="<?php echo esc_url($deal['bookingUrl']); ?>" target="_blank" class="skyride-deal-button">
                                Ver Oferta
                            </a>
                        </div>
                        
                        <?php if ($deal['featured']): ?>
                            <div class="skyride-deal-badge skyride-badge-featured">Destacado</div>
                        <?php endif; ?>
                        
                        <?php if ($deal['boosted']): ?>
                            <div class="skyride-deal-badge skyride-badge-boosted">Promocionado</div>
                        <?php endif; ?>
                    </div>
                <?php endforeach; ?>
            </div>
        </div>
        
        <script>
        // GA4 Cross-domain tracking
        function skyride_track_cta_click() {
            if (typeof gtag !== 'undefined') {
                gtag('event', 'skyride_cta_click', {
                    'custom_parameter_1': 'quote_button',
                    'custom_parameter_2': window.location.hostname
                });
            }
            
            // Also send to SkyRide analytics
            fetch('https://booking.skyride.city/api/analytics/track-event', {
                method: 'POST',
                headers: {'Content-Type': 'application/json'},
                body: JSON.stringify({
                    event: 'cta_click_wordpress',
                    parameters: {
                        source: 'wordpress',
                        page: window.location.href,
                        referrer: document.referrer
                    },
                    client_id: skyride_get_client_id()
                })
            }).catch(e => console.log('Analytics tracking failed:', e));
        }
        
        function skyride_track_deal_click(dealId) {
            if (typeof gtag !== 'undefined') {
                gtag('event', 'skyride_deal_click', {
                    'deal_id': dealId,
                    'source': 'wordpress'
                });
            }
            
            fetch('https://booking.skyride.city/api/analytics/track-event', {
                method: 'POST',
                headers: {'Content-Type': 'application/json'},
                body: JSON.stringify({
                    event: 'deal_click_wordpress',
                    parameters: {
                        deal_id: dealId,
                        source: 'wordpress',
                        page: window.location.href
                    },
                    client_id: skyride_get_client_id()
                })
            }).catch(e => console.log('Analytics tracking failed:', e));
        }
        
        function skyride_get_client_id() {
            // Simple client ID generation
            let clientId = localStorage.getItem('skyride_client_id');
            if (!clientId) {
                clientId = 'skyride_' + Date.now() + '_' + Math.random().toString(36).substr(2, 9);
                localStorage.setItem('skyride_client_id', clientId);
            }
            return clientId;
        }
        </script>
        <?php
        
        return ob_get_clean();
    }
    
    private function get_cta_config() {
        $cache_key = 'skyride_cta_config';
        $cached = get_transient($cache_key);
        
        if ($cached !== false) {
            return $cached;
        }
        
        $response = wp_remote_get('https://booking.skyride.city/api/wordpress/quote-cta', [
            'timeout' => 10,
            'headers' => [
                'User-Agent' => 'SkyRide-WordPress-Block/1.0'
            ]
        ]);
        
        if (is_wp_error($response)) {
            return [];
        }
        
        $body = wp_remote_retrieve_body($response);
        $data = json_decode($body, true);
        
        if ($data && isset($data['cta_config'])) {
            set_transient($cache_key, $data['cta_config'], 300); // Cache for 5 minutes
            return $data['cta_config'];
        }
        
        return [];
    }
    
    private function get_hot_deals($limit = 6) {
        $cache_key = 'skyride_hot_deals_' . $limit;
        $cached = get_transient($cache_key);
        
        if ($cached !== false) {
            return $cached;
        }
        
        $response = wp_remote_get(
            'https://booking.skyride.city/api/wordpress/hot-deals?limit=' . intval($limit),
            [
                'timeout' => 10,
                'headers' => [
                    'User-Agent' => 'SkyRide-WordPress-Block/1.0'
                ]
            ]
        );
        
        if (is_wp_error($response)) {
            return [];
        }
        
        $body = wp_remote_retrieve_body($response);
        $data = json_decode($body, true);
        
        if ($data && isset($data['deals'])) {
            set_transient($cache_key, $data['deals'], 180); // Cache for 3 minutes
            return $data['deals'];
        }
        
        return [];
    }
}

// Initialize the plugin
new SkyRideGutenbergBlocks();

// Add admin menu for SkyRide settings
add_action('admin_menu', function() {
    add_options_page(
        'SkyRide Settings',
        'SkyRide',
        'manage_options',
        'skyride-settings',
        function() {
            if (isset($_POST['submit'])) {
                update_option('skyride_ga4_id', sanitize_text_field($_POST['ga4_id']));
                echo '<div class="notice notice-success"><p>Configuración guardada!</p></div>';
            }
            
            $ga4_id = get_option('skyride_ga4_id', '');
            ?>
            <div class="wrap">
                <h1>SkyRide Settings</h1>
                <form method="post" action="">
                    <table class="form-table">
                        <tr>
                            <th scope="row">GA4 Measurement ID</th>
                            <td>
                                <input type="text" name="ga4_id" value="<?php echo esc_attr($ga4_id); ?>" 
                                       placeholder="G-XXXXXXXXXX" class="regular-text" />
                                <p class="description">ID de medición de Google Analytics 4 para tracking cross-domain</p>
                            </td>
                        </tr>
                    </table>
                    <?php submit_button(); ?>
                </form>
                
                <h2>Bloques Disponibles</h2>
                <p>Los siguientes bloques están disponibles en el editor de Gutenberg:</p>
                <ul>
                    <li><strong>SkyRide Quote CTA</strong> - Botón "Cotiza ahora" con opciones de embed</li>
                    <li><strong>SkyRide Hot Deals</strong> - Muestra ofertas especiales de vuelos charter</li>
                </ul>
                
                <h2>Información de Integración</h2>
                <table class="widefat">
                    <tr>
                        <th>API Endpoint</th>
                        <td>https://booking.skyride.city/api</td>
                    </tr>
                    <tr>
                        <th>Booking Platform</th>
                        <td>https://booking.skyride.city</td>
                    </tr>
                    <tr>
                        <th>CSP Frame-Ancestors</th>
                        <td>https://www.skyride.city</td>
                    </tr>
                    <tr>
                        <th>Cross-domain Tracking</th>
                        <td><?php echo $ga4_id ? '✅ Configured' : '❌ Not configured'; ?></td>
                    </tr>
                </table>
            </div>
            <?php
        }
    );
});
?>