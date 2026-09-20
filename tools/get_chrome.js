// Extract @sparticuz/chromium headless binary (+ AL2023 system libs) and print paths as JSON
const path = require('path');
const { createRequire } = require('module');

const here = path.join(__dirname, 'chromehelper');
const creq = createRequire(path.join(here, 'package.json'));

(async () => {
  const mod = creq('@sparticuz/chromium');
  const chromium = mod.default || mod;
  const execPath = await chromium.executablePath();
  // Bundled Amazon Linux 2023 system libs (libnspr4, libnss3, ...) for minimal containers.
  // inflate() is idempotent: returns early if already extracted.
  const bin = path.join(here, 'node_modules', '@sparticuz', 'chromium', 'bin', 'al2023.tar.br');
  const libDir = (await mod.inflate(bin)) + '/lib';
  console.log(JSON.stringify({ execPath, libDir, args: chromium.args }));
})().catch(e => { console.error(e); process.exit(1); });
