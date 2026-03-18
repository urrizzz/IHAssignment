import json
import os
from pathlib import Path

from groq import Groq


def _read_text_file(path: str) -> str:
    if not path:
        return ""

    file_path = Path(path)
    if not file_path.exists():
        raise FileNotFoundError(f"File not found: {path}")

    return file_path.read_text(encoding="utf-8")


def _read_source_files(source_files: list[str]) -> str:
    sections = []

    for file_path in source_files:
        content = _read_text_file(file_path)
        sections.append(
            f"=== SOURCE FILE: {file_path} ===\n{content.strip()}\n"
        )

    return "\n".join(sections).strip()


def _build_user_prompt(prompt_text: str, source_files: list[str]) -> str:
    source_bundle = _read_source_files(source_files) if source_files else ""

    if source_bundle:
        return (
            f"{prompt_text.strip()}\n\n"
            f"Additional source files:\n\n"
            f"{source_bundle}\n"
        )

    return prompt_text.strip()


def _extract_json_text(text: str) -> str:
    """
    Try to recover a JSON object from model output.

    This makes the handler more robust in case the model returns:
    - markdown fences
    - headings
    - extra prose before/after the JSON
    """
    text = text.strip()

    if text.startswith("```"):
        lines = text.splitlines()
        lines = lines[1:]

        if lines and lines[-1].strip() == "```":
            lines = lines[:-1]

        text = "\n".join(lines).strip()

        if text.lower().startswith("json"):
            text = text[4:].strip()

    start = text.find("{")
    end = text.rfind("}")
    if start != -1 and end != -1 and end > start:
        text = text[start:end + 1]

    return text


def _build_improved_prompt_path(result_file: str) -> str:
    """
    Create the next prompt version in the run prompts directory.

    Examples:
    - if only prompt_v1.txt exists -> create prompt_v2.txt
    - if prompt_v1.txt and prompt_v2.txt exist -> create prompt_v3.txt
    """
    result_path = Path(result_file)
    run_dir = result_path.parent.parent
    prompt_dir = run_dir / "prompts"
    prompt_dir.mkdir(parents=True, exist_ok=True)

    existing_versions = []

    for path in prompt_dir.glob("prompt_v*.txt"):
        stem = path.stem  # e.g. prompt_v2
        if stem.startswith("prompt_v"):
            version_text = stem.replace("prompt_v", "")
            if version_text.isdigit():
                existing_versions.append(int(version_text))

    next_version = max(existing_versions, default=1) + 1
    return str(prompt_dir / f"prompt_v{next_version}.txt")

def _strip_markdown_code_fence(text: str) -> str:
    text = text.strip()

    if not text.startswith("```"):
        return text

    lines = text.splitlines()

    if lines and lines[0].startswith("```"):
        lines = lines[1:]

    if lines and lines[-1].strip() == "```":
        lines = lines[:-1]

    return "\n".join(lines).strip()


def execute_ai_step(step: dict) -> dict:
    step_id = step.get("id")
    inputs = step.get("inputs", {})
    outputs = step.get("outputs", {})

    prompt_file = inputs.get("prompt_file")
    system_prompt_file = inputs.get("system_prompt_file")
    source_files = inputs.get("source_files", [])
    result_file = outputs.get("result_file")

    print(f"  AI handler invoked for step: {step_id}")
    print(f"    system_prompt_file: {system_prompt_file}")
    print(f"    prompt_file: {prompt_file}")
    print(f"    source_files: {source_files}")

    if not result_file:
        raise ValueError(f"AI step '{step_id}' is missing outputs.result_file")

    if not prompt_file:
        raise ValueError(f"AI step '{step_id}' is missing inputs.prompt_file")

    api_key = os.getenv("GROQ_API_KEY")
    model = step.get("model") or os.getenv("GROQ_MODEL", "llama-3.1-8b-instant")

    if not api_key:
        raise EnvironmentError("GROQ_API_KEY is not set")

    prompt_text = _read_text_file(prompt_file)
    system_prompt_text = _read_text_file(system_prompt_file) if system_prompt_file else ""
    user_prompt = _build_user_prompt(prompt_text, source_files)

    client = Groq(api_key=api_key)

    messages = []
    if system_prompt_text.strip():
        messages.append({"role": "system", "content": system_prompt_text.strip()})
    messages.append({"role": "user", "content": user_prompt})

    response = client.chat.completions.create(
        model=model,
        messages=messages,
        temperature=0.2,
    )

    ai_text = response.choices[0].message.content or ""
    ai_text = ai_text.strip()
    post = step.get("postprocess", {})
    saved_text = ai_text

    saved_text = ai_text
    if post.get("strip_code_fence"):
        saved_text = _strip_markdown_code_fence(ai_text)

    decision = "continue"
    improved_prompt_file = None
    parsed_json = None

    parsed_json = None

    if post.get("parse_json"):
        try:
            json_text = _extract_json_text(ai_text)
            parsed_json = json.loads(json_text)

            if post.get("save_pretty_json"):
                saved_text = json.dumps(parsed_json, indent=2)

            if parsed_json:
                status = str(parsed_json.get("status", "")).strip().lower()
                if status == "retry":
                    decision = "retry"

            if post.get("extract_improved_prompt"):
                improved_prompt_lines = parsed_json.get("improved_prompt_lines")

                if improved_prompt_lines and isinstance(improved_prompt_lines, list):
                    improved_prompt = "\n".join(str(line) for line in improved_prompt_lines).strip()

                    if improved_prompt:
                        improved_prompt_file = _build_improved_prompt_path(result_file)
                        Path(improved_prompt_file).write_text(
                            improved_prompt,
                            encoding="utf-8"
                        )
                        print(f"    Saved improved prompt to: {improved_prompt_file}")

        except Exception as ex:
            print(f"    Failed to parse JSON postprocess: {ex}")
    
    os.makedirs(os.path.dirname(result_file), exist_ok=True)
    Path(result_file).write_text(saved_text, encoding="utf-8")
    
    result = {
        "step_id": step_id,
        "status": "success",
        "decision": decision,
        "model": model,
        "system_prompt_file": system_prompt_file,
        "prompt_file": prompt_file,
        "source_files": source_files,
        "result_file": result_file,
        "response_text": saved_text,
        "improved_prompt_file": improved_prompt_file,
        "parsed_json": parsed_json,
    }

    return result