# 00 - EAF Setup

Goal: get a SPINE-capable Jupyter kernel running on Fermilab's Elastic Analysis Facility (EAF), then optionally enable Spinal Tap from the same Jupyter session. This should take no more than 15 minutes during the live session.

These notes are adapted from the SPINE @ EAF setup slides:

https://docs.google.com/presentation/d/1oInxVcidM0HIs-4MYzE_rpsjewSLHwtWbnaeQsICuvo/edit?slide=id.g3dfaf5ce87a_2_118#slide=id.g3dfaf5ce87a_2_118

## Prerequisites

- Fermilab services account
- FNAL network access, either on site or through the Fermilab VPN
- EAF portal access: https://eaf.fnal.gov/

The EAF documentation is here:

https://eafdocs.fnal.gov/master/index.html

## Start an EAF Server

1. Open https://eaf.fnal.gov/
2. Log in through the standard FNAL SSO page.
3. On the JupyterHub landing page, start a server.
4. For this tutorial setup check, select a CPU-only session unless instructed otherwise.
5. Scroll to the bottom and press **Start**.

The default EAF notebook environment does not include the full SPINE software stack. The tutorial notebooks should run in a Jupyter kernel that launches Python inside a SPINE Apptainer container.

## Create the SPINE Kernel

Open a terminal in EAF and run:

```bash
python -m ipykernel install \
  --name spine-apptainer-kernel \
  --display-name "SPINE Apptainer" \
  --user
```

Then copy the prepared kernel files:

```bash
cp /exp/dune/app/users/drielsma/spine/kernel/* \
   ~/.local/share/jupyter/kernels/spine-apptainer-kernel/
```

This installs a kernel named **SPINE Apptainer**. Select that kernel when running the tutorial notebooks.

## What the Kernel Does

The kernel launcher runs Python inside the SPINE Apptainer image. The important pieces are:

```bash
APPTAINER=/cvmfs/oasis.opensciencegrid.org/mis/apptainer/current/bin/apptainer
IMAGE=/exp/dune/app/users/drielsma/spine/container/spine_latest.sif
```

The launcher binds the file systems needed for the tutorial:

```bash
--bind /exp/dune
--bind ~
```

and clears environment settings that commonly interfere with the container:

```bash
--env LD_PRELOAD=
--env LC_ALL=C.UTF-8
```

It then starts:

```bash
python -m ipykernel_launcher "$@"
```

## Check the Kernel

Create a scratch notebook, select **SPINE Apptainer**, and run:

```python
import spine
print(spine.__file__)
```

If that imports successfully, the tutorial notebooks can use the same kernel.

## Tutorial Data

The notebooks expect the shared tutorial data layout:

```text
/exp/dune/data/users/drielsma/npc-ddas/larcv/generic_test.root
/exp/dune/data/users/drielsma/npc-ddas/reco/DETECTOR/SAMPLE_NAME_spine.h5
```

Tutorial 1 runs the single LArCV file above. Tutorial 2 and later notebooks read reconstructed HDF5 files. At the top of each notebook, choose:

```python
DETECTOR = "generic"
SAMPLE_NAME = "generic_test"
```

or another detector/sample pair provided for the session, for example `DETECTOR = "2x2"` and `SAMPLE_NAME = "2x2_numi"`.

## Optional: Spinal Tap on EAF

Spinal Tap is the event-display GUI used to inspect SPINE output.

Repository:

https://github.com/DeepLearnPhysics/spinal-tap

Hosted S3DF instance:

https://spinal-tap.slac.stanford.edu/

The hosted S3DF instance can access S3DF paths such as `/sdf/data/neutrino/...`. For EAF-local tutorial files under `/exp/dune/...`, use the EAF setup below.

Copy the prepared Jupyter server-proxy configuration:

```bash
cp /exp/dune/app/users/drielsma/spine/spinal-tap/jupyter_server_config.py \
   ~/.jupyter/
```

Then restart your EAF server:

1. Stop the current Jupyter server.
2. Start a new server.
3. Launch the **Spinal Tap** tile from the JupyterHub interface.

The EAF Spinal Tap launcher runs a separate Apptainer image:

```bash
IMAGE=/exp/dune/app/users/drielsma/spine/container/spinal-tap_latest.sif
```

and starts:

```bash
spinal-tap --host 0.0.0.0 --port "$PORT"
```

A useful smoke test is to load:

```text
/exp/dune/data/users/drielsma/npc-ddas/reco/2x2/2x2_numi_spine.h5
```

## If Something Fails

- If the SPINE import fails, confirm the notebook kernel is **SPINE Apptainer**, not the default Python kernel.
- If the kernel is missing, rerun the `ipykernel install` command and recopy the kernel files.
- If Spinal Tap is missing from the launcher, confirm `jupyter_server_config.py` was copied to `~/.jupyter/` and restart the EAF server.
- If files are not visible, check that the container binds include `/exp/dune`.
