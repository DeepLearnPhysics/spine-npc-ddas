"""Generate the compact SPINE tutorial notebooks."""

from __future__ import annotations

import json
from pathlib import Path


ROOT = Path(__file__).resolve().parent
NB_DIR = ROOT / "notebooks"


def md(source: str) -> dict:
    return {"cell_type": "markdown", "metadata": {}, "source": source.splitlines(True)}


def code(source: str) -> dict:
    return {
        "cell_type": "code",
        "execution_count": None,
        "metadata": {},
        "outputs": [],
        "source": source.splitlines(True),
    }


def notebook(cells: list[dict]) -> dict:
    return {
        "cells": cells,
        "metadata": {
            "kernelspec": {
                "display_name": "Python 3",
                "language": "python",
                "name": "python3",
            },
            "language_info": {"name": "python", "pygments_lexer": "ipython3"},
        },
        "nbformat": 4,
        "nbformat_minor": 5,
    }


COMMON_SETUP = r'''
from pathlib import Path

import matplotlib.pyplot as plt
import numpy as np
import pandas as pd
import yaml

from spine.driver import Driver

# Edit these two lines for the sample you want to inspect.
# DATA_PATH may be a single HDF5 file or a glob such as "/path/to/reco/*.h5".
DATA_PATH = "CHANGE_ME/reconstructed_spine_file.h5"

# Use None if no detector geometry is needed. Common examples:
# "icarus", "sbnd", "2x2", "nd-lar", "protodune-sp", "protodune-vd"
DETECTOR = None

CONFIG_CANDIDATES = [
    Path("../config/read_spine_hdf5.yaml"),
    Path("tutorials/config/read_spine_hdf5.yaml"),
]
CONFIG_PATH = next((path for path in CONFIG_CANDIDATES if path.exists()), None)

if DATA_PATH.startswith("CHANGE_ME"):
    raise RuntimeError(
        "Set DATA_PATH at the top of this notebook to the tutorial HDF5 file or file glob."
    )
if CONFIG_PATH is None:
    raise RuntimeError("Could not find tutorials/config/read_spine_hdf5.yaml")

cfg_text = CONFIG_PATH.read_text().replace("DATA_PATH", DATA_PATH)
cfg = yaml.safe_load(cfg_text)
if DETECTOR:
    cfg["geo"] = {"detector": DETECTOR}
driver = Driver(cfg)
print(f"Opened {DATA_PATH}")
print(f"Entries: {len(driver)}")
if DETECTOR:
    print(f"Detector geometry: {DETECTOR}")
'''


def write(name: str, cells: list[dict]) -> None:
    path = NB_DIR / name
    path.write_text(json.dumps(notebook(cells), indent=1) + "\n")


write(
    "01_read_spine_output.ipynb",
    [
        md(
            """# 01 - Reading SPINE Output

Goal: open a reconstructed SPINE HDF5 file, inspect the high-level object hierarchy, and connect particle/interactions fields to analysis questions.

This notebook is the highest-priority hands-on material for the short session. It is adapted from the 2026 workshop HDF5 readback material, with inference moved out of scope."""
        ),
        md(
            """## Runtime contract

Run inside `ghcr.io/deeplearnphysics/spine:latest`.

Set the file path in the first code cell:

```python
DATA_PATH = "/path/to/reconstructed_spine_file.h5"
DETECTOR = "icarus"  # or None
```

The file should contain reconstructed particles/interactions and, for validation cells, truth objects.
Use `DETECTOR = None` when detector geometry is not needed for the exercise."""
        ),
        code(COMMON_SETUP),
        md(
            """## Where to look things up

This tutorial deliberately pauses on small snippets. When a field or class is unfamiliar, use three complementary tools:

- Python introspection: `help(obj)`, `dir(obj)`, `obj.as_dict().keys()`
- The SPINE API browser: https://spine.readthedocs.io
- Source/config examples in `spine-prod`

The point is not to memorize every field. The point is to learn how to inspect the object model without guessing."""
        ),
        code(
            """ENTRY = 0
data = driver.process(entry=ENTRY)
print(data.keys())

reco_particles = data.get("reco_particles", [])
truth_particles = data.get("truth_particles", [])
reco_interactions = data.get("reco_interactions", [])
truth_interactions = data.get("truth_interactions", [])

print(f"Reco particles: {len(reco_particles)}")
print(f"Truth particles: {len(truth_particles)}")
print(f"Reco interactions: {len(reco_interactions)}")
print(f"Truth interactions: {len(truth_interactions)}")"""
        ),
        md(
            """## Inspect one object

SPINE objects expose Python attributes and usually an `as_dict()` method. Start by looking at one reconstructed particle and one reconstructed interaction.

Pause on the line `d = obj.as_dict()`: it is the fastest way to discover the analysis-facing fields saved in this file."""
        ),
        code(
            """def compact_dict(obj, max_items=40):
    if hasattr(obj, "as_dict"):
        d = obj.as_dict()
    else:
        d = vars(obj)
    rows = []
    for key, value in list(d.items())[:max_items]:
        if isinstance(value, np.ndarray):
            rows.append((key, f"array shape={value.shape} dtype={value.dtype}"))
        else:
            rows.append((key, repr(value)[:120]))
    return pd.DataFrame(rows, columns=["field", "value"])

if reco_particles:
    display(compact_dict(reco_particles[0]))
if reco_interactions:
    display(compact_dict(reco_interactions[0]))"""
        ),
        code(
            """# Try this on one object during the tutorial.
# help(reco_particles[0])
# dir(reco_particles[0])
# reco_particles[0].as_dict().keys()"""
        ),
        code(
            """PID_LABELS = {
    -1: "unknown",
    0: "photon",
    1: "electron",
    2: "muon",
    3: "pion",
    4: "proton",
    5: "kaon",
}

SHAPE_LABELS = {
    -1: "unknown",
    0: "shower",
    1: "track",
    2: "michel",
    3: "delta",
    4: "low-energy",
}

def particle_row(p):
    return {
        "id": getattr(p, "id", None),
        "interaction_id": getattr(p, "interaction_id", None),
        "pid": getattr(p, "pid", None),
        "pid_label": PID_LABELS.get(getattr(p, "pid", None), getattr(p, "pid", None)),
        "shape": getattr(p, "shape", None),
        "shape_label": SHAPE_LABELS.get(getattr(p, "shape", None), getattr(p, "shape", None)),
        "primary": getattr(p, "is_primary", None),
        "size": getattr(p, "size", None),
        "depositions_sum": getattr(p, "depositions_sum", np.nan),
        "start_point": getattr(p, "start_point", None),
        "end_point": getattr(p, "end_point", None),
    }

particle_df = pd.DataFrame([particle_row(p) for p in reco_particles])
particle_df"""
        ),
        code(
            """def interaction_row(ia):
    particles = getattr(ia, "particles", [])
    primary_particles = [p for p in particles if getattr(p, "is_primary", False)]
    return {
        "id": getattr(ia, "id", None),
        "nu_id": getattr(ia, "nu_id", None),
        "size": getattr(ia, "size", None),
        "vertex": getattr(ia, "vertex", None),
        "n_particles": len(particles),
        "n_primary": len(primary_particles),
        "primary_pids": [getattr(p, "pid", None) for p in primary_particles],
        "topology": getattr(ia, "topology", None),
    }

interaction_df = pd.DataFrame([interaction_row(ia) for ia in reco_interactions])
interaction_df"""
        ),
        md(
            """## Live exercise

Pick one interaction and answer:

- Which primary particles does SPINE reconstruct?
- Is the vertex close to the visually obvious interaction point?
- Which fields would you trust for a first-pass analysis selection, and which require validation?"""
        ),
        code(
            """from spine.vis.out import Drawer

drawer = Drawer(data)
fig = drawer.get("interactions", "id")
fig.show()"""
        ),
        md(
            """## Inference belongs in `spine-prod`

This short tutorial starts from HDF5 output. For real production, `spine-prod` should own the validated full-chain inference configs, model weights, campaign metadata, and file bookkeeping. That lets analysis notebooks stay focused on object interpretation and validation."""
        ),
        md(
            """## Offline extensions

- Repeat the field inspection for a second detector sample and list which object fields are detector-dependent.
- Build a small field glossary for the 10 particle/interactions attributes your analysis will use.
- Compare the same event in this notebook and Spinal Tap, then record which table fields explain the visual topology."""
        ),
    ],
)


write(
    "02_analysis_selection.ipynb",
    [
        md(
            """# 02 - Michel Electron Mini-Analysis

Goal: build a detector-agnostic Michel electron candidate table from reconstructed SPINE particles, estimate simple selection metrics when truth is available, and send interesting entries to Spinal Tap.

Michel electrons are useful here because the exercise is high-level and physics-facing, but still forces us to reason about SPINE object fields: particle shape, interaction membership, particle size, deposited charge, endpoints, matching, and topology."""
        ),
        code(COMMON_SETUP),
        md(
            """## Analysis idea

A Michel electron is an electron from a stopped muon decay. In reconstructed SPINE objects we will look for:

1. a particle with Michel semantic shape;
2. a track-like particle in the same interaction;
3. small spatial separation between the Michel points and the candidate parent track;
4. enough reconstructed points to avoid tiny fragments.

This is not a final detector-specific Michel selection. It is a compact analysis skeleton that works across detectors as long as the HDF5 file contains reconstructed particles."""
        ),
        code(
            """N_ENTRIES = min(len(driver), 50)
print(f"Scanning {N_ENTRIES} entries")"""
        ),
        code(
            """from spine.utils.globals import MICHL_SHP, TRACK_SHP, SHAPE_LABELS

print(f"Michel shape id: {MICHL_SHP} -> {SHAPE_LABELS[MICHL_SHP]}")
print(f"Track shape id:  {TRACK_SHP} -> {SHAPE_LABELS[TRACK_SHP]}")"""
        ),
        md(
            """## Pause on the distance function

The line `diff = a[:, None, :] - b[None, :, :]` builds all pairwise point differences between two particles. That gives us the closest approach between a Michel candidate and a track without relying on detector-specific geometry."""
        ),
        code(
            """def points(p):
    pts = getattr(p, "points", None)
    if pts is None:
        return np.empty((0, 3))
    return np.asarray(pts)

def min_point_distance(p1, p2):
    a = points(p1)
    b = points(p2)
    if len(a) == 0 or len(b) == 0:
        return np.inf
    diff = a[:, None, :] - b[None, :, :]
    return float(np.sqrt(np.sum(diff * diff, axis=-1)).min())

def deposition_sum(p):
    value = getattr(p, "depositions_sum", None)
    if value is not None:
        return float(value)
    depositions = getattr(p, "depositions", None)
    return float(np.sum(depositions)) if depositions is not None else np.nan"""
        ),
        code(
            """MUON_MIN_POINTS = 20
ATTACH_THRESHOLD_CM = 3.0
MICHEL_MIN_POINTS = 5
MATCH_THRESHOLD = 0.1

print({
    "muon_min_points": MUON_MIN_POINTS,
    "attach_threshold_cm": ATTACH_THRESHOLD_CM,
    "michel_min_points": MICHEL_MIN_POINTS,
    "match_threshold": MATCH_THRESHOLD,
})"""
        ),
        code(
            """def best_attached_track(candidate, particles):
    same_interaction_tracks = [
        p for p in particles
        if getattr(p, "interaction_id", -1) == getattr(candidate, "interaction_id", -2)
        and getattr(p, "shape", -1) == TRACK_SHP
        and getattr(p, "size", 0) >= MUON_MIN_POINTS
    ]
    if not same_interaction_tracks:
        return None, np.inf
    distances = [(track, min_point_distance(candidate, track)) for track in same_interaction_tracks]
    return min(distances, key=lambda item: item[1])

def best_truth_match(p):
    ids = list(getattr(p, "match_ids", []))
    overlaps = list(getattr(p, "match_overlaps", []))
    if not ids or not overlaps:
        return -1, 0.0
    index = int(np.argmax(overlaps))
    return ids[index], float(overlaps[index])

def michel_candidate_row(entry, p, particles):
    parent_track, attach_dist = best_attached_track(p, particles)
    match_id, match_overlap = best_truth_match(p)
    return {
        "entry": entry,
        "particle_id": getattr(p, "id", -1),
        "interaction_id": getattr(p, "interaction_id", -1),
        "size": getattr(p, "size", np.nan),
        "depositions_sum": deposition_sum(p),
        "is_contained": getattr(p, "is_contained", None),
        "attach_dist_cm": attach_dist,
        "attached_track_id": getattr(parent_track, "id", -1) if parent_track is not None else -1,
        "attached_track_size": getattr(parent_track, "size", np.nan) if parent_track is not None else np.nan,
        "match_id": match_id,
        "match_overlap": match_overlap,
        "is_truth_matched": match_overlap >= MATCH_THRESHOLD,
        "ke": getattr(p, "ke", np.nan),
    }"""
        ),
        md(
            """## Build the candidate table

Pause on `p.shape == MICHL_SHP`: this is where the high-level analysis becomes a SPINE-object query. Everything after that is ordinary table building."""
        ),
        code(
            """rows = []
true_rows = []

for entry in range(N_ENTRIES):
    data = driver.process(entry=entry)
    reco_particles = data.get("reco_particles", [])
    truth_particles = data.get("truth_particles", [])

    for p in reco_particles:
        if getattr(p, "shape", -1) == MICHL_SHP:
            rows.append(michel_candidate_row(entry, p, reco_particles))

    for tp in truth_particles:
        if getattr(tp, "shape", -1) == MICHL_SHP:
            match_id, match_overlap = best_truth_match(tp)
            true_rows.append({
                "entry": entry,
                "truth_particle_id": getattr(tp, "id", -1),
                "interaction_id": getattr(tp, "interaction_id", -1),
                "size": getattr(tp, "size", np.nan),
                "depositions_sum": deposition_sum(tp),
                "is_contained": getattr(tp, "is_contained", None),
                "match_id": match_id,
                "match_overlap": match_overlap,
                "is_reco_matched": match_overlap >= MATCH_THRESHOLD,
                "ke": getattr(tp, "ke", np.nan),
            })

candidate_columns = [
    "entry",
    "particle_id",
    "interaction_id",
    "size",
    "depositions_sum",
    "is_contained",
    "attach_dist_cm",
    "attached_track_id",
    "attached_track_size",
    "match_id",
    "match_overlap",
    "is_truth_matched",
    "ke",
]
truth_columns = [
    "entry",
    "truth_particle_id",
    "interaction_id",
    "size",
    "depositions_sum",
    "is_contained",
    "match_id",
    "match_overlap",
    "is_reco_matched",
    "ke",
]
candidates = pd.DataFrame(rows, columns=candidate_columns)
truth_michels = pd.DataFrame(true_rows, columns=truth_columns)

display(candidates.head())
display(truth_michels.head())"""
        ),
        code(
            """if len(candidates):
    candidates["passes_michel_selection"] = (
        (candidates["size"] >= MICHEL_MIN_POINTS)
        & (candidates["attach_dist_cm"] <= ATTACH_THRESHOLD_CM)
    )
else:
    candidates["passes_michel_selection"] = []

summary = candidates.groupby("passes_michel_selection").size().rename("n_reco_michel_candidates").to_frame()
summary"""
        ),
        code(
            """fig, axes = plt.subplots(1, 3, figsize=(13, 3))
if len(candidates):
    candidates["size"].hist(ax=axes[0], bins=30)
    candidates["attach_dist_cm"].replace(np.inf, np.nan).hist(ax=axes[1], bins=30)
    candidates["depositions_sum"].hist(ax=axes[2], bins=30)
axes[0].set_xlabel("Michel candidate points")
axes[1].set_xlabel("closest track distance [cm]")
axes[2].set_xlabel("candidate deposition sum")
plt.tight_layout()"""
        ),
        code(
            """selected = candidates[candidates["passes_michel_selection"]].copy()
selected.head(20)"""
        ),
        md(
            """## Truth metrics, if truth is available

These are intentionally simple counts. They are meant to start a discussion, not to certify a production performance number."""
        ),
        code(
            """n_pred = int(candidates["passes_michel_selection"].sum()) if len(candidates) else 0
n_pred_matched = int((candidates["passes_michel_selection"] & candidates["is_truth_matched"]).sum()) if len(candidates) else 0
n_true = len(truth_michels)
n_true_matched = int(truth_michels["is_reco_matched"].sum()) if len(truth_michels) else 0

purity = n_pred_matched / n_pred if n_pred else np.nan
efficiency = n_true_matched / n_true if n_true else np.nan

pd.DataFrame([{
    "selected_reco_michels": n_pred,
    "selected_truth_matched": n_pred_matched,
    "true_michels": n_true,
    "true_reco_matched": n_true_matched,
    "rough_purity": purity,
    "rough_efficiency": efficiency,
}])"""
        ),
        md(
            """## Spinal Tap handoff

The useful debugging output is a small list of selected candidates and suspicious failures:

- selected Michel candidates with large attachment distance;
- selected candidates with no truth match;
- true Michels with no reco match;
- high-charge candidates that fail the attachment cut."""
        ),
        code(
            """event_list = candidates.sort_values(
    ["passes_michel_selection", "is_truth_matched", "entry", "particle_id"],
    ascending=[False, True, True, True],
)
event_list[[
    "entry",
    "particle_id",
    "interaction_id",
    "passes_michel_selection",
    "is_truth_matched",
    "size",
    "attach_dist_cm",
    "attached_track_id",
    "depositions_sum",
]].to_csv("spinal_tap_michel_event_list.csv", index=False)
print("Wrote spinal_tap_michel_event_list.csv")
event_list.head(20)"""
        ),
        md(
            """## Live exercise

Choose one:

1. Change `ATTACH_THRESHOLD_CM` from 3 cm to 1 cm or 5 cm. What happens to the candidate count?
2. Raise `MICHEL_MIN_POINTS`. Which candidates disappear first?
3. Open one unmatched selected candidate in Spinal Tap. Is it a real Michel, a delta ray, a fragment, or a shower piece?
4. Open one true unmatched Michel in Spinal Tap. Was it missed by segmentation, clustering, or matching?"""
        ),
        md(
            """## Offline extensions

- Add a parent-muon stopping requirement using the track endpoint and nearby charge.
- Estimate a rough Michel energy spectrum from `depositions_sum` or `ke`, then compare matched reco and truth.
- Split efficiency by candidate size, containment, or detector region.
- Build a curated Spinal Tap list of five clean Michels and five failure modes.
- Try the same notebook on a second detector sample and identify which thresholds need retuning."""
        ),
    ],
)


write(
    "03_truth_validation.ipynb",
    [
        md(
            """# 03 - Truth Validation

Goal: validate the analysis-facing objects with matching, confusion matrices, and a simple vertex-resolution diagnostic.

This is the compressed version of the PID and primary/vertex validation notebooks from the full workshop."""
        ),
        code(COMMON_SETUP),
        code(
            """from sklearn.metrics import confusion_matrix

N_ENTRIES = min(len(driver), 100)
MATCH_THRESHOLD = 0.1
print(f"Validating {N_ENTRIES} entries with overlap threshold {MATCH_THRESHOLD}")"""
        ),
        code(
            """particle_rows = []
primary_rows = []
vertex_rows = []

for entry in range(N_ENTRIES):
    data = driver.process(entry=entry)

    pairs = data.get("particle_matches_t2r", [])
    overlaps = data.get("particle_matches_t2r_overlap", np.ones(len(pairs)))
    for i, (truth_p, reco_p) in enumerate(pairs):
        overlap = overlaps[i]
        if overlap < MATCH_THRESHOLD:
            continue
        if getattr(truth_p, "pid", -1) < 0 or getattr(reco_p, "pid", -1) < 0:
            continue
        particle_rows.append({
            "entry": entry,
            "overlap": overlap,
            "true_pid": truth_p.pid,
            "reco_pid": reco_p.pid,
            "true_primary": bool(getattr(truth_p, "is_primary", False)),
            "reco_primary": bool(getattr(reco_p, "is_primary", False)),
            "true_size": getattr(truth_p, "size", np.nan),
            "reco_size": getattr(reco_p, "size", np.nan),
            "true_nu_id": getattr(truth_p, "nu_id", -1),
        })
        primary_rows.append({
            "entry": entry,
            "truth": bool(getattr(truth_p, "is_primary", False)),
            "reco": bool(getattr(reco_p, "is_primary", False)),
            "overlap": overlap,
            "true_nu_id": getattr(truth_p, "nu_id", -1),
        })

    ia_pairs = data.get("interaction_matches_t2r", [])
    ia_overlaps = data.get("interaction_matches_t2r_overlap", np.ones(len(ia_pairs)))
    for i, (truth_ia, reco_ia) in enumerate(ia_pairs):
        overlap = ia_overlaps[i]
        if overlap < MATCH_THRESHOLD:
            continue
        if not hasattr(truth_ia, "vertex") or not hasattr(reco_ia, "vertex"):
            continue
        vertex_rows.append({
            "entry": entry,
            "truth_interaction_id": getattr(truth_ia, "id", -1),
            "reco_interaction_id": getattr(reco_ia, "id", -1),
            "overlap": overlap,
            "true_nu_id": getattr(truth_ia, "nu_id", -1),
            "vertex_distance_cm": float(np.linalg.norm(truth_ia.vertex - reco_ia.vertex)),
        })

particles = pd.DataFrame(particle_rows)
primaries = pd.DataFrame(primary_rows)
vertices = pd.DataFrame(vertex_rows)

display(particles.head())
display(vertices.head())"""
        ),
        code(
            """PID_LABELS = ["photon", "electron", "muon", "pion", "proton"]
valid_pid = particles.query("0 <= true_pid <= 4 and 0 <= reco_pid <= 4")

cm_counts = confusion_matrix(valid_pid["true_pid"], valid_pid["reco_pid"], labels=[0, 1, 2, 3, 4])
cm_norm = confusion_matrix(valid_pid["true_pid"], valid_pid["reco_pid"], labels=[0, 1, 2, 3, 4], normalize="true")

fig, ax = plt.subplots(figsize=(6, 5))
im = ax.imshow(cm_norm, vmin=0, vmax=1, cmap="Blues")
plt.colorbar(im, ax=ax, label="row-normalized fraction")
ax.set_xticks(range(5), PID_LABELS, rotation=45, ha="right")
ax.set_yticks(range(5), PID_LABELS)
ax.set_xlabel("reco PID")
ax.set_ylabel("true PID")
for i in range(5):
    for j in range(5):
        ax.text(j, i, f"{cm_norm[i, j]:.2f}\\n({cm_counts[i, j]})", ha="center", va="center", fontsize=8)
plt.tight_layout()"""
        ),
        code(
            """mpv_primary = primaries[primaries["true_nu_id"] > -1]
primary_counts = confusion_matrix(mpv_primary["truth"], mpv_primary["reco"], labels=[False, True])
primary_norm = confusion_matrix(mpv_primary["truth"], mpv_primary["reco"], labels=[False, True], normalize="true")

fig, ax = plt.subplots(figsize=(4, 4))
im = ax.imshow(primary_norm, vmin=0, vmax=1, cmap="Greens")
plt.colorbar(im, ax=ax, label="row-normalized fraction")
ax.set_xticks([0, 1], ["non-primary", "primary"], rotation=30, ha="right")
ax.set_yticks([0, 1], ["non-primary", "primary"])
ax.set_xlabel("reco")
ax.set_ylabel("truth")
for i in range(2):
    for j in range(2):
        ax.text(j, i, f"{primary_norm[i, j]:.2f}\\n({primary_counts[i, j]})", ha="center", va="center")
plt.tight_layout()"""
        ),
        code(
            """mpv_vertices = vertices[vertices["true_nu_id"] > -1]
fig, ax = plt.subplots(figsize=(6, 3))
mpv_vertices["vertex_distance_cm"].hist(ax=ax, bins=30)
ax.set_xlabel("truth-reco vertex distance [cm]")
ax.set_ylabel("matched interactions")
ax.grid(alpha=0.3)

bad_vertices = mpv_vertices.sort_values("vertex_distance_cm", ascending=False).head(10)
bad_vertices"""
        ),
        md(
            """## Live exercise

Pick one bad vertex or one PID confusion mode and send that `(entry, interaction_id)` back to Spinal Tap. Decide whether the problem is segmentation, fragmentation, interaction clustering, PID, primary ID, or vertexing."""
        ),
        md(
            """## Offline extensions

- Split PID confusion by particle length, deposited charge, containment, or detector module boundary.
- Build efficiency and purity curves for the selection in Notebook 2.
- Compare validation metrics before and after changing a production modifier or post-processing threshold.
- Turn one recurring failure mode into a short debugging note with event IDs and screenshots."""
        ),
        md(
            """## Real-analysis checklist

- Record the exact SPINE and `spine-prod` versions used to make the file.
- Keep the inference config, weight path or tag, detector geometry, and input file provenance.
- Validate object definitions before optimizing cuts.
- Keep event-display debugging tied to table rows; screenshots without entry IDs are not reproducible."""
        ),
    ],
)
