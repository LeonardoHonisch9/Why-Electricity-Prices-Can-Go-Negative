"""
Parameter sweep for the simplified electricity market.

Question:
    Under what combinations of electricity demand and renewable generation
    do negative electricity prices emerge?

Unlike heatmap_sweep.py (which varies wind and solar capacity independently,
holding demand fixed), this sweep scales wind and solar together -- as a
single "renewable capacity multiplier" -- against demand. That makes it
possible to draw a clean threshold curve: for each demand level, the minimum
renewable capacity multiplier at which negative prices first appear.

Outputs:
    plots/negative_hours_heatmap.png
    plots/negative_price_threshold.png
    plots/sweep_results.csv
"""

import os
import csv

import matplotlib
matplotlib.use("Agg")

import matplotlib.pyplot as plt
import numpy as np

from electricity_market.model import clear_market
from electricity_market.scenarios import build_day, HOURS

OUT_DIR = os.path.join(os.path.dirname(__file__), "plots")
os.makedirs(OUT_DIR, exist_ok=True)

# Demand values tested (MW)
DEMAND_LEVELS = list(range(30, 121, 5))

# Renewable capacity multiplier tested (applied to both wind and solar together)
RENEWABLE_SCALES = np.arange(0.5, 2.51, 0.1)

# Baseline renewable capacity (MW) at multiplier = 1.0
BASE_WIND_PEAK = 50
BASE_SOLAR_PEAK = 40

# Daily demand variation (MW)
DEMAND_SWING = 10

# Baseline point shown on the heatmap
BASELINE_DEMAND = 70
BASELINE_RENEWABLE_SCALE = 1.0


def evaluate_scenario(demand_base, renewable_scale):
    wind_peak = BASE_WIND_PEAK * renewable_scale
    solar_peak = BASE_SOLAR_PEAK * renewable_scale

    demand, hourly_generators = build_day(
        demand_base=demand_base,
        demand_swing=DEMAND_SWING,
        wind_peak=wind_peak,
        solar_peak=solar_peak,
    )

    prices = []
    for h in HOURS:
        result = clear_market(hourly_generators[h], demand[h])
        if result.market_price is not None:
            prices.append(result.market_price)

    if not prices:
        return 0, None, None

    negative_hours = sum(price < 0 for price in prices)
    minimum_price = min(prices)
    average_price = sum(prices) / len(prices)
    return negative_hours, minimum_price, average_price


def run_sweep():
    negative_matrix = []
    results = []

    for renewable_scale in RENEWABLE_SCALES:
        row = []
        for demand_base in DEMAND_LEVELS:
            negative_hours, minimum_price, average_price = evaluate_scenario(
                demand_base, renewable_scale
            )
            row.append(negative_hours)
            results.append({
                "demand_base_MW": demand_base,
                "renewable_scale": round(float(renewable_scale), 2),
                "wind_peak_MW": BASE_WIND_PEAK * renewable_scale,
                "solar_peak_MW": BASE_SOLAR_PEAK * renewable_scale,
                "negative_hours": negative_hours,
                "minimum_price_EUR_MWh": minimum_price,
                "average_price_EUR_MWh": average_price,
            })
        negative_matrix.append(row)

    return np.array(negative_matrix), results


def save_results_csv(results):
    path = os.path.join(OUT_DIR, "sweep_results.csv")
    with open(path, "w", newline="", encoding="utf-8") as file:
        writer = csv.DictWriter(file, fieldnames=results[0].keys())
        writer.writeheader()
        writer.writerows(results)
    print(f"Saved data: {path}")


def find_threshold(negative_matrix):
    """For each demand level, the lowest renewable scale at which any
    negative-price hour appears."""
    threshold_demand = []
    threshold_scale = []

    for demand_index, demand in enumerate(DEMAND_LEVELS):
        for renewable_index, scale in enumerate(RENEWABLE_SCALES):
            if negative_matrix[renewable_index, demand_index] > 0:
                threshold_demand.append(demand)
                threshold_scale.append(scale)
                break

    return threshold_demand, threshold_scale


def plot_heatmap(negative_matrix):
    fig, ax = plt.subplots(figsize=(11, 7))

    image = ax.imshow(
        negative_matrix,
        origin="lower",
        aspect="auto",
        interpolation="nearest",
        extent=[
            min(DEMAND_LEVELS) - 2.5, max(DEMAND_LEVELS) + 2.5,
            min(RENEWABLE_SCALES) - 0.05, max(RENEWABLE_SCALES) + 0.05,
        ],
        vmin=0, vmax=24,
    )

    colorbar = fig.colorbar(image, ax=ax)
    colorbar.set_label("Negative-price hours per day")

    threshold_demand, threshold_scale = find_threshold(negative_matrix)
    if threshold_demand:
        ax.plot(threshold_demand, threshold_scale, linewidth=2.5, linestyle="--",
                 color="white", label="First negative-price hour")

    ax.scatter(
        BASELINE_DEMAND, BASELINE_RENEWABLE_SCALE, s=120, marker="o",
        edgecolors="black", linewidths=1.5, label="Baseline scenario", zorder=5,
        color="white",
    )

    ax.set_xlabel("Base electricity demand (MW)")
    ax.set_ylabel("Renewable capacity multiplier")
    ax.set_title("When Do Negative Electricity Prices Appear?")

    yticks = np.arange(0.5, 2.51, 0.25)
    ax.set_yticks(yticks)
    ax.set_yticklabels([f"{x:.2f}x" for x in yticks])

    ax.legend(loc="upper right", frameon=True)

    fig.tight_layout()
    path = os.path.join(OUT_DIR, "negative_hours_heatmap.png")
    fig.savefig(path, dpi=200)
    plt.close(fig)
    print(f"Saved plot: {path}")


def plot_threshold(negative_matrix):
    threshold_demand, threshold_scale = find_threshold(negative_matrix)

    if not threshold_demand:
        print("No negative-price threshold found within the tested range.")
        return

    fig, ax = plt.subplots(figsize=(9, 5))
    ax.plot(threshold_demand, threshold_scale, marker="o")
    ax.set_xlabel("Base electricity demand (MW)")
    ax.set_ylabel("Minimum renewable capacity multiplier")
    ax.set_title("Threshold for Negative Electricity Prices")
    ax.grid(alpha=0.3)

    yticks = np.arange(0.5, max(threshold_scale) + 0.25, 0.25)
    ax.set_yticks(yticks)
    ax.set_yticklabels([f"{x:.2f}x" for x in yticks])

    fig.tight_layout()
    path = os.path.join(OUT_DIR, "negative_price_threshold.png")
    fig.savefig(path, dpi=200)
    plt.close(fig)
    print(f"Saved plot: {path}")


if __name__ == "__main__":
    print("Running electricity-market parameter sweep...")
    negative_matrix, results = run_sweep()
    save_results_csv(results)
    plot_heatmap(negative_matrix)
    plot_threshold(negative_matrix)
    print("Sweep complete.")
