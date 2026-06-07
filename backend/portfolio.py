"""
Portfolio management and validation
Handles portfolio input, storage, and basic metrics
"""

import json
import os
from dataclasses import dataclass, asdict
from typing import List, Dict, Optional
from datetime import datetime
import csv
from io import StringIO

PORTFOLIO_FILE = "portfolio.json"


@dataclass
class Holding:
    """Single holding in portfolio"""
    symbol: str
    quantity: float
    purchase_price: float
    current_price: Optional[float] = None

    @property
    def cost_basis(self) -> float:
        """Total cost of this holding"""
        return self.quantity * self.purchase_price

    @property
    def current_value(self) -> float:
        """Current market value"""
        if not self.current_price:
            return self.cost_basis
        return self.quantity * self.current_price

    @property
    def gain_loss(self) -> float:
        """Dollar gain/loss"""
        return self.current_value - self.cost_basis

    @property
    def gain_loss_pct(self) -> float:
        """Percentage gain/loss"""
        if self.cost_basis == 0:
            return 0
        return (self.gain_loss / self.cost_basis) * 100


@dataclass
class Portfolio:
    """User's complete portfolio"""
    holdings: List[Holding]
    created_at: str
    updated_at: str
    user_id: Optional[str] = None

    @property
    def total_cost_basis(self) -> float:
        """Total invested amount"""
        return sum(h.cost_basis for h in self.holdings)

    @property
    def total_current_value(self) -> float:
        """Current portfolio value"""
        return sum(h.current_value for h in self.holdings)

    @property
    def total_gain_loss(self) -> float:
        """Total dollar gain/loss"""
        return self.total_current_value - self.total_cost_basis

    @property
    def total_gain_loss_pct(self) -> float:
        """Total percentage gain/loss"""
        if self.total_cost_basis == 0:
            return 0
        return (self.total_gain_loss / self.total_cost_basis) * 100

    @property
    def holding_count(self) -> int:
        """Number of holdings"""
        return len(self.holdings)

    @property
    def largest_position_weight(self) -> float:
        """Largest holding as % of portfolio"""
        if self.total_current_value == 0:
            return 0
        return max(
            (h.current_value / self.total_current_value for h in self.holdings),
            default=0
        )

    def get_holding(self, symbol: str) -> Optional[Holding]:
        """Get holding by symbol"""
        for h in self.holdings:
            if h.symbol.upper() == symbol.upper():
                return h
        return None

    def add_holding(self, holding: Holding):
        """Add or update a holding"""
        existing = self.get_holding(holding.symbol)
        if existing:
            # Update existing
            idx = self.holdings.index(existing)
            self.holdings[idx] = holding
        else:
            # Add new
            self.holdings.append(holding)
        self.updated_at = datetime.utcnow().isoformat()

    def remove_holding(self, symbol: str) -> bool:
        """Remove holding by symbol"""
        holding = self.get_holding(symbol)
        if holding:
            self.holdings.remove(holding)
            self.updated_at = datetime.utcnow().isoformat()
            return True
        return False


def parse_csv(csv_content: str) -> List[Holding]:
    """
    Parse CSV content into holdings
    Expected format: Symbol,Quantity,PurchasePrice
    Example:
    AAPL,10,150
    MSFT,5,350
    """
    holdings = []
    reader = csv.DictReader(StringIO(csv_content))

    for row in reader:
        try:
            holding = Holding(
                symbol=row["Symbol"].strip().upper(),
                quantity=float(row["Quantity"]),
                purchase_price=float(row["PurchasePrice"])
            )
            holdings.append(holding)
        except (KeyError, ValueError) as e:
            raise ValueError(f"Invalid CSV format: {e}")

    return holdings


def create_portfolio(holdings: List[Holding], user_id: Optional[str] = None) -> Portfolio:
    """Create new portfolio"""
    now = datetime.utcnow().isoformat()
    return Portfolio(
        holdings=holdings,
        created_at=now,
        updated_at=now,
        user_id=user_id
    )


def validate_portfolio(portfolio: Portfolio) -> Dict[str, any]:
    """Basic portfolio validation"""
    errors = []
    warnings = []

    if len(portfolio.holdings) == 0:
        errors.append("Portfolio is empty")

    if portfolio.total_current_value <= 0:
        errors.append("Portfolio value must be positive")

    # Check for duplicate symbols
    symbols = [h.symbol for h in portfolio.holdings]
    if len(symbols) != len(set(symbols)):
        errors.append("Duplicate holdings detected")

    # Check for invalid quantities
    for h in portfolio.holdings:
        if h.quantity <= 0:
            errors.append(f"{h.symbol}: Quantity must be positive")
        if h.purchase_price <= 0:
            errors.append(f"{h.symbol}: Price must be positive")

    return {
        "valid": len(errors) == 0,
        "errors": errors,
        "warnings": warnings
    }


def save_portfolio(portfolio: Portfolio) -> bool:
    """Save portfolio to JSON file"""
    try:
        data = {
            "created_at": portfolio.created_at,
            "updated_at": portfolio.updated_at,
            "user_id": portfolio.user_id,
            "holdings": [asdict(h) for h in portfolio.holdings]
        }
        with open(PORTFOLIO_FILE, 'w') as f:
            json.dump(data, f, indent=2)
        return True
    except Exception as e:
        print(f"Error saving portfolio: {e}")
        return False


def load_portfolio() -> Optional[Portfolio]:
    """Load portfolio from JSON file"""
    if not os.path.exists(PORTFOLIO_FILE):
        return None

    try:
        with open(PORTFOLIO_FILE, 'r') as f:
            data = json.load(f)

        holdings = [
            Holding(
                symbol=h["symbol"],
                quantity=h["quantity"],
                purchase_price=h["purchase_price"],
                current_price=h.get("current_price")
            )
            for h in data["holdings"]
        ]

        return Portfolio(
            holdings=holdings,
            created_at=data["created_at"],
            updated_at=data["updated_at"],
            user_id=data.get("user_id")
        )
    except Exception as e:
        print(f"Error loading portfolio: {e}")
        return None


def get_sector_weights(portfolio: Portfolio, sector_map: Dict[str, str]) -> Dict[str, float]:
    """
    Calculate sector weights
    sector_map: {symbol: sector}
    """
    sector_values = {}

    for holding in portfolio.holdings:
        sector = sector_map.get(holding.symbol, "Other")
        if sector not in sector_values:
            sector_values[sector] = 0
        sector_values[sector] += holding.current_value

    total = sum(sector_values.values())
    return {
        sector: (value / total) if total > 0 else 0
        for sector, value in sector_values.items()
    }


def get_top_n_concentration(portfolio: Portfolio, n: int = 3) -> float:
    """Calculate concentration of top N holdings"""
    if not portfolio.holdings:
        return 0

    total = portfolio.total_current_value
    if total == 0:
        return 0

    sorted_holdings = sorted(
        portfolio.holdings,
        key=lambda h: h.current_value,
        reverse=True
    )

    top_n_value = sum(h.current_value for h in sorted_holdings[:n])
    return top_n_value / total
