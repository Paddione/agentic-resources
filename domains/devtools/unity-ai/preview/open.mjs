#!/usr/bin/env node
// One command to show generated assets in index.html, whatever the client:
//
//   node open.mjs <file-or-folder>... [--root <dir>]... [--port 8380] [--idle <minutes>|default] [--open] [--no-dir] [--json]
//   node open.mjs --stop [--port 8380] [--json]  stop the server now (it also exits by itself after an hour idle)
//
// --json prints one JSON object on stdout instead of the lines below (`preview`, `fallback`, `server` as every
// server line, `browser`, `notes`, `errors`, plus `serverStarted` or `stopped`): what `unity ai preview` reads.
//
// --idle sets the server's idle limit: passed to the one it starts, or set on the one already running (which
// otherwise keeps its own). It stays on that server; `--idle default` puts the server's default back.
// A server from before the idle limit existed (no `idleMinutes` in its health) is never reused: it would run for
// ever and cannot be stopped from here, so the launcher moves to the next free port and says so.
//                 [--<param> <value>]...        e.g. --sheet 4x2 --modality skybox --orgName my-studio
//
// It starts serve.mjs when no healthy instance owns the port (detached, so it
// outlives this command), scoped to the folders the given files live in, plus
// any --root (an already-running restricted instance is widened the same way),
// reads each file's sidecar, and prints, one per line, `<key>:  <value>`:
//
//   preview:  http://127.0.0.1:8380/?file=C:/out/frog.png&...&dir=C:/out   <- for a browser tool, or the user
//   fallback: file:///.../index.html?file=C:/out/frog.png&modelId=...     <- works with no server; carries the
//                                                                          sidecar's fields, since a file:// page
//                                                                          cannot read the sidecar itself
//   server:   started serve.mjs on port 8380, serving files under C:/out  <- only when this run started it; it ends
//             (the previous server stopped by itself: no request for 60 min) with why the last one stopped, when known
//   note:     ...                                                          <- something worth knowing, not fatal
//   browser:  opened the preview in the default browser                   <- with --open
//
// The server it starts writes its few lines (start, roots, stop and why, or a crash) to
// unity-ai-preview-<port>.log in the temp folder, appended: the next start reads why the previous server on that
// port stopped from it. No request is logged; the only paths in it are the folders it serves and the annotation
// files Save writes. A log that is not a regular file of this user's (a symlink, or one another user planted in a
// shared /tmp) is left alone: it is not read, and the server runs unlogged.
//
// Failures go to stderr with the same `server:` / `browser:` keys. Exit code 0
// when a URL was printed and every requested step worked; 1 when the server
// was wanted and could not start, or --open could not launch a browser (the
// URLs are still printed); 2 on bad arguments.
//
// When every file given lives in the same folder, the preview URL also
// carries that folder as `dir=`, after the files: the new files are selected
// and the rest of the folder's generated assets stay listed, even in a fresh
// browser tab (the page only remembers a tab's earlier view inside that tab).
// --no-dir shows the given files alone. Several files put each one's own
// sidecar fields in the fallback URL (the page's `items=`), so no asset is
// shown with another's model, cost or ids.
// The fallback URL never carries dir=
// (a file:// page cannot list a folder), so with folder arguments only there
// is none. --open launches the user's default browser on the preview URL
// (the fallback when the server could not start): `start` on Windows, `open`
// on macOS, `xdg-open` elsewhere. Extra --key value pairs are passed through
// as query parameters (README.md lists them); the keys the arguments decide
// (file, dir, ...) are refused. Needs Node.js only.
import { spawn } from 'node:child_process';
import { constants as FS, closeSync, lstatSync, openSync, readdirSync, readFileSync, unlinkSync, writeSync } from 'node:fs';
import { randomUUID } from 'node:crypto';
import { tmpdir } from 'node:os';
import { get, request as httpRequest } from 'node:http';
import { access, readFile, realpath, stat } from 'node:fs/promises';
import { dirname, join, resolve, sep } from 'node:path';
import { fileURLToPath, pathToFileURL } from 'node:url';

const HERE = fileURLToPath(new URL('.', import.meta.url));
const SERVE = resolve(HERE, 'serve.mjs');
const INDEX = resolve(HERE, 'index.html');
const DEFAULT_PORT = 8380;
const SERVICE_ID = 'unity-ai-asset-preview';                    // what serve.mjs answers on /__health — keep in step
const SERVE_EXIT_PORT_TAKEN = 3;                                 // serve.mjs's exit code when a non-preview program holds the port — keep in step
const SIDECAR_SUFFIXES = ['.unityai.json', '.provenance.json'];  // same list as serve.mjs and index.html
// Sidecar fields the page shows in its details panel or views the asset by, copied into the file:// URL (README:
// "Query parameters"): `sheet`, `frameCount` and `fps` slice and play a sprite sheet, so a sheet keeps its grid there
// too. Same list as PreviewCommand.SidecarFields; tests/argv_errors.py checks the two match.
const SIDECAR_FIELDS = ['modelId', 'modelName', 'modality', 'pointsCost', 'prompt', 'createdAt', 'jobId', 'assetId', 'sheet', 'frameCount', 'fps'];
// Query keys the positional arguments decide; passing them as --key would fight the launcher's own output.
const ARGUMENT_KEYS = new Set(['file', 'f', 'path', 'items', 'dir']);
const START_TIMEOUT_MS = 6000, PROBE_TIMEOUT_MS = 1500, POLL_MS = 150, OPENER_TIMEOUT_MS = 4000;
const HEALTH_BODY_LIMIT = 64 * 1024;   // /__health is a few dozen bytes; anything streaming past this is not our server
// serve.mjs's own lines, which the log is read for — keep in step with its console output.
const SERVE_START_LINE = 'asset preview: http://';   // printed once it listens: a log section per server
const SERVE_QUIT_WHY = 'asked to quit';              // POST /__quit, which `--stop` sends
// `${why}, stopping`, for its two reasons only: a served folder whose path ends in ", stopping" is not a stop.
const SERVE_STOP_LINE = new RegExp(`^(no request for \\d+ min|${SERVE_QUIT_WHY}), stopping$`);
const LOG_LIMIT = 256 * 1024;   // a server writes about five lines; past this the log is started over

// `--json` (what `unity ai preview` passes under a machine format): no lines, one JSON object on stdout at the end
// with the same content, so a caller reads data instead of this file's wording. Usage errors stay plain stderr.
const JSON_OUT = process.argv.slice(2).includes('--json');
const said = [];   // [key, value, isError] in the order they were said
const out = (key, value) => (JSON_OUT ? said.push([key, value, false]) : console.log(`${(key + ':').padEnd(10)}${value}`));
const fail = (key, value) => (JSON_OUT ? said.push([key, value, true]) : console.error(`${(key + ':').padEnd(10)}${value}`));
// The JSON object: the links, whether this run started a server, every `server:` line (advisories included), the
// browser line, notes, and the errors (`fail` lines) in order. Written with a callback so an exit right after it
// cannot cut it off on a pipe.
function report(extra) {
  const lines = (k) => said.filter(([key]) => key === k).map(([, v]) => v);
  const result = { preview: lines('preview')[0] ?? null, fallback: lines('fallback')[0] ?? null, server: lines('server'), browser: lines('browser').at(-1) ?? null,
    notes: [...lines('note'), ...lines('sidecar')], errors: said.filter(([, , e]) => e).map(([key, value]) => ({ key, value })), ...extra };
  return new Promise((done) => process.stdout.write(JSON.stringify(result) + '\n', done));
}
// UNC / network paths are refused here as serve.mjs refuses them: the server would otherwise reach the host.
const isNetworkPath = (p) => /^[\\/]{2}/.test(String(p));
const fwd = (p) => p.replace(/\\/g, '/');

function usage(msg) {
  if (msg) console.error(msg);
  console.error('usage: node open.mjs <file-or-folder>... [--root <dir>]... [--port <n>] [--idle <minutes>|default] [--open] [--no-dir] [--json] [--<param> <value>]...');
  console.error('       node open.mjs --stop [--port <n>] [--json]');
  process.exit(2);
}

// ---- arguments -------------------------------------------------------------
const targets = [], rootArgs = [], params = [];
let port = DEFAULT_PORT, openBrowser = false, withDir = true, stop = false, idle = null;   // idle: null = leave the server's limit alone; 'default' = the server's default
const PORT_TRIES = 10;   // ports tried past --port when the one asked for holds a server this launcher cannot use
const argv = process.argv.slice(2);
for (let i = 0; i < argv.length; i++) {
  const a = argv[i];
  const value = () => {   // the next argument, which must not itself be a flag: `--root --open` is a mistake, not a folder
    const v = argv[i + 1];
    if (v === undefined || v.startsWith('--')) usage(`${a} needs a value`);
    return argv[++i];
  };
  if (a === '--json') continue;   // read above, before any output
  if (a === '--open') openBrowser = true;
  else if (a === '--stop') stop = true;
  else if (a === '--no-dir') withDir = false;
  else if (a === '--root') rootArgs.push(value());
  else if (a === '--port') { port = Number(value()); if (!Number.isInteger(port) || port < 1 || port > 65535) usage('--port needs a number between 1 and 65535'); }
  else if (a === '--idle') { const v = value(); idle = v === 'default' ? v : Number(v); if (idle !== 'default' && (!Number.isInteger(idle) || idle < 0)) usage('--idle needs a whole number of minutes (0 = never exit) or "default"'); }
  else if (a.startsWith('--')) {
    const key = a.slice(2);
    if (!/^[A-Za-z][A-Za-z0-9_]*$/.test(key)) usage(`unknown option ${a}`);
    if (ARGUMENT_KEYS.has(key)) usage(`${a}: pass files and folders as plain arguments instead`);
    params.push([key, value()]);
  }
  else targets.push(a);
}
if (stop) {
  if (targets.length || rootArgs.length || params.length || openBrowser || !withDir || idle !== null) usage('--stop takes only --port');
  // The launcher may have moved past --port to the next free one (see ensureServer), so every port in that range
  // that holds a preview server is asked to stop; the outcome is reported per port.
  const first = port; let found = 0, failed = 0;
  for (let i = 0; i < PORT_TRIES; i++, port++) {
    const h = await health();
    if (!h) continue;
    found++;
    if (typeof h.idleMinutes !== 'number') { failed++; fail('server', `the preview server on port ${port} predates this launcher and cannot be asked to stop — end the process listening on that port yourself`); continue; }
    const r = await post('/__quit');
    if (r.status === 200) out('server', `asked the preview server on port ${port} to stop`);
    else { failed++; fail('server', `the server on port ${port} did not stop (${r.error ?? `HTTP ${r.status}`})`); }
  }
  if (!found) out('server', `nothing running on ports ${first} to ${port - 1}`);
  if (JSON_OUT) await report({ stopped: !failed });
  process.exit(failed ? 1 : 0);
}
if (!targets.length) usage();

// ---- what to show ----------------------------------------------------------
// A local path that exists, as a file or as a folder; anything else (missing, unreadable, a device, a share) is a
// usage error naming the real reason, since the URL would only fail later inside the page.
async function localPath(given, { folder = false } = {}) {
  const abs = resolve(given);
  if (isNetworkPath(given) || isNetworkPath(abs)) usage(`network paths are refused: ${given}`);
  let s;
  try { s = await stat(abs); } catch (err) { usage(err.code === 'ENOENT' ? `not found: ${abs}` : `cannot read ${abs} (${err.code})`); }
  if (folder && !s.isDirectory()) usage(`--root needs a folder: ${abs}`);
  if (!s.isDirectory() && !s.isFile()) usage(`not a file or a folder: ${abs}`);
  // stat only proves it is there. The server will read the file, or list and traverse the folder; without that
  // permission the preview URL would be printed and then fail inside the page, so it is an argument error here.
  // (A permission that changes after this check is the server's 403/404 to report, not ours.)
  try { await access(abs, s.isDirectory() ? FS.R_OK | FS.X_OK : FS.R_OK); }
  catch (err) { usage(`cannot read ${abs} (${err.code})`); }
  return { kind: s.isDirectory() ? 'dir' : 'file', abs };
}
const items = [];   // [key, absolute path]
for (const t of targets) { const { kind, abs } = await localPath(t); items.push([kind, abs]); }
const roots = [];
for (const r of rootArgs) roots.push((await localPath(r, { folder: true })).abs);

// The folders the shown files live in, plus any --root: a root ADDS a folder (a material's maps kept elsewhere,
// the next generation's folder), it does not replace the ones the arguments need — serving a root while refusing
// the file in the URL would print a preview that 403s. A folder that is a whole drive (a file given at C:\ or /)
// is refused: serve.mjs would then hand out every file on it; `serve.mjs --all` exists for that choice.
const fileFolders = [...new Set(items.filter(([k]) => k === 'file').map(([, p]) => dirname(p)))];
const serveRoots = [...new Set([...items.map(([k, p]) => (k === 'dir' ? p : dirname(p))), ...roots])];
for (const r of serveRoots) if (dirname(r) === r) usage(`refusing to serve a whole drive (${r}): put the file in a folder, or pass --root <folder>`);

// Readable query strings: encode everything, then let ':' and '/' back in (both are legal in a query).
const enc = (v) => encodeURIComponent(v).replace(/%3A/gi, ':').replace(/%2F/gi, '/');
const query = (list, extra = []) => [...list.map(([k, p]) => [k, fwd(p)]), ...params, ...extra].map(([k, v]) => `${enc(k)}=${enc(v)}`).join('&');
// Files that all live in one folder bring the folder along (served page only): listed after the files, so the
// page selects the files and then fills in the folder's other generated assets without repeating them.
const folderParam = withDir && items.every(([k]) => k === 'file') && fileFolders.length === 1 ? [['dir', fwd(fileFolders[0])]] : [];

// The file:// page cannot read a sidecar, so the fallback URL carries the sidecar's fields itself. Only fields
// the caller did not pass already. A sidecar that is not JSON is skipped with a note, and the next suffix is tried.
async function sidecarFields(file) {
  const given = new Set(params.map(([k]) => k));
  for (const name of SIDECAR_SUFFIXES.map((suffix) => file + suffix)) {
    const text = await readFile(name, 'utf8').catch(() => null);
    if (text === null) continue;
    try {
      const j = JSON.parse(text);
      return Object.fromEntries(SIDECAR_FIELDS.filter((f) => !given.has(f) && j[f] !== undefined && j[f] !== null && j[f] !== '').map((f) => [f, String(j[f])]));
    } catch { out('sidecar', `${name} is not valid JSON — its fields are left out of the fallback URL`); }
  }
  return {};
}
// One file: plain parameters, which the page applies to it. Several: `items=`, a JSON array of {path, ...fields},
// so each asset keeps its OWN model, cost and ids — as plain parameters the first file's sidecar would be shown
// for every one of them.
async function fallbackQuery(files) {
  if (!files.length) return null;
  if (files.length === 1) return query(files, Object.entries(await sidecarFields(files[0][1])));
  const list = [];
  for (const [, p] of files) list.push({ path: fwd(p), ...(await sidecarFields(p)) });
  return query([], [['items', JSON.stringify(list)]]);
}
const fileItems = items.filter(([k]) => k === 'file');
const fallbackQ = await fallbackQuery(fileItems);
const fallbackUrl = fallbackQ === null ? null : `${pathToFileURL(INDEX).href}?${fallbackQ}`;

// ---- the server ------------------------------------------------------------
// The health answer of a preview server on the port, or null. Inactivity and total time are both bounded, and so is
// the body: a listener that keeps a socket busy, or streams forever, must not hold the launcher.
function health(timeoutMs = PROBE_TIMEOUT_MS) {
  return new Promise((done) => {
    let settled = false;
    const finish = (v) => { if (!settled) { settled = true; clearTimeout(timer); done(v); } };
    const rq = get({ host: '127.0.0.1', port, path: '/__health', timeout: timeoutMs }, (r) => {
      let body = '';
      r.on('data', (c) => { body += c; if (body.length > HEALTH_BODY_LIMIT) { rq.destroy(); finish(null); } });
      r.on('end', () => { try { const j = JSON.parse(body); finish(j.service === SERVICE_ID ? j : null); } catch { finish(null); } });
    });
    const timer = setTimeout(() => { rq.destroy(); finish(null); }, timeoutMs);
    rq.on('error', () => finish(null));
    rq.on('timeout', () => { rq.destroy(); finish(null); });
  });
}
// One JSON POST to the running server from this process (never a page): status and body, or an error.
function post(path, payload) {
  return new Promise((done) => {
    const rq = httpRequest({ host: '127.0.0.1', port, path, method: 'POST', headers: { 'content-type': 'application/json' }, timeout: PROBE_TIMEOUT_MS }, (r) => {
      let body = ''; r.on('data', (c) => (body += c)); r.on('end', () => done({ status: r.statusCode, body }));
    });
    rq.on('error', (e) => done({ error: e.message }));
    rq.on('timeout', () => { rq.destroy(); done({ error: 'no answer' }); });
    rq.end(payload === undefined ? undefined : JSON.stringify(payload));
  });
}
// POST /__root: what a second `serve.mjs --root` start does. Refused for browsers, accepted from a local process.
// The server answers 200 whether or not it accepted every folder, so its `roots` list is checked against what was
// asked (both as the filesystem names them, the way the server records roots).
async function widen(dirs) {
  const reply = await post('/__root', { roots: dirs });
  if (reply.error) return { ok: false, why: `the running server did not answer the request to serve ${dirs.join(', ')} (${reply.error})` };
  if (reply.status !== 200) return { ok: false, why: `the running server refused to serve ${dirs.join(', ')} (HTTP ${reply.status})` };
  let served;
  try { served = JSON.parse(reply.body); } catch { return { ok: false, why: 'the running server gave an unreadable answer when asked to serve this folder' }; }
  if (served.restricted === false) return { ok: true };   // serves everything already
  const norm = (p) => (process.platform === 'win32' ? p.toLowerCase() : p);
  const under = (p, r) => norm(p) === norm(r) || norm(p).startsWith(norm(r.endsWith(sep) ? r : r + sep));
  const missing = [];
  for (const d of dirs) {
    const real = await realpath(d).catch(() => d);
    if (!(Array.isArray(served.roots) && served.roots.some((r) => under(real, r)))) missing.push(d);
  }
  return missing.length ? { ok: false, why: `the running server did not add ${missing.join(', ')}; files there will not load — stop it and run again` } : { ok: true };
}
const sleep = (ms) => new Promise((r) => setTimeout(r, ms));

// The server's output goes to a log per port in the temp folder, since it outlives this command and has no terminal.
const serverLog = (p) => join(tmpdir(), `unity-ai-preview-${p}.log`);
// What is at the log's path: 'none', 'ours' (a regular file this user owns), or 'foreign' (anything else, never
// read, truncated or appended to). The owner check only exists where uids do; Windows temp folders are per-user.
function logState(path) {
  let st;
  try { st = lstatSync(path); } catch (e) { return e.code === 'ENOENT' ? 'none' : 'foreign'; }
  if (!st.isFile()) return 'foreign';
  return typeof process.getuid === 'function' && st.uid !== process.getuid() ? 'foreign' : 'ours';
}
// A crash is Node's uncaught-error report: a line starting with the error's name (`TypeError: …`,
// `Error [ERR_X]: …`) followed by its stack. A line that only contains the word (a served folder named BuildErrors)
// is not one.
const CRASH_LINE = /^[A-Za-z]*Error\b[^:]*:/;
const STACK_LINE = /^at /;
// Why the last server started on port `p` stopped, read from its section of the log, or null when there is none
// (no server was started there by this launcher, or the log was started over). Only called before starting a new
// server, so that last server is gone: a section with no stop line ended without saying so.
function previousStop(p) {
  let text;
  if (logState(serverLog(p)) !== 'ours') return null;
  try { text = readFileSync(serverLog(p), 'utf8'); } catch { return null; }
  const at = text.lastIndexOf(SERVE_START_LINE);
  if (at < 0) return null;
  const lines = text.slice(at).split(/\r?\n/).slice(1).map((l) => l.trim()).filter(Boolean);
  const stop = lines.map((l) => SERVE_STOP_LINE.exec(l)).find(Boolean);
  if (stop) return stop[1] === SERVE_QUIT_WHY ? 'was stopped with --stop' : `stopped by itself: ${stop[1]}`;
  const error = lines.find((l, i) => CRASH_LINE.test(l) && STACK_LINE.test(lines[i + 1] || ''));
  if (error) return `crashed: ${error.slice(0, 200)}`;
  return 'ended without saying why: its process was closed from outside, with the app that started it, by a kill or by a restart';
}
// The log to hand the server, opened for appending (two launchers racing for a port must not clobber each other's
// lines), or null when the temp folder will not take it: the server then runs unlogged, as before.
function openServerLog(p) {
  try {
    const path = serverLog(p);
    const state = logState(path);
    if (state === 'foreign') return null;
    // O_NOFOLLOW: a symlink swapped in after the check is refused, not written through (0 where it does not exist).
    const flags = FS.O_WRONLY | FS.O_CREAT | FS.O_APPEND | (FS.O_NOFOLLOW || 0);
    const big = state === 'ours' && lstatSync(path).size > LOG_LIMIT;
    return openSync(path, big ? flags | FS.O_TRUNC : flags, 0o600);
  } catch { return null; }
}

// A server is only usable once it serves the folders this run needs. Whichever way we got one — it was already
// there, we started it, or ours lost a race and another won the port — the same check runs, because "healthy" and
// "serving our folders" are not the same thing and the difference is a page full of 403s.
// A server from before the idle limit existed: it never exits and has no /__quit, so it cannot be reused or stopped
// from here. (One without root scoping is older still.)
const outdated = (h) => typeof h.restricted !== 'boolean' || typeof h.idleMinutes !== 'number';
async function usable(h, started) {
  if (h.restricted) { const w = await widen(serveRoots); if (!w.ok) return { ok: false, why: w.why }; }
  // A running server keeps its limit unless this run asked for one: `--idle 0` on an existing server must hold.
  // The idle limit is not what makes the server usable, so a refusal is a warning beside a working preview URL;
  // a connection error is re-probed, and a server that vanished meanwhile is reported so the caller starts one.
  let idleNote = null, idleWarn = false;
  const want = idle === 'default' ? h.defaultIdleMinutes : idle;
  if (!started && idle !== null && h.idleMinutes !== want) {
    const r = await post('/__idle', { minutes: idle });
    if (r.error && !(await health())) return { gone: true };
    if (r.status === 200) idleNote = want ? `idle limit of the running server set to ${want} min` : 'the running server now stays up until stopped';
    else { idleWarn = true; idleNote = `the running server kept its idle limit of ${h.idleMinutes} min: --idle ${idle} was not taken (${r.error ?? `HTTP ${r.status}`})`; }
  }
  return { ok: true, started, idleNote, idleWarn };
}

// One usable server: the one already on the port, or one started there. A port holding a server this launcher
// cannot use (an older serve.mjs, which never exits) is skipped for the next free one, so an upgrade's first
// generation shows its preview instead of a refusal; the old process is named so the user can end it.
async function ensureServer() {
  const skipped = [];
  for (let i = 0; i < PORT_TRIES; i++, port++) {
    const running = await health();
    if (running && outdated(running)) { skipped.push(port); continue; }
    if (running) {
      const u = await usable(running, false);
      if (!u.gone) return { ...u, skipped };
    }
    const started = await startServer();
    if (started.portTaken || started.gone) continue;   // a foreign program holds the port, or the winner of it vanished: next port
    return { ...started, skipped };
  }
  return { ok: false, why: `no usable port between ${port - PORT_TRIES} and ${port - 1}`, skipped };
}
// Start serve.mjs detached. On Windows a child inherits every inheritable handle of this process, including the
// pipe a caller reads our output from (`unity ai preview` run by an agent), so the hour-long server would hold that
// pipe open and the caller would wait for it after we have printed the link and exited. There the server is started
// through PowerShell's Start-Process, which hands it no inherited handles: without a -Redirect* parameter it goes through
// ShellExecute, which does not inherit. Never add -RedirectStandardOutput/-RedirectStandardError here: they switch it to
// CreateProcess with inheritance, and the pipe hang is back (the log is redirected by cmd for that reason).
function spawnServer(args, log) {
  if (process.platform === 'win32') {
    // cmd does the redirection itself (append, as the opened log was), so the log keeps working without handing
    // this process's handles on; `log` is the path here, not a descriptor. Paths reach cmd through environment
    // variables, never in its command line: cmd expands %NAME% even inside quotes, which would turn a folder
    // named %USERNAME% into another folder, and the server would serve that one too.
    const root = process.env.SystemRoot || 'C:/Windows';
    const vars = {};
    [process.execPath, ...args, ...(log === null ? [] : [log])].forEach((v, i) => { vars[`UNITY_AI_SERVE_${i}`] = String(v); });
    const refs = [process.execPath, ...args].map((_, i) => `"%UNITY_AI_SERVE_${i}%"`).join(' ');
    const cmdline = `/d /v:off /c "${refs} >> ${log === null ? 'NUL' : `"%UNITY_AI_SERVE_${args.length + 1}%"`} 2>&1"`;
    const ps = (a) => `'${a.replace(/'/g, "''")}'`;
    const script = `Start-Process -WindowStyle Hidden -FilePath ${ps(join(root, 'System32', 'cmd.exe'))} -ArgumentList ${ps(cmdline)}`;
    return spawn(join(root, 'System32', 'WindowsPowerShell', 'v1.0', 'powershell.exe'),
      ['-NoProfile', '-NonInteractive', '-Command', script], { stdio: 'ignore', windowsHide: true, env: { ...process.env, ...vars } });
  }
  return spawn(process.execPath, args, { detached: true, stdio: log === null ? 'ignore' : ['ignore', log, log], windowsHide: true });
}
// Start serve.mjs on `port` and wait for it to answer. Its output is not ours to show (it outlives us), but an
// early exit is: a refused --root, a port taken meanwhile, a Node that will not run — each would otherwise look
// like a timeout.
async function startServer() {
  let exited = null, h = null;
  const previous = previousStop(port);
  let log = openServerLog(port);
  // Windows hands cmd the log's path, not the descriptor (see spawnServer).
  const logPath = process.platform === 'win32' && log !== null ? serverLog(port) : null;
  let logStart = 0;
  if (logPath !== null) { closeSync(log); log = logPath; try { logStart = lstatSync(logPath).size; } catch { /* new file */ } }
  // On Windows the child is PowerShell, which says nothing of how the server ended: its early exit is read from what
  // the server wrote to the log since this start (a port held by another program, a refused --root, a crash).
  const logTail = () => { try { return readFileSync(logPath).subarray(logStart).toString('utf8'); } catch { return ''; } };
  const serveArgs = [SERVE, String(port), ...serveRoots.flatMap((r) => ['--root', r]), ...(idle === null || idle === 'default' ? [] : ['--idle', String(idle)])];
  const child = spawnServer(serveArgs, log);
  if (log !== null && logPath === null) closeSync(log);   // the server holds its own handle
  child.on('error', (e) => { exited = process.platform === 'win32' ? `PowerShell could not be started (${e.message})` : `node could not start serve.mjs (${e.message})`; });
  let exitCode = null;
  // On Windows the child is PowerShell, which exits as soon as it has started the server: only a failure counts.
  child.on('exit', (code, signal) => {
    if (process.platform === 'win32' && code === 0) return;
    const how = signal ? `signal ${signal}` : `code ${code}`;
    exitCode = code; exited = process.platform === 'win32' ? `PowerShell could not start serve.mjs (exit ${how})` : `serve.mjs exited with ${how}`;
  });
  child.unref();
  const deadline = Date.now() + START_TIMEOUT_MS;
  while (!h && exited === null && Date.now() < deadline) {
    await sleep(POLL_MS);
    h = await health(Math.max(200, Math.min(PROBE_TIMEOUT_MS, deadline - Date.now())));
    if (!h && logPath !== null && logTail().includes(`port ${port} is taken by something else`)) { exitCode = SERVE_EXIT_PORT_TAKEN; exited = 'serve.mjs found the port taken by something else'; }
  }
  // Ours may have exited 0 precisely because another instance won the port; that one is a stranger to our roots,
  // so it goes through the same usable() check as any server we did not start.
  if (!h && exited) h = await health();
  if (h) return outdated(h) ? { portTaken: true } : { ...(await usable(h, exited === null)), previous };   // an older server may have won the port meanwhile
  if (exitCode === SERVE_EXIT_PORT_TAKEN) return { portTaken: true };
  if (logPath !== null && exited === null) {
    // Anything the server wrote besides its start lines (serve.mjs's `asset preview:`, `serving files only under:`,
    // `exits after`/`stays up` and `already running:`) is what it printed on the way out.
    const last = logTail().split(/\r?\n/).map((l) => l.trim()).filter((l) => l && !/^(asset preview:|serving files only under:|exits after |stays up until |already running: )/.test(l)).at(-1);
    if (last) exited = `serve.mjs stopped (${last.slice(0, 200)})`;
  }
  if (exited) return { ok: false, why: `${exited} before answering — run it by hand to see why: node "${SERVE}" ${port} --root "<folder>"` };
  return { ok: false, why: `nothing answered on port ${port} within ${START_TIMEOUT_MS / 1000}s (is the port taken by another program?)` };
}

// ---- open -------------------------------------------------------------------
function openInBrowser(url) {
  return new Promise((done) => {
    let child;
    try {
      if (process.platform === 'win32') {
        // The system's own cmd.exe by absolute path: on Windows a writable folder early in PATH is common, and
        // `cmd` is a name anyone can shadow. Its quoting: `start "" "<url>"` keeps the & of the query string out
        // of cmd's hands.
        const cmd = join(process.env.SystemRoot || 'C:/Windows', 'System32', 'cmd.exe');
        child = spawn(cmd, ['/d', '/c', `start "" "${url.replace(/"/g, '%22')}"`], { windowsVerbatimArguments: true, windowsHide: true, stdio: 'ignore' });
      } else {
        // macOS ships `open` at a fixed path, so pin it for the same reason; `xdg-open` has no fixed home and
        // must come from PATH, as every desktop launcher on Linux does.
        child = spawn(process.platform === 'darwin' ? '/usr/bin/open' : 'xdg-open', [url], { stdio: 'ignore' });
      }
    } catch (e) { return done(String(e?.message ?? e)); }
    // The openers hand the URL to the browser and return; an opener that lingers (some xdg-open setups wait
    // for the browser) is not an error, so stop waiting after a moment and let it be.
    const timer = setTimeout(() => { child.removeAllListeners(); child.unref(); done(null); }, OPENER_TIMEOUT_MS);
    child.on('error', (e) => { clearTimeout(timer); done(String(e?.message ?? e)); });
    child.on('exit', (code) => { clearTimeout(timer); done(code === 0 ? null : `opener exited with code ${code}`); });
  });
}

// Redirect pages older than a day are removed before a new one is written, so they do not pile up in the temp
// folder; only ours (the name and .html), and only what this user may remove.
function clearOldPages() {
  try {
    const cutoff = Date.now() - 24 * 60 * 60 * 1000;
    for (const name of readdirSync(tmpdir())) {
      if (!/^unity-ai-preview-[0-9a-f-]{36}\.html$/.test(name)) continue;
      const file = join(tmpdir(), name);
      try { const st = lstatSync(file); if (st.isFile() && st.mtimeMs < cutoff) unlinkSync(file); } catch { /* not ours to remove, or gone */ }
    }
  } catch { /* an unreadable temp folder: nothing to clear */ }
}
// What to hand the opener for `url`. The OS opens a file:// URL as a path and drops its query (Windows' shell
// does), and the query is the whole asset list of the fallback: so a small page in the temp folder redirects to
// it, and that page is opened. Created under a new random name, never over an existing file (a shared /tmp).
function openable(url) {
  if (!url.startsWith('file:') || !url.includes('?')) return url;
  const attr = url.replace(/&/g, '&amp;').replace(/"/g, '&quot;').replace(/</g, '&lt;').replace(/>/g, '&gt;');
  clearOldPages();
  const page = join(tmpdir(), `unity-ai-preview-${randomUUID()}.html`);
  const fd = openSync(page, 'wx', 0o600);
  try { writeSync(fd, `<!doctype html><meta charset="utf-8"><meta http-equiv="refresh" content="0;url=${attr}"><title>Asset Preview</title><a href="${attr}">Open the preview</a>`); }
  finally { closeSync(fd); }
  return pathToFileURL(page).href;
}

// ---- go ---------------------------------------------------------------------
const server = await ensureServer();
const previewUrl = server.ok ? `http://127.0.0.1:${port}/?${query(items, folderParam)}` : null;
if (previewUrl) out('preview', previewUrl);
if (fallbackUrl) out('fallback', fallbackUrl);
else if (!server.ok) out('note', 'no fallback URL: a page opened from disk cannot list a folder — pass files for one');   // only matters when the served URL is missing
for (const p of server.skipped ?? []) fail('server', `an older preview server is still running on port ${p}; it never exits on its own and cannot be stopped from here — end that process when convenient`);
if (server.started) out('server', `started serve.mjs on port ${port}, serving files under ${serveRoots.join(', ')}${server.previous ? ` (the previous server ${server.previous})` : ''}`);
if (server.idleNote) (server.idleWarn ? fail : out)('server', server.idleNote);
if (!server.ok) fail('server', server.why);
let opened = true;
if (openBrowser) {
  const target = previewUrl ?? fallbackUrl;
  if (!target) { opened = false; fail('browser', 'nothing to open: no server and no file to show from disk'); }
  else {
    let err;
    try { err = await openInBrowser(openable(target)); } catch (e) { err = String(e?.message ?? e); }
    if (err) { opened = false; fail('browser', `could not open the default browser (${err}); open the URL above yourself`); }
    else out('browser', `opened ${previewUrl ? 'the preview' : 'the fallback'} in the default browser`);
  }
}
// Set the code and let Node exit on its own: process.exit() can cut off console.log to a pipe, which is exactly
// how an agent captures this output.
process.exitCode = server.ok && opened ? 0 : 1;
if (JSON_OUT) await report({ serverStarted: !!server.started });
