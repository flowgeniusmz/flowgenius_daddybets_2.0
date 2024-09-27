import pandas as pd
import numpy as np
import requests
from sklearn.model_selection import train_test_split, cross_val_score
from sklearn.preprocessing import StandardScaler
from sklearn.ensemble import RandomForestClassifier
import nfl_data_py as nfl

# Step 1: Data Collection

def fetch_historical_game_data():
    """
    Fetch historical game data using nfl_data_py.
    """
    # Specify the seasons you want data for
    seasons = list(range(2018, 2023))  # 2015 to 2021 seasons

    # Fetch play-by-play data
    print("Fetching historical game data...")
    pbp_data = nfl.import_pbp_data(seasons, downcast=True)
    
    # Aggregate data at the game level
    game_data = pbp_data.groupby(['game_id', 'posteam']).agg({
        'total_home_score': 'max',
        'total_away_score': 'max',
        'home_team': 'first',
        'away_team': 'first',
        'posteam_score': 'max',
        'defteam_score': 'max',
        'total_home_epa': 'sum',
        'total_away_epa': 'sum',
        'play_id': 'count',
    }).reset_index()
    
    # Determine win/loss
    game_data['win_loss'] = game_data.apply(
        lambda row: 1 if (
            (row['posteam'] == row['home_team'] and row['total_home_score'] > row['total_away_score']) or
            (row['posteam'] == row['away_team'] and row['total_away_score'] > row['total_home_score'])
        ) else 0, axis=1)
    
    # Identify if the team is playing at home or away
    game_data['home_away'] = game_data.apply(
        lambda row: 1 if row['posteam'] == row['home_team'] else 0, axis=1)
    
    return game_data

def fetch_betting_lines():
    """
    Fetch current betting lines using The Odds API.
    """
    # Insert your actual The Odds API key here
    API_KEY = '6b94ab1d81d71ea87b64473a1519fefd'  # Replace with your actual API key
    SPORT = 'americanfootball_nfl'
    REGIONS = 'us'  # Options: us, uk, eu, au
    MARKETS = 'h2h,spreads'  # Options: h2h, spreads, totals
    ODDS_FORMAT = 'american'  # Options: decimal, american
    DATE_FORMAT = 'iso'  # Options: iso, unix

    print("Fetching current betting lines...")
    odds_response = requests.get(
        f'https://api.the-odds-api.com/v4/sports/{SPORT}/odds',
        params={
            'api_key': API_KEY,
            'regions': REGIONS,
            'markets': MARKETS,
            'oddsFormat': ODDS_FORMAT,
            'dateFormat': DATE_FORMAT,
        }
    )

    if odds_response.status_code != 200:
        print(f"Failed to get odds: status_code {odds_response.status_code}, response body {odds_response.text}")
        return None

    odds_json = odds_response.json()

    # Transform the JSON data into a DataFrame
    betting_lines = []
    for game in odds_json:
        game_id = game['id']
        commence_time = game['commence_time']
        home_team = game['home_team']
        away_team = game['away_team']
        for bookmaker in game['bookmakers']:
            for market in bookmaker['markets']:
                for outcome in market['outcomes']:
                    betting_lines.append({
                        'game_id': game_id,
                        'commence_time': commence_time,
                        'home_team': home_team,
                        'away_team': away_team,
                        'bookmaker': bookmaker['title'],
                        'market': market['key'],
                        'team': outcome.get('name', ''),
                        'odds': outcome.get('price', ''),
                        'point': outcome.get('point', '')
                    })

    betting_lines_df = pd.DataFrame(betting_lines)
    return betting_lines_df

def fetch_upcoming_games():
    """
    Fetch the upcoming NFL games schedule.
    """
    current_year = pd.Timestamp.now().year
    schedule = nfl.import_schedules([current_year])

    # Determine the correct date column
    date_columns = ['game_date', 'gameday', 'start_time']
    for col in date_columns:
        if col in schedule.columns:
            date_col = col
            break
    else:
        raise ValueError("No date column found in schedule DataFrame.")

    # Convert the date column to datetime
    schedule[date_col] = pd.to_datetime(schedule[date_col], errors='coerce')

    # Remove rows with invalid dates
    schedule = schedule.dropna(subset=[date_col])

    today = pd.Timestamp.now()

    # Filter for upcoming games
    upcoming_games = schedule[schedule[date_col] >= today]

    if upcoming_games.empty:
        print("No upcoming games found.")
        return pd.DataFrame()  # Return an empty DataFrame

    # Rename the date column to 'game_datetime' for consistency
    upcoming_games = upcoming_games.rename(columns={date_col: 'game_datetime'})

    return upcoming_games

# Step 2: Data Preprocessing

def preprocess_data(game_data):
    """
    Preprocess the game data for modeling.
    """
    # Handle missing values
    game_data.fillna(0, inplace=True)
    
    # Feature Engineering
    game_data['point_diff'] = game_data['posteam_score'] - game_data['defteam_score']
    game_data['total_epa'] = game_data['total_home_epa'] + game_data['total_away_epa']
    
    return game_data

# Step 3: Model Development

def develop_model(data):
    """
    Develop and train the predictive model.
    """
    # Define features and target variable
    features = ['point_diff', 'total_epa', 'play_id', 'home_away']
    X = data[features]
    y = data['win_loss']  # Target variable: 1 for win, 0 for loss

    # Split data into training and testing sets
    print("Developing the model...")
    X_train, X_test, y_train, y_test = train_test_split(X, y, test_size=0.2)
    
    # Normalize the data
    scaler = StandardScaler()
    X_train = scaler.fit_transform(X_train)
    X_test = scaler.transform(X_test)

    # Choose a modeling technique (Random Forest Classifier)
    model = RandomForestClassifier(n_estimators=100)

    # Train the model
    model.fit(X_train, y_train)

    # Validate the model
    scores = cross_val_score(model, X_test, y_test, cv=5)
    print(f"Model Accuracy: {np.mean(scores)*100:.2f}%")

    return model, scaler

# Step 4: Probability Estimation

def estimate_probabilities(model, upcoming_game_data):
    """
    Estimate the probabilities of winning for upcoming games.
    """
    # Predict probabilities
    probabilities = model.predict_proba(upcoming_game_data[['point_diff', 'total_epa', 'play_id', 'home_away']])[:, 1]
    upcoming_game_data = upcoming_game_data.copy()
    upcoming_game_data['probability'] = probabilities
    return upcoming_game_data

# Step 5: Expected Value Calculation

def american_odds_to_implied_prob(odds):
    if odds > 0:
        return 100 / (odds + 100)
    else:
        return -odds / (-odds + 100)

def calculate_expected_value(betting_data):
    """
    Calculate the expected value for each bet.
    """
    # Convert odds to implied probabilities
    betting_data['odds'] = betting_data['odds'].astype(float)
    betting_data['implied_prob'] = betting_data['odds'].apply(american_odds_to_implied_prob)

    # Calculate Expected Value
    betting_data['expected_value'] = betting_data['probability'] - betting_data['implied_prob']
    return betting_data

# Step 6: Risk Assessment (Kelly Criterion)

def kelly_criterion(probability, odds):
    """
    Calculate the Kelly Criterion for stake sizing.
    """
    if odds > 0:
        b = odds / 100
    else:
        b = 100 / -odds
    q = 1 - probability
    f_star = (b * probability - q) / b
    return max(f_star, 0)

# Step 7: Bet Selection

def select_bets(betting_data):
    """
    Select the best bets based on expected value and Kelly Criterion.
    """
    # Select bets with positive expected value
    positive_ev_bets = betting_data[betting_data['expected_value'] > 0]

    # Calculate optimal stake using Kelly Criterion
    positive_ev_bets = positive_ev_bets.copy()
    positive_ev_bets['kelly_fraction'] = positive_ev_bets.apply(
        lambda row: kelly_criterion(row['probability'], float(row['odds'])), axis=1
    )

    # Filter out bets with unreasonable Kelly fractions
    positive_ev_bets = positive_ev_bets[
        (positive_ev_bets['kelly_fraction'] > 0) & (positive_ev_bets['kelly_fraction'] <= 1)
    ]

    return positive_ev_bets

# Step 8: Main Function

def main():
    # Fetch data
    game_data = fetch_historical_game_data()
    betting_lines = fetch_betting_lines()

    if betting_lines is None:
        print("No betting lines data available.")
        return

    # Preprocess data
    data = preprocess_data(game_data)

    # Develop model
    model, scaler = develop_model(data)

    # Prepare upcoming game data
    print("Preparing upcoming game data...")
    upcoming_games = fetch_upcoming_games()

    if upcoming_games.empty:
        print("No upcoming games found.")
        return

    # Prepare teams in upcoming games
    teams_in_upcoming_games = pd.melt(
        upcoming_games[['game_id', 'home_team', 'away_team']],
        id_vars=['game_id'],
        value_vars=['home_team', 'away_team'],
        var_name='home_away_str',
        value_name='team'
    )

    teams_in_upcoming_games['home_away'] = teams_in_upcoming_games['home_away_str'].map({'home_team': 1, 'away_team': 0})

    # Aggregate team statistics from historical data
    team_stats = data.groupby('posteam').agg({
        'point_diff': 'mean',
        'total_epa': 'mean',
        'play_id': 'mean'
    }).reset_index()

    # Merge to get features for upcoming teams
    upcoming_game_data = pd.merge(
        teams_in_upcoming_games,
        team_stats,
        left_on='team',
        right_on='posteam',
        how='left'
    )

    # Drop rows with missing data
    upcoming_game_data.dropna(subset=['point_diff', 'total_epa', 'play_id'], inplace=True)

    if upcoming_game_data.empty:
        print("No data available for upcoming games.")
        return

    # Prepare features
    features = ['point_diff', 'total_epa', 'play_id', 'home_away']
    upcoming_game_data[features] = scaler.transform(upcoming_game_data[features])

    # Estimate probabilities
    upcoming_game_data = estimate_probabilities(model, upcoming_game_data)

    # Map team abbreviations to full team names
    team_abbrev_to_name = {
        'ARI': 'Arizona Cardinals',
        'ATL': 'Atlanta Falcons',
        'BAL': 'Baltimore Ravens',
        'BUF': 'Buffalo Bills',
        'CAR': 'Carolina Panthers',
        'CHI': 'Chicago Bears',
        'CIN': 'Cincinnati Bengals',
        'CLE': 'Cleveland Browns',
        'DAL': 'Dallas Cowboys',
        'DEN': 'Denver Broncos',
        'DET': 'Detroit Lions',
        'GB': 'Green Bay Packers',
        'HOU': 'Houston Texans',
        'IND': 'Indianapolis Colts',
        'JAX': 'Jacksonville Jaguars',
        'KC': 'Kansas City Chiefs',
        'LAC': 'Los Angeles Chargers',
        'LAR': 'Los Angeles Rams',
        'LV': 'Las Vegas Raiders',
        'MIA': 'Miami Dolphins',
        'MIN': 'Minnesota Vikings',
        'NE': 'New England Patriots',
        'NO': 'New Orleans Saints',
        'NYG': 'New York Giants',
        'NYJ': 'New York Jets',
        'PHI': 'Philadelphia Eagles',
        'PIT': 'Pittsburgh Steelers',
        'SEA': 'Seattle Seahawks',
        'SF': 'San Francisco 49ers',
        'TB': 'Tampa Bay Buccaneers',
        'TEN': 'Tennessee Titans',
        'WAS': 'Washington Commanders',
    }
    upcoming_game_data['team_name'] = upcoming_game_data['team'].map(team_abbrev_to_name)

    # Clean team names in betting lines
    betting_lines['team'] = betting_lines['team'].str.strip()
    # Adjust team names in betting lines to match team_name in upcoming_game_data
    betting_lines['team'] = betting_lines['team'].replace({
        'Washington Football Team': 'Washington Commanders',
        'Washington Redskins': 'Washington Commanders',
        'San Diego Chargers': 'Los Angeles Chargers',
        'LA Chargers': 'Los Angeles Chargers',
        'St. Louis Rams': 'Los Angeles Rams',
        'LA Rams': 'Los Angeles Rams',
        'Oakland Raiders': 'Las Vegas Raiders',
        'New York Giants': 'New York Giants',
        'NY Giants': 'New York Giants',
        'New York Jets': 'New York Jets',
        'NY Jets': 'New York Jets',
        'SF 49ers': 'San Francisco 49ers',
        'Tampa Bay Bucs': 'Tampa Bay Buccaneers',
        'New England Pats': 'New England Patriots',
        'Jacksonville Jaguars': 'Jacksonville Jaguars',
        'Jax Jaguars': 'Jacksonville Jaguars',
        'Houston Texans': 'Houston Texans',
        'Arizona Cardinals': 'Arizona Cardinals',
        'Baltimore Ravens': 'Baltimore Ravens',
        'Buffalo Bills': 'Buffalo Bills',
        'Carolina Panthers': 'Carolina Panthers',
        'Chicago Bears': 'Chicago Bears',
        'Cincinnati Bengals': 'Cincinnati Bengals',
        'Cleveland Browns': 'Cleveland Browns',
        'Dallas Cowboys': 'Dallas Cowboys',
        'Denver Broncos': 'Denver Broncos',
        'Detroit Lions': 'Detroit Lions',
        'Green Bay Packers': 'Green Bay Packers',
        'Indianapolis Colts': 'Indianapolis Colts',
        'Kansas City Chiefs': 'Kansas City Chiefs',
        'Miami Dolphins': 'Miami Dolphins',
        'Minnesota Vikings': 'Minnesota Vikings',
        'New Orleans Saints': 'New Orleans Saints',
        'Philadelphia Eagles': 'Philadelphia Eagles',
        'Pittsburgh Steelers': 'Pittsburgh Steelers',
        'Seattle Seahawks': 'Seattle Seahawks',
        'Tennessee Titans': 'Tennessee Titans',
        'Atlanta Falcons': 'Atlanta Falcons',
        'Los Angeles Rams': 'Los Angeles Rams',
        'Los Angeles Chargers': 'Los Angeles Chargers',
        'Las Vegas Raiders': 'Las Vegas Raiders',
        'Houston Oilers': 'Tennessee Titans',
        'St Louis Rams': 'Los Angeles Rams',
        'San Fran 49ers': 'San Francisco 49ers',
        'Tampa Bay Buccaneers': 'Tampa Bay Buccaneers',
        'New England Patriots': 'New England Patriots',
        'LA Raiders': 'Las Vegas Raiders',
        # Add any other necessary mappings
    })

    # Merge betting lines with upcoming game data
    merged_data = pd.merge(
        betting_lines,
        upcoming_game_data[['team_name', 'probability']],
        left_on=['team'],
        right_on=['team_name'],
        how='inner'
    )

    if merged_data.empty:
        print("No matching teams found between betting lines and upcoming games.")
        return

    # Calculate expected value
    betting_data = calculate_expected_value(merged_data)

    # Select bets
    recommended_bets = select_bets(betting_data)

    if recommended_bets.empty:
        print("No recommended bets found.")
        return

    # Output recommended bets
    print("Recommended Bets:")
    print(recommended_bets[['game_id', 'team', 'market', 'odds', 'expected_value', 'kelly_fraction']])

    # Optional: Save recommended bets to a CSV file
    recommended_bets.to_csv('data/csv/recommended_bets.csv', index=False)

if __name__ == "__main__":
    main()
