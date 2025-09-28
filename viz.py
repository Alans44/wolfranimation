# viz.py
import os, sys, subprocess, shlex

def run(scene, f2d=None, f3d=None, x=(-6,6), y=(-4,4), z=(-3,3), quality="l"):
    env = os.environ.copy()
    if f2d is not None: env["FUNC2D"] = f2d
    if f3d is not None: env["FUNC3D"] = f3d
    env["XRANGE"] = f"{x[0]},{x[1]}"
    env["YRANGE"] = f"{y[0]},{y[1]}"
    env["ZRANGE"] = f"{z[0]},{z[1]}"

    # -p = preview, -q{l|m|h|k} = quality
    cmd = f'manim -p q{quality and " -q"+quality or ""} -p -q{quality} equation_viz.py {scene}'
    # fix duplicated args above if you like; leaving explicit is fine
    cmd = f"manim -p -q{quality} equation_viz.py {scene}"
    print(">>", cmd)
    subprocess.run(shlex.split(cmd), env=env, check=True)

if __name__ == "__main__":
    # examples:
    # python viz.py Graph2DScene "sin(x)"
    # python viz.py Graph3DScene None "sin(x)*cos(y)"
    scene = sys.argv[1]
    f2d  = sys.argv[2] if len(sys.argv) > 2 and sys.argv[2].lower() != "none" else None
    f3d  = sys.argv[3] if len(sys.argv) > 3 and sys.argv[3].lower() != "none" else None
    run(scene, f2d=f2d, f3d=f3d, quality="l")
