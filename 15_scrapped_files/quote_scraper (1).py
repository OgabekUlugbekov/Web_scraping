import logging
logging.basicConfig(
    filename='quote_log.log',
    level=logging.INFO,
    format='%(asctime)s - %(levelname)s - %(message)s'
)

class QuoteScraper:
    def __init__(self, base_url: str = "http://quotes.toscrape.com"):
        self.base_url = base_url

    def scrape_quotes(self) -> list:
        import requests
        from bs4 import BeautifulSoup
        quotes = []
        page = 1
        while True:
            url = f"{self.base_url}/page/{page}/" if page > 1 else self.base_url
            try:
                response = requests.get(url)
                response.raise_for_status()
                logging.info(f"Scraped page {page}")
            except Exception as e:
                logging.error(f"Failed to scrape page {page}: {e}")
                break

            soup = BeautifulSoup(response.text, 'html.parser')
            quote_elements = soup.find_all('div', class_='quote')
            if not quote_elements:
                break

            for quote_elem in quote_elements:
                try:
                    quote_text = quote_elem.find('span', class_='text').text
                    author = quote_elem.find('small', class_='author').text
                    tags = [tag.text for tag in quote_elem.find_all('a', class_='tag')]

                    quote = {
                        'quote_text': quote_text,
                        'author': author,
                        'tags': tags
                    }
                    quotes.append(quote)
                except Exception as e:
                    logging.warning(f"Failed to scrape quote: {e}")
                    continue

            page += 1

        logging.info(f"Scraped {len(quotes)} quotes")
        return quotes

def get_unique_tags(quotes: list) -> list:
    tags = set()
    for quote in quotes:
        tags.update(quote['tags'])
    return sorted(tags)

def filter_quotes(quotes: list, tag: str = None) -> list:
    if not tag:
        return quotes
    return [quote for quote in quotes if tag in quote['tags']]

def export_to_csv(quotes: list):
    import pandas as pd
    try:
        df = pd.DataFrame(quotes)
        df.to_csv('quotes.csv', index=False)
        logging.info("Saved quotes to CSV")
    except Exception as e:
        logging.error(f"Failed to save CSV: {e}")
        raise

def generate_visual_report(quotes: list):
    import matplotlib.pyplot as plt
    try:
        if not quotes:
            return

        authors = {}
        for quote in quotes:
            author = quote['author']
            authors[author] = authors.get(author, 0) + 1

        top_authors = dict(sorted(authors.items(), key=lambda x: x[1], reverse=True)[:5])
        names = list(top_authors.keys())
        counts = list(top_authors.values())

        plt.figure(figsize=(8, 6))
        plt.bar(names, counts, color='lightblue')
        plt.xlabel('Authors')
        plt.ylabel('Number of Quotes')
        plt.title('Top 5 Authors by Number of Quotes')
        plt.xticks(rotation=45)
        plt.tight_layout()
        plt.savefig('static/quotes_by_author.png')
        plt.close()
        logging.info("Made chart for report")
    except Exception as e:
        logging.error(f"Failed to make chart: {e}")
        raise

from flask import Flask, render_template, send_file, request
app = Flask(__name__)

@app.route('/', methods=['GET', 'POST'])
def index():
    from jinja2 import Environment, FileSystemLoader
    try:
        scraper = QuoteScraper()
        tag = request.form.get('tag', '') if request.method == 'POST' else ''
        
        quotes = scraper.scrape_quotes()
        quotes = filter_quotes(quotes, tag if tag else None)
        tags = get_unique_tags(quotes)

        export_to_csv(quotes)
        generate_visual_report(quotes)

        env = Environment(loader=FileSystemLoader('templates'))
        template = env.get_template('report.html')
        with open('report.html', 'w') as f:
            f.write(template.render(quotes=quotes, tags=tags))
        logging.info("Made HTML report")

        return app.send_static_file('report.html')
    except Exception as e:
        logging.error(f"Web app error: {e}")
        return f"Error: {e}", 500

@app.route('/download')
def download():
    return send_file('quotes.csv', as_attachment=True)

if __name__ == '__main__':
    app.run(debug=True)