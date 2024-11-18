#!/bin/bash

# How to use:
# To sync with copernicus marine servers
#./get_glorys_data.sh -u USERNAME -p PASSWORD -f "_*199301*" -s
#
# To store files in a directory of your choosing
#./get_glorys_data.sh -u USERNAME -p PASSWORD -o "./datasets/glorys/daily"  -f "_*199301*" -s
#
# If you have already logged in to the service before
#./get_glorys_data.sh -f "_*199301*" -s

# Default values
outdir="./datasets/glorys/daily"
sync=false
interim=false
data_version="202311" # This is the latest avaiable version of glorys as of November 2024

# TODO: add comment to README explaining filter, as well as 
# to top of this script

# Parse command-line arguments
while getopts ":u:p:o:f:sid:" opt; do
  case $opt in
    u) username="$OPTARG";;
    p) password="$OPTARG";;
    o) outdir="$OPTARG";;
    f) filter="$OPTARG";;
    s) sync=true;;
    i) interim=true;;
    d) data_version="$OPTARG";;
    \?) echo "Invalid option: -$OPTARG" >&2; exit 1;;
    :) echo "Option -$OPTARG requires an argument." >&2; exit 1;;
  esac
done

# Check if username and password are provided
if [ -z "$username" ] || [ -z "$password" ]; then
    login=""
else
    login="--username $username --password $password"
fi

# Check if filter is provided, exit if it is not availble
if [ -z "$filter" ] ; then
    echo "ERROR: Please provide a filter for specific files on the copernicusmarine "
    echo "ERROR: server to avoid downloading too many files. More information filtering"
    echo "ERROR: copernicus data can be found here: "
    echo "ERROR: https://help.marine.copernicus.eu/en/articles/7983226-copernicus-marine-toolbox-cli-get-original-files#h_6fca0c5cb2"
    exit 1
fi

# Check if syncing data to servers, or if defining own directories
if [ $sync = true ]; then
    sync=" --sync --dataset-version $data_version " 
else
    sync=" -o $outdir "
fi

# Check if getting Interim product and dataset IDs
if [ $interim = true ]; then
    productId="cmems_mod_glo_phy_myint_0.083deg_P1D-m"
else
    productId="cmems_mod_glo_phy_my_0.083deg_P1D-m"
fi

echo "=========== Starting download ==========="

command="copernicusmarine get -i $productId $login --filter $filter --force-download $sync --log-level DEBUG"
echo -e $command
eval "$command"

echo "=========== Download completed! ==========="
