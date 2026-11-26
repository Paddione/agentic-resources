#!/usr/bin/env node
// Optional local server for index.html — only needed by clients whose built-in
// browser pane refuses to run JavaScript on file:// pages (e.g. Claude Desktop).
// Opening index.html straight from disk needs no server at all.
//
//   node serve.mjs [port] --root <dir>... [--idle <minutes>]     or     node serve.mjs [port] --all [--idle <minutes>]
//
// Serves this folder at http://127.0.0.1:<port>/ and exposes local files
// read-only under /fs/<absolute path>, so the page's ?file=C:\out\frog.png
// parameter keeps working unchanged. POST /locate finds a picked/dropped
// file by name + size under the user's usual folders; GET /ls/<folder> (with
// ?deep=1 to walk its subfolders) lists a
// folder's previewable files (the page's ?dir=); POST /annotate writes the
// page's annotations next to an asset as <asset>.annotations.json and
// <asset>.annotated.png — the only two names it ever writes, and never the
// asset itself. Binds to loopback only, and never starts another process.
// --root (repeatable) is required: only files under those folders are served,
// listed, searched or written to. --all instead serves any local file the current
// user can read and lets /locate search Downloads, Desktop, Documents, Pictures,
// Videos, Music and OneDrive; any local process can talk to a loopback server, so
// that mode is opt-in. UNC / network paths are always refused, in every mode.
// Starting again with --root while an instance runs adds the folder to that
// instance (a plain "already running" otherwise).
// The server is started detached by open.mjs and would otherwise outlive every
// session: it exits on its own after --idle minutes (default 60, 0 = never)
// without a request. An open page pings /__health every few minutes while it
// is visible, so a tab someone is looking at keeps it alive; closed tabs let it
// go. Two more local-process-only routes (same guard as /__root): POST /__idle
// {"minutes": n | "default"} changes the limit of a running instance
// (`open.mjs --idle`), POST /__quit stops it at once (`open.mjs --stop`).
// Every response carries `X-Content-Type-Options: nosniff`; /fs/ responses add
// `Content-Security-Policy: sandbox`, so a served HTML or SVG file navigated to
// directly runs in an opaque origin, never as this server's origin. Requests
// whose Host, Origin or Fetch-Metadata say they come from another origin (another
// site, another local port, a rebound hostname) are refused. Of all scripts,
// only a folder's `gallery.js` is served as JavaScript; other .js files come
// back as text so a <script src> pointed at them is rejected.
//
// Exits 0 immediately with "already running" if a healthy instance owns the port.
import { createServer, get } from 'node:http';
import { createReadStream } from 'node:fs';
import { stat, lstat, realpath, readdir, writeFile, rm } from 'node:fs/promises';
import { basename, dirname, extname, join, resolve, sep } from 'node:path';
import { fileURLToPath } from 'node:url';
import { request as httpRequest } from 'node:http';
import { homedir } from 'node:os';

const HERE = fileURLToPath(new URL('.', import.meta.url));
const args = process.argv.slice(2);
const ROOTS = [];
const PENDING = new Map();   // canonical root → as given, for a root that did not exist yet
const MISSING = new Set(['ENOENT', 'ENOTDIR']);   // the only realpath failures that mean "not there yet"
const DEFAULT_IDLE_MIN = 60;
let PORT = 8380, portGiven = false, ALL = false, IDLE_MIN = DEFAULT_IDLE_MIN;
for (let i = 0; i < args.length; i++) {
  const a = args[i];
  if (a === '--root') {
    if (!args[i + 1]) { console.error('--root needs a folder'); process.exit(2); }
    const root = await canonicalRoot(args[++i]);
    if (root.refused) { console.error(`${root.refused}: ${args[i]}`); process.exit(2); }
    addRoot(args[i], root);
  } else if (a === '--idle') {
    IDLE_MIN = Number(args[++i]);
    if (!Number.isInteger(IDLE_MIN) || IDLE_MIN < 0) { console.error('--idle needs a whole number of minutes (0 = never exit)'); process.exit(2); }
  } else if (a === '--all') ALL = true;
  else if (/^\d+$/.test(a) && !portGiven) { PORT = Number(a); portGiven = true; }
  else { console.error(`unknown argument: ${a}`); process.exit(2); }
}
if (ALL === ROOTS.length > 0) {
  console.error(ALL ? '--all and --root cannot be combined' : 'pass --root <folder> (repeatable) to serve one folder, or --all to serve every file you can read');
  process.exit(2);
}

const TYPES = {
  '.html': 'text/html; charset=utf-8', '.js': 'text/javascript', '.mjs': 'text/javascript', '.json': 'application/json',
  '.md': 'text/markdown; charset=utf-8', '.css': 'text/css',
  '.png': 'image/png', '.jpg': 'image/jpeg', '.jpeg': 'image/jpeg', '.webp': 'image/webp', '.gif': 'image/gif',
  '.svg': 'image/svg+xml', '.bmp': 'image/bmp', '.avif': 'image/avif', '.exr': 'image/x-exr', '.hdr': 'image/vnd.radiance',
  '.mp3': 'audio/mpeg', '.wav': 'audio/wav', '.ogg': 'audio/ogg', '.flac': 'audio/flac', '.m4a': 'audio/mp4',
  '.mp4': 'video/mp4', '.webm': 'video/webm', '.mov': 'video/quicktime',
  '.glb': 'model/gltf-binary', '.gltf': 'model/gltf+json', '.fbx': 'application/octet-stream', '.obj': 'text/plain',
};

const PAGE_FILES = new Set(['index.html', 'gallery.js', 'README.md']);
// The only script /fs/ hands out as JavaScript: a folder's gallery.js, which the page loads by explicit request.
// Any other .js/.mjs is served as text so <script src> (with nosniff) refuses it.
const GALLERY_FILE = 'gallery.js';
const LOCATE_BUDGET_MS = 5000;   // /locate gives up after this and says so
// What /ls/ reports: the asset types the page can show (sidecars and gallery.js are read separately).
const PREVIEWABLE = new Set(Object.keys(TYPES).filter((e) => !['.html', '.htm', '.css', '.js', '.mjs', '.json', '.md'].includes(e)).concat(['.exr', '.hdr', '.tga', '.bmp', '.avif', '.flac', '.m4a', '.aac', '.mov', '.usdz', '.bvh']));

function send(res, code, body, type = 'text/plain; charset=utf-8', headers = {}) {
  res.writeHead(code, { ...headers, 'content-type': type, 'cache-control': 'no-cache' });   // extra headers add, never override
  res.end(body);
}

async function serveFile(req, res, file, { sandbox = false } = {}) {
  const s = await stat(file).catch(() => null);
  if (!s || !s.isFile()) return send(res, 404, `not found: ${file}`);
  const ext = extname(file).toLowerCase();
  const isScript = ext === '.js' || ext === '.mjs';
  const type = isScript && basename(file) !== GALLERY_FILE ? 'text/plain; charset=utf-8' : (TYPES[ext] ?? 'application/octet-stream');
  const headers = { 'content-type': type, 'cache-control': 'no-cache', 'accept-ranges': 'bytes', 'x-content-type-options': 'nosniff' };
  if (sandbox) headers['content-security-policy'] = 'sandbox';   // a served file must never script as this origin

  // Range requests keep <audio>/<video> seeking happy.
  const range = /^bytes=(\d*)-(\d*)$/.exec(req.headers.range ?? '');
  if (range && (range[1] || range[2])) {
    const start = range[1] ? Number(range[1]) : Math.max(0, s.size - Number(range[2]));
    const end = range[1] && range[2] ? Math.min(Number(range[2]), s.size - 1) : s.size - 1;
    if (start > end || start >= s.size) { res.writeHead(416, { 'content-range': `bytes */${s.size}` }); return res.end(); }
    res.writeHead(206, { ...headers, 'content-range': `bytes ${start}-${end}/${s.size}`, 'content-length': end - start + 1 });
    return stream(createReadStream(file, { start, end }), res);
  }
  res.writeHead(200, { ...headers, 'content-length': s.size });
  stream(createReadStream(file), res);
}
// A read error after stat (file locked, deleted, permission changed) must not crash the server; an aborted
// client (media scrubbing does this constantly) must not leak the file handle.
function stream(rs, res) {
  rs.on('error', () => res.destroy());
  res.on('close', () => rs.destroy());
  rs.pipe(res);
}

// UNC / network paths (\\host\share, //host/share) would make the server open an SMB connection to an
// attacker-named host and, on Windows, offer the user's credentials. Local drives and POSIX paths only.
function isNetworkPath(p) { return /^[\\/]{2}/.test(String(p)); }
// A root as the filesystem really names it, so it compares like with like against the realpath'd
// file below: on macOS `/tmp` is a symlink to `/private/tmp`, and a root given as `/tmp/out` never
// matched a file that resolves under `/private/tmp/out`. A root that does not exist yet is the realpath
// of its deepest existing ancestor plus the missing tail, and is resolved again once it exists (see
// settleRoots), since its on-disk casing or a link may differ from what was typed. Only a missing
// component counts as missing; a component that cannot be resolved for any other reason refuses the
// root, so no part of a root is ever left unresolved. Network paths are refused before realpath, which
// would otherwise reach the host, and again after it, for a local link whose target is a share.
async function canonicalRoot(dir) {
  const network = { refused: 'network paths are refused' };
  if (isNetworkPath(dir)) return network;
  const abs = resolve(/^[a-zA-Z]:$/.test(dir) ? dir + sep : dir);   // a bare drive letter is the drive, not the cwd
  if (isNetworkPath(abs)) return network;
  const missing = [];
  for (let base = abs; ; base = dirname(base)) {
    try {
      const real = await realpath(base);
      return isNetworkPath(real) ? network : { path: join(real, ...missing), pending: missing.length > 0 };
    } catch (err) {
      if (!MISSING.has(err.code) || dirname(base) === base) return { refused: `cannot be resolved (${err.code})` };
      missing.unshift(basename(base));
    }
  }
}
function addRoot(given, root) {
  if (root.path !== resolve(given)) console.log(`root ${given} is ${root.path}`);
  if (ROOTS.includes(root.path)) return false;
  ROOTS.push(root.path);
  if (root.pending) PENDING.set(root.path, given);
  return true;
}
function under(real) { return ROOTS.some((r) => real === r || real.startsWith(r.endsWith(sep) ? r : r + sep)); }
async function settleRoots() {
  for (const [root, given] of [...PENDING]) {
    const fresh = await canonicalRoot(given);
    const at = ROOTS.indexOf(root);
    if (at < 0) continue;
    if (fresh.refused) { PENDING.delete(root); console.log(`root ${given} is no longer served: ${fresh.refused}`); continue; }
    if (fresh.path !== root) {
      PENDING.delete(root);
      if (ROOTS.includes(fresh.path)) ROOTS.splice(at, 1); else ROOTS[at] = fresh.path;
      console.log(`root ${given} is ${fresh.path}`);
    }
    if (fresh.pending) PENDING.set(fresh.path, given); else PENDING.delete(fresh.path);
  }
}
// The reason a path may not be served, or null. The file as it really is decides, in every mode: a mapped drive
// or a link whose target is a share is a network path however it was spelled.
// The 403 body for a path outside the roots. /ls/ also marks that refusal with the REFUSED header, which is what
// the page reads to offer the command that adds a typed folder: the prose can change without breaking it.
const OUTSIDE_ROOTS = 'outside the allowed roots';
const REFUSED = { 'x-preview-refused': 'outside-roots' };
async function refused(file) {
  const network = 'network paths are refused', outside = OUTSIDE_ROOTS;
  if (isNetworkPath(file)) return network;
  const real = await realpath(file).catch(() => null);
  if (real && isNetworkPath(real)) return network;
  if (ROOTS.length === 0) return null;
  if (!real) {
    // A path that does not exist — the page probing for <asset>.annotations.json before any is saved — is judged
    // by where it would be: its deepest existing ancestor as the filesystem names it plus the missing tail, the
    // same resolution a root gets. Under the roots it is not refused and the caller answers 404; outside, 403.
    let would = await canonicalRoot(file);
    if (would.refused) return would.refused;   // network, or an ancestor that cannot be resolved: say which
    if (under(would.path)) return null;
    if (PENDING.size) {   // a root that did not exist may exist now, and so may more of this path
      await settleRoots();
      would = await canonicalRoot(file);
      if (would.refused) return would.refused;
      if (under(would.path)) return null;
    }
    return outside;
  }
  if (under(real)) return null;
  if (PENDING.size) { await settleRoots(); if (under(real)) return null; }
  return outside;
}

// Find a file by name + size (+ closest modified time) under the user's usual folders, or under --root.
// Used for files the browser handed over without a path (file picker, drag & drop). Time-boxed.
// The preview page carries the matching copy of this set as SKIP_FOLDERS, for the folder picker's own walk;
// the two must agree, so change both together.
const SKIP_DIRS = new Set(['node_modules', '.git', 'AppData', 'Library', 'obj', 'bin', '.cache', '.vscode']);
// How deep either walker goes. The preview page carries its own copy of this number for the folder picker (a
// browser page cannot share a constant with this file); the two must agree, so change both together.
const MAX_WALK_DEPTH = 6;
async function locateFile({ name, size, mtime, hints }, deadline) {
  const roots = ROOTS.length ? ROOTS
    : ['Downloads', 'Desktop', 'Documents', 'Pictures', 'Videos', 'Music', 'OneDrive'].map((d) => join(homedir(), d));
  const matches = []; let outOfTime = false;
  // Folders the page already shows files from come first: a dropped file usually sits next to them.
  for (const h of Array.isArray(hints) ? hints.slice(0, 20) : []) {
    if (typeof h !== 'string' || await refused(h)) continue;
    const p = join(h, name), s = await stat(p).catch(() => null);
    if (s && s.isFile() && s.size === size) matches.push({ path: p, mtimeMs: s.mtimeMs });
  }
  if (matches.length) return { matches: matches.map((m) => m.path) };
  async function walk(dir, depth) {
    if (Date.now() > deadline) { outOfTime = true; return; }
    if (depth > MAX_WALK_DEPTH || matches.length >= 8) return;   // unchanged from the literal it replaced: this walker starts at depth 0 and allows one more level than /ls/
    let entries;
    try { entries = await readdir(dir, { withFileTypes: true }); } catch { return; }
    for (const e of entries) {
      if (Date.now() > deadline) { outOfTime = true; return; }
      const p = join(dir, e.name);
      if (e.isDirectory()) { if (!SKIP_DIRS.has(e.name) && !e.name.startsWith('.')) await walk(p, depth + 1); }
      else if (e.name === name) {
        const s = await stat(p).catch(() => null);
        if (s && s.size === size) matches.push({ path: p, mtimeMs: s.mtimeMs });
      }
    }
  }
  for (const r of roots) { if (outOfTime) break; await walk(r, 0); }
  if (mtime) matches.sort((a, b) => Math.abs(a.mtimeMs - mtime) - Math.abs(b.mtimeMs - mtime));
  return { matches: matches.map((m) => m.path) };
}

const BODY_LIMIT = 65536;
const ANNOTATE_BODY_LIMIT = 24 * 1024 * 1024;   // /annotate carries a rendered PNG (≤ 2048 px on the long side)
// Rejects with { status: 413 } on an oversize body; the handler answers first, then drops the connection.
// Same-origin check that does not rely on one header: Host must be this loopback server, Origin (when a
// browser sends it) must match, and Fetch Metadata (when sent) must be same-origin or a direct navigation.
const OUR_HOSTS = new Set([`127.0.0.1:${PORT}`, `localhost:${PORT}`, `[::1]:${PORT}`]);

// Idle exit. Every request (the page's heartbeat included) moves `lastSeen`, at its start and again when its
// response closes; a timer looks once a minute and closes the listener when the quiet stretch reaches IDLE_MIN.
// Responses still in flight finish first, then the process ends. open.mjs restarts it in well under a second on
// the next generation.
let lastSeen = Date.now(), inflight = 0, stopping = false, idleTimer = null;
const IDLE_CHECK_MS = 60_000, STOP_GRACE_MS = 5000, STOP_CAP_MS = 60_000;
const EXIT_PORT_TAKEN = 3;   // the port is held by something that is not a preview server; open.mjs matches on this code
function stopServer(why) {
  if (stopping) return;   // a second quit, or an idle tick during the grace period, must not cut the first stop short
  stopping = true;
  clearInterval(idleTimer);
  console.log(`${why}, stopping`);
  server.close(() => process.exit(0));
  // close() waits for idle keep-alive sockets too, so a client holding one open must not keep us alive: once
  // nothing is in flight, a short grace period ends the process; a response that never finishes hits the cap.
  const arm = setInterval(() => { if (inflight === 0) { clearInterval(arm); setTimeout(() => process.exit(0), STOP_GRACE_MS).unref(); } }, 200);
  arm.unref();
  setTimeout(() => process.exit(0), STOP_CAP_MS).unref();
}
// The three control routes are for other local processes only: a browser always sends Origin or Sec-Fetch-Site
// on a POST, and is refused. One definition, since it is what keeps a page from stopping or widening the server.
function isLocalPost(req) { return req.method === 'POST' && !req.headers.origin && !req.headers['sec-fetch-site']; }
function watchIdle() {   // reads IDLE_MIN on every tick: POST /__idle can change it while running
  idleTimer = setInterval(() => {
    if (IDLE_MIN && Date.now() - lastSeen >= IDLE_MIN * 60_000) stopServer(`no request for ${IDLE_MIN} min`);
  }, IDLE_CHECK_MS);
  idleTimer.unref();
}
function requestIsOurs(req) {
  const host = String(req.headers.host || '').toLowerCase();
  if (!OUR_HOSTS.has(host)) return false;
  const origin = req.headers.origin;
  if (origin && origin.toLowerCase() !== `http://${host}`) return false;
  const site = req.headers['sec-fetch-site'];
  if (site && site !== 'same-origin' && site !== 'none') return false;
  return true;
}

// Collects the raw bytes and decodes once at the end: a multi-byte character split across two chunks must not
// become U+FFFD. `limit` is a byte count.
function readBody(req, limit = BODY_LIMIT) {
  return new Promise((resolve, reject) => {
    const chunks = []; let size = 0, done = false;
    req.on('data', (c) => {
      if (done) return;
      size += c.length;
      if (size > limit) { done = true; chunks.length = 0; req.pause(); reject(Object.assign(new Error('body too large'), { status: 413 })); return; }
      chunks.push(c);
    });
    req.on('end', () => { if (!done) resolve(Buffer.concat(chunks).toString('utf8')); }); req.on('error', reject);
  });
}
// A malformed body is the caller's mistake (400), not a server failure (500).
async function readJson(req, limit) {
  const text = await readBody(req, limit);
  let v;
  try { v = JSON.parse(text || '{}'); } catch { throw Object.assign(new Error('invalid JSON body'), { status: 400 }); }
  if (!v || typeof v !== 'object' || Array.isArray(v)) throw Object.assign(new Error('a JSON object body is required'), { status: 400 });
  return v;
}

const server = createServer(async (req, res) => {
  try {
    const url = new URL(req.url, 'http://x');
    const path = decodeURIComponent(url.pathname);
    // Only this page (same origin) or a direct navigation may talk to the server: another site, another local
    // port, or a DNS-rebound hostname gets nothing — not even an existence oracle through <img src>.
    if (!requestIsOurs(req)) return send(res, 403, 'requests from other origins are refused');
    lastSeen = Date.now(); inflight++;
    res.once('close', () => { inflight--; lastSeen = Date.now(); });
    // `launcher` and `roots` are what the page needs to show the user the command that restarts a stopped server.
    if (path === '/__health') return send(res, 200, JSON.stringify({ ok: true, service: 'unity-ai-asset-preview', restricted: ROOTS.length > 0, roots: ROOTS, idleMinutes: IDLE_MIN, defaultIdleMinutes: DEFAULT_IDLE_MIN, launcher: join(HERE, 'open.mjs'), platform: process.platform }), 'application/json');
    // POST /__idle {"minutes": n | "default"} — a later `open.mjs --idle` changing the limit of the running instance.
    if (path === '/__idle') {
      if (!isLocalPost(req)) return send(res, 403, 'forbidden');
      const body = await readJson(req);
      const minutes = body.minutes === 'default' ? DEFAULT_IDLE_MIN : body.minutes;
      if (!Number.isInteger(minutes) || minutes < 0) return send(res, 400, 'minutes must be a whole number (0 = never exit) or "default"');
      IDLE_MIN = minutes; lastSeen = Date.now();
      console.log(IDLE_MIN ? `idle limit now ${IDLE_MIN} min` : 'idle limit off: stays up until stopped');
      return send(res, 200, JSON.stringify({ idleMinutes: IDLE_MIN }), 'application/json');
    }
    // POST /__quit — stop now (open.mjs --stop).
    if (path === '/__quit') {
      if (!isLocalPost(req)) return send(res, 403, 'forbidden');
      send(res, 200, JSON.stringify({ stopping: true }), 'application/json');
      res.once('close', () => stopServer('asked to quit'));   // close, not finish: an aborted reply must still stop us
      return;
    }
    // POST /__root {"roots":[...]} — a later `serve.mjs --root <dir>` start widening a restricted instance.
    if (path === '/__root') {
      if (!isLocalPost(req)) return send(res, 403, 'forbidden');
      const { roots } = await readJson(req);
      if (!Array.isArray(roots) || !roots.every((r) => typeof r === 'string' && r)) return send(res, 400, 'roots required');
      if (ROOTS.length === 0) return send(res, 200, JSON.stringify({ restricted: false }), 'application/json');   // already serves everything
      for (const r of roots) { const root = await canonicalRoot(r); if (!root.refused && addRoot(r, root)) console.log(`now also serving files under: ${root.path}`); }
      return send(res, 200, JSON.stringify({ restricted: true, roots: ROOTS }), 'application/json');
    }

    // POST /locate {"name","size","mtime"} → {"matches":[paths]} — the custom header forces a CORS preflight, which
    // this server never answers, so only pages served from here can call the POST routes.
    if (path === '/locate') {
      if (req.method !== 'POST' || req.headers['x-preview-action'] !== 'locate') return send(res, 403, 'forbidden');
      const q = await readJson(req);
      if (!q.name || typeof q.size !== 'number' || /[\\/]/.test(q.name)) return send(res, 400, 'name and size required');
      const { matches } = await locateFile(q, Date.now() + LOCATE_BUDGET_MS);
      return send(res, 200, JSON.stringify({ matches }), 'application/json');
    }

    // POST /annotate {"path","json","png"} — the page's marks for an existing, allowed asset, written next to it
    // as <asset>.annotations.json and (when a PNG came along) <asset>.annotated.png. Nothing else is ever written,
    // and the asset itself is never touched. Same guard as /locate.
    if (path === '/annotate') {
      if (req.method !== 'POST' || req.headers['x-preview-action'] !== 'annotate') return send(res, 403, 'forbidden');
      const { path: file, json, png } = await readJson(req, ANNOTATE_BODY_LIMIT);
      if (!file || typeof file !== 'string') return send(res, 400, 'path required');
      // Allowlist first, existence second, like /fs/ and /ls/: a path outside the roots is 403 whether or not it
      // exists. The file as it really is (realpath) is what both the check and the writes see, so a symlink outside
      // --root pointing inside it cannot pass the check and receive the files.
      const why = await refused(resolve(file));
      if (why) return send(res, 403, why);
      const abs = await realpath(file).catch(() => null), s = abs && await stat(abs).catch(() => null);
      if (!abs || !s || !s.isFile()) return send(res, 404, `not found: ${file}`);
      if (await refused(abs)) return send(res, 403, OUTSIDE_ROOTS);
      if (!json || typeof json !== 'object' || json.kind !== 'unity-ai-annotations' || !Array.isArray(json.marks)) return send(res, 400, 'json must be a unity-ai-annotations document');
      const m = typeof png === 'string' ? /^data:image\/png;base64,([A-Za-z0-9+/]+=*)$/.exec(png) : null;
      if (typeof png === 'string' && !m) return send(res, 400, 'png must be a data:image/png;base64 URL');
      // The two names, checked right before writing: absent, or a plain file. A symlink (or anything else) standing
      // at one of them is refused, so the allowlist cannot be escaped through the output side either.
      const jsonPath = `${abs}.annotations.json`, pngPath = `${abs}.annotated.png`;   // must match ANNOT_SUFFIX / ANNOT_PNG_SUFFIX in index.html
      for (const target of [jsonPath, pngPath]) {
        const l = await lstat(target).catch(() => null);
        if (l && !l.isFile()) return send(res, 403, `refusing to write ${basename(target)}: something other than a plain file is already there`);
      }
      // PNG first, JSON last: a failure leaves either nothing new or a complete pair, never a JSON that promises a
      // PNG which is not there. Without a PNG, a previous one is removed, so the pair is both-current or JSON-only.
      const out = { json: jsonPath };
      if (m) { await writeFile(pngPath, Buffer.from(m[1], 'base64')); out.png = pngPath; }
      else await rm(pngPath, { force: true });
      await writeFile(jsonPath, JSON.stringify(json, null, 2) + '\n', 'utf8');
      console.log(`annotations written: ${out.json}${out.png ? ` + ${basename(out.png)}` : ' (no PNG)'}`);
      return send(res, 200, JSON.stringify(out), 'application/json');
    }

    // The page itself and its siblings.
    const name = path === '/' ? 'index.html' : path.slice(1);
    if (PAGE_FILES.has(name)) return serveFile(req, res, join(HERE, name));

    // /ls/C:/out  → the folder's previewable files as JSON, so the page can open a folder from its sidecars alone.
    if (path.startsWith('/ls/')) {
      let dir = path.slice(4);
      const deep = url.searchParams.get('deep') === '1';   // opt-in: walk the subfolders too
      if (!/^[a-zA-Z]:[\\/]/.test(dir) && !dir.startsWith('/')) dir = '/' + dir;
      const why = await refused(dir);
      if (why) return send(res, 403, why, undefined, why === OUTSIDE_ROOTS ? REFUSED : {});
      const files = [];
      let unreadable = 0;   // subfolders readdir refused: reported so the page can say the listing is partial
      // `name` stays relative to the folder that was asked for, so a subfolder's files carry their path with
      // them: the page can fetch them and show where they came from. Depth is capped and the noise folders are
      // skipped, on the same rules the file search uses.
      const list = async (abs, rel, depth) => {
        let entries;
        try { entries = await readdir(abs, { withFileTypes: true }); } catch { if (depth === 0) return 'unreadable'; unreadable++; return null; }
        const names = new Set(entries.filter((e) => e.isFile()).map((e) => e.name));
        for (const e of entries) {
          if (e.isDirectory()) {
            if (deep && depth < MAX_WALK_DEPTH && !SKIP_DIRS.has(e.name) && !e.name.startsWith('.')) await list(join(abs, e.name), rel ? `${rel}/${e.name}` : e.name, depth + 1);
            continue;
          }
          if (!e.isFile() || !PREVIEWABLE.has(extname(e.name).toLowerCase()) || /\.(provenance|unityai|annotations)\.json$|\.annotated\.png$/i.test(e.name)) continue;   // sidecars and annotation outputs are notes, not assets
          const st = await stat(join(abs, e.name)).catch(() => null);
          if (!st) { unreadable++; continue; }   // a file we cannot stat is one we cannot report: counted, not dropped
          // `generated`: a provenance sidecar sits next to the file, i.e. the generator wrote it.
          files.push({ name: rel ? `${rel}/${e.name}` : e.name, size: st.size, mtimeMs: st.mtimeMs, generated: names.has(e.name + '.unityai.json') || names.has(e.name + '.provenance.json') });
        }
        return null;
      };
      if (await list(dir, '', 0) === 'unreadable') return send(res, 404, `not a readable folder: ${dir}`);
      // Generation order. Linux stamps files written in one timer tick with the same mtime, so the name breaks the
      // tie: the listing is the same on every run and every filesystem, not readdir's hash order.
      files.sort((a, b) => (a.mtimeMs - b.mtimeMs) || a.name.localeCompare(b.name));
      return send(res, 200, JSON.stringify({ dir, deep, files, unreadable }), 'application/json');
    }

    // /fs/C:/out/frog.png  or  /fs//home/me/frog.png  → local file, read-only.
    if (path.startsWith('/fs/')) {
      let local = path.slice(4);
      if (!/^[a-zA-Z]:[\\/]/.test(local) && !local.startsWith('/')) local = '/' + local;   // POSIX absolute
      const why = await refused(local);
      if (why) return send(res, 403, why);
      return serveFile(req, res, local, { sandbox: true });
    }
    send(res, 404, 'not found');
  } catch (err) {
    send(res, err?.status ?? 500, String(err?.message ?? err));
    if (err?.status === 413) res.once('finish', () => req.destroy());   // answer, then drop the rest of the upload
  }
});

// Defer to the instance that owns the port, after handing it our --root folders: whoever started us wants those
// folders served, and the running instance is now the only one that can serve them. Both ways of losing the port
// come here — finding it taken at startup, and losing the listen race below — so neither drops its roots and
// leaves its caller with a preview URL whose files 403.
function deferTo() {
  if (!ROOTS.length) { console.log(`already running: http://127.0.0.1:${PORT}/`); process.exit(0); }
  const rq = httpRequest({ host: '127.0.0.1', port: PORT, path: '/__root', method: 'POST', headers: { 'content-type': 'application/json' } }, (rr) => {
    let out = ''; rr.on('data', (c) => (out += c));
    rr.on('end', () => {
      let added = null;
      try { added = JSON.parse(out).restricted ? `now also serving ${ROOTS.join(', ')}` : 'unrestricted, nothing to add'; } catch { /* answered, but not with JSON */ }
      if (rr.statusCode === 200 && added) { console.log(`already running: http://127.0.0.1:${PORT}/ — ${added}`); process.exit(0); }
      console.error(`already running, but it refused the new root (${rr.statusCode})`); process.exit(1);
    });
  });
  rq.on('error', () => { console.error(`already running on port ${PORT}, but it did not answer the request to serve ${ROOTS.join(', ')}`); process.exit(1); });
  rq.end(JSON.stringify({ roots: ROOTS }));
}
// A healthy preview server on the port, or not ours / not answering.
function probe(onMine, onTheirs) {
  get(`http://127.0.0.1:${PORT}/__health`, (r) => {
    let body = '';
    r.on('data', (c) => (body += c));
    r.on('end', () => (body.includes('unity-ai-asset-preview') ? onMine() : onTheirs()));
  }).on('error', onTheirs);
}

// Reuse a healthy instance instead of failing on EADDRINUSE.
probe(deferTo, () => {
  // Two launchers starting at once both find the port free; the one that loses `listen` defers to the winner
  // (roots and all) instead of dying on an unhandled EADDRINUSE.
  server.on('error', (err) => {
    if (err.code !== 'EADDRINUSE') { console.error(`could not listen on port ${PORT}: ${err.message}`); process.exit(1); }
    probe(deferTo, () => { console.error(`port ${PORT} is taken by something else`); process.exit(EXIT_PORT_TAKEN); });
  });
  server.listen(PORT, '127.0.0.1', () => {
    console.log(`asset preview: http://127.0.0.1:${PORT}/   (add ?file=<path>; local files under /fs/)`);
    if (ROOTS.length) console.log(`serving files only under: ${ROOTS.join(', ')}`);
    console.log(IDLE_MIN ? `exits after ${IDLE_MIN} min without a request (--idle <min>, 0 = never)` : 'stays up until stopped (--idle 0)');
    watchIdle();
  });
});
