# Sky Ride Brand Implementation Guide

## Official Brand Colors

### Primary Palette
- **Primary Navy**: `#152c46` (RGB 21,44,70)
- **Secondary Blue**: `#4670b5` (RGB 70,112,181)  
- **Corporate Black**: `#000000` (Editorial use, contrast)

### Derived Colors
- **Primary Light**: `rgba(21, 44, 70, 0.1)`
- **Primary Dark**: `#0f1f31`
- **Accent Light**: `rgba(70, 112, 181, 0.1)`
- **Accent Dark**: `#365a96`

## Typography

### Official Font
- **Primary**: Open Sans (web, Google Fonts)
- **Fallbacks**: `system-ui`, `-apple-system`, `BlinkMacSystemFont`, `sans-serif`

### Implementation
```css
font-family: 'Open Sans', system-ui, -apple-system, sans-serif;
```

## Design Tokens

### Radius
- **Primary**: `16px` (--sr-radius)
- **Small**: `12px` (--sr-radius-sm)

### Shadows
- **Primary**: `0 8px 24px rgba(21, 44, 70, 0.15)` (--sr-shadow)
- **Small**: `0 4px 16px rgba(21, 44, 70, 0.12)` (--sr-shadow-sm)

## Brand Usage Rules

### ✅ Permitted Uses
- Use official colors exactly as specified
- Maintain proper aspect ratios for logos
- Apply Open Sans typography consistently
- Use approved design tokens

### ❌ Prohibited Actions
- **DO NOT** rotate, distort, or stretch logos
- **DO NOT** change colors outside approved palette  
- **DO NOT** use arbitrary alignments or transformations
- **DO NOT** apply custom colors to SVG/PNG assets

## Asset Linter Implementation

### Color Validation
The brand implementation includes automated validation to prevent unauthorized colors:

```javascript
// Blocks non-approved colors in SVG/PNG assets
const approvedColors = ['#152c46', '#4670b5', '#000000', '#ffffff'];
// Linter checks all assets against this list
```

### Minimum Sizes
- **Logo Minimum**: 65×75 pixels
- **Wordmark Minimum**: 100×35 pixels

## Component Styling

### Buttons
```css
/* Primary Button */
.btn-primary {
  background-color: var(--sr-color-primary);
  color: white;
  border-radius: var(--sr-radius);
  font-family: var(--sr-font-family);
}

.btn-primary:hover {
  background-color: var(--sr-color-accent);
}

/* Secondary Button */
.btn-secondary {
  background-color: transparent;
  color: var(--sr-color-primary);
  border: 2px solid var(--sr-color-primary);
}
```

### Cards
```css
.card {
  background: white;
  border-radius: var(--sr-radius);
  box-shadow: var(--sr-shadow);
  border: none;
}
```

### Badges
```css
/* Sky Ride Protection Badge */
.sr-protection-badge {
  background: linear-gradient(135deg, var(--sr-color-primary) 0%, var(--sr-color-accent) 100%);
  color: white;
  padding: 8px 16px;
  border-radius: var(--sr-radius);
}

/* Price Match Badge */
.sr-pricematch-badge {
  background-color: var(--sr-color-accent-light);
  color: var(--sr-color-accent-dark);
  border: 1px solid var(--sr-color-accent);
}
```

## WordPress Blocks Integration

### Block Styling
All WordPress Gutenberg blocks use Sky Ride brand tokens:

```css
.wp-block-skyride {
  font-family: var(--sr-font-family);
}

.skyride-cta-primary {
  background: var(--sr-color-primary);
  border-radius: var(--sr-radius);
}
```

### Hot Deals Block
```css
.skyride-deal-card.sr-hot-deals-card::before {
  content: 'HOT DEAL';
  background: var(--sr-color-accent);
  color: white;
}
```

## UI Components Branded

### Current Implementation Status
- ✅ Navbar with wordmark and primary CTA
- ✅ Hosted Quote with timer and Sky Ride Protection badge
- ✅ Checkout with proper pricing breakdown
- ✅ Portal Operator with navy header
- ✅ Hot Deals with accent band
- ✅ WordPress blocks with brand tokens

### Pricing Display Format
```html
<div class="sr-checkout-item">
  <span>Precio del vuelo</span>
  <span>$X,XXX</span>
</div>
<div class="sr-checkout-item">
  <span class="sr-service-fee">Service fee Sky Ride</span>
  <span class="sr-service-fee">$XXX</span>
</div>
```

## Asset Management

### File Structure
```
/frontend/public/brand/
├── logo-primary.svg        # Main logo (color version)
├── logo-primary.png        # PNG fallback
├── wordmark.svg           # Navbar wordmark
└── favicon.svg            # Favicon

/scripts/
└── generate-favicons.js   # Favicon generator utility
```

### CSP Compliance
WordPress blocks maintain proper Content Security Policy:
```
frame-ancestors https://www.skyride.city
```

## Testing & Quality Assurance

### Visual Validation
- Logo proportions maintained (aspect ratio preserved)
- Brand colors applied consistently
- Typography rendering correctly across browsers
- Shadow and radius tokens working properly

### Automated Checks
- Asset linter validates color compliance
- Lighthouse performance ≥ 90 for branded pages
- Accessibility compliance maintained

### Brand Manual References
All implementations reference official Sky Ride brand manual specifications for:
- Color accuracy (Navy #152c46, Blue #4670b5)
- Typography specifications (Open Sans)
- Minimum size requirements
- Usage restrictions and guidelines

---

**Note**: This implementation strictly follows the Sky Ride brand manual. Any deviations from approved colors, typography, or usage guidelines are automatically flagged by the asset linter system.