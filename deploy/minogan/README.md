# deploy/minogan — Mesh Minogan service image (CP-0088 P0.7, PROPOSAL ONLY)

Nothing here has been deployed or pushed. See `docs/planning/CP_0088_P0_7_DEPLOY_PROPOSAL.md` for hosting options,
costs, the Worker integration and what needs operator approval.

| File | Purpose |
|------|---------|
| `Dockerfile` | slim Python 3.13, multi-stage, non-root uid 10001, `/data` volume, tokens secret file, loopback bind, HEALTHCHECK |
| `Dockerfile.dockerignore` | build-context allowlist (`pyproject.toml`, `src/` only) — used by BuildKit with `-f` |
| `compose.proposal.yaml` | single-VM layout: service + `cloudflared` sidecar sharing the loopback namespace (not run) |
| `smoke.py` / `smoke_input.json` | loopback smoke: health, 401 without token, 200 + ledger id with token |

## Local build + smoke (operator machine with Docker; no registry, no network exposure)

```bash
docker build -f deploy/minogan/Dockerfile -t mesh-minogan:local .
mkdir -p /tmp/mm && TOK=$(python3 -c 'import secrets;print(secrets.token_urlsafe(32))')
H=$(printf '%s\n' "$TOK" | docker run --rm -i --entrypoint mesh mesh-minogan:local minogan hash-token)
python3 -c 'import json,sys;json.dump({"tenants":{sys.argv[1]:[sys.argv[2]]}},open("/tmp/mm/tokens.json","w"))' \
  "$(python3 -c 'import json;print(json.load(open("deploy/minogan/smoke_input.json"))["org_id"])')" "$H"
chmod 0444 /tmp/mm/tokens.json
docker run -d --name mm --read-only --tmpfs /tmp -v mm-data:/data \
  -v /tmp/mm/tokens.json:/run/secrets/minogan_tokens:ro -v "$PWD/deploy/minogan:/smoke:ro" mesh-minogan:local
docker exec -e MINOGAN_SMOKE_TOKEN="$TOK" mm python /smoke/smoke.py --input /smoke/smoke_input.json  # loopback in-container
docker inspect --format '{{.State.Health.Status}}' mm
docker exec mm mesh minogan verify --root /data --replay
docker rm -f mm && docker volume rm mm-data
```

Expected smoke output: `"ok": true`, `"score": 45` (fixture fx_005), `"unauth_status": 401`, a `ledger_id`.
