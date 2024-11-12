clear all;

% load in matlab file with GLORICH data
% created with:T = readtable('hydrochemistry.csv','NumHeaderLines',1);
%load GLORICH_Data.mat;
T = readtable('hydrochemistry.csv','NumHeaderLines',1);
stations = T{:,1};

%"102481","COLORADO R AT NIB AB MORELOS DAM NR ANDRADE, CA.","9522000","USA","AZ",32.71,-114.71,"NA1983"
%"110042","Fraser River at Hope","BC08MF0001","Canada","BC",49.38,-121.45,"NA1983
%"110009","Skeena River at Usk","BC08EF0001","Canada","BC",54.63,-128.41,"NA1983"
%"110004","Stikine River above Choquette River","BC08CF0002","Canada","BC",56.82,-131.76,"NA1983"
%"102954","COPPER R AT MILLION DOLLAR BRIDGE NR CORDOVA AK","15214000","USA","AK",60.67,-144.74,"NA1983"
%"102983","SUSITNA R AT SUSITNA STATION AK","15294350","USA","AK",61.54,-150.51,"NA1983"
%"102985","NUSHAGAK R AT EKWOK AK","15302500","USA","AK",59.34,-157.47,"NA1983"
%"102986","KUSKOKWIM R AT CROOKED CREEK AK","15304000","USA","AK",61.87,-158.10,"NA1983"

% Define rivers.  I took the lat/lon from the mouths defined in Global NEWS
% Where stream gages are upstream, this makes the assumption that those
% properties are reasonably indicative of conditions at the river mouth.
num_rivers = 8;
river_name{1} = 'Colorado'; station_num(1) = 102481;
lat(1) = 31.75; lon(1) = 245.25;
river_name{2} = 'Fraser'; station_num(2) = 110042;
lat(2) = 49.25; lon(2) = 237.25;
river_name{3} = 'Skeena'; station_num(3) = 110009;
lat(3) = 54.25; lon(3) = 229.75;
river_name{4} = 'Stikine'; station_num(4) = 110004;
lat(4) = 56.75; lon(4) = 227.75;
river_name{5} = 'Copper'; station_num(5) = 102954;
lat(5) = 60.25; lon(5) = 215.25;
river_name{6} = 'Susitna'; station_num(6) = 102983;
lat(6) = 61.75; lon(6) = 209.75;
river_name{7} = 'Nushagak'; station_num(7) = 102985;
lat(7) = 58.75; lon(7) = 201.75;
river_name{8} = 'Kuskokwim'; station_num(8) = 102986;
lat(8) = 60.25; lon(8) = 197.75;
% Rely on ArcticGRO for the Arctic rivers
% Yukon at Pilot Station
%river_name{9} = 'Yukon'; station_num(9) = 102988;
%lat(9) = 60.25; lon(9) = 197.75;
% Mackenzie at Tsiigehtchic is the same as ArcticGRO
%river_name{10} = 'Mackenzie'; station_num(10) = 120036;
%lat(10) = 60.25; lon(10) = 197.75;
%river_name{9} = 'Anadyr'; station_num(9) = 510090;
%lat(9) = 64.75; lon(9) = 177.75; 

% co2 system solver to derive DIC from alkalinity, pH and temperature
addpath /home/cas/matlab/co2sys

for n = 1:num_rivers
  aa = find(stations == station_num(n));
  num_stations(n) = size(aa,1);
  discharge(n) = nanmean(T{aa,6});
  alk_vec = T{aa,20};
  alk(n) = nanmean(alk_vec);
  % nitrogen species
  tn_vec = T{aa,62}; num_tn(n) = size(find(isfinite(tn_vec) == 1),1); tn(n) = nanmean(tn_vec);
  dn_vec = T{aa,64}; num_dn(n) = size(find(isfinite(dn_vec) == 1),1); dn(n) = nanmean(dn_vec);
  % first method of extracting particulate nitrogen from GLORICH
  pn1_vec = tn_vec - dn_vec; pn1_vec(pn1_vec < 0) = 0;
  num_pn1(n) = size(find(isfinite(pn1_vec) == 1),1); pn1(n) = nanmean(pn1_vec);
  %pn_vec = T{aa,66}; num_pn(n) = size(find(isfinite(pn_vec) == 1),1); pn(n) = nanmean(pn_vec);
  tin_vec = T{aa,68}; num_tin(n) = size(find(isfinite(tin_vec) == 1),1); tin(n) = nanmean(tin_vec);
  din_vec = T{aa,70}; num_din(n) = size(find(isfinite(din_vec) == 1),1); din(n) = nanmean(din_vec);
  ton_vec = T{aa,72}; num_ton(n) = size(find(isfinite(ton_vec) == 1),1); ton(n) = nanmean(ton_vec);
  %don_vec = T{aa,74}; num_don(n) = size(find(isfinite(don_vec) == 1),1); don(n) = nanmean(don_vec);
  pon_vec = T{aa,76}; num_pon(n) = size(find(isfinite(pon_vec) == 1),1); pon(n) = nanmean(pon_vec);
  tkn_vec = T{aa,78}; num_tkn(n) = size(find(isfinite(tkn_vec) == 1),1); tkn(n) = nanmean(tkn_vec);
  dkn_vec = T{aa,80}; num_dkn(n) = size(find(isfinite(dkn_vec) == 1),1); dkn(n) = nanmean(dkn_vec);
  % second method of extracting particulate nitrogen from GLORICH
  pn2_vec = tkn_vec - dkn_vec; pn1_vec(pn2_vec < 0) = 0;
  num_pn2(n) = size(find(isfinite(pn2_vec) == 1),1); pn2(n) = nanmean(pn2_vec);
  no3_vec = T{aa,82}; num_no3(n) = size(find(isfinite(no3_vec) == 1),1); no3(n) = nanmean(no3_vec);
  no2_vec = T{aa,84}; num_no2(n) = size(find(isfinite(no2_vec) == 1),1); no2(n) = nanmean(no2_vec);
  no2no3_vec = T{aa,86}; num_no2no3(n) = size(find(isfinite(no2no3_vec) == 1),1); no2no3(n) = nanmean(no2no3_vec);
  tnh4_vec = T{aa,88}; num_tnh4(n) = size(find(isfinite(tnh4_vec) == 1),1); tnh4(n) = nanmean(tnh4_vec);
  dnh4_vec = T{aa,90}; num_dnh4(n) = size(find(isfinite(dnh4_vec) == 1),1); dnh4(n) = nanmean(dnh4_vec);
  don_vec = dn_vec-no2no3_vec-dnh4(n); don_vec(don_vec < 0) = 0; 
  num_don(n) = size(find(isfinite(don_vec) == 1),1); don(n) = nanmean(don_vec);
  % phosphorus
  tp_vec = T{aa,92}; num_tp(n) = size(find(isfinite(tp_vec) == 1),1); tp(n) = nanmean(tp_vec);
  dp_vec = T{aa,94}; num_dp(n) = size(find(isfinite(dp_vec) == 1),1); dp(n) = nanmean(dp_vec);
  pp_vec = tp_vec - dp_vec; pp_vec(pp_vec < 0) = 0; 
  num_pp(n) = size(find(isfinite(pp_vec) == 1),1); pp(n) = nanmean(pp_vec);
  %pp_vec = T{aa,96}; pp(n) = nanmean(pp_vec);
  tip_vec = T{aa,98}; num_tip(n) = size(find(isfinite(tip_vec) == 1),1); tip(n) = nanmean(tip_vec);
  dip_vec = T{aa,100}; num_dip(n) = size(find(isfinite(dip_vec) == 1),1); dip(n) = nanmean(dip_vec);
  dop_vec = dp_vec - dip_vec; dop_vec(dop_vec < 0) = 0; 
  num_dop(n) = size(find(isfinite(dop_vec) == 1),1); dop(n) = nanmean(dop_vec); 
  % oxygen
  o2_vec = T{aa,12}; num_o2(n) = size(find(isfinite(o2_vec) == 1),1); o2(n) = nanmean(o2_vec);
  % silica
  si_vec = T{aa,34}; num_si(n) = size(find(isfinite(si_vec) == 1),1); si(n) = nanmean(si_vec);
  % dic, fill in with pH if needed
  %dic_vec = T{aa,52};
  %bb = find(isfinite(dic_vec));
  pH_vec = T{aa,10}; pH(n) = nanmean(pH_vec);
  temp_vec = T{aa,8}; temp(n) = nanmean(temp_vec);
  
  
  % Simple initial DIC calculation based on mean alk and mean pH, room for
  % improvement here.
  
  if isnan(temp(n)); temp(n) = 5; end;
  %[RESULT,HEADERS,NICEHEADERS]=CO2SYS(PAR1,PAR2,PAR1TYPE,PAR2TYPE,...
  % ...SAL,TEMPIN,TEMPOUT,PRESIN,PRESOUT,SI,PO4,NH4,H2S,pHSCALEIN,...
  % ...K1K2CONSTANTS,KSO4CONSTANT,KFCONSTANT,BORON)     
  out = CO2SYS(alk(n),pH(n),1,3,0,temp(n),temp(n), ...
               100,100,0,0,0,0,4,15,1,2,2);
  dic(n) = mean(out(:,2));
end

lon_stations_glorich = lon;
lat_stations_glorich = lat;
station_names_glorich = river_name;

Q_ann_glorich = discharge;
dic_ann_glorich = dic;
alk_ann_glorich = alk;
no3_ann_glorich = no2no3;
% use no3 for the Stikine
no3_ann_glorich(4) = no3(4);
nh4_ann_glorich = dnh4;
% assume nh4 in Stikine is equal to nh4 in Skeena
nh4_ann_glorich(4) = nh4_ann_glorich(3);
din_ann_glorich = no3_ann_glorich + nh4_ann_glorich;
% Use weighted average of TN-DN and TKN-DKN
pn1(num_pn1 == 0) = 0; pn2(num_pn2 == 0) = 0;
pn_ann_glorich = (pn1.*num_pn1 + pn2.*num_pn2)./(num_pn1 + num_pn2);
% assume particulate nitrogen in Stikine is equal to Skeena
pn_ann_glorich(4) = pn_ann_glorich(3);
don_ann_glorich = don;
% assume dissolved organic nitrogen in Stikine is equal to Skeena
don_ann_glorich(4) = don_ann_glorich(3);

dip_ann_glorich = dip;
% assume po4 in Stikine is equal to po4 in GLORICH
dip_ann_glorich(4) = dip_ann_glorich(3);

dop_ann_glorich = dop;
% assume dop in the Stikine and Skeena are equal to that in the Copper
% DOP constraints are generally poor.  The Fraser is based on a single
% joint dp, dip measurement.  However, the contribution of dop to the total
% phosphorus load is also very low, so this is an issue I'm willing to
% stomach.
dop_ann_glorich(3) = dop_ann_glorich(5);
dop_ann_glorich(4) = dop_ann_glorich(5);

pp_ann_glorich = pp;
% set particulate load in the Stikine to that in the Skeena
pp_ann_glorich(4) = pp_ann_glorich(3);

si_ann_glorich = si;
o2_ann_glorich = o2;
dfe_ann_glorich = ones(size(o2_ann_glorich))*NaN;
pfe_ann_glorich = ones(size(o2_ann_glorich))*NaN;

% did not try and extract monthly data from GLORICH, so leave as NaNs
dic_monthly_glorich = ones(12,size(lon_stations_glorich,2))*NaN;
alk_monthly_glorich = ones(12,size(lon_stations_glorich,2))*NaN;
no3_monthly_glorich = ones(12,size(lon_stations_glorich,2))*NaN;
nh4_monthly_glorich = ones(12,size(lon_stations_glorich,2))*NaN;
din_monthly_glorich = ones(12,size(lon_stations_glorich,2))*NaN;
don_monthly_glorich = ones(12,size(lon_stations_glorich,2))*NaN;
pn_monthly_glorich = ones(12,size(lon_stations_glorich,2))*NaN;
dip_monthly_glorich = ones(12,size(lon_stations_glorich,2))*NaN;
dop_monthly_glorich = ones(12,size(lon_stations_glorich,2))*NaN;
pp_monthly_glorich = ones(12,size(lon_stations_glorich,2))*NaN;
dfe_monthly_glorich = ones(12,size(lon_stations_glorich,2))*NaN;
pfe_monthly_glorich = ones(12,size(lon_stations_glorich,2))*NaN;
si_monthly_glorich = ones(12,size(lon_stations_glorich,2))*NaN;
o2_monthly_glorich = ones(12,size(lon_stations_glorich,2))*NaN;

save NEP_GLORICH_data lon_stations_glorich lat_stations_glorich station_names_glorich ...
     Q_ann_glorich dic_ann_glorich alk_ann_glorich no3_ann_glorich nh4_ann_glorich ...
     din_ann_glorich pn_ann_glorich don_ann_glorich dip_ann_glorich dop_ann_glorich ...
     pp_ann_glorich si_ann_glorich o2_ann_glorich dfe_ann_glorich pfe_ann_glorich ...
     dic_monthly_glorich alk_monthly_glorich no3_monthly_glorich nh4_monthly_glorich ...
     din_monthly_glorich don_monthly_glorich pn_monthly_glorich dip_monthly_glorich ...
     dop_monthly_glorich pp_monthly_glorich dfe_monthly_glorich pfe_monthly_glorich ...
     si_monthly_glorich o2_monthly_glorich
     

% Ordering of the GLORICH Data
%1. "STAT_ID",
%2. "RESULT_DATETIME",
%3. "SAMPLE_TIME_DESC",
%4. "SAMPLING_MODE",
%5. "Ref",
%6. "Discharge_inst",
%7. "Discharge_inst_vrc",
%8. "Temp_water",
%9. "Temp_water_vrc",
%10. "pH",
%11. "pH_vrc",
%12. "DO_mgL",
%13. "DO_mgL_vrc",
%14. "DOSAT",
%15. "DOSAT_vrc",
%16. "SpecCond25C",
%17. "SpecCond25C_vrc",
%18. "SPM",
%19. "SPM_vrc",
%20. "Alkalinity",
%21. "Alkalinity_vrc",
%22. "HCO3",
%23. "HCO3_vrc",
%24. "CO3",
%25. "CO3_vrc",
%26. "Ca",
%27. "Ca_vrc",
%28. "Mg",
%29. "Mg_vrc",
%30. "Na",
%31. "Na_vrc",
%32. "K",
%33. "K_vrc",
%34. "SiO2",
%35. "SiO2_vrc",
%36. "Cl",
%37. "Cl_vrc",
%38. "SO4",
%39. "SO4_vrc",
%40. "F",
%41. "F_vrc",
%42. "DSr",
%43. "DSr_vrc",
%44. "TC",
%45. "TC_vrc",
%46. "DC",
%47. "DC_vrc",
%48. "PC",
%49. "PC_vrc",
%50. "TIC",
%51. "TIC_vrc",
%52. "DIC",
%53. "DIC_vrc",
%54. "PIC",
%55. "PIC_vrc",
%56. "TOC",
%57. "TOC_vrc",
%58. "DOC",
%59. "DOC_vrc",
%60. "POC",
%61. "POC_vrc",
%62. "TN",
%63. "TN_vrc",
%64. "DN",
%65. "DN_vrc",
%66. "PN",
%67. "PN_vrc",
%68. "TIN",
%69. "TIN_vrc",
%70. "DIN",
%71. "DIN_vrc",
%72. "TON",
%73. "TON_vrc",
%74. "DON",
%75. "DON_vrc",
%76. "PON",
%77. "PON_vrc",
%78. "TKN",
%79. "TKN_vrc",
%80. "DKN",
%81. "DKN_vrc",
%82. "NO3",
%83. "NO3_vrc",
%84. "NO2",
%85. "NO2_vrc",
%86. "NO2_NO3",
%87. "NO2_NO3_vrc",
%88. "TNH4",
%89. "TNH4_vrc",
%90. "DNH4",
%91. "DNH4_vrc",
%92. "TP",
%93. "TP_vrc",
%94. "DP",
%95. "DP_vrc",
%96. "PP",
%97. "PP_vrc",
%98. "TIP",
%99. "TIP_vrc",
%100. "DIP",
%101. "DIP_vrc",
%102. "PS",
%103. "PS_vrc"
