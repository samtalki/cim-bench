"""Retained-source replay only: excluded from fresh-export comparisons."""
import sys
import shutil
from pathlib import Path
import pytest
import powerio
sys.path.insert(0, str(Path(__file__).parent.parent / "parsers"))
from powerio_adapter import PowerIOAdapter


@pytest.mark.parametrize("dataset", ["svedala_igm_cgmes_3", "realgrid_cgmes_2_4"])
def test_powerio_replay(benchmark, tmp_path, dataset):
    loaded = PowerIOAdapter().load(dataset)
    destination = tmp_path / "replay"

    def replay():
        if destination.is_dir():
            shutil.rmtree(destination)
        elif destination.exists():
            destination.unlink()
        return powerio.emit(loaded.module, "cgmes", destination)

    result = benchmark(replay)
    assert result.fidelity == "exact_same_format"
    benchmark.extra_info.update(library="powerio", dataset=dataset,
                                operation="retained-source replay",
                                export_semantics="byte-exact input replay; no serialization")
