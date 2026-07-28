"""Run the Phase 2 native QGIS project-context and Processing smoke test."""

from __future__ import annotations

import os

from qgis.analysis import QgsNativeAlgorithms
from qgis.core import QgsApplication, QgsFeature, QgsGeometry, QgsProject, QgsVectorLayer

from geocompiler.qgis import (  # noqa: E402
    QgisCompiler,
    QgisProjectContextAdapter,
    QgisWorkflowRunner,
)
from geocompiler.workflow import (  # noqa: E402
    GeometryKind,
    ParameterKind,
    WorkflowInput,
    WorkflowIR,
    WorkflowParameter,
    WorkflowStep,
)


def main() -> None:
    prefix_path = os.environ.get("QGIS_PREFIX_PATH")
    if prefix_path:
        QgsApplication.setPrefixPath(prefix_path, True)
    application = QgsApplication([], False)
    application.initQgis()
    project = QgsProject.instance()
    try:
        registry = QgsApplication.processingRegistry()
        if registry.providerById("native") is None:
            registry.addProvider(QgsNativeAlgorithms())

        layer = QgsVectorLayer("LineString?crs=EPSG:32640", "Roads", "memory")
        feature = QgsFeature(layer.fields())
        feature.setGeometry(QgsGeometry.fromWkt("LINESTRING (0 0, 100 0)"))
        assert layer.dataProvider().addFeatures([feature])
        assert layer.isValid()
        project.addMapLayer(layer)

        context = QgisProjectContextAdapter().inspect(project)
        assert len(context.layers) == 1
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

        compiled = QgisCompiler().compile(
            workflow,
            context,
            input_layer_ids={"roads": layer.id()},
        )
        output = (
            QgisWorkflowRunner()
            .execute(
                compiled,
                input_bindings={"roads": layer},
            )
            .outputs["result"]
        )
        assert output.isValid()
        assert output.featureCount() == 1
        print(f"QGIS {QgsApplication.platform()}: native:buffer smoke test passed")
    finally:
        project.clear()
        application.exitQgis()


if __name__ == "__main__":
    main()
