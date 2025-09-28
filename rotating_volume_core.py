# rotating_volume_core.py (original colors + Wolfram integration)
from manim import *
import numpy as np
import math as m
import os
import argparse
from wolfram_bridge import compute_with_wolfram

# -------- tiny safe evaluator --------
def safe_eval_expr(expr: str, *, x: float) -> float:
    allowed = {k: getattr(m, k) for k in dir(m) if not k.startswith("_")}
    allowed.update({k: getattr(np, k) for k in dir(np) if not k.startswith("_")})
    allowed.update({"pi": m.pi, "e": m.e, "tau": m.tau})
    allowed["x"] = x
    return float(eval(expr, {"__builtins__": {}}, allowed))

def estimate_ymax(expr: str, a: float, b: float) -> float:
    xs = np.linspace(a, b, 256)
    vals = []
    for xv in xs:
        try:
            vals.append(abs(safe_eval_expr(expr, x=xv)))
        except Exception:
            vals.append(0.0)
    ymax = max(vals) if vals else 1.0
    return max(1.0, ymax) * 1.15

# -------- interactive prompts --------
def _prompt_params(default_expr="exp(x)", default_a=1.0, default_b=2.0):
    print("\n=== Volume of Revolution (around x-axis) ===")
    print("Enter f(x) using math/NumPy style (e.g., sin(x), exp(x)+0.3*x, abs(sin(5*x))).")
    print("You can use pi, e, tau.\n")
    expr = input(f"f(x) [{default_expr}]: ").strip() or default_expr

    def parse_limit(s, default_val):
        s = s.strip()
        if not s:
            return float(default_val)
        try:
            allowed = {k: getattr(m, k) for k in dir(m) if not k.startswith("_")}
            allowed.update({"pi": m.pi, "e": m.e, "tau": m.tau})
            return float(eval(s, {"__builtins__": {}}, allowed))
        except Exception:
            print(f"Could not parse '{s}', using default {default_val}")
            return float(default_val)

    a_str = input(f"a (lower limit) [{default_a}]: ")
    b_str = input(f"b (upper limit) [{default_b}]: ")
    a = parse_limit(a_str, default_a)
    b = parse_limit(b_str, default_b)
    if a == b: b += 1
    if a > b: a, b = b, a

    try:
        _ = safe_eval_expr(expr, x=(a + b) * 0.5)
    except Exception as e:
        print(f"Expression check failed: {e}, using default.")
        expr = default_expr

    print(f"\nUsing: f(x) = {expr}, interval = [{a}, {b}]\n")
    return expr, a, b

# -------- the scene --------
class Rotating3DAxis(ThreeDScene):
    expr = "exp(x)"
    a = 1.0
    b = 2.0

    def construct(self):
        if os.getenv("SKIP_PROMPT", "0") != "1":
            self.expr, self.a, self.b = _prompt_params(self.expr, self.a, self.b)
        expr, a, b = self.expr, float(self.a), float(self.b)

        # Try Wolfram for yMax & integral; fall back if unavailable
        w = compute_with_wolfram(expr, a, b)
        if w and isinstance(w.get("yMaxNumeric"), (int, float)):
            y_max = float(w["yMaxNumeric"])
        else:
            y_max = estimate_ymax(expr, a, b)

        self.set_camera_orientation(phi=75 * DEGREES, theta=45 * DEGREES)

        step = max(1.0, y_max / 3)
        axes = ThreeDAxes(
            x_range=[a - 1, b + 1, 1],
            y_range=[-y_max, y_max, step],
            z_range=[-y_max, y_max, step],
        )
        self.add(axes)

        f = lambda x: safe_eval_expr(expr, x=x)

        # graph (default Manim yellow)
        graph = axes.plot(f, x_range=[a, b], color=YELLOW)
        self.play(Create(graph), run_time=2)

        # surface (default Manim blue)
        surface = Surface(
            lambda u, v: axes.c2p(u, f(u) * np.cos(v), f(u) * np.sin(v)),
            u_range=[a + 1e-3, b],
            v_range=[0, TAU],
            resolution=(24, 48),
            fill_opacity=0.5,
            color=BLUE,
        )
        self.play(Create(surface), run_time=2.5)

        # rotate
        self.play(Rotate(VGroup(axes, graph, surface),
                         angle=2 * PI, axis=OUT,
                         run_time=6, rate_func=smooth))
        self.wait(0.3)

        # slice and radius
        p = 0.5 * (a + b)
        sliced_surface = Surface(
            lambda u, v: axes.c2p(u, f(u) * np.cos(v), f(u) * np.sin(v)),
            u_range=[p, p + 0.06 * max(0.05, (b - a))],
            v_range=[0, TAU],
            resolution=(16, 40),
            fill_opacity=0.5,
            color=BLUE,
        )
        self.play(Transform(surface, sliced_surface), run_time=1.0)

        radius_line = Line(
            start=axes.c2p(p, 0, 0),
            end=axes.c2p(p, f(p), 0),
            color=RED,
        )
        self.play(Create(radius_line), run_time=0.8)

        radius_label = MathTex(r"r = f(x)", color=RED).next_to(radius_line, RIGHT, buff=0.15)
        self.move_camera(phi=0, theta=-90 * DEGREES, run_time=1.0)
        self.play(Write(radius_label), run_time=0.8)

        self.wait(0.4)
        self.clear()

        # integral label: prefer Wolfram's TeX if available
        if w and isinstance(w.get("integralTeX"), str) and len(w["integralTeX"]) > 0:
            integral = MathTex(w["integralTeX"])
        else:
            integral = MathTex(rf"V \;=\; \int_{{{self._fmt(a)}}}^{{{self._fmt(b)}}} \pi\,[f(x)]^2\,dx")
        self.play(Write(integral))
        self.wait(2)

    @staticmethod
    def _fmt(v: float) -> str:
        return str(int(v)) if abs(v - int(v)) < 1e-9 else f"{v:.3g}"

# -------- programmatic entry --------
def _run_programmatically():
    p = argparse.ArgumentParser()
    p.add_argument("--quality", choices=["low", "medium", "high"], default="low")
    p.add_argument("--preview", action="store_true", default=True)
    p.add_argument("--no-prompt", action="store_true", help="Skip interactive prompts (use defaults).")
    args = p.parse_args()

    qmap = {"low": "low_quality", "medium": "medium_quality", "high": "high_quality"}
    with tempconfig({"quality": qmap[args.quality], "preview": args.preview}):
        if args.no_prompt:
            os.environ["SKIP_PROMPT"] = "1"
        scene = Rotating3DAxis()
        scene.render()

if __name__ == "__main__":
    _run_programmatically()
