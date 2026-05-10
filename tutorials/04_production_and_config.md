# 04 - Production and Configuration

Goal: understand how `spine-prod` turns validated SPINE configurations into reproducible production jobs, and how the `spine.config` package composes those configurations.

This is a terminal-oriented tutorial rather than a notebook. The useful activity is reading config files, resolving what they mean, and dry-running production commands.

Useful references while working:

- SPINE API browser: https://spine.readthedocs.io
- Local config docs in `spine-prod/spine/src/spine/config/README.md`
- Python helpers: `help(load_config_file)`, `help(Driver)`, `dir(cfg_object)`

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
  --config infer/generic/full_chain_240805.yaml \
  --source /path/to/input.root \
  --profile s3df_ampere \
  --dry-run
```

For a real small test, use interactive mode:

```bash
./submit.py -I \
  --config infer/generic/full_chain_240805.yaml \
  --source /path/to/input.root
```

Useful production switches:

- `--source-list files.txt`: preferred for reproducible file lists
- `--files-per-task N`: group inputs into array tasks
- `--ntasks N`: cap job-array size
- `--apply-mods data lite`: compose config modifiers
- `--list-mods CONFIG`: inspect available modifiers
- `--preload`: resolve `!download` assets before job submission

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
- fallback: `$SPINE_BASEDIR/.cache/weights`
- override: `$SPINE_CACHE_DIR`

## Production Checklist

Before accepting a production HDF5 file for analysis, preserve:

- `spine-prod` git commit
- bundled SPINE submodule commit or SPINE package version
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
