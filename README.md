# Odds Checker and Arbitrage Calculator

## Overview

This Python script fetches the betting odds data from "The Odds API" and allows the user to identify arbitrage opportunities by comparing the retrieved odds data against user-inputted odds. Arbitrage betting involves placing bets on all outcomes of an event to guarantee a profit, regardless of the result.

## Dependencies

- Python 3.x
- Poetry

## Configuration

Various configurations can be adjusted at the start of the script:

- **API_KEY:** Your personal API key from "The Odds API".
- **SPORT:** Specifies the sport you are interested in (e.g., 'basketball_nba').
- **REGIONS:** Target regions ('uk', 'us', 'eu', or 'au'). Multiple regions can be comma-delimited.
- **MARKETS:** Types of odds to fetch ('h2h', 'spreads', or 'totals'). Multiple types can be comma-delimited.
- **ODDS_FORMAT:** The format of the odds to be retrieved ('decimal' or 'american').
- **DATE_FORMAT:** Format to receive date data ('iso' or 'unix').

## Expected Usage

**User Input:**
- Search Team: The user inputs a team to search the odds for.
- Bet Odds: The user enters the odds they have been offered.
- API Odds: The user enters the odds from the API they wish to compare.
- Desired Winnings: The user inputs the desired winning amount.

**Output:**

Displays the odds for the specified team from various bookmakers. Calculates and displays whether there's an arbitrage opportunity and how to bet to achieve desired winnings.

