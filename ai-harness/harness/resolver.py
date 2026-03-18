import re


OUTPUT_REFERENCE_PATTERN = re.compile(r"^\$\{steps\.([^.]+)\.outputs\.([^.}]+)\}$")
RESULT_REFERENCE_PATTERN = re.compile(r"^\$\{steps\.([^.]+)\.result\.([^.}]+)\}$")
DECISION_REFERENCE_PATTERN = re.compile(r"^\$\{steps\.([^.]+)\.decision\}$")
STATUS_REFERENCE_PATTERN = re.compile(r"^\$\{steps\.([^.]+)\.status\}$")
SHARED_REFERENCE_PATTERN = re.compile(r"^\$\{shared\.([^.}]+)\}$")


def resolve_run_variables(value, context: dict):
    """
    Replace simple runtime variables such as ${run_id} inside strings.
    """
    if isinstance(value, str):
        return value.replace("${run_id}", context.get("run_id", ""))
    return value


def resolve_value(value, context: dict):
    """
    Resolve supported workflow references.

    Supported forms:
    - ${run_id}
    - ${steps.some_step.outputs.some_output}
    - ${steps.some_step.result.some_field}
    - ${steps.some_step.decision}
    - ${steps.some_step.status}
    - ${shared.some_key}
    """
    value = resolve_run_variables(value, context)

    if isinstance(value, str):
        match = OUTPUT_REFERENCE_PATTERN.match(value)
        if match:
            step_id, output_name = match.groups()
            return context["steps"][step_id]["outputs"][output_name]

        match = RESULT_REFERENCE_PATTERN.match(value)
        if match:
            step_id, field_name = match.groups()
            return context["steps"][step_id]["result"][field_name]

        match = DECISION_REFERENCE_PATTERN.match(value)
        if match:
            step_id = match.group(1)
            return context["steps"][step_id]["decision"]

        match = STATUS_REFERENCE_PATTERN.match(value)
        if match:
            step_id = match.group(1)
            return context["steps"][step_id]["status"]

        match = SHARED_REFERENCE_PATTERN.match(value)
        if match:
            shared_key = match.group(1)
            return context.get("shared", {}).get(shared_key)

        return value

    if isinstance(value, list):
        return [resolve_value(item, context) for item in value]

    if isinstance(value, dict):
        return {key: resolve_value(val, context) for key, val in value.items()}

    return value


def resolve_step(step: dict, context: dict) -> dict:
    """
    Resolve all supported variables inside a workflow step.
    """
    return resolve_value(step, context)