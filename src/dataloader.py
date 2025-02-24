import json
from itertools import product
import time

import hydra
import numpy as np
import torch
import torchvision.transforms as transforms
import xarray as xr
from omegaconf import DictConfig
from torch.utils.data import DataLoader, Dataset
from tqdm import tqdm


class ComponentsWashuDataset(Dataset):
    def __init__(
        self,
        root_dir,
        transform=None,
        components=["pm25", "no3", "so4", "ss", "nh4", "dust", "bc", "om"],
        years=list(range(2000, 2023)),
    ):
        self.root_dir = root_dir
        self.transform = transform
        self.components = components
        self.yyyymm = [
            f"{year}{month:02d}" for year, month in product(years, range(1, 13))
        ]

    def __len__(self):
        return len(self.yyyymm)

    def __getitem__(self, idx):
        yyyymm = self.yyyymm[idx]

        # read files for all components from
        layers = []
        for component in self.components:
            filename = f"{self.root_dir}/{component}/{yyyymm}.nc"
            da = xr.open_dataarray(filename)
            layers.append(da.values)

        tensor = torch.FloatTensor(np.stack(layers, axis=0))

        if self.transform:
            tensor = self.transform(tensor)

        return tensor


@hydra.main(config_path="../conf", config_name="config", version_base=None)
def main(cfg: DictConfig):
    """This script tests the dataloader and saves aggregate statistics in a summary file."""

    components = cfg.dataloader_components
    transform = transforms.Resize(cfg.grid_size)
    # transform = None

    root_dir = "data/input/pm25_components__washu__grid_0_1__dataloader/monthly"
    dataset = ComponentsWashuDataset(
        root_dir=root_dir,
        transform=transform,
        components=components,
    )

    loader = DataLoader(
        dataset,
        batch_size=8,
        shuffle=True,
        num_workers=4,
        pin_memory=True,
        persistent_workers=True,
    )

    # compute the means and standard deviations without storing all the data
    # do not sum nans
    totals_sum = torch.zeros(len(components))
    totals_ss = torch.zeros(len(components))
    totals_n = torch.zeros(len(components))

    # also keep track of time
    start_time = time.time()

    input_size = None
    for batch in tqdm(loader):
        if input_size is None:
            input_size = batch.shape[2:]
        totals_n += (~torch.isnan(batch)).sum(dim=(0, 2, 3))
        x = torch.nan_to_num(batch, nan=0.0)
        totals_sum += x.sum(dim=(0, 2, 3))
        totals_ss += (x**2).sum(dim=(0, 2, 3))

    elapsed_time = time.time() - start_time

    # compute means and stds
    means = totals_sum / totals_n
    stds = torch.sqrt(totals_ss / totals_n - means**2)

    # conver to dict with components as keys
    means_dict = {component: float(mean) for component, mean in zip(components, means)}
    stds_dict = {component: float(std) for component, std in zip(components, stds)}

    # save to file
    summary = {"means": means_dict, "stds": stds_dict, "elapsed_time": elapsed_time, "input_grid_size": input_size}

    summary_file = f"{root_dir}/summary.json"

    with open(summary_file, "w") as f:
        json.dump(summary, f, indent=2)


def example(
    root_dir,
    grid_size=(128, 256),
    components=["pm25", "no3", "so4", "ss", "nh4", "dust", "bc", "om"],
):
    # load summary stats
    with open(f"{root_dir}/summary.json", "r") as f:
        summary = json.load(f)

    means = [summary["means"][component] for component in components]
    stds = [summary["stds"][component] for component in components]

    transform = transforms.Compose(
        [
            transforms.Resize(grid_size),
            transforms.Normalize(mean=means, std=stds),
        ]
    )

    # create torch dataset
    dataset = ComponentsWashuDataset(
        root_dir=root_dir,
        transform=transform,
        components=components,
    )

    # create loader with 4 parallel workers
    loader = DataLoader(
        dataset,
        batch_size=8,
        shuffle=True,
        num_workers=4,
        pin_memory=True,
        persistent_workers=True,
    )

    for batch in loader:
        # training logic here ...
        pass


if __name__ == "__main__":
    main()

