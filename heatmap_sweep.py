"""
Investigates the report's central question directly: how does the number of
negative-price hours per day depend on installed renewable capacity?

Produces a heatmap over (wind peak capacity, solar peak capacity), holding
demand and conventional-generator prices fixed, colored by the number of
hours per day the market clears below zero. Saves plots/heatmap.png.
"""

import os
import numpy as np
import matplotlib
matplotlib.use("Agg")
import matplotlib.pyplot as plt

from electricity_market.model import clear_market
from electricity_market.scenarios import build_generators, demand_profile, wind_profile, solar_profile, HOURS

OUT_DIR = os.path.join(os.path.dirname(__file__), "plots")
os.makedirs(OUT_DIR, exist_ok=True)

RESOLUTION = 40  # grid points per axis


def negative_hours_for(wind_peak, solar_peak, demand_base=80, demand_swing=20,
                        nuclear_price=40, gas_price=100):
    demand = demand_profile(base=demand_base, swing=demand_swing)
    wind_cap = wind_profile(peak=wind_peak)
    solar_cap = solar_profile(peak=solar_peak)

    count = 0
    for h in HOURS:
        gens = [
            *[g for g in build_generators(h, wind_cap, solar_cap)
              if g.name in ("Wind Farm", "Solar Farm")],
        ]
        # override nuclear/gas prices per function args
        from electricity_market.model import Generator
        gens.append(Generator("Nuclear Plant", 50, nuclear_price))
        gens.append(Generator("Gas Plant", 60, gas_price))

        result = clear_market(gens, demand[h])
        if result.market_price is not None and result.market_price < 0:
            count += 1
    return count


def build_heatmap(demand_base=80, demand_swing=20):
    wind_range = np.linspace(0, 100, RESOLUTION)
    solar_range = np.linspace(0, 100, RESOLUTION)
    grid = np.zeros((RESOLUTION, RESOLUTION))

    for j, solar_peak in enumerate(solar_range):
        for i, wind_peak in enumerate(wind_range):
            grid[j, i] = negative_hours_for(
                wind_peak, solar_peak, demand_base=demand_base, demand_swing=demand_swing
            )
    return wind_range, solar_range, grid


def plot_heatmap(wind_range, solar_range, grid, title, filename):
    fig, ax = plt.subplots(figsize=(7, 6))
    im = ax.pcolormesh(wind_range, solar_range, grid, shading="auto", cmap="viridis")
    cbar = fig.colorbar(im, ax=ax)
    cbar.set_label("Hours per day with negative price")
    ax.set_xlabel("Wind capacity (MW)")
    ax.set_ylabel("Solar capacity (MW)")
    ax.set_title(title)
    fig.tight_layout()
    path = os.path.join(OUT_DIR, filename)
    fig.savefig(path, dpi=150)
    plt.close(fig)
    print(f"Saved: {path}")


if __name__ == "__main__":
    # Fixed, moderate demand -- shows the pure effect of renewable capacity.
    wind_range, solar_range, grid = build_heatmap(demand_base=80, demand_swing=20)
    plot_heatmap(
        wind_range, solar_range, grid,
        "Negative-price hours vs. renewable capacity\n(demand fixed at 80 MW ± 20 MW)",
        "heatmap.png",
    )

    # Lower demand -- shows the same renewable capacity produces MORE
    # negative hours once overall demand is lower, confirming both factors
    # (renewables AND demand level) matter together.
    wind_range2, solar_range2, grid2 = build_heatmap(demand_base=50, demand_swing=10)
    plot_heatmap(
        wind_range2, solar_range2, grid2,
        "Negative-price hours vs. renewable capacity\n(low demand: 50 MW ± 10 MW)",
        "heatmap_low_demand.png",
    )
