"""
Merit-order electricity market model.

Implements the formulation from Section 3 of the report:
    - Each generator G_i = (Q_i, P_i): capacity Q_i (MW), offer price P_i (EUR/MWh)
    - Generators are sorted by price (cheapest first)
    - Capacity is accepted in order until demand D is satisfied
    - The offer price of the marginal (last accepted) generator sets the
      market clearing price P_market
"""

from dataclasses import dataclass
from typing import List


@dataclass
class Generator:
    name: str
    capacity_mw: float   # Q_i
    price_eur_mwh: float # P_i

    def __repr__(self):
        return f"{self.name} ({self.capacity_mw} MW @ {self.price_eur_mwh} EUR/MWh)"


@dataclass
class ClearingResult:
    market_price: float
    marginal_generator: str
    accepted: dict            # generator name -> MW accepted (q_i)
    demand_satisfied: bool
    total_accepted_mw: float


def clear_market(generators: List[Generator], demand_mw: float) -> ClearingResult:
    """
    Clears the market for a single time period using the merit-order rule.

    Sorts offers from cheapest to most expensive, accepts capacity in that
    order until demand is met, and returns the marginal price.
    """
    if demand_mw < 0:
        raise ValueError("Demand cannot be negative.")

    # Sort cheapest -> most expensive (Eq. 4 in the report)
    ordered = sorted(generators, key=lambda g: g.price_eur_mwh)

    accepted = {}
    remaining = demand_mw
    marginal_price = None
    marginal_name = None

    for gen in ordered:
        if remaining <= 0:
            break
        take = min(gen.capacity_mw, remaining)
        if take > 0:
            accepted[gen.name] = take
            remaining -= take
            marginal_price = gen.price_eur_mwh
            marginal_name = gen.name

    total_accepted = sum(accepted.values())
    demand_satisfied = remaining <= 1e-9

    if not demand_satisfied:
        # Not enough total capacity to meet demand at all.
        marginal_price = None
        marginal_name = "UNMET DEMAND"

    return ClearingResult(
        market_price=marginal_price,
        marginal_generator=marginal_name,
        accepted=accepted,
        demand_satisfied=demand_satisfied,
        total_accepted_mw=total_accepted,
    )
