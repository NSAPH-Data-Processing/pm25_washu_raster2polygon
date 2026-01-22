import os
import requests
import hydra
import logging
from tqdm import tqdm

logger = logging.getLogger(__name__)

@hydra.main(config_path="../conf", config_name="config", version_base=None)
def main(cfg):
    """
    Download PM2.5 NetCDF files from Dataverse.

    This script downloads satellite PM2.5 data that has been uploaded to Dataverse,
    replacing the previous Box-based download mechanism.
    """

    # == Dataverse configuration
    dataverse_cfg = cfg.satellite_pm25[cfg.temporal_freq].dataverse

    server_url = dataverse_cfg.server_url
    doi = dataverse_cfg.doi
    api_token = dataverse_cfg.get("api_token", None)  # Optional, for restricted datasets

    # == Setup output directory
    download_dir = f"{cfg.datapaths.base_path}/input/raw/{cfg.temporal_freq}"
    os.makedirs(download_dir, exist_ok=True)

    logger.info(f"Downloading from Dataverse: {server_url}")
    logger.info(f"DOI: {doi}")
    logger.info(f"Output directory: {download_dir}")

    # == Get dataset files list from Dataverse API
    # API endpoint: /api/datasets/:persistentId/?persistentId=doi:DOI
    dataset_url = f"{server_url}/api/datasets/:persistentId/?persistentId={doi}"

    headers = {}
    if api_token:
        headers["X-Dataverse-key"] = api_token

    try:
        response = requests.get(dataset_url, headers=headers)
        response.raise_for_status()
        dataset_info = response.json()

        if dataset_info.get("status") != "OK":
            raise ValueError(f"Dataverse API error: {dataset_info}")

        # Extract file list from dataset metadata
        files = dataset_info["data"]["latestVersion"]["files"]
        logger.info(f"Found {len(files)} files in dataset")

        # == Download each NetCDF file
        file_prefix = cfg.satellite_pm25[cfg.temporal_freq].file_prefix

        for file_info in tqdm(files, desc="Downloading files"):
            filename = file_info["dataFile"]["filename"]
            file_id = file_info["dataFile"]["id"]

            # Filter to only download files matching our prefix (NetCDF files)
            if not filename.startswith(file_prefix):
                logger.debug(f"Skipping {filename} (doesn't match prefix {file_prefix})")
                continue

            if not filename.endswith(".nc"):
                logger.debug(f"Skipping {filename} (not a NetCDF file)")
                continue

            output_path = os.path.join(download_dir, filename)

            # Skip if file already exists
            if os.path.exists(output_path):
                logger.info(f"Skipping {filename} (already exists)")
                continue

            # Download file
            # API endpoint: /api/access/datafile/:id
            file_url = f"{server_url}/api/access/datafile/{file_id}"

            logger.info(f"Downloading {filename}...")
            file_response = requests.get(file_url, headers=headers, stream=True)
            file_response.raise_for_status()

            # Write file with progress
            total_size = int(file_response.headers.get("content-length", 0))
            with open(output_path, "wb") as f:
                if total_size == 0:
                    f.write(file_response.content)
                else:
                    for chunk in file_response.iter_content(chunk_size=8192):
                        f.write(chunk)

            logger.info(f"Downloaded {filename}")

        logger.info("Download completed successfully.")

    except requests.exceptions.RequestException as e:
        logger.error(f"Failed to download from Dataverse: {e}")
        raise
    except KeyError as e:
        logger.error(f"Unexpected Dataverse API response format: {e}")
        raise


if __name__ == "__main__":
    main()
