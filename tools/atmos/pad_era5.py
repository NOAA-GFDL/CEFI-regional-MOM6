# run on analysis
# before:
# module python/3.9 nco/5.0.1 gcp

# to create liquid precip:
# cdo -setrtoc,-1e9,0,0 -chname,tp,lp -sub ERA5_tp_${y}_padded.nc ERA5_sf_${y}_padded.nc ERA5_lp_${y}_padded.nc

import os
import subprocess


def run_cmd(cmd):
   subprocess.run([cmd], shell=True, check=True) 


# Extract data for these years.
# The last year will be extracted but will only be used 
# to pad the end of the second to last year.
YEARS = range(1993, 2022)

# To reduce file size, only extract and pad this
# lat/lon subset that encompasses the NWA domain.
REGION_SLICE = 'latitude,0.0,60.0 -d longitude,260.0,325.0'

# Location to save temporary data to.
# Use TMPDIR as set on ppan.
TMP = os.environ['TMPDIR']

# Location to save the final padded data to.
FINAL = '/work/acr/era5/padded/'

# Location of the complete archive of ERA5 data
UDA = '/archive/uda/ERA5/Hourly_Data_On_Single_Levels/reanalysis/global/1hr-timestep/annual_file-range/'

# Short and long names used in the ERA5 data archive file names.
NAMES = {
    'P_mean_sea_level': 'mean_sea_level_pressure',
    'P_surface': 'surface_pressure',  # Needed for calculating specific humidity
    'Pr_total': 'total_precipitation',
    'snowfall': 'snowfall',
    'sfc_solar_rad_downward': 'surface_solar_radiation_downwards',
    'sfc_thermal_rad_downward': 'surface_thermal_radiation_downwards',
    'T_2m': '2m_temperature',
    'Td_2m': '2m_dewpoint_temperature', 
    'u_10m': '10m_u_component_of_wind',
    'v_10m': '10m_v_component_of_wind'
}

GROUPS = {
    'P_mean_sea_level': 'Temperature_and_Pressure',
    'P_surface': 'Temperature_and_Pressure',  # Needed for calculating specific humidity
    'Pr_total': 'Precipitation_and_Rain',
    'snowfall': 'Snow',
    'sfc_solar_rad_downward': 'Radiation_and_Heat',
    'sfc_thermal_rad_downward': 'Radiation_and_Heat',
    'T_2m': 'Temperature_and_Pressure',
    'Td_2m': 'Temperature_and_Pressure', 
    'u_10m': 'Wind',
    'v_10m': 'Wind'
}

# Names of actual data variables for each file.
# This will also be used in the final file name.
VARIABLES = {
    'P_mean_sea_level': 'msl',
    'P_surface': 'sp',
    'Pr_total': 'tp',
    'snowfall': 'sf',
    'sfc_solar_rad_downward': 'ssrd',
    'sfc_thermal_rad_downward': 'strd',
    'T_2m': 't2m',
    'Td_2m': 'd2m',
    'u_10m': 'u10',
    'v_10m': 'v10'
}

def main():
    for var in NAMES:
        print(var)

        long_name = NAMES[var]
        var_name = VARIABLES[var]
        group = GROUPS[var]

        # dmget all of the files for this variable.
        files = [os.path.join(UDA, group, var, f'ERA5_1hr_{long_name}_{y}.nc') for y in YEARS]
        for f in files:
            if not os.path.exists(f):
                print(f'{f} does not exist')


        print(f'  dmget {var}')
        run_cmd('dmget ' + ' '.join(files))
        
        for f in files:
            # Copy a single file to TMP (not all at once since they are large).
            tmp_file = os.path.join(TMP, os.path.basename(f))
            if not os.path.isfile(tmp_file):
                print(f'  gcp {f}')
                run_cmd(f'gcp --sync {f} {TMP}')

            # Subset the file by latitude and longitude.
            print(f'  slice {tmp_file}')
            sliced_file = tmp_file.replace('.nc', '_sliced.nc').replace(long_name, var_name)
            cmd = f'ncks {tmp_file} -d {REGION_SLICE} -O {sliced_file}'
            run_cmd(cmd)

            # Make time the unlimited dimension.
            print('  fix time')
            run_cmd(f'ncks --mk_rec_dmn time {sliced_file} -O {sliced_file}')

            # Unpack the data; FMS doesn't seem to work with packed data?
            print('  unpack')
            run_cmd(f'ncpdq -U {sliced_file} -O {sliced_file}')

            # Latitude is stored north to south, so flip it.
            print('  flip')
            run_cmd(f'ncpdq -a "time,-latitude,longitude" {sliced_file} -O {sliced_file}')

            # Delete the large temporary file.
            print(f'  rm {tmp_file}')
            os.remove(tmp_file)

        final_files = []

        for y in YEARS[0:-1]:
            # Get the names of the current year's file and the next year's file.
            this_file = os.path.join(TMP, f'ERA5_1hr_{var_name}_{y}_sliced.nc')
            next_file = os.path.join(TMP, f'ERA5_1hr_{var_name}_{y+1}_sliced.nc')

            # Extract the first time in the next year (midnight Jan 1). 
            print(f'tail {y+1}')
            tail_file = os.path.join(TMP, 'tail.nc')
            run_cmd(f'ncks {next_file} -d time,0,0 -O {tail_file}')

            # Append the first time in the next year to the end of the current year. 
            print(f'concat {y} tail')
            padded_file = this_file.replace('sliced', 'padded').replace('1hr_', '')
            run_cmd(f'ncrcat {this_file} {tail_file} -O {padded_file}')
            final_files.append(padded_file)

            # The non-padded file for the current year can now be deleted.
            print(f'rm {y}')
            os.remove(this_file)

        # Copy all of the final padded files to the final directory. 
        print('gcp final result')
        run_cmd('gcp ' + ' '.join(final_files) + ' ' + FINAL)


if __name__ == '__main__':
    main()
