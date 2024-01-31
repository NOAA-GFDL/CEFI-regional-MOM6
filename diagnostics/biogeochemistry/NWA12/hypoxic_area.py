"""
Compare monthly climatologies of hypoxic area (area with a July
mean bottom oxygen concentration below 2 mg L-1 over over the LA-TX Shelf between the model and geostatistical estimates from Matli et al. (2020)  
How to use:
python hypoxic_area.py /archive/acr/fre/NWA/2023_04/NWA12_COBALT_2023_04_kpo4-coastatten-physics/gfdl.ncrc5-intel22-prod --daily
"""
from calendar import month_abbr
import cartopy.crs as ccrs
import datetime as dt
from matplotlib.legend_handler import HandlerTuple
import matplotlib.pyplot as plt
import numpy as np
import pandas as pd
import xarray
import xskillscore as skill

PC = ccrs.PlateCarree()

import os
import sys

# Get the directory of the current script
script_dir = os.path.dirname(os.path.abspath(__file__))
sys.path.append(os.path.join(script_dir, '../../physics'))
from plot_common import open_var, save_figure


def date_parser(x):
    if isinstance(x, dt.datetime):
        return pd.to_datetime(x)
    else:
        return pd.to_datetime(x, format='%b-%y')


def plot_hypoxic_area(pp_root, label, use_daily):
    mom_grid = xarray.open_dataset('../../data/geography/ocean_static.nc')
    if use_daily:
        o2 = open_var(pp_root, 'ocean_cobalt_daily_2d', 'btm_o2') * 32 * 1035 # mol kg-1 -> mg l-1
    else:
        o2 = open_var(pp_root, 'ocean_cobalt_btm', 'btm_o2') * 32 * 1035
    mask = (
        (mom_grid.geolon >= -94.605) &
        (mom_grid.geolon <= -89.512) & 
        (mom_grid.geolat >= 28.219) & 
        (mom_grid.geolat <= 29.717) &
        (mom_grid.deptho <= 100)
    )
    hypoxic_area = (o2.where((mask) & (o2 < 2)) * mom_grid.areacello).sum(['yh', 'xh']).load()
    hypoxic_area /= (1000**2) # m2 -> km2

    if use_daily:
        hypoxic_area = hypoxic_area.resample(time='1MS').mean('time')

    df = pd.read_excel('../../data/obs/matli_average_hypoxic_extent.xlsx', index_col='date', parse_dates=True, date_parser=date_parser)

    mod_july = hypoxic_area.sel(time=hypoxic_area['time.month']==7).to_pandas()
    mod_july.index = mod_july.index.year
    mod_july.name = 'Model'

    obs_july = df.loc[df.index.month==7]
    obs_july.index = obs_july.index.year

    plot_df = pd.concat([obs_july, mod_july], axis=1)
    o = plot_df.Mean.to_xarray()
    m = plot_df.Model.to_xarray()

    f, axs = plt.subplots(2, 1, figsize=(8, 8))
    ax = axs[0]
    df.loc['1993':'2017'].groupby(lambda x: x.month).mean().Mean.plot(ax=ax, c='k', label='Matli et al.')
    hypoxic_area.sel(time=slice('1993', '2017')).groupby('time.month').mean('time').plot(ax=ax, c='r', label='Model')
    ax.set_ylabel('Hypoxic area (km$^2$)')
    ax.set_ylim(0, 18000)
    ax.set_xlabel('')
    ax.set_title('(a) West LA-TX shelf hypoxic area climatology (1993-2017)')
    ax.legend(loc='upper left', frameon=False)
    ax.set_xticks(np.arange(1, 13))
    ax.set_xticklabels(month_abbr[1:13])
    ax.set_xlim(1, 12)

    ax = axs[1]
    p2 = ax.fill_between(plot_df.index, plot_df.LCI, plot_df.UCI, color='#bbbbbb', label='Matli et al.')
    p0 = ax.plot(plot_df.index, plot_df.Mean, c='k')
    p1 = ax.plot(plot_df.index, plot_df.Model, c='r')
    ax.legend(
        [(p0[0], p2), p1[0]], ['Matli et al.', 'Model'], 
        handler_map={tuple: HandlerTuple(ndivide=None)},
        frameon=False,
        loc='upper left'
    )

    ax.set_xlim(1985, 2019)
    ax.set_ylabel('Hypoxic area (km$^2$)')
    ax.set_ylim(0, 35000)
    ax.set_title('(b) July mean hypoxic area')

    bias = float(skill.me(m, o, skipna=True))
    rmse = float(skill.rmse(m, o, skipna=True))
    corr = float(skill.pearson_r(m, o, skipna=True))
    mdae = float(skill.median_absolute_error(m, o, skipna=True))

    ax.text(2011, 33500-200, f'Bias: {bias:2.0f}')
    ax.text(2011, 32000-200, f'RMSE: {rmse:2.0f}')
    ax.text(2011, 29000-200, f'Corr: {corr:2.2f}')
    ax.text(2011, 30500-200, f'MedAE: {mdae:2.0f}')

    kind = 'daily' if use_daily else 'monthly'
    save_figure(f'hypoxic_area_from_{kind}', label=label, pdf=True, output_dir='../figures')


if __name__ == '__main__':
    from argparse import ArgumentParser
    parser = ArgumentParser()
    parser.add_argument('pp_root', help='Path to postprocessed data (up to but not including /pp/)')
    parser.add_argument('-l', '--label', help='Label to add to figure file names', type=str, default='')
    parser.add_argument('-D', '--daily', help='Use monthly data', action='store_true')
    args = parser.parse_args()
    plot_hypoxic_area(args.pp_root, args.label, args.daily)
