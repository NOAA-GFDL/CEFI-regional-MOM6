# module load cdo/2.1.1 nco/5.0.1
import os
from subprocess import run


def run_cmd(cmd, print_cmd=True):
    if print_cmd:
        print(cmd)
    run([cmd], shell=True, check=True) 


years = range(2021, 2024)
glorys_root = '/work/acr/glorys/GLOBAL_ANALYSISFORECAST_PHY_001_024/monthly'

years = range(1993, 2020)
glorys_root = '/work/acr/glorys/GLOBAL_MULTIYEAR_PHY_001_030/monthly'

out_dir = os.environ['TMPDIR']

outfiles = []

for year in years:
    print(year)
    infile = os.path.join(glorys_root, f'glorys_monthly_ts_fine_{year}.nc')
    if not os.path.exists(infile):
        raise FileNotFoundError(f'Did not find the GLORYS file {infile}')
    else:
        outfile = os.path.join(out_dir, os.path.basename(infile).replace('fine', 'coarse'))
        if not os.path.exists(outfile):
            run_cmd(f'cdo selvar,thetao,so -gridboxmean,3,3 {infile} {outfile}')
        else:
            print(f'Skipping {infile}; already written')
        outfiles.append(outfile)
        
# files_to_concat = ' '.join(outfiles)
# # Place to put final file.
# # Currently on vftmp, will need to gcp elsewhere afterwards. 
# concatted_file = f'/vftmp/Andrew.C.Ross/GLORYS_REANALYSIS_NEP_{years[0]}-{years[-1]}_coarse.nc'
# run_cmd(f'ncrcat -h {files_to_concat} -O {concatted_file}')
# run_cmd(f'cdo chname,lat,latitude -chname,lon,longitude {concatted_file} {concatted_file}.tmp')
# os.rename(f'{concatted_file}.tmp', concatted_file)
