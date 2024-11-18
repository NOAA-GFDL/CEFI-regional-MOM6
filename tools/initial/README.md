# Downloading CEFI Data Products

## GLORYS
The two scripts available for downloading GLORYS data are `subet_glorys_data.sh` and `get_glorys_data.sh`. The `subset` tool downloads datasets covering a particular geographic region, timespan, and set of variables as a single netcdf file. While this can be convenient when you need to access several variables over a particular region or timespan in a single file, it can also be relatively slow. Additionally, files provided by the `subset` tool are about 3 times larger than the original files stored on the copernicus marine servers, due to a currently unresolved bug in the tool. 

If you would like to download the "original" - i.e the unmodified daily/monthly frequency files covering the entire globe that copernicusmarine produces - you can use `copernicusmarine get` tool instead. This tool downloads the files over `FTP` using multiple threads, making it significantly faster than the `subset` tool; a single months worth of Glorys data across all available variables takes about 5 minutes to download using the `get` tool, which is about the time it takes to download a days worth of data for a single variable using the `subset` tool.

If you need a lot of data covering a large timespan, we recommend using the `get` tool to download the data, and then subsetting it as need afterwards. For downloads covering a smaller geographic region or timespan, the `subset` tool will save you the trouble of downloading the full datasets if you do not need them.

### Using the scripts
Activate your python environment containing the copernicusmarine package. 

To run the `subset` tool, fill in the following variables written in all caps: 
```
./subset_glorys_data.sh -u USERNAME -p PASSWORD -o OUTPUT_DIR -x LAT_LOWER_BOUND -X LAT_UPPER_BOUND -y LON_LOWER_BOUND -Y LON_UPPER_BOUND -s START_DATE -e END_DATE
```
Note that most copernicusmarine tools will attempt to verify your credentials before running any command. Once you have logged in once, the copernicusmarine tool will cache your login information, meaning you do not have to pass in a username or password again. 

The `get` tool gives you the option to download the files in a directory structure that mimics the structure used by `copernicus marine` to make it easier to sync your local files with their servers. If you would like to download you file in this manner, use the command: 
```
./get_glorys_data.sh -u USERNAME -p PASSWORD -f FILTER -s
```

where the `-s` flag will sync your files with the server files. The filter string is a regular expression selecting data for a particular date range. For example, if you wanted to download all data for Jan 1993, you can do so use the command "*_199301*". If you wanted to download all data for the first week of September 2020, you could do so as follows: "*_2020090[1-7]*". Most regular expression syntax is supported - see the copernicus marine website for more details.

If you would prefer to use your own directory structure to download GLORYS data, you can do so as follows: 
```
./get_glorys_data.sh -u USERNAME -p PASSWORD -o "./datasets/glorys/daily"  -f "_*199301*"
```
As always, feel free to omit the username and password if you login details are cached. 

# Writing initial conditions
Work in Progress!
