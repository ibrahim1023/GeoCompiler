"""Approved QGIS algorithm definitions and deterministic compatibility checks."""

from __future__ import annotations

from collections.abc import Iterable
from enum import StrEnum

from pydantic import BaseModel, ConfigDict, Field

from geocompiler.workflow.errors import CompatibilityError, UnsupportedOperationError
from geocompiler.workflow.models import (
    GeometryKind,
    ParameterKind,
    WorkflowIR,
    WorkflowStep,
    value_matches_parameter_kind,
)


class OutputGeometryKind(StrEnum):
    POINT = GeometryKind.POINT
    LINE = GeometryKind.LINE
    POLYGON = GeometryKind.POLYGON
    RASTER = GeometryKind.RASTER
    SAME_AS_INPUT = "same_as_input"


class ParameterDefinition(BaseModel):
    """A deterministic requirement for one algorithm parameter."""

    model_config = ConfigDict(extra="forbid", frozen=True)

    kind: ParameterKind
    required: bool = True


class AlgorithmDefinition(BaseModel):
    """An allow-listed QGIS Processing operation."""

    model_config = ConfigDict(extra="forbid", frozen=True)

    operation: str = Field(min_length=1)
    qgis_algorithm_id: str = Field(min_length=1)
    input_kinds: dict[str, frozenset[GeometryKind]]
    parameters: dict[str, ParameterDefinition]
    output_kinds: dict[str, OutputGeometryKind]
    requires_projected_crs: bool = False


class SpatialContext(BaseModel):
    """CRS properties supplied by a deterministic project-context inspector."""

    model_config = ConfigDict(extra="forbid", frozen=True)

    projected_references: dict[str, bool] = Field(default_factory=dict)


class AlgorithmRegistry:
    """The only allowed bridge from semantic workflow operations to QGIS IDs."""

    def __init__(self, definitions: Iterable[AlgorithmDefinition]) -> None:
        definitions = tuple(definitions)
        self._definitions = {definition.operation: definition for definition in definitions}
        if len(self._definitions) != len(definitions):
            raise ValueError("algorithm definitions must have unique operations")

    @property
    def operations(self) -> frozenset[str]:
        return frozenset(self._definitions)

    def resolve(self, operation: str) -> AlgorithmDefinition:
        try:
            return self._definitions[operation]
        except KeyError as error:
            raise UnsupportedOperationError(f"unsupported operation: {operation}") from error

    def validate(self, workflow: WorkflowIR, context: SpatialContext) -> None:
        geometries = {input_.id: input_.kind for input_ in workflow.inputs}
        projected = dict(context.projected_references)

        for step in workflow.steps_in_dependency_order:
            definition = self.resolve(step.operation)
            self._validate_inputs(step, definition, geometries)
            self._validate_parameters(step, definition, workflow)
            self._validate_crs(step, definition, projected)
            self._record_outputs(step, definition, geometries, projected)

    def _validate_inputs(
        self,
        step: WorkflowStep,
        definition: AlgorithmDefinition,
        geometries: dict[str, GeometryKind],
    ) -> None:
        unknown_ports = set(step.inputs).difference(definition.input_kinds)
        if unknown_ports:
            raise CompatibilityError(
                f"step {step.id} unsupported input port: {sorted(unknown_ports)[0]}"
            )
        for port, accepted_kinds in definition.input_kinds.items():
            if port not in step.inputs:
                raise CompatibilityError(f"step {step.id} is missing required input: {port}")
            reference = step.inputs[port]
            actual_kind = geometries[reference]
            if actual_kind not in accepted_kinds:
                accepted = ", ".join(sorted(kind.value for kind in accepted_kinds))
                raise CompatibilityError(
                    f"step {step.id} input {port} expects one of {accepted}; "
                    f"got {actual_kind.value}"
                )

    def _validate_parameters(
        self,
        step: WorkflowStep,
        definition: AlgorithmDefinition,
        workflow: WorkflowIR,
    ) -> None:
        unknown_parameters = set(step.parameters).difference(definition.parameters)
        if unknown_parameters:
            raise CompatibilityError(
                f"step {step.id} unsupported parameter: {sorted(unknown_parameters)[0]}"
            )
        for name, parameter_definition in definition.parameters.items():
            if parameter_definition.required and name not in step.parameters:
                raise CompatibilityError(f"step {step.id} missing required parameter: {name}")
            if name not in step.parameters:
                continue
            value = step.parameters[name]
            if isinstance(value, str) and value.startswith("$"):
                parameter = workflow.parameters_by_id[value[1:]]
                if parameter.kind is not parameter_definition.kind:
                    raise CompatibilityError(
                        f"step {step.id} parameter {name} requires "
                        f"{parameter_definition.kind.value}; "
                        f"got {parameter.kind.value}"
                    )
            elif not value_matches_parameter_kind(value, parameter_definition.kind):
                raise CompatibilityError(
                    f"step {step.id} parameter {name} requires {parameter_definition.kind.value}"
                )

    def _validate_crs(
        self,
        step: WorkflowStep,
        definition: AlgorithmDefinition,
        projected: dict[str, bool],
    ) -> None:
        if not definition.requires_projected_crs:
            return
        for reference in step.inputs.values():
            if projected.get(reference) is not True:
                raise CompatibilityError(
                    f"step {step.id} operation {definition.operation} requires a projected CRS"
                )

    def _record_outputs(
        self,
        step: WorkflowStep,
        definition: AlgorithmDefinition,
        geometries: dict[str, GeometryKind],
        projected: dict[str, bool],
    ) -> None:
        inherited_reference = step.inputs.get("INPUT")
        for port, reference in step.outputs.items():
            if port not in definition.output_kinds:
                raise CompatibilityError(f"step {step.id} unsupported output port: {port}")
            output_kind = definition.output_kinds[port]
            if output_kind is OutputGeometryKind.SAME_AS_INPUT:
                if inherited_reference is None:
                    raise CompatibilityError(f"step {step.id} cannot infer output geometry")
                geometries[reference] = geometries[inherited_reference]
            else:
                geometries[reference] = GeometryKind(output_kind.value)
            if inherited_reference and inherited_reference in projected:
                projected[reference] = projected[inherited_reference]


def default_algorithm_registry() -> AlgorithmRegistry:
    """Return the initial vector-first GeoCompiler algorithm allow-list."""

    vector = frozenset({GeometryKind.POINT, GeometryKind.LINE, GeometryKind.POLYGON})
    polygon = frozenset({GeometryKind.POLYGON})
    same = {"OUTPUT": OutputGeometryKind.SAME_AS_INPUT}

    def definition(
        operation: str,
        qgis_algorithm_id: str,
        input_kinds: dict[str, frozenset[GeometryKind]],
        parameters: dict[str, ParameterDefinition],
        output_kinds: dict[str, OutputGeometryKind],
        requires_projected_crs: bool = False,
    ) -> AlgorithmDefinition:
        return AlgorithmDefinition(
            operation=operation,
            qgis_algorithm_id=qgis_algorithm_id,
            input_kinds=input_kinds,
            parameters=parameters,
            output_kinds=output_kinds,
            requires_projected_crs=requires_projected_crs,
        )

    definitions = [
        definition(
            "buffer",
            "native:buffer",
            {"INPUT": vector},
            {"DISTANCE": ParameterDefinition(kind=ParameterKind.DISTANCE)},
            {"OUTPUT": OutputGeometryKind.POLYGON},
            True,
        ),
        definition(
            "centroid",
            "native:centroids",
            {"INPUT": polygon},
            {},
            {"OUTPUT": OutputGeometryKind.POINT},
        ),
        definition("dissolve", "native:dissolve", {"INPUT": vector}, {}, same),
        definition(
            "intersection",
            "native:intersection",
            {"INPUT": vector, "OVERLAY": vector},
            {},
            same,
        ),
        definition(
            "union",
            "native:union",
            {"INPUT": polygon, "OVERLAY": polygon},
            {},
            {"OUTPUT": OutputGeometryKind.POLYGON},
        ),
        definition(
            "difference",
            "native:difference",
            {"INPUT": polygon, "OVERLAY": polygon},
            {},
            {"OUTPUT": OutputGeometryKind.POLYGON},
        ),
        definition(
            "clip",
            "native:clip",
            {"INPUT": vector, "OVERLAY": polygon},
            {},
            same,
        ),
        definition(
            "convex_hull",
            "native:convexhull",
            {"INPUT": vector},
            {},
            {"OUTPUT": OutputGeometryKind.POLYGON},
        ),
        definition(
            "join_by_location",
            "native:joinattributesbylocation",
            {"INPUT": vector, "JOIN": vector},
            {},
            same,
        ),
        definition(
            "extract_by_location",
            "native:extractbylocation",
            {"INPUT": vector, "INTERSECT": vector},
            {},
            same,
        ),
        definition(
            "nearest_feature",
            "native:joinbynearest",
            {"INPUT": vector, "INPUT_2": vector},
            {},
            same,
        ),
        definition(
            "distance_to_nearest_hub",
            "qgis:distancetonearesthublinetohub",
            {"INPUT": vector, "HUBS": vector},
            {},
            same,
            True,
        ),
        definition(
            "field_calculator",
            "native:fieldcalculator",
            {"INPUT": vector},
            {"FORMULA": ParameterDefinition(kind=ParameterKind.STRING)},
            same,
        ),
        definition(
            "extract_by_expression",
            "native:extractbyexpression",
            {"INPUT": vector},
            {"EXPRESSION": ParameterDefinition(kind=ParameterKind.STRING)},
            same,
        ),
        definition("aggregate", "native:aggregate", {"INPUT": vector}, {}, same),
        definition(
            "reproject",
            "native:reprojectlayer",
            {"INPUT": vector},
            {"TARGET_CRS": ParameterDefinition(kind=ParameterKind.STRING)},
            same,
        ),
        definition("fix_geometries", "native:fixgeometries", {"INPUT": vector}, {}, same),
        definition(
            "multipart_to_singleparts",
            "native:multiparttosingleparts",
            {"INPUT": vector},
            {},
            same,
        ),
    ]
    return AlgorithmRegistry(definitions)
