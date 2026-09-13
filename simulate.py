"""
Runs two 24-hour scenarios through the merit-order model:

  1. "Typical day": moderate wind/solar, normal demand.
  2. "Negative price day": sunny + windy + low demand (e.g. a mild spring
     Sunday) -- the conditions the report identifies as the cause of
     negative prices.

Produces:
  - A printed hour-by-hour summary of clearing prices
  - plots/typical_day.png
  - plots/negative_price_day.png
  - plots/comparison.png
"""

import os
import matplotlib
matplotlib.use("Agg")
import matplotlib.pyplot as plt

from electricity_market.model import clear_market
from electricity_market.scenarios import build_day, HOURS

OUT_DIR = os.path.join(os.path.dirname(__file__), "plots")
os.makedirs(OUT_DIR, exist_ok=True)


def run_scenario(label, **scenario_kwargs):
    demand, hourly_generators = build_day(**scenario_kwargs)
    prices = []
    marginal_gens = []
    for h in HOURS:
        result = clear_market(hourly_generators[h], demand[h])
        prices.append(result.market_price)
        marginal_gens.append(result.marginal_generator)

    print(f"\n=== {label} ===")
    for h in HOURS:
        flag = "  <-- NEGATIVE PRICE" if prices[h] is not None and prices[h] < 0 else ""
        print(f"h={h:02d}  demand={demand[h]:6.1f} MW  "
              f"price={prices[h]:7.2f} EUR/MWh  marginal={marginal_gens[h]:<14}{flag}")

    n_negative = sum(1 for p in prices if p is not None and p < 0)
    print(f"Hours with negative price: {n_negative}/24")

    return demand, prices, marginal_gens


def plot_scenario(label, demand, prices, filename):
    fig, ax1 = plt.subplots(figsize=(9, 4.5))

    ax1.set_xlabel("Hour of day")
    ax1.set_ylabel("Demand (MW)", color="tab:blue")
    ax1.plot(HOURS, demand, color="tab:blue", marker="o", label="Demand")
    ax1.tick_params(axis="y", labelcolor="tab:blue")

    ax2 = ax1.twinx()
    ax2.set_ylabel("Market clearing price (EUR/MWh)", color="tab:red")
    ax2.plot(HOURS, prices, color="tab:red", marker="s", label="Market price")
    ax2.axhline(0, color="gray", linewidth=0.8, linestyle="--")
    ax2.tick_params(axis="y", labelcolor="tab:red")

    plt.title(label)
    fig.tight_layout()
    path = os.path.join(OUT_DIR, filename)
    fig.savefig(path, dpi=150)
    plt.close(fig)
    print(f"Saved plot: {path}")


def plot_comparison(prices_a, label_a, prices_b, label_b, filename):
    fig, ax = plt.subplots(figsize=(9, 4.5))
    ax.plot(HOURS, prices_a, marker="o", label=label_a)
    ax.plot(HOURS, prices_b, marker="s", label=label_b)
    ax.axhline(0, color="gray", linewidth=0.8, linestyle="--")
    ax.set_xlabel("Hour of day")
    ax.set_ylabel("Market clearing price (EUR/MWh)")
    ax.set_title("Market price: typical day vs. negative-price day")
    ax.legend()
    fig.tight_layout()
    path = os.path.join(OUT_DIR, filename)
    fig.savefig(path, dpi=150)
    plt.close(fig)
    print(f"Saved plot: {path}")


if __name__ == "__main__":
    demand_typ, prices_typ, _ = run_scenario(
        "Typical day (moderate wind/solar, normal demand)",
        low_demand_day=False, windy_day=False, sunny_day=False,
    )
    plot_scenario("Typical day", demand_typ, prices_typ, "typical_day.png")

    demand_neg, prices_neg, _ = run_scenario(
        "Negative-price day (holiday demand + strong wind + full sun)",
        demand_base=48, demand_swing=8,   # e.g. a mild public holiday
        wind_peak=70, solar_peak=65,
    )
    plot_scenario("Negative-price day", demand_neg, prices_neg, "negative_price_day.png")

    plot_comparison(prices_typ, "Typical day", prices_neg, "Negative-price day",
                     "comparison.png")
