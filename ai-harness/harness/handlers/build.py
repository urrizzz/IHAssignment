import json
import os
import subprocess


def execute_build_step(step: dict) -> dict:
    """
    Execute a real build inside the dotnet-runner container.

    Expected workflow inputs:
    - project_dir: path visible inside the shared /workspace mount
      example: /workspace/runs/run_001/generated/GeneratedPipeline
    - command: build command to run inside that directory
      example: dotnet build

    This handler:
    1. runs the build inside the dotnet-runner container
    2. captures stdout/stderr
    3. writes console output to console_file
    4. writes structured result JSON to result_file
    """
    step_id = step.get("id")
    inputs = step.get("inputs", {})
    outputs = step.get("outputs", {})

    command = inputs.get("command")
    project_dir = inputs.get("project_dir")
    result_file = outputs.get("result_file")
    console_file = outputs.get("console_file")

    print(f"  Build handler invoked for step: {step_id}")

    if not result_file:
        raise ValueError(f"Build step '{step_id}' is missing outputs.result_file")

    if not project_dir:
        raise ValueError(f"Build step '{step_id}' is missing inputs.project_dir")

    if not command:
        raise ValueError(f"Build step '{step_id}' is missing inputs.command")
    
    # -------------------------------
    # MATERIALIZE PROJECT
    # -------------------------------

    parts = project_dir.strip("/").split("/")
    try:
        runs_index = parts.index("runs")
        run_id = parts[runs_index + 1]
    except (ValueError, IndexError):
        raise ValueError(f"Cannot extract run_id from project_dir: {project_dir}")

    generated_code_file = f"/workspace/runs/{run_id}/results/generated_code.cs"

    program_cs_path = os.path.join(project_dir, "Program.cs")
    csproj_path = os.path.join(project_dir, "GeneratedPipeline.csproj")

    os.makedirs(project_dir, exist_ok=True)

    # Write Program.cs
    if not os.path.exists(generated_code_file):
        raise ValueError(f"Generated code file not found: {generated_code_file}")

    with open(generated_code_file, "r", encoding="utf-8") as f:
        code = f.read()

    with open(program_cs_path, "w", encoding="utf-8") as f:
        f.write(code)

    # Write minimal .csproj
    if not os.path.exists(csproj_path):
        with open(csproj_path, "w", encoding="utf-8") as f:
            f.write("""<Project Sdk="Microsoft.NET.Sdk">
  <PropertyGroup>
    <OutputType>Exe</OutputType>
    <TargetFramework>net8.0</TargetFramework>
    <ImplicitUsings>enable</ImplicitUsings>
    <Nullable>enable</Nullable>
  </PropertyGroup>
</Project>
""")

    os.makedirs(os.path.dirname(result_file), exist_ok=True)

    if console_file:
        os.makedirs(os.path.dirname(console_file), exist_ok=True)

    # Run the build inside the existing dotnet-runner container.
    # The project_dir path must be valid inside that container.
    docker_command = [
        "docker",
        "exec",
        "dotnet-runner",
        "sh",
        "-lc",
        f"cd {project_dir} && {command}",
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
            "project_dir": project_dir,
            "command": command,
            "docker_command": docker_command,
            "errors": stderr.splitlines(),
            "warnings": [],
            "result_file": result_file,
            "console_file": console_file,
        }

    except Exception as ex:
        if console_file:
            with open(console_file, "w", encoding="utf-8") as f:
                f.write(f"Build handler exception:\n{str(ex)}\n")

        result = {
            "step_id": step_id,
            "status": "failed",
            "success": False,
            "exit_code": -1,
            "decision": "continue",
            "project_dir": project_dir,
            "command": command,
            "docker_command": docker_command,
            "errors": [str(ex)],
            "warnings": [],
            "result_file": result_file,
            "console_file": console_file,
        }

    with open(result_file, "w", encoding="utf-8") as f:
        json.dump(result, f, indent=2)

    return result