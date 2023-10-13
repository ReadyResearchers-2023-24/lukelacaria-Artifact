import requests

# An api key is emailed to you when you sign up to a plan
# Get a free API key at https://api.the-odds-api.com/
API_KEY = "ecf1dd9282fb68a2fc952a7cfe2d927a"

SPORT = "basketball_nba"

REGIONS = "us"  # uk | us | eu | au. Multiple can be specified if comma delimited

MARKETS = "h2h"  # h2h | spreads | totals. Multiple can be specified if comma delimited

ODDS_FORMAT = "decimal"  # decimal | american

DATE_FORMAT = "iso"  # iso | unix


def get_odds_data(team_search):
    """
    Retrieves the odds data from the API for a specified team search query.
    """
    odds_response = requests.get(
        f"https://api.the-odds-api.com/v4/sports/{SPORT}/odds",
        params={
            "api_key": API_KEY,
            "regions": REGIONS,
            "markets": MARKETS,
            "oddsFormat": ODDS_FORMAT,
            "dateFormat": DATE_FORMAT,
            "team": team_search,
        },
    )

    if odds_response.status_code != 200:
        print(
            f"Failed to get odds: status_code {odds_response.status_code},"
            + "response body {odds_response.text}"
        )
        return None
    else:
        # Check the usage quota
        print("Remaining requests", odds_response.headers["x-requests-remaining"])
        print("Used requests", odds_response.headers["x-requests-used"])
        return odds_response.json()


def print_odds(data, team_search):
    """
    Prints the odds data in a user-friendly format.
    """
    grouped_data = {}

    for i in data:
        if i["home_team"] == team_search or i["away_team"] == team_search:
            match_key = f"{i['home_team']} vs {i['away_team']}"
            if match_key not in grouped_data:
                grouped_data[match_key] = {}

            for bookmaker in i["bookmakers"]:
                title = bookmaker["title"]
                if title not in grouped_data[match_key]:
                    grouped_data[match_key][title] = {}
                for market in bookmaker["markets"]:
                    for outcome in market["outcomes"]:
                        team_name = outcome["name"]
                        odds = outcome["price"]
                        grouped_data[match_key][title][team_name] = odds

    print("\n\nMONEYLINE ODDS\n=========================\n\n")

    for match_key, bookmakers_data in grouped_data.items():
        print(f"\nMatch: {match_key}\n------------------------")
        for title, odds in bookmakers_data.items():
            print(f"{title}")
            for team, value in odds.items():
                print(f"\t{team}: {value}")

    if not grouped_data:
        print(f"{team_search} does not play!")
        exit()
    else:
        return (
            team_search,
            None,
        )  # Arbitrage across different matches would require more complex logic.

    print("\n\nMONEYLINE ODDS\n=========================\n\n")
    for title, odds in odds_dict.items():
        print(f"{title}")
        for team, value in odds.items():
            print(f"\t{team}: {value}")
            if team == team_search:
                orig_team = team
            else:
                arb_team = team
    if orig_team:
        return orig_team, arb_team
    else:
        print(f"{team_search} does not play!")
        exit()


def check_arb(bet_odds, api_odds):
    """
    Compares the user inputted bet odds to the odds retrieved from the API and
    calculates whether there is an arbitrage opportunity.
    """
    implied_prob_bet = 1 / bet_odds
    implied_prob_api = 1 / api_odds
    arb_percent = (1 - (implied_prob_bet + implied_prob_api)) * 100

    if arb_percent > 0:
        print(
            f"\n\nThere is an arbitrage opportunity! You could make a {arb_percent:.2f}% profit."
        )
    else:
        print("\n\nThere is no arbitrage opportunity.")


def test_bet(bet_odds, api_odds, exp_win, orig_team, arb_team):
    """
    Compares the user bet amount to the best available api odds in order to determine
    how much to bet on each side of the pick
    """
    bet_amt = 0
    arb_amt = 0
    bet_amt = round(exp_win / bet_odds, 2)
    arb_amt = round(exp_win / api_odds, 2)
    total_bet = round(bet_amt + arb_amt, 2)
    profit = round(((exp_win / total_bet) - 1) * 100, 2)
    if total_bet < exp_win:
        print(f"\n\nBet on {orig_team}: ${bet_amt}")
        print(f"Bet on {arb_team}: ${arb_amt}")
        print(f"Total wager: ${total_bet}")
        print(f"Total winnings: ${exp_win}")
        print(f"Profit: ${round(exp_win - total_bet, 2)}")
        print(f"Return on wager: {round(profit, 2)}%")
    else:
        print("\n\nThere is no arbitrage opportunity.")


# Main program
def main():
    team_search = input("Enter a team name to search odds for: ")

    data = get_odds_data(team_search)
    if data is not None:
        orig_team, arb_team = print_odds(data, team_search)

        bet_odds = float(input("Enter the odds of your bet: "))
        api_odds = float(input("Enter the API odds to compare to your bet: "))
        exp_win = float(input("Enter how much you would like to win: "))
        test_bet(bet_odds, api_odds, exp_win, orig_team, arb_team)


if __name__ == "__main__":
    main()
