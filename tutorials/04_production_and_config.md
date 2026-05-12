# 04 - Production and Configuration

Goal: understand how `spine-prod` turns validated SPINE configurations into reproducible production jobs, and how the `spine.config` package composes those configurations.

This is a terminal-oriented tutorial rather than a notebook. The useful activity is reading config files, resolving what they mean, and dry-running production commands.

Useful references while working:

- SPINE API browser: https://spine.readthedocs.io
- `spine-prod` README and `QUICKREF.md`
- SPINE config docs in the installed/container SPINE package
- Python helpers: `help(load_config_file)`, `help(Driver)`, `dir(cfg_object)`

## Production Runtime Model

As of `spine-prod` 0.5.0+, production jobs no longer rely on a bundled SPINE git submodule as the normal runtime. Instead, `spine-prod` is the production orchestrator and SPINE itself is supplied by a tagged pre-packaged container image.

The default runtime is a SPINE image from:

```text
ghcr.io/deeplearnphysics/spine:<version>
```

For example, recent `spine-prod` releases default to a matching Shifter-style tag such as:

```bash
docker:ghcr.io/deeplearnphysics/spine:0.12.0
```

and a site-local Singularity/Apptainer image path such as:

```bash
/sdf/data/neutrino/images/spine_v0-12-0.sif
```

The container packages SPINE, OpT0Finder, and runtime dependencies. Batch jobs invoke the `spine` executable from inside the configured container.

The important environment variables are set by `source configure.sh` and can be overridden before sourcing:

```bash
export SPINE_CONTAINER_VERSION=0.12.0
export SPINE_CONTAINER_PATH=/path/to/spine_v0-12-0.sif
source configure.sh
```

Useful runtime variables:

- `SPINE_CONTAINER_VERSION`: container release version, without a leading `v`.
- `SPINE_CONTAINER_TAG`: registry image tag, typically `docker:ghcr.io/deeplearnphysics/spine:<version>`.
- `SPINE_CONTAINER_PATH`: local `.sif` image used by Singularity/Apptainer-capable sites.
- `SPINE_CONTAINER_RUNTIME_BIN`: optional explicit runtime executable, useful on EAF when Apptainer comes from CVMFS.
- `SPINE_CONTAINER_RUNTIME_ARGS`: optional extra Apptainer/Singularity flags.
- `SPINE_CONTAINER_PLATFORM`: Docker/Podman platform override for interactive fallback.

Live question: what should an analysis note record now: a SPINE git checkout, or the `spine-prod` commit plus the exact SPINE container version/tag?

## Live Exercise 1: Find the Config Stack

Start from a top-level production config, for example:

```bash
cd spine-prod
sed -n '1,80p' config/infer/generic/full_chain_240805.yaml
```

The important pattern is:

```yaml
include:
  - base/base_240718.yaml
  - io/io_240805.yaml
  - model/model_240805.yaml
  - post/post_240718.yaml
```

Read this as a versioned recipe:

- `base`: detector/build/runtime defaults
- `io`: input schema and output writer
- `model`: network architecture and weights
- `post`: post-processing, object builders, matching, and analysis-facing products

Live question: which file would you edit or override to change the input file list? Which file owns the model weights?

Current shorthand requests also work:

```bash
./submit.py --config infer/generic --source /path/to/input.root --dry-run
./submit.py --config infer/icarus/latest --source /path/to/input.root --dry-run
```

These generate a concrete composite config at submission time. That generated config is part of the production provenance.

## Live Exercise 2: Read an Override Block

Open a model component:

```bash
sed -n '1,120p' config/infer/generic/model/model_240805.yaml
```

The file includes common model defaults, then applies targeted dot-notation overrides:

```yaml
include: model_common.yaml

override:
  model.weight_path: !download
    url: https://...
    hash: ...
  model.modules.graph_spice.embedder.uresnet.spatial_size: 768
```

Key ideas:

- `include` loads a base config file and merges it first.
- `override` changes individual nested fields without copying the whole tree.
- Dot notation means `model.modules.graph_spice...` is edited in place.
- `!download` resolves to a cached local file path after downloading and hash-checking the remote asset.

Live question: why is this safer than pasting an absolute local checkpoint path into every production config?

## Live Exercise 3: Modifiers

Open a modifier:

```bash
sed -n '1,120p' config/infer/generic/modifier/data/mod_data_common.yaml
```

This kind of file transforms a simulation config into data mode:

- removes truth parsers from `io.loader.dataset.schema`
- removes truth output products from `io.writer.keys`
- switches `build` and `post` processors to reco-only mode
- removes truth-matching processors

The removal syntax is compact:

```yaml
override:
  io.loader.dataset.schema-:
    - seg_label
    - ppn_label
  model.network_input-: seg_label
  post-:
    - match
```

Live question: what would break if you ran a data file with an MC config that still expects truth labels?

## Live Exercise 4: Dry Run a Production Command

Use `submit.py --dry-run` to inspect what would be submitted without launching jobs:

```bash
./submit.py \
  --config infer/generic/latest \
  --source /path/to/input.root \
  --profile s3df_ampere \
  --dry-run
```

For a real small test, use interactive mode:

```bash
./submit.py -I \
  --config infer/generic/latest \
  --source /path/to/input.root
```

Interactive mode normally uses the `spine` executable on `PATH`. If that is unavailable, it can fall back to the configured container. You can force container-backed interactive execution:

```bash
./submit.py -I \
  --interactive-runtime container \
  --config infer/generic/latest \
  --source /path/to/input.root \
  --set base.world_size=0
```

On EAF, the Apptainer executable and extra runtime flags may need to be explicit:

```bash
export SPINE_CONTAINER_RUNTIME_BIN=/cvmfs/eaf.opensciencegrid.org/apptainer/bin/apptainer
export SPINE_CONTAINER_RUNTIME_ARGS="--env LD_PRELOAD= --env LC_ALL=C.UTF-8"
```

For local debugging against an unreleased SPINE checkout, `spine-prod` still has an escape hatch:

```bash
./submit.py \
  --spine-path /path/to/spine \
  -I --interactive-runtime local \
  --config infer/generic/latest \
  --source /path/to/input.root \
  --set base.world_size=0
```

That is a debugging path, not the default production model.

Useful production switches:

- `--source-list files.txt`: preferred for reproducible file lists
- `--files-per-task N`: group inputs into array tasks
- `--ntasks N`: cap job-array size
- `--apply-mods data lite`: compose config modifiers
- `--list-mods CONFIG`: inspect available modifiers
- `--preload`: resolve `!download` assets before job submission
- `--set key=value`: override SPINE config values at submission time
- `--interactive-runtime local|container`: choose local or container-backed interactive execution
- `--spine-path /path/to/spine`: use an unreleased checkout for debugging

## `spine.config` Cheat Sheet

Main entry point:

```python
from spine.config import load_config_file

cfg = load_config_file("config/infer/generic/full_chain_240805.yaml")
```

Core features:

- `include`: recursively load and merge config files in order.
- `!include`: inline-load a YAML fragment as a value.
- `!path`: resolve a path relative to the config file or `SPINE_CONFIG_PATH` without loading the file.
- `!download`: download a remote file, validate the optional SHA256 hash, cache it, and return the cached path.
- `override`: edit nested values using dot notation.
- `key+`: append to lists.
- `key-`: remove list entries or dictionary keys.
- `remove`: delete nested fields after includes are merged.
- `__meta__`: record version, description, compatibility, and component metadata.

Path resolution order:

1. absolute path, if it exists
2. path relative to the including config file
3. entries in `SPINE_CONFIG_PATH`
4. automatic `.yaml` / `.yml` extension retries

Download cache:

- default: `$SPINE_PROD_BASEDIR/.cache/weights` when using `spine-prod`
- override: `$SPINE_CACHE_DIR`

The `!download` cache handles model weights and other remote assets. This is separate from the SPINE software runtime, which production now gets from the configured container image.

## Production Checklist

Before accepting a production HDF5 file for analysis, preserve:

- `spine-prod` git commit
- SPINE container version/tag and, where relevant, local `.sif` path
- top-level config path and generated composite config, if modifiers/latest were used
- command line, profile, and source list
- model weight URL/hash or cached path
- input file provenance and detector geometry assumptions
- output HDF5 location and any skim/lite modifiers

## Offline Extensions

- Write a tiny modifier that changes only output writer keys to create an analysis-lite file.
- Compare `latest` composition with a pinned versioned config for one detector.
- Add a dry-run CI check that loads a config and preloads all `!download` assets.
- Build a one-page detector-specific production recipe for your analysis group.
