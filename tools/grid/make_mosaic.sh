# module load nco/4.8.1
# module load fre/bronx-19


# Need to add ntiles to ocean topog for later use with fre tools.
ncap2 -s 'defdim("ntiles", 1);ntiles[ntiles]=1' ocean_topog.nc -O ocean_topog.nc
make_solo_mosaic --num_tiles 1 --dir . --mosaic_name ocean_mosaic --tile_file ocean_hgrid.nc
make_quick_mosaic --input_mosaic ocean_mosaic.nc --mosaic_name grid_spec --ocean_topog ocean_topog.nc
