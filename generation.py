"""
AI provider calls + trimesh 3D generation.
No web server — pure Python, called directly from the Qt app.
"""
import os, re, sys, uuid, subprocess
from pathlib import Path

MODELS_DIR = Path("models")
MODELS_DIR.mkdir(exist_ok=True)

# ── System prompt ────────────────────────────────────────────────────────────
SYSTEM_PROMPT = r"""
You are an expert mechanical/product design engineer who generates Python + trimesh
code to create realistic, highly-detailed 3D models optimised for FDM printing.

━━━ UNDERSTANDING USER REQUESTS ━━━
Users often write short, casual descriptions like:
  "a mug", "phone mount for bike", "box with a lid", "stand for my monitor"
You MUST interpret these generously and create the most sensible, realistic version
of the object. Never refuse or ask for clarification — always produce a complete model.

How to interpret common shorthand:
  "for bike" / "bike mount"  → handlebar clamp + arm + cradle
  "holder"                   → something that grips/holds the named object
  "stand"                    → stable base + support arm or upright
  "box" / "case"             → enclosure with walls and a removable or hinged lid
  "clip"                     → snap-fit attachment mechanism
  "bracket"                  → L-shaped or U-shaped mounting plate with bolt holes
  "hook"                     → curved appendage for hanging
If size is unspecified, use typical real-world dimensions (e.g. phone ~76x160 mm,
mug ~80 mm dia x 95 mm tall, handlebar ~35 mm OD, M3 bolt hole radius 1.65 mm).

━━━ TRIMESH CHEAT SHEET ━━━
import trimesh, numpy as np, math

# Primitives — ALL centred at origin by default!
box  = trimesh.creation.box(extents=[W, D, H])
cyl  = trimesh.creation.cylinder(radius=r, height=h, sections=64)
sph  = trimesh.creation.sphere(radius=r, subdivisions=3)
ann  = trimesh.creation.annulus(r_min=r1, r_max=r2, height=h)   # hollow cylinder / tube
cone = trimesh.creation.cone(radius=r, height=h, sections=64)

# Move (in-place)
mesh.apply_translation([x, y, z])

# Rotate around an axis through a pivot point
tf = trimesh.transformations.rotation_matrix(math.radians(deg), [ax,ay,az], [px,py,pz])
mesh.apply_transform(tf)

# Boolean CSG — ALWAYS pass a list, never two separate arguments:
u = trimesh.boolean.union([a, b, c])
d = trimesh.boolean.difference([main, cutter])        # subtract cutter from main
d = trimesh.boolean.difference([main, cut1, cut2])    # subtract multiple cutters
i = trimesh.boolean.intersection([a, b])

# After EVERY boolean — stabilise with process=False:
result = trimesh.Trimesh(vertices=np.array(result.vertices),
                         faces=np.array(result.faces), process=False)

━━━ POSITIONING RULE ━━━
box(H=10) has centre at z=0, bottom at z=-5.
To rest on the print bed: apply_translation([0, 0, H/2])
The final `model` must have its lowest point at z=0.

━━━ QUALITY & DESIGN RULES ━━━
• THINK first: what are the real mechanical parts of this object?
  Break it into named parts (clamp, arm, cradle, ledge, clip, rib…)
  then build each as a distinct trimesh primitive or boolean result.
• sections=64 for visible cylinders; sections=32 for small/hidden ones
• Minimum wall / rib thickness: 2 mm
• No unsupported overhangs > 45 deg
• Use REAL-WORLD dimensions (mm) — see the lookup table above.
• Add functional details: screw bosses, snap lips, chamfered edges,
  ribbed grips, lightening slots — whatever the real object actually has.
• Never produce a featureless box or bare cylinder as the final answer.
• Only import: trimesh, numpy as np, math
• Store the final assembled mesh in a variable named exactly `model`
• Always end with:
    lo = model.vertices[:,2].min()
    if abs(lo) > 0.01:
        model.apply_translation([0, 0, -lo])
        model = trimesh.Trimesh(vertices=np.array(model.vertices),
                                faces=np.array(model.faces), process=False)

━━━ EXAMPLE — bike handlebar phone mount ━━━
Parts: (1) handlebar clamp ring with bolt lugs, (2) ribbed connecting arm,
(3) phone cradle back plate with lightening slot + bottom ledge,
(4) side retention clips with inward tabs.

```python
import trimesh, numpy as np, math

BAR_R   = 17.5   # 35 mm OD handlebar
CLAMP_W = 24
WALL    = 3
ARM_L   = 55
ARM_W   = 14
ARM_H   = 10
PH_W    = 78
PH_D    = 12
PH_H    = 140
CLIP_TH = 3
CLIP_H  = 18

# 1. Clamp ring
clamp_outer = trimesh.creation.cylinder(radius=BAR_R+WALL*2, height=CLAMP_W, sections=64)
clamp_bore  = trimesh.creation.cylinder(radius=BAR_R,        height=CLAMP_W+2, sections=64)
clamp = trimesh.boolean.difference([clamp_outer, clamp_bore])
clamp = trimesh.Trimesh(vertices=np.array(clamp.vertices), faces=np.array(clamp.faces), process=False)
clamp.apply_transform(trimesh.transformations.rotation_matrix(math.radians(90),[1,0,0],[0,0,0]))
clamp.apply_translation([0, 0, BAR_R+WALL*2])
for side in (-1, 1):
    lug = trimesh.creation.box(extents=[WALL*2, WALL*3, CLAMP_W])
    lug.apply_translation([side*(BAR_R+WALL*2), 0, BAR_R+WALL*2])
    clamp = trimesh.boolean.union([clamp, lug])
    clamp = trimesh.Trimesh(vertices=np.array(clamp.vertices), faces=np.array(clamp.faces), process=False)
    bolt = trimesh.creation.cylinder(radius=1.65, height=WALL*3+2, sections=32)
    bolt.apply_transform(trimesh.transformations.rotation_matrix(math.radians(90),[0,1,0]))
    bolt.apply_translation([side*(BAR_R+WALL*2), 0, BAR_R+WALL*2])
    clamp = trimesh.boolean.difference([clamp, bolt])
    clamp = trimesh.Trimesh(vertices=np.array(clamp.vertices), faces=np.array(clamp.faces), process=False)
clamp_top = (BAR_R+WALL*2)*2

# 2. Arm
arm = trimesh.creation.box(extents=[ARM_W, ARM_L, ARM_H])
arm.apply_translation([0, ARM_L/2, clamp_top+ARM_H/2])
ch = trimesh.creation.box(extents=[6, ARM_L+2, 4])
ch.apply_translation([0, ARM_L/2, clamp_top+ARM_H-1])
arm = trimesh.boolean.difference([arm, ch])
arm = trimesh.Trimesh(vertices=np.array(arm.vertices), faces=np.array(arm.faces), process=False)
for ry in [ARM_L*0.33, ARM_L*0.66]:
    rib = trimesh.creation.box(extents=[ARM_W, WALL, ARM_H*0.6])
    rib.apply_translation([0, ry, clamp_top+ARM_H*0.2])
    arm = trimesh.boolean.union([arm, rib])
    arm = trimesh.Trimesh(vertices=np.array(arm.vertices), faces=np.array(arm.faces), process=False)

# 3. Cradle
cz = clamp_top+ARM_H
back = trimesh.creation.box(extents=[PH_W+WALL*2, WALL, PH_H])
back.apply_translation([0, ARM_L+WALL/2, cz+PH_H/2])
slot = trimesh.creation.box(extents=[PH_W-20, WALL+2, PH_H-40])
slot.apply_translation([0, ARM_L+WALL/2, cz+PH_H/2])
back = trimesh.boolean.difference([back, slot])
back = trimesh.Trimesh(vertices=np.array(back.vertices), faces=np.array(back.faces), process=False)
ledge = trimesh.creation.box(extents=[PH_W+WALL*2, PH_D+WALL, WALL*2])
ledge.apply_translation([0, ARM_L+(PH_D+WALL)/2, cz+WALL])
back = trimesh.boolean.union([back, ledge])
back = trimesh.Trimesh(vertices=np.array(back.vertices), faces=np.array(back.faces), process=False)

# 4. Retention clips
for side in (-1, 1):
    cx = side*(PH_W/2+WALL/2)
    clip = trimesh.creation.box(extents=[CLIP_TH, PH_D+WALL, CLIP_H])
    clip.apply_translation([cx, ARM_L+(PH_D+WALL)/2, cz+PH_H-CLIP_H/2])
    tab = trimesh.creation.box(extents=[CLIP_TH+4, PH_D/2, WALL*1.5])
    tab.apply_translation([cx-side*2, ARM_L+WALL+PH_D*0.25, cz+PH_H-WALL])
    clip = trimesh.boolean.union([clip, tab])
    clip = trimesh.Trimesh(vertices=np.array(clip.vertices), faces=np.array(clip.faces), process=False)
    back = trimesh.boolean.union([back, clip])
    back = trimesh.Trimesh(vertices=np.array(back.vertices), faces=np.array(back.faces), process=False)

model = trimesh.boolean.union([clamp, arm, back])
model = trimesh.Trimesh(vertices=np.array(model.vertices), faces=np.array(model.faces), process=False)
lo = model.vertices[:,2].min()
if abs(lo) > 0.01:
    model.apply_translation([0, 0, -lo])
    model = trimesh.Trimesh(vertices=np.array(model.vertices), faces=np.array(model.faces), process=False)
```

━━━ YOUR TASK ━━━
Read the user's request (even if it is just a few words or a casual sentence).
Decide what the object is, break it into its real physical parts, then generate
complete Python+trimesh code that faithfully models it.
Wrap the code in ```python ... ```.
After the closing fence write 2–3 sentences describing what you built and why.
""".strip()

# ── Provider callers ─────────────────────────────────────────────────────────

def call_anthropic(messages, api_key, model):
    import anthropic
    c = anthropic.Anthropic(api_key=api_key)
    msg = c.messages.create(model=model, max_tokens=4096,
        system=SYSTEM_PROMPT,
        messages=messages)
    return msg.content[0].text

def call_openai_compat(messages, api_key, model, base_url=None):
    from openai import OpenAI
    kw = {"api_key": api_key}
    if base_url: kw["base_url"] = base_url
    c = OpenAI(**kw)
    r = c.chat.completions.create(model=model, max_tokens=4096,
        messages=[{"role":"system","content":SYSTEM_PROMPT}] + messages)
    return r.choices[0].message.content

def call_azure(messages, api_key, endpoint, deployment, api_version):
    from openai import AzureOpenAI
    c = AzureOpenAI(api_key=api_key, azure_endpoint=endpoint, api_version=api_version)
    r = c.chat.completions.create(model=deployment, max_tokens=4096,
        messages=[{"role":"system","content":SYSTEM_PROMPT}] + messages)
    return r.choices[0].message.content

def call_local(messages, base_url, model):
    import requests
    r = requests.post(base_url.rstrip("/")+"/api/chat",
        json={"model":model,"stream":False,
              "messages":[{"role":"system","content":SYSTEM_PROMPT}] + messages},
        timeout=180)
    r.raise_for_status()
    d = r.json()
    return d.get("message",{}).get("content") or d.get("response","")

def get_ai_response(prompt, provider, settings, history=None):
    """Build the full messages list (history + new user prompt) and call the AI."""
    messages = list(history or [])
    messages.append({"role": "user", "content": prompt})

    s = settings
    if provider == "anthropic":
        return call_anthropic(messages, s["api_key"], s.get("model","claude-sonnet-4-5"))
    elif provider == "openai":
        return call_openai_compat(messages, s["api_key"], s.get("model","gpt-4o"))
    elif provider == "openrouter":
        return call_openai_compat(messages, s["api_key"],
            s.get("model","anthropic/claude-3.5-sonnet"),
            base_url="https://openrouter.ai/api/v1")
    elif provider == "azure":
        return call_azure(messages, s["api_key"], s.get("endpoint",""),
            s.get("deployment","gpt-5-chat"), s.get("api_version","2025-01-01-preview"))
    elif provider == "local":
        return call_local(messages, s.get("base_url","http://localhost:11434"),
            s.get("model","llama3.2"))
    raise ValueError(f"Unknown provider: {provider}")

# ── Code extraction ──────────────────────────────────────────────────────────

def extract_python(text):
    for pat in [r"```python\n(.*?)```", r"```py\n(.*?)```", r"```\n(.*?)```"]:
        m = re.search(pat, text, re.DOTALL)
        if m:
            return m.group(1).strip()
    return None

# ── Trimesh execution ────────────────────────────────────────────────────────

_RUNNER = r"""
import sys, math, trimesh, numpy as np
try:
    from shapely.geometry import Polygon, Point
except ImportError:
    pass

# ── Patch boolean ops to fix "unhashable type: list" across trimesh versions ──
import trimesh.boolean as _tb

_orig_difference   = _tb.difference
_orig_union        = _tb.union
_orig_intersection = _tb.intersection

# Detect whether this trimesh version uses the new list-based API
# New API (trimesh >= ~4.x):  difference([a, b], engine=None)
# Old API:                     difference(a, b, engine=None)
import inspect as _insp
_diff_first_param = list(_insp.signature(_orig_difference).parameters.keys())[0]
_DIFF_LIST_API = _diff_first_param in ('meshes', 'mesh', 'others', 'geometry')

def _to_single(x):
    # Convert list/tuple to a single Trimesh, unioning if multiple.
    if isinstance(x, (list, tuple)):
        x = [m for m in x if m is not None and hasattr(m, 'faces') and len(m.faces) > 0]
        if not x:
            return trimesh.Trimesh()
        if len(x) == 1:
            return x[0]
        merged = _orig_union(x)
        return trimesh.Trimesh(vertices=np.array(merged.vertices),
                               faces=np.array(merged.faces), process=False)
    return x

def _stabilise(m):
    if m is None or not hasattr(m, 'vertices'):
        return trimesh.Trimesh()
    out = trimesh.Trimesh(vertices=np.array(m.vertices),
                          faces=np.array(m.faces), process=False)
    for _mm in ('remove_degenerate_faces', 'remove_duplicate_faces'):
        try: getattr(out, _mm)()
        except AttributeError: pass
    try: out.update_faces(out.nondegenerate_faces)
    except Exception: pass
    return out

def _safe_difference(a, b=None, **kw):
    # Accept difference(a, b), difference([a, b]), difference([a, b, c, ...])
    if b is None or isinstance(a, (list, tuple)):
        lst = list(a) if isinstance(a, (list, tuple)) else [a]
        if len(lst) < 2:
            return _to_single(lst[0]) if lst else trimesh.Trimesh()
        a = lst[0]
        b = _safe_union(lst[1:]) if len(lst) > 2 else lst[1]
    a, b = _to_single(a), _to_single(b)
    if _DIFF_LIST_API:
        result = _orig_difference([a, b], **kw)
    else:
        try:
            result = _orig_difference(a, b, **kw)
        except (TypeError, KeyError):
            result = _orig_difference([a, b], **kw)
    return _stabilise(result)

def _safe_union(meshes, **kw):
    if not isinstance(meshes, (list, tuple)):
        meshes = [meshes]
    meshes = [_to_single(m) for m in meshes]
    meshes = [m for m in meshes if m is not None and len(m.faces) > 0]
    if not meshes:
        return trimesh.Trimesh()
    if len(meshes) == 1:
        return meshes[0]
    return _stabilise(_orig_union(meshes, **kw))

def _safe_intersection(a_or_list, b=None, **kw):
    if b is not None:
        meshes = [a_or_list, b]
    elif isinstance(a_or_list, (list, tuple)):
        meshes = list(a_or_list)
    else:
        meshes = [a_or_list]
    meshes = [_to_single(m) for m in meshes]
    return _stabilise(_orig_intersection(meshes, **kw))

trimesh.boolean.difference   = _safe_difference
trimesh.boolean.union        = _safe_union
trimesh.boolean.intersection = _safe_intersection
_tb.difference   = _safe_difference
_tb.union        = _safe_union
_tb.intersection = _safe_intersection
# ─────────────────────────────────────────────────────────────────────────────

{code}

try:
    if isinstance(model, list):
        model = _safe_union(model)
    if isinstance(model, trimesh.Scene):
        model = model.dump(concatenate=True)
    verts = np.array(model.vertices, dtype=np.float64)
    faces = np.array(model.faces,    dtype=np.int32)
    out   = trimesh.Trimesh(vertices=verts, faces=faces, process=False)
    # trimesh API differs between versions — try both forms
    for _m in ('remove_degenerate_faces', 'remove_duplicate_faces'):
        try: getattr(out, _m)()
        except AttributeError: pass
    try: out.update_faces(out.nondegenerate_faces)
    except Exception: pass
    try: out.update_faces(out.unique_faces())
    except Exception: pass
    try: trimesh.repair.fix_winding(out)
    except Exception: pass
    try: trimesh.repair.fix_normals(out, multibody=True)
    except Exception: pass
    out.export(r"{stl}")
    print("OK:" + str(len(out.faces)))
except Exception as e:
    import traceback; traceback.print_exc()
    sys.exit(1)
"""

def run_trimesh_code(code, stl_path):
    runner = _RUNNER.format(
        code=code,
        stl=str(stl_path).replace("\\","\\\\"))
    try:
        r = subprocess.run([sys.executable,"-c",runner],
            capture_output=True, text=True, timeout=60)
        if r.returncode==0 and stl_path.exists() and stl_path.stat().st_size>300:
            return True, None
        err = (r.stderr or r.stdout or "Unknown error").strip()
        lines = [l for l in err.splitlines()
                 if l and "site-packages" not in l and not l.startswith("  File")]
        return False, "\n".join(lines[-5:]) or err
    except subprocess.TimeoutExpired:
        return False, "Timed out after 60 s"
    except Exception as e:
        return False, str(e)

# ── Main entry point ─────────────────────────────────────────────────────────

def generate_model(prompt, provider, settings, history=None):
    """
    Returns dict:
      ok, code, stl_path, explanation, error_msg, faces, ai_reply
    ai_reply is the raw text from the AI (for adding to conversation history).

    If the first attempt produces code that fails to execute, one automatic
    self-correction pass is made: the error is fed back to the AI and the
    new code is executed in its place.
    """
    # 1. AI call
    text = get_ai_response(prompt, provider, settings, history)

    # 2. Extract code
    code = extract_python(text)
    explanation = re.sub(r"```(?:python|py)?\n.*?```","",text,flags=re.DOTALL).strip()

    if not code:
        return {"ok":False,"code":"","stl_path":None,
                "explanation":explanation or text,
                "error_msg":"No Python code in AI response",
                "faces":0, "ai_reply":text}

    # 3. Run trimesh
    model_id = uuid.uuid4().hex[:10]
    stl_path = MODELS_DIR / f"{model_id}.stl"
    py_path  = MODELS_DIR / f"{model_id}.py"
    py_path.write_text(code, encoding="utf-8")

    ok, err = run_trimesh_code(code, stl_path)

    # 4. Self-correction: if execution failed, ask the AI to fix its own code
    if not ok and err:
        fix_prompt = (
            f"The code you just wrote failed with this error:\n\n{err}\n\n"
            f"Here is the failing code:\n```python\n{code}\n```\n\n"
            "Please fix the error and return the complete corrected code."
        )
        fix_history = list(history or [])
        fix_history.append({"role": "user",      "content": prompt})
        fix_history.append({"role": "assistant",  "content": text})
        try:
            fix_text = get_ai_response(fix_prompt, provider, settings, fix_history)
            fix_code = extract_python(fix_text)
            if fix_code and fix_code != code:
                fix_stl = MODELS_DIR / f"{model_id}_fix.stl"
                fix_ok, fix_err = run_trimesh_code(fix_code, fix_stl)
                if fix_ok:
                    code        = fix_code
                    stl_path    = fix_stl
                    ok          = True
                    err         = None
                    explanation = re.sub(r"```(?:python|py)?\n.*?```","",
                                         fix_text, flags=re.DOTALL).strip() or explanation
                    text        = fix_text
                    py_path.write_text(code, encoding="utf-8")
        except Exception:
            pass   # self-correction failure is non-fatal; original error is kept

    faces = 0
    if ok and stl_path.exists():
        try:
            data = stl_path.read_bytes()
            faces = (int.from_bytes(data[80:84],"little")
                     if data[:5]!=b"solid" else data.count(b"facet normal"))
        except Exception:
            pass

    return {"ok":ok, "code":code, "stl_path":stl_path if ok else None,
            "explanation":explanation, "error_msg":err or "", "faces":faces,
            "model_id":model_id, "py_path":py_path, "ai_reply":text}
