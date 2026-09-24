#!/usr/bin/env bash
# External quickstart helper for signed-off 0.16.3 single-node release (CP-0035).
#
# Default: --dry-run (print planned steps; exit 0 if artifacts exist).
# --execute: checksum SHA256SUMS + verify_bundle only (fail-closed).
#
# Bounds:
#   - Does NOT rebuild / reopen 0.16.3 packaging RC
#   - Does NOT invent plaintext / Vault-ACME / Raft / N>2 / GIA
#   - Fail-closed on missing artifacts or verify failure
#
# Usage:
#   bash scripts/quickstart_0.16.3.sh
#   bash scripts/quickstart_0.16.3.sh --dry-run
#   bash scripts/quickstart_0.16.3.sh --execute
#   bash scripts/quickstart_0.16.3.sh --release-dir PATH --execute

set -euo pipefail

MODE="dry-run"
RELEASE_DIR=""
REPO_ROOT=""

usage() {
  cat <<'USAGE'
Usage: quickstart_0.16.3.sh [--dry-run|--execute] [--release-dir DIR] [--repo-root DIR]

  --dry-run       Print planned steps; check artifact presence only (default)
  --execute       Run sha256sum -c and scripts/verify_bundle.py (fail-closed)
  --release-dir   Override dist/releases/0.16.3 path
  --repo-root     Override repository root (default: parent of scripts/)
  -h, --help      Show this help
USAGE
}

die() {
  echo "ERROR: $*" >&2
  exit 1
}

while [[ $# -gt 0 ]]; do
  case "$1" in
    --dry-run) MODE="dry-run"; shift ;;
    --execute) MODE="execute"; shift ;;
    --release-dir)
      [[ $# -ge 2 ]] || die "--release-dir requires a path"
      RELEASE_DIR="$2"
      shift 2
      ;;
    --repo-root)
      [[ $# -ge 2 ]] || die "--repo-root requires a path"
      REPO_ROOT="$2"
      shift 2
      ;;
    -h|--help) usage; exit 0 ;;
    *) die "unknown argument: $1 (see --help)" ;;
  esac
done

SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
if [[ -z "$REPO_ROOT" ]]; then
  REPO_ROOT="$(cd "${SCRIPT_DIR}/.." && pwd)"
fi
if [[ -z "$RELEASE_DIR" ]]; then
  RELEASE_DIR="${REPO_ROOT}/dist/releases/0.16.3"
fi

BUNDLE="${RELEASE_DIR}/neural-mesh-gia-single-node-0.16.3.tar.gz"
MANIFEST="${RELEASE_DIR}/neural-mesh-gia-single-node-0.16.3.manifest.json"
SUMS="${RELEASE_DIR}/SHA256SUMS"
SIGNOFF="${RELEASE_DIR}/SIGNOFF.json"
VERIFY_PY="${REPO_ROOT}/scripts/verify_bundle.py"

echo "QUICKSTART_0.16.3 mode=${MODE}"
echo "REPO_ROOT=${REPO_ROOT}"
echo "RELEASE_DIR=${RELEASE_DIR}"

require_file() {
  local p="$1"
  [[ -f "$p" ]] || die "missing required artifact: $p"
  echo "OK present: $p"
}

# Fail-closed presence checks (both modes)
require_file "$BUNDLE"
require_file "$MANIFEST"
require_file "$SUMS"
require_file "$SIGNOFF"

# Refuse plaintext / rebuild hints in this helper's contract
echo "BOUNDS: single-node 0.16.3 CLOSED; no rebuild; no plaintext; no Vault-ACME-req; no Raft/N>2/GIA"

plan() {
  echo "PLAN:"
  echo "  1) sha256sum -c SHA256SUMS  (cwd=${RELEASE_DIR})"
  echo "  2) python scripts/verify_bundle.py <bundle> --manifest <manifest> --expected-ver 0.16.3"
  echo "  3) (optional manual) rc_install_verify.py / clean_node_smoke.py — see docs/quickstart/QUICKSTART_0.16.3.md"
}

if [[ "$MODE" == "dry-run" ]]; then
  plan
  echo "DRY_RUN: PASS (no checksum or verify executed)"
  exit 0
fi

# execute mode
[[ -f "$VERIFY_PY" ]] || die "missing verify script: $VERIFY_PY"
command -v sha256sum >/dev/null 2>&1 || die "sha256sum not found on PATH"

plan
echo "EXECUTE: checksum"
(
  cd "$RELEASE_DIR"
  sha256sum -c SHA256SUMS
)

PYTHON=""
if [[ -x "${REPO_ROOT}/.venv/bin/python" ]]; then
  PYTHON="${REPO_ROOT}/.venv/bin/python"
elif command -v python3 >/dev/null 2>&1; then
  PYTHON="python3"
else
  die "no python interpreter found"
fi

echo "EXECUTE: verify_bundle via ${PYTHON}"
"${PYTHON}" "${VERIFY_PY}" \
  "${BUNDLE}" \
  --manifest "${MANIFEST}" \
  --expected-ver 0.16.3

echo "EXECUTE: PASS"
exit 0
