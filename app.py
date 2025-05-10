from flask import Flask, render_template, jsonify
import requests
import time
from datetime import datetime, timezone

app = Flask(__name__)

API_KEY = "f104f27bfbcccdd991a83aa22a1941f4"
BASE_URL = "https://api.the-odds-api.com/v4/sports"
PROB_THRESHOLD = 0.6

@app.route('/')
def home():
    return render_template('index.html')

@app.route('/api/predictions')
def get_predictions():
    today_utc = datetime.now(timezone.utc).date()

    sports_resp = requests.get(f"{BASE_URL}/", params={"apiKey": API_KEY})
    sports = sports_resp.json()
    soccer_leagues = [s["key"] for s in sports if "Soccer" in s["group"]]

    predictions = []

    for league_key in soccer_leagues:
        odds_url = f"{BASE_URL}/{league_key}/odds"
        odds_params = {
            "apiKey": API_KEY,
            "regions": "eu",
            "markets": "h2h",
            "oddsFormat": "decimal"
        }

        try:
            response = requests.get(odds_url, params=odds_params)
            if response.status_code != 200:
                continue

            matches = response.json()
            for match in matches:
                if not match.get("bookmakers"):
                    continue

                match_time = datetime.fromisoformat(match["commence_time"].replace("Z", "+00:00"))
                if match_time.date() != today_utc:
                    continue

                bookmaker = match["bookmakers"][0]
                outcomes = bookmaker["markets"][0]["outcomes"]

                probabilities = []
                for outcome in outcomes:
                    odds = outcome["price"]
                    prob = 1 / odds
                    probabilities.append((outcome["name"], prob, odds))

                best_outcome = max(probabilities, key=lambda x: x[1])
                if best_outcome[1] >= PROB_THRESHOLD:
                    predictions.append({
                        "home_team": match["home_team"],
                        "away_team": match["away_team"],
                        "time": match_time.strftime('%H:%M UTC'),
                        "prediction": best_outcome[0],
                        "probability": f"{best_outcome[1] * 100:.2f}%",
                        "odds": best_outcome[2]
                    })

        except Exception as e:
            continue

        time.sleep(1)

    return jsonify(predictions)

if __name__ == '__main__':
    app.run(debug=True)
