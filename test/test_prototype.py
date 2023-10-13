import pytest
import sys
sys.path.append('src')
from prototype import check_arb, test_bet

# Assuming that you might run tests from the root directory
# or setup PYTHONPATH accordingly, so 'src' is recognized

# Test for `check_arb` function
def test_check_arb_positive(capsys):
    check_arb(2.2, 2.1)  # Here capsys is a built-in pytest fixture which captures stdout and stderr during test execution.
    captured = capsys.readouterr()
    assert "There is an arbitrage opportunity!" in captured.out
    
def test_check_arb_negative(capsys):
    check_arb(2, 0.6)
    captured = capsys.readouterr()
    assert "There is no arbitrage opportunity." in captured.out

# Additional Tests for the other functions...
'''
# Example testing for the 'test_bet' function
def test_test_bet_profitable(capsys):
    test_bet(2, 0.4, 100, "Team A", "Team B")
    captured = capsys.readouterr()
    assert "Bet on Team A: $50.0" in captured.out
    assert "Bet on Team B: $250.0" in captured.out
    assert "Total wager: $300.0" in captured.out
    assert "Total winnings: $100" in captured.out
    assert "Profit: $-200.0" in captured.out
    assert "Return on wager: -200.0%" in captured.out
'''
def test_test_bet_non_profitable(capsys):
    # Hardcoded values
    bet_odds = 2
    api_odds = 0.6
    exp_win = 100
    orig_team = "Team A"
    arb_team = "Team B"
    
    # Call the function under test with hardcoded values
    test_bet(bet_odds, api_odds, exp_win, orig_team, arb_team)
    
    # Capture the output and assert
    captured = capsys.readouterr()
    assert "There is no arbitrage opportunity." in captured.out

# You might add more test cases to ensure your functions are working as expected in all scenarios.
