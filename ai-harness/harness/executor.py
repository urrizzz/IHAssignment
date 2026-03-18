import json
import os
from datetime import datetime, UTC

from handlers.ai import execute_ai_step
from handlers.build import execute_build_step
from handlers.run import execute_run_step
from resolver import resolve_step


def utc_now():
    return datetime.now(UTC).isoformat()


def write_step_metadata(step: dict, status: str, started_at: str, finished_at: str, context: dict, error: str | None = None) -> None:
    step_id = step.get("id")
    metadata_dir = f"/workspace/runs/{context['run_id']}/metadata"
    os.makedirs(metadata_dir, exist_ok=True)

    metadata = {
        "step_id": step_id,
        "type": step.get("type"),
        "status": status,
        "started_at": started_at,
        "finished_at": finished_at,
        "resolved_inputs": step.get("inputs", {}),
        "outputs": step.get("outputs", {})
    }

    if error:
        metadata["error"] = error

    with open(f"{metadata_dir}/{step_id}.json", "w") as f:
        json.dump(metadata, f, indent=2)


def execute_step(step: dict) -> dict:
    step_type = step.get("type")

    if step_type == "ai":
        return execute_ai_step(step)
    elif step_type == "build":
        return execute_build_step(step)
    elif step_type == "run":
        return execute_run_step(step)
    else:
        raise ValueError(f"Unsupported step type: {step_type}")
    
def should_retry(step: dict, step_result: dict) -> bool:
    retry_enabled = step.get("retry_on_failure", False)
    decision = step_result.get("decision")
    return retry_enabled and decision == "retry"


def execute_workflow(workflow: dict, context: dict) -> dict:
    """
    Execute all workflow steps using a shared context object.

    Important:
    - context is created in main.py
    - the same context is reused across iterations
    - this allows shared values like current_prompt_file
      to survive from one iteration to the next
    """
    steps = workflow.get("steps", [])

    print("Executing workflow...")

    for step in steps:
        resolved_step = resolve_step(step, context)

        step_id = resolved_step.get("id")
        step_type = resolved_step.get("type")
        print(f"- Step: {step_id} ({step_type})")

        retry_flag = resolved_step.get("retry_on_failure", False)
        print(f"    retry_on_failure: {retry_flag}")

        started_at = utc_now()

        try:
            step_result = execute_step(resolved_step)
            finished_at = utc_now()

            context["steps"][step_id] = {
                "outputs": resolved_step.get("outputs", {}),
                "result": step_result,
                "status": step_result.get("status"),
                "decision": step_result.get("decision")
            }

            # If this is the initial prompt design step and no shared prompt
            # has been set yet, use its result as the current prompt.
            if step_id == "design_prompt" and not context["shared"].get("current_prompt_file"):
                initial_prompt_file = step_result.get("result_file")
                if initial_prompt_file:
                    print(f"    initial prompt for workflow: {initial_prompt_file}")
                    context["shared"]["current_prompt_file"] = initial_prompt_file            

            # Capture improved prompt if AI produced one
            improved_prompt_file = step_result.get("improved_prompt_file")
            if improved_prompt_file:
                print(f"    updated prompt for next iteration: {improved_prompt_file}")
                context["shared"]["current_prompt_file"] = improved_prompt_file            

            if should_retry(resolved_step, step_result):
                print(f"    retry requested by step: {step_id}")
                return {
                    "status": "retry",
                    "retry_step_id": step_id
                }

            write_step_metadata(
                step=resolved_step,
                status="success",
                started_at=started_at,
                finished_at=finished_at,
                context=context
            )

        except Exception as ex:
            finished_at = utc_now()

            write_step_metadata(
                step=resolved_step,
                status="failed",
                started_at=started_at,
                finished_at=finished_at,
                context=context,
                error=str(ex)
            )

            raise

    return {
        "status": "success"
    }