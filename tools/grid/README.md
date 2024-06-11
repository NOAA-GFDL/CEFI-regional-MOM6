# MOM6 grid generation tool 

  

This documentation provides an overview of how we use ESMG gridtools and COSIMA-regional-mom6 gridtools for the MOM6 ocean model. These tools are essential for handling, manipulating, and visualizing grid data in MOM6 simulations. 

  

## [ESMG Gridtools](https://github.com/ESMG/gridtools) 

  

**ESMG (Earth System Modeling Grid) gridtools** are a set of utilities designed to facilitate the handling and manipulation of grid data used in Earth system models, including MOM6. 

### Key Features 
- **Grid Generation and Manipulation**: 
  - Create various types of model grids (rectilinear, curvilinear, etc.). 
  - Interpolate data between different grids. 
  - Adjust grid resolutions. 
    
### Generate grids using ESMG 
- **Set up conda environment**:  
    - clone the repository from GitHub: 
```bash 
git clone https://github.com/ESMG/gridtools.git 
``` 
  - **Create a conda environment**: When creating the conda environemnt, issues might arise from incompatibility between environemnts. [This tutorial](https://github.com/ESMG/gridtools/blob/de0a18c1ce0807748aa70023300dfc415277bd4c/docs/conda/README.md?plain=1#L70) was very helpful providing alternative installation methods. Here I use alternative installation method (2):  

```bash 
conda create -n gridTools python==3.7.10 
conda activate gridTools 
./slow_bootstrap.sh 
``` 
- **Create Jupyter Kernel** 
```bash 
conda install ipykernel 
python -m ipykernel install --user --name gridTools --display-name "Grid Tools Environment" 
``` 
- **Follow tutorials and example notebooks**: The main tutorial is under "examples/mkGridIterative.ipynb" 
    - Examples 3 and 3FRE are great exmaples to create your own grid. 
    - You need [bathymetry](https://github.com/ESMG/gridtools/blob/main/docs/resources/Bathymetry.md) information to generate your own grid. 


## [COSIMA-regional-mom6 Gridtools](https://github.com/COSIMA/regional-mom6)  

**COSIMA (Consortium for Ocean-Sea Ice Modelling in Australia) regional-mom6 gridtools** are specifically tailored for handling regional configurations of the MOM6 ocean model. It is a great method to learn about grid generation, and use the package to generate your own grid,n however, it is best for generating regional horizontal grids with uniform spacing in longitude and latitude, and only supports boundary segments that are parallel to either lines of constant longitude and latitude.  

For a full description and tutorial of these tools go to the following links:  

* [ESMG gridtools](https://github.com/ESMG/gridtools) 

* [COSIMA regional-mom6](https://github.com/COSIMA/regional-mom6)
