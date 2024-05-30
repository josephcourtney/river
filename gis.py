import re
from itertools import cycle
from pathlib import Path

import geopandas as gpd
import matplotlib.pyplot as plt
import numpy as np
from jkit.plot import make_plot_grid

# mpl.use("module://jkit.kitty_backend")

dataframes = {}
for path in Path("./data/connecticut/Shape/").glob("GU_*.shp"):
    subwords = list(re.findall(r"[A-Z][a-z]+", path.stem[3:]))  # break up camelcase
    key = "_".join(w.lower() for w in subwords)
    dataframes[key] = gpd.read_file(path)

fig, ax = make_plot_grid(1, 1)

color_cycle = cycle(plt.cm.tab10.colors)


for i, (table, name, size_key, lw, kwargs) in enumerate(
    [
        (
            "county_or_equivalent",
            "county_nam",
            16,
            2.0,
            {"weight": "bold", "alpha": 0.4},
        ),
        ("minor_civil_division", "gnis_name", None, 0.5, {"alpha": 0.5}),
        ("incorporated_place", "place_name", "population", 0.5, {}),
        ("unincorporated_place", "place_name", "population", 0.5, {}),
        ("native_american_area", "name", None, 0.5, {}),
    ],
):
    color = next(color_cycle)
    dataframes[table].boundary.plot(
        ax=ax[0],
        label=table,
        lw=lw,
        color=color,
        zorder=i,
    )
    for _, place in dataframes[table].iterrows():
        if isinstance(size_key, int | float):
            size = size_key
        elif isinstance(size_key, str):
            size = 12 + 1.5 * np.log(
                place[size_key] / dataframes[table][size_key].max(),
            )
        else:
            size = 6

        if isinstance(place[name], str):
            text = ax[0].text(
                place.geometry.centroid.x,
                place.geometry.centroid.y,
                re.sub(r"\s+", "\n", place[name]),
                color=color,
                size=size,
                ha="center",
                va="center",
                **kwargs,
            )


dataframes["state_or_territory"].boundary.plot(
    ax=ax[0],
    label="state_or_territory",
    lw=2.5,
    color="k",
)

ax[0].legend()

plt.show()
