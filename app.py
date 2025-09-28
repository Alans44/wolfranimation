# filename: app.py
import os
import shutil
import subprocess
from pathlib import Path

import streamlit as st

APP_DIR = Path(__file__).parent.resolve()
OUT_DIR = APP_DIR / "out"
OUT_DIR.mkdir(exist_ok=True)

st.set_page_config(
    page_title="Equation Visualizer (Manim)",
    page_icon="📈",
    layout="wide",
    initial_sidebar_state="expanded",
)

# ------------------ Styled header ------------------
st.markdown(
    """
    <style>
    .hero {
        padding: 18px 22px;
        border-radius: 18px;
        background: radial-gradient(1200px 600px at 0% 0%, #0ea5e922, transparent 60%),
                    radial-gradient(1200px 600px at 100% 0%, #22c55e22, transparent 60%),
                    linear-gradient(135deg, #0f172a, #0b1220);
        border: 1px solid #1e293b;
        color: #e2e8f0;
        margin-bottom: 10px;
    }
    .muted { color:#93a3b8; }
    .chip {
        display:inline-block; padding:6px 10px; margin:4px 6px 0 0;
        border-radius:999px; background:#0b1220; border:1px solid #1f2a44; color:#cbd5e1;
        cursor:pointer; font-size: 0.9rem;
    }
    .card {
        padding: 14px 16px; border-radius: 14px; border: 1px solid #1f2a44; background: #0b1220;
    }
    </style>
    <div class="hero">
      <h2 style="margin:0">📈 Equation Visualizer</h2>
      <div class="muted">Enter an equation, tune ranges, render beautiful 2D/3D animations with Manim.</div>
    </div>
    """,
    unsafe_allow_html=True
)

# ------------------ Sidebar ------------------
with st.sidebar:
    st.header("Render Settings")
    quality = st.selectbox("Quality", ["l (fast)", "m", "h", "k (4K)"], index=0)
    use_latex = st.toggle("Use LaTeX tick numbers & labels", value=True, help="Disable if LaTeX is not configured.")
    st.caption("Tip: keep 'l' for previews; switch to 'h'/'k' for final exports.")

# ------------------ Helpers ------------------
def run_manim(scene: str, func2d: str | None, func3d: str | None,
              xr: tuple[float,float], yr: tuple[float,float], zr: tuple[float,float] = (-3.5,3.5),
              q: str = "l", use_latex_flag: bool = True, outfile: Path | None = None) -> Path:
    """
    Calls Manim in a subprocess and returns the output video path.
    """
    env = os.environ.copy()
    if func2d: env["FUNC2D"] = func2d
    else: env.pop("FUNC2D", None)
    if func3d: env["FUNC3D"] = func3d
    else: env.pop("FUNC3D", None)
    env["XRANGE"] = f"{xr[0]},{xr[1]}"
    env["YRANGE"] = f"{yr[0]},{yr[1]}"
    env["ZRANGE"] = f"{zr[0]},{zr[1]}"
    env["USE_LATEX"] = "1" if use_latex_flag else "0"
    env["ALLOW_INPUT"] = "0"  # GUI: never prompt in Manim file

    out_path = outfile or (OUT_DIR / f"{scene.lower()}_{('2d' if scene=='Graph2DScene' else '3d')}.mp4")
    # Ensure clean output file
    if out_path.exists():
        out_path.unlink()

    # manim command
    cmd = [
        "manim",
        "-q", q[0],               # l/m/h/k
        "-o", out_path.name,      # output filename
        str(APP_DIR / "equation_viz.py"),
        scene,
    ]

    # On Windows, make sure cwd is the app dir for stable media paths
    res = subprocess.run(cmd, cwd=APP_DIR, env=env, capture_output=True, text=True)

    if res.returncode != 0:
        raise RuntimeError(f"Manim failed:\nSTDOUT:\n{res.stdout}\n\nSTDERR:\n{res.stderr}")

    # Move from manim's output directory to OUT_DIR if needed
    # Manim saves into media/videos/<module>/<quality>/
    # We already set -o, so it will be in the cwd's media folder; search it:
    media_root = APP_DIR / "media"
    found = list(media_root.rglob(out_path.name))
    if found:
        src = found[0]
        shutil.move(str(src), str(out_path))
    return out_path

# ------------------ Content ------------------
tab2d, tab3d = st.tabs(["🟦 2D Function", "🟩 3D Surface"])

# Example chips (click to fill)
examples_2d = ["sin(x)", "x**3 - 3*x", "exp(-x**2)*cos(3*x)", "sin(x) + x**2/8"]
examples_3d = ["sin(x)*cos(y)", "(x**2 - y**2)/4", "exp(-(x**2+y**2))*cos(3*x)*sin(3*y)"]

with tab2d:
    st.markdown('<div class="card">', unsafe_allow_html=True)
    st.subheader("2D: y = f(x)")
    cols = st.columns([3,1,1])
    with cols[0]:
        f2d = st.text_input("Function", value="sin(x)", placeholder="e.g., sin(x) or y = sin(x)")
    with cols[1]:
        xr_min = st.number_input("x min", value=-6.0)
    with cols[2]:
        xr_max = st.number_input("x max", value=6.0)

    st.caption("Examples:")
    ex_row = "".join([f'<span class="chip" onclick="window.parent.postMessage({{type:\'set2d\',v:\'{e}\'}} , \'*\')">{e}</span>' for e in examples_2d])
    st.markdown(ex_row, unsafe_allow_html=True)

    r2d = st.button("Render 2D", type="primary")
    st.markdown('</div>', unsafe_allow_html=True)

    if r2d:
        try:
            vid = run_manim(
                scene="Graph2DScene",
                func2d=f2d, func3d=None,
                xr=(xr_min, xr_max), yr=(-4, 4),
                q=quality[0], use_latex_flag=use_latex
            )
            st.success("Rendered!")
            st.video(str(vid))
            st.caption(f"Saved to: {vid}")
        except Exception as e:
            st.error(str(e))

with tab3d:
    st.markdown('<div class="card">', unsafe_allow_html=True)
    st.subheader("3D: z = f(x, y)")
    c1, c2, c3 = st.columns([3,1,1])
    with c1:
        f3d = st.text_input("Surface", value="sin(x)*cos(y)", placeholder="e.g., sin(x)*cos(y) or z = ...")
    with c2:
        xr_min3 = st.number_input("x min", value=-3.5, key="xmin3")
        yr_min3 = st.number_input("y min", value=-3.5, key="ymin3")
    with c3:
        xr_max3 = st.number_input("x max", value=3.5, key="xmax3")
        yr_max3 = st.number_input("y max", value=3.5, key="ymax3")

    st.caption("Examples:")
    ex_row3 = "".join([f'<span class="chip" onclick="window.parent.postMessage({{type:\'set3d\',v:\'{e}\'}} , \'*\')">{e}</span>' for e in examples_3d])
    st.markdown(ex_row3, unsafe_allow_html=True)

    r3d = st.button("Render 3D", type="primary")
    st.markdown('</div>', unsafe_allow_html=True)

    if r3d:
        try:
            vid = run_manim(
                scene="Graph3DScene",
                func2d=None, func3d=f3d,
                xr=(xr_min3, xr_max3), yr=(yr_min3, yr_max3), zr=(-3.5, 3.5),
                q=quality[0], use_latex_flag=use_latex
            )
            st.success("Rendered!")
            st.video(str(vid))
            st.caption(f"Saved to: {vid}")
        except Exception as e:
            st.error(str(e))

# -------------- Tiny JS to fill examples --------------
st.markdown(
    """
    <script>
    window.addEventListener('message', (event) => {
      const data = event.data || {};
      if (data.type === 'set2d') {
        const txt = window.parent.document.querySelector('input[aria-label="Function"]');
        if (txt) { txt.value = data.v; txt.dispatchEvent(new Event('input', {bubbles:true})); }
      }
      if (data.type === 'set3d') {
        const txt = window.parent.document.querySelector('input[aria-label="Surface"]');
        if (txt) { txt.value = data.v; txt.dispatchEvent(new Event('input', {bubbles:true})); }
      }
    });
    </script>
    """,
    unsafe_allow_html=True
)
