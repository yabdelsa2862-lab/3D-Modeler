"""
Forge 3D — Flask backend
3D generation uses trimesh + manifold3d (pure Python, no OpenSCAD needed).
"""
import os
import re
import sys
import uuid
import base64
import subprocess
from pathlib import Path
from flask import Flask, render_template, request, jsonify, send_file, abort

MODELS_DIR = Path("models")
MODELS_DIR.mkdir(exist_ok=True)

# ─────────────────────────────────────────────────────────────────────────────
# System prompt  (trimesh-based, no OpenSCAD)
# ─────────────────────────────────────────────────────────────────────────────
SYSTEM_PROMPT = r"""
You are an expert 3D modeling engineer. Generate Python code using the `trimesh` library
to create high-quality, detailed 3D models optimised for FDM printing.

━━━ LIBRARY REFERENCE ━━━
import trimesh, numpy as np, math

# ── Primitives (ALL centered at origin by default!) ──
box  = trimesh.creation.box(extents=[width, depth, height])
cyl  = trimesh.creation.cylinder(radius=r, height=h, sections=64)
sph  = trimesh.creation.sphere(radius=r, subdivisions=3)
ann  = trimesh.creation.annulus(r_min=inner_r, r_max=outer_r, height=h)
cone = trimesh.creation.cone(radius=r, height=h, sections=64)

# ── Move / rotate (modify in-place) ──
mesh.apply_translation([x, y, z])            # shift centre to (x,y,z)
tf = trimesh.transformations.rotation_matrix(
        math.radians(deg), [ax, ay, az], pivot=[px, py, pz])
mesh.apply_transform(tf)

# ── Boolean CSG ──
result = trimesh.boolean.union([a, b, c])
result = trimesh.boolean.difference(main, [cutter1, cutter2])
result = trimesh.boolean.intersection([a, b])

# ── After every boolean op: stabilise ──
result = trimesh.Trimesh(vertices=result.vertices, faces=result.faces, process=True)

━━━ CRITICAL POSITIONING RULE ━━━
A box with height=10 has its CENTER at z=0, so its BOTTOM is at z=-5.
To sit on the print-bed (z=0):  apply_translation([0, 0, h/2])
Always put the model's lowest point at z=0.

━━━ QUALITY RULES ━━━
• sections=64 for all cylinders/cones for smooth curves
• minimum wall thickness 2 mm
• no overhangs > 45° without a support feature
• make it look like a real product — add fillets-by-chamfer, cable slots,
  mounting holes, realistic proportions
• Only import: trimesh, numpy as np, math
• Store final mesh in variable `model`

━━━ COMPLETE EXAMPLE — phone stand with cable slot ━━━
```python
import trimesh, numpy as np, math

W, D, TH = 88, 110, 5      # base width, depth, thickness
WALL      = 3               # wall mm
TILT      = 20              # back tilt degrees

# ── Base plate ──
base = trimesh.creation.box(extents=[W, D, TH])
base.apply_translation([0, 0, TH / 2])

# ── Corner chamfers on base (subtract four diagonal rods) ──
chamfer_r = 8
for sx, sy in [(-1,-1),(1,-1),(1,1),(-1,1)]:
    rod = trimesh.creation.cylinder(radius=chamfer_r, height=TH+2)
    rod.apply_translation([sx*(W/2), sy*(D/2), TH/2])
    base = trimesh.boolean.difference(base, [rod])
    base = trimesh.Trimesh(vertices=base.vertices, faces=base.faces, process=True)

# ── Back support ──
su_h = 95
support = trimesh.creation.box(extents=[W, WALL, su_h])
support.apply_translation([0, D/2 - WALL/2, su_h / 2])
pivot = [0, D/2 - WALL/2, 0]
support.apply_transform(
    trimesh.transformations.rotation_matrix(math.radians(TILT), [1,0,0], pivot))

# ── Phone ledge ──
ledge = trimesh.creation.box(extents=[W, 20, WALL])
ledge.apply_translation([0, 10, TH + WALL/2])

# ── Cable slot in ledge ──
slot = trimesh.creation.box(extents=[22, 22, WALL + 2])
slot.apply_translation([0, 10, TH + WALL/2])
ledge = trimesh.boolean.difference(ledge, [slot])
ledge = trimesh.Trimesh(vertices=ledge.vertices, faces=ledge.faces, process=True)

# ── Rubber-pad recesses (four cylinders subtracted from base underside) ──
for rx, ry in [(-W/2+8, -D/2+8), (W/2-8, -D/2+8),
               (-W/2+8,  D/2-8), (W/2-8,  D/2-8)]:
    pad = trimesh.creation.cylinder(radius=5, height=1.5, sections=32)
    pad.apply_translation([rx, ry, 0.75])
    base = trimesh.boolean.difference(base, [pad])
    base = trimesh.Trimesh(vertices=base.vertices, faces=base.faces, process=True)

model = trimesh.boolean.union([base, support, ledge])
model = trimesh.Trimesh(vertices=model.vertices, faces=model.faces, process=True)
```

Now generate similarly detailed, production-quality Python+trimesh code for the user's request.
Include all functional features, realistic proportions, and proper print-bed orientation.
Wrap the code in a ```python ... ``` fence. After the fence, add a 2-sentence explanation.
""".strip()


# ─────────────────────────────────────────────────────────────────────────────
# AI provider callers
# ─────────────────────────────────────────────────────────────────────────────

def call_anthropic(prompt, api_key, model):
    import anthropic
    client = anthropic.Anthropic(api_key=api_key)
    msg = client.messages.create(
        model=model, max_tokens=4096,
        system=SYSTEM_PROMPT,
        messages=[{"role": "user", "content": prompt}],
    )
    return msg.content[0].text


def call_openai_compat(prompt, api_key, model, base_url=None):
    from openai import OpenAI
    kw = {"api_key": api_key}
    if base_url:
        kw["base_url"] = base_url
    client = OpenAI(**kw)
    r = client.chat.completions.create(
        model=model,
        messages=[{"role": "system", "content": SYSTEM_PROMPT},
                  {"role": "user", "content": prompt}],
        max_tokens=4096,
    )
    return r.choices[0].message.content


def call_azure(prompt, api_key, endpoint, deployment, api_version):
    from openai import AzureOpenAI
    client = AzureOpenAI(api_key=api_key, azure_endpoint=endpoint, api_version=api_version)
    r = client.chat.completions.create(
        model=deployment,
        messages=[{"role": "system", "content": SYSTEM_PROMPT},
                  {"role": "user", "content": prompt}],
        max_tokens=4096,
    )
    return r.choices[0].message.content


def call_local(prompt, base_url, model):
    import requests
    r = requests.post(
        base_url.rstrip("/") + "/api/chat",
        json={"model": model, "stream": False,
              "messages": [{"role": "system", "content": SYSTEM_PROMPT},
                           {"role": "user", "content": prompt}]},
        timeout=180,
    )
    r.raise_for_status()
    d = r.json()
    return d.get("message", {}).get("content") or d.get("response", "")


# ─────────────────────────────────────────────────────────────────────────────
# Code extraction + execution
# ─────────────────────────────────────────────────────────────────────────────

def extract_python(text: str) -> str | None:
    """Pull Python code from the first ``` fence in the response."""
    for pat in [r"```python\n(.*?)```", r"```py\n(.*?)```", r"```\n(.*?)```"]:
        m = re.search(pat, text, re.DOTALL)
        if m:
            return m.group(1).strip()
    return None


_RUNNER_TMPL = r"""
import sys, math
import trimesh
import numpy as np
try:
    from shapely.geometry import Polygon, Point
except ImportError:
    pass

# ── user code ──────────────────────────────────────────
{code}
# ── end user code ──────────────────────────────────────

import traceback
try:
    if isinstance(model, list):
        model = trimesh.boolean.union(model)
    if isinstance(model, trimesh.Scene):
        model = model.dump(concatenate=True)
    result = trimesh.Trimesh(vertices=model.vertices, faces=model.faces, process=True)
    trimesh.repair.fix_winding(result)
    trimesh.repair.fix_normals(result, multibody=True)
    result.export(r"{stl_path}")
    print("OK:" + str(len(result.faces)))
except Exception as e:
    traceback.print_exc()
    sys.exit(1)
"""


def run_trimesh_code(code: str, stl_path: Path) -> tuple[bool, str]:
    """Execute AI-generated trimesh code in a subprocess; save STL."""
    runner = _RUNNER_TMPL.format(
        code=code,
        stl_path=str(stl_path).replace("\\", "\\\\"),
    )
    try:
        result = subprocess.run(
            [sys.executable, "-c", runner],
            capture_output=True, text=True, timeout=60,
        )
        if (result.returncode == 0
                and stl_path.exists()
                and stl_path.stat().st_size > 300):
            return True, None

        # Extract a clean error message from stderr
        err = (result.stderr or result.stdout or "Unknown error").strip()
        lines = [l for l in err.splitlines()
                 if l and not l.startswith("  File") and "site-packages" not in l]
        return False, "\n".join(lines[-4:]) or err

    except subprocess.TimeoutExpired:
        return False, "Model generation timed out (60 s)"
    except Exception as e:
        return False, str(e)


def stl_to_b64(stl_path: Path) -> str | None:
    """Read STL file and return base-64 string for inline delivery."""
    try:
        return base64.b64encode(stl_path.read_bytes()).decode()
    except Exception:
        return None


# ─────────────────────────────────────────────────────────────────────────────
# Flask app
# ─────────────────────────────────────────────────────────────────────────────

def create_app():
    app = Flask(__name__)

    @app.route("/")
    def index():
        return render_template("app.html")

    @app.route("/generate", methods=["POST"])
    def generate():
        data = request.get_json(force=True)
        prompt = (data.get("prompt") or "").strip()
        provider = data.get("provider", "anthropic")
        s = data.get("settings", {})

        if not prompt:
            return jsonify({"error": "Prompt is required"}), 400

        # ── 1. Call AI ──────────────────────────────────────────
        try:
            if provider == "anthropic":
                text = call_anthropic(prompt, s["api_key"], s.get("model", "claude-sonnet-4-6"))
            elif provider == "openai":
                text = call_openai_compat(prompt, s["api_key"], s.get("model", "gpt-4o"))
            elif provider == "openrouter":
                text = call_openai_compat(
                    prompt, s["api_key"],
                    s.get("model", "anthropic/claude-3.5-sonnet"),
                    base_url="https://openrouter.ai/api/v1")
            elif provider == "azure":
                text = call_azure(
                    prompt, s["api_key"],
                    s.get("endpoint", ""), s.get("deployment", "gpt-4o"),
                    s.get("api_version", "2024-02-01"))
            elif provider == "local":
                text = call_local(
                    prompt,
                    s.get("base_url", "http://localhost:11434"),
                    s.get("model", "llama3.2"))
            else:
                return jsonify({"error": "Unknown provider"}), 400
        except Exception as e:
            return jsonify({"error": str(e)}), 500

        # ── 2. Extract Python code ──────────────────────────────
        code = extract_python(text)
        if not code:
            return jsonify({"error": "No Python code found in AI response", "raw": text}), 400

        explanation = re.sub(r"```(?:python|py)?\n.*?```", "", text, flags=re.DOTALL).strip()

        # ── 3. Run trimesh ──────────────────────────────────────
        model_id = uuid.uuid4().hex[:10]
        stl_path = MODELS_DIR / f"{model_id}.stl"
        py_path  = MODELS_DIR / f"{model_id}.py"
        py_path.write_text(code, encoding="utf-8")

        ok, err_msg = run_trimesh_code(code, stl_path)

        # ── 4. Encode STL as base-64 for inline delivery ────────
        stl_b64 = stl_to_b64(stl_path) if ok else None

        return jsonify({
            "model_id":    model_id,
            "code":        code,
            "explanation": explanation,
            "ok":          ok,
            "error_msg":   err_msg,
            "stl_b64":     stl_b64,                    # inline STL — no second request
            "faces":       _count_faces(stl_path) if ok else 0,
        })

    @app.route("/download/<model_id>/<ftype>")
    def download(model_id, ftype):
        if ftype not in ("stl", "py"):
            abort(400)
        safe = re.sub(r"[^a-f0-9]", "", model_id)[:10]
        ext  = "stl" if ftype == "stl" else "py"
        p    = MODELS_DIR / f"{safe}.{ext}"
        if not p.exists():
            abort(404)
        dl_name = f"forge3d_{safe}.{ext}"
        return send_file(p, as_attachment=True, download_name=dl_name)

    return app


def _count_faces(stl_path: Path) -> int:
    try:
        data = stl_path.read_bytes()
        if data[:5] == b"solid":          # ASCII STL
            return data.count(b"facet normal")
        return int.from_bytes(data[80:84], "little")  # binary STL
    except Exception:
        return 0
