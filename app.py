import os
import re
import uuid
import subprocess
from pathlib import Path
from flask import Flask, render_template, request, jsonify, send_file, abort

app = Flask(__name__)

MODELS_DIR = Path("models")
MODELS_DIR.mkdir(exist_ok=True)

SYSTEM_PROMPT = """You are an expert 3D modeling assistant specializing in OpenSCAD for 3D printing.

When the user describes a 3D object, generate complete, valid OpenSCAD code.

Rules:
- Use ONLY OpenSCAD code (not Python, Blender, or other tools)
- All measurements in millimeters
- Ensure manifold geometry (watertight, no self-intersections)
- Minimum wall thickness: 1.5mm for FDM printing
- Minimize overhangs; design for printability without supports when possible
- Declare parameters as variables at the top for easy customization
- Add brief inline comments on non-obvious sections

CRITICAL: Always wrap your OpenSCAD code in a ```openscad ... ``` block.
After the code block, write 2-3 sentences explaining your key design decisions."""


# ─── Provider Callers ────────────────────────────────────────────────────────

def call_anthropic(prompt, api_key, model):
    import anthropic
    client = anthropic.Anthropic(api_key=api_key)
    msg = client.messages.create(
        model=model,
        max_tokens=4096,
        system=SYSTEM_PROMPT,
        messages=[{"role": "user", "content": prompt}],
    )
    return msg.content[0].text


def call_openai_compat(prompt, api_key, model, base_url=None):
    from openai import OpenAI
    kwargs = {"api_key": api_key}
    if base_url:
        kwargs["base_url"] = base_url
    client = OpenAI(**kwargs)
    resp = client.chat.completions.create(
        model=model,
        messages=[
            {"role": "system", "content": SYSTEM_PROMPT},
            {"role": "user", "content": prompt},
        ],
        max_tokens=4096,
    )
    return resp.choices[0].message.content


def call_azure(prompt, api_key, endpoint, deployment, api_version):
    from openai import AzureOpenAI
    client = AzureOpenAI(
        api_key=api_key,
        azure_endpoint=endpoint,
        api_version=api_version,
    )
    resp = client.chat.completions.create(
        model=deployment,
        messages=[
            {"role": "system", "content": SYSTEM_PROMPT},
            {"role": "user", "content": prompt},
        ],
        max_tokens=4096,
    )
    return resp.choices[0].message.content


def call_local(prompt, base_url, model):
    import requests
    url = base_url.rstrip("/") + "/api/chat"
    resp = requests.post(
        url,
        json={
            "model": model,
            "messages": [
                {"role": "system", "content": SYSTEM_PROMPT},
                {"role": "user", "content": prompt},
            ],
            "stream": False,
        },
        timeout=180,
    )
    resp.raise_for_status()
    data = resp.json()
    return data.get("message", {}).get("content") or data.get("response", "")


# ─── Helpers ─────────────────────────────────────────────────────────────────

def extract_scad(text):
    """Pull OpenSCAD code from a markdown code fence."""
    for pat in [r"```openscad\n(.*?)```", r"```scad\n(.*?)```", r"```\n(.*?)```"]:
        m = re.search(pat, text, re.DOTALL)
        if m:
            return m.group(1).strip()
    return None


OPENSCAD_EXECUTABLES = [
    "openscad",
    r"C:\Program Files\OpenSCAD\openscad.exe",
    r"C:\Program Files (x86)\OpenSCAD\openscad.exe",
    "/usr/bin/openscad",
    "/usr/local/bin/openscad",
    "/Applications/OpenSCAD.app/Contents/MacOS/OpenSCAD",
]


def try_compile(scad_path: Path, stl_path: Path):
    for exe in OPENSCAD_EXECUTABLES:
        try:
            result = subprocess.run(
                [exe, "-o", str(stl_path), str(scad_path)],
                capture_output=True,
                text=True,
                timeout=90,
            )
            if result.returncode == 0 and stl_path.exists():
                return True, None
        except (FileNotFoundError, OSError, subprocess.TimeoutExpired):
            continue
    return False, "OpenSCAD not found — install it from openscad.org to enable STL export."


# ─── Routes ──────────────────────────────────────────────────────────────────

@app.route("/")
def index():
    return render_template("index.html")


@app.route("/generate", methods=["POST"])
def generate():
    data = request.get_json(force=True)
    prompt = (data.get("prompt") or "").strip()
    provider = data.get("provider", "anthropic")
    s = data.get("settings", {})

    if not prompt:
        return jsonify({"error": "Prompt is required"}), 400

    try:
        if provider == "anthropic":
            text = call_anthropic(prompt, s["api_key"], s.get("model", "claude-sonnet-4-6"))
        elif provider == "openai":
            text = call_openai_compat(prompt, s["api_key"], s.get("model", "gpt-4o"))
        elif provider == "openrouter":
            text = call_openai_compat(
                prompt,
                s["api_key"],
                s.get("model", "anthropic/claude-3.5-sonnet"),
                base_url="https://openrouter.ai/api/v1",
            )
        elif provider == "azure":
            text = call_azure(
                prompt,
                s["api_key"],
                s.get("endpoint", ""),
                s.get("deployment", "gpt-4o"),
                s.get("api_version", "2024-02-01"),
            )
        elif provider == "local":
            text = call_local(
                prompt,
                s.get("base_url", "http://localhost:11434"),
                s.get("model", "llama3.2"),
            )
        else:
            return jsonify({"error": "Unknown provider"}), 400
    except Exception as e:
        return jsonify({"error": str(e)}), 500

    scad_code = extract_scad(text)
    if not scad_code:
        return jsonify({"error": "No OpenSCAD code found in AI response", "raw": text}), 400

    explanation = re.sub(r"```(?:openscad|scad)?\n.*?```", "", text, flags=re.DOTALL).strip()

    model_id = uuid.uuid4().hex[:10]
    scad_path = MODELS_DIR / f"{model_id}.scad"
    stl_path = MODELS_DIR / f"{model_id}.stl"

    scad_path.write_text(scad_code, encoding="utf-8")
    compiled, compile_msg = try_compile(scad_path, stl_path)

    return jsonify(
        {
            "model_id": model_id,
            "scad_code": scad_code,
            "explanation": explanation,
            "compiled": compiled,
            "compile_message": compile_msg,
            "stl_available": stl_path.exists(),
        }
    )


@app.route("/models/<path:filename>")
def serve_model(filename):
    p = (MODELS_DIR / filename).resolve()
    if not str(p).startswith(str(MODELS_DIR.resolve())):
        abort(403)
    if p.suffix not in (".stl", ".scad"):
        abort(403)
    if not p.exists():
        abort(404)
    return send_file(p)


@app.route("/download/<model_id>/<file_type>")
def download(model_id, file_type):
    if file_type not in ("stl", "scad"):
        abort(400)
    safe_id = re.sub(r"[^a-f0-9]", "", model_id)[:10]
    path = MODELS_DIR / f"{safe_id}.{file_type}"
    if not path.exists():
        abort(404)
    return send_file(path, as_attachment=True, download_name=f"model_{safe_id}.{file_type}")


if __name__ == "__main__":
    print("🔷 3D Model Generator running at http://localhost:5000")
    app.run(debug=True, port=5000)
