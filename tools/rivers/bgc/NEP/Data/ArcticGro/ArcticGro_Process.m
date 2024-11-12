% Program to process the ArcticGro data

clear all

filename = 'ArcticGRO_Water_Quality_Data.xlsx'
% co2 system solver to derive DIC from alkalinity, pH and temperature
addpath /home/cas/matlab/co2sys

% Longitude and Latitude from GlobalNEWS
river_name{1} = 'Ob';
lon(1) = 68.5; lat(1) = 68.75;
river_name{2} = 'Yenisey';
lon(2) = 82.25; lat(2) = 71.25;
river_name{3} = 'Lena';
lon(3) = 128; lat(3) = 73;
river_name{4} = 'Kolyma';
lon(4) = 161.25; lat(4) = 69.25;
river_name{5} = 'Yukon';
lon(5) = -164.75; lat(5) = 62.75;
river_name{6} = 'Mackenzie';
lon(6) = -134.75; lat(6) = 69.25;


for n = 1:6
  Data = readtable(filename,'Sheet',n);
  discharge(n) = nanmean(Data{:,5});
  temp(n) = nanmean(Data{:,6});
  % alk in mg CaCO3/L ~ g CaCO3/m3
  alk(n) = nanmean(Data{:,9});
  alk(n) = alk(n)/(40+12+16*3)*2*1e3; % to milliequivalents per m-3
  % pH
  pH(n) = nanmean(Data{:,7});
  % tdn in mg N L-1 ~ g N/m3
  tdn(n) = nanmean(Data{:,21});
  tdn(n) = tdn(n)*1e3/14; % mmoles m-3
  % no3 in micrograms N per L ~ mg N m-3
  no3(n) = nanmean(Data{:,22});
  no3(n) = no3(n)/14; % mmoles m-3
  % nh4 in micrograms N per L ~ mg N m-3
  nh4(n) = nanmean(Data{:,23});
  nh4(n) = nh4(n)/14; % mmoles m-3
  % tdp in micrograms P per L ~ mg P m-3
  tdp(n) = nanmean(Data{:,24});
  tdp(n) = tdp(n)/31; % mmoles m-3
  % po4 in micrograms P per L ~ mg P m-3
  po4(n) = nanmean(Data{:,25});
  po4(n) = po4(n)/31; % mmoles m-3
  % sio2 in mg SiO2 per L ~ g P m-3
  sio2(n) = nanmean(Data{:,26});
  sio2(n) = sio2(n)*1e3/(28.06+16*2);
  % pon in micrograms N per L ~ mg N m-3
  pon(n) = nanmean(Data{:,47});
  pon(n) = pon(n)/14; %mmoles m-3

  % calculate DIC from alk, pH and DIC
  out = CO2SYS(alk(n),pH(n),1,3,0,temp(n),temp(n), ...
               100,100,0,0,0,0,4,15,1,2,2);
  dic(n) = mean(out(:,2));

  % calculate don from tdn, no3 and nh4
  aa = find(isfinite(Data{:,21}) & isfinite(Data{:,22}) & isfinite(Data{:,23}));
  don(n) = nanmean(Data{aa,21}*1e3/14 - Data{aa,22}/14 - Data{aa,23}/14);

  % calculate dop from tdp and po4
  bb = find(isfinite(Data{:,24}/31) & isfinite(Data{:,25}/31));
  dop(n) = nanmean(Data{aa,24}/31 - Data{aa,25}/31);
end

% Fill in particulate phosphorus from GLOBAL NEWS
pp(1) = 1.29;  % Ob
pp(2) = 0.82;  % Yenisey
pp(3) = 1.48;  % Lena
pp(4) = 1.21;  % Kolyma
pp(5) = 1.94;  % Yukon
pp(6) = 1.44;  % Mackenzie

% For reference (DIN, DON, PN, DIP, DOP, PP)
% Yukon: 7.30 17.25  29.10 0.07 0.42 1.94
% Mackenzie: 7.42 19.86 24.34 0.14 0.48 1.44
% St. Lawrence: 52.80 24.86 3.81 0.98 0.55 0.21
% Ob: 21.80 24.16 22.35 1.16 0.56 1.29
% Lena: 7.74 21.34 25.48 0.24 0.52 1.48
% Yenisey: 8.54 21.65 14.21 0.088 0.52 0.82
% Kolyma: 10.17 21.92 21.27 0.18 0.53 1.21

lon_stations_arcticgro = lon;
lat_stations_arcticgro = lat;
station_names_arcticgro = river_name;

Q_ann_arcticgro = discharge;
dic_ann_arcticgro = dic;
alk_ann_arcticgro = alk;
no3_ann_arcticgro = no3;
nh4_ann_arcticgro = nh4;
din_ann_arcticgro = no3_ann_arcticgro + nh4_ann_arcticgro;
pn_ann_arcticgro = pon;
don_ann_arcticgro = don;
dip_ann_arcticgro = po4;
dop_ann_arcticgro = dop;
pp_ann_arcticgro = pp;
si_ann_arcticgro = sio2;
o2_ann_arcticgro = ones(size(Q_ann_arcticgro))*NaN;
dfe_ann_arcticgro = ones(size(Q_ann_arcticgro))*NaN;
pfe_ann_arcticgro = ones(size(Q_ann_arcticgro))*NaN;

% did not try and extract monthly data from arcticgro, so leave as NaNs
dic_monthly_arcticgro = ones(12,size(lon_stations_arcticgro,2))*NaN;
alk_monthly_arcticgro = ones(12,size(lon_stations_arcticgro,2))*NaN;
no3_monthly_arcticgro = ones(12,size(lon_stations_arcticgro,2))*NaN;
nh4_monthly_arcticgro = ones(12,size(lon_stations_arcticgro,2))*NaN;
din_monthly_arcticgro = ones(12,size(lon_stations_arcticgro,2))*NaN;
don_monthly_arcticgro = ones(12,size(lon_stations_arcticgro,2))*NaN;
pn_monthly_arcticgro = ones(12,size(lon_stations_arcticgro,2))*NaN;
dip_monthly_arcticgro = ones(12,size(lon_stations_arcticgro,2))*NaN;
dop_monthly_arcticgro = ones(12,size(lon_stations_arcticgro,2))*NaN;
pp_monthly_arcticgro = ones(12,size(lon_stations_arcticgro,2))*NaN;
dfe_monthly_arcticgro = ones(12,size(lon_stations_arcticgro,2))*NaN;
pfe_monthly_arcticgro = ones(12,size(lon_stations_arcticgro,2))*NaN;
si_monthly_arcticgro = ones(12,size(lon_stations_arcticgro,2))*NaN;
o2_monthly_arcticgro = ones(12,size(lon_stations_arcticgro,2))*NaN;

save arcticgro_data lon_stations_arcticgro lat_stations_arcticgro station_names_arcticgro ...
     Q_ann_arcticgro dic_ann_arcticgro alk_ann_arcticgro no3_ann_arcticgro nh4_ann_arcticgro ...
     din_ann_arcticgro pn_ann_arcticgro don_ann_arcticgro dip_ann_arcticgro dop_ann_arcticgro ...
     pp_ann_arcticgro si_ann_arcticgro o2_ann_arcticgro dfe_ann_arcticgro pfe_ann_arcticgro ...
     dic_monthly_arcticgro alk_monthly_arcticgro no3_monthly_arcticgro nh4_monthly_arcticgro ...
     din_monthly_arcticgro don_monthly_arcticgro pn_monthly_arcticgro dip_monthly_arcticgro ...
     dop_monthly_arcticgro pp_monthly_arcticgro dfe_monthly_arcticgro pfe_monthly_arcticgro ...
     si_monthly_arcticgro o2_monthly_arcticgro
