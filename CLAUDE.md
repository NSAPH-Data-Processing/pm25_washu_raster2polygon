# CLAUDE.md

This file provides guidance to Claude Code (claude.ai/code) when working with code in this repository.

## Project Overview

Environmental data processing pipeline that aggregates Washington University satellite PM2.5 (fine particulate matter) estimates from raster/grid format (NetCDF files) to polygon aggregations (parquet files) for US geographic regions.

## Commands

### Environment Setup
```bash
conda env create -f environment.yaml
conda activate pm25_randall
```

### Running the Pipeline

**Via Snakemake (recommended):**
```bash
snakemake --cores 4 -C polygon_name=county temporal_freq=yearly
```
Options: `polygon_name={county|zcta|census_tract}`, `temporal_freq={yearly|monthly}`

**Manual execution:**
```bash
python src/create_datapaths.py                 # Initialize directory structure/symlinks
python src/download_shapefile.py               # Get US Census shapefiles
python src/download_pm25_dataverse.py          # Download satellite data from Dataverse
export PYTHONPATH=.
python src/aggregate_pm25.py                   # Aggregate PM2.5 to polygons
python src/concat_monthly.py                   # Concatenate monthly files (if temporal_freq=monthly)
```

**Override Hydra config parameters:**
```bash
python src/aggregate_pm25.py polygon_name=zcta temporal_freq=monthly year=2021
python src/create_datapaths.py datapaths=cannon_v6gl
```

## Architecture

### Pipeline Stages
1. **create_datapaths.py** - Creates directory structure and symlinks to lab data repositories (for Cannon cluster)
2. **download_pm25_dataverse.py** - Downloads NetCDF files from Dataverse via API (standalone, run before pipeline)
3. **aggregate_pm25.py** - Core logic: maps polygon geometries to raster cells, computes mean PM2.5 per polygon
4. **concat_monthly.py** - Consolidates 12 monthly parquet files into yearly (only for monthly frequency)

Note: `download_pm25.py` (legacy Box download via Selenium) is deprecated but retained for reference.

### Configuration System (Hydra)
- `conf/config.yaml` - Main config with defaults
- `conf/datapaths/` - Environment-specific paths (V5GL, V6GL, Cannon cluster)
- `conf/shapefiles/shapefiles.yaml` - Polygon metadata (years, ID columns, prefixes)
- `conf/satellite_pm25/` - PM2.5 dataset version configs

### Key Technical Details
- **Shapefile backward compatibility**: `available_shapefile_year()` in `aggregate_pm25.py:19` selects most recent prior shapefile when exact year unavailable
- **Performance optimization**: `utils/faster_zonal_stats.py` pre-computes polygon-to-raster mappings once, reuses for all months
- **Output format**: Parquet files with polygon ID as index, columns: pm25, year (and month for monthly)

### Output File Naming
```
pm25__randall__{polygon_name}_{temporal_freq}__{year}[_{month}].parquet
```

### Data Flow
```
NetCDF (Raster) → Shapefile (Polygons) → Mapping (Cell Indices) → Aggregation (Mean PM2.5) → Parquet
```
