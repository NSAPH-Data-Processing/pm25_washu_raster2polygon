#!/bin/bash
#
#SBATCH -p serial_requeue # partition (queue)
#SBATCH -c 48 # number of cores 
#SBATCH --mem 184GB # memory 
#SBATCH -t 0-12:00 # time (D-HH:MM)

#singularity exec $HOME/singularity_images/satellite_pm25_raster2polygon_latest.sif snakemake --cores 16 -C polygon_name=county temporal_freq=monthly

snakemake --cores 24 -C polygon_name=county temporal_freq=yearly
snakemake --cores 24 -C polygon_name=county temporal_freq=monthly
snakemake --cores 24 -C polygon_name=zcta temporal_freq=yearly
snakemake --cores 24 -C polygon_name=zcta temporal_freq=monthly
