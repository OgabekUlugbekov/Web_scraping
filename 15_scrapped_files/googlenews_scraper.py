class GoogleNewsScraper:
    def __init__(self, url: str = "https://news.google.com/rss"):
        self.url = url

    def scrape_articles(self) -> list:
        import feedparser
        articles = []
        try:
            feed = feedparser.parse(self.url)
            for entry in feed.entries[:20]:
                try:
                    headline = entry.title
                    publisher = entry.source.title if 'source' in entry and 'title' in entry.source else 'N/A'
                    date = entry.published if 'published' in entry else 'N/A'

                    articles.append({
                        'headline': headline,
                        'publisher': publisher,
                        'date': date
                    })
                except Exception as e:
                    continue
        except Exception as e:
            print(f"Error: {e}")
        return articles

def export_to_json(articles: list):
    import json
    with open('news.json', 'w') as f:
        json.dump(articles, f, indent=2)

from flask import Flask, render_template, send_file
app = Flask(__name__)

@app.route('/')
def index():
    try:
        scraper = GoogleNewsScraper()
        articles = scraper.scrape_articles()
        export_to_json(articles)
        return render_template('report.html', articles=articles)
    except Exception as e:
        return f"Error: {e}", 500

@app.route('/download')
def download():
    return send_file('news.json', as_attachment=True)

if __name__ == '__main__':
    app.run(debug=True)