import numpy as np
from os import path
import xarray

def uvt_hgrid(hgrid):
    u = (
        hgrid
        [['x', 'y']]
        .isel(nxp=slice(0, None, 2), nyp=slice(1, None, 2))
        .rename({'y': 'lat', 'x': 'lon', 'nxp': 'xq', 'nyp': 'yh'})
    )

    v = (
        hgrid
        [['x', 'y']]
        .isel(nxp=slice(1, None, 2), nyp=slice(0, None, 2))
        .rename({'y': 'lat', 'x': 'lon', 'nxp': 'xh', 'nyp': 'yq'})
    )

    t = (
        hgrid
        [['x', 'y']]
        .isel(nxp=slice(1, None, 2), nyp=slice(1, None, 2))
        .rename({'y': 'lat', 'x': 'lon', 'nxp': 'xh', 'nyp': 'yh'})
    )

    return u, v, t

def mult(width, total_width=100):
    i = np.arange(1, total_width+1)
    return 1 - np.tanh((2/np.e)*(i-1)/(width-1))


def create_damping(shape, nsponge, s_width, e_width, n_width, rate):
    assert rate < 1
    mult_south = np.zeros(shape)
    mult_east = np.zeros(shape)
    mult_north = np.zeros(shape)
    mult_south[0:nsponge, :] = mult(s_width, total_width=nsponge)[0:nsponge, np.newaxis]
    mult_east[:, -nsponge:] = np.fliplr(mult(e_width, total_width=nsponge)[np.newaxis, 0:nsponge])
    mult_north[-nsponge:, :] = np.flipud(mult(n_width, total_width=nsponge)[0:nsponge, np.newaxis])
    combined = np.maximum(mult_south, mult_east)
    combined = np.maximum(combined, mult_north)
    tanh = combined * rate
    return tanh


def write_damping(hgrid, output_dir, nsponge, width, rate, suffix=None):
    target_u, target_v, target_t = uvt_hgrid(hgrid)
    
    s_dy = hgrid['dy'].isel(ny=0).mean()
    s_width = int(np.round(width / 2 / s_dy))

    e_dx = hgrid['dx'].isel(nx=-1).mean()
    e_width = int(np.round(width * 2 / e_dx))
    
    # For NWA12: limit to part over ocean
    n_dy = hgrid['dy'].isel(ny=-1, nxp=slice(1000, None)).mean()
    n_width = int(np.round(width / n_dy))
    
    uv_ds = xarray.Dataset(
        data_vars=dict(
            Idamp_u=(['yh', 'xq'], create_damping(target_u.lon.shape, nsponge, s_width, e_width, n_width, rate)),
            Idamp_v=(['yq', 'xh'], create_damping(target_v.lon.shape, nsponge, s_width, e_width, n_width, rate))
        ),
        coords=dict(
            xh=target_v.xh,
            xq=target_u.xq,
            yh=target_u.yh,
            yq=target_v.yq
        )
    )
    for v in ['Idamp_u', 'Idamp_v']:
        uv_ds[v].attrs['units'] = 's-1'
        uv_ds[v].attrs['cell_methods'] = 'time: point'
    encodings = {v: {'dtype': np.int32} for v in ['xh', 'xq', 'yh', 'yq']}
    encodings.update({v: {'_FillValue': None} for v in ['Idamp_u', 'Idamp_v']})
    fname = 'damping_tgb_uv.nc' if suffix is None else f'damping_tanh_uv_{suffix}.nc'
    uv_ds.to_netcdf(
        path.join(output_dir, fname), 
        format='NETCDF3_64BIT',
        engine='netcdf4',
        encoding=encodings
    )
    
    t_ds = xarray.Dataset(
        data_vars=dict(
            Idamp=(['yh', 'xh'], create_damping(target_t.lon.shape, nsponge, s_width, e_width, n_width, rate))
        ),
        coords=dict(
            xh=target_t.xh,
            yh=target_t.yh
        )
    )
    t_ds['Idamp'].attrs['units'] = 's-1'
    t_ds['Idamp'].attrs['cell_methods'] = 'time: point'
    encodings = {v: {'dtype': np.int32} for v in ['xh', 'yh']}
    encodings.update({'Idamp': {'_FillValue': None}})
    fname = 'damping_tgb_t.nc' if suffix is None else f'damping_tanh_t_{suffix}.nc'
    t_ds.to_netcdf(
        path.join(output_dir, fname),
        format='NETCDF3_64BIT',
        engine='netcdf4',
        encoding=encodings
    )


if __name__ == '__main__':
    import argparse
    from yaml import safe_load
    parser = argparse.ArgumentParser()
    parser.add_argument('-c', '--config')
    args = parser.parse_args()
    with open(args.config, 'r') as file: 
        config = safe_load(file)
    hgrid = xarray.open_dataset(config['filesystem']['ocean_hgrid'])
    write_damping(hgrid, './', 250, 175e3, 1 / (7 * 24 * 3600))
