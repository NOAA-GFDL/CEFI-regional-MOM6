#!/bin/bash
# Git bisect test script for CEFI-regional-MOM6 experiments
#
# Intended for tracking answer-changing commits in MOM6. For each commit
# git bisect checks out, this script:
#   1. Optionally merges a CEFI base commit on top of the checked-out commit
#      so that CEFI-specific prerequisites are always present
#   2. Builds MOM6SIS2 using the docker/linux-intel container settings
#   3. Runs the 48hr test for the specified experiment
#   4. Compares ocean.stats against a reference copy
#   5. Resets back to the original HEAD so git bisect can continue
#   6. Exits with a code git bisect understands
#
# Exit codes:
#   0   – good commit (ocean.stats matches reference)
#   1   – bad  commit (ocean.stats differs from reference)
#   125 – skip this commit (build or run failed)
#
# Usage (run from src/MOM6/ via git bisect run):
#   git bisect run ../../builds/bisect-test.sh \
#       -e <experiment> \
#       -r /path/to/reference \
#       -n <ntasks> \
#       [-b <cefi_base_commit>]
#
# Required arguments:
#   -e  Experiment directory name (relative to exps/, e.g. NEP10.COBALT or NWA12.COBALT)
#   -r  Path to the directory containing the reference ocean.stats file
#   -n  Number of MPI tasks for srun (must match the layout in input.nml_48hr)
#
# Optional arguments:
#   -b  CEFI base commit to merge on top of each bisect candidate before
#       building.  Use this when bisecting a dev/gfdl commit range that was
#       merged into dev/cefi, to ensure CEFI-specific commits are always
#       present.  The script resets back to the original HEAD after each test.
#
# Typical setup when the answer change arrived via a dev/gfdl → dev/cefi merge:
#
#   BAD_MERGE=<bad dev/cefi merge commit>
#   GOOD_MERGE=<good dev/cefi merge commit>
#
#   git bisect start
#   git bisect bad  $(git rev-parse ${BAD_MERGE}^2)   # dev/gfdl tip at bad merge
#   git bisect good $(git rev-parse ${GOOD_MERGE}^2)  # dev/gfdl tip at good merge
#   git bisect run ../../builds/bisect-test.sh \
#       -e <experiment> \
#       -r /path/to/reference \
#       -n <ntasks> \
#       -b $(git rev-parse ${GOOD_MERGE}^1)            # dev/cefi base before good merge
#
# See builds/README_bisect.md for full setup instructions and per-experiment
# ntasks values.

set -euo pipefail

# ---------------------------------------------------------------------------
# Argument parsing
# ---------------------------------------------------------------------------
EXP_NAME=""
REF_DIR=""
NTASKS=""
CEFI_BASE=""

usage() {
    echo "Usage: $0 -e <experiment_name> -r <reference_dir> -n <ntasks> [-b <cefi_base_commit>]"
    echo "  -e  Experiment name (subdirectory of exps/, e.g. NEP10.COBALT or NWA12.COBALT)"
    echo "  -r  Path to reference directory containing ocean.stats"
    echo "  -n  Number of MPI tasks for srun (must match layout in input.nml_48hr)"
    echo "  -b  (optional) CEFI base commit to merge before building"
    exit 125
}

while getopts "e:r:n:b:h" opt; do
    case "$opt" in
        e) EXP_NAME="$OPTARG" ;;
        r) REF_DIR="$OPTARG" ;;
        n) NTASKS="$OPTARG" ;;
        b) CEFI_BASE="$OPTARG" ;;
        h) usage ;;
        *) usage ;;
    esac
done

if [[ -z "$EXP_NAME" || -z "$REF_DIR" || -z "$NTASKS" ]]; then
    echo "ERROR: -e, -r, and -n are required."
    usage
fi

# ---------------------------------------------------------------------------
# Paths (all derived from this script's location so they work regardless of
# where git bisect was started from)
# ---------------------------------------------------------------------------
SCRIPT_DIR=$(cd "$(dirname "$0")" && pwd)   # builds/
REPO_ROOT=$(cd "$SCRIPT_DIR/.." && pwd)     # repo root
MOM6_DIR="$REPO_ROOT/src/MOM6"
EXP_DIR="$REPO_ROOT/exps/$EXP_NAME"
BINARY="$SCRIPT_DIR/build/docker-linux-intel/ocean_ice/repro/MOM6SIS2"

if [[ ! -d "$EXP_DIR" ]]; then
    echo "ERROR: Experiment directory not found: $EXP_DIR"
    exit 125
fi

if [[ ! -f "$REF_DIR/ocean.stats" ]]; then
    echo "ERROR: Reference ocean.stats not found at $REF_DIR/ocean.stats"
    echo "Please place a known-good ocean.stats there before running bisect."
    exit 125
fi

# ---------------------------------------------------------------------------
# Optionally merge the CEFI base on top of the current bisect candidate.
# This ensures CEFI-specific commits (e.g. configuration prerequisites) are
# always present when bisecting a raw dev/gfdl commit range.
# We record the original HEAD so we can reset back after the test.
# ---------------------------------------------------------------------------
BISECT_HEAD=$(git -C "$MOM6_DIR" rev-parse HEAD)

if [[ -n "$CEFI_BASE" ]]; then
    echo "=== Merging CEFI base $CEFI_BASE onto bisect candidate $BISECT_HEAD ==="
    # Merge without committing so we can reset cleanly afterwards.
    # If the merge fails (conflict) we skip this commit.
    set +e
    git -C "$MOM6_DIR" merge --no-ff "$CEFI_BASE" -m "bisect-tmp: merge CEFI base"
    MERGE_EXIT=$?
    set -e
    if [[ $MERGE_EXIT -ne 0 ]]; then
        echo "Merge of CEFI base conflicted — skipping this commit (exit 125)"
        git -C "$MOM6_DIR" merge --abort 2>/dev/null || git -C "$MOM6_DIR" reset --hard "$BISECT_HEAD"
        exit 125
    fi
fi

# Helper: always reset back to the original bisect HEAD before exiting,
# so git bisect can cleanly check out the next candidate.
# This will always run on exit due to trap command after declaration
cleanup_git() {
    git -C "$MOM6_DIR" reset --hard "$BISECT_HEAD"
}
trap cleanup_git EXIT

# ---------------------------------------------------------------------------
# Build (docker / linux-intel, repro, mom6sis2) via the container build driver
# ---------------------------------------------------------------------------
echo "=== Building MOM6 (bisect candidate $BISECT_HEAD) ==="
cd "$SCRIPT_DIR"
set +e
# -n flag tells script not to clean up build dir
bash ci_build_driver.sh -n
BUILD_EXIT=$?
set -e

if [[ $BUILD_EXIT -ne 0 ]]; then
    echo "Build failed — skipping this commit (exit 125)"
    exit 125
fi

if [[ ! -x "$BINARY" ]]; then
    echo "Binary not found at $BINARY after build — skipping (exit 125)"
    exit 125
fi

# ---------------------------------------------------------------------------
# Environment setup (mirrors driver.sh)
# ---------------------------------------------------------------------------
cd "$EXP_DIR"

source $MODULESHOME/init/bash
module load cray-mpich-abi
module unload cray-hdf5

# Link shared datasets
pushd "$EXP_DIR/.." > /dev/null
ln -fs /gpfs/f5/gfdl_med/world-shared/datasets ./
popd > /dev/null

# Copy ERA5 forcing files to run directory to avoid I/O issues
# caused by symlinks on c5
echo "Copying atmosphere forcing to INPUT dir"
pushd "${EXP_DIR}/INPUT"
for f in ERA5_* ; do
    if [ -L ${f} ] ; then
        echo "Copying ${f}"
        # readlink gets the full path to the symlinked data,
        # cp --remove-destination removes the symlink + copies over the actual data
        cp --remove-destination "$(readlink ${f})" ${f}
    else
        echo "${f} is already copied over, skipping copy"
    fi
done
popd

export img="/gpfs/f5/cefi/world-shared/container/gaea_intel_2023.2.0.sif"
export MPICH_SMP_SINGLE_COPY_MODE="NONE"

export APPTAINERENV_LD_LIBRARY_PATH=${CRAY_LD_LIBRARY_PATH}:${LD_LIBRARY_PATH}:/opt/cray/pe/lib64:/usr/lib64/libibverbs:/opt/cray/libfabric/1.20.1/lib64:/opt/cray/pals/1.4/lib:\$LD_LIBRARY_PATH

export APPTAINER_CONTAINLIBS="/opt/cray/pals/1.6/lib/libpals.so.0,/usr/lib64/libjansson.so.4,/usr/lib64/libjson-c.so.3,/usr/lib64/libdrm.so.2,/lib64/libtinfo.so.6,/usr/lib64/libnl-3.so.200,/usr/lib64/librdmacm.so.1,/usr/lib64/libibverbs.so.1,/usr/lib64/libibverbs/libmlx5-rdmav34.so,/usr/lib64/libnuma.so.1,/usr/lib64/libnl-cli-3.so.200,/usr/lib64/libnl-genl-3.so.200,/usr/lib64/libnl-nf-3.so.200,/usr/lib64/libnl-route-3.so.200,/usr/lib64/libnl-3.so.200,/usr/lib64/libnl-idiag-3.so.200,/usr/lib64/libnl-xfrm-3.so.200,/usr/lib64/libnl-genl-3.so.200"

export APPTAINER_BIND="/usr/share/libdrm,/var/spool/slurmd,/opt/cray,/opt/intel,${EXP_DIR},/etc/libibverbs.d,/usr/lib64/libibverbs,/usr/lib64/libnl3-200,${HOME}"

export FI_VERBS_PREFER_XRC=0

# ---------------------------------------------------------------------------
# Clean up any leftovers from a previous bisect iteration
# ---------------------------------------------------------------------------
rm -rf  "$EXP_DIR/RESTART_48hrs" \
        "$EXP_DIR/RESTART" \
        "$EXP_DIR/out_bisect" \
        "$EXP_DIR/err_bisect"
rm -f   "$EXP_DIR/input.nml"

# ---------------------------------------------------------------------------
# Run 48hr experiment
# ---------------------------------------------------------------------------
echo "=== Running 48hr experiment for $EXP_NAME ==="
ln -fs input.nml_48hr input.nml

set +e
srun --ntasks ${NTASKS} --export=ALL \
    apptainer exec \
        -B $HOME:$HOME \
        -B /autofs/ncrc-svm1_home1/role.medgrp:/autofs/ncrc-svm1_home1/role.medgrp \
        --writable-tmpfs $img \
        bash ./execrunscript.sh \
    > out_bisect 2> err_bisect
RUN_EXIT=$?
set -e

# Collect outputs
[[ -d RESTART    ]] && mv RESTART    RESTART_48hrs
[[ -f ocean.stats ]] && mv ocean.stats RESTART_48hrs/

# ---------------------------------------------------------------------------
# Handle run failure
# ---------------------------------------------------------------------------
if [[ $RUN_EXIT -ne 0 ]]; then
    echo "Model run failed (srun exit $RUN_EXIT) — skipping this commit (exit 125)"
    rm -rf "$EXP_DIR/RESTART_48hrs" "$EXP_DIR/out_bisect" "$EXP_DIR/err_bisect"
    rm -f  "$EXP_DIR/input.nml"
    exit 125
fi

if [[ ! -f "$EXP_DIR/RESTART_48hrs/ocean.stats" ]]; then
    echo "ocean.stats was not produced — skipping this commit (exit 125)"
    rm -rf "$EXP_DIR/RESTART_48hrs" "$EXP_DIR/out_bisect" "$EXP_DIR/err_bisect"
    rm -f  "$EXP_DIR/input.nml"
    exit 125
fi

# ---------------------------------------------------------------------------
# Compare ocean.stats against reference
# ---------------------------------------------------------------------------
if diff "$EXP_DIR/RESTART_48hrs/ocean.stats" "$REF_DIR/ocean.stats" > /dev/null 2>&1; then
    RESULT=0
    echo "=== ocean.stats matches reference — GOOD commit ==="
else
    RESULT=1
    echo "=== ocean.stats differs from reference — BAD commit ==="
    echo "--- diff ---"
    diff "$EXP_DIR/RESTART_48hrs/ocean.stats" "$REF_DIR/ocean.stats" || true
fi

# ---------------------------------------------------------------------------
# Cleanup experiment outputs
# (git reset back to BISECT_HEAD is handled by the EXIT trap above)
# ---------------------------------------------------------------------------
rm -rf "$EXP_DIR/RESTART_48hrs" "$EXP_DIR/out_bisect" "$EXP_DIR/err_bisect"
rm -f  "$EXP_DIR/input.nml"

exit $RESULT
