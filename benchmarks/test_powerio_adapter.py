"""Correctness checks are separate from timed benchmarks."""
import sys
from pathlib import Path
sys.path.insert(0, str(Path(__file__).parent.parent / "parsers"))
import powerio
from powerio_adapter import PowerIOAdapter
from datasets import DATASETS


def test_registered_profiles_and_fresh_export(tmp_path, monkeypatch):
    # Use a small redistributable synthetic CGMES source emitted from MATPOWER.
    case = b"""function mpc = case2
mpc.version = '2';
mpc.baseMVA = 100;
mpc.bus = [1 3 0 0 0 0 1 1 0 110 1 1.1 0.9; 2 1 1 0 0 0 1 1 0 110 1 1.1 0.9];
mpc.branch = [1 2 0.01 0.1 0 100 0 0 0 0 1 -360 360];
"""
    source = tmp_path / "input"
    powerio.emit(powerio.parse(case, format="matpower"), "cgmes", source)
    paths = sorted(source.glob("*.xml"))
    assert len(paths) == 4
    monkeypatch.setitem(DATASETS, "synthetic", {str(i): p for i,p in enumerate(paths)})
    adapter = PowerIOAdapter()
    loaded = adapter.load("synthetic")
    assert loaded.counts["lines"] == 1
    assert loaded.fresh is None
    preparation = adapter.prepare_export(loaded)
    assert preparation["export_preparation_seconds"] >= 0
    destination = adapter.export(loaded, tmp_path / "out.xml")
    assert powerio.parse(destination, format="cgmes").value.component_counts() == loaded.counts
    assert len(list(destination.glob("*.xml"))) == 4
    assert adapter.export(loaded, tmp_path / "out.xml") == destination
    assert powerio.emit(loaded.module, "cgmes").fidelity == "exact_same_format"


def test_missing_profile_is_not_silently_dropped(tmp_path, monkeypatch):
    import pytest
    monkeypatch.setitem(DATASETS, "missing", {"EQ": tmp_path / "missing.xml"})
    with pytest.raises(FileNotFoundError):
        PowerIOAdapter().load("missing")
