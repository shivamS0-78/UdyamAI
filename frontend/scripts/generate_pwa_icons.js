const fs = require('fs');
const path = require('path');
const sharp = require('sharp');

const publicDir = path.join(__dirname, '../public');
const iconsDir = path.join(publicDir, 'icons');

if (!fs.existsSync(iconsDir)) {
  fs.mkdirSync(iconsDir, { recursive: true });
}

// Read the official white logo icon
const logoIconWhiteContent = fs.readFileSync(path.join(publicDir, 'logo-icon-white.svg'), 'utf8');

// Extract inner path elements from logo-icon-white.svg
const innerPathsMatch = logoIconWhiteContent.match(/<svg[^>]*>([\s\S]*?)<\/svg>/i);
const innerPaths = innerPathsMatch ? innerPathsMatch[1] : '';

function createIconSvg({ size, isMaskable = false, isApple = false }) {
  const rx = isMaskable || isApple ? 0 : Math.round(size * 0.22);
  
  // In maskable icons, keep logo within 65% safe zone. In standard icons, 70%.
  const logoScaleRatio = isMaskable ? 0.60 : 0.68;
  const targetLogoSize = size * logoScaleRatio;
  const scale = targetLogoSize / 545; // 545 is width of original viewBox
  
  // Original viewBox: "710 565 545 515"
  // Original center: x = 710 + 545/2 = 982.5, y = 565 + 515/2 = 822.5
  const origCenterX = 982.5;
  const origCenterY = 822.5;
  
  const targetCenterX = size / 2;
  const targetCenterY = size / 2;
  
  const translateX = targetCenterX - (origCenterX * scale);
  const translateY = targetCenterY - (origCenterY * scale);

  return `<?xml version="1.0" encoding="UTF-8"?>
<svg xmlns="http://www.w3.org/2000/svg" viewBox="0 0 ${size} ${size}" width="${size}" height="${size}">
  <defs>
    <linearGradient id="pwaBg" x1="0%" y1="0%" x2="100%" y2="100%">
      <stop offset="0%" stop-color="#0f172a" />
      <stop offset="50%" stop-color="#0b1329" />
      <stop offset="100%" stop-color="#020617" />
    </linearGradient>
    <radialGradient id="pwaAmbientGlow" cx="50%" cy="50%" r="50%">
      <stop offset="0%" stop-color="#10b981" stop-opacity="0.22" />
      <stop offset="50%" stop-color="#059669" stop-opacity="0.08" />
      <stop offset="100%" stop-color="#020617" stop-opacity="0" />
    </radialGradient>
    <filter id="subtleGlow" x="-20%" y="-20%" width="140%" height="140%">
      <feGaussianBlur stdDeviation="${size * 0.015}" result="blur" />
      <feComposite in="SourceGraphic" in2="blur" operator="over" />
    </filter>
  </defs>

  <!-- Background Layer -->
  <rect width="${size}" height="${size}" ${rx > 0 ? `rx="${rx}"` : ''} fill="url(#pwaBg)" />
  
  ${rx > 0 ? `<rect width="${size - 2}" height="${size - 2}" x="1" y="1" rx="${rx - 1}" fill="none" stroke="#1e293b" stroke-width="1.5" stroke-opacity="0.6" />` : ''}

  <!-- Ambient Glow -->
  <circle cx="${targetCenterX}" cy="${targetCenterY}" r="${size * 0.38}" fill="url(#pwaAmbientGlow)" />

  <!-- UdyamAI Official Brand Icon -->
  <g transform="translate(${translateX.toFixed(2)}, ${translateY.toFixed(2)}) scale(${scale.toFixed(4)})" filter="url(#subtleGlow)">
    ${innerPaths}
  </g>
</svg>`;
}

async function generateAllIcons() {
  const configs = [
    { name: 'icon-192x192', size: 192, isMaskable: false, isApple: false },
    { name: 'icon-512x512', size: 512, isMaskable: false, isApple: false },
    { name: 'maskable-icon-512x512', size: 512, isMaskable: true, isApple: false },
    { name: 'apple-touch-icon', size: 180, isMaskable: false, isApple: true },
  ];

  for (const cfg of configs) {
    const svgContent = createIconSvg(cfg);
    const svgPath = path.join(iconsDir, `${cfg.name}.svg`);
    const pngPath = path.join(iconsDir, `${cfg.name}.png`);

    // Write SVG
    fs.writeFileSync(svgPath, svgContent, 'utf8');
    console.log(`Generated SVG: ${svgPath}`);

    // Generate crisp PNG using Sharp
    await sharp(Buffer.from(svgContent))
      .resize(cfg.size, cfg.size)
      .png({ quality: 100, compressionLevel: 9 })
      .toFile(pngPath);
    console.log(`Generated PNG: ${pngPath} (${cfg.size}x${cfg.size})`);
  }

  console.log('All PWA icons generated successfully from official UdyamAI brand logo!');
}

generateAllIcons().catch(err => {
  console.error('Error generating icons:', err);
  process.exit(1);
});
