#!/usr/bin/env node

const fs = require('fs');
const path = require('path');
const { chromium } = require('playwright');

function parseArgs(argv) {
  const args = {
    cdpUrl: 'http://127.0.0.1:9222',
    configPath: path.resolve(__dirname, '../src/tiktok_uploader_cdp/config.toml'),
    outPath: path.resolve(process.cwd(), 'tmp/selector_dom_report.json'),
    limitPerSelector: 3,
  };

  for (let i = 2; i < argv.length; i += 1) {
    const key = argv[i];
    const value = argv[i + 1];
    if (!value || value.startsWith('--')) {
      throw new Error(`Missing value for ${key}`);
    }
    if (key === '--cdp-url') args.cdpUrl = value;
    else if (key === '--config') args.configPath = path.resolve(value);
    else if (key === '--out') args.outPath = path.resolve(value);
    else if (key === '--limit') args.limitPerSelector = Number(value);
    else throw new Error(`Unknown argument: ${key}`);
    i += 1;
  }

  return args;
}

function extractQuotedValues(line) {
  const values = [];
  const re = /"((?:\\.|[^"\\])*)"/g;
  let m;
  while ((m = re.exec(line)) !== null) {
    values.push(m[1].replace(/\\"/g, '"'));
  }
  return values;
}

function parseSelectorsFromToml(tomlText) {
  const lines = tomlText.split(/\r?\n/);
  const selectors = {};
  let inSelectors = false;
  let currentKey = null;
  let currentValues = [];

  const flushArray = () => {
    if (currentKey) {
      selectors[currentKey] = [...currentValues];
      currentKey = null;
      currentValues = [];
    }
  };

  for (const rawLine of lines) {
    const line = rawLine.trim();

    if (!line || line.startsWith('#')) continue;

    if (line.startsWith('[') && line.endsWith(']')) {
      if (inSelectors) {
        flushArray();
      }
      inSelectors = line === '[selectors]';
      continue;
    }

    if (!inSelectors) continue;

    if (currentKey) {
      const vals = extractQuotedValues(line);
      currentValues.push(...vals);
      if (line.includes(']')) {
        flushArray();
      }
      continue;
    }

    const eq = line.indexOf('=');
    if (eq < 0) continue;
    const key = line.slice(0, eq).trim();
    const rhs = line.slice(eq + 1).trim();

    if (rhs.startsWith('[')) {
      const vals = extractQuotedValues(rhs);
      if (rhs.includes(']')) {
        selectors[key] = vals;
      } else {
        currentKey = key;
        currentValues = vals;
      }
      continue;
    }

    if (rhs.startsWith('"')) {
      const vals = extractQuotedValues(rhs);
      selectors[key] = vals.length > 0 ? vals : [rhs.replace(/^"|"$/g, '')];
    }
  }

  if (currentKey) {
    flushArray();
  }

  return selectors;
}

async function inspectSelector(frame, selector, limit) {
  try {
    const loc = frame.locator(selector);
    const count = await loc.count();
    const sample = [];

    const max = Math.min(count, limit);
    for (let i = 0; i < max; i += 1) {
      const item = loc.nth(i);
      const visible = await item.isVisible().catch(() => false);
      const enabled = await item.isEnabled().catch(() => false);
      const html = await item.evaluate((el) => el.outerHTML).catch(() => null);
      const tag = await item.evaluate((el) => el.tagName).catch(() => null);
      sample.push({ index: i, tag, visible, enabled, outerHTML: html });
    }

    return { selector, count, sample, error: null };
  } catch (err) {
    return { selector, count: 0, sample: [], error: String(err) };
  }
}

async function inspectPage(contextIndex, pageIndex, page, selectorsMap, limit) {
  const frames = page.frames();
  const frameReports = [];

  for (let fIdx = 0; fIdx < frames.length; fIdx += 1) {
    const frame = frames[fIdx];
    const selectorResults = {};

    for (const [key, list] of Object.entries(selectorsMap)) {
      const arr = Array.isArray(list) ? list : [String(list)];
      const checks = [];
      for (const sel of arr) {
        checks.push(await inspectSelector(frame, sel, limit));
      }
      selectorResults[key] = checks;
    }

    frameReports.push({
      frameIndex: fIdx,
      frameName: frame.name() || '',
      frameUrl: frame.url(),
      selectors: selectorResults,
    });
  }

  return {
    contextIndex,
    pageIndex,
    pageUrl: page.url(),
    title: await page.title().catch(() => ''),
    frames: frameReports,
  };
}

function summarizeUploadInput(report) {
  const lines = [];
  for (const page of report.pages) {
    for (const frame of page.frames) {
      const checks = frame.selectors.upload_input || [];
      for (const c of checks) {
        if (c.count > 0) {
          lines.push(
            `context=${page.contextIndex} page=${page.pageIndex} frame=${frame.frameIndex} ` +
              `selector=${JSON.stringify(c.selector)} count=${c.count}`
          );
        }
      }
    }
  }
  return lines;
}

async function main() {
  const args = parseArgs(process.argv);
  const tomlText = fs.readFileSync(args.configPath, 'utf8');
  const selectors = parseSelectorsFromToml(tomlText);

  const browser = await chromium.connectOverCDP(args.cdpUrl);
  const pages = [];

  for (let cIdx = 0; cIdx < browser.contexts().length; cIdx += 1) {
    const context = browser.contexts()[cIdx];
    for (let pIdx = 0; pIdx < context.pages().length; pIdx += 1) {
      const page = context.pages()[pIdx];
      pages.push(await inspectPage(cIdx, pIdx, page, selectors, args.limitPerSelector));
    }
  }

  const report = {
    createdAtUtc: new Date().toISOString(),
    cdpUrl: args.cdpUrl,
    configPath: args.configPath,
    selectorsKeys: Object.keys(selectors),
    pages,
  };

  fs.mkdirSync(path.dirname(args.outPath), { recursive: true });
  fs.writeFileSync(args.outPath, JSON.stringify(report, null, 2), 'utf8');

  const summary = summarizeUploadInput(report);
  console.log(`Saved report: ${args.outPath}`);
  if (summary.length === 0) {
    console.log('No upload_input selectors matched in any context/page/frame.');
  } else {
    console.log('upload_input matches:');
    for (const line of summary) console.log(`- ${line}`);
  }

  await browser.close();
}

main().catch((err) => {
  console.error(String(err));
  process.exit(1);
});
