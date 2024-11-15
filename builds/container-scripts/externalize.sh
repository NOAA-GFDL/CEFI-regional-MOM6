#!/bin/bash

################################################################################
# Help                                                                         #
################################################################################
Help()
{
   # Display Help
   echo "Add description of the script functions here."
   echo
   echo "Syntax: scriptTemplate [-|h|e|p]"
   echo "options:"
   echo "-h     Print this Help."
   echo "-e     Create the external executable in the user-specified folder"
   echo "-p     env file that contains the necessary modules within the container"
   echo
}

################################################################################
################################################################################
# Main program                                                                 #
################################################################################
################################################################################
################################################################################
# Process the input options. Add options as needed.                            #
################################################################################
# Get the options
#while getopts ":hep" option; do
#   case $option in
#      h) # display Help
#         Help
#         exit;;
#      e) # external directory to hold externalized executables
#         exec_dir=$2
#         echo "Will create external executable in $exec_dir"
#      p) # env file that contains the necessary modules inside the container
#         env_file=$3
#	 echo "Will load modules in $env_file" 
#               
#   esac
#done
#shift $(($OPTIND ))

while getopts ":he:p:" option; do
   case $option in
      h) # display Help
         Help
         exit
         ;;
      e) # external directory to hold externalized executables
         exec_dir=$OPTARG
         echo "Will create external executable in $exec_dir"
         ;;
      p) # env file that contains the necessary modules inside the container
         env_file=$OPTARG
         echo "Will load modules in $env_file"
         ;;
   esac
done

# Shift past the processed options
shift $((OPTIND -1))


fileList=$@

source $env_file
mkdir -p $exec_dir
cp /opt/container-scripts/run_container_executable.sh $exec_dir
cp /opt/container-scripts/build_container_executable.sh $exec_dir
#replace the paths in the script
sed -i "s|IMAGE|$SINGULARITY_CONTAINER|g" $exec_dir/*_executable.sh
nbinds=`echo $SINGULARITY_BIND | awk -F "," '{print NF }'`
bindstring=" "
for (( i = 1; i <= $nbinds; i++ )); do binddir=`echo $SINGULARITY_BIND | cut -d "," -f $i` && bindstring="${bindstring} -B ${binddir}" ; done
echo $bindstring
sed -i "s|BINDDIRS|$bindstring|g" $exec_dir/*_executable.sh
sed -i "s|LDLIB_PATH|$LD_LIBRARY_PATH|g" $exec_dir/*_executable.sh
sed -i "s|LIB_PATH|$LIBRARY_PATH|g" $exec_dir/*_executable.sh
sed -i "s|FI_PATH|$FI_PROVIDER_PATH|g" $exec_dir/*_executable.sh

for file in $fileList
do
  fullfile=$(readlink -m $file)
  basefile=$(basename "$fullfile")
  cp $exec_dir/run_container_executable.sh $exec_dir/$basefile
  pathdir=$(dirname $fullfile)
  echo "fullfile is $fullfile"
  echo $pathdir
 
  EXEC_PATH="$pathdir:$PATH"
  sed -i "s|EXEC_PATH|$EXEC_PATH|g" $exec_dir/$basefile
  sed -i "s|ESMF_MK|$ESMFMKFILE|g" $exec_dir/$basefile
done
#fileList="make cmake ecbuild python python3"
fileList=""
for file in $fileList
do
  fullfile=$(which $file)
  basefile=$(basename "$fullfile")
  cp $exec_dir/build_container_executable.sh $exec_dir/$basefile
  pathdir=$(dirname $fullfile)
 
  EXEC_PATH="$pathdir:$PATH"
  sed -i "s|EXEC_PATH|$EXEC_PATH|g" $exec_dir/$basefile
  sed -i "s|CMAKE_PREPATH|$CMAKE_PREFIX_PATH|g" $exec_dir/$basefile
  sed -i "s|ESMF_MK|$ESMFMKFILE|g" $exec_dir/$basefile
done

chmod +x $exec_dir/*
