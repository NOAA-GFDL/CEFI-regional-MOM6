#!/bin/bash
#SBATCH --nodes=8
#SBATCH --time=60
#SBATCH --job-name="NEP10.COBALTv2"
#SBATCH --output=NEP10.COBALTv2_o.%j
#SBATCH --error=NEP10.COBALTv2_e.%j
#SBATCH --qos=debug
#SBATCH --partition=batch
#SBATCH --clusters=c5
#SBATCH --account=cefi

#
ntasks1=904


# copy MOM_override
rm -rf RESTART*
[[ -f input.nml ]] && rm -rf input.nml

#
echo "Test started:  " `date`

#echo "run 20x56 48hrs test ..."
ln -fs input.nml_48hr input.nml
srun --ntasks ${ntasks1} --cpus-per-task=1 --export=ALL ./MOM6SIS2  > out1 2>err1
mv RESTART RESTART_48hrs
mv ocean.stats RESTART_48hrs

echo "Test ended:  " `date`
