import os
import hydra
import logging
import numpy as np
import xarray as xr

logger = logging.getLogger(__name__)


MONTH_MAP = {
    "JAN": 1,
    "FEB": 2,
    "MAR": 3,
    "APR": 4,
    "MAY": 5,
    "JUN": 6,
    "JUL": 7,
    "AUG": 8,
    "SEP": 9,
    "OCT": 10,
    "NOV": 11,
    "DEC": 12,
}


@hydra.main(config_path="../conf", config_name="config", version_base=None)
def main(cfg):
    """
    Download yearly V5 satellite PM2.5 components data from Washington University's Atmospheric Composition Analysis Group.
    https://sites.wustl.edu/acag/datasets/surface-pm2-5/
    """

    # == url for download and save dirs
    component = cfg.component
    resolution = cfg.resize_resolution

    download_dir = f"data/input/pm25_components__washu__raw/{cfg.temporal_freq}/"
    src_dir = f"{download_dir}/{component}"

    resolution_str = str(cfg.resize_resolution).replace(".", "_")
    tgt_dir = f"data/input/pm25_components__washu__grid_{resolution_str}__dataloader/{cfg.temporal_freq}/{component}/"

    # loop over all file contents that read every netcdf
    for filename in os.listdir(src_dir):
        if not filename.endswith(".nc"):
            continue

        # read the netcdf file
        file_path = os.path.join(src_dir, filename)
        ds = xr.open_dataset(file_path, engine="h5netcdf")

        # resize the grids
        # lon = ds[cfg.satellite_component.longitude_layer].values
        # lat = ds[cfg.satellite_component.latitude_layer].values
        # lonmin, lonmax = lon.min(), lon.max()
        # latmin, latmax = lat.min(), lat.max()
        # new_lon = np.arange(lonmin, lonmax, resolution)
        # new_lat = np.arange(latmin, latmax, resolution)
        new_lat = np.arange(cfg.bbox.min_lat, cfg.bbox.max_lat, resolution)
        new_lon = np.arange(cfg.bbox.min_lon, cfg.bbox.max_lon, resolution)

        # interpolate ds, uses bilinear interpolation by default
        new_dict = {
            cfg.satellite_component.longitude_layer: new_lon,
            cfg.satellite_component.latitude_layer: new_lat,
        }
        ds = ds.interp(**new_dict)
        
        # update Delta_Lat and Delta_Lon attributes in the dataset
        # ds.attrs["Delta_Lat"] = resolution
        # ds.attrs["Delta_Lon"] = resolution

        # extract year and name from the filename
        # filename pattern V5NA04.02.HybridSO4-SO4.NorthAmerica.yyyy-yyyy-MMM.nc
        yyyy, _, mmm = filename.split(".")[-2].split("-")
        year = int(yyyy)
        month = MONTH_MAP[mmm]
        tgt_filename = f"{year}{month:02d}.nc"

        # standardize layer name
        layer_name = cfg.satellite_component.layer[component]
        ds = ds.rename({layer_name: "values"})
        ds = ds["values"]

        # save the processed data
        os.makedirs(tgt_dir, exist_ok=True)
        ds.to_netcdf(f"{tgt_dir}/{tgt_filename}")


if __name__ == "__main__":
    main()
