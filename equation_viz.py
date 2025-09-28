# filename: equation_viz.py
from __future__ import annotations
import os, math
import numpy as np
import sympy as sp

from manim import (
    Scene, ThreeDScene, Axes, ThreeDAxes, VGroup,
    MathTex, Tex, Text,  # Text used when LaTeX disabled
    FadeIn, Create, ORIGIN, Surface,
    UP, DOWN, LEFT, RIGHT
)

# -----------------------------
# Config: LaTeX toggle (env var)
# -----------------------------
# USE_LATEX="1" (default) or "0"
USE_LATEX = os.getenv("USE_LATEX", "1") not in ("0", "false", "False")

def label_obj(tex_or_text: str, font_size: int = 36):
    """Return a label object. Uses MathTex if LaTeX enabled, else Text."""
    if USE_LATEX:
        return MathTex(tex_or_text).scale(font_size/36)
    return Text(tex_or_text, font_size=font_size)

# ---------------------------
# Read functions from env / IO
# ---------------------------
def _read_equations():
    f2d = os.getenv("FUNC2D", "").strip()
    f3d = os.getenv("FUNC3D", "").strip()
    # Avoid interactive prompt in headless runs; only prompt if explicitly empty and TTY
    if f2d == "" and os.getenv("ALLOW_INPUT", "0") == "1":
        try: f2d = input("Enter 2D function y = f(x) (or just f(x)) [blank to skip]: ").strip()
        except Exception: f2d = ""
    if f3d == "" and os.getenv("ALLOW_INPUT", "0") == "1":
        try: f3d = input("Enter 3D function z = f(x,y) (or just f(x,y)) [blank to skip]: ").strip()
        except Exception: f3d = ""
    return f2d, f3d

def _rhs(s: str) -> str:
    return s.split("=", 1)[1] if "=" in s else s

def _sym(s: str):
    try:
        return sp.sympify(s, convert_xor=True)
    except Exception:
        return None

X, Y = sp.symbols("x y")
F2_RAW, F3_RAW = _read_equations()

def parse2d(s):
    if not s: return None, None, None
    expr = _sym(_rhs(s))
    if expr is None: return None, None, None
    f = sp.lambdify(X, expr, modules=["numpy", {"pi": math.pi, "e": math.e}])
    tex = r"y = " + sp.latex(expr) if USE_LATEX else f"y = {sp.sstr(expr)}"
    return f, expr, tex

def parse3d(s):
    if not s: return None, None, None
    expr = _sym(_rhs(s))
    if expr is None: return None, None, None
    f = sp.lambdify((X, Y), expr, modules=["numpy", {"pi": math.pi, "e": math.e}])
    tex = r"z = " + sp.latex(expr) if USE_LATEX else f"z = {sp.sstr(expr)}"
    return f, expr, tex

F2D, E2D, T2D = parse2d(F2_RAW)
F3D, E3D, T3D = parse3d(F3_RAW)

def _read_range(name: str, default_tuple):
    """
    Expect env var like 'XRANGE' = 'min,max,step'; step optional.
    Returns a (min, max, step) tuple compatible with Manim ranges.
    """
    s = os.getenv(name, "").strip()
    if not s:
        return default_tuple
    parts = [p for p in s.split(",") if p]
    vals = list(map(float, parts[:2]))
    step = float(parts[2]) if len(parts) > 2 else default_tuple[2]
    return (vals[0], vals[1], step)

# Ranges from env (with defaults)
XR = _read_range("XRANGE", (-6.0, 6.0, 1.0))
YR = _read_range("YRANGE", (-4.0, 4.0, 1.0))
ZR = _read_range("ZRANGE", (-3.5, 3.5, 1.0))

# -------------------------
# 2D Scene
# -------------------------
class Graph2DScene(Scene):
    def construct(self):
        if F2D is None:
            self.play(FadeIn(Text("No 2D function provided.", font_size=32)))
            self.wait(1.2)
            return

        axes = Axes(
            x_range=XR, y_range=YR,
            x_length=10, y_length=6,
            tips=False,
            axis_config={"include_numbers": USE_LATEX}  # numeric ticks need LaTeX
        ).to_edge(ORIGIN)

        title = label_obj(T2D, 38).to_edge(UP)
        self.play(Create(axes), FadeIn(title)); self.wait(0.2)

        def safe_fx(x):
            try:
                with np.errstate(all="ignore"):
                    v = F2D(x)
                if v is None: return np.nan
                if isinstance(v, np.ndarray): return v
                return float(v)
            except Exception:
                return np.nan

        graph = axes.plot(
            lambda t: safe_fx(t),
            x_range=(XR[0], XR[1]),
            dt=0.02, use_smoothing=False
        )
        self.play(Create(graph)); self.wait(0.6)

        self.play(FadeIn(label_obj("x", 24).next_to(axes.x_axis.get_end(), DOWN)))
        self.play(FadeIn(label_obj("y", 24).next_to(axes.y_axis.get_end(), LEFT)))
        self.wait(0.8)

# -------------------------
# 3D Scene
# -------------------------
class Graph3DScene(ThreeDScene):
    def construct(self):
        if F3D is None:
            self.play(FadeIn(Text("No 3D function provided.", font_size=32)))
            self.wait(1.2)
            return

        self.set_camera_orientation(phi=65*math.pi/180, theta=45*math.pi/180, zoom=1.2)

        axes = ThreeDAxes(
            x_range=XR, y_range=YR, z_range=ZR,
            x_length=8, y_length=8, z_length=5,
            axis_config={"include_numbers": USE_LATEX}
        )

        title = label_obj(T3D, 38).to_edge(UP)
        self.play(Create(axes), FadeIn(title)); self.wait(0.2)

        def safe_fxy(u, v):
            try:
                with np.errstate(all="ignore"):
                    val = F3D(u, v)
                if val is None: return np.nan
                if isinstance(val, np.ndarray): return val
                return float(val)
            except Exception:
                return np.nan

        surface = Surface(
            lambda u, v: axes.c2p(u, v, safe_fxy(u, v)),
            u_range=[XR[0], XR[1]],
            v_range=[YR[0], YR[1]],
            resolution=(32, 32),
            fill_opacity=0.85,
            checkerboard_colors=None,
        )

        self.play(FadeIn(surface))
        self.begin_3dillusion_camera_rotation(rate=0.15)
        self.wait(3.0)
        self.stop_3dillusion_camera_rotation()

        self.play(FadeIn(label_obj("x", 22).move_to(axes.x_axis.get_end() + np.array([0.3, -0.2, 0]))))
        self.play(FadeIn(label_obj("y", 22).move_to(axes.y_axis.get_end() + np.array([0.0, 0.3, 0]))))
        self.play(FadeIn(label_obj("z", 22).move_to(axes.z_axis.get_end() + np.array([0.0, 0.0, 0.3]))))
        self.wait(0.8)
