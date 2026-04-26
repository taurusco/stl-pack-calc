"""Generate two demo STL parts that exercise mesh nesting:

1. tray.stl — tapered open-top sheet-metal tote (nests by pure translation along Z)
2. beam.stl — sheet-metal C-channel beam (nests by sliding along its length)

Run with: /Users/ppg/.venv-stlpack/bin/python _gen_demos.py
"""
import numpy as np
from stl import mesh as stlmesh


def make_tapered_tote(out_path, L_bot=100.0, W_bot=60.0, L_top=160.0, W_top=120.0, H=60.0, t=3.0):
    """Open-top frustum shell. Slope 0.5 → pitch ≈ 2t/slope = 12 mm when nested."""
    # Inner frustum: shifted in by t on each side; floor at z=t
    L_bot_i, W_bot_i = L_bot - 2 * t, W_bot - 2 * t
    L_top_i, W_top_i = L_top - 2 * t, W_top - 2 * t

    outer = np.array([
        [-L_bot/2, -W_bot/2, 0], [ L_bot/2, -W_bot/2, 0],
        [ L_bot/2,  W_bot/2, 0], [-L_bot/2,  W_bot/2, 0],
        [-L_top/2, -W_top/2, H], [ L_top/2, -W_top/2, H],
        [ L_top/2,  W_top/2, H], [-L_top/2,  W_top/2, H],
    ], dtype=np.float64)
    inner = np.array([
        [-L_bot_i/2, -W_bot_i/2, t], [ L_bot_i/2, -W_bot_i/2, t],
        [ L_bot_i/2,  W_bot_i/2, t], [-L_bot_i/2,  W_bot_i/2, t],
        [-L_top_i/2, -W_top_i/2, H], [ L_top_i/2, -W_top_i/2, H],
        [ L_top_i/2,  W_top_i/2, H], [-L_top_i/2,  W_top_i/2, H],
    ], dtype=np.float64)
    verts = np.vstack([outer, inner])  # 16 verts; inner indices 8..15

    faces = []
    # Outer floor (z=0), face down
    faces += [[0, 2, 1], [0, 3, 2]]
    # Outer side walls (face outward)
    for a, b, c, d in [(0,1,5,4), (1,2,6,5), (2,3,7,6), (3,0,4,7)]:
        faces += [[a, b, c], [a, c, d]]
    # Inner side walls (face inward — reversed winding)
    for a, b, c, d in [(8,9,13,12), (9,10,14,13), (10,11,15,14), (11,8,12,15)]:
        faces += [[a, c, b], [a, d, c]]
    # Inner floor (z=t), face up
    faces += [[8, 9, 10], [8, 10, 11]]
    # Top rim (annular ring at z=H)
    for o0, o1, i0, i1 in [(4,5,12,13), (5,6,13,14), (6,7,14,15), (7,4,15,12)]:
        faces += [[o0, i0, i1], [o0, i1, o1]]

    faces = np.array(faces, dtype=np.int64)
    m = stlmesh.Mesh(np.zeros(len(faces), dtype=stlmesh.Mesh.dtype))
    for i, f in enumerate(faces):
        for j in range(3):
            m.vectors[i][j] = verts[f[j]]
    m.save(out_path)
    print(f"tray: wrote {out_path}  ({len(faces)} triangles)  outer {L_bot}x{W_bot} → {L_top}x{W_top}, h={H}, t={t}")


def make_c_channel(out_path, L=400.0, W=80.0, H=40.0, t=3.0):
    """Sheet-metal C-channel: floor + two walls, open top, length along Z.
    Two of these nest by sliding along Z; pitch ≈ t."""
    # Three boxes (floor, left wall, right wall) — overlapping slightly at corners is fine
    # for triangle-soup BVH testing.
    boxes = [
        # floor
        ([-W/2, 0, 0], [W/2, t, L]),
        # left wall
        ([-W/2, 0, 0], [-W/2 + t, H, L]),
        # right wall
        ([W/2 - t, 0, 0], [W/2, H, L]),
    ]
    all_faces = []
    all_verts = []
    base = 0
    for (lo, hi) in boxes:
        x0, y0, z0 = lo
        x1, y1, z1 = hi
        v = np.array([
            [x0, y0, z0], [x1, y0, z0], [x1, y1, z0], [x0, y1, z0],
            [x0, y0, z1], [x1, y0, z1], [x1, y1, z1], [x0, y1, z1],
        ])
        # 12 triangles for a box
        f = np.array([
            [0,1,2],[0,2,3],          # -Z
            [4,6,5],[4,7,6],          # +Z
            [0,5,1],[0,4,5],          # -Y
            [3,2,6],[3,6,7],          # +Y
            [0,3,7],[0,7,4],          # -X
            [1,5,6],[1,6,2],          # +X
        ]) + base
        all_verts.append(v)
        all_faces.append(f)
        base += 8
    verts = np.vstack(all_verts)
    faces = np.vstack(all_faces)
    m = stlmesh.Mesh(np.zeros(len(faces), dtype=stlmesh.Mesh.dtype))
    for i, f in enumerate(faces):
        for j in range(3):
            m.vectors[i][j] = verts[f[j]]
    m.save(out_path)
    # Center about origin in X/Y for nicer rendering
    print(f"beam: wrote {out_path}  ({len(faces)} triangles)  W={W} H={H} L={L} t={t}")


if __name__ == "__main__":
    import os
    here = os.path.dirname(os.path.abspath(__file__))
    # Tray: compact cup/tote (postal-tote shape). Pitch ≈ 12 mm.
    make_tapered_tote(
        os.path.join(here, "tray.stl"),
        L_bot=100, W_bot=60, L_top=160, W_top=120, H=60, t=3,
    )
    # Beam: elongated sheet-metal trough (only tapers in the cross-section width).
    # Pitch ≈ 8 mm in the height direction.
    make_tapered_tote(
        os.path.join(here, "beam.stl"),
        L_bot=600, W_bot=60, L_top=600, W_top=120, H=40, t=3,
    )
