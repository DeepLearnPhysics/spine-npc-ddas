# Exercise Menu

Use this as the instructor-facing menu of things participants can solve during the live session or take offline.

## Pre-Session Check

### 00: EAF Setup

- Confirm the notebook kernel is **SPINE Apptainer**.
- Run `import spine` and identify which container path Python is using.
- Confirm `/exp/dune/data/users/drielsma/npc-ddas` is visible from the kernel.

## Live Exercises

### 01: One-File Production

- Run the `generic_test.root` production command interactively and identify the config, source file, container image, and local `jobs/` directory.
- Find the output HDF5 path that Notebook 2 should open.
- Explain why full production campaigns are not being run inside the tutorial timing.

### Notebook 2: Reading SPINE Output

- Inspect one `RecoParticle` with `as_dict()`. Pick three fields and explain what each one means physically.
- Use `help(reco_particles[0])` and the RTD API browser to find where one field is documented.
- Build a one-row summary for one `RecoInteraction`: particle count, primary count, vertex, topology, and primary PIDs.
- Open the same entry in Spinal Tap and connect one visual feature to one table field.

### Notebook 3: Matching and Validation

- Build one PID confusion matrix and identify the dominant confusion mode.
- Inspect one bad vertex candidate in Spinal Tap and decide whether the table diagnostic matches what you see visually.
- Change `MATCH_THRESHOLD` and explain how the matched-pair counts change.
- Pick one event-class confusion and identify whether PID, primary labeling, or clustering drove the mistake.

### Notebook 4: Michel Mini-Analysis

- Change `ATTACH_THRESHOLD_CM` from 3 cm to 1 cm or 5 cm and explain how the candidate count changes.
- Raise `MICHEL_MIN_POINTS` and identify what kind of candidates disappear first.
- Open one selected candidate with no truth match in Spinal Tap and classify the failure mode.
- Open one true Michel with no reco match and decide whether it is a segmentation, clustering, matching, or threshold problem.

### Optional Production and Config

- Trace one top-level config through its `include` files and identify which component owns IO, weights, and post-processing.
- Find a `!download` weight and explain where it will be cached.
- Read a `data` or `lite` modifier and list exactly what it removes.
- Write down which `spine.config` feature you would use for a small local override versus a reusable production modifier.

## Offline Extensions

- Turn the Michel mini-analysis into a detector-specific calibration note with tuned thresholds.
- Add a parent-muon stopping requirement using the distance between the candidate and a track endpoint.
- Estimate a Michel energy spectrum using `depositions_sum` or `ke` and compare matched reco/truth distributions.
- Split Michel efficiency by containment, candidate size, detector region, or module boundary.
- Build a curated Spinal Tap gallery of clean Michels and recurring failure modes.
- Write a small `spine-prod` modifier that makes an analysis-lite output file.
- Compare a `latest` production config to a pinned versioned config and document what changed.
- Add a CI-style config check that loads a config and preloads all `!download` assets.
