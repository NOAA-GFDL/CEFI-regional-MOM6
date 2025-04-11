import numpy as np
import pandas as pd 
import xesmf
import xarray
import sys
import copy
import warnings
warnings.filterwarnings("ignore")

def update_stencil_sum(ocean_mask):
    
    # Make 3x3 stensil 
    sten_nlat = 3
    sten_nlon = 3

    glofas_stensil_sum = np.zeros(ocean_mask.shape)
    for nlat in range(sten_nlat):
        ilat_last = -(2-nlat)
        if ilat_last == 0:
            ilat_last = None
        
        for nlon in range(sten_nlon):
            ilon_last = -(2-nlon)
            if ilon_last == 0:
                ilon_last = None
       
            glofas_stensil_sum[1:-1,1:-1] += ocean_mask[nlat:ilat_last,nlon:ilon_last]
        
    return glofas_stensil_sum 

def get_glofas_pour_points():
    ldd_modified = copy.deepcopy(ldd)
    # GloFAS VERSION 3: editing pour points along map seam in Russia at date line. 
    # Not sure if these are the best points to change or what happens with this runoff
    #ldd_modified[168,299:301]=1
    #ldd_modified[132,299]=1
   
    # GloFAS VERSION 4: editing pour points along map seam in Russia Chukotka Region at date line.
    lat_idx = np.where(np.round(glofas_lat,3) == 68.875)[0][0]
    lon_idx = np.where(np.round(glofas_lon,3) == 180.025)[0][0]
    ldd_modified[lat_idx,lon_idx]=1 # change from 5 to stop advancing halo point
    
    # GloFAS VERSION 4: editing pour points to connect Columbia River to the ocean
    lat_idx = np.where(np.round(glofas_lat,3) == 46.175)[0][0]
    lon_idx = np.where(np.round(glofas_lon,3) == 236.275)[0][0]
    ldd_modified[lat_idx,lon_idx]=5 # change to 5 to advance halo point    
    lat_idx = np.where(np.round(glofas_lat,3) == 46.225)[0][0]
    lon_idx = np.where(np.round(glofas_lon,3) == 236.475)[0][0]
    ldd_modified[lat_idx,lon_idx]=5 # change to 5 to advance halo point   
    
    glofas_ocean_mask = np.isnan(ldd)

    # initialize the while loop
    n_updates = 1

    # continue 
    while n_updates>0:
        n_updates = 0
        ocean_stencil_sum = update_stencil_sum(glofas_ocean_mask)    
        for jj in range(len(glofas_lat)):
            for ii in range(len(glofas_lon)):
            
                if (ldd_modified[jj,ii]==5) and (glofas_ocean_mask[jj,ii]==0) and (ocean_stencil_sum[jj,ii]>0):
                    # update ocean mask so counted in next calculation of the stencil sum
                    glofas_ocean_mask[jj,ii] = 1
                    n_updates+=1
                
    pour_points = (ldd_modified==5)*(ocean_stencil_sum>0)
    
    return pour_points

def get_mom_mask_for_glofas():
    # eliminate pour points outside of nep domain so they won't be mapped on the boundary in the d2s phase
    mom_to_glofas = xesmf.Regridder(
        {'lat': lat, 'lon': lon, 'lat_b': latb, 'lon_b': lonb},
        {'lon': glofas_lon, 'lat': glofas_lat, 'lon_b': glofas_lonb , 'lat_b': glofas_latb },
        method='conservative',
        periodic=True,
        reuse_weights=False)
    mom_mask_for_glofas = mom_to_glofas(np.ones((ocn_mask.shape)))
    
    mom_mask_for_glofas[mom_mask_for_glofas<.5]=0
    mom_mask_for_glofas[mom_mask_for_glofas>.5]=1
    
    return mom_mask_for_glofas.astype(bool)


def write_runoff(glofas, hgrid, coast_mask, out_file):
    # From Alistair
    area = (hgrid.area[::2, ::2] + hgrid.area[1::2, 1::2]) + (hgrid.area[1::2, ::2] + hgrid.area[::2, 1::2])

    pour_points = get_glofas_pour_points()
    glofas_mom_pour_points = pour_points*get_mom_mask_for_glofas()

    # Identify nearest coastal land point to GloFAS pour points
    # Source pour points indices
    flat_pour_point_mask = glofas_mom_pour_points.ravel().astype('bool')
    pour_lon = glo_lons.ravel()[flat_pour_point_mask]
    pour_lat = glo_lats.ravel()[flat_pour_point_mask]
    #linear index of glofas_elements
    glo_id = np.arange(np.prod(glofas_mom_pour_points.shape))
    pour_id = glo_id[flat_pour_point_mask]

    # Coastal destination indices
    # Flatten mask and coordinates to 1D
    flat_coast_mask = coast_mask.ravel().astype('bool')
    coast_lon = lon.ravel()[flat_coast_mask]
    coast_lat = lat.ravel()[flat_coast_mask]
    #linear index of mom elements
    mom_id = np.arange(np.prod(coast_mask.shape))
    coast_id = mom_id[flat_coast_mask]
    # Use xesmf to find the index of the nearest coastal cell
    # for every grid cell in the MOM domain
    glo_coast_to_mom = xesmf.Regridder(
       {'lat': coast_lat, 'lon': coast_lon},
       {'lat': pour_lat, 'lon': pour_lon},
       method='nearest_s2d',
       locstream_in=True,
       locstream_out=True,
       reuse_weights=False)

    nearest_glo_coast = glo_coast_to_mom(coast_id).ravel()
    
    tmp_glo_values = glofas.values

    # discharge on GloFAS grid, reshaped to 2D (time, grid_id)
    raw = tmp_glo_values.reshape([glofas.shape[0],-1])

    # Zero array that will be filled with runoff at coastal cells
    mom_glo_filled = np.zeros((raw.shape[0],np.prod(ocn_mask.shape)))

    # Loop over each GloFAS pour point and add it to the nearest coastal cell
    for mom_i, glo_i in zip(nearest_glo_coast,pour_id):
        mom_glo_filled[:, mom_i] += raw[:, glo_i] 

    # Hill et al product only extends to mid 2021 so only including through 2020
    if yr < 2021:
       hill_coast_to_mom = xesmf.Regridder({'lat': coast_lat, 'lon': coast_lon},
                                 {'lat': hill_lat, 'lon': hill_lon},
                                 method='nearest_s2d',
                                 locstream_in=True,
                                 locstream_out=True,
                                 reuse_weights=False) 
       nearest_hill_coast = hill_coast_to_mom(coast_id).ravel()
       # Loop over each GloFAS pour point and add it to the nearest coastal cell
       mom_hill_filled = np.zeros(([raw.shape[0],np.prod(ocn_mask.shape)]))
       for mom_i, hill_i in zip(nearest_hill_coast, range(len(nearest_hill_coast))):
           mom_hill_filled[:, mom_i] += hdis.values[:, hill_i]/(24*60*60) # m3 d-1 -> m3 s-1

       # replace glofas_filled indicies with hill values
       mom_glo_filled[:,np.unique(nearest_hill_coast)] = mom_hill_filled[:,np.unique(nearest_hill_coast)]

    # Reshape back to 3D and convert to kg m-2 s-1: multiply by 1000 kg m-3 and divide by grid cell area in m2
    filled_reshape = 1000*mom_glo_filled.reshape((glofas.shape[0],ocn_mask.shape[0],ocn_mask.shape[1]))/area.values

    # Convert to xarray
    ds = xarray.Dataset({
        'runoff': (['time', 'y', 'x'], filled_reshape),
        'area': (['y', 'x'], area.data),
        'lat': (['y', 'x'], lat.data),
        'lon': (['y', 'x'], lon.data)
        },
        coords={'time': glofas['time'].data, 'y': np.arange(filled_reshape.shape[1]), 'x': np.arange(filled_reshape.shape[2])}
    )

    # Drop '_FillValue' from all variables when writing out
    all_vars = list(ds.data_vars.keys()) + list(ds.coords.keys())
    encodings = {v: {'_FillValue': None} for v in all_vars}

    # Make sure time has the right units and datatype
    # otherwise it will become an int and MOM will fail. 
    encodings['time'].update({
        'units': 'days since 1950-01-01',
        'dtype': float, 
        'calendar': 'gregorian'
    })

    ds['time'].attrs = {'cartesian_axis': 'T'}
    ds['x'].attrs = {'cartesian_axis': 'X'}
    ds['y'].attrs = {'cartesian_axis': 'Y'}
    ds['lat'].attrs = {'units': 'degrees_north'}
    ds['lon'].attrs = {'units': 'degrees_east'}
    ds['runoff'].attrs = {'units': 'kg m-2 s-1'}

    # Write out
    ds.to_netcdf(
        out_file,
        unlimited_dims=['time'],
        format='NETCDF3_64BIT',
        encoding=encodings,
        engine='netcdf4'
    )
    ds.close()


if __name__ == '__main__':
    # Determine coastal points in NEP domain
    ocn_mask = xarray.open_dataset('/work/Liz.Drenkard/mom6/NEP_ocean_static_nomask.nc').wet.values.astype(bool)
    
    stencil_sum = 0 * ocn_mask
    
    # sum ocean mask values to the:     north          south                 east                   west
    stencil_sum[1:-1,1:-1] = ~ocn_mask[2:,1:-1] + ~ocn_mask[:-2,1:-1] + ~ocn_mask[1:-1,:-2] + ~ocn_mask[1:-1,2:]
    ## Domain Edges
    ### North     
    stencil_sum[-1,1:-1]   =                      ~ocn_mask[-2,1:-1]  + ~ocn_mask[-1,:-2]   + ~ocn_mask[-1,2:]
    ### South
    stencil_sum[0,1:-1]    = ~ocn_mask[1,1:-1]  +                       ~ocn_mask[0,:-2]    + ~ocn_mask[0,2:]
    ### East                          
    stencil_sum[1:-1,-1]   = ~ocn_mask[2:,-1]   + ~ocn_mask[:-2,-1]   +                       ~ocn_mask[1:-1,-2]    
    ### West                          
    stencil_sum[1:-1,0]    = ~ocn_mask[2:,0]    + ~ocn_mask[:-2,0]    + ~ocn_mask[1:-1,1]

    ## Domain Corners
    ## Northwest
    stencil_sum[-1,0]      =                      ~ocn_mask[-2,0]     + ~ocn_mask[-1,2]
    ## Northeast               
    stencil_sum[-1,-1]     =                      ~ocn_mask[-2,-1]    +                       ~ocn_mask[-1,-2]
    ## Southeast               
    stencil_sum[0,-1]      = ~ocn_mask[1,-1]    +                                             ~ocn_mask[0,-2]
    ## Southwest
    stencil_sum[0,0]       = ~ocn_mask[1,0]     +                       ~ocn_mask[0,1]
    
    coast = (ocn_mask)*(stencil_sum)

    # Load regional ocean hgrid
    hgrid = xarray.open_dataset( '/work/Liz.Drenkard/mom6/nep_10km/setup/grid/ocean_hgrid.nc')
    lon = hgrid.x[1::2, 1::2].values
    lonb = hgrid.x[::2, ::2].values
    lat = hgrid.y[1::2, 1::2].values
    latb = hgrid.y[::2, ::2].values 
     
    # Load GloFAS local drain direction map
    ldd = xarray.open_dataset('/work/Liz.Drenkard/mom6/nep_10km/setup/runoff/ncks_glofas/ldd_v4.0_NEP_subset.nc').ldd.values
    
    # GloFAS Version 3.1: Mackenzie river patch
    #ldd[132,743:746]=5

    yr=int(sys.argv[1])
    # GloFAS 4.0 subset to model region:
    glo_files = [f'/work/Liz.Drenkard/mom6/nep_10km/setup/runoff/ncks_glofas/glofas_v4.0_nep_subset_{y}.nc' for y in [yr-1, yr, yr+1]]


    glofas = (
         xarray.open_mfdataset(glo_files, combine='by_coords')
         .rename({'latitude': 'lat', 'longitude': 'lon'})
	 .sel(time=slice(f'{yr-1}-12-31 12:00:00', f'{yr+1}-01-01 12:00:00'))
         .dis24)
     
    glofas_lat = glofas['lat'].values 
    glofas_lon = glofas['lon'].values
    glofas_lon[glofas_lon<0]=glofas_lon[glofas_lon<0]+360
    deg_incr = abs(np.unique(np.diff(glofas_lat))[0]) 
    # updated icrement for  version 4.0 of GloFAS, assumes constant diff for both lats & lons : 
    glofas_latb = np.arange(glofas_lat[0] + deg_incr/2., glofas_lat[-1]-deg_incr, -deg_incr)
    glofas_lonb = np.arange(glofas_lon[0] - deg_incr/2., glofas_lon[-1]+deg_incr, deg_incr) 
    glo_lons,glo_lats = np.meshgrid(glofas_lon,glofas_lat) 
    
    #print(glofas_lonb.shape,glofas_lon.shape,glofas_latb.shape,glofas_lat.shape) 
    
    # UNCOMMENT FOR HILL DATA
    if yr < 2021: 
        hill_files = [f'/work/Liz.Drenkard/external_data/goa_freshwater_discharge/goa_dischargex_0901{y}_0831{y+1}.nc' for y in [yr-1, yr]]
        hill = xarray.open_mfdataset(hill_files,combine='nested',concat_dim='time')
        hill['time'] = pd.to_datetime([(str(hill.year.values[nt])+'-'+str(hill.month.values[nt]).zfill(2)+'-'+str(hill.day.values[nt]).zfill(2)) for nt in range(len(hill.day))])

    # using climatological hill data with 2021 half year
    elif yr == 2021:
        hill_files = ['/work/Liz.Drenkard/external_data/goa_freshwater_discharge/goa_dischargex_09012020_08312021.nc',
                     '/work/Liz.Drenkard/external_data/goa_freshwater_discharge/goa_dischargex_09011991_08312021_clim.nc']
        hill = xarray.open_mfdataset(hill_files,combine='nested',concat_dim='time')
        years = hill.year.values
        years[years==1992] = 2021
        years[years==1993] = 2022
        hill['time'] = pd.to_datetime([(str(years[nt])+'-'+str(hill.month.values[nt]).zfill(2)+'-'+str(hill.day.values[nt]).zfill(2)) for nt in range(len(hill.day))])

    # using only hill climatological data
    else:
        hill_files = ['/work/Liz.Drenkard/external_data/goa_freshwater_discharge/goa_dischargex_09011991_08312021_clim.nc',
                     '/work/Liz.Drenkard/external_data/goa_freshwater_discharge/goa_dischargex_09011991_08312021_clim.nc']
        hill = xarray.open_mfdataset(hill_files,combine='nested',concat_dim='time')
        years = hill.year.values
        months = hill.month.values
        days = hill.day.values

        # updating the years and days for respective years
        middle_year_start = np.argmax(years)
        years[:middle_year_start] = yr-1
        middle_year_seam_start = np.argmin(years) + int(yr%4==0) # leap year condition on the end 

        # leap year condition for updating days, months
        if yr%4 == 0:
            # find location of 28th day of february
            leap_day_28 = np.where(days==28)[0][5]
            # add "29" day after Feb 28 (shifts days by 1 day); drop last day in file
            days = np.append(np.append(days[:leap_day_28+1],29),days[leap_day_28+1:-1])
            # add "2" day after Feb 28 (shifts months by 1 day); drop last day in file
            months = np.append(np.append(months[:leap_day_28+1],2),months[leap_day_28+1:-1])
            
        years[middle_year_start:middle_year_seam_start] = yr
        middle_year_end = np.argmax(years==1993) + int(yr%4==0) # leap year condition on the end
        years[middle_year_seam_start:middle_year_end] = yr
        years[middle_year_end:] = yr+1

        hill['time'] = pd.to_datetime([(str(years[nt])+'-'+str(months[nt]).zfill(2)+'-'+str(days[nt]).zfill(2)) for nt in range(len(hill.day))])

    hdis = hill.sel(time=slice(f'{yr-1}-12-31 12:00:00', f'{yr+1}-01-01 12:00:00')).q   
    hill_lat = hill.lat.values
    hill_lon = hill.lon.values
    hill_lon[hill_lon<0]=hill_lon[hill_lon<0]+360
        
    #
    outdir = sys.argv[2]
    out_file = outdir + 'glofas_v4_hill_dis_runoff_' +str(yr) + '.nc' 
    print('Calling Write command')
    write_runoff(glofas, hgrid, coast, out_file)


