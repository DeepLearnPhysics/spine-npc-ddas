# 01 - Run One SPINE Production Example

Goal: run one small `spine-prod` example on one LArCV file, then understand just enough provenance to know what file the next notebook is reading.

This is a terminal-oriented tutorial. Keep the live path to about 5 minutes: one dry run, plus an interactive command only if the instructor confirms the runtime is already ready.

Required input at EAF:

```text
/exp/dune/data/users/drielsma/npc-ddas/larcv/generic_test.root
```

The output should be a reconstructed SPINE HDF5 file. Notebook 2 can read that output, with the option to switch to pre-produced files under:

```text
/exp/dune/data/users/drielsma/npc-ddas/reco
```

Useful references while working:

- SPINE API browser: https://spine.readthedocs.io
- `spine-prod` README and `QUICKREF.md`
- production examples in `spine-prod/config/infer`
- Python helpers later in notebooks: `help(Driver)`, `dir(obj)`, `obj.as_dict().keys()`

## Required: Run One File

Use the pre-installed `spine-prod` checkout on EAF. Do not clone the repository or download weights during the live session.

```bash
cd /exp/dune/app/users/drielsma/spine-prod
source configure_eaf.sh
```

For reference, `configure_eaf.sh` does the EAF-specific runtime setup before sourcing the normal `spine-prod` configuration:

```bash
export SPINE_CONTAINER_RUNTIME_BIN=/cvmfs/oasis.opensciencegrid.org/mis/apptainer/current/bin/apptainer
export SPINE_CONTAINER_RUNTIME_ARGS="--env LD_PRELOAD= --env LC_ALL=C.UTF-8"
export SPINE_CONTAINER_PATH=/exp/dune/app/users/drielsma/spine/container/spine_latest.sif

source /exp/dune/app/users/drielsma/spine-prod/configure.sh
```

First do a dry run. This checks the config, source file, runtime profile, and generated job metadata without spending time on inference:

```bash
./submit.py \
  --config infer/generic/latest \
  --source /exp/dune/data/users/drielsma/npc-ddas/larcv/generic_test.root \
  --dry-run
```

Live questions:

- Which top-level config is being requested?
- Which input file is being reconstructed?
- Which SPINE container tag or image path would be used?
- Where would the job metadata and resolved config be written?

If the dry run looks correct and the instructor wants to run inference live, run the same file interactively through the configured container:

```bash
./submit.py -I \
  --interactive-runtime container \
  --config infer/generic/latest \
  --source /exp/dune/data/users/drielsma/npc-ddas/larcv/generic_test.root \
  --set base.world_size=0
```

The live session should stop here. The rest of this page is reference material for people who want to understand production more deeply.

## What To Record

For the file you just made, record:

- `spine-prod` git commit
- SPINE container version/tag and, where relevant, local `.sif` path
- top-level config request, for example `infer/generic/latest`
- exact command line
- input LArCV file
- output HDF5 file
- generated/resolved config path, if `submit.py` wrote one

That is the minimal provenance needed before opening the HDF5 file in Notebook 2.

## Optional: Production Runtime Model

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

## Optional: Request a GPU at EAF

If you need an interactive EAF GPU slot before running the command, use the current EAF GPU request procedure from the site documentation. Once the shell is on a GPU node, repeat the required setup:

```bash
cd /exp/dune/app/users/drielsma/spine-prod
source configure_eaf.sh
```

Then run the dry run first, followed by the interactive command only if the dry run resolves the expected config and source file.

## Optional: Run at NERSC

At NERSC/S3DF-style sites, the same production request should be expressed through a site profile rather than the EAF interactive path:

```bash
./submit.py \
  --config infer/generic/latest \
  --source /path/to/input.root \
  --profile s3df_ampere \
  --dry-run
```

For real campaigns, prefer source lists over ad hoc single-file commands:

```bash
./submit.py \
  --config infer/generic/latest \
  --source-list files.txt \
  --files-per-task 1 \
  --profile s3df_ampere \
  --dry-run
```

## Optional: Compose Configurations

Start from a top-level production config, for example:

```bash
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

Current shorthand requests also work:

```bash
./submit.py --config infer/generic/latest --source /path/to/input.root --dry-run
./submit.py --config infer/icarus/latest --source /path/to/input.root --dry-run
```

These generate a concrete composite config at submission time. That generated config is part of the production provenance.

## Optional: Overrides, Downloads, and Modifiers

Model components often include common defaults, then apply targeted dot-notation overrides:

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

Modifiers transform a base production request. For example, a data modifier might:

- remove truth parsers from `io.loader.dataset.schema`
- remove truth output products from `io.writer.keys`
- switch `build` and `post` processors to reco-only mode
- remove truth-matching processors

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

## Optional: `spine.config` Cheat Sheet

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
