from __future__ import annotations

import json
import tomllib
from importlib.metadata import version
from pathlib import Path
from typing import Any

import yaml
from custom_components.duosida_local.sensor import SENSORS
from homeassistant.const import UnitOfTemperature
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
    manifest_requirement = Requirement(manifest["requirements"][0])
    project = tomllib.loads((ROOT / "pyproject.toml").read_text(encoding="utf-8"))
    dependency = next(
        requirement
        for requirement in project["dependency-groups"]["dev"]
        if requirement.startswith("duosida-local")
    )
    library_requirement = Requirement(dependency)

    assert manifest["version"] == "0.1.0a2"
    assert manifest_requirement.name == library_requirement.name == "duosida-local"
    assert (
        manifest_requirement.url
        == library_requirement.url
        == ("git+https://github.com/matiaskunin/duosida-local.git@v0.1.0a2")
    )
    assert version("duosida-local") == manifest["version"]
    assert "[tool.uv.sources]" not in (ROOT / "pyproject.toml").read_text(encoding="utf-8")
    assert 'version: "0.12.10"' in (ROOT / ".github" / "workflows" / "ci.yml").read_text(
        encoding="utf-8"
    )
    assert manifest["iot_class"] == "local_push"
    assert manifest["dependencies"] == ["network"]
    assert hacs["homeassistant"] == "2026.8.0"

    quality_scale = yaml.safe_load((INTEGRATION / "quality_scale.yaml").read_text())
    assert quality_scale["rules"]["test-coverage"] == "done"
    assert quality_scale["rules"]["brands"]["status"] == "todo"


def test_temperature_defaults_to_celsius_but_remains_user_overridable() -> None:
    temperature = next(sensor for sensor in SENSORS if sensor.key == "station_temperature")
    assert temperature.native_unit_of_measurement == UnitOfTemperature.CELSIUS
    assert temperature.suggested_unit_of_measurement == UnitOfTemperature.CELSIUS
