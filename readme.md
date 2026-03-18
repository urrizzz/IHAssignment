# AI Engineering Harness for Healthcare Data Import

## Overview

This project demonstrates a lightweight **AI engineering harness** designed to generate, validate, and iterate on code using AI agents.

Instead of building a fixed data pipeline, the system focuses on **orchestrating AI-driven workflows** that transform a task description into a working implementation.

The harness is workflow-driven, extensible, and designed for experimentation with different AI strategies.

---

## Goal

The objective is to build a system that:

- Accepts a structured task description (GitHub Issue)
- Uses AI to generate implementation code
- Compiles and executes the generated code
- Validates results
- Iterates automatically to improve output

This project focuses on **workflow orchestration and iteration**, not full production implementation.

---

## Key Idea

> The harness is a **workflow execution engine**, not a hardcoded pipeline.

- Behavior is defined externally (JSON workflows)
- No code changes are required to modify execution logic
- AI is used not only for generation, but also for validation and iteration

---

## Architecture

The system consists of:

### Components

- **AI Harness (Python)**
  - Orchestrates workflow execution
  - Manages steps, artifacts, and iteration

- **.NET Runner**
  - Builds and executes generated code

- **Shared Workspace**
  - `/workspace/tasks` — task definitions and prompts  
  - `/workspace/samples` — input data  
  - `/workspace/runs` — run artifacts  
  - `/workspace/output` — final results  

### Design Principle

> All components communicate through artifacts — ensuring loose coupling.

---

## Step Types

The system intentionally uses only three step types:

1. **AI Step**
   - Generates prompts, code, or analysis

2. **Build Step**
   - Compiles generated code

3. **Run Step**
   - Executes code and produces output

> Extensible by design — new step types can be introduced without modifying the core harness.

---

## Task Input (GitHub Issue)

The task input is treated as the **single source of truth**.

It defines:

- Requirements
- Edge cases
- Expected output

### Key Properties

- Used across multiple AI steps:
  - prompt generation
  - code generation
  - validation

- Persisted across iterations:
  - remains unchanged while prompts evolve

- Used for validation:
  - acts as ground truth for evaluating results

> This separates stable task intent from dynamic prompt evolution.

---

## Example Workflow: Patient Import

The implemented workflow (`patient_import_v3`) demonstrates an AI-driven pipeline for importing patient data.

### Steps

1. **Design Prompt (AI)**
   - Generates an optimized coding prompt based on task and sample data

2. **Generate Code (AI)**
   - Produces a .NET implementation of the pipeline

3. **Build Code (Build)**
   - Compiles generated code

4. **Run Code (Run)**
   - Executes the pipeline on sample input

5. **Analyze & Improve (AI)**
   - Evaluates build results and output
   - Generates improved prompt
   - Triggers retry if needed

---

## Workflow Definition

Workflows are defined declaratively in JSON.

Example (simplified):

```json
{
  "workflow_id": "patient-import-v3",
  "max_iterations": 3,
  "steps": [
    { "id": "design_prompt", "type": "ai" },
    { "id": "generate_code", "type": "ai" },
    { "id": "build_code", "type": "build" },
    { "id": "run_code", "type": "run" },
    { "id": "analyze_build", "type": "ai", "retry_on_failure": true }
  ]
}