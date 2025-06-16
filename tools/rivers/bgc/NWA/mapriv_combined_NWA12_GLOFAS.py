import pandas as pd
from scipy.io import loadmat
from scipy.spatial.distance import cdist
from scipy.interpolate import griddata
import numpy as np
import xarray as xr
from subprocess import run

# name of netcdf file to be created
nc_file_name = './RiverNutrients_Integrated_NWA12_GLOFAS_RC4US1990to2022_2023_04_v2_PYTHON.nc'

# GLOBAL NEWS based map for filling in gaps
NEWS_file = './RiverNutrients_GlobalNEWS2_plusFe_Q100_GLOFAS_NWA12.nc'

# load in monthly world ocean T, S climatology for saturated oxygen calculation
# TODO: Add code to work with data off of archive instead of work
woa_temp = xr.open_dataset('/work/role.medgrp/shared_data/river_input/woa_sst_climo.nc')['t_an']

# Parameters for the assignment algorithm.
# TODO: Plotting parameters may not be needed if plotting with pyplot
Q_min = 0 # minimum flow in m3 sec
plot_width = 4 # width of window (in degrees) for inspecting locations
                 # of rivers and outflow points that have been assigned to
                 # them.
min_dist = 2.0  # minimum distance (degrees) of the closest outflow point
                 # for the river to be considered in the domain (useful
                 # for preventing the algorithm from trying to map rivers
                 # flowing to different ocean basins.
max_dist = 2.0  # maximum distance (degrees) away that the algorithm
                 # looks for points for rivers that are in the domain
nutrient_option = 2 # option for deriving dissolved organic nutrients
inspect_map = 'n' # flag enabling you to pause and inspect each river
                   # mapping as it is being done.
plot_progress = True

# set the bio-availability of phosphorus and the fractionation of dissolved
# organic PP is set to 30# based on Froelich Partitioning of detritus
# between
frac_PP = 0.5
frac_ldon = 0.3
frac_sldon = 0.35
frac_srdon = 0.35
frac_ldop = 0.3
frac_sldop = 0.35
frac_srdop = 0.35
# 40 nM dissolved iron concentration from De Baar and De Jong + 30nM
# Colloidal and nanoparticle flux as reported in Canfield and Raiswell
const_fed = 70.0e-6

###########################################################################
# USGS data compiled by Fabian Gomez                                      #
###########################################################################
monthly_RC4US = xr.open_dataset('/home/Andrew.C.Ross/git/RC4USCoast/Data/netcdf/mclim_19902022_chem.nc').transpose( "RC4USCoast_ID","time","nv" )
# Drop unused varialbes
monthly_RC4US = monthly_RC4US.drop_vars( ["source","dataset","region", "orgNf", "orgNu", "nox","dicm","temp","phl","phf", "doc", "original_ID", "climatology_bnds"] )
monthly_RC4US = monthly_RC4US.reset_coords( ["lat","lon"], drop = True )
monthly_RC4US = monthly_RC4US.rename( {"river_name":"Station Name","mouth_lat":"lat", "mouth_lon":"lon"} )

# Add additional vars to monthly_RC4US dataset and change units of some vars
monthly_RC4US["din"] = monthly_RC4US["no3"] + monthly_RC4US["nh4"]
# The RC4US database seems to be in mmoles O m-3 rather than mmoles O2 m-3,
# divide by 2.0 for consistency with other O2 data sources
monthly_RC4US["do"] = monthly_RC4US["do"] / 2.0

if nutrient_option == 1:
    # This option will eventually set all river values for pn, dop and pp using GlobalNEWS
    for var in ["pn","dop","pp" ]:
        # choice of din is arbitrary, just need come variable already in the array to set the shape of the new vars
        monthly_RC4US[ var ] = xr.fill_like( monthly_RC4US.din, fill_value = np.nan )

elif nutrient_option == 2 :
    # This option will use differences between total filtered and unfiltered
    # and other properties to derive pn, dop and pp.  This unfortunately
    # generates negative values in some cases.
    monthly_RC4US["pn"] = monthly_RC4US["tnu"] - monthly_RC4US["tnf"]
    # flipped < to >= since where selects values matching condition
    monthly_RC4US["pn"] = monthly_RC4US["pn"].where( monthly_RC4US.pn >= 0, np.nan )
    # Note that po4 is dip
    monthly_RC4US["dop"] = monthly_RC4US["tpf"] - monthly_RC4US["po4"]
    # flipped < to >= since where selects values matching condition
    monthly_RC4US["dop"] = monthly_RC4US.dop.where(monthly_RC4US.dop >= 0, np.nan)
    monthly_RC4US["pp"] = (monthly_RC4US["tpu"] - monthly_RC4US["tpf"])*frac_PP
    monthly_RC4US["pp"] = monthly_RC4US.pp.where( monthly_RC4US.pp >= 0, np.nan)

# Drop variables from dataset once we are done with them
monthly_RC4US = monthly_RC4US.drop_vars( [ "tnf", "tpf", "tnu","tpu" ] )
# Change name of other varias as well
monthly_RC4US = monthly_RC4US.rename({"sio2":"si","do":"o2","po4":"dip"})

# TODO: make sure mouth_lat and mouth_lon in this dataset aling with the values in the other RC4US dataset
# Should be the same since the matlab script uses them as if they were the same, but still
Q_mon_RC4US = xr.open_dataset('/home/Andrew.C.Ross/git/RC4USCoast/Data/netcdf/mclim_19902022_disc.nc').transpose("RC4USCoast_ID","time","nv").disc
Q_mon_RC4US = Q_mon_RC4US.reset_coords( ["lat","lon"] , drop = True)

# Append Q_mon data to monthly data
monthly_RC4US["Q"] = Q_mon_RC4US

# Rename time to month and convert to index
monthly_RC4US = monthly_RC4US.rename( {"time":"month"} )
monthly_RC4US = monthly_RC4US.rename( {"RC4USCoast_ID":"index"} )
monthly_RC4US["month"] = [ x for x in range(1,13) ]

monthly_RC4US_df = monthly_RC4US.to_dataframe()
monthly_RC4US_df = monthly_RC4US_df.reorder_levels(["month","index"])
monthly_RC4US_df = monthly_RC4US_df.sort_index()

ann_RC4US = monthly_RC4US_df.groupby("index").mean("month")

# Append Station names to Annual Dataset [1,slice(None)] selects all indices in the first month
ann_RC4US["Station Name"] = monthly_RC4US_df.loc[1,slice(None)]["Station Name"]

# Manual edits
sus_filter = (ann_RC4US["Station Name"] == "Susquehanna")
ann_RC4US.loc[ sus_filter, 'lat' ] = 38.5
ann_RC4US.loc[ sus_filter, 'lon' ] = -77.5

del_filter = (ann_RC4US["Station Name"] == "Delaware")
ann_RC4US.loc[ del_filter, 'lat' ] = 39.5
ann_RC4US.loc[ del_filter, 'lon' ] = -75.5

pot_filter = (ann_RC4US["Station Name"] == "Potomac")
ann_RC4US.loc[ pot_filter, 'lat' ] = 38.5
ann_RC4US.loc[ pot_filter, 'lon' ] = -77.5

mis_filter = (ann_RC4US["Station Name"] == "Mississippi")
ann_RC4US.loc[ mis_filter, 'lat' ] = 29.25
ann_RC4US.loc[ mis_filter, 'lon' ] = -89.25

ala_filter = (ann_RC4US["Station Name"] == "Alabama")
ann_RC4US.loc[ ala_filter, 'lat' ] = 30.5

# Unicode escape line need to prevent issues reading one line.
# NOTE: This csv has been modified from the /archive/cas/ original to remove an extra comma in line 41
station_data_GSL = pd.read_csv('/work/role.medgrp/COBALT_EVAL/River_Data/Lavoie_GSL/river_discharge_approx.csv', encoding='unicode_escape')
station_data_GSL = station_data_GSL.drop("#", axis =1)
station_data_GSL = station_data_GSL.rename(columns={"name":"Station Name", "Flow ":"Q"})
station_data_GSL.index.name = "index"

station_data_GSL.loc[ station_data_GSL["Station Name"] == "Saint John", ["lat","lon"] ] = (46.25, -66.25)
station_data_GSL.loc[ station_data_GSL["Station Name"] == "Saint John", ["lat","lon"] ]

# TODO: Add code to work with data off of archive instead of work
dic_GSL = pd.read_csv("/work/role.medgrp/COBALT_EVAL/River_Data/Lavoie_GSL/river_DIC.dat", delimiter = '\s+', skiprows=1, header = None, index_col = 1).drop(0, axis = 1)
alk_GSL = pd.read_csv("/work/role.medgrp/COBALT_EVAL/River_Data/Lavoie_GSL/river_Alk.dat", delimiter = '\s+', skiprows=1, header = None, index_col = 1).drop(0, axis = 1)
no3_GSL = pd.read_csv("/work/role.medgrp/COBALT_EVAL/River_Data/Lavoie_GSL/river_nox.dat", delimiter = '\s+', skiprows=1, header = None, index_col = 1).drop(0, axis = 1)

# Reset column index
dic_GSL.columns = range(78)
alk_GSL.columns = range(78)
no3_GSL.columns = range(78)

monthly_GSL = pd.concat([dic_GSL.stack(),alk_GSL.stack(),no3_GSL.stack()], axis=1)
monthly_GSL = monthly_GSL.rename_axis(index=["month","index"])
monthly_GSL.columns = ["dic","alk","no3"]

# in areas where nh4 is not available, set to 0 to prevent extrapolation
monthly_GSL["nh4"] = 0
# if no nh4 present DIN = no3
monthly_GSL["din"] = monthly_GSL["no3"] + monthly_GSL["nh4"]

monthly_GSL[ ["don", "pn", "dip", "dop", "pp" , "si", "o2"] ] = np.nan
monthly_GSL

monthly_GSL[ "lon" ] = monthly_GSL.index.get_level_values("index").map( station_data_GSL["lon"] ).values
monthly_GSL[ "lat" ] = monthly_GSL.index.get_level_values("index").map( station_data_GSL["lat"] ).values
monthly_GSL[ "Station Name" ] = monthly_GSL.index.get_level_values("index").map( station_data_GSL["Station Name"] ).values
monthly_GSL[ "Q" ] = monthly_GSL.index.get_level_values("index").map( station_data_GSL["Q"] ).values

ann_GSL = monthly_GSL.groupby(level="index").mean("time")
# NH4 and DIN should be nans for the annual GSL data
ann_GSL[ ["nh4","din"] ] = np.nan
ann_GSL

# Add Station names back to Dataframe
ann_GSL["Station Name"] = station_data_GSL["Station Name"]

# TODO: Stage on archive
# NOTE removed extra 98 in row 22 as it lead to error. this file is different from version in /archive/cas
station_data_extra = pd.read_csv("/work/role.medgrp//Regional_MOM6/NWA12/NWA12_ExtraRivers/stations_extra_NWA12.csv")
station_data_extra = station_data_extra.drop("Station_ID", axis=1)
station_data_extra = station_data_extra.rename(columns = {"Name":"Station Name","flow":"Q"})

# Add nans
station_data_extra[ "o2" ] = np.nan
station_data_extra[ "nh4" ] = 0
station_data_extra[ "no3" ] = station_data_extra[ "din" ]
station_data_extra.index.name = "index"

station_Data_extra_monthly = pd.DataFrame(np.nan, index = pd.MultiIndex.from_product( [range(1,13),station_data_extra.index ] ) , columns = station_data_extra.columns)
station_Data_extra_monthly = station_Data_extra_monthly.rename_axis( index = ["month","index"] )


ann_df = pd.concat( [ ann_RC4US, ann_GSL, station_data_extra], axis = 0 ,ignore_index  = True)

monthly_df = pd.concat( [monthly_RC4US_df, monthly_GSL ,station_Data_extra_monthly] , axis =0)
monthly_df = monthly_df.sort_index(level="month",sort_remaining=False)
# Reindex
monthly_df.index = pd.MultiIndex.from_product( [range(1,13),range(242)], names = ["month","index"] )

###########################################################################
# Load in monthly climatology of river forcing from the regional grid.    #
# File contains:                                                          #
# runoff: monthly average runoff in kg m-2 sec-1                          #
# area_mod: area of grid cell in m-2                                      #
# lon_mod: longitude (0-360 degrees)                                      #
# lat_mod: latitude                                                       #
#                                                                         #
# The file was calculated from daily output using the routine             #
# "make_climatology.m".  This routine and all associated files can be     #
# found in the same directory as the data file                            #
###########################################################################
mat = loadmat("glofas_runoff_mean.mat") # This is a dictonary of numpy arrays
runoff = mat["runoff"]
area_mod = mat["area_mod"]
lon_mod = mat["lon_mod"]
lat_mod = mat["lat_mod"]

# convert runoff from kg m-2 sec-1 to m3 sec-1
Q_mod_monthly =  runoff *area_mod /1000
Q_mod_ann =  np.mean(Q_mod_monthly,0)

###########################################################################
# Filter for rivers in the region, set thresholds for minimum river size, #
# set parameters for plotting routines.                                   #
###########################################################################
# use grid to filter rivers outside domain
lat_mod_max = np.max( lat_mod )
lat_mod_min = np.min( lat_mod )
lon_mod_max = np.max( lon_mod )
lon_mod_min = np.min( lon_mod )

in_region = (ann_df.lon <= lon_mod_max) & (ann_df.lon >= lon_mod_min) & (ann_df.lat <= lat_mod_max) & (ann_df.lat >= lat_mod_min)
in_region &= ( (ann_df.Q != np.inf) & (ann_df.Q > Q_min) ) # There shouldn't be any inifinite values, but just in case

ann_reg_df =ann_df[in_region]

monthly_reg_df = monthly_df[ monthly_df.index.get_level_values("index").map(in_region) ]
###########################################################################
# Assigning outflow points to rivers.                                     #
#  1. Assignment starts with the rivers with the smallest flow and works  #
#     to the largest, w/larger river characteristics taking precedence to #
#     ensure the most significant rivers are well represented.            #
#  2. The algorithm keeps choosing the closest points to each river mouth #
#     until the assigned flow is as close as possible to that observed    #
#  3. Once the outflow points are assigned using the mean flow values,    #
#     monthly concentrations are assigned to those points.                #
#  4. A simple "nearest neighbor" algorithm is used to fill in the gaps   #
###########################################################################

# Sort rivers by discharge
# need to use argsort, since indices for sorting ann_reg_df will be used in monthly_reg_df
sort_ind = np.argsort(ann_reg_df["Q"],kind= "mergesort") # choose merge sort to preserve order of equal elements
ann_reg_df_sorted = ann_reg_df.iloc[sort_ind].reset_index(drop = True)

# TODO: Confirm that this is the desired outcome
monthly_reg_df_sorted = monthly_reg_df.groupby("month", group_keys=False).apply(lambda x: x.iloc[sort_ind] )
# TODO: Avoid resetting entire index here
monthly_reg_df_sorted.index = pd.MultiIndex.from_product( [ range(1,13), ann_reg_df_sorted.index ] )

# Create vectors of values at the runoff points from the model grid.  These
# are used to accelerate the mapping relative to wrangling the full grid
# with all the zeros included. "ind_ro" are the grid indexes with runoff
ind_ro = (Q_mod_ann > 0)
Q_mod_vec = Q_mod_ann[ ind_ro ]
lon_mod_runoff_vec = lon_mod[ ind_ro ]
lat_mod_runoff_vec = lat_mod[ ind_ro ]

Q_mod_monthly_vecs = Q_mod_monthly[:,ind_ro]

# Constants for o2 saturation calculation (taken from COBALT)
a_0 = 2.00907
a_1 = 3.22014
a_2 = 4.05010
a_3 = 4.94457
a_4 = -2.56847e-1
a_5 = 3.88767
sal = 0
b_0 = -6.24523e-3
b_1 = -7.37614e-3
b_2 = -1.03410e-2
b_3 = -8.17083e-3
c_0 = -4.88682e-7

# Set temp range to [0,40]
woa_temp = woa_temp.where( woa_temp <= 40, 40)
woa_temp = woa_temp.where( woa_temp >= 0, 0)

# Subset temps
ind_ro_da = xr.DataArray( ind_ro, dims = ["yh","xh"], coords = {"yh":woa_temp.yh,"xh":woa_temp.xh} )

temp_woa_monthly_vecs = woa_temp.where(ind_ro_da, drop = True).stack(woa=('yh', 'xh')).dropna(dim='woa', how='all')

tt = 298.15 - temp_woa_monthly_vecs
tkb = 273.15 + temp_woa_monthly_vecs

ts = np.log(tt / tkb)

# constants out front convert from ml/l to mmol m-3
o2sat_woa_monthly_vecs = (1000.0/22391.6) * 1000 * np.exp(a_0 + a_1*ts + a_2*ts**2 + a_3*ts**3 + a_4*ts**4 + a_5*ts**5 +
            (b_0 + b_1*ts + b_2*ts**2 + b_3*ts**3 + c_0*sal) * sal)

# Create dataframe to use in assignment algorithm below
o2_df = o2sat_woa_monthly_vecs.to_dataframe()[["t_an"]].set_index(pd.MultiIndex.from_product( [range(1,13), range( len(lat_mod_runoff_vec) )], names = ["month","index"] ) )
o2_df = o2_df.rename({"t_an":"o2"},axis=1)

###########################################################################
# Load in fields generated from global NEWS.  Where necessary, the ratio  #
# of constituents relative to DIN will be used to fill forcing gaps       #
# The m-file used to generate the NEWS forcing file is included in this   #
# directory and uses an analogous mapping algorithm to this one           #
###########################################################################
ann_NEWS = xr.open_dataset(NEWS_file)

aa = ann_NEWS.NO3_CONC > 0

ann_NEWS["don_ratio"] = (ann_NEWS.LDON_CONC + ann_NEWS.SLDON_CONC + ann_NEWS.SRDON_CONC ) / ann_NEWS.NO3_CONC
ann_NEWS["pn_ratio"] = ann_NEWS.NDET_CONC / ann_NEWS.NO3_CONC
ann_NEWS["dip_ratio"] = ann_NEWS.PO4_CONC / ann_NEWS.NO3_CONC
ann_NEWS["dop_ratio"] = (ann_NEWS.LDOP_CONC + ann_NEWS.SLDOP_CONC + ann_NEWS.SRDOP_CONC ) / ann_NEWS.NO3_CONC
ann_NEWS["pp_ratio"] = ann_NEWS.PDET_CONC / ann_NEWS.NO3_CONC
ann_NEWS["si_ratio"] = ann_NEWS.SI_CONC / ann_NEWS.NO3_CONC

# Select just the ratios
ann_NEWS_ratios = ann_NEWS[ ["don_ratio", "pp_ratio", "pn_ratio","dip_ratio", "dop_ratio", "si_ratio"] ]

# Turn the ratios into vectors
ann_NEWS_ratios = ann_NEWS_ratios.where(aa, drop = True).stack(ratio=('y', 'x')).dropna(dim ="ratio",how='all')

ann_NEWS_ratios_df = ann_NEWS_ratios.to_dataframe()

# Clean up the dataframe
ann_NEWS_ratios_df = ann_NEWS_ratios_df.reset_index(drop=True).drop(columns = ["y","x"])
# need column names to sorted_annual data for assignemnt
ann_NEWS_ratios_df.columns = ["don","pp","pn","dip","dop","si"]

# Dataframe to hold monthly values mapped onto model runoff points
mod_monthly_vecs = pd.DataFrame( 0, index = pd.MultiIndex.from_product( [range(1,13), range( len(lat_mod_runoff_vec) )] ),
                                columns = ["dic","alk","no3","nh4","din","don","pn", "dip", "dop", "pp", "si", "o2"],
                                 dtype = "float64")
mod_monthly_vecs = mod_monthly_vecs.rename_axis( index = ["month","index"])

# Get pairwise distances between lat/lon news and lat/lon mod_runoff
# Combine lat /lon runoffs
mod_runoff_matrix = np.column_stack( (lon_mod_runoff_vec, lat_mod_runoff_vec) )

# put columns of monthly_fill_values in the same order as columns of mod_monhtly_vecs
monthly_reg_df_sorted = monthly_reg_df_sorted[mod_monthly_vecs.columns]

for k, row in ann_reg_df_sorted.iterrows():
    # Get pairwise distance
    news_points = np.column_stack( (row.lon, row.lat) )
    distances = np.squeeze( cdist(news_points, mod_runoff_matrix) )

    # sort data
    dist_sort_ind = np.argsort(distances)
    dist_sort = distances[ dist_sort_ind ]

    if dist_sort[0] < min_dist:
        Q_sum1 = 0
        Q_sum2 = 0
        n = 0
        while (Q_sum2 < row.Q) and (dist_sort[n] < max_dist) :
            Q_sum1 = Q_sum2
            Q_sum2 = Q_sum1 + Q_mod_vec[ dist_sort_ind[n] ]
            n += 1 # move to end to account for fact that python is 0 indexed

        nrp = n # num runoff points

        if abs(Q_sum1 - row.Q) < abs(Q_sum2 - row.Q):
            nrp -= 1 # i.e if Q_sum1 is closer to ther Qact_sort value, choose one fewer runoff point

        # make sure nrp is always greater than 1 so something is always selected
        #nrp = max(1, nrp)

        # enter monthly concentration values into an array of monthly values
        # if no monthly value is available, use annuals after setting nan to zero
        # Ok to do this for "din, no3, and nh4, since matlab script leaves these values as zero
        # if they nan in both the monthly and annual data
        variables_monthly = ["dic","alk","din","no3","nh4"]

        # If the annual data is nan, set the fill value to 0. Otherwise, use annual dat
        #ann_fill_values = row[ variables_monthly ]
        ann_fill_values = row
        # need to specify type here to avoid warnings
        #ann_fill_values = ann_fill_values.astype(np.float64).fillna(0)
        ann_fill_values[ variables_monthly ] = ann_fill_values[ variables_monthly ].astype(np.float64).fillna(0)

mod_monthly_vecs.groupby("month").sum()

# nearest neighbor search to fill in any 0 values left for each input field
# after the river mapping is done.
aa = ( mod_monthly_vecs == 0 )
bb = ( mod_monthly_vecs > 0 )

bb.groupby("month").sum()

mod_runoff_df = pd.DataFrame( np.tile(mod_runoff_matrix,(12,1)) , index = pd.MultiIndex.from_product( [range(1,13), range(len(mod_runoff_matrix))] ), columns = ["lat","lon"] )

# Unfortunately, need to do interpolation manually for each of the columns here because the
# TODO: Find some way passing unique coordinates to each column to simplify this step
# TODO: Do this interp monthwise to ensure data does not carray over between months
for col in bb.columns:
    if col == "o2":
        continue
    for month in range(1,13):
        #interp = griddata( np.round( mod_runoff_df[ bb[col] ], 4) , mod_monthly_vecs[col][ bb[col] ].values, mod_runoff_df[ aa[col] ], method = "nearest")
        runoff_src = mod_runoff_df.loc[ (month,bb[col]),: ]
        data = mod_monthly_vecs.loc[ (month, bb[col]), col ].values
        runoff_dest = mod_runoff_df.loc[ (month,aa[col]),: ]
        interp = griddata( np.round( runoff_src, 4) , data, runoff_dest, method = "nearest")
        mod_monthly_vecs.loc[ (month,aa[col]), col ] = interp

mod_monthly_vecs

mod_monthly_vecs.groupby("month").sum()

# For o2sat, fill in any 0 values with saturated o2 at the world ocean
# atlas climatology
mod_monthly_vecs[aa["o2"] ] = o2_df[ aa["o2"] ]

monthly_fluxes = mod_monthly_vecs.mul(Q_mod_monthly_vecs.flatten(), axis =0)

ann_fluxes = monthly_fluxes.groupby("index").mean("month")

# TODO: Implement plotting
variables = ["DIC_CONC", "ALK_CONC", "NO3_CONC", "NH4_CONC", "LDON_CONC", "SLDON_CONC", "SRDON_CONC",
             "PO4_CONC", "LDOP_CONC", "SLDOP_CONC", "SRDOP_CONC", "NDET_CONC", "PDET_CONC", "SI_CONC", "O2_CONC", "DON_CONC", "DOP_CONC"]
dims = Q_mod_monthly.shape
conc_ds = xr.Dataset( {var: (["month", "lat", "lon"], np.full_like( Q_mod_monthly, 0 ) ) for var in variables},
                     coords = {"month": range(1,13), "lat": range( dims[1] ), "lon": range(dims[2] ) } )

# Map calculated values on to NWA GRID, Unfotunatley, have to do this manually for now
# TODO: Find cleaner way to do all of these mappings
for m in range(12):
    conc_ds["DIC_CONC"].isel(month=m).values[ind_ro] = mod_monthly_vecs.loc[m+1,:]["dic"]
    conc_ds["ALK_CONC"].isel(month=m).values[ind_ro] = mod_monthly_vecs.loc[m+1,:]["alk"]
    conc_ds["NO3_CONC"].isel(month=m).values[ind_ro] = mod_monthly_vecs.loc[m+1,:]["no3"]
    conc_ds["NH4_CONC"].isel(month=m).values[ind_ro] = mod_monthly_vecs.loc[m+1,:]["nh4"]
    conc_ds["NDET_CONC"].isel(month=m).values[ind_ro] = mod_monthly_vecs.loc[m+1,:]["pn"]
    conc_ds["PO4_CONC"].isel(month=m).values[ind_ro] = mod_monthly_vecs.loc[m+1,:]["dip"]
    conc_ds["SI_CONC"].isel(month=m).values[ind_ro] = mod_monthly_vecs.loc[m+1,:]["si"]
    conc_ds["O2_CONC"].isel(month=m).values[ind_ro] = mod_monthly_vecs.loc[m+1,:]["o2"]
    conc_ds["DON_CONC"].isel(month=m).values[ind_ro] = mod_monthly_vecs.loc[m+1,:]["don"]
    conc_ds["DON_CONC"].isel(month=m).values[ind_ro] = mod_monthly_vecs.loc[m+1,:]["dop"]

# Calculate L, SL, and Sr from Dop and Don values
conc_ds["LDON_CONC"] = conc_ds["DON_CONC"] * frac_ldon
conc_ds["SLDON_CONC"] = conc_ds["DON_CONC"] * frac_sldon
conc_ds["SRDON_CONC"] = conc_ds["DON_CONC"] * frac_srdon

conc_ds["LDOP_CONC"] = conc_ds["DOP_CONC"] * frac_ldop
conc_ds["SLDOP_CONC"] = conc_ds["DOP_CONC"] * frac_sldop
conc_ds["SRDOP_CONC"] = conc_ds["DOP_CONC"] * frac_srdop

# Get rid of unneded don and dop vars
conc_ds = conc_ds.drop_vars(["DOP_CONC","DON_CONC"])

# MOM6 is taking river values in moles m-3 for other constituents.  Change
# for consistency across river constituents
conc_ds = conc_ds / 1e3

# Add iron concentrations - initialize with nitrate and then overwrite
# 40 nM dissolved iron concentration from De Baar and De Jong + 30nM
# Colloidal and nanoparticle flux as reported in Canfield and Raiswell
conc_ds["FED_CONC"] = conc_ds["NO3_CONC"].where( conc_ds["NO3_CONC"] <= 0, const_fed)
conc_ds["FEDET_CONC"]= conc_ds["NO3_CONC"].where( conc_ds["NO3_CONC"] <= 0, 0)

###########################################################################
# Save Files                                                              #
###########################################################################
# option to save matlab file
# save River_DIC_ALK_RC4US_NWA ALK_CONC DIC_CONC

# Construct netcdf file following format used by nutrient input files to
# MOM6

# Make reference dates for standard non-leap year
# conc_ds.reset_coords({"month":pd.Date
# time = datenum(dates) - datenum([1990 1 1 0 0 0])
months = np.arange("1990-01-16","1991-01-16", dtype="datetime64[M]")
months = months + np.timedelta64(15,"D")

conc_ds = conc_ds.assign_coords({"month":months})

conc_ds = conc_ds.rename({"month":"time"})

conc_ds.to_netcdf("test_python_combine.nc",unlimited_dims="time")
