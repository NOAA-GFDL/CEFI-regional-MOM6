# Build base image
docker build -t 1d_mom6_cobalt:base .

# run docker container image in interactive mode 
docker run --mount "type=bind,source=/Users/$USER/work,target=/work" -it 1d_mom6_cobalt:base bash --login
