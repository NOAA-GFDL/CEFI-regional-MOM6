#!/bin/bash
podman build -f Dockerfile -t mom6_sis2_generic_4p_compile_symm_yaml:prod
podman save -o mom6_sis2_generic_4p_compile_symm_yaml-prod.tar localhost/mom6_sis2_generic_4p_compile_symm_yaml:prod
apptainer build --disable-cache CEFI_NWA12_COBALT_V1.sif docker-archive://mom6_sis2_generic_4p_compile_symm_yaml-prod.tar
