#!/usr/bin/env node
// CP-0088 P0.2/P0.3 — freeze minogan.scorer/v1 fixtures from the REAL pilot pipeline.
//
// synthetic.mjs (OTLP) -> ingest.fetch (normalize + redaction + signals) -> scoreAgents -> ruleScorer (computeScore score_v0.3)
//
// The pilot is NOT modified: src/, scripts/, schema.sql are copied to a throw-away /tmp dir and only the copy's
// getScorer() is patched to capture (ScorerInput, ruleScorer output). Randomness (crypto.getRandomValues /
// randomUUID / Math.random) and the clock (Date.now) are replaced by a seeded PRNG and a fake clock, so re-running
// produces byte-identical fixtures. Local only: no network (globalThis.fetch is stubbed to refuse).
//
// usage: node scripts/minogan/gen_fixtures.mjs [--pilot /workspace/minogan-pilot] [--out tests/fixtures/minogan]
import fs from 'node:fs';
import os from 'node:os';
import path from 'node:path';
import { execFileSync } from 'node:child_process';
import { createHash } from 'node:crypto';

const args = Object.fromEntries(process.argv.slice(2).reduce((a, v, i, arr) => (v.startsWith('--') ? [...a, [v.slice(2), arr[i + 1]]] : a), []));
const PILOT = path.resolve(args.pilot || '/workspace/minogan-pilot');
const OUT = path.resolve(args.out || path.join(path.dirname(new URL(import.meta.url).pathname), '../../tests/fixtures/minogan'));
const T0 = Date.UTC(2026, 9, 1, 12, 0, 0); // fixed epoch for all worlds (2026-10-01T12:00:00Z)

// ---------- determinism: seeded PRNG + fake clock + no network ----------
let rng;
function mulberry32(a) { return () => { a |= 0; a = (a + 0x6d2b79f5) | 0; let t = Math.imul(a ^ (a >>> 15), 1 | a); t = (t + Math.imul(t ^ (t >>> 7), 61 | t)) ^ t; return ((t ^ (t >>> 14)) >>> 0) / 4294967296; }; }
const clock = { t: T0 };
const realCrypto = globalThis.crypto;
const hex = (n) => [...Array(n)].map(() => Math.floor(rng() * 256).toString(16).padStart(2, '0')).join('');
Object.defineProperty(globalThis, 'crypto', { configurable: true, writable: true, value: {
  subtle: realCrypto.subtle,
  getRandomValues: (arr) => { for (let i = 0; i < arr.length; i++) arr[i] = Math.floor(rng() * 256); return arr; },
  randomUUID: () => { const h = hex(16); return `${h.slice(0, 8)}-${h.slice(8, 12)}-4${h.slice(13, 16)}-a${h.slice(17, 20)}-${h.slice(20, 32)}`; },
} });
Math.random = () => rng();
Date.now = () => clock.t;
globalThis.fetch = async () => { throw new Error('network disabled in fixture generator'); };

// ---------- throw-away copy of the pilot ----------
const sha256File = (p) => createHash('sha256').update(fs.readFileSync(p)).digest('hex');
let pilotVersion = 'pilot unversioned at capture time';
try { pilotVersion = execFileSync('git', ['-C', PILOT, 'rev-parse', 'HEAD'], { stdio: ['ignore', 'pipe', 'ignore'] }).toString().trim(); } catch { /* not a git repo */ }
const TMP = fs.mkdtempSync(path.join(os.tmpdir(), 'minogan-capture-'));
for (const p of ['src', 'scripts', 'schema.sql', 'package.json']) fs.cpSync(path.join(PILOT, p), path.join(TMP, p), { recursive: true });
fs.symlinkSync(path.join(PILOT, 'node_modules'), path.join(TMP, 'node_modules'));
const scorerPath = path.join(TMP, 'src/shared/scorer.js');
const orig = fs.readFileSync(scorerPath, 'utf8');
const NEEDLE = 'export function getScorer(_env) {\n  return ruleScorer;\n}';
if (!orig.includes(NEEDLE)) throw new Error('pilot getScorer() changed; update the capture patch');
fs.writeFileSync(scorerPath, orig.replace(NEEDLE, `export function getScorer(_env) {
  const cap = globalThis.__MINOGAN_CAPTURE;
  if (!cap) return ruleScorer;
  return { id: 'rules', methodology: METHODOLOGY, needs: cap.needs, async score(input) {
    const snap = JSON.parse(JSON.stringify(input));
    const out = await ruleScorer.score(input);
    cap.records.push({ input: snap, expected: JSON.parse(JSON.stringify(out)) });
    return out;
  } };
}`));

const imp = (rel) => import(path.join(TMP, rel));
const { makeD1 } = await imp('scripts/d1-shim.mjs');
const { scenario, DEMO_AGENT } = await imp('scripts/synthetic.mjs');
const { sha256Hex, scoreAgents } = await imp('src/shared/engine.js');
const ingest = (await imp('src/ingest.js')).default;
const { SCORER_CONTRACT_VERSION, ruleScorer } = await imp('src/shared/scorer.js');
const { METHODOLOGY } = await imp('src/shared/rules.js');

const KEY = 'mk_dev_fixture_0123456789abcdef01';
const ctx = { waitUntil: () => {} };
const PHASES = ['baseline', 'normal', 'loop', 'policy', 'spike', 'injection', 'exfil'];
// world = { seed, autonomy, dataSensitivity, phases, events (scorer needs events), rescoreH: hours after `now` }
const WORLDS = [
  { seed: 101, autonomy: 65, dataSensitivity: 60, phases: PHASES, events: false, rescoreH: [0.5, 3, 12, 30, 72, 160] },
  { seed: 202, autonomy: 30, dataSensitivity: 20, phases: PHASES, events: true, rescoreH: [1, 26, 48] },
  { seed: 303, autonomy: 90, dataSensitivity: 95, phases: ['baseline', 'normal', 'injection', 'exfil'], events: false, rescoreH: [2, 25, 50, 100] },
  { seed: 404, autonomy: 50, dataSensitivity: 50, phases: ['baseline', 'normal', 'loop', 'spike'], events: false, rescoreH: [6, 30] },
  { seed: 505, autonomy: 10, dataSensitivity: 80, phases: ['normal', 'policy', 'exfil'], events: true, rescoreH: [1, 47, 49] },
  { seed: 606, autonomy: 75, dataSensitivity: 40, phases: ['baseline', 'policy', 'injection'], events: false, rescoreH: [24.5, 36, 96] },
  { seed: 707, autonomy: 55, dataSensitivity: 65, phases: ['baseline', 'normal'], events: false, rescoreH: [1, 30] },
  { seed: 808, autonomy: 100, dataSensitivity: 100, phases: PHASES, events: false, rescoreH: [0.25, 8, 40, 120] },
  // two-stage worlds: quiet history first (score snapshots become the 24h–7d baseline), then a later incident -> watch/elevated drift
  { seed: 909, autonomy: 60, dataSensitivity: 60, phases: ['baseline', 'normal'], events: false, rescoreH: [2, 12], later: { offsetH: 30, phases: ['spike'], rescoreH: [1, 20] } },
  { seed: 1010, autonomy: 40, dataSensitivity: 70, phases: ['baseline', 'normal'], events: true, rescoreH: [6], later: { offsetH: 28, phases: ['loop'], rescoreH: [3, 40] } },
  { seed: 1111, autonomy: 80, dataSensitivity: 30, phases: ['baseline', 'normal'], events: false, rescoreH: [4, 10], later: { offsetH: 26, phases: ['policy'], rescoreH: [12] } },
  { seed: 1212, autonomy: 20, dataSensitivity: 90, phases: ['baseline', 'normal', 'spike'], events: false, rescoreH: [5], later: { offsetH: 48, phases: ['injection'], rescoreH: [6, 30] } },
];

const records = [];
for (const [wi, w] of WORLDS.entries()) {
  rng = mulberry32(w.seed);
  const now = T0 + wi * 86400000;
  clock.t = now;
  const cap = { needs: w.events ? ['events'] : [], records: [] };
  globalThis.__MINOGAN_CAPTURE = cap;
  Object.assign(DEMO_AGENT, { autonomy: w.autonomy, dataSensitivity: w.dataSensitivity });
  const DB = await makeD1();
  const org = `org_fx_${w.seed}`;
  await DB.prepare("INSERT INTO orgs (id, name, type, is_synthetic, created_at) VALUES (?1, 'Synthetic fixture org', 'enterprise', 1, ?2)").bind(org, now).run();
  await DB.prepare("INSERT INTO api_keys (id, org_id, key_hash, env, scope, created_at, prefix) VALUES ('k_fx', ?1, ?2, 'dev', 'ingest', ?3, ?4)").bind(org, await sha256Hex(KEY), now, KEY.slice(0, 12)).run();
  const env = { DB, SESSION_SECRET: 'fixture-session-secret-0123456789abcdef' };
  const sc = scenario(now);
  const steps = [];
  for (const phase of w.phases) {
    for (const [bi, body] of sc[phase].entries()) {
      const n0 = cap.records.length;
      const res = await ingest.fetch(new Request('https://ingest.test/v1/traces', { method: 'POST', headers: { authorization: `Bearer ${KEY}`, 'content-type': 'application/json' }, body: JSON.stringify(body) }), env, ctx);
      if (res.status !== 200) throw new Error(`ingest ${phase}[${bi}] -> ${res.status} ${await res.text()}`);
      for (let k = n0; k < cap.records.length; k++) steps.push(`${phase}[${bi}]`);
    }
  }
  const rows = (await DB.prepare('SELECT * FROM agents WHERE org_id = ?1').bind(org).all()).results;
  for (const h of w.rescoreH) {
    clock.t = now + Math.round(h * 3600000);
    const n0 = cap.records.length;
    await scoreAgents(DB, rows, clock.t, env);
    for (let k = n0; k < cap.records.length; k++) steps.push(`rescore+${h}h`);
  }
  if (w.later) {
    const t1 = now + w.later.offsetH * 3600000;
    clock.t = t1;
    const sc2 = scenario(t1);
    for (const phase of w.later.phases) {
      for (const [bi, body] of sc2[phase].entries()) {
        const n0 = cap.records.length;
        const res = await ingest.fetch(new Request('https://ingest.test/v1/traces', { method: 'POST', headers: { authorization: `Bearer ${KEY}`, 'content-type': 'application/json' }, body: JSON.stringify(body) }), env, ctx);
        if (res.status !== 200) throw new Error(`ingest later ${phase}[${bi}] -> ${res.status} ${await res.text()}`);
        for (let k = n0; k < cap.records.length; k++) steps.push(`later+${w.later.offsetH}h:${phase}[${bi}]`);
      }
    }
    for (const h of w.later.rescoreH) {
      clock.t = t1 + Math.round(h * 3600000);
      const n0 = cap.records.length;
      await scoreAgents(DB, rows, clock.t, env);
      for (let k = n0; k < cap.records.length; k++) steps.push(`later+${w.later.offsetH}h:rescore+${h}h`);
    }
  }
  cap.records.forEach((r, k) => records.push({ world: w.seed, step: steps[k], ...r }));
}
delete globalThis.__MINOGAN_CAPTURE;

// ---------- variants: pipeline inputs with one field moved, scored by the REAL pilot ruleScorer ----------
// Covers drift bands the scenario rarely hits (watch/elevated), null onboarding attrs and no-write agents.
const pipelineCount = records.length;
for (const [k, r] of records.slice(0, pipelineCount).entries()) {
  if (k % 6 !== 0) continue;
  const s0 = r.expected.score;
  const vs = [
    ['baseline_watch', (i) => { i.baseline_score = Math.max(1, Math.round(s0 / 1.15)); }],
    ['baseline_elevated', (i) => { i.baseline_score = Math.max(1, Math.round(s0 / 1.35)); }],
    ['baseline_drop', (i) => { i.baseline_score = Math.min(100, s0 + 20); }],
    ['null_onboarding', (i) => { i.agent.autonomy = null; i.agent.data_sensitivity = null; }],
    ['no_writes', (i) => { i.features.writes = 0; i.features.approvedWrites = 0; i.features.writeTools = 0; }],
  ];
  for (const [name, f] of vs) {
    const input = JSON.parse(JSON.stringify(r.input));
    delete input.events; // computeScore ignores events; keep fixtures small
    f(input);
    const expected = JSON.parse(JSON.stringify(await ruleScorer.score(JSON.parse(JSON.stringify(input)))));
    records.push({ world: r.world, step: `${r.step}|variant:${name}`, input, expected });
  }
}

// ---------- canonical JSON (sorted keys, no whitespace) for dedup ----------
const canon = (v) => (Array.isArray(v) ? `[${v.map(canon).join(',')}]` : v && typeof v === 'object'
  ? `{${Object.keys(v).sort().filter((k) => v[k] !== undefined).map((k) => `${JSON.stringify(k)}:${canon(v[k])}`).join(',')}}` : JSON.stringify(v));
const seen = new Set();
const fixtures = [];
for (const r of records) {
  const d = createHash('sha256').update(canon(r.input)).digest('hex');
  if (seen.has(d)) continue;
  seen.add(d);
  fixtures.push({ id: `fx_${String(fixtures.length).padStart(3, '0')}`, world: r.world, step: r.step, input_sha256: d, input: r.input, expected: r.expected });
}

// ---------- redaction guard: no prompt/completion/tool-arg content may survive ----------
const blob = JSON.stringify(fixtures);
for (const bad of ['SYNTHETIC prompt', 'IGNORE ALL', 'jane.doe', '4111 1111', '123-45-6789', 'Synthetic export', '"prompt"', '"completion"', 'gen_ai.input.messages', 'gen_ai.tool.call.arguments', 'gen_ai.tool.call.result']) {
  if (blob.includes(bad)) throw new Error(`content leak in fixtures: ${bad}`);
}

// ---------- invalid inputs (typed-error cases), derived from valid fixtures ----------
const base = fixtures.find((f) => f.input.signals.length >= 2 && f.input.events) || fixtures[0];
const clone = () => { const i = JSON.parse(JSON.stringify(base.input)); i.events = i.events.slice(0, 3); return i; };
const mut = (code, f) => { const i = clone(); f(i); return { code, from: base.id, input: i }; };
const invalid = [
  mut('contract_version', (i) => { i.contract = 'minogan.scorer/v2'; }),
  mut('validation', (i) => { delete i.features; }),
  mut('validation', (i) => { i.signals[0].severity = 'critical'; }),
  mut('validation', (i) => { i.features.distinctTools = '4'; }),
  mut('validation', (i) => { i.agent.allowed_tools = 'lookup_order'; }),
  mut('validation', (i) => { i.window = { from: 1 }; }),
  mut('validation', (i) => { i.unexpected_top_level = 1; }),
  mut('content_key', (i) => { i.signals[0].prompt = 'redacted-in-real-life'; }),
  mut('content_key', (i) => { i.events[0].completion = 'redacted-in-real-life'; }),
  mut('content_key', (i) => { i.agent['gen_ai.input.messages'] = 'x'; }),
  mut('limit', (i) => { i.events = Array.from({ length: 201 }, () => i.events[0]); }),
  mut('limit', (i) => { i.signals[0].trace_ids = Array.from({ length: 11 }, (_, k) => `t${k}`); }),
];

fs.mkdirSync(OUT, { recursive: true });
const meta = {
  schema: 'mesh.minogan.fixtures/v0',
  contract: SCORER_CONTRACT_VERSION, pilot_methodology: METHODOLOGY,
  pilot_path: PILOT, pilot_version: pilotVersion,
  pilot_files_sha256: Object.fromEntries(['src/shared/scorer.js', 'src/shared/rules.js', 'src/shared/engine.js', 'src/shared/normalize.js', 'src/ingest.js', 'scripts/synthetic.mjs']
    .map((p) => [p, sha256File(path.join(PILOT, p))])),
  generator: 'scripts/minogan/gen_fixtures.mjs', node: process.version, epoch_t0: T0,
  worlds: WORLDS, count: fixtures.length, pipeline_captures: pipelineCount, variant_rule: 'every 6th pipeline capture x {baseline_watch, baseline_elevated, baseline_drop, null_onboarding, no_writes}; expected from the real pilot ruleScorer',
  note: 'SYNTHETIC TEST DATA. Inputs captured from the real pilot pipeline (ingest redaction applied); expected = pilot ruleScorer output (computeScore score_v0.3) before validateOutput. Metadata only.',
};
// one fixture per line keeps diffs reviewable without pretty-printing megabytes
const write = (name, obj, listKey) => fs.writeFileSync(path.join(OUT, name),
  `{"meta":${JSON.stringify(obj.meta)},\n"${listKey}":[\n${obj[listKey].map((x) => JSON.stringify(x)).join(',\n')}\n]}\n`);
write('scorer_v1_fixtures.json', { meta, fixtures }, 'fixtures');
write('scorer_v1_invalid.json', { meta: { schema: 'mesh.minogan.fixtures.invalid/v0', from: base.id, count: invalid.length }, cases: invalid }, 'cases');
fs.rmSync(TMP, { recursive: true, force: true });
console.log(JSON.stringify({ fixtures: fixtures.length, captured: records.length, pipeline: pipelineCount, invalid: invalid.length, pilot_version: pilotVersion, out: OUT }));
