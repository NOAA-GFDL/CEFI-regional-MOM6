#!/bin/bash
#
# This script creates a super-grid based on user input for station name, latitude, and longitude.
# Assume fre-NCtools is installed in your system (https://github.com/NOAA-GFDL/FRE-NCtools.git)
# Usage: ./BuildExchangeGrid.sh BATS 31.6667 -64.1667

# Check if the correct number of arguments are provided
if [ "$#" -ne 3 ]; then
    echo "Usage: $0 <station_name> <latitude> <longitude>"
    exit 1
fi

# Assign arguments to variables
station_name="$1"
latitude="$2"
longitude="$3"

# Calculate the bounds for the grid
xbnd_min=$(awk -v lon="$longitude" 'BEGIN { printf "%.4f", lon - 0.2 }')
xbnd_max=$(awk -v lon="$longitude" 'BEGIN { printf "%.4f", lon + 0.2 }')
ybnd_min=$(awk -v lat="$latitude" 'BEGIN { printf "%.4f", lat - 0.2 }')
ybnd_max=$(awk -v lat="$latitude" 'BEGIN { printf "%.4f", lat + 0.2 }')

# Create a folder for the station
[[ -d $station_name ]] && rm -rf $station_name
mkdir -p "$station_name"
cd "$station_name"

# Create the super-grid based on user input
make_hgrid --grid_type regular_lonlat_grid \
           --nxbnd 2 --nybnd 2 \
           --xbnd "$xbnd_min,$xbnd_max" \
           --ybnd "$ybnd_min,$ybnd_max" \
           --nlon 8 --nlat 8 \
           --grid_name ocean_hgrid


make_solo_mosaic --num_tiles 1 --dir ./ --mosaic_name ocean_mosaic --tile_file ocean_hgrid.nc
make_solo_mosaic --num_tiles 1 --dir ./ --mosaic_name atmos_mosaic --tile_file ocean_hgrid.nc
make_solo_mosaic --num_tiles 1 --dir ./ --mosaic_name land_mosaic --tile_file ocean_hgrid.nc

make_topog --mosaic ocean_mosaic.nc --topog_type  rectangular_basin --bottom_depth 4000 --output ocean_topog

make_coupler_mosaic --atmos_mosaic atmos_mosaic.nc --land_mosaic land_mosaic.nc --ocean_mosaic ocean_mosaic.nc --ocean_topog ocean_topog.nc --mosaic_name grid_spec --check --verbose
