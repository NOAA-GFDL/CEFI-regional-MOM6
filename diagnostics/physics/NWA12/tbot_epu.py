"""
Compare annual average bottom-temperature anomalies in four different northeast US ecological production units from model,
reanalysis, and observed data
How to use:
python tbot_epu.py /archive/acr/fre/NWA/2023_04/NWA12_COBALT_2023_04_kpo4-coastatten-physics/gfdl.ncrc5-intel22-prod/ 
"""

from datetime import datetime, timedelta
import matplotlib.pyplot as plt
import pandas as pd
from string import ascii_lowercase
import xarray
import os
import sys

# Get the directory of the current script
script_dir = os.path.dirname(os.path.abspath(__file__))
sys.path.append(os.path.join(script_dir, '../'))
from plot_common import open_var


# Convert decimal date to a datetime object
# https://stackoverflow.com/questions/20911015/decimal-years-to-datetime-in-python/20911144#20911144
def decimal_to_dt(decimal):
    year = int(decimal)
    rem = decimal - year
    base = datetime(year, 1, 1)
    result = base + timedelta(seconds=(base.replace(year=base.year + 1) - base).total_seconds() * rem)
    return result


def load_ecodata(epu):
    ecodata = pd.read_csv(f'/net2/acr/ecodata/data-raw/bot_temp_{epu}.csv')
    ecodata['Time'] = ecodata['Time'].apply(decimal_to_dt)
    ecodata = ecodata.set_index(['Time', 'Var']).squeeze().unstack(level='Var')
    ecodata.index = ecodata.index.round('1D')
    ecodata.index.name = 'time'
    # Average to start of month
    monthly = ecodata['Tbot_anom'].resample('1MS').mean()
    return monthly


def epu_average(var, area):
    ave = var.weighted(area).mean(['yh', 'xh']).compute()
    # Note anomalies from ecodata/SOE are supposed to be relative to a 1981--2010 climatology. 
    anom = ave.groupby('time.month') - ave.sel(time=slice('1993', '2010')).groupby('time.month').mean('time')
    # Resample so data is indexed by start of month
    monthly = anom.resample(time='1MS').first()
    return monthly.to_pandas()


def plot_tbot_epu(pp_root):
    grid = xarray.open_dataset('../../data/geography/ocean_static.nc')
    masks = xarray.open_dataset('../../data/geography/EPU.nc')
    masked_area = grid['areacello'].where(masks).fillna(0)
    glorys = xarray.open_dataset('../../data/diagnostics/glorys_epu.nc')

    model_monthly = open_var(pp_root, 'ocean_monthly', 'tob')

    long_names_ordered = {
        'SS': 'Scotian Shelf',
        'GOM': 'Gulf of Maine',
        'GB': 'Georges Bank',
        'MAB': 'Mid-Atlantic Bight'
    }

    glorys_color = '#648fff'
    model_color = '#dc267f'
    lw = 1.5

    f, axs = plt.subplots(2, 2, figsize=(12, 8))

    for epu, ax, letter in zip(long_names_ordered, axs.flat, ascii_lowercase):
        mod = epu_average(model_monthly, masked_area[epu])
        glo = glorys['tob_anom'].sel(EPU=epu).to_series()
        obs = load_ecodata(epu)
        combined = pd.concat((mod, glo, obs), axis=1, keys=['mod', 'glorys', 'obs']).dropna()
        annual = combined.resample('1AS').mean()
        obs_corr = annual.corr().loc['mod', 'obs']
        glo_corr = annual.corr().loc['mod', 'glorys']
        annual['mod'].plot(label='Model', c=model_color, lw=lw, ax=ax)
        annual['glorys'].plot(label=f'GLORYS12 (r={glo_corr:2.2f})', c=glorys_color, lw=lw, ax=ax)    
        annual['obs'].plot(label=f'Observed (r={obs_corr:2.2f})', c='k', lw=lw, ax=ax)  
        name = long_names_ordered[epu]
        ax.set_title(f'({letter}) {name}')
        
    for ax in axs.flat:
        ax.set_xlim('1992', '2020')
        ax.set_xlabel('')
        ax.set_ylabel('Bottom temp. anomaly (℃)')
        ax.set_ylim(-2.75, 2.5)
        ax.legend(loc='lower right', frameon=False)

    plt.savefig(f'../figures/tbotepu.png', dpi=200, bbox_inches='tight')


if __name__ == '__main__':
    from argparse import ArgumentParser
    parser = ArgumentParser()
    parser.add_argument('pp_root', help='Path to postprocessed data (up to but not including /pp/)')
    args = parser.parse_args()
    plot_tbot_epu(args.pp_root)
