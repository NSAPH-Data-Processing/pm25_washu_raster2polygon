# satellite_pm25_raster2polygon

Code to produce spatial aggregations of pm25 estimates as generated by the [Atmospheric Composition Analysis Group](https://sites.wustl.edu/acag/datasets/surface-pm2-5/). The spatial aggregation are performed for satellite pm25 from grid/raster (NetCDF) to polygons (shp).

---

# Satellite PM25

The [Atmospheric Composition Analysis Group](https://sites.wustl.edu/acag/datasets/surface-pm2-5/) uses a combination of satellite images, monitors and simulation to generate estimates of pm25. Estimates are stored in NetCDF files and made publicly available. There are several versions of the estimates.

The version [V5.GL.04](https://sites.wustl.edu/acag/datasets/surface-pm2-5/#V5.GL.04) consists of mean PM2.5 (ug/m3) available at:

*  Temporal frequency: Annual and monthly  
*  Grid resolutions: (0.1° × 0.1°) and (0.01° × 0.01°)  
*  Geographic regions: North America, Europe, Asia, and Global

In this repository, we specifically aggregate the V5.GL.04 files for North America only, but parameters can be modified to change the temporal frequency and grid resolution of interest. 

The file name convention is V5GL04.HybridPM25.NorthAmerica.yyyymm-yyyymm.nc e.g. V5GL04.HybridPM25.NorthAmerica.201801-201812.nc is the file for 2018 and:
* "V5GL04.HybridPM25.NorthAmerica" is the lower resolution filename prefix
* "V5GL04.HybridPM25c_0p10.NorthAmerica" is the higher resolution filename prefix

More information on parameters is shown below.

## References:
Aaron van Donkelaar, Melanie S. Hammer, Liam Bindle, Michael Brauer, Jeffery R. Brook, Michael J. Garay, N. Christina Hsu, Olga V. Kalashnikova, Ralph A. Kahn, Colin Lee, Robert C. Levy, Alexei Lyapustin, Andrew M. Sayer and Randall V. Martin (2021). Monthly Global Estimates of Fine Particulate Matter and Their Uncertainty Environmental Science & Technology, 2021, [doi:10.1021/acs.est.1c05309](https://pubs.acs.org/doi/10.1021/acs.est.1c05309).

---

# Codebook

## Dataset Columns:

* county aggregations:

* zcta aggregations:

---

# Configuration files

The configuration structure withing the `/conf` folder allow you to modify the input parameters for the following steps:

* create directory paths: `utils/create_dir_paths.py`
* download pm25: `src/download_pm25.py`
* download shapefiles: `src/download_shapefile.py`
* aggregate pm25: `src/aggregate_pm25.py`

The key parameters are:
* `temporal_freq` which determines whether the original annual or monthly pm25 files will be aggregated. The options are: `annual` and `monthly`.
* `polygon_name` which determines into which polygons the pm25 grid will the aggregated. The options are: `zcta` and `county`.

---

# Run

## Conda environment

Clone the repository and create a conda environment.

```bash
git clone <https://github.com/<user>/repo>
cd <repo>

conda env create -f requirements.yml
conda activate <env_name> #environment name as found in requirements.yml
```

It is also possible to use `mamba`.

```bash
mamba env create -f requirements.yml
mamba activate <env_name>
```

## Input and output paths

Run

```bash
python utils/create_dir_paths.py 
```

## Pipeline

You can run the pipeline steps manually or run the snakemake pipeline described in the Snakefile.

**run pipeline steps manually**

```bash
python src/download_shapefile.py
python src/download_pm25.py
python src/aggregate_pm25.py
```

**run snakemake pipeline**
or run the pipeline:

```bash
snakemake --cores 4 -C polygon_name=county temporal_freq=annual 
```

Modify `cores`, `polygon_name` and `temporal_freq` as you find convenient.

## Dockerized Pipeline

Create the folder where you would like to store the output dataset.

```bash 
mkdir <path>/satellite_pm25_raster2polygon
```

### Pull and Run:

```bash
docker pull nsaph/satellite_pm25_raster2polygon
docker run -v <path>:/app/data/input/satellite_pm25/annual <path>/satellite_pm25_raster2polygon/:/app/data/output/satellite_pm25_raster2polygon nsaph/satellite_pm25_raster2polygon
```  

If you are interested in storing the input raw and intermediate data run

```bash
docker run -v <path>/satellite_pm25_raster2polygon/:/app/data/ nsaph/satellite_pm25_raster2polygon
```

If you want to build your own image use
```
docker build -t <image_name> .
```

For multiplatform use
```
docker buildx build --platform linux/amd64,linux/arm64 -t <username>/<image_name>:<tag> . --push
```
