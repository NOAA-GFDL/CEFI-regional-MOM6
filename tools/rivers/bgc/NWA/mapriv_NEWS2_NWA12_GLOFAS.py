import pandas as pd
from scipy.io import loadmat
from scipy.spatial.distance import cdist
from scipy.interpolate import griddata
import numpy as np
import xarray as xr

# name of netcdf file to be created
nc_file_name = './RiverNutrients_GlobalNEWS2_plusFe_Q100_GLOFAS_NWA12.nc'

# Parameters for the assignment algorithm.
Q_min = 100 # minimum flow in m3 sec
plot_width = 3 # width of window (in degrees) for inspecting locations
                 # of rivers and outflow points that have been assigned to
                 # them.
min_dist = 2  # minimum distance (degrees) of the closest outflow point
                 # for the river to be considered in the domain (useful
                 # for preventing the algorithm from trying to map rivers
                 # flowing to different ocean basins.
inspect_map = 'n' # flag enabling you to pause and inspect each river
                   # mapping as it is being done.

# set the bio-availability of phosphorus and the fractionation of dissolved
# organic PP is set to 30# based on Froelich Partitioning of detritus
# between
frac_PP = 0.3
frac_ldon = 0.3
frac_sldon = 0.35
frac_srdon = 0.35
frac_ldop = 0.3
frac_sldop = 0.35
frac_srdop = 0.35
# 40 nM dissolved iron concentration from De Baar and De Jong + 30nM
# Colloidal and nanoparticle flux as reported in Canfield and Raiswell
const_fed = 70.0e-6

# GlobalNEWS2 data obtained from Emilio Mayorga
#filename = 'GlobalNEWS2_RH2000Dataset-version1.0.xls'
basin = pd.read_csv("GlobalNEWS2_RH2000Dataset-version1.0_BASINS.csv")
hydrology = pd.read_csv("GlobalNEWS2_RH2000Dataset-version1.0_HYDROLOGY.csv")
loading = pd.read_csv("GlobalNEWS2_RH2000Dataset-version1.0_RIVER_EXPORTS.csv")

# find all the river basins that empty into "land", e.g., lakes
ocean = basin['ocean']
land_index = (ocean == "Land")
river_names_all = basin["basinname"]

# basin area in
area = basin["A"]
lon_news_all = basin["mouth_lon"]
lat_news_all = basin["mouth_lat"]

# Loads in Mg yr-1 converted to moles per sec
DIN_load_all = loading["Ld_DIN"]*1e6/14/86400/365
DIP_load_all = loading["Ld_DIP"]*1e6/31/86400/365
DON_load_all = loading["Ld_DON"]*1e6/14/86400/365
DOP_load_all = loading["Ld_DOP"]*1e6/31/86400/365
Si_load_all = loading["Ld_DSi"]*1e6/28.1/86400/365
PN_load_all = (loading["Ld_PN"]*1e6/14/86400/365)
PP_load_all = (loading["Ld_PP"]*1e6/31/86400/365)*frac_PP

# actual and natural discharge (convert from km3/yr to m3/sec)
# Used the actual hydrology to calculate concentrations
Qact_all = hydrology["Qact"]*1e9/(86400*365)
Qnat_all = hydrology["Qnat"]*1e9/(86400*365)

###########################################################################
# Load in monthly climatology of river forcing from the regional grid.    #
# File contains:                                                          #
# runoff: monthly average runoff in kg m-2 sec-1                          #
# area_mod: area of grid cell in m-2                                          #
# lon_mod: longitude (0-360 degrees)                                          #
# lat_mod: latitude                                                           #
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
Q_mod_monthly = runoff *area_mod /1000
Q_mod_ann = np.mean(Q_mod_monthly,0)

grid_file = xr.open_dataset("/work/role.medgrp/Regional_MOM6/NWA12/nwa12_ocean_static.nc")
depth = grid_file.deptho.fillna(-1)

###########################################################################
# Filter for rivers in the region, set thresholds for minimum river size, #
# set parameters for plotting routines.                                   #
###########################################################################
# use grid to filter rivers outside domain
lat_mod_max = np.max( lat_mod )
lat_mod_min = np.min( lat_mod )
lon_mod_max = np.max( lon_mod )
lon_mod_min = np.min( lon_mod )

in_region = (lon_news_all <= lon_mod_max) & (lon_news_all >= lon_mod_min) & (lat_news_all <= lat_mod_max) & (lat_news_all >= lat_mod_min)
in_region &= ( (Qact_all != np.inf) & (Qact_all > Q_min) ) # There shouldn't be any inifinite values, but just in case

# If you are using a high threshold, grab one smaller river to constrain
# Carribean Islands
if Q_min > 100 :
    in_region[river_names_all == 'GHAASBasin1808'] = True

num_rivers = in_region.sum()

# Establish vectors of flow and nutrient loads for the NWA
Qact = Qact_all[in_region]
lon_news = lon_news_all[in_region]
lat_news = lat_news_all[in_region]
DIN_load = DIN_load_all[in_region]
DON_load = DON_load_all[in_region]
PN_load = PN_load_all[in_region]
DIP_load = DIP_load_all[in_region]
DOP_load = DOP_load_all[in_region]
PP_load = PP_load_all[in_region]
Si_load = Si_load_all[in_region]
river_names = river_names_all[in_region]

###########################################################################
# Following inspection of initial mapping, add any manual edits here to   #
# prevent anomalous extrapolations, etc.                                  #
###########################################################################

# Move the Susquehanna a bit south so that it catches the Chesapeake
# and not the Delaware.

susquehanna_index = ( river_names == 'Susquehanna' )
lat_news[ susquehanna_index ] = 38.5
lon_news[ susquehanna_index ] = -76.67

###########################################################################
# END MANUAL EDITS                                                        #
###########################################################################


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

frames = [Qact, lon_news, lat_news, DIN_load, DON_load, PN_load, DIP_load, DOP_load, PP_load, Si_load, river_names]
rivers_df = pd.concat(frames, axis=1)

# Sort rivers by discharge
rivers_df_sort = rivers_df.sort_values(by="Qact")

# Total N and P load diagnostics
# NOTE: need to use names of vars in original csv, not names of array in matlab script
N_load_sort = rivers_df_sort["Ld_DIN"] + rivers_df_sort["Ld_DON"] + rivers_df_sort["Ld_PN"]
P_load_sort = rivers_df_sort["Ld_DIP"] + rivers_df_sort["Ld_DOP"] + rivers_df_sort["Ld_PP"]

# Calculate concentrations
# Loads are in moles N sec-1, Q in m3 s-1; conc in moles N m-3
Qact_sort = rivers_df_sort["Qact"]
conc = rivers_df_sort.drop(columns=["Qact", "mouth_lon", "mouth_lat", "basinname"])
conc = conc.div( Qact_sort, axis = 0 )

# initialize vectors to hold nutrient concentrations at eac runoff
# point.
aa = Q_mod_ann > 0
Q_mod_vec = Q_mod_ann[aa]
Q_mod_len = len(Q_mod_vec)
cols = ["din_conc","don_conc","pn_conc","dip_conc","dop_conc","pp_conc","si_conc"]
# need dtype to match dtype of conc to avoid warnings down the line
conc_matrix = pd.DataFrame(0, columns = cols, index = np.arange( Q_mod_len), dtype=conc["Ld_DIN"].dtype)

# NOTE: Numpy stores elements in Row-Major order, while MATLAB stores them in
# Column major order. As a result, elements will NOT be in the same order!
lon_mod_runoff_vec = lon_mod[aa]
lat_mod_runoff_vec = lat_mod[aa]

# Get pairwise distances between lat/lon news and lat/lon mod_runoff
# Combine lat /lon runoffs
mod_runoff_matrix = np.column_stack( (lon_mod_runoff_vec, lat_mod_runoff_vec) )

# Filter out rivers lying outside of the domain
for k in range(num_rivers):
    # Append lat/lon news to the top of the runoff matrix
    lon_news_k = rivers_df_sort["mouth_lon"].iloc[k]
    lat_news_k = rivers_df_sort["mouth_lat"].iloc[k]
    news_points = np.column_stack( (lon_news_k, lat_news_k) )

    # Get pairwise distance
    distances = np.squeeze( cdist(news_points, mod_runoff_matrix) )

    # sort data
    dist_sort_ind = np.argsort(distances)
    dist_sort = distances[ dist_sort_ind ]

    if dist_sort[0] < min_dist:
        Q_sum1 = 0
        Q_sum2 = 0
        n = 0
        while Q_sum2 < Qact_sort.iloc[k]:
            Q_sum1 = Q_sum2
            Q_sum2 = Q_sum1 + Q_mod_vec[ dist_sort_ind[n] ]
            n += 1 # move to end to account for fact that python is 0 indexed

        nrp = n # num runoff points
        if abs(Q_sum1 - Qact_sort.iloc[k]) < abs(Q_sum2 - Qact_sort.iloc[k]):
            nrp -= 1 # i.e if Q_sum1 is closer to ther Qact_sort value, choose one fewer runoff point

        # dist sort should have all the values in [1:len(conc_matrix)] so there
        # shouldn't be issues with passing dist_sort indices to conc_matrix
        conc_matrix.loc[ dist_sort_ind[:nrp] ] = conc.iloc[k].values

        if inspect_map == "y":
            pass
            # TODO: Implement mapping!
    else:
        if inspect_map == "y":
            pass
            # TODO: Implement mapping!

# nearest neighbor search to fill in any 0 values left for each input field
# after the river mapping is done.
aa = ( conc_matrix["din_conc"] == 0 )
bb = ( conc_matrix["din_conc"] > 0 )

interp = griddata(mod_runoff_matrix[bb], conc_matrix[bb].values, mod_runoff_matrix[aa], method = "nearest")
conc_matrix[aa] = interp
# Initialize 2D concentration arrays; these are the ones read into MOM6 to
# specify the nutrient concentrations of river inputs.

# TODO: Make this more concise / memory efficient
din_conc = np.zeros( lon_mod.shape )
don_conc = np.zeros( lon_mod.shape )
dip_conc = np.zeros( lon_mod.shape )
dop_conc = np.zeros( lon_mod.shape )
pn_conc = np.zeros( lon_mod.shape )
pp_conc = np.zeros( lon_mod.shape )
si_conc = np.zeros( lon_mod.shape )

# Map concentration vectors onto 2D arrays.
aa = Q_mod_ann > 0
din_conc[aa] = conc_matrix["din_conc"]
don_conc[aa] = conc_matrix["don_conc"]
pn_conc[aa] = conc_matrix["pn_conc"]
dip_conc[aa] = conc_matrix["dip_conc"]
dop_conc[aa] = conc_matrix["dop_conc"]
pp_conc[aa] = conc_matrix["pp_conc"]
si_conc[aa] = conc_matrix["si_conc"]

# TODO: Do we need these vars?
NO3_CONC = din_conc.copy()
LDON_CONC = don_conc*frac_ldon
SLDON_CONC = don_conc*frac_sldon
SRDON_CONC = don_conc*frac_srdon
PO4_CONC = dip_conc.copy()
LDOP_CONC = dop_conc*frac_ldop
SLDOP_CONC = dop_conc*frac_sldop
SRDOP_CONC = dop_conc*frac_srdop
NDET_CONC = pn_conc.copy()
PDET_CONC = pp_conc.copy()   # The bioavailability of particulate P has already  been accounted for.

SI_CONC = si_conc.copy()
# Add iron concentrations - initialize with nitrate and then overwrite
FED_CONC = NO3_CONC.copy()
FEDET_CONC = NO3_CONC.copy()
# 40 nM dissolved iron concentration from De Baar and De Jong + 30nM
# Colloidal and nanoparticle flux as reported in Canfield and Raiswell
FED_CONC[FED_CONC > 0] = const_fed
FEDET_CONC[FEDET_CONC > 0] = 0.0

coords = {"time":[0],
          "y":np.arange(1, lat_mod.shape[0]+1 ), # 1 indexed to match matlab output - not strictly necessary
          "x":np.arange(1, lat_mod.shape[1]+1 )
          }
ds = xr.Dataset(coords = coords,
                data_vars = dict(
                    lat= ( ["y","x"], lat_mod, {"units":"degrees north"} ),
                    lon= ( ["y","x"], lon_mod, {"units":"degrees east"} ),
                    NO3_CONC = (["time","y","x"], np.expand_dims(NO3_CONC, axis=0) ,{"units":"mol m-3", "long_name":"DIN_CONC"} ),
                    LDON_CONC = (["time","y","x"], np.expand_dims( LDON_CONC , axis=0) ,{"units":"mol m-3", "long_name":"0.3*DON_CONC"} ),
                    SLDON_CONC = (["time","y","x"], np.expand_dims( SLDON_CONC , axis=0) ,{"units":"mol m-3", "long_name":"0.35*DON_CONC"} ),
                    SRDON_CONC = (["time","y","x"], np.expand_dims( SRDON_CONC , axis=0) ,{"units":"mol m-3", "long_name":"0.35*DON_CONC"} ),
                    NDET_CONC = (["time","y","x"], np.expand_dims( NDET_CONC , axis=0) ,{"units":"mol m-3", "long_name":"1.0*PN_CONC"} ),
                    PO4_CONC = (["time","y","x"], np.expand_dims( PO4_CONC , axis=0) ,{"units":"mol m-3", "long_name":"PO4_CONC"} ),
                    LDOP_CONC = (["time","y","x"], np.expand_dims( LDOP_CONC  , axis=0) ,{"units":"mol m-3", "long_name":"0.3*DOP_CONC"} ),
                    SLDOP_CONC = (["time","y","x"], np.expand_dims( SLDOP_CONC , axis=0)  ,{"units":"mol m-3", "long_name":"0.35*DOP_CONC"} ),
                    SRDOP_CONC = (["time","y","x"], np.expand_dims( SRDOP_CONC , axis=0)  ,{"units":"mol m-3", "long_name":"0.35*DOP_CONC"} ),
                    PDET_CONC = (["time","y","x"], np.expand_dims( PDET_CONC , axis=0) ,{"units":"mol m-3", "long_name":"0.3*PP_CONC"} ),
                    FED_CONC = (["time","y","x"], np.expand_dims( FED_CONC , axis=0) ,{"units":"mol m-3", "long_name":"FED_CONC"} ),
                    FEDET_CONC = (["time","y","x"], np.expand_dims( FEDET_CONC , axis=0),{"units":"mol m-3", "long_name":"FEDET_CONC"} ),
                    SI_CONC = (["time","y","x"], np.expand_dims( SI_CONC , axis=0) ,{"units":"mol m-3", "long_name":"si_CONC"} ),
                )
               )

# set time attrs
ds.time.attrs = {"calendar":"NOLEAP","calendar_type":"NOLEAP","modulo":"T","units":"days since 1900-1-1 0:00:00","time_origin":"01-JAN-1990 00:00:00"}

# Write dataset
ds.to_netcdf("RiverNutrients_GlobalNEWS2_plusFe_Q100_GLOFAS_NWA12_PYTHON.nc",unlimited_dims="time")
