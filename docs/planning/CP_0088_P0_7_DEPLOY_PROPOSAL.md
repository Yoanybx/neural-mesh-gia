# CP-0088 P0.7 — Mesh Minogan service: deployment PROPOSAL

> **PROPOSAL ONLY. No costs incurred.** No account, key, VM, domain, tunnel, bucket or registry was created; no
> image was pushed; nothing was deployed. Every price below was read from the provider's page on
> **2026-10-18** (America/New_York) and must be re-checked at order time. Prices exclude VAT/taxes.

Artifacts in this commit: `deploy/minogan/Dockerfile` (+ `Dockerfile.dockerignore`), `deploy/minogan/compose.proposal.yaml`
(not run), `deploy/minogan/smoke.py` + `smoke_input.json`, `deploy/minogan/README.md`.

## 1. What has to be hosted

One process: `mesh minogan serve` (stdlib HTTP, P0.5) + AgentMemory (P0.4) + score ledger (P0.6) under one root.

Hard constraints (from the code, not preferences):

| Constraint | Why | Consequence |
|------------|-----|-------------|
| Persistent local disk | memory, ledger and C-RAM objects are files; restart must keep them | no ephemeral-disk platform as primary storage |
| POSIX semantics: `fcntl.flock`, `fsync`, atomic `rename`, `O_APPEND` | crash-safe pending-head protocol (kill -9 tested) | no object-storage FUSE (R2/S3 mounts) as primary storage |
| **Single writer** per root | per-agent locks are in-process; per-tenant ledger coverage cache is per process | exactly **one** replica; no horizontal scaling on a shared volume |
| Loopback bind (`127.0.0.1`) | code guard: `make_server` refuses non-loopback hosts | exposure via a connector in the same network namespace (§3) |
| Small footprint | ~60 MB RSS; p95 46 ms @ 200 events with ledger (local bench) | the smallest VM/machine size is enough to start |

## 2. Hosting options (monthly, list price, checked 2026-10-18)

| Option | Compute | Persistent disk | Est. / month | Fit | Source |
|--------|---------|-----------------|--------------|-----|--------|
| **DigitalOcean Droplet, Basic 1 GiB / 1 vCPU / 25 GiB SSD** | $6.00 | local SSD included (Volumes: 100 GiB $10) ; weekly backups +20% ($1.20) | **$6.00–7.20** | ✅ real disk, flock, single writer natural; US + EU regions | https://www.digitalocean.com/pricing/droplets · https://www.digitalocean.com/pricing/volumes |
| DigitalOcean Basic 512 MiB / 1 vCPU / 10 GiB | $4.00 | included | $4.00 | ⚠️ tight with Docker + cloudflared | same |
| Hetzner Cloud CX23 (2 vCPU / 4 GB / 40 GB, **EU only**: FSN/NBG/HEL) | €5.49 ($6.49) excl. IPv4 | local 40 GB; Volume €0.0572/GB; Snapshot €0.0143/GB | **≈ €5.5–6.5** | ✅ best spec/€; ⚠️ third-party trackers report CX23 often sold out (Oct 2026); EU data residency | https://docs.hetzner.com/general/infrastructure-and-availability/price-adjustment/ (June 2026 table; volume price from the April 2026 revision: https://web.archive.org/web/20260513201413/https:/docs.hetzner.com/general/infrastructure-and-availability/price-adjustment/) |
| Hetzner Cloud US (ASH/HIL) CPX11 (2 vCPU / 2 GB) | €17.49 ($20.49) | local 40 GB | ≈ $20.5 | ✅ but 3× DO for the same need | same (June 2026 table) |
| Fly.io `shared-cpu-1x` 512 MB + 3 GB volume | $3.69 | Volume $0.15/GB ($0.45); snapshots first 10 GB free | **≈ $4.14** (+$2 dedicated IPv4 optional) | ⚠️ volume = one NVMe on one host, no replication (Fly warns: single volume ⇒ downtime/data-loss risk); Fly proxy expects a non-loopback bind ⇒ needs cloudflared **inside** the container (or the opt-in flag, §3C) | https://fly.io/docs/about/pricing/ · https://fly.io/docs/volumes/overview/ |
| Railway Hobby (0.5 GB RAM always-on + 1 GB volume) | $5 plan incl. $5 usage; RAM $10/GB-mo, CPU $20/vCPU-mo (usage), volume $0.15/GB | Hobby max volume 5 GB | **≈ $5.5–6** | ⚠️ 5 GB cap on Hobby; egress $0.05/GB; container platform → same exposure issue as Fly | https://railway.com/pricing |
| Render Starter (0.5 CPU / 512 MB) + persistent disk | $7.00 (+ $0 Hobby workspace) | $0.25/GB/mo (10 GB = $2.50) | **≈ $7.25–9.50** | ⚠️ highest per-GB disk; platform router → exposure issue as Fly | https://render.com/pricing |
| Cloudflare Containers (`lite`, Workers Paid) | $5 Workers Paid incl. 25 GiB-h mem, 375 vCPU-min, 200 GB-h disk; always-on lite ≈ +$1.7 | **ephemeral disk**: fresh disk after sleep/restart/rollout; snapshots immutable, 30-day TTL; R2 FUSE lacks full POSIX | ≈ $6.7 | ❌ **disqualified as primary**: no durable POSIX disk ⇒ memory/ledger would be lost or need a storage rewrite (P1+) | https://developers.cloudflare.com/containers/pricing/ · https://developers.cloudflare.com/containers/faq/ · https://developers.cloudflare.com/containers/platform-details/limits/ |

Shared, Cloudflare side (likely already partly in place for the pilot):

| Item | Price | Source |
|------|-------|--------|
| Workers Paid (if the pilot is not already on it) | $5/month min.; 10 M requests + 30 M CPU-ms included; subrequests from a Worker are not billed | https://developers.cloudflare.com/workers/platform/pricing/ |
| Cloudflare Tunnel (`cloudflared`) | no charge for the connector — stated by a third-party guide (https://tech-insider.org/cloudflare-tunnel-setup-2026-homelab/); Cloudflare's Tunnel docs list no price. **Verify on the Cloudflare Zero Trust plans page before relying on it** | https://developers.cloudflare.com/workers-vpc/configuration/tunnel/ |
| Workers VPC (Worker → private service via Tunnel) | free during open beta; standard Workers pricing applies | https://developers.cloudflare.com/workers-vpc/platform/pricing/ |
| Cloudflare Access service token (alternative path) | Zero Trust Free plan up to 50 users per the same third-party guide — **unverified on an official page** | https://www.cloudflare.com/plans/ |
| R2 backups | $0.015/GB-month, 10 GB-month free, no egress fees | https://developers.cloudflare.com/r2/pricing/ |

Estimated recommended total: **$6.00/month** (DO 1 GiB) + $0–1.20 backups + $0 Tunnel/VPC + $0 R2 (under 10 GB)
(+ $5 Workers Paid only if not already paid for the pilot). **Nothing has been purchased.**

## 3. Exposure without weakening the loopback guard

**A. Recommended — connector in the same network namespace (no code change).** `cloudflared` runs as a sidecar
sharing the service's network namespace (`network_mode: service:mesh-minogan` in `compose.proposal.yaml`) and makes
an **outbound** connection to Cloudflare. The origin is `http://127.0.0.1:8787`. The host publishes **no** inbound
port (cloud firewall: deny all inbound except SSH from the operator IP, or SSH via Tunnel too). The HEALTHCHECK also
probes loopback from inside the container.

**B. Same container, TLS terminator** (Caddy/nginx in the image listening publicly with TLS + client-cert or IP
allow-list, proxying to 127.0.0.1). Works on Fly/Railway/Render, but adds a public listener, certificate management
and a second process to the image. Not recommended for v0.

**C. Opt-in non-loopback bind — PROPOSAL, NOT IMPLEMENTED.** If a platform router (Fly/Render/Railway) must reach
the process directly, add `--allow-non-loopback` that is refused unless **both** the flag and an env acknowledgement
(`MESH_MINOGAN_PUBLIC_BIND_ACK=i-understand-tls-is-terminated-upstream`) are present, logs a startup warning, and
still requires Bearer auth. Requires operator approval and its own tests; the current guard stays as is.

## 4. Pilot (Cloudflare Workers) → Mesh

Preferred path — **Workers VPC binding over the Tunnel** (no public hostname at all):

```
Worker (pilot getScorer → mesh) ──VPC binding──► Cloudflare ══Tunnel (QUIC, outbound from VM)══► cloudflared ─► 127.0.0.1:8787
```

- Worker code: `env.MESH.fetch("http://mesh/v1/score", {method:"POST", headers:{Authorization:`Bearer ${env.MESH_TOKEN}`}, body})`;
  per Cloudflare docs the URL host is ignored and routing uses the VPC Service config (http, tunnel id, `127.0.0.1:8787`).
- **Auth layers**: (1) network — only Workers bound to the VPC Service reach the origin, the VM has no inbound port;
  (2) app — per-tenant Bearer (plaintext only in the Worker secret store via `wrangler secret put`; the VM holds sha256 only);
  (3) tenant — `org_id` must equal the token's tenant (403 otherwise). mTLS is not needed on this path (the Tunnel is
  mutually authenticated by Cloudflare); if a public hostname is ever used instead, put **Cloudflare Access with a
  service token** (`CF-Access-Client-Id/Secret` headers from the Worker) in front, plus the Bearer.
- **Beta caveat**: Workers VPC is in open beta (APIs may change). Fallback: public Tunnel hostname + Access service token.
- **Latency budget**: Mesh itself p95 ≈ 46 ms (local, 200 events, with ledger). Add Worker-PoP ↔ origin-region RTT
  (same continent typically tens of ms; cross-Atlantic ~80–100 ms). Place the VM in the region closest to the pilot's
  users/tenants; the pilot should use a 2 s client timeout (service deadline is 1.5 s) and **fall back to its built-in
  rules scorer** on timeout/5xx. Measure after deployment; no numbers here are measured on a real network.
- Pilot remains untouched by this proposal; wiring `getScorer()` to Mesh is a separate pilot change needing approval.

## 5. Recommendation

**DigitalOcean Basic Droplet 1 GiB (single VM) + Docker Compose (service + cloudflared sidecar) + Workers VPC
binding + nightly backup to R2.** ≈ **$6–7/month**.

Rationale: a plain VM satisfies every hard constraint by construction (local POSIX disk with flock/fsync, one process
= one writer, no platform router demanding a public bind); outbound-only Tunnel keeps the loopback guard and leaves
zero inbound attack surface; flat USD price, US and EU regions, built-in weekly/daily backups as a second layer.
Hetzner CX23 is the cheaper alternative if EU residency is preferred **and** stock is available. Fly.io is cheapest
on paper but would need cloudflared inside the container (or option 3C) and its single-volume caveat is the same
risk as a VM disk without the VM's simplicity. Cloudflare Containers is excluded until a storage redesign (ephemeral
disk).

## 6. Backup and restore (ledger + memory)

- Data is append-only (immutable CAS objects + append-only index + small head files). A naive live `cp -r` can
  capture heads and buckets at different instants → **do not copy live**.
- Nightly (low-traffic window): `docker compose stop mesh-minogan` (SIGINT; pilot falls back to rules for the few
  seconds) → `tar` of the volume → `docker compose start` → encrypt (age/restic) → upload to **R2** (private bucket,
  scoped API token, object lock / lifecycle 35 days). Alternative: a crash-consistent block snapshot (DO
  backups/snapshots) — equivalent to a kill -9 state, which the recovery protocol handles.
- **Restore drill (weekly)**: restore into a scratch dir and run `mesh minogan verify --root <dir> --replay`; alert
  if `ok` is false. Record the ledger head hashes per tenant in the backup manifest (first step toward the P1
  external anchoring).
- RPO ≤ 24 h (nightly) — tighten later with more frequent stops or a P1 `mesh minogan backup` that takes the locks.

## 7. Risks

| Risk | Mitigation |
|------|-----------|
| Single VM / single disk = SPOF (hardware, host maintenance) | nightly R2 backup + provider backups; pilot falls back to rules scorer; documented restore drill |
| Workers VPC is beta | fallback path: Tunnel public hostname + Access service token + Bearer |
| Token leakage (Worker secret) | per-tenant tokens, sha256-only on server, rotation = add new hash, deploy, remove old |
| Running >1 replica by mistake | `replicas: 1`, documented; P1: lockfile at root refusing a second process |
| Prices / availability change (e.g. Hetzner CX23 stock, Hetzner 2026 price rises) | re-check at order time; table dated |
| Image supply chain | pin `python:3.13-slim` and `cloudflared` by digest; build on the VM or a private registry (no public push) |
| Disk growth (stored inputs kept forever) | 25 GiB local is ample at pilot scale; alert at 70%; retention policy is P1 |
| Data residency (tenant metadata in US vs EU) | choose region with the operator; metadata only (no prompts/completions) |
| stdlib HTTP server under abuse | no public listener (Tunnel/VPC only); Cloudflare in front; rate limiting is P1 |

## 8. Requires operator approval (none done)

1. Choose provider/region and **create the account + payment method** (DigitalOcean recommended).
2. Create the VM (Basic 1 GiB), firewall (no inbound except operator SSH), enable provider backups (optional +20%).
3. Cloudflare: create the Tunnel, the Workers VPC Service (or Access app + service token), Workers Paid if needed.
4. Create R2 bucket + scoped API token for backups; choose encryption key custody.
5. Generate per-tenant tokens; put plaintext in Worker secrets; put sha256 in `/etc/mesh-minogan/tokens.json` on the VM.
6. Build the image on the VM (or approve a **private** registry); pin base image digests.
7. Pilot change: point `getScorer()` at Mesh with timeout + rules fallback (pilot is untouched so far).
8. Any change to the loopback guard (option 3C) — not proposed for v0.

## 9. What was verified locally (2026-10-18)

- **Docker is not installed on the build box → the image was NOT built.** Dockerfile is unbuilt; the README gives
  the exact build + smoke commands for a machine with Docker.
- Container-equivalent smoke instead: built the wheel (`uv build`), installed it into a fresh Python 3.13 venv
  (works fully offline from the local cache), ran the image's exact ENTRYPOINT (`mesh minogan serve --host 127.0.0.1
  --memory-root <data> --port 8787`) with a tokens file in the secret path layout, then: HEALTHCHECK command → OK;
  `smoke.py` → health 200, unauthenticated 401, authenticated 200 (score 45 = fixture fx_005 expected), ledger id
  `msl_…_1`; `mesh minogan verify --replay` → ok; socket listening on `127.0.0.1:8787` only; clean SIGINT stop;
  token absent from logs. Covered by `tests/test_minogan_deploy_cp0088.py` (Dockerfile/compose invariants + smoke).
