"""Tests for multi-state data ingestion script and knowledge provider."""

from app.geo.state_datasets import (
    STATE_DATASETS,
    get_all_state_codes,
    get_state_priority_sectors,
    get_state_profile,
    ingest_state,
    is_sector_aligned_with_state,
)

MAJOR_STATES = [
    "MH",
    "KA",
    "TN",
    "UP",
    "GJ",
    "RJ",
    "PB",
    "HR",
    "WB",
    "MP",
    "AP",
    "TS",
    "KL",
    "BR",
    "OD",
    "AS",
    "JH",
    "CG",
    "UK",
    "HP",
]


def test_state_datasets_contain_all_major_states():
    for code in MAJOR_STATES:
        assert code in STATE_DATASETS, f"State {code} missing from STATE_DATASETS"
        data = STATE_DATASETS[code]
        assert len(data["districts"]) > 0
        assert len(data["sample_villages"]) > 0
        assert len(data["key_mandis"]) > 0
        assert len(data["priority_sectors"]) > 0


def test_get_all_state_codes():
    codes = get_all_state_codes()
    assert len(codes) >= 20
    for st in ["MH", "GJ", "TN", "UP", "PB", "KL", "BR"]:
        assert st in codes


def test_get_state_profile():
    mh = get_state_profile("MH")
    assert mh is not None
    assert mh["state_name"] == "Maharashtra"
    assert "Pune" in mh["districts"] or "Ahmednagar" in mh["districts"]


def test_priority_sector_matching():
    sectors_gj = get_state_priority_sectors("GJ")
    assert any("Dairy" in s for s in sectors_gj)
    assert is_sector_aligned_with_state("Dairy & Milk Processing", "GJ") is True
    assert is_sector_aligned_with_state("Attar Fragrances", "GJ") is False
    assert is_sector_aligned_with_state("Fragrances", "UP") is True


def test_ingest_state_dry_run_all_states():
    for st in MAJOR_STATES:
        stats = ingest_state(st, dry_run=True)
        assert stats["villages"] == len(STATE_DATASETS[st]["sample_villages"])
        assert stats["mandis"] == len(STATE_DATASETS[st]["key_mandis"])
