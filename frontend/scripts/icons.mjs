// Renders the PWA icons and favicon from the SVG logo. Run: npm run icons
import sharp from 'sharp'
import fs from 'fs'

const mark = fs.readFileSync('public/logo-mark.svg')
const full = fs.readFileSync('scripts/logo-fullbleed.svg')
const jobs = [
  [mark, 192, 'public/icon-192.png'],
  [mark, 512, 'public/icon-512.png'],
  [full, 512, 'public/icon-maskable-512.png'],
  [full, 180, 'public/apple-touch-icon.png'],
  [mark, 64, 'public/favicon.png'],
  [Buffer.from(fs.readFileSync('public/logo.svg')), 1180, 'public/logo.png'],
]
for (const [svg, size, out] of jobs) {
  await sharp(svg, { density: 384 }).resize(size).png().toFile(out)
  console.log('wrote', out)
}
