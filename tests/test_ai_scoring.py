from ai_moomoo_trader.ai import HeuristicAIScorer
from ai_moomoo_trader.data.sample_data import generate_prices


def test_ai_scorer_range():
    prices = generate_prices("US.NVDA", days=80)
    score = HeuristicAIScorer().score(prices)
    assert 0 <= score.final_score <= 100
    assert score.symbol == "US.NVDA"
