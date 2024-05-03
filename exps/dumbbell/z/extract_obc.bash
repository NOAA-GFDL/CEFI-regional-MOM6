#!/bin/bash
# Extract boundary conditions for the child domain from the output of
# the parent domain.
ln -fs 00010101.prog.nc prog.nc


ncks -O -d xq,40,40 -v uav prog.nc west.nc
ncks -d xh,39,39 -v SSH -A  prog.nc west.nc
ncks -d xh,39,39 -v salt -A  prog.nc west.nc
ncks -d xh,39,39 -v h -A  prog.nc west.nc
ncks -d xh,39,39 -v v -A  prog.nc west.nc
ncatted -a modulo,Time,c,c,' ' west.nc
ncrename -v uav,u_segment_001 west.nc
ncrename -v SSH,zeta_segment_001 west.nc
ncrename -v h,dz_u_segment_001 west.nc
ncks -d xh,39,39 -v h -A  prog.nc west.nc
ncrename -v salt,salt_segment_001 west.nc
ncrename -v v,v_segment_001 west.nc
# Change this if changing DUMBBELL_FRACTION
ncks -d xh,39,39 -v v -A  prog.nc west.nc
ncap2 -A -s 'v(:,:,0:1,:)=0; v(:,:,19:20,:)=0; v(:,:,2,:)=h(:,:,2,:); v(:,:,18,:)=h(:,:,17,:); v(:,:,3:17,:)=0.5*(h(:,:,2:16,:)+h(:,:,3:17,:))' west.nc west.nc
ncrename -v h,dz_salt_segment_001 west.nc
ncrename -v v,dz_v_segment_001 west.nc
ncatted -a units,dz_v_segment_001,m,c,'m' west.nc
## For dvdx
#ncks -d xh,41,41 -v v -A  prog.nc west.nc
#ncrename -v v,dvdx_segment_001 west.nc
#ncap2 -A -s 'dvdx_segment_001(:,:,:,0)=v(:,:,:,42)-v(:,:,:,41)' prog.nc west.nc
#ncks -d xh,41,41 -v v -A  prog.nc west.nc
#ncrename -v v,dz_dvdx_segment_001 west.nc
#ncap2 -A -s 'dz_dvdx_segment_001(:,:,:,:)=dz_v_segment_001(:,:,:,:)' west.nc west.nc

ncks -O -d xq,80,80 -v uav prog.nc east.nc
ncks -d xh,80,80 -v SSH -A  prog.nc east.nc
ncks -d xh,80,80 -v salt -A  prog.nc east.nc
ncks -d xh,80,80 -v h -A  prog.nc east.nc
ncks -d xh,80,80 -v v -A  prog.nc east.nc
ncatted -a modulo,Time,c,c,' ' east.nc
ncrename -v uav,u_segment_002 east.nc
ncrename -v SSH,zeta_segment_002 east.nc
ncrename -v h,dz_u_segment_002 east.nc
ncks -d xh,80,80 -v h -A  prog.nc east.nc
ncrename -v salt,salt_segment_002 east.nc
ncrename -v v,v_segment_002 east.nc
# Change this if changing DUMBBELL_FRACTION
ncks -d xh,80,80 -v v -A  prog.nc east.nc
ncap2 -A -s 'v(:,:,0:1,:)=0; v(:,:,19:20,:)=0; v(:,:,2,:)=h(:,:,2,:); v(:,:,18,:)=h(:,:,17,:); v(:,:,3:17,:)=0.5*(h(:,:,2:16,:)+h(:,:,3:17,:))' east.nc east.nc
ncrename -v h,dz_salt_segment_002 east.nc
ncrename -v v,dz_v_segment_002 east.nc
ncatted -a units,dz_v_segment_002,m,c,'m' east.nc
## For dvdx
#ncks -d xh,81,81 -v v -A  prog.nc east.nc
#ncrename -v v,dvdx_segment_002 east.nc
#ncap2 -A -s 'dvdx_segment_002(:,:,:,0)=v(:,:,:,82)-v(:,:,:,81)' prog.nc east.nc
#ncks -d xh,81,81 -v v -A  prog.nc east.nc
#ncrename -v v,dz_dvdx_segment_002 east.nc
#ncap2 -A -s 'dz_dvdx_segment_002(:,:,:,:)=dz_v_segment_002(:,:,:,:)' east.nc east.nc
