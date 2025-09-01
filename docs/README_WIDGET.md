# Widget System Documentation

## Overview
SkyRide embeddable booking widget for WordPress and external websites.

## Architecture

### 1. Widget Core
Location: `frontend/widget/index.js`
- UMD module for universal compatibility
- Standalone booking form
- API integration for quotes and bookings

### 2. WordPress Integration
Location: `assets/skyride-frontend.js` + `wordpress-gutenberg-block.php`
- Custom Gutenberg block
- Dynamic widget loading
- Data attribute configuration

## Widget Deployment

### Build Process
```bash
cd frontend
npm run build:widget
# Creates: public/widget.js
```

### CDN Distribution
Widget served from:
```
https://booking.skyride.city/widget.js
```

## WordPress Usage

### 1. Install Plugin
Add `wordpress-gutenberg-block.php` to WordPress plugins.

### 2. Add Block
In Gutenberg editor:
1. Add "SkyRide Booking" block
2. Configure routes and styling
3. Publish page

### 3. Block Attributes
```json
{
  "routes": ["PTY-BLB", "PTY-DAV"],
  "theme": "light",
  "primaryColor": "#0066cc",
  "showLogo": true
}
```

## External Website Usage

### Basic Integration
```html
<div id="skyride-widget" 
     data-routes="PTY-BLB,PTY-DAV"
     data-theme="light"></div>
<script src="https://booking.skyride.city/widget.js"></script>
```

### Advanced Configuration
```html
<div id="skyride-widget"
     data-routes="PTY-BLB,PTY-DAV,PTY-CHX"
     data-theme="dark"
     data-primary-color="#cc0066" 
     data-show-logo="false"
     data-api-base="https://booking.skyride.city"
     data-ga-id="G-XXXXXXXXXX"></div>
```

## Widget Features

### 1. Route Selection
- Dropdown with configured routes
- Origin/destination autocomplete
- Popular routes pre-filled

### 2. Date/Passenger Selection
- Date picker (future dates only)
- Passenger count (1-8)
- Return date optional

### 3. Quote Generation
- Real-time pricing
- Multiple aircraft options
- Price breakdown display

### 4. Booking Flow
- Contact form
- WhatsApp CTA
- Hosted checkout option

## Configuration Options

### Data Attributes
- `data-routes`: Comma-separated route list
- `data-theme`: "light" or "dark"
- `data-primary-color`: Hex color code
- `data-show-logo`: "true" or "false"
- `data-api-base`: Override API endpoint
- `data-ga-id`: Google Analytics tracking

### Styling
Widget inherits site styling but includes:
- CSS custom properties for theming
- Responsive design
- Accessibility features

## Analytics Integration

### Google Analytics 4
Widget automatically tracks:
- Widget loads
- Quote requests
- Quote generated
- Contact form submissions
- WhatsApp CTA clicks

### Custom Events
```javascript
gtag('event', 'skyride_quote_generated', {
  'origin': 'PTY',
  'destination': 'BLB',
  'amount': 1500,
  'currency': 'USD'
});
```

## API Dependencies

### Required Endpoints
- `GET /api/availability`: Check flight availability
- `POST /api/quotes`: Generate pricing quotes
- `POST /api/contacts`: Submit contact forms

### Rate Limiting
Widget respects API rate limits:
- 5 requests per minute per IP
- Graceful degradation on limits

## Troubleshooting

### Common Issues
1. **Widget not loading**: Check CDN availability
2. **API errors**: Verify CORS settings
3. **Styling conflicts**: Use CSS specificity overrides

### Debug Mode
Add `data-debug="true"` for console logging:
```html
<div id="skyride-widget" data-debug="true"></div>
```
