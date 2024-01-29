"""
Compare model vertical profiles of seasonal temperature climatologies in four different northeast US ecological production units from Glorys data
How to use:
python temp_profile.py /archive/acr/fre/NWA/2023_04/NWA12_COBALT_2023_04_kpo4-coastatten-physics/gfdl.ncrc5-intel22-prod
"""
from matplotlib.lines import Line2D
import matplotlib.pyplot as plt
import numpy as np

from string import ascii_lowercase
import xarray

import os
import sys

# Get the directory of the current script
script_dir = os.path.dirname(os.path.abspath(__file__))
sys.path.append(os.path.join(script_dir, '../'))
from plot_common import open_var, save_figure

long_names = {
    'SS': 'Scotian Shelf--Eastern Gulf of Maine',
    'GOM': 'Gulf of Maine',
    'GB': 'Georges Bank',
    'MAB': 'Mid-Atlantic Bight'
}
season_colors = {'DJF': '#377eb8', 'MAM': '#4daf4a', 'JJA': '#e41a1c', 'SON': '#ff7f00'} 

def plot_temp_profile(pp_root, label):
    mod_temp = open_var(pp_root, 'ocean_monthly_z', 'thetao')
    mod_salt = open_var(pp_root, 'ocean_monthly_z', 'so')
    mod = xarray.merge((mod_temp, mod_salt)).sel(time=slice('1993-03-01', '2019-11-30'))
    mod_climo = mod.sel(z_l=slice(0, 200)).groupby('time.season').mean('time')
    masks = xarray.open_dataset('../../data/geography/regions_60m.nc')
    glorys = xarray.open_dataset('../../data/diagnostics/glorys_epu_3d.nc')
    glorys_climo = glorys.sel(time=slice('1993-03-01', '2019-11-30')).groupby('time.season').mean('time')

    f, axs = plt.subplots(2, 2, figsize=(10, 8))

    for epu, ax, letter in zip(long_names.keys(), axs.flat, ascii_lowercase):
        glorys_epu = glorys_climo.sel(region=epu)
        mod_epu = mod_climo.weighted(masks['areacello'].where(masks[epu]).fillna(0)).mean(['yh', 'xh']).load()
        
        for s, c in season_colors.items():
            y = mod_epu.sel(season=s).thetao
            ax.plot(y, mod_epu.z_l, c=c, label=s)
            
            #
            y = glorys_epu.sel(season=s).thetao
            ax.plot(y, glorys_epu.depth, c=c, linestyle=':')
        
        name = long_names[epu]
        ax.set_title(f'({letter}) {name} EPU', fontsize=10)
        ax.set_xlabel('Potential temperature (℃)')
        ax.set_ylabel('Depth (m)')

        ax.set_ylim(0, 150)
        ax.set_xlim(4, 22)
        ax.set_xticks(np.arange(4, 23, 2))
        ax.set_xticklabels([t if t % 4 == 0 else '' for t in np.arange(4, 23, 2)])
        ax.set_yticks(np.arange(0, 151, 10))
        ax.set_yticklabels([t if t % 20 == 0 else '' for t in np.arange(0, 151, 10)])
        ax.invert_yaxis()
        
    f.subplots_adjust(hspace=0.3)

    handles = [Line2D([0], [0], color=c) for c in season_colors.values()]
    legend = f.legend(handles, season_colors.keys(), loc='center right', frameon=False, title='Season', bbox_to_anchor=(-0, 0, 1.01, 1.15))
    legend._legend_box.align = 'left' # Left align title text

    handles = [Line2D([0], [0], color='k', linestyle=ls) for ls in ['-', ':']]
    legend = f.legend(handles, ['Model', 'GLORYS12'], loc='center right', frameon=False, title='Dataset', bbox_to_anchor=(-0, 0, 1.05, 0.85))
    legend._legend_box.align = 'left' # Left align title text
    save_figure('epu_temp_profile', label, pdf=True, output_dir='../figures')


if __name__ == '__main__':
    from argparse import ArgumentParser
    parser = ArgumentParser()
    parser.add_argument('pp_root', help='Path to postprocessed data (up to but not including /pp/)')
    parser.add_argument('-l', '--label', help='Label to add to figure file names', type=str, default='')
    args = parser.parse_args()
    plot_temp_profile(args.pp_root, args.label)



