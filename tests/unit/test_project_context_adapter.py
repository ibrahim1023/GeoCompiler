from __future__ import annotations

import pytest

from geocompiler.qgis.context import QgisProjectContextAdapter


class FakeCrs:
    def __init__(self, auth_id: str, crs_type: str) -> None:
        self._auth_id = auth_id
        self._crs_type = crs_type

    def authid(self) -> str:
        return self._auth_id

    def type(self) -> str:
        return self._crs_type

    def isGeographic(self) -> bool:
        return self._crs_type == "geographic"


class FakeField:
    def __init__(self, name: str, type_name: str) -> None:
        self._name = name
        self._type_name = type_name

    def name(self) -> str:
        return self._name

    def typeName(self) -> str:
        return self._type_name


class FakeVectorLayer:
    def __init__(self, layer_id: str, selected_count: int = 0) -> None:
        self._layer_id = layer_id

    def id(self) -> str:
        return self._layer_id

    def name(self) -> str:
        return "Parcels"

    def type(self) -> str:
        return "vector"

    def geometryType(self) -> str:
        return "polygon"

    def crs(self) -> FakeCrs:
        return FakeCrs("EPSG:32640", "projected")

    def fields(self) -> list[FakeField]:
        return [FakeField("parcel_id", "String"), FakeField("area_m2", "Real")]

    def featureCount(self) -> int:
        return 12

    def selectedFeatureCount(self) -> int:
        return 2

    def source(self) -> str:
        raise AssertionError("data sources must not be inspected")

    def getFeatures(self) -> object:
        raise AssertionError("raw features must not be inspected")


class FakeRasterLayer:
    def id(self) -> str:
        return "dem"

    def name(self) -> str:
        return "Elevation"

    def type(self) -> str:
        return "raster"

    def crs(self) -> FakeCrs:
        return FakeCrs("EPSG:4326", "geographic")

    def featureCount(self) -> int:
        return 1


class FakePluginLayer:
    def type(self) -> str:
        return "plugin"


class FakeProject:
    def __init__(self, layers: dict[str, object]) -> None:
        self._layers = layers

    def mapLayers(self) -> dict[str, object]:
        return self._layers


def test_empty_project_produces_an_empty_context() -> None:
    context = QgisProjectContextAdapter().inspect(FakeProject({}))

    assert context.layers == ()
    assert context.selected_layer_ids == ()
    assert context.processing_history == ()


def test_vector_and_raster_metadata_is_safe_and_deterministic() -> None:
    context = QgisProjectContextAdapter().inspect(
        FakeProject(
            {
                "parcels": FakeVectorLayer("parcels"),
                "dem": FakeRasterLayer(),
                "plugin": FakePluginLayer(),
            }
        ),
        processing_history=[{"algorithm_id": "native:buffer", "title": "Buffer"}],
    )

    assert [layer.id for layer in context.layers] == ["dem", "parcels"]
    parcels = context.layers[1]
    assert parcels.geometry_kind == "vector_polygon"
    assert parcels.crs_auth_id == "EPSG:32640"
    assert parcels.is_projected is True
    assert [(field.name, field.type_name) for field in parcels.fields] == [
        ("parcel_id", "String"),
        ("area_m2", "Real"),
    ]
    assert context.selected_layer_ids == ("parcels",)
    assert context.processing_history[0].algorithm_id == "native:buffer"
    assert context.spatial_context().projected_references == {"dem": False, "parcels": True}
    assert "source" not in context.model_dump_json()
    assert "coordinates" not in context.model_dump_json()


def test_invalid_history_never_falls_back_to_raw_commands() -> None:
    with pytest.raises(ValueError, match="algorithm_id"):
        QgisProjectContextAdapter().inspect(
            FakeProject({}),
            processing_history=[{"command": "processing.run('native:buffer', {})"}],
        )


def test_active_project_requires_pyqgis_outside_qgis() -> None:
    with pytest.raises(RuntimeError, match="PyQGIS"):
        QgisProjectContextAdapter().inspect()
