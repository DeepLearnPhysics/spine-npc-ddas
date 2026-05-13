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


SETUP_IMPORTS = r'''
# Standard Python/path tools for working with local files.
from pathlib import Path

# Analysis utilities used throughout the tutorials.
import matplotlib.pyplot as plt
import numpy as np
import pandas as pd
import yaml

# The Driver is the main SPINE entry point for reading one event at a time.
from spine.driver import Driver
'''

SETUP_SAMPLE_TEMPLATE = '''
# Prefer the shared DUNE path used in the workshop environment.
# Fall back to the repository-local tutorial assets when needed.
# We include both relative spellings because notebook kernels do not always
# start in the notebook directory.
DATA_ROOT_CANDIDATES = [
    Path("/exp/dune/data/users/drielsma/npc-ddas"),
    Path("../assets"),
    Path("tutorials/assets"),
]

# Pick the first location that actually exists on disk.
DATA_ROOT = next((path for path in DATA_ROOT_CANDIDATES if path.exists()), None)
if DATA_ROOT is None:
    raise RuntimeError("Could not find a workshop data directory.")

# The reco HDF5 files live under reco/ inside the chosen data root.
HDF5_DATA_DIR = DATA_ROOT / "reco"

# Edit these values to switch samples.
# The expected layout is:
#   reco/DETECTOR/SAMPLE_NAME_spine.h5
DETECTOR = "{detector}"
SAMPLE_NAME = "{sample_name}"

# GEOMETRY tells SPINE which detector geometry description to use.
# For this workshop we use the detector name directly.
GEOMETRY = {geometry_expr}
HDF5_FILE_NAME = f"{{SAMPLE_NAME}}_spine.h5"

# Build the final path to the reconstructed SPINE HDF5 file.
DATA_PATH = HDF5_DATA_DIR / DETECTOR / HDF5_FILE_NAME

print(f"Using data root: {{DATA_ROOT}}")
print(f"Reco file: {{DATA_PATH}}")
'''

SETUP_DRIVER = r'''
# As with the data paths, the notebook working directory can vary.
# These two candidates point to the same tutorial config from different cwd values.
CONFIG_CANDIDATES = [
    Path("../config/read_spine_hdf5.yaml"),
    Path("tutorials/config/read_spine_hdf5.yaml"),
]
CONFIG_PATH = next((path for path in CONFIG_CANDIDATES if path.exists()), None)

# Replace the DATA_PATH placeholder in the YAML template with the file we chose above.
DATA_PATH = str(DATA_PATH)
if CONFIG_PATH is None:
    raise RuntimeError("Could not find tutorials/config/read_spine_hdf5.yaml")

# Read the YAML as text first so we can substitute the concrete file path.
cfg_text = CONFIG_PATH.read_text().replace("DATA_PATH", DATA_PATH)

# Convert the YAML text into a normal Python dictionary.
cfg = yaml.safe_load(cfg_text)

# Some detector samples need an explicit geometry block so downstream code knows
# which detector layout and coordinate conventions to use.
if GEOMETRY:
    cfg["geo"] = {"detector": GEOMETRY}

# Create the SPINE driver. From this point on, driver.process(entry=...) reads events.
driver = Driver(cfg)
print(f"Opened {DATA_PATH}")
print(f"Entries: {len(driver)}")
if GEOMETRY:
    print(f"Detector geometry: {GEOMETRY}")
'''

def common_setup_cells(detector: str, sample_name: str, geometry_expr: str = "DETECTOR") -> list[dict]:
    setup_sample = SETUP_SAMPLE_TEMPLATE.format(
        detector=detector,
        sample_name=sample_name,
        geometry_expr=geometry_expr,
    )
    return [
        md(
            """## Step 1: import the tools for this notebook

This first code cell does not touch any data yet. It only imports the Python modules we will use later.

If an import fails, stop here. There is no point debugging later cells until this environment cell runs cleanly."""
        ),
        code(SETUP_IMPORTS),
        md(
            """## Step 2: choose the input file

This second code cell answers one question: which SPINE HDF5 file should the rest of the notebook read?

It looks for the shared workshop area first, then for the repository-local tutorial assets. It also defines the detector name and sample tag that control which file gets opened."""
        ),
        code(setup_sample),
        md(
            """## Step 3: build the SPINE driver from YAML

Now that the notebook knows which file to read, it loads the tutorial YAML config, injects the concrete file path, and creates a `Driver` object.

The geometry override in this step is important: it tells SPINE which detector geometry description to attach when the chosen sample needs one."""
        ),
        code(SETUP_DRIVER),
                md(
                        """## Config loading note: `safe_load` vs `load_config_file`

The setup cell above uses `yaml.safe_load` because this tutorial config is deliberately tiny: it reads one YAML template, replaces `DATA_PATH`, and creates a normal Python dictionary.

For real SPINE configuration work, prefer `spine.config.load_config_file`. That loader understands SPINE's config composition features, including `include`, `!include`, `!path`, `!download`, `override`, and removal operations. It is the better tool when you want to start from a production config and add or modify blocks in a notebook.

For example, you can load a base config and add a block from Python:

```python
cfg = load_config_file("/path/to/base_config.yaml")
cfg["geo"] = {"detector": DETECTOR}
cfg["ana"] = {"save": save_cfg}
driver = Driver(cfg)
```

If you prefer to express the same geometry change in YAML instead of Python, you can make that edit directly in the config layer:

```yaml
include: /path/to/base_config.yaml

geo:
    detector: DETECTOR
```

That YAML overlay is equivalent in spirit to loading the base config and then setting `cfg["geo"]` from Python.

Use `help(load_config_file)` when you want to explore its options interactively."""
                ),
    ]


def write(name: str, cells: list[dict]) -> None:
    path = NB_DIR / name
    path.write_text(json.dumps(notebook(cells), indent=1) + "\n")


write(
    "02_read_spine_output.ipynb",
    [
        md(
            """# 02 - Reading SPINE Output

Goal: open a reconstructed SPINE HDF5 file, inspect the high-level object hierarchy, and connect particle and interaction fields to analysis questions.

This notebook is the workshop on-ramp. It moves step by step through the basic SPINE object model and the main event-level collections."""
        ),
        md(
            """## Before you type anything

Start with this mental model:

- A SPINE output file is a collection of events.
- Each event contains a mixture of reconstructed objects and/or truth objects.
- The most common high-level objects are particles and interactions.
- A particle is one logical reconstructed physics object:
  - In the case of single track-like particles, it is all depositions associated with the same track.
  - In the case of shower-like particles, it is a collection of shower fragments that originate from the same primary particle.
- An interaction is a group of particles that belong together (originate from the same primary vertex).

You do not need to memorize the full object model. The goal is to learn how to inspect it easily."""
        ),
        md(
            """## Runtime contract

Run inside `ghcr.io/deeplearnphysics/spine:latest` (see `00_eaf_setup.md`).

Set the sample in the first code cell:

```python
DETECTOR = "2x2"
SAMPLE_NAME = "2x2_numi"
GEOMETRY = DETECTOR
```

The notebooks look for data in this order:

1. `/exp/dune/data/users/drielsma/npc-ddas`
2. `tutorials/assets`

Internally the code checks both `../assets` and `tutorials/assets` so the same repo-local fallback still works when the notebook kernel starts in a different working directory.

In either case they read:

```python
HDF5_DATA_DIR / DETECTOR / f"{SAMPLE_NAME}_spine.h5"
```

That keeps the workshop default aligned with the shared DUNE location while still allowing a repo-local fallback.

The HDF5 file should contain reconstructed particles and interactions and, for later validation, truth objects."""
        ),
        *common_setup_cells("2x2", "2x2_numi"),
        md(
            """## The config we are actually using

The driver is not magic. It is created from a YAML config. For this notebook we inspect it once, here, and later notebooks will refer back to this pattern instead of repeating the full dump.

Read this cell carefully. It tells you what the notebook is loading and which matching post-processors are enabled."""
        ),
        code(
            """print(cfg_text)

# If you prefer Python objects to raw YAML, inspect `cfg` as well.
cfg"""
        ),
        md(
            """## Where to look things up

When a field or class is unfamiliar, use three complementary tools:

- Python introspection: `help(obj)`, `dir(obj)`, `obj.as_dict().keys()`
- The SPINE API browser: https://spine.readthedocs.io
- Source and config examples in `spine-prod`

The point is not to memorize every field. The point is to learn how to inspect the object model without guessing."""
        ),
        md(
            """## Read one entry

Start with exactly one event entry. Before running the next cell, make a prediction:

1. What do you think `driver.process(...)` returns?
2. Do you expect a list, a dictionary, or one custom object?
3. What keys do you think will be present?"""
        ),
        code(
            """ENTRY = 0

# `driver.process` returns a dictionary of event-level data products.
data = driver.process(entry=ENTRY)"""
        ),
        code(
            """list(data)"""
        ),
        md(
            """Now pull out the four high-level collections we will use most often. Pause here and check the counts before inspecting individual objects.

If one collection is empty, that is not automatically a bug. It may just mean the file does not contain that category for this event."""
        ),
        code(
            """reco_particles = data.get("reco_particles", [])
truth_particles = data.get("truth_particles", [])
reco_interactions = data.get("reco_interactions", [])
truth_interactions = data.get("truth_interactions", [])"""
        ),
        code(
            """pd.DataFrame(
    {
        "collection": [
            "reco_particles",
            "truth_particles",
            "reco_interactions",
            "truth_interactions",
        ],
        "count": [
            len(reco_particles),
            len(truth_particles),
            len(reco_interactions),
            len(truth_interactions),
        ],
    }
)"""
        ),
        md(
            """## Inspect one object slowly

SPINE objects expose Python attributes and usually an `as_dict()` method. Start by looking at one reconstructed particle and one reconstructed interaction.

This is the moment where beginners usually start guessing field names. Do not guess. Inspect."""
        ),
        code(
            """particle = reco_particles[0]
interaction = reco_interactions[0]"""
        ),
        code(
            """type(particle), type(interaction)"""
        ),
        code(
            """# `as_dict()` gives a fast survey of what the object knows about itself.
list(particle.as_dict())"""
        ),
        code(
            """# Try one or more of these during the tutorial.
# help(particle)
# dir(particle)
# particle.as_dict().keys()
# interaction.as_dict().keys()"""
        ),
        code(
            """def preview_value(value):
    if isinstance(value, np.ndarray):
        return f"array shape={value.shape} dtype={value.dtype}"
    return repr(value)[:120]


def compact_dict(obj, max_items=25):
    if hasattr(obj, "as_dict"):
        mapping = obj.as_dict()
    else:
        mapping = vars(obj)
    rows = [(key, preview_value(value)) for key, value in list(mapping.items())[:max_items]]
    return pd.DataFrame(rows, columns=["field", "preview"])


compact_dict(particle)"""
        ),
        code(
            """compact_dict(interaction)"""
        ),
        md(
            """## Micro-exercise: ask the object questions

Use the previous output to answer these before moving on:

1. Which field appears to store the particle ID?
2. Which field appears to link a particle to an interaction?
3. Which field looks like a particle type prediction?
4. Which field looks energy-like or charge-like?

If you are not sure, test your guess with one tiny line of code."""
        ),
        code(
            """{
    "particle_id": getattr(particle, "id", None),
    "interaction_id": getattr(particle, "interaction_id", None),
    "pid": getattr(particle, "pid", None),
    "depositions_sum": getattr(particle, "depositions_sum", None),
}"""
        ),
        md(
            """## Use SPINE labels

Do not hard-code PID or semantic-shape labels in analysis notebooks. Import the labels from SPINE so the notebook follows the installed package."""
        ),
        code(
            """from spine.constants import PID_LABELS, SHAPE_LABELS"""
        ),
        code(
            """display(pd.Series(SHAPE_LABELS, name="shape label").to_frame())
display(pd.Series(PID_LABELS, name="PID label").to_frame())"""
        ),
        md(
            """## Build a first particle table

Pick a short list of fields first. This is the analysis contract you are choosing to rely on.

Notice how small this list is. In real analysis you almost never want every field at once."""
        ),
        code(
            """PARTICLE_FIELDS = [
    "id",
    "interaction_id",
    "pid",
    "shape",
    "is_primary",
    "size",
    "depositions_sum",
]

PARTICLE_FIELDS"""
        ),
        code(
            """# Build one row per reconstructed particle.
particle_df = pd.DataFrame(
    [{field: getattr(p, field, None) for field in PARTICLE_FIELDS} for p in reco_particles]
)
particle_df["pid_label"] = particle_df["pid"].map(PID_LABELS)
particle_df["shape_label"] = particle_df["shape"].map(SHAPE_LABELS)
particle_df"""
        ),
        md(
            """## Micro-exercise: answer real analysis questions

Try to answer each question with one or two lines of Python:

1. What is the PID label of the first reconstructed particle?
2. Which particles belong to the same interaction as that particle?
3. Which of those particles are marked primary?
4. Which column would you use as a first-pass energy or charge proxy?"""
        ),
        code(
            """first_interaction_id = particle_df.loc[0, "interaction_id"]
first_interaction_id"""
        ),
        code(
            """same_interaction_particles = particle_df.query("interaction_id == @first_interaction_id")
same_interaction_particles"""
        ),
        md(
            """## Build an interaction table

Interactions group particles. The next table summarizes multiplicities and primary content without forcing us to inspect every particle manually."""
        ),
        code(
            """def primary_particles(interaction):
    return [p for p in getattr(interaction, "particles", []) if getattr(p, "is_primary", False)]"""
        ),
        code(
            """interaction_df = pd.DataFrame(
    [
        {
            "id": getattr(ia, "id", None),
            "nu_id": getattr(ia, "nu_id", None),
            "size": getattr(ia, "size", None),
            "vertex": getattr(ia, "vertex", None),
            "n_particles": len(getattr(ia, "particles", [])),
            "n_primary": len(primary_particles(ia)),
            "primary_pids": [getattr(p, "pid", None) for p in primary_particles(ia)],
            "topology": getattr(ia, "topology", None),
        }
        for ia in reco_interactions
    ]
)
interaction_df"""
        ),
        md(
            """## Cross-check particle to interaction bookkeeping

The next cell answers a common beginner question: if a particle stores an `interaction_id`, can we recover the full interaction and compare the counts?"""
        ),
        code(
            """chosen_interaction_id = int(first_interaction_id)

interaction_df.query("id == @chosen_interaction_id")"""
        ),
        md(
            """## Live exercise

Pick one interaction and answer:

- Which primary particles does SPINE reconstruct?
- Is the vertex close to the visually obvious interaction point?
- If you wanted the total deposited charge for this interaction, would you sum particle-level values or read a field from the interaction object? Why?"""
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
- Build a small field glossary for the 10 particle and interaction attributes your analysis will use.
- Compare the same event in this notebook and Spinal Tap, then record which table fields explain the visual topology.
- Write one extra cell that computes the total `depositions_sum` for every interaction by grouping particles."""
        ),
    ],
)


write(
    "04_analysis_selection.ipynb",
    [
        md(
            """# 04 - Michel Electron Mini-Analysis

Goal: build a detector-agnostic Michel electron candidate table from reconstructed SPINE particles, estimate simple selection metrics when truth is available, and send interesting entries to Spinal Tap.

Notebook 1 introduced the YAML config and the object-inspection workflow. Here we build on that rather than repeating it.

This notebook builds an analysis table step by step, starting from small object-level questions and ending with a compact selection."""
        ),
        md(
            """## Physics story in one paragraph

A Michel electron is an electron from a stopped muon decay. In reconstructed SPINE objects, the key ingredients are:

1. a particle with Michel semantic shape;
2. a track-like particle in the same interaction;
3. small spatial separation between the Michel points and the candidate parent track;
4. enough reconstructed points to avoid tiny fragments.

This is not a final detector-specific Michel selection. It is a compact analysis skeleton that works across detectors as long as the HDF5 file contains reconstructed particles."""
        ),
        *common_setup_cells("2x2", "2x2_numi"),
        md(
            """## Reuse the setup from Notebook 1

    This notebook uses the same readback config as Notebook 1. The full YAML appears there.

The new work in this notebook is the analysis logic, not the file-loading logic."""
        ),
        code(
            """N_ENTRIES = min(len(driver), 50)
print(f"Scanning {N_ENTRIES} entries")"""
        ),
        code(
            """from spine.constants import MICHL_SHP, TRACK_SHP, SHAPE_LABELS

print(f"Michel shape id: {MICHL_SHP} -> {SHAPE_LABELS[MICHL_SHP]}")
print(f"Track shape id:  {TRACK_SHP} -> {SHAPE_LABELS[TRACK_SHP]}")"""
        ),
        md(
            """## Start with one event, not fifty

Before writing a batch loop, inspect one event and ask simpler questions:

1. Does this event contain any Michel-shaped particles?
2. If yes, which interaction do they belong to?
3. Is there a track-like particle in that same interaction?"""
        ),
        code(
            """EXAMPLE_ENTRY = 0
example = driver.process(entry=EXAMPLE_ENTRY)
example_particles = example.get("reco_particles", [])"""
        ),
        code(
            """example_particle_df = pd.DataFrame(
    [
        {
            "id": getattr(p, "id", -1),
            "interaction_id": getattr(p, "interaction_id", -1),
            "shape": getattr(p, "shape", -1),
            "shape_label": SHAPE_LABELS.get(getattr(p, "shape", -1), "unknown"),
            "size": getattr(p, "size", np.nan),
            "depositions_sum": getattr(p, "depositions_sum", np.nan),
        }
        for p in example_particles
    ]
)

example_particle_df.head(20)"""
        ),
        code(
            """example_michels = example_particle_df.query("shape == @MICHL_SHP")
example_michels"""
        ),
        md(
            """## Pause on the distance function

The line `diff = a[:, None, :] - b[None, :, :]` builds all pairwise point differences between two particles. That gives us the closest approach between a Michel candidate and a track without relying on detector-specific geometry.

If that NumPy expression feels unfamiliar, that is fine. Treat it as a utility function and focus on what goes in and what comes out."""
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
        md(
            """## Choose simple thresholds

These numbers are analysis choices, not universal truths. The point of the notebook is to make those choices visible and easy to change."""
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

Pause on `p.shape == MICHL_SHP`: this is where the high-level analysis becomes a SPINE-object query. Everything after that is ordinary table building.

Read the loop with this question in mind: which lines are SPINE-specific, and which lines are just normal Python and pandas?"""
        ),
        code(
            """rows = []
true_rows = []

for entry in range(N_ENTRIES):
    data = driver.process(entry=entry)
    reco_particles = data.get("reco_particles", [])
    truth_particles = data.get("truth_particles", [])

    # First collect reconstructed Michel candidates.
    for p in reco_particles:
        if getattr(p, "shape", -1) == MICHL_SHP:
            rows.append(michel_candidate_row(entry, p, reco_particles))

    # Then collect truth Michels so we can estimate rough efficiency.
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
            })"""
        ),
        code(
            """candidate_columns = [
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
        md(
            """## Micro-exercise: interrogate one candidate row

Pick one row from `candidates` and answer:

1. What interaction does it belong to?
2. What track did we attach it to?
3. Is the attachment distance small or large?
4. If truth is available, does the best overlap look convincing?"""
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
            """## SPINE-native CSV export

The derived Michel table above is useful for teaching and for quick iteration. But when you want to dump raw SPINE object information to CSV, use SPINE's save analysis script instead of hand-writing lots of export code.

This is a good division of labor:

- use normal notebook code for derived quantities such as `attach_dist_cm` or custom selections;
- use the save script for standard object attributes that already exist on particles and interactions."""
        ),
        code(
            """# This config is a compact example of what you could put in a standalone YAML file.
save_cfg = {
    "save": {
        "obj_type": ["particle", "interaction"],
        "run_mode": "both",
        "match_mode": "both",
        "overwrite": True,
        "particle": [
            "id",
            "interaction_id",
            "pid",
            "shape",
            "size",
            "depositions_sum",
            "is_primary",
        ],
        "interaction": [
            "id",
            "nu_id",
            "size",
            "topology",
            "vertex",
        ],
    }
}

print(yaml.safe_dump({"ana": save_cfg}, sort_keys=False))"""
        ),
        code(
            """from spine.ana.manager import AnaManager

SAVE_OUTPUT_DIR = Path("save_demo_output")
SAVE_OUTPUT_DIR.mkdir(exist_ok=True)

save_manager = AnaManager(save_cfg, log_dir=str(SAVE_OUTPUT_DIR))
# Run the save script on a small sample first so the output stays easy to inspect.
for entry in range(min(10, len(driver))):
    save_manager(driver.process(entry=entry))
save_manager.close()

sorted(path.name for path in SAVE_OUTPUT_DIR.glob("save_*.csv"))"""
        ),
        code(
            """saved_particles = pd.read_csv(SAVE_OUTPUT_DIR / "save_reco_particles.csv")
saved_particles.head()"""
        ),
        md(
            """## Spinal Tap handoff

The useful debugging output is a small list of selected candidates and suspicious failures:

- selected Michel candidates with large attachment distance;
- selected candidates with no truth match;
- true Michels with no reco match;
- high-charge candidates that fail the attachment cut.

This CSV is still custom because it stores derived quantities from our notebook selection logic, not just raw SPINE object attributes."""
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
4. Open one true unmatched Michel in Spinal Tap. Was it missed by segmentation, clustering, or matching?
5. Compare one row from `saved_particles` with one row from `candidates`. Which columns came directly from SPINE, and which ones did we derive ourselves?"""
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
    "03_event_selection.ipynb",
    [
        md(
            """# 03 - Event Selection

Goal: study the ingredients that drive neutrino event selection by checking PID, primary labeling, vertex quality, and matching-based diagnostics on a realistic sample.

Notebook 1 covered SPINE object inspection. Notebook 2 turned those objects into analysis tables. This notebook shifts to the question most people actually care about in practice: can you trust the objects well enough to build a neutrino event selection?"""
        ),
        md(
            """## What you should already know

This notebook reuses the same file-loading setup as Notebook 1, without repeating the full YAML.

It defaults to the `nd-lar_lbnf` sample rather than `2x2_numi` because this detector/sample pair is a better place to discuss neutrino event-selection ingredients such as PID, primaries, and vertex quality.

The new concepts here are:

- truth-to-reco matching;
- overlap thresholds;
- confusion matrices;
- simple validation plots that tell you where to look next."""
        ),
        *common_setup_cells("nd-lar", "nd-lar_lbnf"),
        code(
            """from sklearn.metrics import confusion_matrix

N_ENTRIES = min(len(driver), 100)
MATCH_THRESHOLD = 0.1
print(f"Validating {N_ENTRIES} entries with overlap threshold {MATCH_THRESHOLD}")"""
        ),
        md(
            """## Sanity-check one event first

Before aggregating many events, inspect one event and ask:

1. Are there matched particle pairs at all?
2. Are there matched interaction pairs at all?
3. What does the overlap value look like for this event?"""
        ),
        code(
            """ENTRY = 0
example = driver.process(entry=ENTRY)

particle_pairs = example.get("particle_matches_t2r", [])
particle_overlaps = example.get("particle_matches_t2r_overlap", np.ones(len(particle_pairs)))
interaction_pairs = example.get("interaction_matches_t2r", [])
interaction_overlaps = example.get("interaction_matches_t2r_overlap", np.ones(len(interaction_pairs)))"""
        ),
        code(
            """pd.DataFrame(
    {
        "collection": ["particle_matches_t2r", "interaction_matches_t2r"],
        "count": [len(particle_pairs), len(interaction_pairs)],
        "max_overlap": [
            float(np.max(particle_overlaps)) if len(particle_overlaps) else np.nan,
            float(np.max(interaction_overlaps)) if len(interaction_overlaps) else np.nan,
        ],
    }
)"""
        ),
        md(
            """## Build validation tables

The next cell converts matched objects into four ordinary tables:

- one row per matched particle pair;
- one row per matched primary-label comparison;
- one row per matched interaction pair for event-class validation;
- one row per matched interaction pair for vertex validation.

Once the tables exist, the rest of the notebook is mostly pandas and plotting."""
        ),
        code(
            """particle_rows = []
primary_rows = []
interaction_rows = []
vertex_rows = []


def interaction_class(interaction):
    # In this tutorial we collapse neutrino interactions into three categories:
    #   CC numu: at least one primary muon
    #   CC nue:  at least one primary electron
    #   NC nu:   no primary lepton
    primary_pids = {
        getattr(p, "pid", -1)
        for p in getattr(interaction, "particles", [])
        if getattr(p, "is_primary", False)
    }
    if 2 in primary_pids:
        return "CC numu"
    if 1 in primary_pids:
        return "CC nue"
    return "NC nu"

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
        interaction_rows.append({
            "entry": entry,
            "truth_interaction_id": getattr(truth_ia, "id", -1),
            "reco_interaction_id": getattr(reco_ia, "id", -1),
            "overlap": overlap,
            "true_nu_id": getattr(truth_ia, "nu_id", -1),
            "true_class": interaction_class(truth_ia),
            "reco_class": interaction_class(reco_ia),
        })
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
interactions = pd.DataFrame(interaction_rows)
vertices = pd.DataFrame(vertex_rows)

display(particles.head())
display(interactions.head())
display(vertices.head())"""
        ),
        md(
            """## Ask simple questions before plotting

Before reading the confusion matrix, check that you understand the table columns:

1. Which columns come from truth?
2. Which columns come from reconstruction?
3. Which columns are bookkeeping or metadata?
4. Which filters below are removing unmatched or non-neutrino entries?"""
        ),
        code(
            """from spine.constants import PID_LABELS

PID_LABELS = [PID_LABELS[i] for i in range(5)]
valid_pid = particles.query("0 <= true_pid <= 4 and 0 <= reco_pid <= 4")

cm_counts = confusion_matrix(valid_pid["true_pid"], valid_pid["reco_pid"], labels=[0, 1, 2, 3, 4])
cm_norm = confusion_matrix(
    valid_pid["true_pid"],
    valid_pid["reco_pid"],
    labels=[0, 1, 2, 3, 4],
    normalize="true",
)

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
        md(
            """## Primary-particle validation

Here we restrict to neutrino-associated truth particles as a very simple slice of the dataset. That is what the `true_nu_id > -1` cut is doing."""
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
        md(
            """## Vertex-resolution diagnostic

This is intentionally simple: for matched truth and reco interactions, compute the distance between the two vertices and look at the tail."""
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
            """## Neutrino event-class confusion matrix

For event selection, a very common first question is whether SPINE gets the broad interaction class right.

Here we collapse matched neutrino interactions into three bins:

- `CC numu`: one or more primary muons;
- `CC nue`: one or more primary electrons;
- `NC nu`: no primary lepton.

This is a compact diagnostic to follow up in the event display once you have already looked at the vertex behavior."""
        ),
        code(
            """EVENT_CLASS_LABELS = ["CC numu", "CC nue", "NC nu"]

nu_interactions = interactions[interactions["true_nu_id"] > -1]
event_counts = confusion_matrix(
    nu_interactions["true_class"],
    nu_interactions["reco_class"],
    labels=EVENT_CLASS_LABELS,
)
event_norm = confusion_matrix(
    nu_interactions["true_class"],
    nu_interactions["reco_class"],
    labels=EVENT_CLASS_LABELS,
    normalize="true",
)

fig, ax = plt.subplots(figsize=(5, 4))
im = ax.imshow(event_norm, vmin=0, vmax=1, cmap="Purples")
plt.colorbar(im, ax=ax, label="row-normalized fraction")
ax.set_xticks(range(3), EVENT_CLASS_LABELS, rotation=30, ha="right")
ax.set_yticks(range(3), EVENT_CLASS_LABELS)
ax.set_xlabel("reco event class")
ax.set_ylabel("truth event class")
for i in range(3):
    for j in range(3):
        ax.text(j, i, f"{event_norm[i, j]:.2f}\\n({event_counts[i, j]})", ha="center", va="center", fontsize=9)
plt.tight_layout()"""
        ),
        md(
            """## Live exercise

Pick one bad vertex or one PID confusion mode and send that event back to Spinal Tap. Then decide what kind of failure you are looking at:

- segmentation;
- fragmentation;
- interaction clustering;
- PID;
- primary labeling;
- vertexing.

The important shift here is from counting mistakes to diagnosing mistakes."""
        ),
        md(
            """## Offline extensions

- Split PID confusion by particle length, deposited charge, containment, or detector module boundary.
- Build efficiency and purity curves for the selection in Notebook 4.
- Compare validation metrics before and after changing a production modifier or post-processing threshold.
- Turn one recurring failure mode into a short debugging note with event IDs and screenshots."""
        ),
    ],
)

legacy_notebook = NB_DIR / "03_truth_validation.ipynb"
if legacy_notebook.exists():
    legacy_notebook.unlink()
