"""
Sample usage:
 sbatch compute_tides_job.sh
"""
import cartopy.crs as ccrs
from cartopy.mpl.geoaxes import GeoAxes
from matplotlib.colors import BoundaryNorm, ListedColormap
import matplotlib.pyplot as plt
from mpl_toolkits.axes_grid1 import AxesGrid
import numpy as np
import xarray
import xesmf

from compute_tides import open_grid_file

PC = ccrs.PlateCarree()

def get_map_norm(cmap, levels, no_offset=True):
    """
    Get a discrete colormap and normalization for plotting with matplotlib.
    Set no_offset=False to obtain a colormap that is similar to what xarray.plot() yields.
    """
    nlev = len(levels)
    cmap = plt.cm.get_cmap(cmap, nlev-int(no_offset))
    colors = list(cmap(np.arange(nlev)))
    cmap = ListedColormap(colors, "")
    norm = BoundaryNorm(levels, ncolors=nlev, clip=False)
    return cmap, norm


# Periods of each harmonic constituent in hours.
# (for converting phase from degrees to hours)
periods = {
    'M2': 12.42, 
    'S2': 12, 
    'N2': 12.66,
    'K2': 11.97,
    'K1': 23.93, 
    'O1': 25.82,
    'P1': 24.07,
    'Q1': 26.87,
    'MF': 327.9,
    'MM': 661.3
}

# Model ocean_static or ocean_hgrid file:
model_grid = open_grid_file('../data/geography/ocean_static.nc')

# Tide data produced by compute_tides.py
model = xarray.open_dataset('./figures/computed_tides.nc')

# Subsampling used for the data from compute_tides.py:
sub = 1

# Color map to use for amplitude shading
amp_colormap = 'magma'

# Color map to use for phase contour lines
phase_colormap = 'hsv'

# Color map to use for the shading in the amplitude difference plot
diff_colormap = 'coolwarm'

# cartopy projection used to plot the maps
plot_proj = ccrs.PlateCarree()

# extent of the maps (lon_west, lon_east, lat_south, lat_north)
map_extent = [-99, -35, 4, 59]

# Open the TPXO data
# Important: also subsets to region around NWA12 domain
tpxo = (
    xarray
    .open_dataset('/work/acr/tpxo9/h_tpxo9.v1.nc')
    .isel(ny=slice(500, 1100), nx=slice(1500, -2))
    .rename({'lon_z': 'lon', 'lat_z': 'lat'})
)

# Add information about constituent to the TPXO data
tpxo['constit'] = (('nc', ), ['M2', 'S2', 'N2', 'K2', 'K1', 'O1', 'P1', 'Q1', 'MM', 'MF', 'M4', 'MN4', 'MS4', '2N2', 'S1'])
tpxo = tpxo.swap_dims({'nc': 'constit'})

# Mask amplitude and phase over land
tpxo_ha = tpxo.ha.where(tpxo.ha > 0)
tpxo_hp = tpxo.hp.where(tpxo.hp > 0)

# Interpolate TPXO to model grid for comparison of amplitude
tpxo_to_model = xesmf.Regridder(
    tpxo[['lon', 'lat']],
    model[['geolon', 'geolat']].rename({'geolon': 'lon', 'geolat': 'lat'}),
    method='bilinear'
)
tpxo_interp = tpxo_to_model(tpxo['ha'])


def plot_tides(constit, amp_levels, delta_levels):
    """
    constit: tidal constituent to plot (one of the ten with periods defined above)
    amp_levels: limits of color scale for model and TPXO amplitude
    delta_levels: limits of the color scale for the plot model minus TPXO amplitude
    """
    # Get difference in amplitudes
    delta = model.A.sel(constit=constit) - tpxo_interp.sel(constit=constit)
    delta *= 100 # -> cm

    # Plot phase lines every hour, except for long period tides
    if periods[constit] > 48:
        phase_levels = np.arange(0, periods[constit], 24) 
    else:
        phase_levels = np.arange(0, periods[constit], 1) 
    
    # Set up color maps and common plot arguments
    phase_colors = plt.get_cmap(phase_colormap)(np.linspace(0, 1, len(phase_levels)))
    cmap, norm = get_map_norm(amp_colormap, levels=amp_levels)
    delta_cmap, delta_norm = get_map_norm(diff_colormap, levels=delta_levels)
    common = dict(cmap=cmap, norm=norm, transform=PC)

    fig = plt.figure(figsize=(12, 8))
    grid = AxesGrid(fig, 111, 
        axes_class=(GeoAxes, dict(projection=plot_proj)),
        nrows_ncols=(1, 3),
        axes_pad=0.3,
        cbar_location='bottom',
        cbar_mode='edge',
        cbar_pad=0.2,
        cbar_size='15%',
        label_mode=''
    )
    # Panel 0: regional model tides
    p = grid[0].pcolormesh(model.geolon_c[::sub, ::sub], model.geolat_c[::sub, ::sub], model.A.sel(constit=constit)*100, **common)
    grid[0].contour(model.geolon, model.geolat, model.g.sel(constit=constit)*periods[constit]/360, colors=phase_colors, levels=phase_levels, transform=PC)
    cbar = grid.cbar_axes[0].colorbar(p, extend='max')
    cbar.ax.set_xlabel('Amplitude (cm)')
    grid[0].set_title(f'(a) Model {constit} amplitude and phase')

    # Panel 1: TPXO tides
    p = grid[1].pcolormesh(tpxo.lon-360, tpxo.lat, tpxo_ha.sel(constit=constit)*100, **common)
    grid[1].contour(tpxo.lon-360, tpxo.lat, tpxo_hp.sel(constit=constit)*periods[constit]/360, colors=phase_colors, levels=phase_levels, transform=PC)
    cbar = grid.cbar_axes[1].colorbar(p, extend='max')
    cbar.ax.set_xlabel('Amplitude (cm)')
    grid[1].set_title(f'(b) TPXO9 {constit} amplitude and phase')

    # Pantel 2: amplitude of regional - TPXO
    p = grid[2].pcolormesh(model.geolon_c[::sub, ::sub], model.geolat_c[::sub, ::sub], delta, cmap=delta_cmap, norm=delta_norm, transform=PC)
    grid[2].set_title(f'(c) Model - TPXO9 {constit} amp.')
    cbar = grid.cbar_axes[2].colorbar(p, extend='both')
    cbar.ax.set_xlabel('Difference (cm)')

    for ax in grid:
        ax.set_extent(map_extent)
        ax.set_xticks([])
        ax.set_yticks([])
        ax.set_xticklabels([])
        ax.set_yticklabels([])
        ax.set_xlabel('')
        ax.set_ylabel('')
        ax.set_facecolor('#bbbbbb')
        for s in ax.spines.values():
            s.set_visible(False)

    plt.savefig(f'./figures/tpxo_comparison_{constit}', dpi=200, bbox_inches='tight')


plot_tides(
    'M2',                  # constituent
    np.arange(0, 150, 10), # amplitude color bar levels (min, max, spacing)
    np.arange(-30, 31, 5)  # difference color bar levels (min, max, spacing)
)
