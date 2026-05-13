# SPINE Short Tutorial Set

This is a compact tutorial sequence for a 3 hour SPINE session: a 45 minute lecture plus 2 hours and 15 minutes of hands-on work. It is distilled from `DeepLearnPhysics/spine-workshop-2026`, especially the HDF5 readback, PID, primary/vertex, and validation material, with a new production/configuration tutorial based on `DeepLearnPhysics/spine-prod`.

## Runtime

Expected container:

```bash
ghcr.io/deeplearnphysics/spine:latest
```

The notebooks assume reconstructed SPINE HDF5 files and companion LArCV files are available under a common tutorial directory. At FNAL/EAF the defaults are:

```python
LARCV_DATA_DIR = Path("/exp/dune/data/users/drielsma/npc-ddas/larcv")
HDF5_DATA_DIR = Path("/exp/dune/data/users/drielsma/npc-ddas/reco")
DETECTOR = "generic"
TAG = "tutorial"
```

The expected structure is:

```text
HDF5_DATA_DIR/DETECTOR/DETECTOR_TAG_spine.hdf5
LARCV_DATA_DIR/DETECTOR/DETECTOR_TAG.root
```

This is intentionally notebook-local rather than hidden in the Jupyter kernel launch script. It makes the EAF/Apptainer setup easier to inspect and lets students switch detector/tag/geometry explicitly.

Full inference production is intentionally not part of the timed exercise. The agenda includes only a short `spine-prod` smoke test so students see where reconstructed HDF5 files come from before the notebooks switch to pre-produced outputs.

## Recommended Agenda

The lecture slides are here: https://docs.google.com/presentation/d/1ddDAj8LcYOIF1xPD5DhmeozyJ2q7fRmwE1Bbrzekbrs/edit?usp=sharing

| Time | Segment | Material |
| --- | --- | --- |
| Before session | EAF setup | `00_eaf_setup.md` |
| 11:00-11:45 | Lecture | SPINE object hierarchy, DUNE use cases, performance benchmarks, production context |
| 11:45-11:55 | Reco smoke test | Short `spine-prod` dry-run or one-file demo after EAF setup |
| 11:55-12:30 | Notebook 1 | `notebooks/01_read_spine_output.ipynb` plus a short Spinal Tap teaser |
| 12:30-13:30 | Break | Lunch / reset |
| 13:30-14:05 | Notebook 2 | `notebooks/02_event_selection.ipynb` matching and validation |
| 14:05-14:40 | Notebook 3 | `notebooks/03_analysis_selection.ipynb` Michel mini-analysis |
| 14:40-14:55 | Production/config | `04_production_and_config.md` |
| 14:55-15:00 | Checklist | Production files, versions, metadata, next steps |

This keeps the lecture inside the first 90 minute block and leaves 2 hours and 15 minutes for hands-on work. If the session runs long, treat the reco smoke test and production/config material as guided demos, then move the deeper `spine-prod` details offline.

## Notebook Scope

0. `00_eaf_setup.md`
   EAF login, SPINE Apptainer Jupyter kernel setup, import check, shared tutorial data layout, optional Spinal Tap setup, and a short `spine-prod` reco smoke test.

1. `01_read_spine_output.ipynb`
   Opens a reconstructed HDF5 file with `spine.driver.Driver`, inspects `RecoParticle`, `TruthParticle`, `RecoInteraction`, and `TruthInteraction` objects, and builds small tables of object fields.

2. `02_event_selection.ipynb`
   Uses SPINE truth-matching products to study the ingredients of neutrino event selection by building PID and primary-ID confusion matrices plus a vertex-resolution diagnostic for a small number of entries.

3. `03_analysis_selection.ipynb`
   Builds a detector-agnostic Michel-electron candidate table from reconstructed particles using semantic shape, interaction membership, closest-track attachment, and truth matching when available.

4. `04_production_and_config.md`
   A terminal-oriented production tutorial: how `spine-prod` organizes detector configs, how to read `include` stacks and modifiers, how `spine.config` resolves `include`, `!include`, `!path`, `!download`, `override`, and removal operations, and how to dry-run or interactively test a production command.

## Source Material Reused

- `spine-workshop-2026/basics/inference/Inference_storage.ipynb`
- `spine-workshop-2026/reconstruction/michel/michel.ipynb`
- `spine-workshop-2026/reconstruction/PID/ParticleIdentification.ipynb`
- `spine-workshop-2026/reconstruction/vertex/Primary_and_Vertex.ipynb`
- `spine-prod/README.md`
- `spine-prod/QUICKREF.md`
- `spine-prod/config/infer/*`
- SPINE config documentation from the packaged/runtime SPINE release

The original workshop covers a week of material. This sequence deliberately leaves out training, detailed calorimetry, shower dE/dx, and full-chain inference so the session stays focused on reading and using SPINE analysis objects.

## Live vs Offline Work

Each notebook contains short live exercises that can be solved together in a few minutes. Longer adjacent-project prompts are explicitly marked as offline extensions. The intended live goal is competence with object inspection, simple selections, event-display debugging, and production config literacy, not statistical closure on reconstruction performance.

For an instructor-facing list of prompts, see `EXERCISES.md`.

## API Exploration

When a class, field, or helper is unfamiliar, use:

- the SPINE API browser: https://spine.readthedocs.io
- Python introspection: `help(obj)`, `dir(obj)`, `obj.as_dict().keys()`
- production examples in `spine-prod/config/infer`

The notebooks intentionally include cells that are worth reading line by line. The intended teaching style is interactive: predict what one line does, run it, inspect the object/table it returns, then decide what analysis question it enables.
