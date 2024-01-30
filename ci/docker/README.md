# Build base image
```console
docker build -t 1d_mom6_cobalt:base .
```

# run docker container image in interactive mode 
```console
docker run --mount "type=bind,source=/Users/$USER/work,target=/work" -it 1d_mom6_cobalt:base bash --login
```
