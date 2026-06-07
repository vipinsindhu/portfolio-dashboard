"""
Educational content engine for Learn tab
Provides interactive lessons on common investing pitfalls
"""

LESSONS = [
    {
        "id": "overconcentration",
        "title": "Overconcentration Risk",
        "category": "Portfolio Construction",
        "difficulty": "beginner",
        "pitfall": "Holding more than 20% of your portfolio in a single stock",
        "why_risky": [
            "Magnifies losses: If TSLA is 40% of your $10k portfolio and drops 20%, you lose $800 (8% of total)",
            "Reduces diversification benefits: One company's problems become your problems",
            "Increases volatility: Your portfolio swings wildly with one stock",
            "Single-company risk: Company-specific news hits harder"
        ],
        "real_example": {
            "scenario": "Tech enthusiast portfolio",
            "holding": "TSLA 40% ($4,000)",
            "others": "AAPL 30%, MSFT 20%, Cash 10%",
            "problem": "When TSLA dropped 30% in 2022, this portfolio fell 12% (vs market 10%)",
            "lesson": "Diversification cushioned some pain, but TSLA overweight amplified losses"
        },
        "solution": {
            "rule": "No single holding should exceed 10-15% of your portfolio",
            "why_it_works": "Even if one stock drops 50%, your portfolio drops only 5-7.5%",
            "implementation": [
                "Calculate: Max position = Portfolio value × 15%",
                "Example: $10k portfolio → Max $1,500 per stock",
                "Rebalance quarterly: Trim winners that grow beyond 15%"
            ]
        },
        "metric": "position_weight",
        "red_flag_threshold": 0.20,
        "warning_threshold": 0.15,
        "tags": ["risk-management", "diversification", "position-sizing"]
    },
    {
        "id": "sector-clustering",
        "title": "Sector Clustering",
        "category": "Diversification",
        "difficulty": "beginner",
        "pitfall": "Having too much exposure to a single sector (40%+ in one sector)",
        "why_risky": [
            "Sector-wide downturns hit you hard: Tech crash = your portfolio crashes",
            "Missing opportunities: If healthcare surges, you're underweight",
            "Loses correlation benefits: Different sectors move differently - that's your protection",
            "Concentration risk compounded: Often happens with tech stocks (easy to overweight)"
        ],
        "real_example": {
            "scenario": "Growth investor in 2022",
            "holdings": "AAPL (25%), MSFT (20%), GOOGL (15%), NVDA (10%), META (8%)",
            "sector_exposure": "Tech: 78%",
            "problem": "Tech sector fell 33% in 2022. This portfolio fell 25% (vs S&P 500: 18%)",
            "lesson": "Defensive sectors (healthcare, utilities, staples) would have cushioned the blow"
        },
        "solution": {
            "rule": "Allocate no more than 30-35% to any single sector",
            "target_allocation": {
                "Technology": "25-30%",
                "Finance": "15-20%",
                "Healthcare": "15-20%",
                "Consumer": "10-15%",
                "Industrial": "5-10%",
                "Other": "5-10%",
                "Bonds/Cash": "10-20%"
            },
            "implementation": [
                "Audit current holdings: Group by sector",
                "Identify overweight sectors (>30%)",
                "Add holdings from underweight sectors",
                "Use diversified ETFs (VTI) to fill gaps"
            ]
        },
        "metric": "sector_concentration",
        "red_flag_threshold": 0.40,
        "warning_threshold": 0.35,
        "tags": ["diversification", "sector-allocation"]
    },
    {
        "id": "concentration-risk",
        "title": "Concentration Risk",
        "category": "Risk Management",
        "difficulty": "beginner",
        "pitfall": "Top 3 holdings represent more than 50% of portfolio",
        "why_risky": [
            "Violates diversification principle: Your portfolio depends on 3 bets",
            "Amplifies mistakes: If your top 3 ideas are wrong, portfolio is in trouble",
            "Reduces expected return: Concentrated portfolios have higher risk for similar returns",
            "Harder to sleep at night: Volatility spikes with concentration"
        ],
        "real_example": {
            "scenario": "High-conviction investor",
            "holdings": "AAPL (35%), MSFT (20%), GOOGL (15%), 10 other stocks (30%)",
            "problem": "Top 3 are 70% of portfolio. When Apple had chip shortage fears, portfolio fell 8% in one day",
            "lesson": "That 30% in other holdings would have stabilized portfolio if AAPL had fallen 25%"
        },
        "solution": {
            "rule": "Top 3 holdings should be <50% of portfolio (ideally <40%)",
            "formula": "If Top3 > 50%, rebalance by trimming largest and buying others",
            "diversification_ratio": "Aim for 15-30 holdings to reduce company-specific risk",
            "implementation": [
                "Calculate concentration: (Top1 + Top2 + Top3) / Total",
                "If >50%, sell 20% of each top position",
                "Reinvest in underweight sectors or broad ETFs"
            ]
        },
        "metric": "top3_concentration",
        "red_flag_threshold": 0.60,
        "warning_threshold": 0.50,
        "tags": ["risk-management", "position-sizing", "diversification"]
    },
    {
        "id": "insufficient-diversification",
        "title": "Insufficient Diversification",
        "category": "Portfolio Construction",
        "difficulty": "beginner",
        "pitfall": "Portfolio has fewer than 10 holdings",
        "why_risky": [
            "Company-specific risk not diversified: 1 bad earnings report = portfolio drop",
            "Can't benefit from mean reversion: Small portfolio means less opportunity to catch winners",
            "Time-intensive: Can't monitor 5 stocks as well as you can 20",
            "Misses diversification benefit: Research shows 10-15 holdings optimal"
        ],
        "real_example": {
            "scenario": "Casual investor with 5 picks",
            "holdings": "AAPL, MSFT, GOOGL, NVDA, AMZN",
            "problem": "When NVDA missed earnings, portfolio fell 4% in one day (holding was 20%)",
            "lesson": "Same position in diversified portfolio would have caused <1% drop"
        },
        "solution": {
            "rule": "Maintain 15-30 holdings for individual stock investors",
            "alternative": "Use index funds (VTI, VOO) for automatic diversification",
            "implementation": [
                "Start with 10-15 quality companies you understand",
                "Add 2-3 new positions quarterly from underrepresented sectors",
                "Use ETFs for sectors you don't want to pick individual stocks"
            ]
        },
        "metric": "holding_count",
        "red_flag_threshold": 5,
        "warning_threshold": 10,
        "tags": ["diversification", "portfolio-construction"]
    },
    {
        "id": "performance-chasing",
        "title": "Performance Chasing",
        "category": "Behavioral Finance",
        "difficulty": "intermediate",
        "pitfall": "Buying stocks that had the best returns last year",
        "why_risky": [
            "Mean reversion: Best performers often underperform next year",
            "Buying high: You're buying stocks when they're most expensive (highest P/E)",
            "Timing mistake: Often buy right before sector correction",
            "Reduces returns: Research shows chasers underperform buy-and-hold by 2-3% annually"
        ],
        "real_example": {
            "scenario": "Chasing 2021 winners into 2022",
            "holdings": "Bought: NVDA, Tesla, ARK Innovation ETF (2021's best performers)",
            "result": "NVDA -50%, Tesla -65%, ARKK -66% in 2022",
            "lesson": "Those 2021 winners became 2022's worst performers"
        },
        "solution": {
            "rule": "Don't buy stocks in top performers list - buy their fallen competitors",
            "value_approach": "Buy beaten-down sectors (mean reversion)",
            "implementation": [
                "Ignore year-to-date performance rankings",
                "Look for quality companies with depressed valuations",
                "Buy 5-year low performers that have recovered fundamentals",
                "Dollar-cost average into positions over 3-6 months"
            ]
        },
        "metric": "momentum_exposure",
        "red_flag_threshold": "All holdings YTD return >+25%",
        "warning_threshold": "Average holding YTD return >+15%",
        "tags": ["behavioral-finance", "market-timing", "value-investing"]
    },
    {
        "id": "bond-stock-imbalance",
        "title": "Bonds vs Stocks Imbalance",
        "category": "Asset Allocation",
        "difficulty": "beginner",
        "pitfall": "Portfolio is 100% stocks or too many bonds for long-term",
        "why_risky": [
            "All stocks: High volatility, difficult to sleep at night, panic selling in crashes",
            "Too many bonds: Misses long-term stock growth, returns lag inflation",
            "No hedge: Stocks and bonds move differently - bonds protect in downturns",
            "Age mismatch: 25-year-old with 80% bonds = misses 40+ years of growth"
        ],
        "real_example": {
            "scenario": "30-year-old with all stocks during 2020 crash",
            "portfolio_hit": "-34% (S&P 500 correction)",
            "problem": "Panic sold at bottom, missed 60% recovery rally",
            "lesson": "20% bonds would have reduced decline to -27%, less likely to panic sell"
        },
        "solution": {
            "rule": "Bonds = 100 - your_age (approximate)",
            "for_30yo": "30% bonds, 70% stocks",
            "for_50yo": "50% bonds, 50% stocks",
            "implementation": [
                "Add low-cost bond index (BND, AGG) for stability",
                "Rebalance annually: Sell winners, buy laggards",
                "Bonds act as 'dry powder' to buy dips"
            ]
        },
        "metric": "stock_percentage",
        "red_flag_threshold": "100% stocks (age 40+) or >70% bonds (age <35)",
        "warning_threshold": "Imbalance > 20% from target",
        "tags": ["asset-allocation", "risk-management"]
    }
]


def get_all_lessons():
    """Return all lessons"""
    return LESSONS


def get_lesson_by_id(lesson_id: str):
    """Get single lesson by ID"""
    for lesson in LESSONS:
        if lesson["id"] == lesson_id:
            return lesson
    return None


def get_lessons_by_category(category: str):
    """Get all lessons in a category"""
    return [l for l in LESSONS if l["category"] == category]


def get_lesson_categories():
    """Get unique categories"""
    return sorted(set(l["category"] for l in LESSONS))


def get_difficulty_levels():
    """Get unique difficulty levels"""
    return sorted(set(l["difficulty"] for l in LESSONS))
