import json
import os
import subprocess


def execute_run_step(step: dict) -> dict:
    """
    Execute the generated .NET project inside the dotnet-runner container.

    Expected workflow inputs:
    - working_dir: path inside /workspace
      example: /workspace/runs/run_001/generated/GeneratedPipeline
    - command: run command
      example: dotnet run

    Outputs:
    - result_file: structured JSON result
    - console_file: stdout/stderr log
    """
    step_id = step.get("id")
    inputs = step.get("inputs", {})
    outputs = step.get("outputs", {})

    working_dir = inputs.get("working_dir")
    command = inputs.get("command")
    result_file = outputs.get("result_file")
    console_file = outputs.get("console_file")

    print(f"  Run handler invoked for step: {step_id}")
    print(f"    working_dir: {working_dir}")
    print(f"    command: {command}")

    if not result_file:
        raise ValueError(f"Run step '{step_id}' is missing outputs.result_file")

    if not working_dir:
        raise ValueError(f"Run step '{step_id}' is missing inputs.working_dir")

    if not command:
        raise ValueError(f"Run step '{step_id}' is missing inputs.command")

    os.makedirs(os.path.dirname(result_file), exist_ok=True)

    if console_file:
        os.makedirs(os.path.dirname(console_file), exist_ok=True)

    docker_command = [
        "docker",
        "exec",
        "dotnet-runner",
        "sh",
        "-lc",
        f"cd {working_dir} && {command}",
    ]

    try:
        process = subprocess.run(
            docker_command,
            capture_output=True,
            text=True,
        )

        stdout = process.stdout or ""
        stderr = process.stderr or ""
        exit_code = process.returncode
        success = exit_code == 0

        if console_file:
            with open(console_file, "w", encoding="utf-8") as f:
                f.write("DOCKER COMMAND:\n")
                f.write(" ".join(docker_command))
                f.write("\n\nSTDOUT:\n")
                f.write(stdout)
                f.write("\n\nSTDERR:\n")
                f.write(stderr)

        result = {
            "step_id": step_id,
            "status": "success" if success else "failed",
            "success": success,
            "exit_code": exit_code,
            "decision": "continue",
            "working_dir": working_dir,
            "command": command,
            "docker_command": docker_command,
            "result_file": result_file,
            "console_file": console_file,
        }

    except Exception as ex:
        if console_file:
            with open(console_file, "w", encoding="utf-8") as f:
                f.write(f"Run handler exception:\n{str(ex)}\n")

        result = {
            "step_id": step_id,
            "status": "failed",
            "success": False,
            "exit_code": -1,
            "decision": "continue",
            "working_dir": working_dir,
            "command": command,
            "docker_command": docker_command,
            "result_file": result_file,
            "console_file": console_file,
            "errors": [str(ex)],
        }

    with open(result_file, "w", encoding="utf-8") as f:
        json.dump(result, f, indent=2)

    return result