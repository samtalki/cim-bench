"""PowerIO's native balanced model, including every registered CGMES profile.

The native component-count index is constructed during load. Query timings
measure access to that index, like other native typed-model adapters; they
are not SPARQL join timings. No dataset counts are hardcoded.
"""
from dataclasses import dataclass
from importlib.metadata import version
from pathlib import Path
import shutil
import tempfile
import time

import powerio
import psutil

from datasets import DATASETS
from parser_adapter import ParserAdapter


@dataclass
class LoadedPowerIO:
    module: powerio.PioModule
    counts: dict[str, int]
    fresh: object = None
    preparation: object = None


class PowerIOAdapter(ParserAdapter):
    @classmethod
    def get_version(cls):
        return version("powerio")

    @classmethod
    def get_dependencies(cls):
        return cls._get_package_dependencies("powerio")

    @classmethod
    def get_display_name(cls):
        return "PowerIO"

    @classmethod
    def get_color(cls):
        return "#176b87"

    @classmethod
    def get_tags(cls):
        return ["parser", "serializer", "query", "typed-model", "python", "rust"]

    def load(self, dataset_key):
        dataset = DATASETS[dataset_key]
        if "ZIP" in dataset:
            module = powerio.parse(dataset["ZIP"], format="cgmes")
        else:
            # PowerIO's Source confines acquisition to one directory and refuses
            # symlinks. Copy exactly the registered files, including COMMON.
            # This cost is deliberately inside the timed load.
            with tempfile.TemporaryDirectory(prefix="powerio-cim-") as directory:
                for key, path in dataset.items():
                    if key != "_metadata":
                        destination = Path(directory) / path.name
                        if destination.exists():
                            raise ValueError(f"duplicate profile filename: {path.name}")
                        shutil.copyfile(path, destination)
                module = powerio.parse(directory, format="cgmes")
        counts = module.value.component_counts()
        return LoadedPowerIO(module, counts)

    def get_load_metrics(self, loaded_obj, memory_mb):
        return {"memory_mb": f"{memory_mb:.1f}", **loaded_obj.counts,
                "diagnostics": len(loaded_obj.module.diagnostics),
                "query_semantics": "native component-count index built during load",
                "export_semantics": "fresh CGMES 3.0 EQ/TP/SSH/SV"}

    def get_lines_count(self, loaded_obj):
        return loaded_obj.counts["lines"]

    def get_generators_count(self, loaded_obj):
        return loaded_obj.counts["generators"]

    def get_loads_count(self, loaded_obj):
        return loaded_obj.counts["loads"]

    def get_substations_count(self, loaded_obj):
        return loaded_obj.counts["substations"]

    def prepare_export(self, loaded_obj):
        """Measured separately; retain original module for the replay test."""
        process = psutil.Process()
        before = process.memory_info().rss
        start = time.perf_counter()
        loaded_obj.fresh = loaded_obj.module.sever_source()
        loaded_obj.preparation = {
            "export_preparation_seconds": time.perf_counter() - start,
            "export_preparation_rss_bytes": process.memory_info().rss - before,
            "export_semantics": "fresh CGMES 3.0 EQ/TP/SSH/SV",
        }
        return loaded_obj.preparation

    def export(self, loaded_obj, output_path):
        if loaded_obj is None:  # template's capability probe
            return
        if loaded_obj.fresh is None:
            raise RuntimeError("prepare_export must run outside export timing")
        destination = Path(output_path).parent / "powerio-fresh"
        # Each timing includes replacing the previous output, as file writers do.
        if destination.exists():
            shutil.rmtree(destination)
        result = powerio.emit(loaded_obj.fresh, "cgmes", destination)
        if result.fidelity == "exact_same_format":
            raise AssertionError("fresh export unexpectedly replayed the input")
        return destination
