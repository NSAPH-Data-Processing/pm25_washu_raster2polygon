#!/usr/bin/env python3
"""
Consolidate monthly PM2.5 aggregation files into yearly files.

This script takes the monthly parquet files from the intermediate directory
and combines all 12 months for each year into a single yearly file in the output directory.

Usage:
    python src/concat_monthly.py year=2020
    
    # With overrides:
    python src/concat_monthly.py polygon_name=zcta year=2020
"""

import pandas as pd
import os
import hydra
import logging
from pathlib import Path

logging.basicConfig(level=logging.INFO, format='[%(asctime)s][%(levelname)s] - %(message)s')
LOGGER = logging.getLogger(__name__)


def consolidate_year(intermediate_dir, output_dir, year, polygon_name, input_freq="monthly"):
    """
    Consolidate all monthly files for a given year into a single yearly file.
    Reads from intermediate directory, outputs to main output directory.
    
    Args:
        intermediate_dir: Directory containing monthly parquet files
        output_dir: Directory to save yearly parquet file
        year: Year to consolidate
        polygon_name: Name of polygon type (county, zcta, etc.)
        input_freq: Frequency of input files (monthly)
    
    Returns:
        List of monthly files that were consolidated
    """
    monthly_files = []
    
    # Pattern: pm25__randall__county_monthly__2020_01.parquet
    # Collect all monthly files for this year from intermediate directory
    for month in range(1, 13):
        month_str = str(month).zfill(2)
        filename = f"pm25__randall__{polygon_name}_{input_freq}__{year}_{month_str}.parquet"
        filepath = os.path.join(intermediate_dir, filename)
        
        if os.path.exists(filepath):
            monthly_files.append(filepath)
        else:
            LOGGER.warning(f"Missing file: {filepath}")
    
    if not monthly_files:
        LOGGER.error(f"No monthly files found for year {year} in {intermediate_dir}")
        raise FileNotFoundError(f"No monthly files found for year {year}")
    
    if len(monthly_files) != 12:
        LOGGER.warning(f"Only found {len(monthly_files)}/12 months for year {year}")
    
    # Read and concatenate all monthly files
    LOGGER.info(f"Reading {len(monthly_files)} monthly files for year {year}")
    dfs = [pd.read_parquet(f) for f in monthly_files]
    yearly_df = pd.concat(dfs, ignore_index=False)
    
    # Sort by polygon ID and month for consistent ordering
    if 'month' in yearly_df.columns:
        yearly_df = yearly_df.sort_values(['month'])
    
    # Save yearly file to output directory (not intermediate)
    # Pattern: pm25__randall__county_monthly__2020.parquet
    output_file = os.path.join(output_dir, f"pm25__randall__{polygon_name}_monthly__{year}.parquet")
    LOGGER.info(f"Saving consolidated file: {output_file} ({len(yearly_df)} rows)")
    yearly_df.to_parquet(output_file)
    
    return monthly_files




@hydra.main(config_path="../conf", config_name="config", version_base=None)
def main(cfg):
    """
    Consolidate monthly PM2.5 files for a specific year into a yearly file using Hydra configuration.
    Reads from intermediate directory, outputs to main output directory.
    """
    
    polygon_name = cfg.polygon_name
    year = cfg.year
    
    # Build paths using datapaths configuration
    monthly_dir = f"{cfg.datapaths.base_path}/output/{polygon_name}_monthly"
    intermediate_dir = f"{monthly_dir}/intermediate"
    
    LOGGER.info(f"Polygon name: {polygon_name}")
    LOGGER.info(f"Year: {year}")
    LOGGER.info(f"Input directory (intermediate): {intermediate_dir}")
    LOGGER.info(f"Output directory: {monthly_dir}")
    
    # Process the specified year
    try:
        monthly_files = consolidate_year(intermediate_dir, monthly_dir, year, polygon_name)
        LOGGER.info(f"Successfully consolidated {len(monthly_files)} monthly files for year {year}")
        
    except Exception as e:
        LOGGER.error(f"Error processing year {year}: {e}")
        raise


if __name__ == "__main__":
    main()
