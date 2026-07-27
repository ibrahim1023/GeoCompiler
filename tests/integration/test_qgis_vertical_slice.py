from __future__ import annotations

import pytest

from geocompiler.qgis import QgisCompiler, QgisProjectContextAdapter, QgisWorkflowRunner
from geocompiler.workflow import (
    GeometryKind,
    ParameterKind,
    WorkflowInput,
    WorkflowIR,
    WorkflowParameter,
    WorkflowStep,
)

qgis_core = pytest.importorskip("qgis.core", reason="requires a QGIS Python runtime")

QgsApplication = qgis_core.QgsApplication
QgsFeature = qgis_core.QgsFeature
QgsGeometry = qgis_core.QgsGeometry
QgsProject = qgis_core.QgsProject
QgsVectorLayer = qgis_core.QgsVectorLayer


@pytest.fixture(scope="session", autouse=True)
def qgis_application() -> object:
    application = QgsApplication.instance() or QgsApplication([], False)
    if QgsApplication.instance() is None:
        application.initQgis()
    try:
        from qgis.analysis import QgsNativeAlgorithms

        registry = QgsApplication.processingRegistry()
        if registry.providerById("native") is None:
            registry.addProvider(QgsNativeAlgorithms())
    except ImportError:
        pass
    yield application
    QgsProject.instance().clear()


def test_project_context_and_buffer_runner_use_live_qgis_processing() -> None:
    project = QgsProject.instance()
    project.clear()
    layer = QgsVectorLayer("LineString?crs=EPSG:32640", "Roads", "memory")
    provider = layer.dataProvider()
    feature = QgsFeature(layer.fields())
    feature.setGeometry(QgsGeometry.fromWkt("LINESTRING (0 0, 100 0)"))
    assert provider.addFeatures([feature])
    assert layer.isValid()
    project.addMapLayer(layer)

    context = QgisProjectContextAdapter().inspect(project)
    assert len(context.layers) == 1
    assert context.layers[0].id == layer.id()
    assert context.layers[0].geometry_kind == "vector_line"
    assert context.layers[0].is_projected is True

    workflow = WorkflowIR(
        schema_version="1.0",
        id="buffer-roads",
        name="Buffer roads",
        inputs=[WorkflowInput(id="roads", title="Roads", kind=GeometryKind.LINE)],
        parameters=[
            WorkflowParameter(
                id="distance",
                title="Distance",
                kind=ParameterKind.DISTANCE,
                default=10,
                unit="m",
            )
        ],
        steps=[
            WorkflowStep(
                id="buffer_roads",
                operation="buffer",
                inputs={"INPUT": "roads"},
                parameters={"DISTANCE": "$distance"},
                outputs={"OUTPUT": "buffered_roads"},
            )
        ],
        outputs={"result": "buffered_roads"},
    )

    compiled = QgisCompiler().compile(workflow, context)
    result = QgisWorkflowRunner().execute(compiled, input_bindings={"roads": layer})

    output = result.outputs["result"]
    assert output.isValid()
    assert output.featureCount() == 1
