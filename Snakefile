import yaml
from src.aggregate_pm25 import available_shapefile_year
from hydra import compose, initialize

conda: "requirements.yaml"
configfile: "conf/snakemake.yaml"

# defaults_dict = {key: value for d in config['defaults'] if isinstance(d, dict) for key, value in d.items()}

# polygon_name=config["polygon_name"]
# temporal_freq = config['temporal_freq']

# shapefiles_cfg = yaml.safe_load(open(f"conf/shapefiles/shapefiles.yaml", 'r'))
# satellite_pm25_cfg = yaml.safe_load(open(f"conf/satellite_pm25/us_pm25.yaml", 'r'))

temporal_freq = config['temporal_freq']
polygon_name = config['polygon_name']

with initialize(version_base=None, config_path="conf"):
    cfg = compose(config_name="config", overrides=[f"temporal_freq={temporal_freq}", f"polygon_name={polygon_name}"])

satellite_pm25_cfg = cfg.satellite_pm25
shapefiles_cfg = cfg.shapefiles

shapefile_years_list = list(shapefiles_cfg[polygon_name].keys())

months_list = "01" if temporal_freq == 'yearly' else [str(i).zfill(2) for i in range(1, 12 + 1)]
years_list = list(range(1998, 2023 + 1))

# == Define rules ==
rule all:
    input:
        expand(
            f"{cfg.datapaths.base_path}/output/{polygon_name}_{temporal_freq}/pm25__randall__{polygon_name}_{temporal_freq}__" +  
                ("{year}.parquet" if temporal_freq == 'yearly' else "{year}_{month}.parquet"), 
            year=years_list,
            month=months_list
        )

# remove and use symlink to the us census geoboundaries 
rule download_shapefiles:
    output:
        f"{cfg.datapaths.base_path}/input/shapefiles/shapefile_{polygon_name}_" + "{shapefile_year}/shapefile.shp" 
    shell:
        f"python src/download_shapefile.py polygon_name={polygon_name} " + "shapefile_year={wildcards.shapefile_year}"

rule download_satellite_pm25:
    output:
        expand(
            f"{cfg.datapaths.base_path}/input/raw/{temporal_freq}/{satellite_pm25_cfg[temporal_freq]['file_prefix']}." + 
            ("{year}01-{year}12.nc" if temporal_freq == 'yearly' else "{year}{month}-{year}{month}.nc"), 
            year=years_list,
            month=months_list)
    log:    
        f"logs/download_satellite_pm25_{temporal_freq}.log"
    shell:
        f"python src/download_pm25.py temporal_freq={temporal_freq} " + " &> {log}"

def get_shapefile_input(wildcards):
    shapefile_year = available_shapefile_year(int(wildcards.year), shapefile_years_list)
    return f"{cfg.datapaths.base_path}/input/shapefiles/shapefile_{polygon_name}_{shapefile_year}/shapefile.shp"

rule aggregate_pm25:
    input:
        get_shapefile_input,
        expand(
            f"{cfg.datapaths.base_path}/input/raw/{temporal_freq}/{satellite_pm25_cfg[temporal_freq]['file_prefix']}." + 
            ("{{year}}01-{{year}}12.nc" if temporal_freq == 'yearly' else "{{year}}{month}-{{year}}{month}.nc"), 
            month=months_list
        )

    output:
        expand(
            f"{cfg.datapaths.base_path}/output/{polygon_name}_{temporal_freq}/pm25__randall__{polygon_name}_{temporal_freq}__" + 
            ("{{year}}.parquet" if temporal_freq == 'yearly' else "{{year}}_{month}.parquet"), 
            month=months_list  # we only want to expand months_list and keep year as wildcard
        )
    log:
        f"logs/satellite_pm25_{polygon_name}_{{year}}.log"
    shell:
        (
            f"PYTHONPATH=. python src/aggregate_pm25.py polygon_name={polygon_name} temporal_freq={temporal_freq} " + 
            ("year={wildcards.year}" if temporal_freq == 'yearly' else "year={wildcards.year}") +
            " &> {log}"
        )

rule concat_monthly:
    input:
        expand(
            f"{cfg.datapaths.base_path}/output/{polygon_name}_monthly/pm25__randall__{polygon_name}_monthly__{{year}}_{month}.parquet",
            month=[str(i).zfill(2) for i in range(1, 12 + 1)]
        )
    output:
        yearly_file=f"{cfg.datapaths.base_path}/output/{polygon_name}_monthly/pm25__randall__{polygon_name}_monthly__{{year}}.parquet",
        intermediate_dir=directory(f"{cfg.datapaths.base_path}/output/{polygon_name}_monthly/intermediate")
    log:
        f"logs/concat_monthly_{polygon_name}_{{year}}.log"
    shell:
        f"PYTHONPATH=. python src/concat_monthly.py polygon_name={polygon_name} &> {{log}}"

