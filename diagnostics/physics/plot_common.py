import cartopy.crs as ccrs
from cartopy.mpl.ticker import LongitudeFormatter, LatitudeFormatter, LatitudeLocator, LongitudeLocator
from glob import glob
from matplotlib.colors import BoundaryNorm, ListedColormap
import matplotlib.pyplot as plt
import numpy as np
import os
import xarray
import xskillscore
import logging
import yaml
import xesmf

# Configure logging for plot_common
logger = logging.getLogger(__name__)

def center_to_outer(center, left=None, right=None):
    """
    Given an array of center coordinates, find the edge coordinates,
    including extrapolation for far left and right edge.
    """
    if hasattr(center,'values'): # handle xarray dataarays and similar objects
        edges = 0.5 * (center.values[0:-1] + center.values[1:])
    else:
        edges = 0.5 * (center[0:-1] + center[1:])
    if left is None:
        left = edges[0] - (edges[1] - edges[0])
    if right is None:
        right = edges[-1] + (edges[-1] - edges[-2])
    outer = np.hstack([left, edges, right])
    return outer


def corners(lon, lat):
    """
    Given 1D lon and lat, return 1D lon and lat corners 
    for use in pcolormesh or xesmf conservative
    """
    lonc = center_to_outer(lon)
    latc = center_to_outer(lat)
    assert len(lonc) == len(lon) + 1
    assert len(latc) == len(lat) + 1
    return lonc, latc


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

def annotate_skill(model, obs, ax, dim=['yh', 'xh'], x0=-98.5, y0=54, yint=4, xint=4, weights=None, cols=1, proj = ccrs.PlateCarree(), plot_lat=False, **kwargs):
    """
    Annotate an axis with model vs obs skill metrics
    """
    bias = xskillscore.me(model, obs, dim=dim, skipna=True, weights=weights)
    rmse = xskillscore.rmse(model, obs, dim=dim, skipna=True, weights=weights)
    corr = xskillscore.pearson_r(model, obs, dim=dim, skipna=True, weights=weights)
    medae = xskillscore.median_absolute_error(model, obs, dim=dim, skipna=True)

    ax.text(x0, y0, f'Bias: {float(bias):2.2f}', transform=proj, **kwargs)

    # Set plot_lat=True in order to plot skill along a line of latitude. Otherwise, plot along longitude
    if plot_lat:
        ax.text(x0-xint, y0, f'RMSE: {float(rmse):2.2f}', transform=proj, **kwargs)
        if cols == 1:
            ax.text(x0-xint*2, y0, f'MedAE: {float(medae):2.2f}', transform=proj, **kwargs)
            ax.text(x0-xint*3, y0, f'Corr: {float(corr):2.2f}', transform=proj, **kwargs)
        elif cols == 2:
            ax.text(x0, y0+yint, f'MedAE: {float(medae):2.2f}', transform=proj, **kwargs)
            ax.text(x0-xint, y0+yint, f'Corr: {float(corr):2.2f}', transform=proj, **kwargs)
        else:
            raise ValueError(f'Unsupported number of columns: {cols}')

    else:
        ax.text(x0, y0-yint, f'RMSE: {float(rmse):2.2f}', transform=proj, **kwargs)
        if cols == 1:
            ax.text(x0, y0-yint*2, f'MedAE: {float(medae):2.2f}', transform=proj, **kwargs)
            ax.text(x0, y0-yint*3, f'Corr: {float(corr):2.2f}', transform=proj, **kwargs)
        elif cols == 2:
            ax.text(x0+xint, y0, f'MedAE: {float(medae):2.2f}', transform=proj, **kwargs)
            ax.text(x0+xint, y0-yint, f'Corr: {float(corr):2.2f}', transform=proj, **kwargs)
        else:
            raise ValueError(f'Unsupported number of columns: {cols}')

def autoextend_colorbar(ax, plot, plot_array=None, **kwargs):
    """
    Add a colorbar, setting the extend metric based on 
    whether the plot data exceeds the plot limits.
    Pulls the data from the passed plot unless plot_array is passed.
    """
    norm_min = plot.norm.vmin
    norm_max = plot.norm.vmax
    
    if plot_array is None:
        plot_array = plot.get_array()
        
    actual_min = plot_array.min()
    actual_max = plot_array.max()
    
    if actual_min < norm_min and actual_max > norm_max:
        extend = 'both'
    elif actual_min < norm_min:
        extend = 'min'
    elif actual_max > norm_max:
        extend = 'max'
    else:
        extend = 'neither'
    return ax.colorbar(plot, extend=extend, **kwargs)

def add_ticks(ax, xticks=np.arange(-100, -31, 1), yticks=np.arange(2, 61, 1), xlabelinterval=2, ylabelinterval=2, fontsize=10, projection = ccrs.PlateCarree(), **kwargs):
    """
    Add lat and lon ticks and labels to a plot axis.
    By default, tick at 1 degree intervals for x and y, and label every other tick.
    Additional kwargs are passed to LongitudeFormatter and LatitudeFormatter.
    """
    ax.yaxis.tick_right()
    ax.set_xticks(xticks, crs = projection)
    if xlabelinterval == 0:
        plt.setp(ax.get_xticklabels(), visible=False)
    else:
        plt.setp([l for i, l in enumerate(ax.get_xticklabels()) if i % xlabelinterval != 0], visible=False, fontsize=fontsize)
        plt.setp([l for i, l in enumerate(ax.get_xticklabels()) if i % xlabelinterval == 0], fontsize=fontsize)
    ax.set_yticks(yticks, crs = projection)
    if ylabelinterval == 0:
        plt.setp(ax.get_yticklabels(), visible=False)
    else:
        plt.setp([l for i, l in enumerate(ax.get_yticklabels()) if i % ylabelinterval != 0], visible=False)
        plt.setp([l for i, l in enumerate(ax.get_yticklabels()) if i % ylabelinterval == 0], fontsize=fontsize)
    lon_formatter = LongitudeFormatter(direction_label=False, **kwargs)
    lat_formatter = LatitudeFormatter(direction_label=False, **kwargs)
    ax.xaxis.set_major_formatter(lon_formatter)
    ax.yaxis.set_major_formatter(lat_formatter)

def open_var(pp_root, kind, var):
    freq = 'daily' if 'daily' in kind else 'monthly'
    longslice = '19930101-20191231' if freq == 'daily' else '199301-201912'
    longfile = os.path.join(pp_root, 'pp', kind, 'ts', freq, '27yr', f'{kind}.{longslice}.{var}.nc')
    if os.path.isfile(longfile):
        os.system(f'dmget {longfile}')
        return xarray.open_dataset(longfile)[var]
    elif len(glob(os.path.join(pp_root, 'pp', kind, 'ts', freq, '1yr', f'{kind}.*.{var}.nc'))) > 0:
        files = glob(os.path.join(pp_root, 'pp', kind, 'ts', freq, '1yr', f'{kind}.*.{var}.nc'))
        os.system(f'dmget {" ".join(files)}')
        return xarray.open_mfdataset(files)[var]
    elif len(glob(os.path.join(pp_root, 'pp', kind, 'ts', freq, '5yr', f'{kind}.*.{var}.nc'))) > 0:
        files = glob(os.path.join(pp_root, 'pp', kind, 'ts', freq, '5yr', f'{kind}.*.{var}.nc'))
        os.system(f'dmget {" ".join(files)}')
        return xarray.open_mfdataset(files)[var]
    else:
        raise Exception('Did not find postprocessed files')

def save_figure(fname, label='', pdf=False, output_dir='figures'):
    if label == '':
        plt.savefig(os.path.join(output_dir, f'{fname}.png'), dpi=200, bbox_inches='tight')
        if pdf:
            plt.savefig(os.path.join(output_dir, f'{fname}.pdf'), bbox_inches='tight')
    else:
        plt.savefig(os.path.join(output_dir, f'{fname}_{label}.png'), dpi=200, bbox_inches='tight')
        if pdf:
            plt.savefig(os.path.join(output_dir, f'{fname}_{label}.pdf'), bbox_inches='tight')

def load_config(config_path: str):
    """Load the configuration file."""
    try:
        with open(config_path, 'r') as f:
            config = yaml.safe_load(f)
            logger.info(f"Loaded configuration from {config_path}")
            return config
    except Exception as e:
        logger.error(f"Error loading configuration from {config_path}: {e}")
        raise

def process_oisst(config, target_grid, model_ave, start=1993, end = 2020, resamp_freq = None):
    """Open and regrid OISST dataset, return relevant vars from dataset."""
    try:
        oisst = (
            xarray.open_mfdataset([config['oisst'] + f'sst.month.mean.{y}.nc' for y in range(start, end)])
            .sst
            .sel(lat=slice(config['lat']['south'], config['lat']['north']), lon=slice(config['lon']['west'], config['lon']['east']))
            .load()
        )
    except Exception as e:
        logger.error(f"Error processing OISST data: {e}")
        raise e("Could not open OISST dataset")

    # Drop any latitude points greater than or equal to 90 to prevent errors when regridding
    oisst = oisst.where( oisst.lat < 90, drop = True)

    oisst_lonc, oisst_latc = corners(oisst.lon, oisst.lat)
    oisst_lonc -= 360

    mom_to_oisst = xesmf.Regridder(
        target_grid,
        {'lat': oisst.lat, 'lon': oisst.lon, 'lat_b': oisst_latc, 'lon_b': oisst_lonc},
        method='conservative_normed',
        unmapped_to_nan=True
    )

    # If a resample frequency is provided, use it to resample the oisst data over time before taking the average
    if resamp_freq:
        oisst = oisst.resample( time = resamp_freq )

    oisst_ave = oisst.mean('time')

    mom_rg = mom_to_oisst(model_ave)
    logger.info("OISST data processed successfully.")
    return mom_rg, oisst_ave, oisst_lonc, oisst_latc

def process_glorys(config, target_grid, var, sel_time = None, resamp_freq = None, preprocess_regrid = None):
    """
    Open and regrid glorys data, return regridded glorys data
    If a function is passed to the preprocess_regrid option, it will be called on the
    data before it is passed to the regridder but after the regridder
    is created and the average is calculated
    NOTE: if preprocess_regrid returns numpy array, the return value of glorys_ave will
    be a numpy array, not an xarray dataarray as is the default
    """
    glorys = xarray.open_dataset( config['glorys'] ).squeeze(drop=True) #.rename({'longitude': 'lon', 'latitude': 'lat'})
    if var in glorys:
        glorys = glorys[var]
    else:
        logger.error("The provided variable is not in the provided glorys file, now exiting")
        raise Exception(f"Error: {var} data not found in glorys_sfc file")

    # Drop any latitude points greater than or equal to 90 to prevent errors when regridding, then get corner points
    try:
        glorys = glorys.where( glorys.lat < 90, drop = True)
        glorys_lonc, glorys_latc = corners(glorys.lon, glorys.lat)
        logger.info("Glorys data is using lon/lat")
    except AttributeError:
        glorys = glorys.where( glorys.latitude < 90, drop = True)
        glorys_lonc, glorys_latc = corners(glorys.longitude, glorys.latitude)
        logger.info("Glorys data is using longitude/latitude")
    except:
        logger.error("Name of longitude and latitude variables is unknown")
        raise Exception("Error: Lat/Latitude, Lon/Longitude not found in glorys data")

    # If a time slice is provided use it to select a portion of the glorys data
    if sel_time:
        glorys = glorys.sel( time = sel_time )

    # If a resample frequency is provided, use it to resample the glorys data over time before taking the average
    if resamp_freq:
        glorys = glorys.resample(time = resamp_freq)

    glorys_ave = glorys.mean('time').load()

    glorys_to_mom = xesmf.Regridder(glorys_ave, target_grid, method='bilinear', unmapped_to_nan=True)

    # If a preprocessing function is provided, call it before doing any regridding
    # glorys_ave may not remain a xarray dataset after this step
    if preprocess_regrid:
        glorys_ave = preprocess_regrid(glorys_ave)

    glorys_rg = glorys_to_mom(glorys_ave)
    logger.info("Glorys data processed successfully.")
    return glorys_rg, glorys_ave, glorys_lonc, glorys_latc


def get_end_of_climatology_period(clima_file):
    """
    Determine the time period covered by the last climatology file. This function is needed
    because decadal climatology data may not be a decade long for the last available time
    period - for example, the last decadal climatology file for the NWA domain extends from
    2005 to 2017. If the climatology files are formatted in the standard NCEI format, the
    last year of the decadal file should be readable from the last two characters of the
    second _ separated entry in the file name.

    """
    # Extract the time period information from the given file path
    logger.info(f"Finding the end year of the last climatology file using file name: {clima_file}")
    period = os.path.basename(clima_file).split("_")[1]
    logger.info(f"Climatology time period: {period}")
    end_decade_char = period[-2]
    logger.info(f"Climatology decade character: {end_decade_char}")
    end_year_char = period[-1]
    logger.info(f"Climatology year character: {end_year_char}")

    # Map the derived decade and year characters to an actual year, stored as an int
    decade_mapping = {
        "A": 2000,
        "B": 2010,
        "C": 2020,
    }

    if end_decade_char in decade_mapping:
        end_year = decade_mapping[end_decade_char] + int(end_year_char)
    else:
        logger.error((f"ERROR: Found unrecognized decade code {end_decade_char} in {clima_file}."
        "please make sure that decadal climatology follows the National Centers for Environemntal"
        "Information naming conventions"))
        raise Exception("Error: unrecognized decade code {end_decade_char} in {clima_file}")

    logger.info(f"Climatology end year: {end_year}")
    logger.info(f"End year of last climatology file found successfully.")
    return end_year

def combine_regional_climatologies(config, regional_grid):
    """
    Given a list of domains and a data directory in the config fle, open the list of regional
    climatology data files, regrid them to the grid defined in regional_grid, and then concat
    and return the result

    This function expects regional climatologies from 1995- 2004 and 2005 to 2014 for each domain
    of interest to all exist in the rc dir, since these are the date range provided by the National Centers
    for Environmental information via their website. The fuction supports end years other than 2014
    in the second file. All files should follow the National Centers for Environmental
    Information naming conventions ( i.e the default naming scheme when files are downloaded from the
    NCEI website) :

    [V][TT][FF][GG].nc
    where:
    [V] - variable ( name of the domain of interest)
    [TT] - time period (95A4 for the 1995 - 2004 data, A5B2 for the 2005 - 2012 data)
    [FF] - field type ( should be s00 for salinity data)
    [GG] - grid (01- 1°, 04 - 1/4° 10 - 1/10°)

    """
    rcdir = config['rcdir']
    rc_list = []

    for region in config["rc_vars"]:
        logger.info(f"Opening {region} climatology")

        # NWA domain data extends from 2005 to 2017, so use globbing to find files for the second decade of interest to ensure compatibility across domains
        second_period =  glob(os.path.join(rcdir, region+'_A5??_s00_10.nc'))
        num_files = len(second_period)
        if num_files  == 1:
            file2005 = second_period[0]
        else:
            logger.error((f"ERROR: found {num_files} decadal average files for the period after 2005. Please make sure"
            "you have a single file in rcdir covering this period"))
            raise Exception("ERROR: found {num_files} for the post 2005 period, expected 1.")

        logger.info(f"Using the following post 2005 files: {file2005}")

        # NOTE that this is now using the nested method to to combine files. This is to prevent issues when combining files that have the same value for the time dimension
        # It *should* reproduce the same results as the default combine_coords methods since that method typically combined along the time dimension( as all the other dimensions were the same
        # for a given region and the combine_coords algorithm ignores dimensions that don't vary across the inputs), but this is still worth noting nonetheless.
        rc = xarray.open_mfdataset([os.path.join(rcdir, region+'_95A4_s00_10.nc'), file2005], decode_times=False, combine='nested',concat_dim='time')

        last_year = get_end_of_climatology_period(file2005)

        # TODO: Is it a problem if climatologies for the same domain cover different time periods? Example: NEP climatology is 2005-2012, while NNP is 2005-2014
        weights = xarray.DataArray([2004-1995+1, last_year-2005+1], dims=['time'], coords={'time': rc.time})
        rc = rc.weighted(weights).mean('time')

        rc_regrid = xesmf.Regridder(rc, regional_grid, method='bilinear', unmapped_to_nan=True)(rc.s_an.isel(depth=0))

        rc_list.append(rc_regrid)
        logger.info(f"Successfully opened and regridded {region} climatology data")

    combined = xarray.concat( rc_list, dim='region').mean('region')

    return combined
