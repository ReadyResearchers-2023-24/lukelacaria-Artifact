from flask import Flask, render_template, request, redirect, url_for, jsonify
from flask_sqlalchemy import SQLAlchemy
from flask_login import LoginManager, UserMixin, login_user, login_required, logout_user, current_user
from werkzeug.security import generate_password_hash, check_password_hash
from flask_cors import CORS
from datetime import datetime, timedelta, timezone
import json
import os
from flask_apscheduler import APScheduler
import requests

app = Flask(__name__)
CORS(app)

API_KEY = 'ecf1dd9282fb68a2fc952a7cfe2d927a'  # Replace with your The Odds API key
SPORT = "basketball_nba"
REGION = "us"
MARKET = "h2h"
ODDS_FORMAT = "decimal"
DATE_FORMAT = "iso"

app.config['SQLALCHEMY_DATABASE_URI'] = 'sqlite:///users.db'  # SQLite database
app.config['SECRET_KEY'] = 'your_secret_key'

# Initialize APScheduler
scheduler = APScheduler()

db = SQLAlchemy(app)
login_manager = LoginManager()
login_manager.init_app(app)
login_manager.login_view = 'login'

class User(UserMixin, db.Model):
    id = db.Column(db.Integer, primary_key=True)
    username = db.Column(db.String(100), unique=True)
    password = db.Column(db.String(100))

class Bet(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    bet_team = db.Column(db.String(100), nullable=False)
    bet_odds = db.Column(db.Float, nullable=False)
    bet_amount = db.Column(db.Float, nullable=False)
    bookmaker = db.Column(db.String(100), nullable=False)
    commence_time = db.Column(db.DateTime, nullable=False)
    user_id = db.Column(db.Integer, db.ForeignKey('user.id'))

    def __repr__(self):
        return f'<Bet {self.bet_team} {self.bet_odds} {self.bet_amount} {self.bookmaker} {self.commence_time}>'

class Hedge(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    bet_team = db.Column(db.String(100), nullable=False)
    bet_odds = db.Column(db.Float, nullable=False)
    bet_amount = db.Column(db.Float, nullable=False)
    user_book = db.Column(db.String(100), nullable=False)
    opp_team = db.Column(db.String(100), nullable=False)
    hedge_book = db.Column(db.String(100), nullable=False)
    hedge_odds = db.Column(db.Float, nullable=False)
    hedge_bet_amt = db.Column(db.Float, nullable=False)
    total_bet_amt = db.Column(db.Float, nullable=False)
    guaranteed_profit = db.Column(db.Float, nullable=False)
    profit_percentage = db.Column(db.Float, nullable=False)
    user_id = db.Column(db.Integer, db.ForeignKey('user.id'))

class Event:
    def __init__(self, json_data):
        self.id = json_data.get('id', None)
        self.home_team = json_data.get('home_team', '')
        self.away_team = json_data.get('away_team', '')
        self.bookmakers = [Bookmaker(bm) for bm in json_data.get('bookmakers', [])]
        self.commence_time = datetime.fromisoformat(json_data.get('commence_time').replace('Z', '+00:00'))

class Bookmaker:
    def __init__(self, json_data):
        self.title = json_data.get('title', '')
        self.markets = [Market(m) for m in json_data.get('markets', [])]

class Market:
    def __init__(self, json_data):
        self.outcomes = [Outcome(o) for o in json_data.get('outcomes', [])]

class Outcome:
    def __init__(self, json_data):
        self.name = json_data.get('name', '')
        self.price = json_data.get('price', 0)

@login_manager.user_loader
def load_user(user_id):
    return User.query.get(int(user_id))

@app.route('/')
def index():
    if not current_user.is_authenticated:
        return redirect(url_for('login'))

    user_bets = Bet.query.filter_by(user_id=current_user.id).all() if current_user.is_authenticated else []
    return render_template('index.html', bets=user_bets)


@app.route('/login', methods=['GET', 'POST'])
def login():
    if current_user.is_authenticated:
        return redirect(url_for('index'))
    if request.method == 'POST':
        username = request.form['username']
        password = request.form['password']
        user = User.query.filter_by(username=username).first()
        if user and check_password_hash(user.password, password):
            login_user(user)
            return redirect(url_for('index'))
        else:
            return redirect(url_for('login'))
    return render_template('login.html')

@app.route('/register', methods=['GET', 'POST'])
def register():
    if current_user.is_authenticated:
        return redirect(url_for('home'))
    if request.method == 'POST':
        username = request.form['username']
        password = generate_password_hash(request.form['password'], method='pbkdf2:sha256')
        new_user = User(username=username, password=password)
        db.session.add(new_user)
        db.session.commit()
        return redirect(url_for('login'))
    return render_template('register.html')

@app.route('/logout', methods=['GET', 'POST'])
@login_required
def logout():
    logout_user()
    return redirect(url_for('index'))

def get_odds_from_api():
    """
    Gets the odds of every game for a specified team and formats it in a readable manner.
    """
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
    events = [Event(item) for item in odds_data]
    #cache_odds(events)
    print(events)
    for event in events:
        print(event.commence_time)
    return events

@app.route('/odds-search', methods=['POST'])
def odds_search():
    team_search = request.form.get('team_search')
    odds_data = get_odds_from_api()
    html_output = format_odds_for_web(odds_data, team_search)
    return html_output

def fetch_and_cache_odds():
    # Fetch odds data from the API
    odds_data = get_odds_from_api()

    # Save data to a JSON file
    cache_odds(odds_data)

def cache_odds(odds_data):
    with open('odds_cache.json', 'w') as file:
        json.dump(odds_data, file)

def read_odds_from_cache():
    if os.path.exists('odds_cache.json'):
        with open('odds_cache.json', 'r') as file:
            return json.load(file)
    return None

def format_odds_for_web(events, team_search):
    """
    Formats the odds data into HTML for display in a web app.
    """
    grouped_data = {}

    for event in events:
        if event.home_team == team_search or event.away_team == team_search:
            match_key = f"{event.home_team} vs {event.away_team}"
            if match_key not in grouped_data:
                grouped_data[match_key] = {}

            for bookmaker in event.bookmakers:
                title = bookmaker.title
                if title not in grouped_data[match_key]:
                    grouped_data[match_key][title] = {}
                for market in bookmaker.markets:
                    for outcome in market.outcomes:
                        team_name = outcome.name
                        odds = outcome.price
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

def get_opposing_teams_odds(events, team_search):
    opposing_teams_odds = {}
    opposing_team = None

    for event in events:
        if event.home_team == team_search:
            commence_time = event.commence_time
            opposing_team = event.away_team
        elif event.away_team == team_search:
            opposing_team = event.home_team
            commence_time = event.commence_time
        else:
            continue

        for bookmaker in event.bookmakers:
            bookmaker_name = bookmaker.title
            for market in bookmaker.markets:
                for outcome in market.outcomes:
                    if outcome.name == opposing_team:
                        opposing_teams_odds[bookmaker_name] = outcome.price

    return opposing_teams_odds, opposing_team, commence_time

def get_opposing_teams_odds_from_cache(team_search):

        odds_data = read_odds_from_cache()
        opposing_teams_odds = {}
        opposing_team = None

        for match in odds_data:
            if match["home_team"] == team_search:
                opposing_team = match["away_team"]
            elif match["away_team"] == team_search:
                opposing_team = match["home_team"]
            else:
                continue

            for bookmaker in match["bookmakers"]:
                bookmaker_name = bookmaker["title"]
                for market in bookmaker["markets"]:
                    for outcome in market["outcomes"]:
                        if outcome["name"] == opposing_team:
                            opposing_teams_odds[bookmaker_name] = outcome["price"]

        return opposing_teams_odds, opposing_team


def check_hedge(bet_team, bet_odds, api_odds):
    """
    Compares the user inputted bet odds to the odds retrieved from the API and
    calculates whether there is an arbitrage opportunity.
    """
    if bet_odds and api_odds != 0:
        implied_prob_bet = 1 / bet_odds
        implied_prob_api = 1 / api_odds
        arb_percent = (1 - (implied_prob_bet + implied_prob_api)) * 100
    else:
        arb_percent = 0

    if arb_percent > 0:
        print(
            f"\n\nThere is an arbitrage opportunity! You could make a {arb_percent:.2f}% profit."
        )
        return True
    else:
        return False

def calc_hedge(hedge_data):
    """
    Calculates the hedging details and updates the hedge_data dictionary.

    Args:
    - hedge_data (dict): A dictionary containing information about the hedge bet.

    Returns:
    - dict: Updated hedge_data dictionary with added calculations.
    - str: HTML output string.
    """
    # Calculate the amount to bet on the opposing team
    hedge_bet_amt = (hedge_data['bet_amount'] * hedge_data['bet_odds']) / hedge_data['hedge_odds']

    # Calculate total bet amount
    total_bet_amt = hedge_data['bet_amount'] + hedge_bet_amt

    # Calculate profits
    profit_if_initial_bet_wins = hedge_data['bet_amount'] * hedge_data['bet_odds'] - total_bet_amt
    profit_if_hedge_bet_wins = hedge_bet_amt * hedge_data['hedge_odds'] - total_bet_amt
    guaranteed_profit = min(profit_if_initial_bet_wins, profit_if_hedge_bet_wins)

    # Calculate profit percentage
    profit_percentage = (guaranteed_profit / total_bet_amt) * 100

    # Update hedge_data dictionary
    hedge_data.update({
        'hedge_bet_amt': hedge_bet_amt,
        'total_bet_amt': total_bet_amt,
        'guaranteed_profit': guaranteed_profit,
        'profit_percentage': profit_percentage
    })

    # Generate HTML output
    html_output = "<h2>Hedging Calculation</h2>"
    html_output += f"<p>Bet on {hedge_data['opp_team']}: ${hedge_bet_amt:.2f}</p>"
    html_output += f"<p>Total wager: ${total_bet_amt:.2f}</p>"
    html_output += f"<p>Guaranteed profit: ${guaranteed_profit:.2f}</p>"
    html_output += f"<p>Profit percentage: {profit_percentage:.2f}%</p>"
    print(hedge_data)

    return hedge_data, html_output

def generate_html_output(hedge_data):
    html_output = ''
    if hedge_data is None:
        return "<p>Error fetching odds data.</p>"
    if hedge_data['hedge_book'] != hedge_data['user_book'] and hedge_data['hedge_opportunity']:
        html_output = f"<p>There is a hedge opportunity on {hedge_data['hedge_book']}"
    if hedge_data['hedge_opportunity']:
        calc_response = calc_hedge(hedge_data)
        hedge_data = calc_response[0]
        html_output += calc_response[1]
    else:
        html_output = "<p>There is no arbitrage opportunity</p>"

    return html_output

def filter_recent_games(bets, hours=3.5):
    """ Filter out games that have started more than specified hours ago.
    
    Args:
    - bets (list): List of Bet objects.
    - hours_ago (float): Number of hours to check against.

    Returns:
    - list: Filtered list of Bet objects.
    """
    current_time = datetime.utcnow()
    filtered_bets = []

    for bet in bets:
        # Check if the commence_time of the bet is within the specified time range
        threshold_time = bet.commence_time + timedelta(hours=hours)
        if current_time < threshold_time:
            filtered_bets.append(bet)

    return filtered_bets

def hedge_find(bet_team, bet_odds, bet_amt, user_book):
    opp_odds_data, opp_team, commence_time = get_opposing_teams_odds(get_odds_from_api(), bet_team)
    
    if opp_odds_data is None:
        return None

    user_book_odds = opp_odds_data.get(user_book, 0)
    best_book, best_odds = max(opp_odds_data.items(), key=lambda x: x[1], default=(None, 0))

    hedge_data = {
        'bet_team': bet_team,
        'bet_odds': float(bet_odds),
        'bet_amount': float(bet_amt),
        'user_book': user_book,
        'opp_team': opp_team,
        'user_book_odds': float(user_book_odds),
        'best_book': best_book,
        'best_odds': float(best_odds),
        'commence_time': commence_time
    }

    if check_hedge(bet_team, bet_odds, user_book_odds):
        hedge_data['hedge_opportunity'] = True
        hedge_data['hedge_book'] = user_book
        hedge_data['hedge_odds'] = user_book_odds
    elif user_book != best_book and check_hedge(bet_team, bet_odds, best_odds):
        hedge_data['hedge_opportunity'] = True
        hedge_data['hedge_book'] = best_book
        hedge_data['hedge_odds'] = best_odds
    else:
        hedge_data['hedge_opportunity'] = False

    return hedge_data

@app.route('/hedge-search', methods=['POST', 'GET'])
def hedge_search():
    bet_team = request.form['bet_team']
    bet_odds = float(request.form['bet_odds'])
    bet_amt = float(request.form['bet_amt'])
    user_book = request.form['bookmaker']

    hedge_data = hedge_find(bet_team, bet_odds, bet_amt, user_book)
    event_commence_time = hedge_data['commence_time']
    html_output = generate_html_output(hedge_data)

    # Create and save the new bet record
    new_bet = Bet(bet_team=bet_team, bet_odds=bet_odds, bet_amount=bet_amt, bookmaker=user_book, commence_time=event_commence_time, user_id=current_user.id)
    db.session.add(new_bet)
    db.session.commit()

    return html_output

def auto_hedge_check():
    print("Auto hedge running...")
    with app.app_context():
        all_bets = Bet.query.all()
        print(all_bets)
        filtered_bets = filter_recent_games(all_bets)
        print(filtered_bets)
        for bet in filtered_bets:
            hedge_data = hedge_find(bet.bet_team, bet.bet_odds, bet.bet_amount, bet.bookmaker)
            if hedge_data and hedge_data['hedge_opportunity']:
                # Calculate hedge details
                hedge_data, _ = calc_hedge(hedge_data)
                print("Auto hedge found!")
                # Create a new hedge record
                print(hedge_data)
                new_hedge = Hedge(
                    bet_team=hedge_data['bet_team'],
                    bet_odds=hedge_data['bet_odds'],
                    bet_amount=hedge_data['bet_amount'],
                    user_book=hedge_data['user_book'],
                    opp_team=hedge_data['opp_team'],
                    hedge_book=hedge_data['hedge_book'],
                    hedge_odds=hedge_data['hedge_odds'],
                    hedge_bet_amt=hedge_data['hedge_bet_amt'],
                    total_bet_amt=hedge_data['total_bet_amt'],
                    guaranteed_profit=hedge_data['guaranteed_profit'],
                    profit_percentage=hedge_data['profit_percentage'],
                    user_id=bet.user_id
                )
                db.session.add(new_hedge)
            db.session.commit()

if __name__ == '__main__':
    with app.app_context():
        db.create_all()
    # Initialize the scheduler with your Flask app
    scheduler.init_app(app)
    scheduler.start()

    # Schedule the auto_hedge_check to run every minute
    scheduler.add_job(id='auto_hedge_job', func=auto_hedge_check, trigger='interval', minutes=0.15)

    app.run(debug=True)
