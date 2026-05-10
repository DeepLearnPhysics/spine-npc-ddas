# SPINE Short Tutorial Set

This is a compact tutorial sequence for a 2 to 2.5 hour hands-on block after a general SPINE introduction. It is distilled from `DeepLearnPhysics/spine-workshop-2026`, especially the HDF5 readback, PID, primary/vertex, and validation material, with a new production/configuration tutorial based on `DeepLearnPhysics/spine-prod`.

## Runtime

Expected container:

```bash
ghcr.io/deeplearnphysics/spine:latest
```

The notebooks assume a reconstructed SPINE HDF5 file is already available. On EAF, set:

```bash
export SPINE_TUTORIAL_H5=/path/to/reconstructed_spine_file.h5
```

Inference is intentionally not part of the timed exercise. The first notebook includes a short discussion cell pointing to `spine-prod` as the production layer that owns validated inference configs, model weights, and campaign bookkeeping.

## Recommended Agenda

| Time | Segment | Material |
| --- | --- | --- |
| 0:00-0:30 | Lecture intro | SPINE object hierarchy, DUNE use cases, common failure modes |
| 0:30-1:05 | Notebook 1 | `notebooks/01_read_spine_output.ipynb` |
| 1:05-1:25 | Spinal Tap teaser | Event display from the same HDF5 file |
| 1:25-1:35 | Break / reset | Leave time for environment issues |
| 1:35-2:10 | Notebook 2 | `notebooks/02_analysis_selection.ipynb` Michel mini-analysis |
| 2:10-2:35 | Spinal Tap debugging | Open selected/failing events from Notebook 2 |
| 2:35-2:55 | Production/config | `04_production_and_config.md` |
| 2:55-3:10 | Truth validation teaser | `notebooks/03_truth_validation.ipynb`, first two plots only |
| 3:10-3:15 | Checklist | Production files, versions, metadata, next steps |

If the hands-on block is closer to 2 hours, treat Notebook 3 as an offline extension and keep only the production/config overview plus one validation plot.

## Notebook Scope

1. `01_read_spine_output.ipynb`
   Opens a reconstructed HDF5 file with `spine.driver.Driver`, inspects `RecoParticle`, `TruthParticle`, `RecoInteraction`, and `TruthInteraction` objects, and builds small tables of object fields.

2. `02_analysis_selection.ipynb`
   Builds a detector-agnostic Michel-electron candidate table from reconstructed particles using semantic shape, interaction membership, closest-track attachment, and truth matching when available.

3. `03_truth_validation.ipynb`
   Uses SPINE truth-matching products to build PID and primary-ID confusion matrices plus a vertex-resolution diagnostic for a small number of entries.

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
- `spine-prod/spine/src/spine/config/README.md`

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
