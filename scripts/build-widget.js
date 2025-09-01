#!/usr/bin/env node
/**
 * Build script for SkyRide Widget
 * Creates a minified UMD bundle for distribution
 */

const fs = require('fs');
const path = require('path');

// Simple minification (for production, consider using terser or similar)
function minifyJS(code) {
    return code
        // Remove comments
        .replace(/\/\*[\s\S]*?\*\//g, '')
        .replace(/\/\/.*$/gm, '')
        // Remove extra whitespace
        .replace(/\s+/g, ' ')
        .replace(/;\s*}/g, ';}')
        .replace(/{\s*/g, '{')
        .replace(/}\s*/g, '}')
        .replace(/,\s*/g, ',')
        .trim();
}

function buildWidget() {
    console.log('🔨 Building SkyRide Widget...');

    const widgetPath = path.join(__dirname, '..', 'frontend', 'widget', 'index.js');
    const outputPath = path.join(__dirname, '..', 'frontend', 'public', 'widget.js');

    // Read source
    const source = fs.readFileSync(widgetPath, 'utf8');

    // Add build timestamp and version
    const buildInfo = `
/* SkyRide Booking Widget v2.0.0 */
/* Built: ${new Date().toISOString()} */
/* https://skyride.city */
`;

    // Create minified version
    const minified = minifyJS(source);
    const output = buildInfo + minified;

    // Ensure public directory exists
    const publicDir = path.dirname(outputPath);
    if (!fs.existsSync(publicDir)) {
        fs.mkdirSync(publicDir, { recursive: true });
    }

    // Write output
    fs.writeFileSync(outputPath, output);

    const originalSize = source.length;
    const minifiedSize = output.length;
    const savings = ((originalSize - minifiedSize) / originalSize * 100).toFixed(1);

    console.log(`✅ Widget built successfully!`);
    console.log(`   Original: ${originalSize} bytes`);
    console.log(`   Minified: ${minifiedSize} bytes (${savings}% smaller)`);
    console.log(`   Output: ${outputPath}`);
}

// Run if called directly
if (require.main === module) {
    buildWidget();
}

module.exports = { buildWidget };
