AI Engineering Harness for Healthcare Data Import

Overview

This project implements a lightweight AI-driven engineering harness that generates, builds, runs, and iteratively improves code to process healthcare data.

The harness executes a workflow defined in JSON using three step types:

* AI steps (prompting, code generation, analysis)
* Build steps (compilation)
* Run steps (execution)

The goal is to demonstrate an iterative pipeline that transforms legacy patient data into structured, FHIR-compatible output.

---

How to Run

Prerequisites:

* Docker and Docker Compose installed
* Internet access for AI model calls
* Optional: API key configured as environment variable

Initial Run:

From the project root (harness folder), run:

docker compose up

What happens:

* Two containers are built:

  * ai-harness (Python workflow orchestrator)
  * .net-runner (.NET 8 environment for build and run)

* Execution flow:

  * ai-harness container starts, executes the workflow, and exits
  * .net-runner container remains available for build/run operations

Re-running the workflow:

docker compose up --build harness

This will:

* rebuild the harness container if needed
* execute the workflow again
* create a new run under /workspace/runs

---

Workflow Configuration

The workflow is defined in:

/workspace/workflows/patient_import_v3.json

This file specifies:

* step sequence
* step types (AI, Build, Run)
* input/output mappings
* retry behavior
* maximum iterations

---

Workspace Structure

/workspace
  workflows/
    patient_import_v3.json (workflow definition)
  tasks/
    import_patients.md (task description)
    system_prompt_designer.md (prompt design system prompt)
    system_code_generator.md (code generation system prompt)
    system_analyzer.md (analyzer system prompt)
    analyze_build.md (analyzer user prompt)
  samples/
    patients.json (input dataset)
  output/
    patients.ndjson (final output)
  runs/ (run artifacts)
    run_001/


Codebase Description

The system is implemented as a generic workflow engine with pluggable step types.

Main components:

main.py

* Entry point
* Loads workflow
* Initializes shared context
* Controls iteration loop
* Handles retry vs success termination

executor.py

* Executes workflow steps sequentially
* Resolves inputs from shared context
* Dispatches execution by step type (AI, Build, Run)
* Stores outputs and decisions
* Stops execution early if retry is requested

ai.py

* Handles AI steps
* Combines system prompt, user prompt, and optional files
* Calls external AI model (Groq)
* Processes responses (JSON, code extraction)
* Produces:
  * generated artifacts
  * retry decision
  * improved prompt for next iteration

Build step handler

* Executes build command (e.g., dotnet build)
* Captures logs and structured result

Run step handler

* Executes generated program (dotnet run)
* Captures logs and output

---

Execution Model

The harness supports three step types:

* AI: generates and analyzes
* Build: compiles code
* Run: executes code

All steps share a common context that includes:

* current prompt
* generated code
* logs and results
* output files

This context persists across iterations.

Iteration flow:

1. Execute workflow steps sequentially
2. Analyzer (AI step) evaluates results
3. If decision = retry:
   * prompt is updated
   * workflow restarts from beginning
4. Stop when:
   * success is reached, or
   * max iterations is reached

---

Output

Final output is written to:

/workspace/output/patients.ndjson

* Format: NDJSON (one JSON object per line)
* Contains FHIR-compatible Patient resources
* No extra logs or text included

---

Notes

* The system is fully workflow-driven
* New pipelines can be created by modifying the workflow JSON
* All intermediate artifacts are stored under /workspace/runs
* Each run is isolated and reproducible
* Prompts evolve across iterations to improve results
