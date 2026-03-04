const fs = require('fs');
const path = require('path');
const JavaScriptObfuscator = require('javascript-obfuscator');
const postcss = require('postcss');
const cssnano = require('cssnano');

const SRC_DIR = path.resolve(__dirname, 'static');
const OUT_DIR = path.resolve(__dirname, 'output');

const JS_OBFUSCATOR_OPTIONS = {
    compact: true,
    controlFlowFlattening: true,
    controlFlowFlatteningThreshold: 0.75,
    deadCodeInjection: true,
    deadCodeInjectionThreshold: 0.4,
    stringArray: true,
    stringArrayEncoding: ['rc4'],
    stringArrayThreshold: 0.75,
    renameGlobals: false,
    reservedNames: [
        'APP', 'URLS', 'ICONS', 'STORAGE_KEY',
        'utils', 'modal', 'navigation',
        'showToast', 'decodeMessage', 'parseFetchError', 'getCookie',
        'open', 'close', 'closeAll',
        'renderContent', 'activateLink',
    ],
    identifierNamesGenerator: 'hexadecimal',
    selfDefending: true,
    splitStrings: true,
    splitStringsChunkLength: 10,
    target: 'browser',
};

function ensureDir(dir) {
    fs.mkdirSync(dir, {recursive: true});
}

function collectFiles(dir, ext) {
    const results = [];
    for (const entry of fs.readdirSync(dir, {withFileTypes: true})) {
        const full = path.join(dir, entry.name);
        if (entry.isDirectory()) {
            results.push(...collectFiles(full, ext));
        } else if (entry.name.endsWith(ext)) {
            results.push(full);
        }
    }
    return results;
}

function obfuscateJS() {
    const files = collectFiles(path.join(SRC_DIR, 'js'), '.js');
    console.log(`[JS] Found ${files.length} file(s)`);

    for (const file of files) {
        const rel = path.relative(SRC_DIR, file);
        const dest = path.join(OUT_DIR, rel);
        ensureDir(path.dirname(dest));

        const code = fs.readFileSync(file, 'utf-8');
        const result = JavaScriptObfuscator.obfuscate(code, JS_OBFUSCATOR_OPTIONS);
        fs.writeFileSync(dest, result.getObfuscatedCode(), 'utf-8');
        console.log(`[JS] ${rel}  OK`);
    }
}

async function minifyCSS() {
    const files = collectFiles(path.join(SRC_DIR, 'css'), '.css');
    console.log(`[CSS] Found ${files.length} file(s)`);

    const processor = postcss([cssnano({preset: 'default'})]);

    for (const file of files) {
        const rel = path.relative(SRC_DIR, file);
        const dest = path.join(OUT_DIR, rel);
        ensureDir(path.dirname(dest));

        const css = fs.readFileSync(file, 'utf-8');
        const result = await processor.process(css, {from: file, to: dest});
        fs.writeFileSync(dest, result.css, 'utf-8');
        console.log(`[CSS] ${rel}  OK`);
    }
}

function copyOtherAssets() {
    const exts = ['.svg', '.png', '.jpg', '.jpeg', '.gif', '.webp', '.ico', '.woff', '.woff2', '.ttf', '.eot'];
    let count = 0;

    function walk(dir) {
        for (const entry of fs.readdirSync(dir, {withFileTypes: true})) {
            const full = path.join(dir, entry.name);
            if (entry.isDirectory()) {
                walk(full);
            } else if (exts.some(e => entry.name.endsWith(e))) {
                const rel = path.relative(SRC_DIR, full);
                const dest = path.join(OUT_DIR, rel);
                ensureDir(path.dirname(dest));
                fs.copyFileSync(full, dest);
                count++;
            }
        }
    }

    walk(SRC_DIR);
    console.log(`[ASSETS] Copied ${count} file(s)`);
}

async function main() {
    console.log('=== Frontend Obfuscation Start ===');
    console.log(`Source: ${SRC_DIR}`);
    console.log(`Output: ${OUT_DIR}`);

    ensureDir(OUT_DIR);
    obfuscateJS();
    await minifyCSS();
    copyOtherAssets();

    console.log('=== Frontend Obfuscation Complete ===');
}

main().catch(err => {
    console.error('Obfuscation failed:', err);
    process.exit(1);
});
