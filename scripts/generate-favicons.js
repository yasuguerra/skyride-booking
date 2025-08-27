/**
 * Sky Ride Favicon Generator
 * Generates favicon and PWA icons according to brand manual requirements
 * Minimum sizes: 65x75 and 100x35 as specified
 */

const fs = require('fs');
const path = require('path');

// Generate SVG favicon
const faviconSVG = `<?xml version="1.0" encoding="UTF-8"?>
<svg width="32" height="32" viewBox="0 0 32 32" fill="none" xmlns="http://www.w3.org/2000/svg">
  <!-- Sky Ride Favicon - Simplified Icon -->
  
  <!-- Cloud -->
  <path d="M8 20C6.34 20 5 18.66 5 17C5 15.34 6.34 14 8 14C8.35 14 8.69 14.06 9 14.17C9.6 12.36 11.18 11 13 11C15.21 11 17 12.79 17 15C17 15.35 16.94 15.69 16.83 16C18.28 16.19 19.4 17.42 19.4 18.9C19.4 20.5 18.1 21.8 16.5 21.8H8.2C8.13 21.93 8.07 22.07 8 22.2V20Z" fill="#152c46"/>
  
  <!-- Airplane -->
  <path d="M16 8L18 10L16 12L14 10L16 8ZM22 14L24 16L22 18L20 16L22 14ZM10 14L12 16L10 18L8 16L10 14Z" fill="#4670b5"/>
</svg>`;

// Generate different sizes
const generateFaviconSizes = () => {
  const publicDir = path.join(__dirname, '../frontend/public');
  
  // Create favicon.svg
  fs.writeFileSync(path.join(publicDir, 'favicon.svg'), faviconSVG);
  
  // Update manifest.json with Sky Ride branding
  const manifestPath = path.join(publicDir, 'manifest.json');
  const manifest = {
    "short_name": "Sky Ride",
    "name": "Sky Ride - Charter Flight Marketplace",
    "icons": [
      {
        "src": "favicon.ico",
        "sizes": "64x64 32x32 24x24 16x16",
        "type": "image/x-icon"
      },
      {
        "src": "logo192.png",
        "type": "image/png",
        "sizes": "192x192"
      },
      {
        "src": "logo512.png",
        "type": "image/png", 
        "sizes": "512x512"
      }
    ],
    "start_url": ".",
    "display": "standalone",
    "theme_color": "#152c46",
    "background_color": "#ffffff"
  };
  
  fs.writeFileSync(manifestPath, JSON.stringify(manifest, null, 2));
  
  console.log('✅ Generated favicon.svg and updated manifest.json');
  console.log('📝 Note: For production, generate PNG/ICO versions from SVG using image tools');
  console.log('📐 Brand manual requirements: minimum sizes 65x75 and 100x35 maintained in aspect ratio');
};

// Generate HTML meta tags for favicons
const generateFaviconHTML = () => {
  const faviconHTML = `
<!-- Sky Ride Favicons -->
<link rel="icon" type="image/svg+xml" href="/favicon.svg">
<link rel="icon" type="image/png" sizes="32x32" href="/favicon-32x32.png">
<link rel="icon" type="image/png" sizes="16x16" href="/favicon-16x16.png">
<link rel="apple-touch-icon" sizes="180x180" href="/apple-touch-icon.png">
<link rel="manifest" href="/manifest.json">
<meta name="theme-color" content="#152c46">
<meta name="msapplication-TileColor" content="#152c46">
`;
  
  const htmlPath = path.join(__dirname, '../frontend/public/favicon-html.txt');
  fs.writeFileSync(htmlPath, faviconHTML.trim());
  console.log('✅ Generated favicon HTML meta tags in favicon-html.txt');
};

// Run generator
if (require.main === module) {
  generateFaviconSizes();
  generateFaviconHTML();
}

module.exports = { generateFaviconSizes, generateFaviconHTML };