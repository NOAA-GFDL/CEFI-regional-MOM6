#!/usr/bin/env python
# coding: utf-8

import netCDF4 as nc
import numpy as np
import matplotlib
matplotlib.use('Agg')
import matplotlib.pyplot as plt
import sys

pgeom=nc.Dataset('../z/ocean_geometry.nc')
geom=nc.Dataset('ocean_geometry.nc')

exp=sys.argv[1]

print('Calculating RMS errors for ',exp,' .... ')


px=pgeom.variables['lonq']
py=pgeom.variables['latq']
pxc=pgeom.variables['lonh']
pyc=pgeom.variables['lath']
pwet=pgeom.variables['wet']

x=geom.variables['lonq']
y=geom.variables['latq']
xc=geom.variables['lonh']
yc=geom.variables['lath']
wet=geom.variables['wet']

Prog=nc.Dataset('../z/prog.nc')
prog=nc.Dataset(exp+'/prog.nc')

prv=Prog.variables['RV']
psalt=Prog.variables['salt']
ptime=Prog.variables['Time']

rv=prog.variables['RV']
salt=prog.variables['salt']
time=prog.variables['Time']



def rv_rms():
    is_=np.where(px>=x[0])[0][0]
    ie_=np.where(px>=x[-1])[0][0]
    prv_=prv[:,:,:,is_:ie_+1]
    diff=1.e4*(rv[:]-prv_[:])
    diff2 = diff**2.0
    rms_diff = diff2.mean(axis=3).mean(axis=2).mean(axis=1)
    plt.plot(time[:],rms_diff,label='RMS Vorticity Error')
    rms_err=diff.std()
    print('Vorticity error (10-4 s-1) = ',str(rms_err)[:12])
    return rms_err

def enstro_rms():
    is_=np.where(px>=x[0])[0][0]
    ie_=np.where(px>=x[-1])[0][0]
    prv_=prv[:,:,:,is_:ie_+1]
    penstro=prv_**2.0
    enstro=rv[:]**2.0
    diff=1.e7*(enstro[:]-penstro[:])
    diff2 = diff**2.0
    rms_diff = diff2.mean(axis=3).mean(axis=2).mean(axis=1)
    plt.plot(time[:],rms_diff,label='RMS Enstrophy Error (10-8 s-2)')
    rms_err=diff.std()
    print('Enstrophy error (10-7 s-2) = ',str(rms_err)[:12])
    return rms_err

def salt_rms():
    is_=np.where(px>=x[0])[0][0]
    ie_=np.where(px>=x[-1])[0][0]
    psalt_=psalt[:,:,:,is_:ie_]
    diff=salt[:]-psalt_
    diff2=diff*diff
    rms=diff2.mean(axis=3).mean(axis=2).mean(axis=1)
    mn=diff.mean(axis=3).mean(axis=2).mean(axis=1)
    plt.plot(time[:],np.sqrt(rms),label='RMS Salt Error')
    rms_err=rms.std()
    print('RMS Salinity error (psu) =', str(rms_err)[:12])
    return rms_err

plt.clf()
fig=plt.figure(1,figsize=(6,4))
rv_rms=rv_rms()
plt.title(exp+' RMS Vorticity Error (10-4 s-1)')
plt.xlabel('days')
plt.ylabel('psu or 10-4 s-1')
plt.grid()
plt.legend()
plt.ylim(0,8.0)
fig.savefig(exp+'/rv_rms.png')
plt.clf()
fig=plt.figure(1,figsize=(6,4))
ens_rms=enstro_rms()
plt.title(exp+' RMS Enstrophy Error (10-8 s-1)')
plt.xlabel('days')
plt.ylabel('10-7 s-1')
plt.grid()
plt.legend()
plt.ylim(0,1.0)
fig.savefig(exp+'/enstro_rms.png')
plt.clf()
fig=plt.figure(1,figsize=(6,4))
salt_rms=salt_rms()
plt.title(exp+' RMS Salinity Error (psu)')
plt.xlabel('days')
plt.ylabel('psu')
plt.grid()
plt.legend()
plt.ylim(0,0.1)
fig.savefig(exp+'/so_rms.png')

g=open(exp+'/err.txt','w')
g.write(str(rv_rms)[:12] +','+str(ens_rms)[:12] +','+str(salt_rms)[:12]+'\n')
g.close()
