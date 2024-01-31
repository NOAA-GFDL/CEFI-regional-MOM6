#!/bin/tcsh
#

module load fre/bronx-20

cd INPUT
#This is to make the super-grid, so nlon=8 for a 4x4 model, nlon=4 for a 2x2 model.
#make_hgrid --grid_type regular_lonlat_grid --nxbnd 2 --nybnd 2 --xbnd -140.2,-139.8 --ybnd -0.2,0.2 --nlon 8 --nlat 8 --grid_name ocean_hgrid
#make_hgrid --grid_type regular_lonlat_grid --nxbnd 2 --nybnd 2 --xbnd -120.2,-119.8 --ybnd -0.2,0.2 --nlon 8 --nlat 8 --grid_name ocean_hgrid
#BATS (lon, lat)=(-64.1667,31.6667)
make_hgrid --grid_type regular_lonlat_grid --nxbnd 2 --nybnd 2 --xbnd -64.3667,-63.9667 --ybnd 31.4667,31.8667 --nlon 8 --nlat 8 --grid_name ocean_hgrid
#make_hgrid --grid_type regular_lonlat_grid --nxbnd 2 --nybnd 2 --xbnd -90.2,-89.8 --ybnd -0.2,0.2 --nlon 8 --nlat 8 --grid_name ocean_hgrid

make_solo_mosaic --num_tiles 1 --dir ./ --mosaic_name ocean_mosaic --tile_file ocean_hgrid.nc
make_solo_mosaic --num_tiles 1 --dir ./ --mosaic_name atmos_mosaic --tile_file ocean_hgrid.nc
make_solo_mosaic --num_tiles 1 --dir ./ --mosaic_name land_mosaic --tile_file ocean_hgrid.nc
make_solo_mosaic --num_tiles 1 --dir ./ --mosaic_name wave_mosaic --tile_file ocean_hgrid.nc

make_topog --mosaic ocean_mosaic.nc --topog_type  rectangular_basin --bottom_depth 4000

make_coupler_mosaic --atmos_mosaic atmos_mosaic.nc --land_mosaic land_mosaic.nc --ocean_mosaic ocean_mosaic.nc --ocean_topog topog.nc --mosaic_name grid_spec --check --verbose

