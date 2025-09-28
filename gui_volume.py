# gui_volume.py
import threading
import tkinter as tk
from tkinter import ttk, messagebox
from manim import tempconfig
import os

# import your scene
from rotating_volume_core import Rotating3DAxis, safe_eval_expr

# -------------------------
# utilities / validation
# -------------------------
def parse_limit(text: str):
    text = (text or "").strip()
    if not text:
        raise ValueError("Empty limit.")
    # allow pi, 2*pi, etc.
    import math as m
    allowed = {"pi": m.pi, "e": m.e, "tau": m.tau}
    try:
        return float(eval(text, {"__builtins__": {}}, allowed))
    except Exception as e:
        raise ValueError(f"Could not parse limit '{text}': {e}")

def quick_check_expr(expr: str, a: float, b: float):
    # probe at midpoint to catch obvious typos
    mid = 0.5 * (a + b)
    try:
        _ = safe_eval_expr(expr, x=mid)
    except Exception as e:
        raise ValueError(f"Expression error: {e}")

# -------------------------
# rendering worker thread
# -------------------------
def render_scene(expr, a, b, quality, preview, set_status, enable_ui):
    set_status("Rendering… this may take a moment")
    try:
        if a == b:
            b = a + 1.0
        if a > b:
            a, b = b, a

        # validate expression before render
        quick_check_expr(expr, a, b)

        qmap = {"Low (fast)": "low_quality", "Medium": "medium_quality", "High": "high_quality"}
        with tempconfig({"quality": qmap[quality], "preview": preview}):
            # don’t prompt inside scene
            os.environ["SKIP_PROMPT"] = "1"

            # instantiate and inject params
            scene = Rotating3DAxis()
            scene.expr = expr
            scene.a = float(a)
            scene.b = float(b)
            scene.render()

        set_status("Done! Video is in the media/videos/ folder.")
    except Exception as e:
        messagebox.showerror("Render failed", str(e))
        set_status("Failed.")
    finally:
        enable_ui()

# -------------------------
# GUI
# -------------------------
def main():
    root = tk.Tk()
    root.title("Volume of Revolution (Manim)")
    root.geometry("640x360")

    # Vars
    expr_var = tk.StringVar(value="exp(x)")
    a_var = tk.StringVar(value="1")
    b_var = tk.StringVar(value="2")
    quality_var = tk.StringVar(value="Low (fast)")
    preview_var = tk.BooleanVar(value=True)
    status_var = tk.StringVar(value="Ready")

    # Layout
    pad = {"padx": 10, "pady": 8}

    header = tk.Label(root, text="Rotate y = f(x) around the x-axis", font=("Segoe UI", 14, "bold"))
    header.grid(row=0, column=0, columnspan=3, sticky="w", **pad)

    tk.Label(root, text="f(x):", font=("Segoe UI", 11)).grid(row=1, column=0, sticky="e", **pad)
    expr_entry = ttk.Entry(root, textvariable=expr_var, width=40)
    expr_entry.grid(row=1, column=1, columnspan=2, sticky="we", **pad)

    tk.Label(root, text="a (lower):", font=("Segoe UI", 11)).grid(row=2, column=0, sticky="e", **pad)
    a_entry = ttk.Entry(root, textvariable=a_var, width=12)
    a_entry.grid(row=2, column=1, sticky="w", **pad)

    tk.Label(root, text="b (upper):", font=("Segoe UI", 11)).grid(row=3, column=0, sticky="e", **pad)
    b_entry = ttk.Entry(root, textvariable=b_var, width=12)
    b_entry.grid(row=3, column=1, sticky="w", **pad)

    tk.Label(root, text="Quality:", font=("Segoe UI", 11)).grid(row=4, column=0, sticky="e", **pad)
    quality_combo = ttk.Combobox(root, textvariable=quality_var, values=["Low (fast)", "Medium", "High"], state="readonly", width=12)
    quality_combo.grid(row=4, column=1, sticky="w", **pad)

    preview_check = ttk.Checkbutton(root, text="Preview when done", variable=preview_var)
    preview_check.grid(row=4, column=2, sticky="w", **pad)

    status_lbl = tk.Label(root, textvariable=status_var, fg="gray")
    status_lbl.grid(row=6, column=0, columnspan=3, sticky="w", padx=12, pady=(6, 0))

    # Buttons
    def set_status(msg):
        status_var.set(msg)
        status_lbl.update_idletasks()

    def disable_ui():
        render_btn.config(state="disabled")
        expr_entry.config(state="disabled")
        a_entry.config(state="disabled")
        b_entry.config(state="disabled")
        quality_combo.config(state="disabled")
        preview_check.config(state="disabled")

    def enable_ui():
        render_btn.config(state="normal")
        expr_entry.config(state="normal")
        a_entry.config(state="normal")
        b_entry.config(state="normal")
        quality_combo.config(state="readonly")
        preview_check.config(state="normal")

    def on_render():
        expr = expr_var.get().strip()
        try:
            a_val = parse_limit(a_var.get())
            b_val = parse_limit(b_var.get())
        except ValueError as e:
            messagebox.showerror("Invalid input", str(e))
            return

        disable_ui()
        set_status("Starting render…")

        t = threading.Thread(
            target=render_scene,
            args=(expr, a_val, b_val, quality_var.get(), preview_var.get(), set_status, enable_ui),
            daemon=True,
        )
        t.start()

    render_btn = ttk.Button(root, text="Render", command=on_render)
    render_btn.grid(row=5, column=1, sticky="w", **pad)

    # resize behavior
    root.columnconfigure(1, weight=1)
    root.mainloop()

if __name__ == "__main__":
    main()
