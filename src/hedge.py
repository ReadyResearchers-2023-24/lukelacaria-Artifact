from flask import Flask, request, jsonify
from flask_cors import CORS
import requests

app = Flask(__name__)
CORS(app)

API_KEY = 'ecf1dd9282fb68a2fc952a7cfe2d927a'  # Replace with your The Odds API key
SPORT = "basketball_nba"
REGION = "us"
MARKET = "h2h"
ODDS_FORMAT = "decimal"
DATE_FORMAT = "iso"

@app.route('/')
def index():
    return app.send_static_file('index.html')

@app.route('/get-odds', methods=['POST'])
def get_odds():
    """
    Gets the odds of every game for a specified team and formats it in a readable manner.
    """
    # Get the team search from the web
    team_search = request.form.get('team_search')
    # Fetch data from The Odds API
    url = f"https://api.the-odds-api.com/v4/sports/{SPORT}/odds"
    params = {
        "apiKey": API_KEY,
        "regions": REGION,
        "markets": MARKET,
        "oddsFormat": ODDS_FORMAT,
        "dateFormat": DATE_FORMAT
    }
    response = requests.get(url, params=params)
    odds_data = response.json()
    formatted_data = format_odds_for_web(odds_data, team_search)
    return formatted_data

def format_odds_for_web(data, team_search):
    """
    Formats the odds data into HTML for display in a web app.
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

    if not grouped_data:
        return f"<p>{team_search} does not play!</p>"

    html_output = "<h3>MONEYLINE ODDS</h3>"

    for match_key, bookmakers_data in grouped_data.items():
        html_output += f"<h4>Match: {match_key}</h4>"
        for title, odds in bookmakers_data.items():
            html_output += f"<p><strong>{title}</strong></p>"
            for team, value in odds.items():
                html_output += f"<p>{team}: {value}</p>"

    return html_output

def get_opposing_teams_odds(team_search):
    """
    Retrieves the odds data from the API for a specified team search query and returns odds for opposing teams.
    """
    odds_response = requests.get(
        f"https://api.the-odds-api.com/v4/sports/{SPORT}/odds",
        params={
            "api_key": API_KEY,
            "regions": REGION,
            "markets": MARKET,
            "oddsFormat": ODDS_FORMAT,
            "dateFormat": DATE_FORMAT,
            "team": team_search,
        },
    )

    if odds_response.status_code != 200:
        print(
            f"Failed to get odds: status_code {odds_response.status_code},"
            + " response body {odds_response.text}"
        )
        return None
    else:
        # Check the usage quota
        print("Remaining requests", odds_response.headers["x-requests-remaining"])
        print("Used requests", odds_response.headers["x-requests-used"])

        odds_data = odds_response.json()
        opposing_teams_odds = []

        for match in odds_data:
            if match["home_team"] == team_search:
                opposing_team = match["away_team"]
            elif match["away_team"] == team_search:
                opposing_team = match["home_team"]
            else:
                continue

            for bookmaker in match["bookmakers"]:
                for market in bookmaker["markets"]:
                    for outcome in market["outcomes"]:
                        if outcome["name"] == opposing_team:
                            opposing_teams_odds.append(outcome["price"])

        return opposing_teams_odds, opposing_team

def check_arb(bet_team, bet_odds, api_odds):
    """
    Compares the user inputted bet odds to the odds retrieved from the API and
    calculates whether there is an arbitrage opportunity.
    """
    get_opposing_teams_odds(bet_team)

    implied_prob_bet = 1 / bet_odds
    implied_prob_api = 1 / api_odds
    arb_percent = (1 - (implied_prob_bet + implied_prob_api)) * 100

    if arb_percent > 0:
        print(
            f"\n\nThere is an arbitrage opportunity! You could make a {arb_percent:.2f}% profit."
        )
    else:
        return False

def calc_arb(bet_odds, api_odds, bet_amt, bet_team, opp_team):
    """
    Calculates the amount to bet on the opposing team, total amount bet, total profit, and profit percentage.
    """
    hedge_bet_amt = (bet_amt * bet_odds) / api_odds

    total_bet_amt = bet_amt + hedge_bet_amt

    profit_if_initial_bet_wins = bet_amt * bet_odds - total_bet_amt
    profit_if_hedge_bet_wins = hedge_bet_amt * api_odds - total_bet_amt

    guaranteed_profit = min(profit_if_initial_bet_wins, profit_if_hedge_bet_wins)

    profit_percentage = (guaranteed_profit / total_bet_amt) * 100

    html_output = "<h2>Hedging Calculation</h2>"
    html_output += f"<p>Bet on {opp_team}: ${hedge_bet_amt:.2f}</p>"
    html_output += f"<p>Total wager: ${total_bet_amt:.2f}</p>"
    html_output += f"<p>Guaranteed profit: ${guaranteed_profit:.2f}</p>"    
    html_output += f"<p>Profit percentage: {profit_percentage:.2f}%</p>"

    return html_output

@app.route('/hedge-finder', methods=['POST', 'GET'])
def hedge_finder():
    bet_team = request.form['bet_team']
    bet_odds = float(request.form['bet_odds'])
    bet_amt = float(request.form['bet_amt'])
    opp_odds, opp_team = get_opposing_teams_odds(bet_team)
    api_odds = max(opp_odds) if opp_odds else 0
    if check_arb(bet_team, bet_odds, api_odds) != False:
        html_output = calc_arb(bet_odds, api_odds, bet_amt, bet_team, opp_team)
    else:
        html_output = f"<p>There is no arbitrage opportunity</p>"
    return html_output
    


if __name__ == '__main__':
    app.run(debug=True)
