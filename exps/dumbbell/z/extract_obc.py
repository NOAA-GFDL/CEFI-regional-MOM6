#!/bin/env python
# Extract boundary conditions for the child domain from the output of
# the parent domain. Run this after extract_obc.bash.
import numpy as np
import netCDF4
import os
import sys
import subprocess
import numpy as np
from datetime import datetime

grd = netCDF4.Dataset('ocean_geometry.nc', "r")
prog = netCDF4.Dataset('prog.nc', "r")
east = netCDF4.Dataset('east.nc', 'a')
west = netCDF4.Dataset('west.nc', 'a')
spval = 1.e20

new = True
if new:
    west.createVariable('dvdx_segment_001', 'f8', ('Time', 'zl', 'yq', 'xq'), fill_value=spval)
    west.variables['dvdx_segment_001'].long_name = 'Part of vorticity.'
    west.variables['dvdx_segment_001'].units = '1/s'

    west.createVariable('dz_dvdx_segment_001', 'f8', ('Time', 'zl', 'yq', 'xq'), fill_value=spval)
    west.variables['dz_dvdx_segment_001'].long_name = 'Layer thicknesses.'
    west.variables['dz_dvdx_segment_001'].units = 'm'

    east.createVariable('dvdx_segment_002', 'f8', ('Time', 'zl', 'yq', 'xq'), fill_value=spval)
    east.variables['dvdx_segment_002'].long_name = 'Part of vorticity.'
    east.variables['dvdx_segment_002'].units = '1/s'

    east.createVariable('dz_dvdx_segment_002', 'f8', ('Time', 'zl', 'yq', 'xq'), fill_value=spval)
    east.variables['dz_dvdx_segment_002'].long_name = 'Layer thicknesses.'
    east.variables['dz_dvdx_segment_002'].units = 'm'

# Whole grid
v = prog.variables['v'][:]
h = prog.variables['h'][:]
salt = prog.variables['salt'][:]
SSH = prog.variables['SSH'][:]
dx = grd.variables['dxBu'][:]

# Segment 1
dvdx = (v[:,:,:,40] - v[:,:,:,39]) / dx[:,40]
vseg = 0.5*(v[:,:,:,40] + v[:,:,:,39])
hseg = 0.5*(h[:,:,:,40] + h[:,:,:,39])
hqseg = np.zeros(vseg.shape)
hqseg[:,:,0:3] = hseg[:,:,0:3]
hqseg[:,:,18:] = hseg[:,:,17:]
hqseg[:,:,3:18] = 0.5*(hseg[:,:,2:17] + hseg[:,:,3:18])
saltseg = 0.5*(salt[:,:,:,40] + salt[:,:,:,39])
sshseg = 0.5*(SSH[:,:,40] + SSH[:,:,39])

west.variables['dvdx_segment_001'][:] = dvdx
west.variables['dz_dvdx_segment_001'][:] = hqseg
west.variables['v_segment_001'][:] = vseg
west.variables['dz_v_segment_001'][:] = hqseg
west.variables['salt_segment_001'][:] = saltseg
west.variables['dz_salt_segment_001'][:] = hseg
west.variables['dz_u_segment_001'][:] = hseg
west.variables['zeta_segment_001'][:] = sshseg
west.close()

# Segment 2
dvdx = (v[:,:,:,80] - v[:,:,:,79]) / dx[:,70]
vseg = 0.5*(v[:,:,:,80] + v[:,:,:,79])
hseg = 0.5*(h[:,:,:,80] + h[:,:,:,79])
hqseg = np.zeros(vseg.shape)
hqseg[:,:,0:3] = hseg[:,:,0:3]
hqseg[:,:,18:] = hseg[:,:,17:]
hqseg[:,:,3:18] = 0.5*(hseg[:,:,2:17] + hseg[:,:,3:18])
saltseg = 0.5*(salt[:,:,:,80] + salt[:,:,:,79])
sshseg = 0.5*(SSH[:,:,80] + SSH[:,:,79])

east.variables['dvdx_segment_002'][:] = dvdx
east.variables['dz_dvdx_segment_002'][:] = hqseg
east.variables['v_segment_002'][:] = vseg
east.variables['dz_v_segment_002'][:] = hqseg
east.variables['salt_segment_002'][:] = saltseg
east.variables['dz_salt_segment_002'][:] = hseg
east.variables['dz_u_segment_002'][:] = hseg
east.variables['zeta_segment_002'][:] = sshseg
east.close()
