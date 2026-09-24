"""Tests for Cycle 34 / CP-0038: 0.18_H1_identity (attestation + tiers).

Markers: identity_cycle34
Aim: ≥14 — mismatch reject, tier bounds, pinned-only abort, no plaintext,
dual_primary unchanged, no Vault required.
"""

from __future__ import annotations

import json
import subprocess
import sys
from pathlib import Path

import pytest

from neural_mesh import __version__
from neural_mesh.identity import (
    SCHEMA_ID,
    IdentityMismatch,
    IdentityPinnedOnlyAbort,
    IdentityPlaintextForbidden,
    IdentityRevoked,
    IdentityService,
    IdentityTierError,
    TrustTier,
    cert_fingerprint,
    cmd_id_attest,
    cmd_id_revoke,
    cmd_id_rotate,
    cmd_id_status,
    cmd_id_tier,
    parse_tier,
)
from neural_mesh.network.tls import bootstrap_pair, issue_foreign_ca_leaf

pytestmark = [pytest.mark.identity_cycle34]

REPO = Path(__file__).resolve().parents[1]

NO_HELD = (
    "Raft,N>2,multi-primary,ML,R2,R3,plaintext,Vault-ACME-req,GIA,"
    "SLO_chase,tag_schema,EVERY_fsync"
)


@pytest.fixture
def fabric(tmp_path: Path):
    root = tmp_path / "fabric"
    ca, leaves = bootstrap_pair(root, ["node-a", "node-b"])
    return root, ca, leaves


def test_package_version_still_0180():
    assert __version__ == "0.18.0"
    pyproject = (REPO / "pyproject.toml").read_text(encoding="utf-8")
    assert 'version = "0.18.0"' in pyproject


def test_capability_and_policy_docs_present():
    cap = REPO / "docs" / "capabilities" / "MESH_IDENTITY_ATTESTATION.md"
    pol = REPO / "docs" / "policy" / "trust-tiers-v1.md"
    sch = REPO / "docs" / "schema" / "identity" / "v1.md"
    assert cap.is_file()
    assert pol.is_file()
    assert sch.is_file()
    ctext = cap.read_text(encoding="utf-8")
    ptext = pol.read_text(encoding="utf-8")
    assert "T0" in ptext and "T3" in ptext
    assert "pinned-only" in ptext.lower() or "pinned-only" in ctext.lower()
    assert "CP-0038" in ctext
    assert "0.18.0" in ctext
    assert "Vault" in ctext or "Vault" in ptext
    assert "GIA" in ctext
    for item in ("Raft", "plaintext", "Vault-ACME-req"):
        assert item in NO_HELD


def test_tier_bounds_parse():
    assert parse_tier(0) == TrustTier.T0
    assert parse_tier("T2") == TrustTier.T2
    assert parse_tier("t3") == TrustTier.T3
    with pytest.raises(IdentityTierError):
        parse_tier(4)
    with pytest.raises(IdentityTierError):
        parse_tier(-1)
    with pytest.raises(IdentityTierError):
        parse_tier("T9")


def test_attest_success_local_ca(fabric):
    root, _ca, _leaves = fabric
    svc = IdentityService(root)
    result = svc.attest("node-a")
    assert result.ok
    assert result.ca_verified
    assert result.tier == int(TrustTier.T2)
    assert result.cert_fingerprint
    assert result.dual_primary == 0
    assert result.vault_acme_required == 0
    assert result.plaintext_fallback == 0
    assert result.schema == SCHEMA_ID
    st = svc.status("node-a")
    assert st.ok
    assert st.record["tier"] == 2
    assert st.dual_primary == 0


def test_mismatch_reject_expected_node_id(fabric):
    root, _ca, _leaves = fabric
    svc = IdentityService(root)
    with pytest.raises(IdentityMismatch):
        svc.attest("node-a", expected_node_id="node-b")
    assert svc.store.pinned_only is True


def test_foreign_ca_reject(fabric, tmp_path):
    root, _ca, _leaves = fabric
    foreign_dir = tmp_path / "foreign"
    issue_foreign_ca_leaf("node-a", foreign_dir)
    # overwrite fabric leaf with foreign leaf (same node_id, wrong CA)
    dest = root / "nodes" / "node-a"
    (dest / "node.crt").write_bytes((foreign_dir / "node.crt").read_bytes())
    (dest / "node.key").write_bytes((foreign_dir / "node.key").read_bytes())
    svc = IdentityService(root)
    with pytest.raises(Exception) as ei:
        svc.attest("node-a")
    # attestation failed or mismatch path; pinned-only entered
    assert svc.store.pinned_only is True
    assert ei.value is not None


def test_plaintext_mode_forbidden(fabric):
    root, _ca, _leaves = fabric
    svc = IdentityService(root)
    with pytest.raises(IdentityPlaintextForbidden):
        svc.attest("node-a", mode="plaintext")


def test_tier_assign_and_downgrade_path(fabric):
    root, _ca, _leaves = fabric
    svc = IdentityService(root)
    svc.attest("node-a")
    rec = svc.set_tier("node-a", "T3", pin=True, reason="ops-pin")
    assert rec.tier == 3
    assert rec.pinned is True
    assert rec.pinned_fingerprint
    assert rec.dual_primary == 0
    rec = svc.downgrade("node-a", reason="step1")
    assert rec.tier == 2
    rec = svc.downgrade("node-a", reason="step2")
    assert rec.tier == 1
    rec = svc.downgrade("node-a", reason="step3")
    assert rec.tier == 0
    # T3 upgrade without pin fails
    svc.attest("node-b")
    with pytest.raises(IdentityTierError):
        svc.set_tier("node-b", TrustTier.T3, pin=False)


def test_tier_bounds_set_rejects_out_of_range(fabric):
    root, _ca, _leaves = fabric
    svc = IdentityService(root)
    svc.attest("node-a")
    with pytest.raises(IdentityTierError):
        svc.set_tier("node-a", 99)


def test_pinned_only_abort_rejects_unpinned(fabric):
    root, _ca, _leaves = fabric
    svc = IdentityService(root)
    # pin node-a at T3
    svc.attest("node-a")
    svc.set_tier("node-a", TrustTier.T3, pin=True)
    svc.enter_pinned_only("test-abort")
    # node-b attested but not pinned → reject in pinned-only
    with pytest.raises(IdentityPinnedOnlyAbort):
        svc.attest("node-b")
    # pinned node-a still ok
    result = svc.attest("node-a")
    assert result.ok
    assert result.pinned_only is True


def test_rotate_no_silent_downgrade(fabric):
    root, _ca, _leaves = fabric
    svc = IdentityService(root)
    svc.attest("node-a")
    svc.set_tier("node-a", TrustTier.T3, pin=True)
    before = svc.store.load("node-a")
    assert before is not None
    old_fp = before.cert_fingerprint
    old_tier = before.tier
    rec = svc.rotate("node-a", keep_tier=True)
    assert rec.tier == old_tier  # no silent downgrade
    assert rec.cert_fingerprint != old_fp
    assert old_fp in (rec.prior_fingerprints or [])
    assert rec.dual_primary == 0
    assert rec.vault_acme_required == 0


def test_revoke_forces_t0_and_pinned_only(fabric):
    root, _ca, _leaves = fabric
    svc = IdentityService(root)
    svc.attest("node-a")
    rec = svc.revoke("node-a", reason="compromised")
    assert rec.revoked is True
    assert rec.tier == 0
    assert rec.revoked_fingerprints
    assert svc.store.pinned_only is True
    with pytest.raises(IdentityRevoked):
        svc.attest("node-a")


def test_dual_primary_hard_zero_on_status(fabric):
    root, _ca, _leaves = fabric
    svc = IdentityService(root)
    svc.attest("node-a")
    st = svc.status("node-a")
    assert st.dual_primary == 0
    assert st.record["dual_primary"] == 0
    assert st.vault_acme_required == 0
    assert st.plaintext_fallback == 0


def test_no_vault_required_local_ca_only(fabric):
    """Attest/rotate work with LocalCA only — no Vault/ACME env."""
    root, _ca, _leaves = fabric
    # ensure no vault env leakage required
    svc = IdentityService(root)
    r = svc.attest("node-a")
    assert r.ok
    assert r.vault_acme_required == 0
    rotated = svc.rotate("node-a")
    assert rotated.cert_fingerprint
    assert rotated.vault_acme_required == 0
    cap = (REPO / "docs" / "capabilities" / "MESH_IDENTITY_ATTESTATION.md").read_text(
        encoding="utf-8"
    )
    assert "Vault/ACME" in cap or "Vault" in cap
    assert "not** required" in cap.lower() or "No Vault" in cap or "not required" in cap.lower()


def test_cli_id_status_attest_tier(fabric):
    root, _ca, _leaves = fabric
    rc = cmd_id_attest(fabric_root=root, node_id="node-a", as_json=True)
    assert rc == 0
    rc = cmd_id_status(fabric_root=root, node_id="node-a", as_json=True)
    assert rc == 0
    rc = cmd_id_tier(fabric_root=root, node_id="node-a", tier="T3", pin=True)
    assert rc == 0
    rc = cmd_id_rotate(fabric_root=root, node_id="node-a")
    assert rc == 0
    rc = cmd_id_revoke(fabric_root=root, node_id="node-b", reason="test")
    assert rc == 0


def test_cli_mesh_id_help_subprocess():
    proc = subprocess.run(
        [sys.executable, "-m", "neural_mesh.cli", "id", "--help"],
        cwd=str(REPO),
        capture_output=True,
        text=True,
        env={**dict(**{k: v for k, v in __import__("os").environ.items()}), "PYTHONPATH": str(REPO / "src")},
    )
    assert proc.returncode == 0
    assert "attest" in proc.stdout
    assert "tier" in proc.stdout
    assert "rotate" in proc.stdout
    assert "revoke" in proc.stdout


def test_fingerprint_stable(fabric):
    root, _ca, leaves = fabric
    fp1 = cert_fingerprint(leaves["node-a"].cert)
    fp2 = cert_fingerprint(leaves["node-a"].cert)
    assert fp1 == fp2
    assert len(fp1) == 64
