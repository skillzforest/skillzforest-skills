#!/usr/bin/env node
// skf-audit-my-cache — audits the HTTP cache policy of a website, as an anonymous visitor sees it.
//
// From a start URL: follows the redirects, reads the page, finds every file it loads (styles, scripts and the
// modules they import, preloads, pictures, icons, fonts, CSS url()), a few other pages of the site, and asks each
// one twice: once plainly, once with its validators (ETag / Last-Modified) to see if the server answers 304.
// Each answer is judged (versioned file? kept how long? revalidated? compressed?), and the report says what a
// second visit downloads again today.
//
// Node 18+, standard library only.
//   node audit_cache.mjs <url> [--pages 3] [--max 150] [--json report.json] [--md report.md] [--api /api/x,/api/y]
//
// Exit code: 0 (report written), 2 (the start URL could not be read).

import http from 'node:http';
import https from 'node:https';
import { writeFileSync } from 'node:fs';
import zlib from 'node:zlib';

const args = process.argv.slice(2);
const opt = (name, def) => { const i = args.indexOf(`--${name}`); return i >= 0 ? args[i + 1] : def; };
const START = args.find((a, i) => !a.startsWith('--') && !(i > 0 && args[i - 1].startsWith('--')));
if (!START) {
  console.error('Usage: node audit_cache.mjs <url> [--pages 3] [--max 150] [--json out.json] [--md out.md] [--api /path,/path]');
  process.exit(2);
}
const PAGES = Number(opt('pages', 3));
const MAX = Number(opt('max', 150));
const API = (opt('api', '') || '').split(',').map((s) => s.trim()).filter(Boolean);
const UA = 'Mozilla/5.0 (compatible; skf-audit-my-cache/1.0)';
const ENCODINGS = 'gzip, deflate, br';

// ---------- HTTP ----------

/** One request, no redirect followed; the body as it came (raw bytes) and decoded. */
function request(url, headers = {}, { timeout = 20000 } = {}) {
  return new Promise((resolve) => {
    const u = new URL(url);
    const lib = u.protocol === 'http:' ? http : https;
    const t0 = Date.now();
    const req = lib.request(u, { method: 'GET', headers: { 'user-agent': UA, 'accept-encoding': ENCODINGS, accept: '*/*', ...headers }, timeout }, (res) => {
      const chunks = [];
      res.on('data', (c) => chunks.push(c));
      res.on('end', () => {
        const raw = Buffer.concat(chunks);
        let body = raw;
        const enc = String(res.headers['content-encoding'] || '').toLowerCase();
        try {
          if (enc === 'gzip') body = zlib.gunzipSync(raw);
          else if (enc === 'br') body = zlib.brotliDecompressSync(raw);
          else if (enc === 'deflate') body = zlib.inflateSync(raw);
          else if (enc === 'zstd' && zlib.zstdDecompressSync) body = zlib.zstdDecompressSync(raw);
        } catch { body = raw; }
        resolve({ url, status: res.statusCode, headers: res.headers, bytes: raw.length, body, ms: Date.now() - t0 });
      });
    });
    req.on('timeout', () => req.destroy(new Error('timeout')));
    req.on('error', (err) => resolve({ url, status: 0, error: err.message, headers: {}, bytes: 0, body: Buffer.alloc(0), ms: Date.now() - t0 }));
    req.end();
  });
}

/** Follows redirects (at most 8), keeping each hop. */
async function follow(url) {
  const hops = [];
  let cur = url;
  for (let i = 0; i < 8; i++) {
    const r = await request(cur, { accept: 'text/html,application/xhtml+xml,*/*;q=0.8' });
    hops.push(r);
    if (r.status >= 300 && r.status < 400 && r.headers.location) cur = new URL(r.headers.location, cur).href;
    else break;
  }
  return hops;
}

// ---------- Parsing ----------

const attr = (tag, name) => {
  const m = new RegExp(`\\s${name}\\s*=\\s*("([^"]*)"|'([^']*)'|([^\\s>]+))`, 'i').exec(tag);
  return m ? (m[2] ?? m[3] ?? m[4] ?? '').replace(/&amp;/g, '&') : null;
};
const srcset = (v) => (v ? v.split(',').map((s) => s.trim().split(/\s+/)[0]).filter(Boolean) : []);

/** The files an HTML page loads, with a kind each; and its links to other pages. */
function parseHtml(html, base) {
  const files = [];
  const links = [];
  const add = (u, kind) => { if (u && !/^(data|blob|javascript|mailto|tel):/i.test(u)) { try { files.push({ url: new URL(u, base).href, kind }); } catch { /* bad url */ } } };
  for (const tag of html.match(/<link\b[^>]*>/gi) ?? []) {
    const rel = (attr(tag, 'rel') || '').toLowerCase();
    const href = attr(tag, 'href');
    if (/stylesheet/.test(rel)) add(href, 'css');
    else if (/modulepreload/.test(rel)) add(href, 'js');
    else if (/preload|prefetch/.test(rel)) add(href, (attr(tag, 'as') || 'other').replace('script', 'js').replace('style', 'css'));
    else if (/icon|manifest/.test(rel)) add(href, 'image');
  }
  for (const tag of html.match(/<script\b[^>]*>/gi) ?? []) add(attr(tag, 'src'), 'js');
  for (const tag of html.match(/<(img|source|video|audio)\b[^>]*>/gi) ?? []) {
    const kind = /^<(video|audio)/i.test(tag) ? 'media' : 'image';
    add(attr(tag, 'src'), kind);
    for (const s of srcset(attr(tag, 'srcset'))) add(s, 'image');
    add(attr(tag, 'poster'), 'image');
  }
  for (const m of html.matchAll(/url\(\s*['"]?([^'")]+)['"]?\s*\)/gi)) add(m[1], 'image');
  for (const tag of html.match(/<a\b[^>]*>/gi) ?? []) {
    const href = attr(tag, 'href');
    if (!href || href.startsWith('#') || /^(mailto|tel|javascript):/i.test(href)) continue;
    try { links.push(new URL(href, base).href.split('#')[0]); } catch { /* bad url */ }
  }
  return { files, links };
}
/** What a script imports (static and dynamic, relative paths only) and what a style sheet loads. */
function parseAsset(text, base, kind) {
  const out = [];
  const add = (u, k) => { try { out.push({ url: new URL(u, base).href, kind: k }); } catch { /* bad url */ } };
  if (kind === 'js') {
    for (const m of text.matchAll(/(?:\bfrom\s*|\bimport\s*\(\s*|\bimport\s+)['"](\.{1,2}\/[^'"]+|\/[^/'"][^'"]*)['"]/g)) add(m[1], 'js');
  } else if (kind === 'css') {
    for (const m of text.matchAll(/@import\s+(?:url\()?\s*['"]?([^'")\s;]+)/gi)) add(m[1], 'css');
    for (const m of text.matchAll(/url\(\s*['"]?([^'")]+)['"]?\s*\)/gi)) if (!/^data:/i.test(m[1])) add(m[1], /\.(woff2?|ttf|otf|eot)(\?|$)/i.test(m[1]) ? 'font' : 'image');
  }
  return out;
}

// ---------- Judging ----------

function cacheControl(h) {
  const d = {};
  for (const part of String(h || '').split(',')) {
    const [k, v] = part.trim().split('=');
    if (k) d[k.toLowerCase()] = v === undefined ? true : v.replace(/"/g, '');
  }
  return d;
}
const kindOf = (url, type) => {
  const p = new URL(url).pathname.toLowerCase();
  type = String(type || '').toLowerCase();
  if (type.includes('text/html')) return 'html';
  if (/\.(m?js)$/.test(p) || type.includes('javascript')) return 'js';
  if (/\.css$/.test(p) || type.includes('text/css')) return 'css';
  if (/\.(woff2?|ttf|otf|eot)$/.test(p) || type.includes('font')) return 'font';
  if (/\.(png|jpe?g|gif|webp|avif|svg|ico)$/.test(p) || type.startsWith('image/')) return 'image';
  if (/\.(mp4|webm|mp3|m4a|ogg|wav)$/.test(p) || type.startsWith('video/') || type.startsWith('audio/')) return 'media';
  if (type.includes('json')) return 'data';
  return 'other';
};
/** A name or a query carrying the content's hash (app.3f9a1c2e.js, app-BN3x8k2Q.js, app.js?v=3f9a1c2e). */
function versioned(url) {
  const u = new URL(url);
  const base = u.pathname.split('/').pop() || '';
  const stem = base.replace(/\.[a-z0-9]+$/i, '');
  if (/[.\-_~][0-9a-f]{7,}$/i.test(stem) || /[.\-_~][0-9a-f]{7,}[.\-_]/i.test(base)) return true;
  const tail = /[.\-_~]([A-Za-z0-9]{8,})$/.exec(stem);
  if (tail && (tail[1].match(/\d/g) ?? []).length >= 2 && /[A-Za-z]/.test(tail[1])) return true;
  for (const [k, v] of u.searchParams) if (/^(v|ver|version|h|hash|rev|t|build|_)$/i.test(k) && /^[A-Za-z0-9._-]{4,}$/.test(v)) return true;
  if (/\/(_next\/static|_astro|assets\/immutable|_nuxt|build\/[a-f0-9]{8,})\//i.test(u.pathname)) return true;
  return false;
}
const TEXTY = new Set(['html', 'js', 'css', 'data', 'other']);
const DAY = 86400;

/** The verdicts of one answer. Each: [code, severity (critical|high|medium|low|info), words]. */
function judge(e) {
  const out = [];
  const cc = e.cc;
  const maxAge = cc['max-age'] !== undefined ? Number(cc['max-age']) : cc['s-maxage'] !== undefined ? null : e.expires ? Math.max(0, Math.round((Date.parse(e.expires) - Date.parse(e.date || new Date())) / 1000)) : null;
  e.freshFor = cc['no-store'] || cc['no-cache'] ? 0 : maxAge;
  const validator = Boolean(e.etag || e.lastModified);
  const big = e.bytes > 20 * 1024;
  if (e.status === 0) return [['UNREACHABLE', 'high', `not answered (${e.error})`]];
  if (e.status >= 300 && e.status < 400) return [['REDIRECT', 'info', `redirects (${e.status}) to ${e.location}`]];
  if (e.status >= 400) return [['ERROR_STATUS', e.status === 404 ? 'medium' : 'high', `answers ${e.status}`]];
  if (e.setCookie && (cc.public || cc['s-maxage'] !== undefined)) out.push(['PUBLIC_WITH_COOKIE', 'critical', 'sets a cookie while a shared cache (CDN, proxy) may keep it: a visitor can get another one\'s session']);
  if (!e.ccRaw && !e.expires) out.push(['NO_CACHE_HEADER', e.kind === 'html' ? 'medium' : 'medium', validator ? 'no Cache-Control: the browser guesses (about 10 % of the file\'s age), unpredictable after a deploy' : 'no Cache-Control and no validator: re-downloaded, or kept for a guessed time']);
  if (e.api) {
    if (cc['no-store'] || cc.private) out.push(['API_NOT_SHARED', 'info', 'an API answer never kept (or only by this browser): right for personal data; for data that is the same for every anonymous visitor, a short public cache (max-age=60, stale-while-revalidate) with Vary: Authorization, Cookie saves a request per page']);
    else if (e.setCookie || !/authorization|cookie/i.test(e.vary || '')) out.push(['API_CACHE_UNKEYED', (e.freshFor ?? 0) > 0 ? 'high' : 'low', 'an API answer that may be kept without Vary: Authorization/Cookie: if it differs for a signed-in visitor, a cache can mix the two']);
  } else if (e.kind === 'html') {
    if (e.freshFor !== null && e.freshFor > 300 && !cc.private) out.push(['HTML_LONG', 'high', `the page is kept ${human(e.freshFor)} without asking: after a deploy, visitors see the old page (and old file names)`]);
    if ((cc['no-cache'] || e.freshFor === 0) && !validator) out.push(['NO_VALIDATOR', 'low', 'asked again each visit without ETag/Last-Modified: always a full download (a 304 would cost nothing)']);
  } else {
    if (cc['no-store']) out.push(['NO_STORE_ASSET', big ? 'high' : 'medium', 'no-store on a site file: never kept, re-downloaded on every page']);
    else if ((cc['no-cache'] || e.freshFor === 0 || (e.freshFor === null && !e.ccRaw)) && !validator) out.push(['NO_VALIDATOR', big ? 'critical' : 'high', 'must be asked again each visit but has no ETag nor Last-Modified: downloaded in full every time']);
    if (validator && e.revalidated !== undefined && e.revalidated !== 304 && (cc['no-cache'] || (e.freshFor ?? 0) < DAY)) out.push(['VALIDATOR_IGNORED', 'high', `has a validator but a conditional request still answers ${e.revalidated}: the 304 never happens (a proxy or compression may change the ETag)`]);
    if (!e.versioned && (cc.immutable || (e.freshFor ?? 0) >= 7 * DAY)) out.push(['LONG_UNVERSIONED', ['js', 'css'].includes(e.kind) ? 'high' : 'medium', `kept ${cc.immutable ? 'as immutable ' : ''}${human(e.freshFor)} under a name that does not change with its content: after a deploy, returning visitors keep the old file`]);
    if (e.versioned && !cc['no-store'] && (e.freshFor ?? 0) < 30 * DAY) out.push(['VERSIONED_SHORT', big ? 'medium' : 'low', `the name carries a version, yet it is kept only ${human(e.freshFor ?? 0)}: it could be kept a year (immutable)`]);
    if (e.versioned && (e.freshFor ?? 0) >= 30 * DAY && !cc.immutable) out.push(['NOT_IMMUTABLE', 'info', 'versioned and long-lived: add immutable so a reload does not ask again']);
    if (!e.versioned && ['js', 'css'].includes(e.kind) && validator && (cc['no-cache'] || (e.freshFor ?? 0) < DAY)) out.push(['UNVERSIONED_REVALIDATED', 'low', 'safe (asked again, 304 when unchanged) but one round trip per file each visit: versioning its name would let it be kept a year']);
  }
  if (TEXTY.has(e.kind) && !e.encoding && e.bytes > 1024) out.push(['NOT_COMPRESSED', e.bytes > 50 * 1024 ? 'high' : 'medium', 'text sent without compression (gzip, br or zstd): 3 to 5 times heavier (a local server without its proxy often shows this, check production)']);
  if (/\*/.test(e.vary || '')) out.push(['VARY_STAR', 'medium', 'Vary: * — never reused from cache']);
  if (/user-agent/i.test(e.vary || '')) out.push(['VARY_UA', 'low', 'Vary: User-Agent splits every shared cache by browser version']);
  if (!out.length) out.push(['OK', 'info', 'fine']);
  return out;
}
const human = (s) => (s === null || s === undefined ? 'an unknown time' : s >= 365 * DAY ? `${Math.round(s / (365 * DAY))} y` : s >= DAY ? `${Math.round(s / DAY)} d` : s >= 3600 ? `${Math.round(s / 3600)} h` : s >= 60 ? `${Math.round(s / 60)} min` : `${s} s`);
const kb = (b) => (b >= 1024 * 1024 ? `${(b / 1024 / 1024).toFixed(1)} MB` : `${(b / 1024).toFixed(b < 10240 ? 1 : 0)} KB`);

/** What a second visit within the hour costs for this file: its full size, a 304, or nothing. */
function secondVisit(e) {
  if (e.status === 0 || e.status >= 400) return { cost: 0, how: 'error' };
  if (e.status >= 300 && e.status < 400) return { cost: 0, how: 'redirect' };
  const cc = e.cc;
  if (cc['no-store']) return { cost: e.bytes, how: 'full' };
  const fresh = e.freshFor;
  if (fresh !== null && fresh >= 3600 && !cc['no-cache']) return { cost: 0, how: 'cache' };
  if (e.revalidated === 304) return { cost: 300, how: '304' };
  return { cost: e.bytes, how: 'full' };
}

// ---------- Run ----------

async function inspect(url, kindHint) {
  const r = await request(url);
  const h = r.headers;
  const e = {
    url, kind: kindOf(url, h['content-type']) === 'other' && kindHint ? kindHint : kindOf(url, h['content-type']),
    status: r.status, error: r.error, bytes: r.bytes, ms: r.ms,
    ccRaw: h['cache-control'] || '', cc: cacheControl(h['cache-control']), expires: h.expires, date: h.date,
    etag: h.etag, lastModified: h['last-modified'], encoding: h['content-encoding'], vary: h.vary, age: h.age,
    setCookie: Boolean(h['set-cookie']), type: h['content-type'], server: h.server, cdn: h['cf-cache-status'] || h['x-cache'] || h['x-vercel-cache'] || h['x-nf-request-id'] && 'netlify' || undefined,
    versioned: versioned(url), sameOrigin: false, body: r.body, location: h.location, api: kindHint === 'api',
  };
  if (e.api) e.kind = 'api';
  if (e.etag || e.lastModified) {
    const cond = {};
    if (e.etag) cond['if-none-match'] = e.etag;
    if (e.lastModified) cond['if-modified-since'] = e.lastModified;
    const again = await request(url, cond);
    e.revalidated = again.status;
  }
  return e;
}

const hops = await follow(START);
const landing = hops[hops.length - 1];
if (!landing || landing.status !== 200) {
  console.error(`The start URL did not give a page: ${hops.map((h) => `${h.status || h.error} ${h.url}`).join(' → ')}`);
  process.exit(2);
}
const origin = new URL(landing.url).origin;
const seen = new Map(); // url → entry
const queue = [];
const pages = [landing.url];

const html = landing.body.toString('utf8');
const first = parseHtml(html, landing.url);
for (const f of first.files) queue.push(f);
const internal = [...new Set(first.links)].filter((l) => l.startsWith(origin) && l !== landing.url && !/\.(pdf|zip|png|jpe?g|webp|mp4)(\?|$)/i.test(l));
for (const l of internal.slice(0, PAGES)) pages.push(l);
for (const p of API) queue.push({ url: new URL(p, origin).href, kind: 'api' });

const pageEntries = [];
for (const p of pages) {
  const e = await inspect(p, 'html');
  e.sameOrigin = true;
  pageEntries.push(e);
  if (p !== landing.url && e.status === 200) for (const f of parseHtml(e.body.toString('utf8'), p).files) queue.push(f);
}
while (queue.length && seen.size < MAX) {
  const f = queue.shift();
  const key = f.url.split('#')[0];
  if (seen.has(key)) continue;
  const e = await inspect(key, f.kind);
  e.sameOrigin = key.startsWith(origin);
  seen.set(key, e);
  if (e.sameOrigin && e.status === 200 && ['js', 'css'].includes(e.kind) && e.bytes < 5 * 1024 * 1024) {
    for (const g of parseAsset(e.body.toString('utf8'), key, e.kind)) if (!seen.has(g.url)) queue.push(g);
  }
}

const files = [...seen.values()];
const all = [...pageEntries, ...files];
for (const e of all) { e.verdicts = judge(e); e.second = secondVisit(e); delete e.body; }

const own = files.filter((e) => e.sameOrigin);
const byKind = {};
for (const e of [...pageEntries, ...own]) {
  const k = e.kind;
  byKind[k] ??= { count: 0, bytes: 0, policies: {}, secondVisit: 0 };
  byKind[k].count++;
  byKind[k].bytes += e.bytes;
  byKind[k].secondVisit += e.second.cost;
  const pol = `${e.ccRaw || '(none)'}${e.etag || e.lastModified ? ' + validator' : ''}`;
  byKind[k].policies[pol] = (byKind[k].policies[pol] || 0) + 1;
}
const ORDER = { critical: 0, high: 1, medium: 2, low: 3, info: 4 };
const findings = {};
for (const e of all) for (const [code, sev, words] of e.verdicts) {
  if (code === 'OK') continue;
  findings[code] ??= { code, severity: sev, words, urls: [], bytes: 0 };
  if (ORDER[sev] < ORDER[findings[code].severity]) findings[code].severity = sev;
  findings[code].urls.push(e.url);
  findings[code].bytes += e.bytes;
}
const sorted = Object.values(findings).sort((a, b) => ORDER[a.severity] - ORDER[b.severity] || b.bytes - a.bytes);
const firstVisit = [...pageEntries.slice(0, 1), ...files].reduce((s, e) => s + e.bytes, 0);
const second = [...pageEntries.slice(0, 1), ...files].reduce((s, e) => s + e.second.cost, 0);
// ---------- Scores ----------
// Six KPIs out of 100, then one score (weighted) and a grade. Each KPI is measured on the site's own answers
// (third-party files are listed, not scored); a KPI with nothing to measure is left out of the total.
const ok200 = (e) => e.status === 200;
const ownPages = pageEntries.filter(ok200);
const ownAssets = own.filter((e) => ok200(e) && !e.api);
const pct = (num, den) => (den ? Math.round((100 * num) / den) : null);
const sum = (list, f) => list.reduce((s, e) => s + f(e), 0);
const has = (e, ...codes) => e.verdicts.some(([c]) => codes.includes(c));
const TEXT_KINDS = new Set(['html', 'js', 'css', 'api', 'data', 'other']);
const textual = [...ownPages, ...own.filter(ok200)].filter((e) => TEXT_KINDS.has(e.kind) && e.bytes > 1024);
const KPI = [
  { id: 'repeatVisit', name: 'Repeat visit reuse', weight: 30,
    what: 'share of the first visit\'s bytes NOT downloaded again on a second visit within the hour',
    score: firstVisit ? Math.max(0, 100 - Math.round((100 * second) / firstVisit)) : null },
  { id: 'validators', name: 'Validators and 304', weight: 20,
    what: 'own pages and files that have an ETag or Last-Modified AND answer 304 when unchanged',
    score: pct([...ownPages, ...ownAssets].filter((e) => e.revalidated === 304).length, ownPages.length + ownAssets.length) },
  { id: 'versioning', name: 'Versioned file names', weight: 15,
    what: 'bytes of own scripts, styles, fonts and pictures whose name changes with their content',
    score: pct(sum(ownAssets.filter((e) => e.versioned), (e) => e.bytes), sum(ownAssets, (e) => e.bytes)) },
  { id: 'lifetimes', name: 'Right lifetimes', weight: 15,
    what: 'own answers kept for a fitting time: versioned → long, unversioned → short or revalidated, pages → revalidated',
    score: pct([...ownPages, ...ownAssets].filter((e) => !has(e, 'NO_VALIDATOR', 'NO_STORE_ASSET', 'LONG_UNVERSIONED', 'VERSIONED_SHORT', 'NO_CACHE_HEADER', 'HTML_LONG')).length, ownPages.length + ownAssets.length) },
  { id: 'compression', name: 'Compression', weight: 10,
    what: 'own text answers over 1 KB sent compressed (gzip, br or zstd)',
    score: pct(textual.filter((e) => e.encoding).length, textual.length) },
  { id: 'safety', name: 'Safety', weight: 10,
    what: 'no session in a shared cache, no stale pages after a deploy, no API cache mixing signed-in and anonymous',
    score: Math.max(0, 100 - 60 * all.filter((e) => has(e, 'PUBLIC_WITH_COOKIE')).length - 25 * all.filter((e) => has(e, 'HTML_LONG', 'API_CACHE_UNKEYED', 'LONG_UNVERSIONED') && ['html', 'js', 'css', 'api'].includes(e.kind)).length) },
];
const status = (s) => (s === null ? 'n/a' : s >= 85 ? 'good' : s >= 60 ? 'to improve' : 'critical');
for (const k of KPI) k.status = status(k.score);
const scored = KPI.filter((k) => k.score !== null);
let overall = scored.length ? Math.round(sum(scored, (k) => k.score * k.weight) / sum(scored, (k) => k.weight)) : 0;
// A session that can leak caps the score, whatever the rest.
if (all.some((e) => has(e, 'PUBLIC_WITH_COOKIE'))) overall = Math.min(overall, 39);
const grade = overall >= 90 ? 'A' : overall >= 75 ? 'B' : overall >= 60 ? 'C' : overall >= 40 ? 'D' : 'E';
const score = { overall, grade, status: status(overall), kpis: KPI };

const report = {
  start: START, landing: landing.url, checkedAt: new Date().toISOString(),
  redirects: hops.slice(0, -1).map((h) => ({ url: h.url, status: h.status, cacheControl: h.headers['cache-control'] || null, location: h.headers.location })),
  server: landing.headers.server || null, cdn: pageEntries[0]?.cdn || null,
  totals: { pages: pageEntries.length, files: files.length, ownFiles: own.length, firstVisitBytes: firstVisit, secondVisitBytes: second },
  score, byKind, findings: sorted,
  entries: all.map(({ cc, ...e }) => e),
};

// ---------- Output ----------

const md = [];
md.push(`# Cache audit — ${landing.url}`, '', `Checked ${report.checkedAt} as an anonymous visitor. Server: ${report.server ?? '?'}${report.cdn ? `, CDN: ${report.cdn}` : ''}.`, '');
if (report.redirects.length) md.push(`Redirects: ${report.redirects.map((r) => `${r.status} ${r.url} (${r.cacheControl ?? 'no Cache-Control'})`).join(' → ')} → ${landing.url}`, '');
md.push(`## Score: ${overall}/100 — grade ${grade} (${status(overall)})`, '', '| KPI | Score | Status | Weight | What is measured |', '|---|---|---|---|---|');
for (const k of KPI) md.push(`| ${k.name} | ${k.score === null ? '—' : `${k.score} %`} | ${k.status} | ${k.weight} | ${k.what} |`);
md.push('', 'Grades: A ≥ 90, B ≥ 75, C ≥ 60, D ≥ 40, E below. A cookie in a shared cache caps the score at 39.', '');
md.push(`**First visit** (home page + its files): ${kb(firstVisit)} transferred. **Second visit within the hour**: ${kb(second)} downloaded again (${firstVisit ? Math.round((100 * second) / firstVisit) : 0} %).`, '');
md.push('## Policy by type (own files)', '', '| Type | Files | Size | 2nd visit | Policies seen |', '|---|---|---|---|---|');
for (const [k, v] of Object.entries(byKind)) md.push(`| ${k} | ${v.count} | ${kb(v.bytes)} | ${kb(v.secondVisit)} | ${Object.entries(v.policies).map(([p, n]) => `\`${p}\` ×${n}`).join('<br>')} |`);
md.push('', '## Findings', '');
if (!sorted.length) md.push('Nothing to report.');
for (const f of sorted) {
  md.push(`### [${f.severity}] ${f.code} — ${f.urls.length} file(s), ${kb(f.bytes)}`, '', f.words, '');
  for (const u of f.urls.slice(0, 8)) md.push(`- ${u}`);
  if (f.urls.length > 8) md.push(`- … and ${f.urls.length - 8} more`);
  md.push('');
}
md.push('## Every answer', '', '| Status | Type | Size | Cache-Control | Validator | 304? | Versioned | 2nd visit | URL |', '|---|---|---|---|---|---|---|---|---|');
for (const e of all) md.push(`| ${e.status} | ${e.kind} | ${kb(e.bytes)} | \`${e.ccRaw || '—'}\` | ${e.etag ? 'ETag' : ''}${e.etag && e.lastModified ? '+' : ''}${e.lastModified ? 'LM' : ''} | ${e.revalidated ?? '—'} | ${e.versioned ? 'yes' : 'no'} | ${e.second.how} | ${e.url.replace(origin, '')} |`);
const text = md.join('\n');

if (opt('json')) writeFileSync(opt('json'), JSON.stringify(report, null, 2));
if (opt('md')) writeFileSync(opt('md'), text);
console.log(text);
