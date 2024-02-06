#!/bin/bash

# How to use
#./get_glorys_data.sh -u USERNAME -p PASSWORD -o "./datasets/glorys/daily" -x -100 -X -35 -y 0 -Y 60 -s "1993-01-01" -e "1993-01-01"

# Default values
outdir="./datasets/glorys/daily"
lon=(-100 -35)
lat=(0 60)
startDate="1993-01-01"
endDate="1993-01-01"
username=""
Password=""

# Parse command-line arguments
while getopts ":u:p:o:x:X:y:Y:s:e:" opt; do
  case $opt in
    u) username="$OPTARG";;
    p) password="$OPTARG";;
    o) outdir="$OPTARG";;
    x) lon[0]="$OPTARG";;
    X) lon[1]="$OPTARG";;
    y) lat[0]="$OPTARG";;
    Y) lat[1]="$OPTARG";;
    s) startDate="$OPTARG";;
    e) endDate="$OPTARG";;
    \?) echo "Invalid option: -$OPTARG" >&2; exit 1;;
    :) echo "Option -$OPTARG requires an argument." >&2; exit 1;;
  esac
done


#check if both username and password are provided
if [ -z "$username" ] || [ -z "$password" ]; then
    echo "Error: Both username and password are required."
    exit 1
fi

# Log in to copernicus Marine
command_string="copernicusmarine login --username $username --password $password"
eval "$command_string"

# Product and dataset IDs
serviceId="GLOBAL_MULTIYEAR_PHY_001_030-TDS"
productId="cmems_mod_glo_phy_my_0.083_P1D-m"

# Variables
variable=("so" "thetao" "uo" "vo" "zos")

# time step
addDays=1

endDate=$(date -d "$endDate + $addDays days" +%Y-%m-%d)

# Time range loop
while [[ "$startDate" != "$endDate" ]]; do

    echo "=============== Date: $startDate ===================="

    command="copernicusmarine subset -i $productId \
    -v ${variable[0]} -v ${variable[1]} -v ${variable[2]} -v ${variable[3]} -v ${variable[4]} \
    -x ${lon[0]} -X ${lon[1]} -y ${lat[0]} -Y ${lat[1]} \
    -t \"$startDate\" -T \"$startDate\" \
    --force-download -o $outdir -f GLORYS_REANALYSIS_$(date -d "$startDate" +%Y-%m-%d).nc"

    echo -e "$command \n============="
    eval "$command"

    startDate=$(date -d "$startDate + $addDays days" +%Y-%m-%d)

done

echo "=========== Download completed! ==========="
