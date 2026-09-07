from __future__ import annotations

import json
from pathlib import Path
from typing import Any

import yaml
from packaging.requirements import Requirement

ROOT = Path(__file__).parents[1]
INTEGRATION = ROOT / "custom_components" / "duosida_local"


def _json(path: Path) -> dict[str, Any]:
    return json.loads(path.read_text(encoding="utf-8"))


def _assert_same_shape(reference: dict[str, Any], translated: dict[str, Any]) -> None:
    assert translated.keys() == reference.keys()
    for key, reference_value in reference.items():
        translated_value = translated[key]
        if isinstance(reference_value, dict):
            assert isinstance(translated_value, dict)
            _assert_same_shape(reference_value, translated_value)
        else:
            assert isinstance(translated_value, type(reference_value))


def test_translation_trees_and_icons_are_complete() -> None:
    strings = _json(INTEGRATION / "strings.json")
    english = _json(INTEGRATION / "translations" / "en.json")
    spanish = _json(INTEGRATION / "translations" / "es.json")
    _assert_same_shape(strings, english)
    _assert_same_shape(strings, spanish)

    icons = _json(INTEGRATION / "icons.json")["entity"]
    for platform, entities in strings["entity"].items():
        assert set(entities) <= set(icons[platform]) | {
            "current",
            "power",
            "session_energy",
            "station_temperature",
            "total_energy",
            "voltage",
        }


def test_release_metadata_is_aligned() -> None:
    manifest = _json(INTEGRATION / "manifest.json")
    hacs = _json(ROOT / "hacs.json")
    library_requirement = Requirement(manifest["requirements"][0])

    assert manifest["version"] == "0.1.0a1"
    assert library_requirement.name == "duosida-local"
    assert library_requirement.url == (
        "git+https://github.com/matiaskunin/duosida-local.git@v0.1.0a1"
    )
    assert 'version: "0.12.10"' in (ROOT / ".github" / "workflows" / "ci.yml").read_text(
        encoding="utf-8"
    )
    assert manifest["iot_class"] == "local_push"
    assert hacs["homeassistant"] == "2026.8.0"

    quality_scale = yaml.safe_load((INTEGRATION / "quality_scale.yaml").read_text())
    assert quality_scale["rules"]["test-coverage"] == "done"
    assert quality_scale["rules"]["brands"]["status"] == "todo"
