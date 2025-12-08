FROM condaforge/mambaforge:23.3.1-1

# install build essentials
RUN apt-get update && apt-get install -y build-essential

WORKDIR /app

# Clone your repository
RUN git clone https://github.com/NSAPH-Data-Processing/satellite_pm25_raster2polygon . 

# Update the base environment
RUN mamba env update -n base -f requirements.yaml 
#&& mamba clean -a

# Create paths to data placeholders
RUN python src/create_datapaths.py

# snakemake --configfile conf/config.yaml --cores 4 -C temporal_freq=yearly
ENTRYPOINT ["snakemake", "--configfile", "conf/config.yaml"]
CMD ["--cores", "4", "-C", "polygon_name=county", "temporal_freq=yearly"]
