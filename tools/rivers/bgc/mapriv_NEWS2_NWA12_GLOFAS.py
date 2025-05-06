import pandas as pd
import numpy as np
import scipy.io
import xarray as xr

# Name of netcdf file to be created
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
# organic; PP is set to 30% based on Froelich; Partitioning of detritus
# between
frac_PP = frac_ldon = 0.3
frac_sldon = frac_srdon = frac_sldop = frac_srdop = 0.35
frac_ldop = 0.3

# 40 nM dissolved iron concentration from De Baar and De Jong + 30nM 
# Colloidal and nanoparticle flux as reported in Canfield and Raiswell
const_fed = 70.0e-6

# GlobalNEWS2 data obtained from Emilio Mayorga
filename = 'GlobalNEWS2_RH2000Dataset-version1.0.xls'
basin = pd.read_excel(filename,sheet_name=1)
hydrology = pd.read_excel(filename,sheet_name=2)
loading = pd.read_excel(filename,sheet_name=3)

# Find all the river basins that empty into "land", e.g., lakes
ocean = basin['ocean']
land_index = np.array( ocean == 'Land' ) # TODO: Do I need to call np.array on this?

river_names_all = basin['basinname']

# Basin area in
area = basin['A']
lon_news_all  = basin['mouth_lon']
lat_news_all = basin['mouth_lat']

# Loads in MG yr-1 converted to moles per sec
DIN_load_all = loading["Ld_DIN"]*1e6/14/86400/365 # TODO: Is this how scientific notation works in py?
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
# area_mod: area of grid cell in m-2                                      #
# lon_mod: longitude (0-360 degrees)                                      #
# lat_mod: latitude                                                       #
#                                                                         #
# The file was calculated from daily output using the routine             #
# "make_climatology.m".  This routine and all associated files can be     #
# found in the same directory as the data file                            #
###########################################################################

glofas_runoff = scipy.io.loadmat("./glofas_runoff_mean.mat")

# Convert runoff from kg m-2 sec-1 to m3 sec-1
Q_mod_monthly = glofas_runoff['runoff'] * glofas_runoff['area_mod']/1000 

grid_file = '/archive/cas/Regional_MOM6/NWA12/nwa12_ocean_static.nc';
depth = xr.open_dataset(grid_file)['deptho'].transpose() # TODO: Confirm this is the intent of original
depth = depth.fillna(-1)


###########################################################################
# Filter for rivers in the region, set thresholds for minimum river size, #
# set parameters for plotting routines.                                   #
###########################################################################

# use grid to filter rivers outside domain
lat_mod_max = np.max( glofas_runoff['lat_mod'] )
lat_mod_min = np.min( glofas_runoff['lat_mod'] )
lon_mod_max = np.max( glofas_runoff['lon_mod'] )
lon_mod_min = np.min( glofas_runoff['lon_mod'] )

# TODO: Confirm that this reproduces the answer of the original 

in_region =  ( (lon_news_all <= lon_mod_max) & (lon_news_all >= lon_mod_min) 
                & (lat_news_all <= lat_mod_max) & ( lat_news_all >= lat_mod_min) 
                & (Qact_all > Q_min) & (Qact_all != np.inf ) )

# If you are using a high threshold, grab one smaller river to constrain
# Carribean Islands
if Q_min > 100: 
    # TODO: Confirm that this reproduces the answer of the original 
    cuba_ind = river_names[ river_names_all == "GHAASBASIN1808" ].index[0]
    in_region[cuba_ind] = True 

# Establish vectors of flow and nutrient loads for the NWA
Qact = Qact_all[in_region]
lon_news = lon_news_all[in_region] # TODO: Aren't these two arrays two dimension? how does this work
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

 #Add in 2 "dummy" rivers to handle Cuba, giving it properties like 
 #Jamaica or Haiti rather than Florida. 

 #GHAASBasin1808 is in Haiti.  Fluxes are characterized by particularly
 #high particulate phosphorus inputs.
index_susquehanna = river_names[ river_names == 'Susquehanna'].index[0]
print(index_susquehanna)
#lat_news.iloc[index_susquehanna] = 38.5
#lon_news.iloc[index_susquehanna] = 76.67

# TODO: Convert this section to python
# Two "rivers" with properties like Haiti used to specify Cuba
#Qact(num_rivers+1) = Qact(cuba_ind)/2  
#lon_news(num_rivers+1) = -81
#lat_news(num_rivers+1) = 22.6
#DIN_load(num_rivers+1) = DIN_load(cuba_ind)/2
#DON_load(num_rivers+1) = DON_load(cuba_ind)/2
#PN_load(num_rivers+1) = PN_load(cuba_ind)/2
#DIP_load(num_rivers+1) = DIP_load(cuba_ind)/2
#DOP_load(num_rivers+1) = DOP_load(cuba_ind)/2
#PP_load(num_rivers+1) = PP_load(cuba_ind)/2
#Si_load(num_rivers+1) = Si_load(cuba_ind)/2
#river_names(num_rivers+1) = river_names(cuba_ind)
#
#Qact(num_rivers+2) = Qact(cuba_ind)/2  
#lon_news(num_rivers+2) = -83.25
#lat_news(num_rivers+2) = 22.6
#DIN_load(num_rivers+2) = DIN_load(cuba_ind)/2
#DON_load(num_rivers+2) = DON_load(cuba_ind)/2
#PN_load(num_rivers+2) = PN_load(cuba_ind)/2
#DIP_load(num_rivers+2) = DIP_load(cuba_ind)/2
#DOP_load(num_rivers+2) = DOP_load(cuba_ind)/2
#PP_load(num_rivers+2) = PP_load(cuba_ind)/2
#Si_load(num_rivers+2) = Si_load(cuba_ind)/2
#river_names(num_rivers+2) = river_names(cuba_ind)
#
#num_rivers = num_rivers + 1
#
# Adjust location of closest Florida basin to avoid extrapolation to 
# Cuba; This has little effect on patterns in Florida.
#for n = 1:num_rivers;
#    n
#    test = strcmp('GHAASBasin448',river_names{n})
#    if test == 1
#        fla_ind = n
#    end
#end
#
#lon_news(fla_ind) = -80.5
#lat_news(fla_ind) = 26.6
#
###########################################################################
# END MANUAL EDITS                                                        %
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

# Sort rivers by discharge

# First combine various series into datafram to make sorting easier
river_df = pd.concat(
    [Qact,
    lon_news,
    lat_news,
    DIN_load,
    DON_load,
    PN_load,
    DIP_load,
    DOP_load,
    PP_load,
    Si_load], axis = 1 # Needed to return data frame
)


river_df = river_df.sort_values('Qact')

# Total N and P load diagnostics
N_load_sort = river_df['Ld_DIN'] + river_df['Ld_DON'] + river_df['Ld_PN']
N_load_sort = river_df['Ld_DIP'] + river_df['Ld_DOP'] + river_df['Ld_PP']

# Calculate Concentrations
# Loads are in moles N sec-1, Q in m3 s-1; conc in moles N m-3
DIN_conc_sort = river_df['Ld_DIN'] / river_df['Qact']
DON_conc_sort = river_df['Ld_DON'] / river_df['Qact']
DIP_conc_sort = river_df['Ld_DIP'] / river_df['Qact']
DOP_conc_sort = river_df['Ld_DOP'] / river_df['Qact']
PN_conc_sort = river_df['Ld_PN'] / river_df['Qact']
PP_conc_sort = river_df['Ld_PP'] / river_df['Qact']
Si_conc_sort = river_df['Ld_Si'] / river_df['Qact']

# initialize vectors to hold nutrient concentrations at eac runoff
# point.
Q_mod_vec = Q_mod_ann[ Q_mod_ann > 0]

print(river_df)
print(Q_mod_vec)
###########################################################################
# Loop identifies points assigned to each river                           #
###########################################################################
