class TwitterScraper:
    def __init__(self, hashtag: str = "python"):
        self.hashtag = hashtag

    def scrape_tweets(self) -> list:
        tweets = []
        try:
            tweets = [
                {'username': 'user1', 'tweet': 'Learning #python is fun!', 'date': '2025-04-29'},
                {'username': 'user2', 'tweet': '#python coding tips for beginners', 'date': '2025-04-28'},
                {'username': 'user3', 'tweet': 'Just built a #python project!', 'date': '2025-04-27'}
            ]
            print("Note: This is a simulated output. Use the Twitter API for real data.")
        except Exception as e:
            print(f"Error: {e}")
        return tweets

def export_to_json(tweets: list):
    import json
    with open('tweets.json', 'w') as f:
        json.dump(tweets, f, indent=2)

from flask import Flask, render_template, send_file
app = Flask(__name__)

@app.route('/')
def index():
    try:
        scraper = TwitterScraper()
        tweets = scraper.scrape_tweets()
        export_to_json(tweets)
        return render_template('report.html', tweets=tweets)
    except Exception as e:
        return f"Error: {e}", 500

@app.route('/download')
def download():
    return send_file('tweets.json', as_attachment=True)

if __name__ == '__main__':
    app.run(debug=True)