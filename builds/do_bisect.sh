#!/bin/bash
#SBATCH --nodes=16
#SBATCH --time=400
#SBATCH --job-name=bisect_MOM6
#SBATCH --output=job_output_files/bisect_%j.out
#SBATCH --qos=normal
#SBATCH --partition=batch
#SBATCH --clusters=c5
#SBATCH --account=cefi

# ===========================================================================
# USER CONFIGURATION — set all values in this block before submitting.
# ===========================================================================

# Experiment to bisect (must match a subdirectory of exps/).
# Supported values: NEP10.COBALT, NWA12.COBALT
EXP_NAME="NEP10.COBALT"
NTASKS=2600
REF_DIR="/path/to/reference/dir"

# --- Commit range to bisect -------------------------------------------------
# Supply the bounding bad and good commit SHAs for src/MOM6.
#
# If the answer change arrived via a dev/gfdl → dev/cefi merge, use the
# second parents of the bounding dev/cefi merge commits so that every
# candidate is a real dev/gfdl commit:
#
#   BAD=$(git -C ../src/MOM6  rev-parse <bad_cefi_merge>^2)
#   GOOD=$(git -C ../src/MOM6 rev-parse <good_cefi_merge>^2)
#
# Otherwise supply the commit SHAs directly.
BAD="<bad commit SHA>"
GOOD="<good commit SHA>"

# (Optional) CEFI base commit to temporarily merge onto each bisect candidate
# before building.  Use this when bisecting a dev/gfdl range so that
# CEFI-specific commits are always present during the build and run.
# Set to the first parent of the good dev/cefi merge commit:
#
#   CEFI_BASE=$(git -C ../src/MOM6 rev-parse <good_cefi_merge>^1)
#
# Leave empty to skip the temporary merge step.
CEFI_BASE=""

# ===========================================================================
# END USER CONFIGURATION — do not edit below this line.
# ===========================================================================

# Enter MOM6 dir to run bisect
cd ../src/MOM6/

git bisect start
git bisect bad  "$BAD"
git bisect good "$GOOD"
git bisect run ../../builds/bisect-test.sh \
    -e "$EXP_NAME" \
    -r "$REF_DIR" \
    -n "$NTASKS" \
    ${CEFI_BASE:+-b "$CEFI_BASE"}
