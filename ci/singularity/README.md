# build singularity image
```console
singularity build 1d_mom6_cobalt.sif ./build_1d_mom6_cobalt.def
```

# Run the singularity container image in interactive mode
```console
singularity shell --fakeroot -B /home/$USER/work:/work -e 1d_mom6_cobalt.sif 
```
