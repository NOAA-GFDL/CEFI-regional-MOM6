clear all

% Add paths to alkalinity/DIC estimation routines
%addpath /home/Andrew.C.Ross/git/nwa12/setup/boundary/ESPER-main/
%addpath /home/Andrew.C.Ross/git/nwa12/setup/boundary/ESPER-main/ESPER_LIR_Files/
%addpath /home/Andrew.C.Ross/git/nwa12/setup/boundary/ESPER-main/ESPER_NN_Files/
%addpath /home/Andrew.C.Ross/git/nwa12/setup/boundary/ESPER-main/SimpleCantEstimateFiles/
addpath ./ESPER/
addpath ./ESPER/ESPER_LIR_Files/
addpath ./ESPER/ESPER_NN_Files/
addpath ./ESPER/SimpleCantEstimateFiles/


year_start = __STARTYEAR__;
year_end = __ENDYEAR__; 
nyears = (year_end - year_start) + 1;

year_ind = 0;
for year = year_start:year_end
    year
    out_file_name = ['./outputs/DICAlk_ESPER_LIR_GLORYS_025_',num2str(year,'%4u'),'.nc'];

    % get grid data and initialize arrays
    if year >= 2021
        in_file_name = ['/work/acr/glorys/GLOBAL_ANALYSISFORECAST_PHY_001_024/monthly/glorys_monthly_ts_coarse_',num2str(year,'%4u'),'.nc'];
    else
        in_file_name = ['/work/acr/glorys/GLOBAL_MULTIYEAR_PHY_001_030/monthly/glorys_monthly_ts_coarse_',num2str(year,'%4u'),'.nc'];
    end 
    
    lon = ncread(in_file_name,'lon'); 
    nlon = size(lon,1);
    lat = ncread(in_file_name,'lat'); 
    nlat = size(lat,1);
    depth = ncread(in_file_name,'depth'); 
    ndepth = size(depth,1);
    [lon_grid, lat_grid] = meshgrid(lon,lat);

    lon_grid_stack = zeros(nlat,nlon,ndepth);
    lat_grid_stack = zeros(nlat,nlon,ndepth);
    depth_stack = ones(nlat,nlon,ndepth);
    for k = 1:ndepth
        lon_grid_stack(:,:,k) = lon_grid;
        lat_grid_stack(:,:,k) = lat_grid;
        depth_stack(:,:,k) = depth(k);
    end

    dic_ann_ts = zeros(nlat,nlon,ndepth);
    alk_ann_ts = zeros(nlat,nlon,ndepth);
    time_days = zeros(nyears,1);
    
    year_ind = year_ind + 1;
    time_start = year - year_start + 1;
    % ncread has a 1-based indice
    pot_temp_monthly = ncread(in_file_name,'thetao',[1 1 1 1],[inf inf inf inf]);
    % uncomment if you want the anthropogenic signal that evolves yearly
    time = year + 0.5;
    % uncomment if you want an anthropogenic signal based on a single year (control run) 
    % time = 1993.5
    pot_temp_ann = squeeze(mean(pot_temp_monthly,4));
    % latitude, longitude, depth
    pot_temp_ann = permute(pot_temp_ann,[2 1 3]);
    salt_monthly = ncread(in_file_name,'so',[1 1 1 1],[inf inf inf inf]);
    salt_ann = squeeze(mean(salt_monthly,4));
    salt_ann = permute(salt_ann,[2 1 3]);
    clear pot_temp_monthly salt_monthly;

    % calculate dic and alkalinity using the ESPER equations from Carter et
    % al. (2021) (L&O)
    dic_ann = zeros(size(pot_temp_ann));
    alk_ann = zeros(size(salt_ann));

    aa = find(isfinite(pot_temp_ann));
    temp_vec = pot_temp_ann(aa);
    salt_vec = salt_ann(aa);
    % limit the salt to the intended range for ESPER
    salt_vec(salt_vec < 5) = 5;
    salt_vec(salt_vec > 50) = 50;
    lon_vec = lon_grid_stack(aa);
    lat_vec = lat_grid_stack(aa);
    depth_vec = depth_stack(aa);

    time_vec = ones(size(lon_vec))*time;
        
    % Prepare for ESPER call
    % Desired Variables, 1 = Alkalinity, 2 = DIC
    DesVar = [1 2];
    % Output Coordinates; longitude in degrees East
    OutCoord = [lon_vec lat_vec depth_vec];
    % Predictor variables; Salt, Temp
    PredVar = [salt_vec temp_vec];
    % Predictor Type (1 = Salt, 2 = Temp)
    PredType = [1 2];
        
    % Call the ESPER routines
    'ESPER Estimation'
    [a,b] = ESPER_LIR(DesVar,OutCoord,PredVar,PredType,'Equations',[8], ...
            'estdates',time_vec);  
    alk_vec = a.TA;
    dic_vec = a.DIC;

    dic_ann(aa) = dic_vec;
    alk_ann(aa) = alk_vec;
    dic_ann(dic_ann == 0) = NaN;
    alk_ann(alk_ann == 0) = NaN;

    % track time in days ince the start year
    time_days = datenum([year 7 1 12 0 0]) - datenum([year_start 1 1 0 0 0]);  

    % Define netcdf dimensions
    ncid = netcdf.create(out_file_name,'CLOBBER');
    dimid0 = netcdf.defDim(ncid,'time',netcdf.getConstant('NC_UNLIMITED'));
    dimid1 = netcdf.defDim(ncid,'xt_ocean',nlon);
    dimid2 = netcdf.defDim(ncid,'yt_ocean',nlat);
    dimid3 = netcdf.defDim(ncid,'st_ocean',ndepth);

    % define attributes
    time_units = ['days since ',num2str(year_start,'%4u'),'-1-1 0:00:00'];
    varid0 = netcdf.defVar(ncid,'time','double',dimid0);
    netcdf.putAtt(ncid,varid0,'calendar','standard');
    netcdf.putAtt(ncid,varid0,'axis','T');
    netcdf.putAtt(ncid,varid0,'units',time_units);
    varid1 = netcdf.defVar(ncid,'xt_ocean','double',dimid1);
    netcdf.putAtt(ncid,varid1,'standard_name','longitude');
    netcdf.putAtt(ncid,varid1,'long_name','longitude');
    netcdf.putAtt(ncid,varid1,'units','degrees_east');
    netcdf.putAtt(ncid,varid1,'axis','X');
    varid2 = netcdf.defVar(ncid,'yt_ocean','double',dimid2);
    netcdf.putAtt(ncid,varid2,'standard_name','latitude');
    netcdf.putAtt(ncid,varid2,'long_name','latitude');
    netcdf.putAtt(ncid,varid2,'units','degrees_north');
    netcdf.putAtt(ncid,varid2,'axis','Y');
    varid3 = netcdf.defVar(ncid,'st_ocean','double',dimid3);
    netcdf.putAtt(ncid,varid3,'long_name','tcell zstar depth');
    netcdf.putAtt(ncid,varid3,'units','meters');
    netcdf.putAtt(ncid,varid3,'axis','Z');
    varid4 = netcdf.defVar(ncid,'DIC','double',[dimid2,dimid1,dimid3,dimid0]);
    netcdf.putAtt(ncid,varid4,'long_name','dissolved inorganic carbon');
    netcdf.putAtt(ncid,varid4,'units','micromoles kg-1');
    varid5 = netcdf.defVar(ncid,'Alk','double',[dimid2,dimid1,dimid3,dimid0]);
    netcdf.putAtt(ncid,varid5,'long_name','alkalinity');
    netcdf.putAtt(ncid,varid5,'units','micromole equiv. kg-1');
    netcdf.close(ncid)

    ncid = netcdf.open(out_file_name,'NC_WRITE');
    % time referenced to 7/1 at noon of each year
    netcdf.putVar(ncid,varid0,0,1,time_days);
    netcdf.putVar(ncid,varid1,lon);
    netcdf.putVar(ncid,varid2,lat);
    netcdf.putVar(ncid,varid3,depth);
    %netcdf.putVar(ncid,varid4,permute(dic_ann_ts,[4,3,2,1]));
    %netcdf.putVar(ncid,varid4,permute(alk_ann_ts,[4,3,2,1]));
    netcdf.putVar(ncid,varid4,dic_ann);
    netcdf.putVar(ncid,varid5,alk_ann);
    netcdf.close(ncid);

end
