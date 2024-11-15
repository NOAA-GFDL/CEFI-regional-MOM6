% Routine to map Global NEWS nutrient data onto the MOM6 NWA grid 
% Run in matlab97

clear all;
nc64startup;

% name of netcdf file to be created
nc_file_name = './RiverNutrients_GlobalNEWS2_plusFe_Q100_GLOFAS_NWA12.nc';

% Parameters for the assignment algorithm.
Q_min = 100; % minimum flow in m3 sec
plot_width = 3; % width of window (in degrees) for inspecting locations
                 % of rivers and outflow points that have been assigned to
                 % them.
min_dist = 2;  % minimum distance (degrees) of the closest outflow point
                 % for the river to be considered in the domain (useful
                 % for preventing the algorithm from trying to map rivers
                 % flowing to different ocean basins.
inspect_map = 'n'; % flag enabling you to pause and inspect each river
                   % mapping as it is being done.
                 
% set the bio-availability of phosphorus and the fractionation of dissolved
% organic; PP is set to 30% based on Froelich; Partitioning of detritus
% between
frac_PP = 0.3;
frac_ldon = 0.3;
frac_sldon = 0.35;
frac_srdon = 0.35;
frac_ldop = 0.3;
frac_sldop = 0.35;
frac_srdop = 0.35;
% 40 nM dissolved iron concentration from De Baar and De Jong + 30nM 
% Colloidal and nanoparticle flux as reported in Canfield and Raiswell
const_fed = 70.0e-6;

% GlobalNEWS2 data obtained from Emilio Mayorga
filename = 'GlobalNEWS2_RH2000Dataset-version1.0.xls';
basin = readtable(filename,'Sheet',2);
hydrology = readtable(filename,'Sheet',3);
loading = readtable(filename,'Sheet',4);

% find all the river basins that empty into "land", e.g., lakes
ocean = basin.ocean;
land_index = zeros(size(ocean));
for n = 1:size(ocean,1);
    test = strcmp('Land',ocean(n));
    land_index(n) = single(test);
end

river_names_all = basin.basinname;

% basin area in 
area = basin.A;
lon_news_all = basin.mouth_lon;
lat_news_all = basin.mouth_lat;
%lon_news_all(lon_news_all < 0) = lon_news_all(lon_news_all < 0) + 360;

% Loads in Mg yr-1 converted to moles per sec
DIN_load_all = loading.Ld_DIN*1e6/14/86400/365;
DIP_load_all = loading.Ld_DIP*1e6/31/86400/365;
DON_load_all = loading.Ld_DON*1e6/14/86400/365;
DOP_load_all = loading.Ld_DOP*1e6/31/86400/365;
Si_load_all = loading.Ld_DSi*1e6/28.1/86400/365;
PN_load_all = (loading.Ld_PN*1e6/14/86400/365);
PP_load_all = (loading.Ld_PP*1e6/31/86400/365)*frac_PP;

% actual and natural discharge (convert from km3/yr to m3/sec)
% Used the actual hydrology to calculate concentrations
Qact_all = hydrology.Qact*1e9/(86400*365);
Qnat_all = hydrology.Qnat*1e9/(86400*365);

%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%
% Load in monthly climatology of river forcing from the regional grid.    %
% File contains:                                                          %
% runoff: monthly average runoff in kg m-2 sec-1                          %
% area_mod: area of grid cell in m-2                                          %
% lon_mod: longitude (0-360 degrees)                                          %
% lat_mod: latitude                                                           %
%                                                                         %
% The file was calculated from daily output using the routine             %
% "make_climatology.m".  This routine and all associated files can be     %
% found in the same directory as the data file                            %
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

in_region = find( (lon_news_all <= lon_mod_max) & (lon_news_all >= lon_mod_min) & ...
    (lat_news_all <= lat_mod_max) & (lat_news_all >= lat_mod_min) & ...
    (isfinite(Qact_all)) & (Qact_all > Q_min) );

% If you are using a high threshold, grab one smaller river to constrain
% Carribean Islands
if Q_min > 100
  for n = 1:size(lon_news_all,1);
    test = strcmp('GHAASBasin1808',river_names_all{n});
    if test == 1;
        cuba_ind = n;
    end
  end
  
  in_region = [in_region; cuba_ind];
end

num_rivers = size(in_region,1);
    
% Establish vectors of flow and nutrient loads for the NWA
Qact = Qact_all(in_region);
lon_news = lon_news_all(in_region);
lat_news = lat_news_all(in_region);
DIN_load = DIN_load_all(in_region);
DON_load = DON_load_all(in_region);
PN_load = PN_load_all(in_region);
DIP_load = DIP_load_all(in_region);
DOP_load = DOP_load_all(in_region);
PP_load = PP_load_all(in_region);
Si_load = Si_load_all(in_region);
river_names = river_names_all(in_region);

%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%
% Following inspection of initial mapping, add any manual edits here to   %
% prevent anomalous extrapolations, etc.                                  %
%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%

 %Add in 2 "dummy" rivers to handle Cuba, giving it properties like 
 %Jamaica or Haiti rather than Florida. 

 %GHAASBasin1808 is in Haiti.  Fluxes are characterized by particularly
 %high particulate phosphorus inputs.
for n = 1:num_rivers;
%    n
%    test = strcmp('GHAASBasin1808',river_names{n})
%    if test == 1;
%        cuba_ind = n;
%    end
    
    % Move the Susquehanna a bit south so that it catches the Chesapeake
    % and not the Delaware.
    if strcmp('Susquehanna',river_names{n})
        lat_news(n) = 38.5;
        lon_news(n) = -76.67;
    end
end

% Two "rivers" with properties like Haiti used to specify Cuba
%Qact(num_rivers+1) = Qact(cuba_ind)/2;  
%lon_news(num_rivers+1) = -81;
%lat_news(num_rivers+1) = 22.6;
%DIN_load(num_rivers+1) = DIN_load(cuba_ind)/2;
%DON_load(num_rivers+1) = DON_load(cuba_ind)/2;
%PN_load(num_rivers+1) = PN_load(cuba_ind)/2;
%DIP_load(num_rivers+1) = DIP_load(cuba_ind)/2;
%DOP_load(num_rivers+1) = DOP_load(cuba_ind)/2;
%PP_load(num_rivers+1) = PP_load(cuba_ind)/2;
%Si_load(num_rivers+1) = Si_load(cuba_ind)/2;
%river_names(num_rivers+1) = river_names(cuba_ind);

%Qact(num_rivers+2) = Qact(cuba_ind)/2;  
%lon_news(num_rivers+2) = -83.25;
%lat_news(num_rivers+2) = 22.6;
%DIN_load(num_rivers+2) = DIN_load(cuba_ind)/2;
%DON_load(num_rivers+2) = DON_load(cuba_ind)/2;
%PN_load(num_rivers+2) = PN_load(cuba_ind)/2;
%DIP_load(num_rivers+2) = DIP_load(cuba_ind)/2;
%DOP_load(num_rivers+2) = DOP_load(cuba_ind)/2;
%PP_load(num_rivers+2) = PP_load(cuba_ind)/2;
%Si_load(num_rivers+2) = Si_load(cuba_ind)/2;
%river_names(num_rivers+2) = river_names(cuba_ind);

%num_rivers = num_rivers + 1;

% Adjust location of closest Florida basin to avoid extrapolation to 
% Cuba; This has little effect on patterns in Florida.
%for n = 1:num_rivers;
%    n
%    test = strcmp('GHAASBasin448',river_names{n})
%    if test == 1;
%        fla_ind = n;
%    end
%end

%lon_news(fla_ind) = -80.5;
%lat_news(fla_ind) = 26.6;

%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%
% END MANUAL EDITS                                                        %
%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%

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
[Qact_sort,sort_ind] = sort(Qact,'ascend');
lon_news_sort = lon_news(sort_ind);
lat_news_sort = lat_news(sort_ind);
DIN_load_sort = DIN_load(sort_ind);
DON_load_sort = DON_load(sort_ind);
PN_load_sort = PN_load(sort_ind);
DIP_load_sort = DIP_load(sort_ind);
DOP_load_sort = DOP_load(sort_ind);
PP_load_sort = PP_load(sort_ind);
Si_load_sort = Si_load(sort_ind);
river_names_sort = river_names(sort_ind);

% Total N and P load diagnostics
N_load_sort = DIN_load_sort + DON_load_sort + PN_load_sort;
P_load_sort = DIP_load_sort + DOP_load_sort + PP_load_sort;

% Calculate concentrations
% Loads are in moles N sec-1, Q in m3 s-1; conc in moles N m-3
DIN_conc_sort = DIN_load_sort./Qact_sort;
DON_conc_sort = DON_load_sort./Qact_sort;
DIP_conc_sort = DIP_load_sort./Qact_sort;
DOP_conc_sort = DOP_load_sort./Qact_sort;
PN_conc_sort = PN_load_sort./Qact_sort;
PP_conc_sort = PP_load_sort./Qact_sort;
Si_conc_sort = Si_load_sort./Qact_sort;

% initialize vectors to hold nutrient concentrations at eac runoff
% point.
aa = find(Q_mod_ann > 0);
Q_mod_vec = Q_mod_ann(aa);
din_conc_vec = zeros(size(Q_mod_vec));
don_conc_vec = zeros(size(Q_mod_vec));
pn_conc_vec = zeros(size(Q_mod_vec));
dip_conc_vec = zeros(size(Q_mod_vec));
dop_conc_vec = zeros(size(Q_mod_vec));
pp_conc_vec = zeros(size(Q_mod_vec));
si_conc_vec = zeros(size(Q_mod_vec));

lon_mod_runoff_vec = lon_mod(aa);
lat_mod_runoff_vec = lat_mod(aa);

%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%
% Loop identifies points assigned to each river                           %
%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%
for k=1:num_rivers
    k
    dist = pdist2([lon_news_sort(k) lat_news_sort(k)], ...
        [lon_mod_runoff_vec lat_mod_runoff_vec]);
    [dist_sort, dist_sort_ind] = sort(dist,'ascend');
    
    if dist_sort(1) < min_dist;  % filters out rivers lying outside the domain
      Q_sum1 = 0;
      Q_sum2 = 0;
      n = 0;
      while Q_sum2 < Qact_sort(k)
        Q_sum1 = Q_sum2;
        n = n+1;
        Q_sum2 = Q_sum1 + Q_mod_vec(dist_sort_ind(n));
      end
      if abs(Q_sum1 - Qact_sort(k)) < abs(Q_sum2 - Qact_sort(k))
        nrp = n-1;  % number of runoff points
        [Q_sum1 Qact_sort(k)]  % a quick check for comparable flow
        din_conc_vec(dist_sort_ind(1:nrp)) = DIN_conc_sort(k);
        don_conc_vec(dist_sort_ind(1:nrp)) = DON_conc_sort(k);
        dip_conc_vec(dist_sort_ind(1:nrp)) = DIP_conc_sort(k);
        dop_conc_vec(dist_sort_ind(1:nrp)) = DOP_conc_sort(k);
        pn_conc_vec(dist_sort_ind(1:nrp)) = PN_conc_sort(k);
        pp_conc_vec(dist_sort_ind(1:nrp)) = PP_conc_sort(k);
        si_conc_vec(dist_sort_ind(1:nrp)) = Si_conc_sort(k);
      else
        nrp = n; % number of runoff points
        [Q_sum2 Qact_sort(k)] % a quick check for comparable flow
        din_conc_vec(dist_sort_ind(1:nrp)) = DIN_conc_sort(k);
        don_conc_vec(dist_sort_ind(1:nrp)) = DON_conc_sort(k);
        dip_conc_vec(dist_sort_ind(1:nrp)) = DIP_conc_sort(k);
        dop_conc_vec(dist_sort_ind(1:nrp)) = DOP_conc_sort(k);
        pn_conc_vec(dist_sort_ind(1:nrp)) = PN_conc_sort(k);
        pp_conc_vec(dist_sort_ind(1:nrp)) = PP_conc_sort(k);
        si_conc_vec(dist_sort_ind(1:nrp)) = Si_conc_sort(k);
      end
        
      if inspect_map == 'y'
        figure(1)
        clf
        scatter3(lon_mod_runoff_vec,lat_mod_runoff_vec,log10(Q_mod_vec),3,log10(Q_mod_vec));
        hold on
        scatter3(lon_mod_runoff_vec(dist_sort_ind(1:nrp)),lat_mod_runoff_vec(dist_sort_ind(1:nrp)), ...
          log10(Q_mod_vec(dist_sort_ind(1:nrp))),40, ...
          log10(Q_mod_vec(dist_sort_ind(1:nrp))),'filled');
        view(2);
        plot3(lon_news_sort(k),lat_news_sort(k),1e5,'k.','MarkerSize',20);
        contour(lon_mod,lat_mod,depth,[0 0],'k-');
        axis([lon_news_sort(k)-plot_width lon_news_sort(k)+plot_width ...
          lat_news_sort(k)-plot_width lat_news_sort(k)+plot_width]);
        caxis([-4 3]);
        titl = ['river number: ',num2str(k),' name: ',river_names_sort{k}];
        title(titl);
        colorbar;

        % provide a few diagnostics to ensure the calculation was done
        % correctly (remove semicolon to inspect as they are mapped) 
        N_conc = DIN_conc_sort(k) + DON_conc_sort(k) + PN_conc_sort(k);
        P_conc = DIP_conc_sort(k) + DOP_conc_sort(k) + PP_conc_sort(k);
        Si_conc = Si_conc_sort(k);
        river_names_sort(k)
        [lon_news_sort(k) lat_news_sort(k)]
        ind = dist_sort_ind(1:nrp);
        'total flow in m3 sec'
        [Qact_sort(k) sum(Q_mod_vec(ind))]
        'Nitrogen and phosphorus in Gg per year';
        [N_load_sort(k) sum(Q_mod_vec(ind))*N_conc]*14*86400*365/1e9;
        [P_load_sort(k) sum(Q_mod_vec(ind))*P_conc]*31*86400*365/1e9;
        'N, P conc (mmoles m-3), DI, DO, P'
        [DIN_conc_sort(k) DON_conc_sort(k) PN_conc_sort(k)]*1e3
        [DIP_conc_sort(k) DOP_conc_sort(k) PP_conc_sort(k)]*1e3
        'Total N, Total P, Total N: Total P';
        [N_conc*1e3 P_conc*1e3 N_conc/P_conc];
        'DO:DI and P:DI ratios';
        [DON_conc_sort(k)/DIN_conc_sort(k) PN_conc_sort(k)/DIN_conc_sort(k)];
        [DOP_conc_sort(k)/DIP_conc_sort(k) PP_conc_sort(k)/DIP_conc_sort(k)];
        'silica concentration (mmoles m-3)';
        [Si_conc_sort(k)]*1e3
        pause
      end
      
    else
      % This is for rivers that were captured by the coarse initial filter
      % to determine if they were in the domain; but are actually outside
      % the domain.  Calibration suggested that a threshold of 0.75 degrees
      % from the specified river mouth reliably identified these cases.
      
      if inspect_map == 'y'
        figure(1)
        clf
        scatter3(lon_mod_runoff_vec,lat_mod_runoff_vec,log10(Q_mod_vec),3,log10(Q_mod_vec));
        hold on
        view(2);
        plot3(lon_news_sort(k),lat_news_sort(k),1e5,'k.','MarkerSize',20); 
        axis([lon_news_sort(k)-15 lon_news_sort(k)+15 ...
          lat_news_sort(k)-15 lat_news_sort(k)+15]);
        caxis([-4 3]);
        titl = ['OUTSIDE: river number: ',num2str(k),' name: ',river_names_sort{k}];
        title(titl);
        colorbar;
        pause
      end
      
    end
end

% nearest neighbor search to fill in any 0 values left for each input field
% after the river mapping is done.
aa = find(din_conc_vec == 0);
bb = find(din_conc_vec > 0);
F = scatteredInterpolant(lon_mod_runoff_vec(bb),lat_mod_runoff_vec(bb),din_conc_vec(bb), ...
    'nearest','nearest');
din_conc_vec(aa) = F(lon_mod_runoff_vec(aa),lat_mod_runoff_vec(aa));

aa = find(don_conc_vec == 0);
bb = find(don_conc_vec > 0);
F = scatteredInterpolant(lon_mod_runoff_vec(bb),lat_mod_runoff_vec(bb),don_conc_vec(bb), ...
    'nearest','nearest');
don_conc_vec(aa) = F(lon_mod_runoff_vec(aa),lat_mod_runoff_vec(aa));

aa = find(pn_conc_vec == 0);
bb = find(pn_conc_vec > 0);
F = scatteredInterpolant(lon_mod_runoff_vec(bb),lat_mod_runoff_vec(bb),pn_conc_vec(bb), ...
    'nearest','nearest');
pn_conc_vec(aa) = F(lon_mod_runoff_vec(aa),lat_mod_runoff_vec(aa));

aa = find(dip_conc_vec == 0);
bb = find(dip_conc_vec > 0);
F = scatteredInterpolant(lon_mod_runoff_vec(bb),lat_mod_runoff_vec(bb),dip_conc_vec(bb), ...
    'nearest','nearest');
dip_conc_vec(aa) = F(lon_mod_runoff_vec(aa),lat_mod_runoff_vec(aa));

aa = find(dop_conc_vec == 0);
bb = find(dop_conc_vec > 0);
F = scatteredInterpolant(lon_mod_runoff_vec(bb),lat_mod_runoff_vec(bb),dop_conc_vec(bb), ...
    'nearest','nearest');
dop_conc_vec(aa) = F(lon_mod_runoff_vec(aa),lat_mod_runoff_vec(aa));

aa = find(pp_conc_vec == 0);
bb = find(pp_conc_vec > 0);
F = scatteredInterpolant(lon_mod_runoff_vec(bb),lat_mod_runoff_vec(bb),pp_conc_vec(bb), ...
    'nearest','nearest');
pp_conc_vec(aa) = F(lon_mod_runoff_vec(aa),lat_mod_runoff_vec(aa));

aa = find(si_conc_vec == 0);
bb = find(si_conc_vec > 0);
F = scatteredInterpolant(lon_mod_runoff_vec(bb),lat_mod_runoff_vec(bb),si_conc_vec(bb), ...
    'nearest','nearest');
si_conc_vec(aa) = F(lon_mod_runoff_vec(aa),lat_mod_runoff_vec(aa));

totn_conc_vec = din_conc_vec + don_conc_vec + pn_conc_vec;
totp_conc_vec = dip_conc_vec + dop_conc_vec + pp_conc_vec;

% calculate ratios of dissolved and particulate to inorganic
din_flux_vec = din_conc_vec.*Q_mod_vec;
dip_flux_vec = dip_conc_vec.*Q_mod_vec;
don_flux_vec = don_conc_vec.*Q_mod_vec;
dop_flux_vec = dop_conc_vec.*Q_mod_vec;
pn_flux_vec = pn_conc_vec.*Q_mod_vec;
pp_flux_vec = pp_conc_vec.*Q_mod_vec;

don_ratio = sum(don_flux_vec)/sum(din_flux_vec);
dop_ratio = sum(dop_flux_vec)/sum(dip_flux_vec);
pn_ratio = sum(pn_flux_vec)/sum(din_flux_vec);
pp_ratio = sum(pp_flux_vec)/sum(dip_flux_vec);

%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%
% Produce plots to evaluate the mapping                                   %
%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%

% Use total fluxes to scale dots, m3 sec-1 * moles m-3 = moles sec-1
totn_flux_vec = totn_conc_vec.*Q_mod_vec;
totp_flux_vec = totp_conc_vec.*Q_mod_vec;
totsi_flux_vec = si_conc_vec.*Q_mod_vec;

% scale marker size with the total nitrogen flux
ms_vec = zeros(size(Q_mod_vec));
ms_vec(log10(Q_mod_vec) < 0) = 1;
ms_vec((log10(Q_mod_vec) > 0) & (log10(Q_mod_vec) < 1)) = 2.5;
ms_vec((log10(Q_mod_vec) > 1) & (log10(Q_mod_vec) < 2)) = 10;
ms_vec((log10(Q_mod_vec) > 2) & (log10(Q_mod_vec) < 3)) = 25;
ms_vec(log10(Q_mod_vec) > 3) = 100;

figure(1)
clf

subplot(1,3,1);
scatter3(lon_mod_runoff_vec,lat_mod_runoff_vec,totn_conc_vec*1e3,ms_vec, ...
    totn_conc_vec*1e3,'filled');
hold on
view(2);
caxis([30 150]);
colorbar
title('total nitrogen concentration, mmoles m-3');

subplot(1,3,2);
scatter3(lon_mod_runoff_vec,lat_mod_runoff_vec,totp_conc_vec*1e3,ms_vec, ...
    totp_conc_vec*1e3,'filled');
hold on
view(2);
caxis([0 10]);
colorbar
title('total phosphorus concentration, mmoles m-3');

subplot(1,3,3)
scatter3(lon_mod_runoff_vec,lat_mod_runoff_vec,totn_conc_vec./totp_conc_vec,ms_vec, ...
    totn_conc_vec./totp_conc_vec,'filled');
hold on
view(2);
caxis([10 100]);
colorbar
title('N:P ratio');

figure(2)
clf

subplot(1,3,1);
scatter3(lon_mod_runoff_vec,lat_mod_runoff_vec,din_conc_vec*1e3,ms_vec, ...
    din_conc_vec*1e3,'filled');
hold on
view(2);
caxis([0 100]);
colorbar
title('din concentration, mmoles m-3');

subplot(1,3,2);
scatter3(lon_mod_runoff_vec,lat_mod_runoff_vec,don_conc_vec*1e3,ms_vec, ...
    don_conc_vec*1e3,'filled');
hold on
view(2);
caxis([0 100]);
colorbar
title('don concentration, mmoles m-3');

subplot(1,3,3)
scatter3(lon_mod_runoff_vec,lat_mod_runoff_vec,pn_conc_vec*1e3,ms_vec, ...
    pn_conc_vec*1e3,'filled');
hold on
view(2);
caxis([0 100]);
colorbar
title('pn concentration, mmoles m-3');

figure(3)
clf

subplot(1,3,1);
scatter3(lon_mod_runoff_vec,lat_mod_runoff_vec,dip_conc_vec*1e3,ms_vec, ...
    dip_conc_vec*1e3,'filled');
hold on
view(2);
caxis([0 5]);
colorbar
title('dip concentration, mmoles m-3');

subplot(1,3,2);
scatter3(lon_mod_runoff_vec,lat_mod_runoff_vec,dop_conc_vec*1e3,ms_vec, ...
    dop_conc_vec*1e3,'filled');
hold on
view(2);
caxis([0 3]);
colorbar
title('dop concentration, mmoles m-3');

subplot(1,3,3)
scatter3(lon_mod_runoff_vec,lat_mod_runoff_vec,pp_conc_vec*1e3,ms_vec, ...
    pp_conc_vec*1e3,'filled');
hold on
view(2);
caxis([0 3]);
colorbar
title('pp concentration, mmoles m-3');

figure(10)
clf

subplot(2,2,1);
scatter3(lon_mod_runoff_vec,lat_mod_runoff_vec,don_conc_vec./din_conc_vec,ms_vec, ...
    don_conc_vec./din_conc_vec,'filled');
hold on
view(2);
caxis([0 2]);
colorbar
title('don:din');

subplot(2,2,2);
scatter3(lon_mod_runoff_vec,lat_mod_runoff_vec,pn_conc_vec./din_conc_vec,ms_vec, ...
    pn_conc_vec./din_conc_vec,'filled');
hold on
view(2);
caxis([0 2]);
colorbar
title('pn:din');

subplot(2,2,3)
scatter3(lon_mod_runoff_vec,lat_mod_runoff_vec,dop_conc_vec./dip_conc_vec,ms_vec, ...
    dop_conc_vec./dip_conc_vec,'filled');
hold on
view(2);
caxis([0 2]);
colorbar
title('dop:dip');

subplot(2,2,4)
scatter3(lon_mod_runoff_vec,lat_mod_runoff_vec,pp_conc_vec./dip_conc_vec,ms_vec, ...
    pp_conc_vec./dip_conc_vec,'filled');
hold on
view(2);
caxis([0 2]);
colorbar
title('pp:dip');

figure(5)
clf
scatter3(lon_mod_runoff_vec,lat_mod_runoff_vec,si_conc_vec*1e3,ms_vec, ...
    si_conc_vec*1e3,'filled');
hold on
view(2);
caxis([30 300]);
colorbar
title('si concentration, mmoles m-3');

figure(6)
clf

subplot(1,2,1);
scatter3(lon_mod_runoff_vec,lat_mod_runoff_vec,log10(totn_flux_vec),ms_vec, ...
    log10(totn_flux_vec),'filled');
hold on
view(2);
caxis([-1 2]);
colorbar
title('N flux, log10(moles sec-1)');

subplot(1,2,2);
scatter3(lon_mod_runoff_vec,lat_mod_runoff_vec,log10(totp_flux_vec),ms_vec, ...
    log10(totp_flux_vec),'filled');
hold on
view(2);
caxis([-3 1]);
colorbar
title('P flux, log10(moles sec-1)');

% output total fluxes in gigagrams of N
total_annual_n = sum(totn_flux_vec)*86400*365*14/1e12
total_annual_p = sum(totp_flux_vec)*86400*365*31/1e12
total_annual_si = sum(totsi_flux_vec)*86400*365*28.1/1e12

'press any key to continue'
pause

% Initialize 2D concentration arrays; these are the ones read into MOM6 to
% specify the nutrient concentrations of river inputs.
din_conc = zeros(size(lon_mod));
don_conc = zeros(size(lon_mod));
dip_conc = zeros(size(lon_mod));
dop_conc = zeros(size(lon_mod));
pn_conc = zeros(size(lon_mod));
pp_conc = zeros(size(lon_mod));
si_conc = zeros(size(lon_mod));

% Map concentration vectors onto 2D arrays.
aa = find(Q_mod_ann > 0);
din_conc(aa) = din_conc_vec;
don_conc(aa) = don_conc_vec;
pn_conc(aa) = pn_conc_vec;
dip_conc(aa) = dip_conc_vec;
dop_conc(aa) = dop_conc_vec;
pp_conc(aa) = pp_conc_vec;
si_conc(aa) = si_conc_vec;

NO3_CONC = din_conc;
LDON_CONC = frac_ldon*don_conc;
SLDON_CONC = frac_sldon*don_conc;
SRDON_CONC = frac_srdon*don_conc;
PO4_CONC = dip_conc;
LDOP_CONC = frac_ldop*dop_conc;
SLDOP_CONC = frac_sldop*dop_conc;
SRDOP_CONC = frac_srdop*dop_conc;
NDET_CONC = pn_conc;
PDET_CONC = pp_conc;   % The bioavailability of particulate P has already
                       % been accounted for.
                       
SI_CONC = si_conc;

% Add iron concentrations - initialize with nitrate and then overwrite
FED_CONC = NO3_CONC;
FEDET_CONC = NO3_CONC;
% 40 nM dissolved iron concentration from De Baar and De Jong + 30nM 
% Colloidal and nanoparticle flux as reported in Canfield and Raiswell
FED_CONC(FED_CONC > 0) = const_fed;
FEDET_CONC(FEDET_CONC > 0) = 0.0;

% series of quick figures to check the 2D nutrient input files.
ms = 8;
figure(7);
clf
subplot(3,2,1);
title('log10(NO3 CONC)'); hold on; 
scatter3(lon_mod(:),lat_mod(:),log10(NO3_CONC(:)),ms,log10(NO3_CONC(:)),'filled'); 
caxis([-4 -1]); colorbar;

subplot(3,2,2);
title('log10(LDON CONC)'); hold on; 
scatter3(lon_mod(:),lat_mod(:),log10(LDON_CONC(:)),ms,log10(LDON_CONC(:)),'filled'); 
caxis([-4 -1]); colorbar;

subplot(3,2,3);
title('log10(SLDON CONC)'); hold on; 
scatter3(lon_mod(:),lat_mod(:),log10(SLDON_CONC(:)),ms,log10(SLDON_CONC(:)),'filled'); 
caxis([-4 -1]); colorbar;

subplot(3,2,4);
title('log10(SRDON CONC)'); hold on; 
scatter3(lon_mod(:),lat_mod(:),log10(SRDON_CONC(:)),ms,log10(SRDON_CONC(:)),'filled'); 
caxis([-4 -1]); colorbar;

subplot(3,2,5);
title('log10(NDET CONC)'); hold on; 
scatter3(lon_mod(:),lat_mod(:),log10(NDET_CONC(:)),ms,log10(NDET_CONC(:)),'filled'); 
caxis([-4 -1]); colorbar;

figure(8);
clf
subplot(3,2,1);
title('log10(PO4 CONC)'); hold on; 
scatter3(lon_mod(:),lat_mod(:),log10(PO4_CONC(:)),ms,log10(PO4_CONC(:)),'filled'); 
caxis([-4 -2]); colorbar;

subplot(3,2,2);
title('log10(LDOP CONC)'); hold on; 
scatter3(lon_mod(:),lat_mod(:),log10(LDOP_CONC(:)),ms,log10(LDOP_CONC(:)),'filled'); 
caxis([-4 -2]); colorbar;

subplot(3,2,3);
title('log10(SLDOP CONC)'); hold on; 
scatter3(lon_mod(:),lat_mod(:),log10(SLDOP_CONC(:)),ms,log10(SLDOP_CONC(:)),'filled'); 
caxis([-4 -2]); colorbar;

subplot(3,2,4);
title('log10(SRDOP CONC)'); hold on; 
scatter3(lon_mod(:),lat_mod(:),log10(SRDOP_CONC(:)),ms,log10(SRDOP_CONC(:)),'filled'); 
caxis([-4 -2]); colorbar;

subplot(3,2,5);
title('log10(PDET CONC)'); hold on; 
scatter3(lon_mod(:),lat_mod(:),log10(PDET_CONC(:)),ms,log10(PDET_CONC(:)),'filled'); 
caxis([-4 -2]); colorbar;

figure(9)
clf
clf
subplot(3,2,1);
title('log10(FED CONC)'); hold on; 
scatter3(lon_mod(:),lat_mod(:),log10(FED_CONC(:)),ms,log10(FED_CONC(:)),'filled'); 
caxis([-5 -3]); colorbar;

subplot(3,2,2);
title('log10(FEDET CONC)'); hold on; 
scatter3(lon_mod(:),lat_mod(:),log10(FEDET_CONC(:)),ms,log10(FEDET_CONC(:)),'filled'); 
caxis([-5 -3]); colorbar;

subplot(3,2,3);
title('log10(SI CONC)'); hold on; 
scatter3(lon_mod(:),lat_mod(:),log10(SI_CONC(:)),ms,log10(SI_CONC(:)),'filled'); 
caxis([-3 -0]); colorbar;

%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%
% Save Files                                                              %
%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%
% option to save matlab file
% save River_DIC_ALK_USGS_NWA ALK_CONC DIC_CONC

% Construct netcdf file following format used by nutrient input files to
% MOM6
time = 0;
nlat = size(lat_mod,1);
nlon = size(lat_mod,2);

ncid = netcdf.create(nc_file_name,'CLOBBER');
dimid0 = netcdf.defDim(ncid,'time',netcdf.getConstant('NC_UNLIMITED'));

dimid1 = netcdf.defDim(ncid,'y',nlat);
dimid2 = netcdf.defDim(ncid,'x',nlon);

%attributes inherited from the old river nutrient forcing file.  The
%calendar needs to be specified even though the nutrient values are
%constant.  Not sure how much of the rest is needed.
varid0 = netcdf.defVar(ncid,'time','double',dimid0);
netcdf.putAtt(ncid,varid0,'calendar','NOLEAP');
netcdf.putAtt(ncid,varid0,'calendar_type','NOLEAP');
netcdf.putAtt(ncid,varid0,'modulo','T');
netcdf.putAtt(ncid,varid0,'units','days since 1900-1-1 0:00:00');
netcdf.putAtt(ncid,varid0,'time_origin','01-JAN-1990 00:00:00');

varid1 = netcdf.defVar(ncid,'y','int',dimid1);
netcdf.putAtt(ncid,varid1,'cartesian_axis','Y');
varid2 = netcdf.defVar(ncid,'x','int',dimid2);
netcdf.putAtt(ncid,varid2,'cartesian_axis','X');
varid3 = netcdf.defVar(ncid,'lat','double',[dimid2 dimid1]);
netcdf.putAtt(ncid,varid3,'units','degrees north');
varid4 = netcdf.defVar(ncid,'lon','double',[dimid2 dimid1]);
netcdf.putAtt(ncid,varid4,'units','degrees east');
varid5 = netcdf.defVar(ncid,'NO3_CONC','double',[dimid2,dimid1,dimid0]);
netcdf.putAtt(ncid,varid5,'units','mol m-3');
netcdf.putAtt(ncid,varid5,'long_name','DIN_CONC');
varid6 = netcdf.defVar(ncid,'LDON_CONC','double',[dimid2,dimid1,dimid0]);
netcdf.putAtt(ncid,varid6,'units','mol m-3');
netcdf.putAtt(ncid,varid6,'long_name','0.3*DON_CONC');
varid7 = netcdf.defVar(ncid,'SLDON_CONC','double',[dimid2,dimid1,dimid0]);
netcdf.putAtt(ncid,varid7,'units','mol m-3');
netcdf.putAtt(ncid,varid7,'long_name','0.35*DON_CONC');
varid8 = netcdf.defVar(ncid,'SRDON_CONC','double',[dimid2,dimid1,dimid0]);
netcdf.putAtt(ncid,varid8,'units','mol m-3');
netcdf.putAtt(ncid,varid8,'long_name','0.35*DON_CONC');
varid9 = netcdf.defVar(ncid,'NDET_CONC','double',[dimid2,dimid1,dimid0]);
netcdf.putAtt(ncid,varid9,'units','mol m-3');
netcdf.putAtt(ncid,varid9,'long_name','1.0*PN_CONC');
varid10 = netcdf.defVar(ncid,'PO4_CONC','double',[dimid2,dimid1,dimid0]);
netcdf.putAtt(ncid,varid10,'units','mol m-3');
netcdf.putAtt(ncid,varid10,'long_name','PO4_CONC');
varid11 = netcdf.defVar(ncid,'LDOP_CONC','double',[dimid2,dimid1,dimid0]);
netcdf.putAtt(ncid,varid11,'units','mol m-3');
netcdf.putAtt(ncid,varid11,'long_name','0.3*DOP_CONC');
varid12 = netcdf.defVar(ncid,'SLDOP_CONC','double',[dimid2,dimid1,dimid0]);
netcdf.putAtt(ncid,varid12,'units','mol m-3');
netcdf.putAtt(ncid,varid12,'long_name','0.35*DOP_CONC');
varid13 = netcdf.defVar(ncid,'SRDOP_CONC','double',[dimid2,dimid1,dimid0]);
netcdf.putAtt(ncid,varid13,'units','mol m-3');
netcdf.putAtt(ncid,varid13,'long_name','0.35*DOP_CONC');
varid14 = netcdf.defVar(ncid,'PDET_CONC','double',[dimid2,dimid1,dimid0]);
netcdf.putAtt(ncid,varid14,'units','mol m-3');
netcdf.putAtt(ncid,varid14,'long_name','0.3*PP_CONC');
varid15 = netcdf.defVar(ncid,'FED_CONC','double',[dimid2,dimid1,dimid0]);
netcdf.putAtt(ncid,varid15,'units','mol m-3');
netcdf.putAtt(ncid,varid15,'long_name','FED_CONC');
varid16 = netcdf.defVar(ncid,'FEDET_CONC','double',[dimid2,dimid1,dimid0]);
netcdf.putAtt(ncid,varid16,'units','mol m-3');
netcdf.putAtt(ncid,varid16,'long_name','FEDET_CONC');
varid17 = netcdf.defVar(ncid,'SI_CONC','double',[dimid2,dimid1,dimid0]);
netcdf.putAtt(ncid,varid17,'units','mol m-3');
netcdf.putAtt(ncid,varid17,'long_name','SI_CONC');
netcdf.close(ncid)

ncid = netcdf.open(nc_file_name,'NC_WRITE');
netcdf.putVar(ncid,varid0,0,1,time);
% nutrient input files appear seem to need dummy axes to be read in
% properly, but eventually do a grid by grid mapping that doesn't require
% these.
netcdf.putVar(ncid,varid1,1:nlat);
netcdf.putVar(ncid,varid2,1:nlon);
netcdf.putVar(ncid,varid3,permute(lon_mod,[2,1]));
netcdf.putVar(ncid,varid4,permute(lat_mod,[2,1]));
netcdf.putVar(ncid,varid5,permute(NO3_CONC,[3,2,1]));
netcdf.putVar(ncid,varid6,permute(LDON_CONC,[3,2,1]));
netcdf.putVar(ncid,varid7,permute(SLDON_CONC,[3,2,1]));
netcdf.putVar(ncid,varid8,permute(SRDON_CONC,[3,2,1]));
netcdf.putVar(ncid,varid9,permute(NDET_CONC,[3,2,1]));
netcdf.putVar(ncid,varid10,permute(PO4_CONC,[3,2,1]));
netcdf.putVar(ncid,varid11,permute(LDOP_CONC,[3,2,1]));
netcdf.putVar(ncid,varid12,permute(SLDOP_CONC,[3,2,1]));
netcdf.putVar(ncid,varid13,permute(SRDOP_CONC,[3,2,1]));
netcdf.putVar(ncid,varid14,permute(PDET_CONC,[3,2,1]));
netcdf.putVar(ncid,varid15,permute(FED_CONC,[3,2,1]));
netcdf.putVar(ncid,varid16,permute(FEDET_CONC,[3,2,1]));
netcdf.putVar(ncid,varid17,permute(SI_CONC,[3,2,1]));
netcdf.close(ncid)
