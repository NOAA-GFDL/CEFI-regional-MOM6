"""
Plot model-data comparison for Northeast Channel temperature and salinity
How to use:
python nechannel.py /archive/acr/fre/NWA/2023_04/NWA12_COBALT_2023_04_kpo4-coastatten-physics/gfdl.ncrc5-intel22-prod/ 
"""

import datetime as dt
import gsw
import h5py
import matplotlib.gridspec as gridspec
import matplotlib.pyplot as plt
import numpy as np
import pandas as pd
from scipy.io import loadmat
import xarray
import os
import sys

# Get the directory of the current script
script_dir = os.path.dirname(os.path.abspath(__file__))
sys.path.append(os.path.join(script_dir, '../'))
from plot_common import open_var, save_figure



# Scotian Shelf Water
T1 = 2
S1 = 32

# Warm Slope Water
T2 = 12
S2 = 35.4

# Labrador Slope Water
T3 = 6
S3 = 34.6


glorys_color = '#648fff'
mooring_color = '#ffb000'
survey_color =  '#ffb000'
model_color = '#dc267f'


def percent_masses(temp, salt):
    delta = T1 * (S2 - S3) - S1 * (T2 - T3) + T2 * S3 - T3 * S2
    m1 = (temp * (S2 - S3) + salt * (T3 - T2) + T2 * S3 - T3 * S2) / delta
    m2 = (temp * (S3 - S1) + salt * (T1 - T3) + T3 * S1 - T1 * S3) / delta
    m3 = (temp * (S1 - S2) + salt * (T2 - T1) + T1 * S2 - T2 * S1) / delta
    return xarray.Dataset({'SSW': m1, 'WSW': m2, 'LSW': m3}) * 100 # -> %


def to_yearly_series(da):
    pa = da.to_pandas()
    pa.index = pa.index.year
    pa.index.name = 'year'
    return pa


def load_casts():
    """
    Load CTD casts. Casts were saved as different versions of matlab files,
    an older version that can be read with loadmat and a newer version
    in HDF format.
    """
    casts = []
    for year in range(1977, 2021): 
        print(year)
        # Try using loadmat. If it's a newer version, use h5py instead.
        try:
            m = loadmat(f'/net2/acr/nefsc/casts_{year}.mat', squeeze_me=True, simplify_cells=True)
        except:
            ds = h5py.File(f'/net2/acr/nefsc/casts_{year}.mat','r')
            ncast = len(ds[f'casts_{year}']['lat'])
            lat = np.squeeze(ds[f'casts_{year}']['lat'][:])
            lon = np.squeeze(ds[f'casts_{year}']['lon'][:])
            p = np.squeeze(ds[f'casts_{year}']['p'][:])
            s = np.squeeze(ds[f'casts_{year}']['s'][:])
            t = np.squeeze(ds[f'casts_{year}']['t'][:])
            yr = np.squeeze(ds[f'casts_{year}']['yr'][:])
            yd = np.squeeze(ds[f'casts_{year}']['yd'][:])
            for i in range(ncast):
                i_lat = float(ds[lat[i]][:])
                i_lon = float(ds[lon[i]][:])
                i_p = ds[p[i]][:].squeeze()
                if i_lat >= 42.2 and i_lat <= 42.6 and i_lon <= 66.8 and i_lon >= 66 and i_p.max() >= 200:
                    if np.logical_and(i_p >= 130, i_p <= 150).any() and np.logical_and(i_p >= 200, i_p <= 220).any():
                        i_s = ds[s[i]][:].squeeze()
                        i_t = ds[t[i]][:].squeeze()
                        i_yr = int(ds[yr[i]][:])
                        i_yd = int(ds[yd[i]][:])
                        save = np.interp(np.arange(150, 201), i_p, i_s).mean()
                        sa = gsw.conversions.SA_from_SP(i_s, i_p, i_lon*-1, i_lat)
                        theta = gsw.conversions.pt_from_t(sa, i_t, i_p, 0)
                        tave = np.interp(np.arange(150, 201), i_p, theta).mean()
                        date = dt.datetime(i_yr, 1, 1) + dt.timedelta(days=i_yd-1)
                        res = pd.Series({'salinity': save, 'temperature': tave, 'date': date})
                        casts.append(res)
        else:
            for cast in m[f'casts_{year}']:
                if cast['lat'] >= 42.2 and cast['lat'] <= 42.6 and cast['lon'] <= 66.8 and cast['lon'] >= 66 and cast['p'].max() >= 200:
                    if np.logical_and(cast['p'] >= 130, cast['p'] <= 150).any() and np.logical_and(cast['p'] >= 200, cast['p'] <= 220).any():
                        save = np.interp(np.arange(150, 201), cast['p'], cast['s']).mean()
                        sa = gsw.conversions.SA_from_SP(cast['s'], cast['p'], cast['lon']*-1, cast['lat'])
                        theta = gsw.conversions.pt_from_t(sa, cast['t'], cast['p'], 0)
                        tave = np.interp(np.arange(150, 201), cast['p'], theta).mean()
                        date = dt.datetime(cast['yr'], 1, 1) + dt.timedelta(days=cast['yd']-1)
                        res = pd.Series({'salinity': save, 'temperature': tave, 'date': date})
                        casts.append(res)

    casts = pd.concat(casts, axis=1).T.set_index('date').dropna()
    return casts


def plot_nechannel(pp_root, label):
    grid = xarray.open_dataset('../../data/geography/ocean_static.nc')
    model = xarray.merge([open_var(pp_root, 'ocean_monthly_z', v) for v in ['thetao', 'so']])   
    if '01_l' in model.coords:
        model = model.rename({'01_l': 'z_l'})

    # Select box representing NE channel
    channel_box = dict(yh=slice(42.2, 42.6), xh=slice(-66.8, -66))
    grid_sliced = grid.sel(**channel_box)
    weight = grid_sliced['areacello'].fillna(0)
    mod_sliced = model.sel(**channel_box)
    layer = mod_sliced.interp(z_l=np.arange(150, 201)).mean('z_l')
    model_means = (
        layer
        .weighted(weight)
        .mean(['xh', 'yh'])
        .load()
        .drop('z_l', errors='ignore')
    )
    model_annual = model_means.resample(time='1AS').mean('time')
    model_masses = percent_masses(model_annual['thetao'], model_annual['so'])

    glorys_means = xarray.open_dataset('../../data/diagnostics/monthly_nechannel_glorys.nc')
    glorys_annual = glorys_means.resample(time='1AS').mean('time')
    glorys_masses = percent_masses(glorys_annual['thetao'], glorys_annual['so'])
    
    bias = model_means.mean('time') - glorys_means.mean('time')

    mooring = (
        xarray.open_dataset('../../data/diagnostics/N01.nc')
        .sel(depth=180)
        .resample(time='1MS')
        .mean('time')
    )
    mooring_annual = mooring.resample(time='1AS').mean('time')
    mooring_masses = percent_masses(mooring_annual['temperature'], mooring_annual['salinity'])

    casts = load_casts()
    monthly_casts = casts.resample('1MS').mean()
    yearly_casts = monthly_casts.resample('1AS').mean()
    matlab_masses = to_yearly_series(percent_masses(yearly_casts.temperature, yearly_casts.salinity))

    # Assemble dataframes for easier plotting
    ssw_df = pd.DataFrame({
        'Model': to_yearly_series(model_masses['SSW']),
        'CTDs': matlab_masses['SSW'],
        'Mooring': to_yearly_series(mooring_masses['SSW']),
        'GLORYS': to_yearly_series(glorys_masses['SSW'])
    })
    lsw_df = pd.DataFrame({
        'Model': to_yearly_series(model_masses['LSW']),
        'CTDs': matlab_masses['LSW'],
        'Mooring': to_yearly_series(mooring_masses['LSW']),
        'GLORYS': to_yearly_series(glorys_masses['LSW'])
    })
    lsw_corr = lsw_df.corr()
    wsw_df = pd.DataFrame({
        'Model': to_yearly_series(model_masses['WSW']),
        'CTDs': matlab_masses['WSW'],
        'Mooring': to_yearly_series(mooring_masses['WSW']),
        'GLORYS': to_yearly_series(glorys_masses['WSW'])
    })
    wsw_corr = wsw_df.corr()

    fig = plt.figure(figsize=(9, 6), tight_layout=True)
    gs = gridspec.GridSpec(2, 2)
    size = 1

    ax = fig.add_subplot(gs[:, 0])
    ax.plot([S2, S3, S1, S2], [T2, T3, T1, T2], c='#bbbbbb', lw=1)
    model_means.plot.scatter(x='so', y='thetao', s=size, c=model_color, edgecolor=model_color, ax=ax, label='Model', zorder=100)
    casts.plot.scatter(x='salinity', y='temperature', s=size, c='k', ax=ax, label='CTDs')
    mooring.plot.scatter(x='salinity', y='temperature', s=size, c=mooring_color, edgecolor=mooring_color,  ax=ax, label='Mooring')
    glorys_means.plot.scatter(x='so', y='thetao', s=size, c=glorys_color, edgecolor=glorys_color, ax=ax, label='GLORYS12')
    ax.set_xlim(31.75, 35.75)
    ax.set_ylim(1, 13)
    ax.text(S2-.3, T2, 'Warm\nslope')
    ax.text(S3, T3-.5, 'Labrador\nslope')
    ax.text(S1-.05, T1+.5, 'Scotian\nShelf')
    ax.set_xlabel('Monthly mean salinity')
    ax.set_ylabel('Monthly mean potential temperature (°C)')
    ax.set_title('(a) Temperature and salinity in NE channel')
    ax.legend(loc='upper left', frameon=False, markerscale=4)
    ax.text(34, 2, f'Model vs. GLORYS12:\nT bias: {bias["thetao"]:2.2f} °C\nS bias: {bias["so"]:2.2f}')

    ax = fig.add_subplot(gs[0, 1])
    lsw_df['Model'].plot(ax=ax, c=model_color, label='Model')
    lsw_df['CTDs'].plot(ax=ax, c='k', label=f'CTDs (r={lsw_corr.loc["Model", "CTDs"]:2.2f})')
    lsw_df['Mooring'].plot(ax=ax, c=mooring_color, label=f'Mooring (r={lsw_corr.loc["Model", "Mooring"]:2.2f})')
    lsw_df['GLORYS'].plot(ax=ax, c=glorys_color, label=f'GLORYS12 (r={lsw_corr.loc["Model", "GLORYS"]:2.2f})')
    ax.set_title('(b) Percent of Labrador slope water')
    ax.set_xlabel('')
    ax.set_xlim(1992, 2020)
    ax.set_ylim(0, 100)
    ax.set_ylabel('Water composition (%)')
    ax.legend(loc='upper left', frameon=False, fontsize=8, ncol=2)

    ax = fig.add_subplot(gs[1, 1])
    wsw_df['Model'].plot(ax=ax, c=model_color, label='Model')
    wsw_df['CTDs'].plot(ax=ax, c='k', label=f'CTDs \n(r={wsw_corr.loc["Model", "CTDs"]:2.2f})')
    wsw_df['Mooring'].plot(ax=ax, c=mooring_color, label=f'Mooring (r={lsw_corr.loc["Model", "Mooring"]:2.2f})')
    wsw_df['GLORYS'].plot(ax=ax, c=glorys_color, label=f'GLORYS12\n (r={wsw_corr.loc["Model", "GLORYS"]:2.2f})')
    ax.set_title('(c) Percent of warm slope water')
    ax.set_xlabel('')
    ax.set_xlim(1992, 2020)
    ax.set_ylim(0, 100)
    ax.set_ylabel('Water composition (%)')
    ax.legend(loc='upper left', ncol=2, frameon=False, fontsize=8)

    save_figure('nechannel', label=label, pdf=True, output_dir='../figures')

    for name, df in dict(wsw=wsw_df, lsw=lsw_df, ssw=ssw_df).items():
        if label == '':
            fname = f'../figures/nechannel_{name}.nc'
        else:
            fname = f'../figures/nechannel_{label}_{name}.nc'
        xarray.Dataset.from_dataframe(df).to_netcdf(fname)


if __name__ == '__main__':
    from argparse import ArgumentParser
    parser = ArgumentParser()
    parser.add_argument('pp_root', help='Path to postprocessed data (up to but not including /pp/)')
    parser.add_argument('-l', '--label', help='Label to add to figure file names', type=str, default='')
    args = parser.parse_args()
    plot_nechannel(args.pp_root, args.label)
