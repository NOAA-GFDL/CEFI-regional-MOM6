% Routine to map USGS nutrient data onto the MOM6 Northwest Atlantic (NWA) 
% grid. Run on matlab97 or above.

clear all;
nc64startup

% name of netcdf file to be created
nc_file_name = './RiverNutrients_Integrated_NWA12_GLOFAS_RC4US1990to2022_2023_04_v2.nc';

% GLOBAL NEWS based map for filling in gaps
NEWS_file = './RiverNutrients_GlobalNEWS2_plusFe_Q100_GLOFAS_NWA12.nc';

% load in monthly world ocean T, S climatology for saturated oxygen calculation
temp = ncread('/archive/acr/shared_data/river_input/woa_sst_climo.nc','t_an');
woa_temp = permute(temp,[3 2 1]);

% Parameters for the assignment algorithm.
Q_min = 0; % minimum flow in m3 sec
plot_width = 4; % width of window (in degrees) for inspecting locations
                 % of rivers and outflow points that have been assigned to
                 % them.
min_dist = 2.0;  % minimum distance (degrees) of the closest outflow point
                 % for the river to be considered in the domain (useful
                 % for preventing the algorithm from trying to map rivers
                 % flowing to different ocean basins.
max_dist = 2.0;  % maximum distance (degrees) away that the algorithm 
                 % looks for points for rivers that are in the domain
nutrient_option = 2; % option for deriving dissolved organic nutrients
inspect_map = 'n'; % flag enabling you to pause and inspect each river
                   % mapping as it is being done.
plot_progress = true;

% set the bio-availability of phosphorus and the fractionation of dissolved
% organic; PP is set to 30% based on Froelich; Partitioning of detritus
% between
frac_PP = 0.5;
frac_ldon = 0.3;
frac_sldon = 0.35;
frac_srdon = 0.35;
frac_ldop = 0.3;
frac_sldop = 0.35;
frac_srdop = 0.35;
% 40 nM dissolved iron concentration from De Baar and De Jong + 30nM 
% Colloidal and nanoparticle flux as reported in Canfield and Raiswell
const_fed = 70.0e-6;

%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%
% USGS data compiled by Fabian Gomez                                      %
%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%
filename_chem = '/home/Andrew.C.Ross/git/RC4USCoast/Data/netcdf/mclim_19902022_chem.nc';
alk_monthly_RC4US = ncread(filename_chem,'alk'); alk_monthly_RC4US = permute(alk_monthly_RC4US,[2 1]);
dic_monthly_RC4US = ncread(filename_chem,'dic'); dic_monthly_RC4US = permute(dic_monthly_RC4US,[2 1]);
no3_monthly_RC4US = ncread(filename_chem,'no3'); no3_monthly_RC4US = permute(no3_monthly_RC4US,[2 1]);
nh4_monthly_RC4US = ncread(filename_chem,'nh4'); nh4_monthly_RC4US = permute(nh4_monthly_RC4US,[2 1]);
din_monthly_RC4US = no3_monthly_RC4US + nh4_monthly_RC4US;
dip_monthly_RC4US = ncread(filename_chem,'po4'); dip_monthly_RC4US = permute(dip_monthly_RC4US,[2 1]);
si_monthly_RC4US = ncread(filename_chem,'sio2'); si_monthly_RC4US = permute(si_monthly_RC4US,[2 1]);
% The RC4US database seems to be in mmoles O m-3 rather than mmoles O2 m-3,
% divide by 2.0 for consistency with other O2 data sources
o2_monthly_RC4US = ncread(filename_chem,'do'); o2_monthly_RC4US = permute(o2_monthly_RC4US,[2 1])/2.0;
don_monthly_RC4US = ncread(filename_chem,'don'); don_monthly_RC4US = permute(don_monthly_RC4US,[2 1]);
temp_monthly_RC4US = ncread(filename_chem,'temp'); temp_monthly_RC4US = permute(temp_monthly_RC4US,[2 1]);
if nutrient_option == 1
  % This option will eventually set all river values for pn, dop and pp using GlobalNEWS
  pn_monthly_RC4US = no3_monthly_RC4US*NaN;
  dop_monthly_RC4US = no3_monthly_RC4US*NaN;
  pp_monthly_RC4US = no3_monthly_RC4US*NaN;
elseif nutrient_option == 2
  % This option will use differences between total filtered and unfiltered
  % and other properties to derive pn, dop and pp.  This unfortunately
  % generates negative values in some cases.
  tnf_monthly_RC4US = ncread(filename_chem,'tnf'); tnf_monthly_RC4US = permute(tnf_monthly_RC4US,[2 1]);
  don2_monthly_RC4US = tnf_monthly_RC4US - din_monthly_RC4US; 
  tnu_monthly_RC4US = ncread(filename_chem,'tnu'); tnu_monthly_RC4US = permute(tnu_monthly_RC4US,[2 1]);
  pn_monthly_RC4US = tnu_monthly_RC4US - tnf_monthly_RC4US;
  pn_monthly_RC4US(pn_monthly_RC4US < 0) = NaN;
  tpf_monthly_RC4US = ncread(filename_chem,'tpf'); tpf_monthly_RC4US = permute(tpf_monthly_RC4US,[2 1]);
  dop_monthly_RC4US = tpf_monthly_RC4US - dip_monthly_RC4US;
  dop_monthly_RC4US(dop_monthly_RC4US < 0) = NaN;
  tpu_monthly_RC4US = ncread(filename_chem,'tpu'); tpu_monthly_RC4US = permute(tpu_monthly_RC4US,[2 1]);
  pp_monthly_RC4US = (tpu_monthly_RC4US - tpf_monthly_RC4US)*frac_PP;
  pp_monthly_RC4US(pp_monthly_RC4US < 0) = NaN;
end
dfe_monthly_RC4US = no3_monthly_RC4US*NaN;
pfe_monthly_RC4US = no3_monthly_RC4US*NaN;

filename_discharge = '/home/Andrew.C.Ross/git/RC4USCoast/Data/netcdf/mclim_19902022_disc.nc';
Q_monthly_RC4US = ncread(filename_discharge,'disc'); Q_monthly_RC4US = permute(Q_monthly_RC4US,[2 1]); % m-3 sec-1
station_names_RC4US = h5read(filename_discharge,'/river_name');
lon_stations_RC4US = ncread(filename_discharge,'mouth_lon');
lat_stations_RC4US = ncread(filename_discharge,'mouth_lat');

Q_ann_RC4US = mean(Q_monthly_RC4US,1,'native','omitnan')';
dic_ann_RC4US = mean(dic_monthly_RC4US,1,'native','omitnan')';
alk_ann_RC4US = mean(alk_monthly_RC4US,1,'native','omitnan')';
no3_ann_RC4US = mean(no3_monthly_RC4US,1,'native','omitnan')';
nh4_ann_RC4US = mean(nh4_monthly_RC4US,1,'native','omitnan')';
o2_ann_RC4US = mean(o2_monthly_RC4US,1,'native','omitnan')';
dip_ann_RC4US = mean(dip_monthly_RC4US,1,'native','omitnan')';
si_ann_RC4US = mean(si_monthly_RC4US,1,'native','omitnan')';
din_ann_RC4US = no3_ann_RC4US + nh4_ann_RC4US;
don_ann_RC4US = mean(don_monthly_RC4US,1,'native','omitnan')';
if nutrient_option == 1
  don_ann_RC4US = ones(size(lon_stations_RC4US))*NaN;
  pn_ann_RC4US = ones(size(lon_stations_RC4US))*NaN;
  dop_ann_RC4US = ones(size(lon_stations_RC4US))*NaN;
  pp_ann_RC4US = ones(size(lon_stations_RC4US))*NaN;
elseif nutrient_option == 2
  don2_ann_RC4US = mean(don2_monthly_RC4US,1,'native','omitnan')';
  pn_ann_RC4US = mean(pn_monthly_RC4US,1,'native','omitnan')';
  dop_ann_RC4US = mean(dop_monthly_RC4US,1,'native','omitnan')';
  pp_ann_RC4US = mean(pp_monthly_RC4US,1,'native','omitnan')';
end
dfe_ann_RC4US = ones(size(lon_stations_RC4US))*NaN;
pfe_ann_RC4US = ones(size(lon_stations_RC4US))*NaN;

for n = 1:size(lon_stations_RC4US,1)
     
    % Move the Susquehanna a bit south so that it catches the Chesapeake
    % and not the Delaware.
    if strcmp('Susquehanna',station_names_RC4US{n})
        lat_stations_RC4US(n) = 38.5;
        lon_stations_RC4US(n) = -77.5;
        %pause
    end
    
    if strcmp('Delaware',station_names_RC4US{n})
        lat_stations_RC4US(n) = 39.5;
        lon_stations_RC4US(n) = -75.5;
    end
    
    if strcmp('Potomac',station_names_RC4US{n})
        lat_stations_RC4US(n) = 38.5;
        lon_stations_RC4US(n) = -77.5;
    end
    
    % Move the Mississipi to the same point and let the larger flow
    % naturally overwrite
    if strcmp('Mississippi',station_names_RC4US{n})
        lat_stations_RC4US(n) = 29.25;
        lon_stations_RC4US(n) = -89.25;
    end
    
    if strcmp('Alabama',station_names_RC4US{n})
        lat_stations_RC4US(n) = 30.5;
    end
    
end

%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%
% Gulf of Saint Lawrence Data from Diane Lavoie                           %
%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%
load /archive/cas/COBALT_EVAL/River_Data/Lavoie_GSL/river_DIC.dat;
dic_GSL = river_DIC; clear river_DIC; 
load /archive/cas/COBALT_EVAL/River_Data/Lavoie_GSL/river_Alk.dat;
alk_GSL = river_Alk; clear river_Alk; % meq m-3
load /archive/cas/COBALT_EVAL/River_Data/Lavoie_GSL/river_nox.dat;
no3_GSL = river_nox; clear river_nox; % mmoles m-3
file_name_GSL = '/archive/cas/COBALT_EVAL/River_Data/Lavoie_GSL/river_discharge_approx.csv';
station_data_GSL = readtable(file_name_GSL);

station_names_GSL = station_data_GSL{:,4};
lon_stations_GSL = station_data_GSL{:,2};
lat_stations_GSL = station_data_GSL{:,3};
Q_ann_GSL = station_data_GSL{:,5};

% Create arrays of monthly values for all river consituents.  If the     
% dataset does not have the required information, enter an NaN.           
dic_monthly_GSL = dic_GSL(1:12,3:end);
alk_monthly_GSL = alk_GSL(1:12,3:end);
no3_monthly_GSL = no3_GSL(1:12,3:end);
% in areas where nh4 is not available, set to 0 to prevent extrapolation
nh4_monthly_GSL = zeros(12,size(lon_stations_GSL,1));
% if no nh4 present DIN = no3
din_monthly_GSL = no3_monthly_GSL + nh4_monthly_GSL;
don_monthly_GSL = ones(12,size(lon_stations_GSL,1))*NaN;
pn_monthly_GSL = ones(12,size(lon_stations_GSL,1))*NaN;
dip_monthly_GSL = ones(12,size(lon_stations_GSL,1))*NaN;
dop_monthly_GSL = ones(12,size(lon_stations_GSL,1))*NaN;
pp_monthly_GSL = ones(12,size(lon_stations_GSL,1))*NaN;
dfe_monthly_GSL = ones(12,size(lon_stations_GSL,1))*NaN;
pfe_monthly_GSL = ones(12,size(lon_stations_GSL,1))*NaN;
si_monthly_GSL = ones(12,size(lon_stations_GSL,1))*NaN;
o2_monthly_GSL = ones(12,size(lon_stations_GSL,1))*NaN;

dic_ann_GSL = mean(dic_monthly_GSL,1)';
alk_ann_GSL = mean(alk_monthly_GSL,1)';
no3_ann_GSL = mean(no3_monthly_GSL,1)';
nh4_ann_GSL = ones(size(lon_stations_GSL))*NaN;
din_ann_GSL = ones(size(lon_stations_GSL))*NaN;
don_ann_GSL = ones(size(lon_stations_GSL))*NaN;
pn_ann_GSL = ones(size(lon_stations_GSL))*NaN;
dip_ann_GSL = ones(size(lon_stations_GSL))*NaN;
dop_ann_GSL = ones(size(lon_stations_GSL))*NaN;
pp_ann_GSL = ones(size(lon_stations_GSL))*NaN;
dfe_ann_GSL = ones(size(lon_stations_GSL))*NaN;
pfe_ann_GSL = ones(size(lon_stations_GSL))*NaN;
si_ann_GSL = ones(size(lon_stations_GSL))*NaN;
o2_ann_GSL = ones(size(lon_stations_GSL))*NaN;

for n = 1:size(lon_stations_GSL,1)
  if strcmp('Saint John',station_names_GSL{n})
        lat_stations_GSL(n) = 46.25;
        lon_stations_GSL(n) = -66.25;
  end
end

%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%
% Selected Large Rivers with Global NEWS nutrients + DIC/Alk (i.e.,       %
% "NEWSplus").  These rivers fill in any large areas without direct obs   %
% to prevent unrealistic extrapolation from much different areas.  For    %
% NWA12, these are primary in Mexico, Central America and South America.  %
%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%
file_name_extra = '/archive/cas/Regional_MOM6/NWA12/NWA12_ExtraRivers/stations_extra_NWA12.csv';
station_data_extra = readtable(file_name_extra);
station_names_extra = station_data_extra{:,1};
lon_stations_extra = station_data_extra{:,3};
lat_stations_extra = station_data_extra{:,4};
Q_ann_extra = station_data_extra{:,5};

dic_ann_extra = station_data_extra{:,6};
alk_ann_extra = station_data_extra{:,7};
% for global NEWS stations, enter all DIN as no3
no3_ann_extra = station_data_extra{:,8};
% for stations where nh4 is not available, enter as 0
nh4_ann_extra = zeros(size(lon_stations_extra));
din_ann_extra = station_data_extra{:,8};
don_ann_extra = station_data_extra{:,9};
pn_ann_extra = station_data_extra{:,10};
dip_ann_extra = station_data_extra{:,11};
dop_ann_extra = station_data_extra{:,12};
pp_ann_extra = station_data_extra{:,13};
dfe_ann_extra = ones(size(lon_stations_extra))*NaN;
pfe_ann_extra = ones(size(lon_stations_extra))*NaN;
si_ann_extra = station_data_extra{:,14};
o2_ann_extra = ones(size(lon_stations_extra))*NaN;

dic_monthly_extra = ones(12,size(lon_stations_extra,1))*NaN;
alk_monthly_extra = ones(12,size(lon_stations_extra,1))*NaN;
no3_monthly_extra = ones(12,size(lon_stations_extra,1))*NaN;
nh4_monthly_extra = ones(12,size(lon_stations_extra,1))*NaN;
din_monthly_extra = ones(12,size(lon_stations_extra,1))*NaN;
don_monthly_extra = ones(12,size(lon_stations_extra,1))*NaN;
pn_monthly_extra = ones(12,size(lon_stations_extra,1))*NaN;
dip_monthly_extra = ones(12,size(lon_stations_extra,1))*NaN;
dop_monthly_extra = ones(12,size(lon_stations_extra,1))*NaN;
pp_monthly_extra = ones(12,size(lon_stations_extra,1))*NaN;
dfe_monthly_extra = ones(12,size(lon_stations_extra,1))*NaN;
pfe_monthly_extra = ones(12,size(lon_stations_extra,1))*NaN;
si_monthly_extra = ones(12,size(lon_stations_extra,1))*NaN;
o2_monthly_extra = ones(12,size(lon_stations_extra,1))*NaN;

%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%
% Combine all annual and monthly station data                             %
%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%

station_names_all = [station_names_RC4US; station_names_GSL; station_names_extra];
lon_stations_all = [lon_stations_RC4US; lon_stations_GSL; lon_stations_extra];
lat_stations_all = [lat_stations_RC4US; lat_stations_GSL; lat_stations_extra];
Q_ann_all = [Q_ann_RC4US; Q_ann_GSL; Q_ann_extra];

dic_ann_all = [dic_ann_RC4US; dic_ann_GSL; dic_ann_extra];
alk_ann_all = [alk_ann_RC4US; alk_ann_GSL; alk_ann_extra];
no3_ann_all = [no3_ann_RC4US; no3_ann_GSL; no3_ann_extra];
nh4_ann_all = [nh4_ann_RC4US; nh4_ann_GSL; nh4_ann_extra];
din_ann_all = [din_ann_RC4US; din_ann_GSL; din_ann_extra];
don_ann_all = [don_ann_RC4US; don_ann_GSL; don_ann_extra];
pn_ann_all = [pn_ann_RC4US; pn_ann_GSL; pn_ann_extra];
dip_ann_all = [dip_ann_RC4US; dip_ann_GSL; dip_ann_extra];
dop_ann_all = [dop_ann_RC4US; dop_ann_GSL; dop_ann_extra];
pp_ann_all = [pp_ann_RC4US; pp_ann_GSL; pp_ann_extra];
dfe_ann_all = [dfe_ann_RC4US; dfe_ann_GSL; dfe_ann_extra];
pfe_ann_all = [pfe_ann_RC4US; pfe_ann_GSL; pfe_ann_extra];
si_ann_all = [si_ann_RC4US; si_ann_GSL; si_ann_extra];
o2_ann_all = [o2_ann_RC4US; o2_ann_GSL; o2_ann_extra];

dic_monthly_all = [dic_monthly_RC4US dic_monthly_GSL dic_monthly_extra];
alk_monthly_all = [alk_monthly_RC4US alk_monthly_GSL alk_monthly_extra];
no3_monthly_all = [no3_monthly_RC4US no3_monthly_GSL no3_monthly_extra];
nh4_monthly_all = [nh4_monthly_RC4US nh4_monthly_GSL nh4_monthly_extra];
din_monthly_all = [din_monthly_RC4US din_monthly_GSL din_monthly_extra];
don_monthly_all = [don_monthly_RC4US don_monthly_GSL don_monthly_extra];
pn_monthly_all = [pn_monthly_RC4US pn_monthly_GSL pn_monthly_extra];
dip_monthly_all = [dip_monthly_RC4US dip_monthly_GSL dip_monthly_extra];
dop_monthly_all = [dop_monthly_RC4US dop_monthly_GSL dop_monthly_extra];
pp_monthly_all = [pp_monthly_RC4US pp_monthly_GSL pp_monthly_extra];
dfe_monthly_all = [dfe_monthly_RC4US dfe_monthly_GSL dfe_monthly_extra];
pfe_monthly_all = [pfe_monthly_RC4US pfe_monthly_GSL pfe_monthly_extra];
si_monthly_all = [si_monthly_RC4US si_monthly_GSL si_monthly_extra];
o2_monthly_all = [o2_monthly_RC4US o2_monthly_GSL o2_monthly_extra];

%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%
% Load in monthly climatology of river forcing from the regional grid.    %
% File contains:                                                          %
% runoff: monthly average runoff in kg m-2 sec-1                          %
% area: area of grid cell in m-2                                          %
% lon: longitude (0-360 degrees)                                          %
% lat: latitude                                                           %                                                                        %
%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%
load ./glofas_runoff_mean.mat

% convert runoff from kg m-2 sec-1 to m3 sec-1
Q_mod_monthly = zeros(size(runoff));
for m = 1:12
  Q_mod_monthly(m,:,:) = squeeze(runoff(m,:,:)).*area_mod./1000;
end
Q_mod_ann = squeeze(mean(Q_mod_monthly,1));
clear lon lat runoff area;

grid_file = '/archive/cas/Regional_MOM6/NWA12/nwa12_ocean_static.nc';
temp = ncread(grid_file,'deptho');
depth = permute(temp,[2,1]); clear temp;
depth(isnan(depth)) = -1;

%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%
% Filter for rivers in the region, set thresholds for minimum river size, %
% set parameters for plotting routines.                                   %
%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%

% use grid to filter rivers outside domain
lat_mod_max = max(lat_mod(:));
lat_mod_min = min(lat_mod(:));
lon_mod_max = max(lon_mod(:));
lon_mod_min = min(lon_mod(:));

in_region = find( (lon_stations_all <= lon_mod_max) & (lon_stations_all >= lon_mod_min) & ...
    (lat_stations_all <= lat_mod_max) & (lat_stations_all >= lat_mod_min) & ...
    (isfinite(Q_ann_all)) & (Q_ann_all > Q_min) );
num_rivers = size(in_region,1);

station_names_reg = station_names_all(in_region);
lon_stations_reg = lon_stations_all(in_region);
lat_stations_reg = lat_stations_all(in_region);
Q_ann_reg = Q_ann_all(in_region);
dic_ann_reg = dic_ann_all(in_region);
alk_ann_reg = alk_ann_all(in_region);
no3_ann_reg = no3_ann_all(in_region);
nh4_ann_reg = nh4_ann_all(in_region);
din_ann_reg = din_ann_all(in_region);
don_ann_reg = don_ann_all(in_region);
pn_ann_reg = pn_ann_all(in_region);
dip_ann_reg = dip_ann_all(in_region);
dop_ann_reg = dop_ann_all(in_region);
pp_ann_reg = pp_ann_all(in_region);
dfe_ann_reg = dfe_ann_all(in_region);
pfe_ann_reg = pfe_ann_all(in_region);
si_ann_reg = si_ann_all(in_region);
o2_ann_reg = o2_ann_all(in_region);

for m = 1:12
  dic_monthly_reg(m,:) = dic_monthly_all(m,in_region);
  alk_monthly_reg(m,:) = alk_monthly_all(m,in_region);
  no3_monthly_reg(m,:) = no3_monthly_all(m,in_region);
  nh4_monthly_reg(m,:) = nh4_monthly_all(m,in_region);
  din_monthly_reg(m,:) = din_monthly_all(m,in_region);
  don_monthly_reg(m,:) = don_monthly_all(m,in_region);
  pn_monthly_reg(m,:) = pn_monthly_all(m,in_region);
  dip_monthly_reg(m,:) = dip_monthly_all(m,in_region);
  dop_monthly_reg(m,:) = dop_monthly_all(m,in_region);
  pp_monthly_reg(m,:) = pp_monthly_all(m,in_region);
  dfe_monthly_reg(m,:) = dfe_monthly_all(m,in_region);
  pfe_monthly_reg(m,:) = pfe_monthly_all(m,in_region);
  si_monthly_reg(m,:) = si_monthly_all(m,in_region);
  o2_monthly_reg(m,:) = o2_monthly_all(m,in_region);
end

%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%
% Assigning outflow points to rivers.                                     %
%  1. Assignment starts with the rivers with the smallest flow and works  %
%     to the largest, w/larger river characteristics taking precedence to %
%     ensure the most significant rivers are well represented.            %
%  2. The algorithm keeps choosing the closest points to each river mouth %
%     until the assigned flow is as close as possible to that observed    %
%  3. Once the outflow points are assigned using the mean flow values,    %
%     monthly concentrations are assigned to those points.                %
%  4. A simple "nearest neighbor" algorithm is used to fill in the gaps   %
%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%

% Sort rivers by discharge
[Q_ann_sort,sort_ind] = sort(Q_ann_reg,'ascend');

station_names_sort = station_names_reg(sort_ind);
lon_stations_sort = lon_stations_reg(sort_ind);
lat_stations_sort = lat_stations_reg(sort_ind);
Q_ann_sort = Q_ann_reg(sort_ind);
dic_ann_sort = dic_ann_reg(sort_ind);
alk_ann_sort = alk_ann_reg(sort_ind);
no3_ann_sort = no3_ann_reg(sort_ind);
nh4_ann_sort = nh4_ann_reg(sort_ind);
din_ann_sort = din_ann_reg(sort_ind);
don_ann_sort = don_ann_reg(sort_ind);
pn_ann_sort = pn_ann_reg(sort_ind);
dip_ann_sort = dip_ann_reg(sort_ind);
dop_ann_sort = dop_ann_reg(sort_ind);
pp_ann_sort = pp_ann_reg(sort_ind);
dfe_ann_sort = dfe_ann_reg(sort_ind);
pfe_ann_sort = pfe_ann_reg(sort_ind);
si_ann_sort = si_ann_reg(sort_ind);
o2_ann_sort = o2_ann_reg(sort_ind);

for m = 1:12
  dic_monthly_sort(m,:) = dic_monthly_reg(m,sort_ind);
  alk_monthly_sort(m,:) = alk_monthly_reg(m,sort_ind);
  no3_monthly_sort(m,:) = no3_monthly_reg(m,sort_ind);
  nh4_monthly_sort(m,:) = nh4_monthly_reg(m,sort_ind);
  din_monthly_sort(m,:) = din_monthly_reg(m,sort_ind);
  don_monthly_sort(m,:) = don_monthly_reg(m,sort_ind);
  pn_monthly_sort(m,:) = pn_monthly_reg(m,sort_ind);
  dip_monthly_sort(m,:) = dip_monthly_reg(m,sort_ind);
  dop_monthly_sort(m,:) = dop_monthly_reg(m,sort_ind);
  pp_monthly_sort(m,:) = pp_monthly_reg(m,sort_ind);
  dfe_monthly_sort(m,:) = dfe_monthly_reg(m,sort_ind);
  pfe_monthly_sort(m,:) = pfe_monthly_reg(m,sort_ind);
  si_monthly_sort(m,:) = si_monthly_reg(m,sort_ind);
  o2_monthly_sort(m,:) = o2_monthly_reg(m,sort_ind);
end

% Create vectors of values at the runoff points from the model grid.  These
% are used to accelerate the mapping relative to wrangling the full grid
% with all the zeros included. "ind_ro" are the grid indexes with runoff
ind_ro = find(Q_mod_ann > 0);
Q_mod_vec = Q_mod_ann(ind_ro);
lon_mod_runoff_vec = lon_mod(ind_ro);
lat_mod_runoff_vec = lat_mod(ind_ro);
Q_mod_monthly_vecs = zeros(12,size(lon_mod_runoff_vec,1));
for m = 1:12
    temp = squeeze(Q_mod_monthly(m,:,:));
    Q_mod_monthly_vecs(m,:) = temp(ind_ro);
end

% Create a grid of saturated oxygen values using the world ocean atlas data
temp_woa_monthly_vecs = zeros(12,size(lon_mod_runoff_vec,1));
o2sat_woa_monthly_vecs = zeros(12,size(lon_mod_runoff_vec,1));

% Constants for o2 saturation calculation (taken from COBALT)
a_0 = 2.00907;
a_1 = 3.22014;
a_2 = 4.05010;
a_3 = 4.94457;
a_4 = -2.56847e-1;
a_5 = 3.88767;
sal = 0;
b_0 = -6.24523e-3;
b_1 = -7.37614e-3;
b_2 = -1.03410e-2;
b_3 = -8.17083e-3;
c_0 = -4.88682e-7;

for m = 1:12
  temp = squeeze(woa_temp(m,:,:));
  % limit for validity of o2sat calculation
  temp(temp > 40) = 40; temp(temp < 0) = 0;
  temp_woa_monthly_vecs(m,:) = temp(ind_ro);
  % calculate the oxygen saturation at a given temperature and salinity = 0
  % code taken from COBALT with limits applied above
  tt = 298.15 - temp_woa_monthly_vecs(m,:);
  tkb = 273.15 + temp_woa_monthly_vecs(m,:);
  ts = log(tt / tkb);
  ts2 = ts  * ts;
  ts3 = ts2 * ts;
  ts4 = ts3 * ts;
  ts5 = ts4 * ts;
  
  o2sat_woa_monthly_vecs(m,:) = (1000.0/22391.6) * 1000 * ... %convert from ml/l to mmol m-3
            exp(a_0 + a_1*ts + a_2*ts2 + a_3*ts3 + a_4*ts4 + a_5*ts5 + ...
            (b_0 + b_1*ts + b_2*ts2 + b_3*ts3 + c_0*sal)*sal);
end

%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%
% Load in fields generated from global NEWS.  Where necessary, the ratio  %
% of constituents relative to DIN will be used to fill forcing gaps       %
% The m-file used to generate the NEWS forcing file is included in this   %
% directory and uses an analogous mapping algorithm to this one           %
%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%
din_ann_NEWS = nc_varget(NEWS_file,'NO3_CONC');
aa = find(din_ann_NEWS > 0);
temp1 = nc_varget(NEWS_file,'LDON_CONC');
temp2 = nc_varget(NEWS_file,'SLDON_CONC');
temp3 = nc_varget(NEWS_file,'SRDON_CONC');
don_ann_NEWS = temp1 + temp2 + temp3;
don_ratio_NEWS_vec = don_ann_NEWS(aa)./din_ann_NEWS(aa);
clear temp1 temp2 temp3;
pn_ann_NEWS = nc_varget(NEWS_file,'NDET_CONC');
pn_ratio_NEWS_vec = pn_ann_NEWS(aa)./din_ann_NEWS(aa);

dip_ann_NEWS = nc_varget(NEWS_file,'PO4_CONC');
dip_ratio_NEWS_vec = dip_ann_NEWS(aa)./din_ann_NEWS(aa);
temp1 = nc_varget(NEWS_file,'LDOP_CONC');
temp2 = nc_varget(NEWS_file,'SLDOP_CONC');
temp3 = nc_varget(NEWS_file,'SRDOP_CONC');
dop_ann_NEWS = temp1 + temp2 + temp3;
dop_ratio_NEWS_vec = dop_ann_NEWS(aa)./din_ann_NEWS(aa);
clear temp1 temp2 temp3;
pp_ann_NEWS = nc_varget(NEWS_file,'PDET_CONC');
pp_ratio_NEWS_vec = pp_ann_NEWS(aa)./din_ann_NEWS(aa);
si_ann_NEWS = nc_varget(NEWS_file,'SI_CONC');
si_ratio_NEWS_vec = si_ann_NEWS(aa)./din_ann_NEWS(aa);

% Vectors to hold monthly values mapped onto model runoff points
dic_mod_monthly_vecs = zeros(12,size(lon_mod_runoff_vec,1));
alk_mod_monthly_vecs = zeros(12,size(lat_mod_runoff_vec,1));
no3_mod_monthly_vecs = zeros(12,size(lat_mod_runoff_vec,1));
nh4_mod_monthly_vecs = zeros(12,size(lat_mod_runoff_vec,1));
din_mod_monthly_vecs = zeros(12,size(lat_mod_runoff_vec,1));
don_mod_monthly_vecs = zeros(12,size(lat_mod_runoff_vec,1));
pn_mod_monthly_vecs = zeros(12,size(lat_mod_runoff_vec,1));
dip_mod_monthly_vecs = zeros(12,size(lat_mod_runoff_vec,1));
dop_mod_monthly_vecs = zeros(12,size(lat_mod_runoff_vec,1));
pp_mod_monthly_vecs = zeros(12,size(lat_mod_runoff_vec,1));
dfe_mod_monthly_vecs = zeros(12,size(lat_mod_runoff_vec,1));
pfe_mod_monthly_vecs = zeros(12,size(lat_mod_runoff_vec,1));
si_mod_monthly_vecs = zeros(12,size(lat_mod_runoff_vec,1));
o2_mod_monthly_vecs = zeros(12,size(lat_mod_runoff_vec,1));


%%

%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%
% Loop identifies points assigned to each river                           %
%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%
for k=1:num_rivers
  dist = pdist2([lon_stations_sort(k) lat_stations_sort(k)], ...
                [lon_mod_runoff_vec lat_mod_runoff_vec]);
  [dist_sort, dist_sort_ind] = sort(dist,'ascend');
    
  if dist_sort(1) < min_dist
    Q_sum1 = 0;
    Q_sum2 = 0;
    n = 0;
    while (Q_sum2 < Q_ann_sort(k) && (dist_sort(n+1) < max_dist))
      Q_sum1 = Q_sum2;
      n = n+1;
      Q_sum2 = Q_sum1 + Q_mod_vec(dist_sort_ind(n));
    end
    if abs(Q_sum1 - Q_ann_sort(k)) < abs(Q_sum2 - Q_ann_sort(k))
      nrp = n-1;  % number of runoff points
      %[Q_sum1 Q_ann_sort(k)]  % a quick check for comparable flow
    else
      nrp = n;
      %[Q_sum2 Q_ann_sort(k)]
    end
    
    % enter monthly concentration values into an array of monthly values
    % if no monthly value is available, use annuals.
    for m = 1:12
      
      if isnan(dic_monthly_sort(m,k))
        if isfinite(dic_ann_sort(k))
          dic_mod_monthly_vecs(m,dist_sort_ind(1:nrp)) = dic_ann_sort(k);
        else
          dic_mod_monthly_vecs(m,dist_sort_ind(1:nrp)) = 0;
        end
      else
        dic_mod_monthly_vecs(m,dist_sort_ind(1:nrp)) = dic_monthly_sort(m,k);
      end
        
      if isnan(alk_monthly_sort(m,k))
        if isfinite(dic_ann_sort(k))
          alk_mod_monthly_vecs(m,dist_sort_ind(1:nrp)) = alk_ann_sort(k);
        else
          alk_mod_monthly_vecs(m,dist_sort_ind(1:nrp)) = 0;
        end
      else
        alk_mod_monthly_vecs(m,dist_sort_ind(1:nrp)) = alk_monthly_sort(m,k);
      end
      
      % mapping assumes that DIN is defined for nutrient calculations since
      % ratios relative to DIN are used to fill in other components.  If
      % DIN is not defined, values are left at 0 and eventually filled with
      % a nearest neighbor filling (next section)
      
      if (isfinite(din_monthly_sort(m,k)) || isfinite(din_ann_sort(k)) )
        if isfinite(din_monthly_sort(m,k))
          din_mod_monthly_vecs(m,dist_sort_ind(1:nrp)) = din_monthly_sort(m,k);
        elseif isfinite(din_ann_sort(k))
          din_mod_monthly_vecs(m,dist_sort_ind(1:nrp)) = din_ann_sort(k);
        end
        
        if isfinite(no3_monthly_sort(m,k))
          no3_mod_monthly_vecs(m,dist_sort_ind(1:nrp)) = no3_monthly_sort(m,k);
        elseif isfinite(no3_ann_sort(k))
          no3_mod_monthly_vecs(m,dist_sort_ind(1:nrp)) = no3_ann_sort(k);
        end
        
        if isfinite(nh4_monthly_sort(m,k))
          nh4_mod_monthly_vecs(m,dist_sort_ind(1:nrp)) = nh4_monthly_sort(m,k);
        elseif isfinite(nh4_ann_sort(k))
          nh4_mod_monthly_vecs(m,dist_sort_ind(1:nrp)) = nh4_ann_sort(k);
        end
      
        if (isnan(don_monthly_sort(m,k)) && isnan(don_ann_sort(k)))
          don_mod_monthly_vecs(m,dist_sort_ind(1:nrp)) = ...
            din_mod_monthly_vecs(m,dist_sort_ind(1:nrp)).* ...
            don_ratio_NEWS_vec(dist_sort_ind(1:nrp))';
        elseif (isnan(don_monthly_sort(m,k)) && ~isnan(don_ann_sort(k)))
          don_mod_monthly_vecs(m,dist_sort_ind(1:nrp)) = don_ann_sort(k);
        else
          don_mod_monthly_vecs(m,dist_sort_ind(1:nrp)) = don_monthly_sort(m,k);
        end
      
        if (isnan(pn_monthly_sort(m,k)) && isnan(pn_ann_sort(k)))
          pn_mod_monthly_vecs(m,dist_sort_ind(1:nrp)) = ...
              din_mod_monthly_vecs(m,dist_sort_ind(1:nrp)).* ...
              pn_ratio_NEWS_vec(dist_sort_ind(1:nrp))';
        elseif (isnan(pn_monthly_sort(m,k)) && ~isnan(pn_ann_sort(k)))
          pn_mod_monthly_vecs(m,dist_sort_ind(1:nrp)) = pn_ann_sort(k);
        else
          pn_mod_monthly_vecs(m,dist_sort_ind(1:nrp)) = pn_monthly_sort(m,k);
        end
      
        if (isnan(dip_monthly_sort(m,k)) && isnan(dip_ann_sort(k)))
          dip_mod_monthly_vecs(m,dist_sort_ind(1:nrp)) = ...
            din_mod_monthly_vecs(m,dist_sort_ind(1:nrp)).* ...
            dip_ratio_NEWS_vec(dist_sort_ind(1:nrp))';
        elseif (isnan(dip_monthly_sort(m,k)) && ~isnan(dip_ann_sort(k)))
          dip_mod_monthly_vecs(m,dist_sort_ind(1:nrp)) = dip_ann_sort(k);
        else
          dip_mod_monthly_vecs(m,dist_sort_ind(1:nrp)) = dip_monthly_sort(m,k);
        end
      
        if (isnan(dop_monthly_sort(m,k)) && isnan(dop_ann_sort(k)))
          dop_mod_monthly_vecs(m,dist_sort_ind(1:nrp)) = ...
              din_mod_monthly_vecs(m,dist_sort_ind(1:nrp)).* ...
              dop_ratio_NEWS_vec(dist_sort_ind(1:nrp))';
        elseif (isnan(dop_monthly_sort(m,k)) && ~isnan(dop_ann_sort(k)))
          dop_mod_monthly_vecs(m,dist_sort_ind(1:nrp)) = dop_ann_sort(k);
        else
          dop_mod_monthly_vecs(m,dist_sort_ind(1:nrp)) = dop_monthly_sort(m,k);
        end
      
        if (isnan(pp_monthly_sort(m,k)) && isnan(pp_ann_sort(k)))
          pp_mod_monthly_vecs(m,dist_sort_ind(1:nrp)) = ...
              din_mod_monthly_vecs(m,dist_sort_ind(1:nrp)).* ...
              pp_ratio_NEWS_vec(dist_sort_ind(1:nrp))';
        elseif (isnan(pp_monthly_sort(m,k)) && ~isnan(pp_ann_sort(k)))
          pp_mod_monthly_vecs(m,dist_sort_ind(1:nrp)) = pp_ann_sort(k);
        else
          pp_mod_monthly_vecs(m,dist_sort_ind(1:nrp)) = pp_monthly_sort(m,k);
        end
      
        if (isnan(si_monthly_sort(m,k)) && isnan(si_ann_sort(k)))
          si_mod_monthly_vecs(m,dist_sort_ind(1:nrp)) = ...
              din_mod_monthly_vecs(m,dist_sort_ind(1:nrp)).* ...
              si_ratio_NEWS_vec(dist_sort_ind(1:nrp))';
        elseif (isnan(si_monthly_sort(m,k)) && ~isnan(si_ann_sort(k)))
          si_mod_monthly_vecs(m,dist_sort_ind(1:nrp)) = si_ann_sort(k);
        else
          si_mod_monthly_vecs(m,dist_sort_ind(1:nrp)) = si_monthly_sort(m,k);
        end
        
        if isnan(o2_monthly_sort(m,k))
          o2_mod_monthly_vecs(m,dist_sort_ind(1:nrp)) = ...
              o2sat_woa_monthly_vecs(m,dist_sort_ind(1:nrp));
        else
          o2_mod_monthly_vecs(m,dist_sort_ind(1:nrp)) = o2_monthly_sort(m,k);
        end
        
      end
    end
            
    % plot to check location if inspect_map == 'y'.  The plot puts
    % open circles at each runoff location in the model grid and fills
    % those that are assigned to each river.  Note that some of the smaller
    % rivers may be replaced with larger ones as the fitting process
    % continues.
    
    if inspect_map == 'y'
      figure(1)
      clf
      scatter3(lon_mod_runoff_vec,lat_mod_runoff_vec,log10(Q_mod_vec),3,log10(Q_mod_vec));
      hold on
      scatter3(lon_mod_runoff_vec(dist_sort_ind(1:nrp)),lat_mod_runoff_vec(dist_sort_ind(1:nrp)), ...
        log10(Q_mod_vec(dist_sort_ind(1:nrp))),25, ...
        log10(Q_mod_vec(dist_sort_ind(1:nrp))),'filled');
      view(2);
      plot3(lon_stations_sort(k),lat_stations_sort(k),1e5,'k.','MarkerSize',20); 
      contour(lon_mod,lat_mod,depth,[0 0],'k-');
      axis([lon_stations_sort(k)-plot_width/2 lon_stations_sort(k)+plot_width/2 ...
          lat_stations_sort(k)-plot_width/2 lat_stations_sort(k)+plot_width/2]);
      caxis([-4 3]);
      titl = ['river number: ',num2str(k),' name: ',station_names_sort{k}];
      title(titl);
      colorbar;
    
      % check the values of each mapping
      N_check = mean(din_mod_monthly_vecs(:,dist_sort_ind(1:nrp)),'all') + ...
        mean(don_mod_monthly_vecs(:,dist_sort_ind(1:nrp)),'all') + ...
        mean(pn_mod_monthly_vecs(:,dist_sort_ind(1:nrp)),'all');
      P_check = mean(dip_mod_monthly_vecs(:,dist_sort_ind(1:nrp)),'all') + ...
        mean(dop_mod_monthly_vecs(:,dist_sort_ind(1:nrp)),'all') + ...
        mean(pp_mod_monthly_vecs(:,dist_sort_ind(1:nrp)),'all');
      SI_check = mean(si_mod_monthly_vecs(:,dist_sort_ind(1:nrp)),'all');
      DIN_check = mean(din_mod_monthly_vecs(:,dist_sort_ind(1:nrp)),'all');
      DON_check = mean(don_mod_monthly_vecs(:,dist_sort_ind(1:nrp)),'all');
      PN_check = mean(pn_mod_monthly_vecs(:,dist_sort_ind(1:nrp)),'all');
      DIP_check = mean(dip_mod_monthly_vecs(:,dist_sort_ind(1:nrp)),'all');
      DOP_check = mean(dop_mod_monthly_vecs(:,dist_sort_ind(1:nrp)),'all');
      PP_check = mean(pp_mod_monthly_vecs(:,dist_sort_ind(1:nrp)),'all');
      SI_check = mean(si_mod_monthly_vecs(:,dist_sort_ind(1:nrp)),'all');
    
      station_names_sort(k)
      ind = dist_sort_ind(1:nrp);
      'total flow in m3 sec'
      [Q_ann_sort(k) sum(Q_mod_vec(dist_sort_ind(1:nrp)))]
      'N, P conc (mmoles m-3), DI, DO, P'
      [DIN_check DON_check PN_check]
      [DIP_check DOP_check PP_check]
      'Total N, Total P, Total N: Total P'
      [N_check P_check N_check/P_check]
      'DO:DI and P:DI ratios';
      [DON_check/DIN_check PN_check/DIN_check];
      [DOP_check/DIP_check PP_check/DIP_check];
      'silica concentration (mmoles m-3)';
      SI_check;
      
      pause
    end
  
  % If river is outside the domain, skip all of the calculations above and
  % just plot for inspection/evaluation
  else
    % This is for rivers that were outside of the domain
    if inspect_map == 'y'
      figure(1)
      clf
      scatter3(lon_mod_runoff_vec,lat_mod_runoff_vec,log10(Q_mod_vec),3,log10(Q_mod_vec));
      hold on
      view(2);
      plot3(lon_stations_sort(k),lat_stations_sort(k),1e5,'k.','MarkerSize',20); 
      axis([lon_stations_sort(k)-10 lon_stations_sort(k)+10 ...
          lat_stations_sort(k)-10 lat_stations_sort(k)+10]);
      caxis([-4 3]);
      titl = ['OUTSIDE: river number: ',num2str(k),' name: ',station_names_sort{k}];
      title(titl);
      colorbar;
      
      pause
    end
      
  end
end

%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%
% nearest neighbor search to fill in any runoff points that were not      %
% assigned after the runoff mapping step                                  %
%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%

for m = 1:12
  aa = find(dic_mod_monthly_vecs(m,:) == 0); 
  bb = find(dic_mod_monthly_vecs(m,:) > 0);
  F = scatteredInterpolant(lon_mod_runoff_vec(bb),lat_mod_runoff_vec(bb), ...
    dic_mod_monthly_vecs(m,bb)','nearest','nearest');
  dic_mod_monthly_vecs(m,aa) = F(lon_mod_runoff_vec(aa),lat_mod_runoff_vec(aa));
  
  aa = find(alk_mod_monthly_vecs(m,:) == 0);
  bb = find(alk_mod_monthly_vecs(m,:) > 0);
  F = scatteredInterpolant(lon_mod_runoff_vec(bb),lat_mod_runoff_vec(bb), ...
    alk_mod_monthly_vecs(m,bb)','nearest','nearest');
  alk_mod_monthly_vecs(m,aa) = F(lon_mod_runoff_vec(aa),lat_mod_runoff_vec(aa));
  
  aa = find(no3_mod_monthly_vecs(m,:) == 0);
  bb = find(no3_mod_monthly_vecs(m,:) > 0);
  F = scatteredInterpolant(lon_mod_runoff_vec(bb),lat_mod_runoff_vec(bb), ...
    no3_mod_monthly_vecs(m,bb)','nearest','nearest');
  no3_mod_monthly_vecs(m,aa) = F(lon_mod_runoff_vec(aa),lat_mod_runoff_vec(aa));
  
  aa = find(nh4_mod_monthly_vecs(m,:) == 0);
  bb = find(nh4_mod_monthly_vecs(m,:) > 0);
  F = scatteredInterpolant(lon_mod_runoff_vec(bb),lat_mod_runoff_vec(bb), ...
    nh4_mod_monthly_vecs(m,bb)','nearest','nearest');
  nh4_mod_monthly_vecs(m,aa) = F(lon_mod_runoff_vec(aa),lat_mod_runoff_vec(aa));
  
  aa = find(din_mod_monthly_vecs(m,:) == 0);
  bb = find(din_mod_monthly_vecs(m,:) > 0);
  F = scatteredInterpolant(lon_mod_runoff_vec(bb),lat_mod_runoff_vec(bb), ...
    din_mod_monthly_vecs(m,bb)','nearest','nearest');
  din_mod_monthly_vecs(m,aa) = F(lon_mod_runoff_vec(aa),lat_mod_runoff_vec(aa));
  
  aa = find(don_mod_monthly_vecs(m,:) == 0);
  bb = find(don_mod_monthly_vecs(m,:) > 0);
  F = scatteredInterpolant(lon_mod_runoff_vec(bb),lat_mod_runoff_vec(bb), ...
    don_mod_monthly_vecs(m,bb)','nearest','nearest');
  don_mod_monthly_vecs(m,aa) = F(lon_mod_runoff_vec(aa),lat_mod_runoff_vec(aa));
  
  aa = find(pn_mod_monthly_vecs(m,:) == 0);
  bb = find(pn_mod_monthly_vecs(m,:) > 0);
  F = scatteredInterpolant(lon_mod_runoff_vec(bb),lat_mod_runoff_vec(bb), ...
    pn_mod_monthly_vecs(m,bb)','nearest','nearest');
  pn_mod_monthly_vecs(m,aa) = F(lon_mod_runoff_vec(aa),lat_mod_runoff_vec(aa));
  
  aa = find(dip_mod_monthly_vecs(m,:) == 0);
  bb = find(dip_mod_monthly_vecs(m,:) > 0);
  F = scatteredInterpolant(lon_mod_runoff_vec(bb),lat_mod_runoff_vec(bb), ...
    dip_mod_monthly_vecs(m,bb)','nearest','nearest');
  dip_mod_monthly_vecs(m,aa) = F(lon_mod_runoff_vec(aa),lat_mod_runoff_vec(aa));
  
  aa = find(dop_mod_monthly_vecs(m,:) == 0);
  bb = find(dop_mod_monthly_vecs(m,:) > 0);
  F = scatteredInterpolant(lon_mod_runoff_vec(bb),lat_mod_runoff_vec(bb), ...
    dop_mod_monthly_vecs(m,bb)','nearest','nearest');
  dop_mod_monthly_vecs(m,aa) = F(lon_mod_runoff_vec(aa),lat_mod_runoff_vec(aa));
  
  aa = find(pp_mod_monthly_vecs(m,:) == 0);
  bb = find(pp_mod_monthly_vecs(m,:) > 0);
  F = scatteredInterpolant(lon_mod_runoff_vec(bb),lat_mod_runoff_vec(bb), ...
    pp_mod_monthly_vecs(m,bb)','nearest','nearest');
  pp_mod_monthly_vecs(m,aa) = F(lon_mod_runoff_vec(aa),lat_mod_runoff_vec(aa));
  
  aa = find(si_mod_monthly_vecs(m,:) == 0);
  bb = find(si_mod_monthly_vecs(m,:) > 0);
  F = scatteredInterpolant(lon_mod_runoff_vec(bb),lat_mod_runoff_vec(bb), ...
    si_mod_monthly_vecs(m,bb)','nearest','nearest');
  si_mod_monthly_vecs(m,aa) = F(lon_mod_runoff_vec(aa),lat_mod_runoff_vec(aa));
end

% For o2sat, fill in any 0 values with saturated o2 at the world ocean
% atlas climatology
for m = 1:12
  aa = find(o2_mod_monthly_vecs(m,:) == 0);
  o2_mod_monthly_vecs(m,aa) = o2sat_woa_monthly_vecs(m,aa);
end

totn_mod_monthly_vecs = din_mod_monthly_vecs + don_mod_monthly_vecs + pn_mod_monthly_vecs;
totp_mod_monthly_vecs = dip_mod_monthly_vecs + dop_mod_monthly_vecs + pp_mod_monthly_vecs;

dicflux_mod_monthly_vecs = dic_mod_monthly_vecs.*Q_mod_monthly_vecs;
alkflux_mod_monthly_vecs = alk_mod_monthly_vecs.*Q_mod_monthly_vecs;
dinflux_mod_monthly_vecs = din_mod_monthly_vecs.*Q_mod_monthly_vecs;
no3flux_mod_monthly_vecs = no3_mod_monthly_vecs.*Q_mod_monthly_vecs;
nh4flux_mod_monthly_vecs = nh4_mod_monthly_vecs.*Q_mod_monthly_vecs;
dipflux_mod_monthly_vecs = dip_mod_monthly_vecs.*Q_mod_monthly_vecs;
donflux_mod_monthly_vecs = don_mod_monthly_vecs.*Q_mod_monthly_vecs;
dopflux_mod_monthly_vecs = dop_mod_monthly_vecs.*Q_mod_monthly_vecs;
pnflux_mod_monthly_vecs = pn_mod_monthly_vecs.*Q_mod_monthly_vecs;
ppflux_mod_monthly_vecs = pp_mod_monthly_vecs.*Q_mod_monthly_vecs;
siflux_mod_monthly_vecs = si_mod_monthly_vecs.*Q_mod_monthly_vecs;
totnflux_mod_monthly_vecs = totn_mod_monthly_vecs.*Q_mod_monthly_vecs;
totpflux_mod_monthly_vecs = totp_mod_monthly_vecs.*Q_mod_monthly_vecs;
o2flux_mod_monthly_vecs = o2_mod_monthly_vecs.*Q_mod_monthly_vecs;

dicflux_mod_ann_vec = mean(dicflux_mod_monthly_vecs,1);
alkflux_mod_ann_vec = mean(alkflux_mod_monthly_vecs,1);
dinflux_mod_ann_vec = mean(dinflux_mod_monthly_vecs,1);
no3flux_mod_ann_vec = mean(no3flux_mod_monthly_vecs,1);
nh4flux_mod_ann_vec = mean(nh4flux_mod_monthly_vecs,1);
dipflux_mod_ann_vec = mean(dipflux_mod_monthly_vecs,1);
donflux_mod_ann_vec = mean(donflux_mod_monthly_vecs,1);
dopflux_mod_ann_vec = mean(dopflux_mod_monthly_vecs,1);
pnflux_mod_ann_vec = mean(pnflux_mod_monthly_vecs,1);
ppflux_mod_ann_vec = mean(ppflux_mod_monthly_vecs,1);
siflux_mod_ann_vec = mean(siflux_mod_monthly_vecs,1);
totnflux_mod_ann_vec = mean(totnflux_mod_monthly_vecs,1);
totpflux_mod_ann_vec = mean(totpflux_mod_monthly_vecs,1);
o2flux_mod_ann_vec = mean(o2flux_mod_monthly_vecs,1);

%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%
% Produce plots to evaluate the mapping                                   %
%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%

% scale marker size with the freshwater flux
ms_vec = zeros(size(Q_mod_vec));
ms_vec(log10(Q_mod_vec) < 0) = 1;
ms_vec((log10(Q_mod_vec) > 0) & (log10(Q_mod_vec) < 1)) = 2.5;
ms_vec((log10(Q_mod_vec) > 1) & (log10(Q_mod_vec) < 2)) = 10;
ms_vec((log10(Q_mod_vec) > 2) & (log10(Q_mod_vec) < 3)) = 25;
ms_vec(log10(Q_mod_vec) > 3) = 100;

% DIC, Alk concentrations and DIC:Alk
if plot_progress
    for m = 1:12

      figure(1)
      clf

      subplot(1,3,1);
      scatter3(lon_mod_runoff_vec,lat_mod_runoff_vec,dic_mod_monthly_vecs(m,:),ms_vec, ...
               dic_mod_monthly_vecs(m,:),'filled');
      hold on
      view(2);
      caxis([0 2500]);
      colorbar
      titlestr = ['DIC, mmoles m-3; month = ',num2str(m)];
      title(titlestr);

      subplot(1,3,2);
      scatter3(lon_mod_runoff_vec,lat_mod_runoff_vec,alk_mod_monthly_vecs(m,:),ms_vec, ...
         alk_mod_monthly_vecs(m,:),'filled');
      hold on
      view(2);
      caxis([0 2500]);
      colorbar
      titlestr = ['Alk, meq m-3; month = ',num2str(m)];
      title(titlestr);

      subplot(1,3,3)
      dic_alk_ratio = dic_mod_monthly_vecs(m,:)./alk_mod_monthly_vecs(m,:);
      scatter3(lon_mod_runoff_vec,lat_mod_runoff_vec,dic_alk_ratio, ...
          ms_vec,dic_alk_ratio,'filled');
      hold on
      view(2);
      caxis([0.8 1.2]);
      colorbar
      title('DIC:Alk ratio');

      %pause
    end

    % Nitrogen Concentrations
    for m = 1:12

      figure(1)
      clf

      subplot(2,2,1);
      scatter3(lon_mod_runoff_vec,lat_mod_runoff_vec,din_mod_monthly_vecs(m,:),ms_vec, ...
               din_mod_monthly_vecs(m,:),'filled');
      hold on
      view(2);
      caxis([0 100]);
      colorbar
      titlestr = ['DIN, mmoles m-3; month = ',num2str(m)];
      title(titlestr);

      subplot(2,2,2);
      scatter3(lon_mod_runoff_vec,lat_mod_runoff_vec,no3_mod_monthly_vecs(m,:),ms_vec, ...
               din_mod_monthly_vecs(m,:),'filled');
      hold on
      view(2);
      caxis([0 100]);
      colorbar
      titlestr = ['no3, mmoles m-3; month = ',num2str(m)];
      title(titlestr);

      subplot(2,2,3);
      scatter3(lon_mod_runoff_vec,lat_mod_runoff_vec,nh4_mod_monthly_vecs(m,:),ms_vec, ...
               nh4_mod_monthly_vecs(m,:),'filled');
      hold on
      view(2);
      caxis([0 20]);
      colorbar
      titlestr = ['nh4, mmoles m-3; month = ',num2str(m)];
      title(titlestr);

      subplot(2,2,4);
      no3_din_ratio = no3_mod_monthly_vecs(m,:)./din_mod_monthly_vecs(m,:);
      scatter3(lon_mod_runoff_vec,lat_mod_runoff_vec,no3_din_ratio, ...
          ms_vec,no3_din_ratio,'filled');
      hold on
      view(2);
      caxis([0 1.0]);
      colorbar
      title('NO3:DIN ratio');

      %pause
    end

    for m = 1:12

      subplot(2,3,1);
      scatter3(lon_mod_runoff_vec,lat_mod_runoff_vec,din_mod_monthly_vecs(m,:),ms_vec, ...
               din_mod_monthly_vecs(m,:),'filled');
      hold on
      view(2);
      caxis([0 100]);
      colorbar
      titlestr = ['DIN, mmoles m-3; month = ',num2str(m)];
      title(titlestr);

      subplot(2,3,2);
      scatter3(lon_mod_runoff_vec,lat_mod_runoff_vec,don_mod_monthly_vecs(m,:),ms_vec, ...
               don_mod_monthly_vecs(m,:),'filled');
      hold on
      view(2);
      caxis([0 100]);
      colorbar
      titlestr = ['DON, mmoles m-3; month = ',num2str(m)];
      title(titlestr);

      subplot(2,3,3);
      scatter3(lon_mod_runoff_vec,lat_mod_runoff_vec,pn_mod_monthly_vecs(m,:),ms_vec, ...
         pn_mod_monthly_vecs(m,:),'filled');
      hold on
      view(2);
      caxis([0 100]);
      colorbar
      titlestr = ['PN, mmoles m-3; month = ',num2str(m)];
      title(titlestr);

      subplot(2,3,5)
      don_din_ratio = don_mod_monthly_vecs(m,:)./din_mod_monthly_vecs(m,:);
      scatter3(lon_mod_runoff_vec,lat_mod_runoff_vec,don_din_ratio, ...
          ms_vec,don_din_ratio,'filled');
      hold on
      view(2);
      caxis([0 2]);
      colorbar
      title('DON:DIN ratio');

      subplot(2,3,6)
      pn_din_ratio = pn_mod_monthly_vecs(m,:)./din_mod_monthly_vecs(m,:);
      scatter3(lon_mod_runoff_vec,lat_mod_runoff_vec,pn_din_ratio, ...
          ms_vec,pn_din_ratio,'filled');
      hold on
      view(2);
      caxis([0 2]);
      colorbar
      title('PN:DIN ratio');

      %pause
    end

    % Phosphorus Concentrations
    for m = 1:12

      figure(1)
      clf

      subplot(2,3,1);
      scatter3(lon_mod_runoff_vec,lat_mod_runoff_vec,dip_mod_monthly_vecs(m,:),ms_vec, ...
               dip_mod_monthly_vecs(m,:),'filled');
      hold on
      view(2);
      caxis([0 3]);
      colorbar
      titlestr = ['DIP, mmoles m-3; month = ',num2str(m)];
      title(titlestr);

      subplot(2,3,2);
      scatter3(lon_mod_runoff_vec,lat_mod_runoff_vec,dop_mod_monthly_vecs(m,:),ms_vec, ...
               dop_mod_monthly_vecs(m,:),'filled');
      hold on
      view(2);
      caxis([0 3]);
      colorbar
      titlestr = ['DOP, mmoles m-3; month = ',num2str(m)];
      title(titlestr);

      subplot(2,3,3);
      scatter3(lon_mod_runoff_vec,lat_mod_runoff_vec,pp_mod_monthly_vecs(m,:),ms_vec, ...
         pp_mod_monthly_vecs(m,:),'filled');
      hold on
      view(2);
      caxis([0 3]);
      colorbar
      titlestr = ['PP, mmoles m-3; month = ',num2str(m)];
      title(titlestr);

      subplot(2,3,5)
      dop_dip_ratio = dop_mod_monthly_vecs(m,:)./dip_mod_monthly_vecs(m,:);
      scatter3(lon_mod_runoff_vec,lat_mod_runoff_vec,dop_dip_ratio, ...
          ms_vec,dop_dip_ratio,'filled');
      hold on
      view(2);
      caxis([0 3]);
      colorbar
      title('DOP:DIP ratio');

      subplot(2,3,6)
      pp_dip_ratio = pp_mod_monthly_vecs(m,:)./dip_mod_monthly_vecs(m,:);
      scatter3(lon_mod_runoff_vec,lat_mod_runoff_vec,pp_dip_ratio, ...
          ms_vec,pp_dip_ratio,'filled');
      hold on
      view(2);
      caxis([0 2]);
      colorbar
      title('PP:DIP ratio');

      %pause
    end

    % silica and oxygen concentrations
    for m = 1:12
      figure(1)
      clf

      subplot(2,1,1);
      scatter3(lon_mod_runoff_vec,lat_mod_runoff_vec,si_mod_monthly_vecs(m,:),ms_vec, ...
               si_mod_monthly_vecs(m,:),'filled');
      hold on
      view(2);
      caxis([0 200]);
      colorbar
      titlestr = ['Si, mmoles m-3; month = ',num2str(m)];
      title(titlestr);

      subplot(2,1,2);
      scatter3(lon_mod_runoff_vec,lat_mod_runoff_vec,o2_mod_monthly_vecs(m,:),ms_vec, ...
               o2_mod_monthly_vecs(m,:),'filled');
      hold on
      view(2);
      caxis([0 350]);
      colorbar
      titlestr = ['o2, mmoles m-3; month = ',num2str(m)];
      title(titlestr);

      %pause
    end

end

% Initialize 2D concentration arrays; these are the ones read into MOM6 to
% specify the nutrient concentrations of river inputs.
DIC_CONC = zeros(12,size(lon_mod,1),size(lon_mod,2));
ALK_CONC = zeros(12,size(lon_mod,1),size(lon_mod,2));
NO3_CONC = zeros(12,size(lon_mod,1),size(lon_mod,2));
NH4_CONC = zeros(12,size(lon_mod,1),size(lon_mod,2));
LDON_CONC = zeros(12,size(lon_mod,1),size(lon_mod,2));
SLDON_CONC = zeros(12,size(lon_mod,1),size(lon_mod,2));
SRDON_CONC = zeros(12,size(lon_mod,1),size(lon_mod,2));
PO4_CONC = zeros(12,size(lon_mod,1),size(lon_mod,2));
LDOP_CONC = zeros(12,size(lon_mod,1),size(lon_mod,2));
SLDOP_CONC = zeros(12,size(lon_mod,1),size(lon_mod,2));
SRDOP_CONC = zeros(12,size(lon_mod,1),size(lon_mod,2));
NDET_CONC = zeros(12,size(lon_mod,1),size(lon_mod,2));
PDET_CONC = zeros(12,size(lon_mod,1),size(lon_mod,2));
SI_CONC = zeros(12,size(lon_mod,1),size(lon_mod,2));
O2_CONC = zeros(12,size(lon_mod,1),size(lon_mod,2));

% Map concentration vectors onto 2D arrays
temp = zeros(size(lon_mod));
for m = 1:12
  temp(ind_ro) = dic_mod_monthly_vecs(m,:);
  DIC_CONC(m,:,:) = temp;
  temp(ind_ro) = alk_mod_monthly_vecs(m,:);
  ALK_CONC(m,:,:) = temp;
  
  temp(ind_ro) = no3_mod_monthly_vecs(m,:);   % contains all NEWS DIN
  %temp(ind_ro) = din_mod_monthly_vecs(m,:);
  NO3_CONC(m,:,:) = temp;
  temp(ind_ro) = nh4_mod_monthly_vecs(m,:);
  NH4_CONC(m,:,:) = temp;
  temp(ind_ro) = don_mod_monthly_vecs(m,:);
  LDON_CONC(m,:,:) = frac_ldon*temp;
  SLDON_CONC(m,:,:) = frac_sldon*temp;
  SRDON_CONC(m,:,:) = frac_srdon*temp;
  temp(ind_ro) = pn_mod_monthly_vecs(m,:);
  NDET_CONC(m,:,:) = temp;
  
  temp(ind_ro) = dip_mod_monthly_vecs(m,:);
  PO4_CONC(m,:,:) = temp;
  temp(ind_ro) = dop_mod_monthly_vecs(m,:);
  LDOP_CONC(m,:,:) = frac_ldop*temp;
  SLDOP_CONC(m,:,:) = frac_sldop*temp;
  SRDOP_CONC(m,:,:) = frac_srdop*temp;
  temp(ind_ro) = pp_mod_monthly_vecs(m,:);
  PDET_CONC(m,:,:) = temp;
  
  temp(ind_ro) = si_mod_monthly_vecs(m,:);
  SI_CONC(m,:,:) = temp;
  temp(ind_ro) = o2_mod_monthly_vecs(m,:);
  O2_CONC(m,:,:) = temp;
end

% MOM6 is taking river values in moles m-3 for other constituents.  Change 
% for consistency across river constituents
DIC_CONC = DIC_CONC./1e3;
ALK_CONC = ALK_CONC./1e3;
NO3_CONC = NO3_CONC./1e3;
NH4_CONC = NH4_CONC./1e3;
LDON_CONC = LDON_CONC./1e3;
SLDON_CONC = SLDON_CONC./1e3;
SRDON_CONC = SRDON_CONC./1e3;
NDET_CONC = NDET_CONC./1e3;
PO4_CONC = PO4_CONC./1e3;
LDOP_CONC = LDOP_CONC./1e3;
SLDOP_CONC = SLDOP_CONC./1e3;
SRDOP_CONC = SRDOP_CONC./1e3;
PDET_CONC = PDET_CONC./1e3;
SI_CONC = SI_CONC./1e3;
O2_CONC = O2_CONC./1e3;

% Add iron concentrations - initialize with nitrate and then overwrite
FED_CONC = NO3_CONC;
FEDET_CONC = NO3_CONC;
% 40 nM dissolved iron concentration from De Baar and De Jong + 30nM 
% Colloidal and nanoparticle flux as reported in Canfield and Raiswell
FED_CONC(FED_CONC > 0) = const_fed;
FEDET_CONC(FEDET_CONC > 0) = 0.0;

ms = 8;

if plot_progress
    % quick set of plots to ensure the mapping to the model grid was successful
    for m = 1:12
      % DIC and alkalinity
      figure(1)
      clf
      subplot(2,1,1);
      title('log10(DIC CONC)'); hold on; 
      scatter3(lon_mod(:),lat_mod(:),log10(DIC_CONC(m,:)),ms,log10(DIC_CONC(m,:)),'filled'); 
      caxis([-1 1]); colorbar;

      subplot(2,1,2);
      title('log10(ALK CONC)'); hold on; 
      scatter3(lon_mod(:),lat_mod(:),log10(ALK_CONC(m,:)),ms,log10(ALK_CONC(m,:)),'filled'); 
      caxis([-1 1]); colorbar;

      %pause
    end

    % Nitrogen
    for m = 1:12
      figure(1);
      clf
      subplot(3,2,1);
      title('log10(NO3 CONC)'); hold on; 
      scatter3(lon_mod(:),lat_mod(:),log10(NO3_CONC(m,:)),ms,log10(NO3_CONC(m,:)),'filled'); 
      caxis([-4 -1]); colorbar;

      subplot(3,2,2);
      title('log10(NH4 CONC)'); hold on; 
      scatter3(lon_mod(:),lat_mod(:),log10(NH4_CONC(m,:)),ms,log10(NH4_CONC(m,:)),'filled'); 
      caxis([-4 -1]); colorbar;

      subplot(3,2,3);
      title('log10(LDON CONC)'); hold on; 
      scatter3(lon_mod(:),lat_mod(:),log10(LDON_CONC(m,:)),ms,log10(LDON_CONC(m,:)),'filled'); 
      caxis([-4 -1]); colorbar;

      subplot(3,2,4);
      title('log10(SLDON CONC)'); hold on; 
      scatter3(lon_mod(:),lat_mod(:),log10(SLDON_CONC(m,:)),ms,log10(SLDON_CONC(m,:)),'filled'); 
      caxis([-4 -1]); colorbar;

      subplot(3,2,5);
      title('log10(SRDON CONC)'); hold on; 
      scatter3(lon_mod(:),lat_mod(:),log10(SRDON_CONC(m,:)),ms,log10(SRDON_CONC(m,:)),'filled'); 
      caxis([-4 -1]); colorbar;

      subplot(3,2,6);
      title('log10(NDET CONC)'); hold on; 
      scatter3(lon_mod(:),lat_mod(:),log10(NDET_CONC(m,:)),ms,log10(NDET_CONC(m,:)),'filled'); 
      caxis([-4 -1]); colorbar;

      %pause
    end

    % Phosphorus
    for m = 1:12
      figure(1);
      clf
      subplot(3,2,1);
      title('log10(PO4 CONC)'); hold on; 
      scatter3(lon_mod(:),lat_mod(:),log10(PO4_CONC(m,:)),ms,log10(PO4_CONC(m,:)),'filled'); 
      caxis([-4 -2]); colorbar;

      subplot(3,2,2);
      title('log10(LDOP CONC)'); hold on; 
      scatter3(lon_mod(:),lat_mod(:),log10(LDOP_CONC(m,:)),ms,log10(LDOP_CONC(m,:)),'filled'); 
      caxis([-4 -2]); colorbar;

      subplot(3,2,3);
      title('log10(SLDOP CONC)'); hold on; 
      scatter3(lon_mod(:),lat_mod(:),log10(SLDOP_CONC(m,:)),ms,log10(SLDOP_CONC(m,:)),'filled'); 
      caxis([-4 -2]); colorbar;

      subplot(3,2,4);
      title('log10(SRDOP CONC)'); hold on; 
      scatter3(lon_mod(:),lat_mod(:),log10(SRDOP_CONC(m,:)),ms,log10(SRDOP_CONC(m,:)),'filled'); 
      caxis([-4 -2]); colorbar;

      subplot(3,2,5);
      title('log10(PDET CONC)'); hold on; 
      scatter3(lon_mod(:),lat_mod(:),log10(PDET_CONC(m,:)),ms,log10(PDET_CONC(m,:)),'filled'); 
      caxis([-4 -2]); colorbar;

      %pause;
    end

    % Iron, Silica, Oxygen
    for m = 1:12
      figure(1)
      clf
      subplot(3,2,1);
      title('log10(FED CONC)'); hold on; 
      scatter3(lon_mod(:),lat_mod(:),log10(FED_CONC(m,:)),ms,log10(FED_CONC(m,:)),'filled'); 
      caxis([-5 -3]); colorbar;

      subplot(3,2,2);
      title('log10(FEDET CONC)'); hold on; 
      scatter3(lon_mod(:),lat_mod(:),log10(FEDET_CONC(m,:)),ms,log10(FEDET_CONC(m,:)),'filled'); 
      caxis([-5 -3]); colorbar;

      subplot(3,2,3);
      title('log10(SI CONC)'); hold on; 
      scatter3(lon_mod(:),lat_mod(:),log10(SI_CONC(m,:)),ms,log10(SI_CONC(m,:)),'filled'); 
      caxis([-3 0]); colorbar;

      subplot(3,2,4);
      title('log10(O2 CONC)'); hold on; 
      scatter3(lon_mod(:),lat_mod(:),log10(O2_CONC(m,:)),ms,log10(O2_CONC(m,:)),'filled'); 
      caxis([-3 0]); colorbar;

      %pause;
    end
end

%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%
% Save Files                                                              %
%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%
% option to save matlab file
% save River_DIC_ALK_RC4US_NWA ALK_CONC DIC_CONC

% Construct netcdf file following format used by nutrient input files to
% MOM6

% Make reference dates for standard non-leap year
dates = [1990 1 16 12 0 0; 1990 2 15 0 0 0; 1990 3 16 12 0 0; ...
         1990 4 16 0 0 0; 1990 5 16 12 0 0; 1990 6 16 0 0 0; ...
         1990 7 16 12 0 0; 1990 8 16 12 0 0; 1990 9 16 0 0 0; ...
         1990 10 16 12 0 0; 1990 11 16 0 0 0; 1990 12 16 12 0 0];
time = datenum(dates) - datenum([1990 1 1 0 0 0]);

nlat = size(lat_mod,1);
nlon = size(lat_mod,2);

ncid = netcdf.create(nc_file_name,'CLOBBER');
dimid0 = netcdf.defDim(ncid,'time',netcdf.getConstant('NC_UNLIMITED'));
dimid1 = netcdf.defDim(ncid,'y',nlat);
dimid2 = netcdf.defDim(ncid,'x',nlon);

varid0 = netcdf.defVar(ncid,'time','double',dimid0);
netcdf.putAtt(ncid,varid0,'calendar','NOLEAP');
netcdf.putAtt(ncid,varid0,'calendar_type','NOLEAP');
netcdf.putAtt(ncid,varid0,'modulo','T');
netcdf.putAtt(ncid,varid0,'units','days since 1990-1-1 0:00:00');
netcdf.putAtt(ncid,varid0,'time_origin','01-JAN-1990 00:00:00');
varid1 = netcdf.defVar(ncid,'y','int',dimid1);
netcdf.putAtt(ncid,varid1,'cartesian_axis','Y');
varid2 = netcdf.defVar(ncid,'x','int',dimid2);
netcdf.putAtt(ncid,varid2,'cartesian_axis','X');
varid3 = netcdf.defVar(ncid,'lat','double',[dimid2 dimid1]);
netcdf.putAtt(ncid,varid3,'units','degrees north');
varid4 = netcdf.defVar(ncid,'lon','double',[dimid2 dimid1]);
netcdf.putAtt(ncid,varid4,'units','degrees east');
varid5 = netcdf.defVar(ncid,'DIC_CONC','double',[dimid2,dimid1,dimid0]);
netcdf.putAtt(ncid,varid5,'units','mol m-3');
netcdf.putAtt(ncid,varid5,'long_name','DIC_CONC');
varid6 = netcdf.defVar(ncid,'ALK_CONC','double',[dimid2,dimid1,dimid0]);
netcdf.putAtt(ncid,varid6,'units','mole Eq. m-3');
netcdf.putAtt(ncid,varid6,'long_name','ALK_CONC');
varid7 = netcdf.defVar(ncid,'NO3_CONC','double',[dimid2,dimid1,dimid0]);
netcdf.putAtt(ncid,varid7,'units','mol m-3');
netcdf.putAtt(ncid,varid7,'long_name','NO3_CONC');
varid8 = netcdf.defVar(ncid,'NH4_CONC','double',[dimid2,dimid1,dimid0]);
netcdf.putAtt(ncid,varid8,'units','mol m-3');
netcdf.putAtt(ncid,varid8,'long_name','NH4_CONC');
varid9 = netcdf.defVar(ncid,'LDON_CONC','double',[dimid2,dimid1,dimid0]);
netcdf.putAtt(ncid,varid9,'units','mol m-3');
netcdf.putAtt(ncid,varid9,'long_name','0.3*DON_CONC');
varid10 = netcdf.defVar(ncid,'SLDON_CONC','double',[dimid2,dimid1,dimid0]);
netcdf.putAtt(ncid,varid10,'units','mol m-3');
netcdf.putAtt(ncid,varid10,'long_name','0.35*DON_CONC');
varid11 = netcdf.defVar(ncid,'SRDON_CONC','double',[dimid2,dimid1,dimid0]);
netcdf.putAtt(ncid,varid11,'units','mol m-3');
netcdf.putAtt(ncid,varid11,'long_name','0.35*DON_CONC');
varid12 = netcdf.defVar(ncid,'NDET_CONC','double',[dimid2,dimid1,dimid0]);
netcdf.putAtt(ncid,varid12,'units','mol m-3');
netcdf.putAtt(ncid,varid12,'long_name','1.0*PN_CONC');
varid13 = netcdf.defVar(ncid,'PO4_CONC','double',[dimid2,dimid1,dimid0]);
netcdf.putAtt(ncid,varid13,'units','mol m-3');
netcdf.putAtt(ncid,varid13,'long_name','PO4_CONC+0.3*PP_CONC');
varid14 = netcdf.defVar(ncid,'LDOP_CONC','double',[dimid2,dimid1,dimid0]);
netcdf.putAtt(ncid,varid14,'units','mol m-3');
netcdf.putAtt(ncid,varid14,'long_name','0.3*DOP_CONC');
varid15 = netcdf.defVar(ncid,'SLDOP_CONC','double',[dimid2,dimid1,dimid0]);
netcdf.putAtt(ncid,varid15,'units','mol m-3');
netcdf.putAtt(ncid,varid15,'long_name','0.35*DOP_CONC');
varid16 = netcdf.defVar(ncid,'SRDOP_CONC','double',[dimid2,dimid1,dimid0]);
netcdf.putAtt(ncid,varid16,'units','mol m-3');
netcdf.putAtt(ncid,varid16,'long_name','0.35*DOP_CONC');
varid17 = netcdf.defVar(ncid,'PDET_CONC','double',[dimid2,dimid1,dimid0]);
netcdf.putAtt(ncid,varid17,'units','mol m-3');
netcdf.putAtt(ncid,varid17,'long_name','0*PP_CONC');
varid18 = netcdf.defVar(ncid,'FED_CONC','double',[dimid2,dimid1,dimid0]);
netcdf.putAtt(ncid,varid18,'units','mol m-3');
netcdf.putAtt(ncid,varid18,'long_name','FED_CONC');
varid19 = netcdf.defVar(ncid,'FEDET_CONC','double',[dimid2,dimid1,dimid0]);
netcdf.putAtt(ncid,varid19,'units','mol m-3');
netcdf.putAtt(ncid,varid19,'long_name','FEDET_CONC');
varid20 = netcdf.defVar(ncid,'O2_CONC','double',[dimid2,dimid1,dimid0]);
netcdf.putAtt(ncid,varid20,'units','mol m-3');
netcdf.putAtt(ncid,varid20,'long_name','O2_CONC');
varid21 = netcdf.defVar(ncid,'SI_CONC','double',[dimid2,dimid1,dimid0]);
netcdf.putAtt(ncid,varid21,'units','mol m-3');
netcdf.putAtt(ncid,varid21,'long_name','SI_CONC');
netcdf.close(ncid)

ncid = netcdf.open(nc_file_name,'NC_WRITE');
netcdf.putVar(ncid,varid0,0,12,time);
% nutrient input files appear seem to need dummy axes to be read in
% properly, but eventually do a grid by grid mapping that doesn't require
% these.
netcdf.putVar(ncid,varid1,1:nlat);
netcdf.putVar(ncid,varid2,1:nlon);
netcdf.putVar(ncid,varid3,permute(lat_mod,[2,1]));
netcdf.putVar(ncid,varid4,permute(lon_mod,[2,1]));
netcdf.putVar(ncid,varid5,permute(DIC_CONC,[3,2,1]));
netcdf.putVar(ncid,varid6,permute(ALK_CONC,[3,2,1]));
netcdf.putVar(ncid,varid7,permute(NO3_CONC,[3,2,1]));
netcdf.putVar(ncid,varid8,permute(NH4_CONC,[3,2,1]));
netcdf.putVar(ncid,varid9,permute(LDON_CONC,[3,2,1]));
netcdf.putVar(ncid,varid10,permute(SLDON_CONC,[3,2,1]));
netcdf.putVar(ncid,varid11,permute(SRDON_CONC,[3,2,1]));
netcdf.putVar(ncid,varid12,permute(NDET_CONC,[3,2,1]));
netcdf.putVar(ncid,varid13,permute(PO4_CONC,[3,2,1]));
netcdf.putVar(ncid,varid14,permute(LDOP_CONC,[3,2,1]));
netcdf.putVar(ncid,varid15,permute(SLDOP_CONC,[3,2,1]));
netcdf.putVar(ncid,varid16,permute(SRDOP_CONC,[3,2,1]));
netcdf.putVar(ncid,varid17,permute(PDET_CONC,[3,2,1]));
netcdf.putVar(ncid,varid18,permute(FED_CONC,[3,2,1]));
netcdf.putVar(ncid,varid19,permute(FEDET_CONC,[3,2,1]));
netcdf.putVar(ncid,varid20,permute(O2_CONC,[3,2,1]));
netcdf.putVar(ncid,varid21,permute(SI_CONC,[3,2,1]));
netcdf.close(ncid)
