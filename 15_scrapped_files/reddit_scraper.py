class RedditScraper:
    def __init__(self, url: str = "https://www.reddit.com/r/Python/hot/"):
        self.url = url

    def scrape_posts(self) -> list:
        import requests
        from bs4 import BeautifulSoup
        posts = []
        try:
            headers = {'User-Agent': 'Mozilla/5.0'}
            response = requests.get(self.url, headers=headers)
            response.raise_for_status()
            soup = BeautifulSoup(response.text, 'html.parser')
            post_elements = soup.select('div.Post')
            for post_elem in post_elements[:10]:
                try:
                    title = post_elem.select_one('h3').text.strip()
                    upvotes = post_elem.select_one('div[data-test-id="post-vote-count"]').text.strip() if post_elem.select_one('div[data-test-id="post-vote-count"]') else '0'
                    upvotes = upvotes.replace('k', '000').replace('.', '')
                    date = post_elem.select_one('time').get('datetime') if post_elem.select_one('time') else 'N/A'

                    posts.append({
                        'title': title,
                        'upvotes': upvotes,
                        'date': date
                    })
                except Exception as e:
                    continue
        except Exception as e:
            print(f"Error: {e}")
        return posts

def export_to_json(posts: list):
    import json
    with open('posts.json', 'w') as f:
        json.dump(posts, f, indent=2)

from flask import Flask, render_template, send_file
app = Flask(__name__)

@app.route('/')
def index():
    try:
        scraper = RedditScraper()
        posts = scraper.scrape_posts()
        export_to_json(posts)
        return render_template('report.html', posts=posts)
    except Exception as e:
        return f"Error: {e}", 500

@app.route('/download')
def download():
    return send_file('posts.json', as_attachment=True)

if __name__ == '__main__':
    app.run(debug=True)