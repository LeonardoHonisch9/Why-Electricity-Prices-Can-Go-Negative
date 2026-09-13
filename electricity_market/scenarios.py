"""
Builds a 24-hour scenario: wind and solar output profiles, an electricity
demand profile with a typical daily shape (night valley, morning/evening
peaks), and fixed conventional generators (nuclear baseload, gas peaker).

The point is to reproduce, in a simplified way, the conditions that create
negative prices in real markets: a sunny/windy midday combined with the
demand valley that happens on a mild weekend day.
"""

import math
from .model import Generator

HOURS = list(range(24))


def demand_profile(low_demand_day: bool = False, base: float = None, swing: float = None):
    """
    Simple two-peak daily demand curve (MW), roughly: valley at night,
    peak in the morning and evening. `low_demand_day` mimics a mild
    weekend/holiday with lower overall demand. Pass `base`/`swing`
    directly for finer control (e.g. an extreme low-demand holiday).
    """
    if base is None:
        base = 70 if low_demand_day else 100
    if swing is None:
        swing = 15 if low_demand_day else 30
    demand = []
    for h in HOURS:
        # two peaks: ~8am and ~19h, valley around 4am
        wave = (
            0.6 * math.sin((h - 4) / 24 * 2 * math.pi * 2)
            + 0.4 * math.sin((h - 8) / 24 * 2 * math.pi)
        )
        demand.append(round(base + swing * wave, 1))
    return demand


def wind_profile(windy_day: bool = False, peak: float = None):
    """Wind capacity available each hour (MW). Wind doesn't follow the sun,
    modeled here as a slow-moving, mostly-flat profile with noise-like bumps."""
    if peak is None:
        peak = 55 if windy_day else 25
    return [round(peak * (0.7 + 0.3 * math.sin(h / 24 * 2 * math.pi + 1)), 1) for h in HOURS]


def solar_profile(sunny_day: bool = False, peak: float = None):
    """Solar capacity available each hour (MW): zero at night, bell curve at midday."""
    if peak is None:
        peak = 60 if sunny_day else 25
    profile = []
    for h in HOURS:
        if 6 <= h <= 19:
            profile.append(round(peak * math.sin((h - 6) / 13 * math.pi), 1))
        else:
            profile.append(0.0)
    return profile


def build_generators(hour_index, wind_cap, solar_cap, wind_price=-10, solar_price=0):
    """
    Returns the list of Generator offers for a given hour, following the
    same offer prices used in the report's worked example (Section 2.3):
    Wind -10 EUR/MWh, Solar 0 EUR/MWh, Nuclear 40 EUR/MWh, Gas 100 EUR/MWh.
    """
    return [
        Generator("Wind Farm", wind_cap[hour_index], wind_price),
        Generator("Solar Farm", solar_cap[hour_index], solar_price),
        Generator("Nuclear Plant", 50, 40),
        Generator("Gas Plant", 60, 100),
    ]


def build_day(low_demand_day=False, windy_day=False, sunny_day=False,
              wind_price=-10, solar_price=0,
              demand_base=None, demand_swing=None, wind_peak=None, solar_peak=None):
    """
    Assembles a full 24-hour scenario: for each hour, returns the demand,
    the generator offers, and (later, via simulate.py) the clearing result.
    """
    demand = demand_profile(low_demand_day, base=demand_base, swing=demand_swing)
    wind_cap = wind_profile(windy_day, peak=wind_peak)
    solar_cap = solar_profile(sunny_day, peak=solar_peak)

    hourly_generators = [
        build_generators(h, wind_cap, solar_cap, wind_price, solar_price)
        for h in HOURS
    ]
    return demand, hourly_generators
