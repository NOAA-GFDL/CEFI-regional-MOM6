#!/bin/bash
for yr in {1993..1993}; do
 for varnm in thetao so zos uv; do
    # ncrcat segments
    for seg in {1..4}; do
        ncrcat -O -h ${varnm}_$(printf %03d $seg)_${yr}-??-??.nc ${varnm}_$(printf %03d $seg)_${yr}.nc
        #append segments
        if [ $seg == 1 ] && [ $varnm == theta ] ; then
           cp ${varnm}_$(printf %03d $seg)_${yr}.nc nep_5km_glorys_obcs_${yr}.nc
        else
           ncks -A ${varnm}_$(printf %03d $seg)_${yr}.nc nep_5km_glorys_obcs_${yr}.nc
        fi
    done
 done
# Include GLORYS time attributes 
ncatted -O -a long_name,time,c,c,"Time (hours since 1950-01-01)" nep_5km_glorys_obcs_${yr}.nc
ncatted -O -a standard_name,time,c,c,"time" nep_5km_glorys_obcs_${yr}.nc
ncatted -O -a calendar,time,c,c,"gregorian" nep_5km_glorys_obcs_${yr}.nc
ncatted -O -a units,time,c,c,"hours since 1950-01-01 00:00:00" nep_5km_glorys_obcs_${yr}.nc

rm  ${varnm}_???_${yr}-??-??.nc
rm ${varnm}_???_${yr}.nc
done
