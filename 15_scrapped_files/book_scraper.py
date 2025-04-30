import logging
logging.basicConfig(
    filename='book_log.log',
    level=logging.INFO,
    format='%(asctime)s - %(levelname)s - %(message)s'
)

class BookScraper:
    def __init__(self, base_url: str = "https://books.toscrape.com"):
        self.base_url = base_url

    def scrape_books(self) -> list:
        import requests
        from bs4 import BeautifulSoup
        books = []
        page = 1
        while True:
            url = f"{self.base_url}/catalogue/page-{page}.html" if page > 1 else f"{self.base_url}/index.html"
            try:
                response = requests.get(url)
                response.raise_for_status()
                logging.info(f"Scraped page {page}")
            except Exception as e:
                logging.error(f"Failed to scrape page {page}: {e}")
                break

            soup = BeautifulSoup(response.text, 'html.parser')
            book_elements = soup.select('article.product_pod')
            if not book_elements:
                break

            for book_elem in book_elements:
                try:
                    title = book_elem.select_one('h3 a')['title']
                    price = float(book_elem.select_one('.price_color').text.replace('£', ''))

                    rating_elem = book_elem.select_one('p.star-rating')
                    rating_classes = rating_elem['class']
                    rating = {'One': 1, 'Two': 2, 'Three': 3, 'Four': 4, 'Five': 5}.get(rating_classes[1], 0)

                    book_url = book_elem.select_one('h3 a')['href']
                    book_page = requests.get(f"{self.base_url}/catalogue/{book_url}")
                    book_soup = BeautifulSoup(book_page.text, 'html.parser')

                    category = book_soup.select_one('.breadcrumb li:nth-child(3) a').text
                    availability = book_soup.select_one('.availability').text.strip()

                    book = {
                        'title': title,
                        'price': price,
                        'rating': rating,
                        'category': category,
                        'availability': availability
                    }
                    books.append(book)
                except Exception as e:
                    logging.warning(f"Failed to scrape book: {e}")
                    continue

            page += 1

        logging.info(f"Scraped {len(books)} books")
        return books

def get_unique_categories(books: list) -> list:
    categories = set()
    for book in books:
        categories.add(book['category'])
    return sorted(categories)

def filter_books(books: list, category: str = None) -> list:
    if not category:
        return books
    return [book for book in books if book['category'] == category]

def export_to_csv(books: list):
    import pandas as pd
    try:
        df = pd.DataFrame(books)
        df.to_csv('books.csv', index=False)
        logging.info("Saved books to CSV")
    except Exception as e:
        logging.error(f"Failed to save CSV: {e}")
        raise

def generate_visual_report(books: list):
    import matplotlib.pyplot as plt
    try:
        if not books:
            return

        ratings = {'1': 0, '2': 0, '3': 0, '4': 0, '5': 0}
        for book in books:
            ratings[str(book['rating'])] += 1

        labels = list(ratings.keys())
        counts = list(ratings.values())

        plt.figure(figsize=(8, 6))
        plt.bar(labels, counts, color='lightgreen')
        plt.xlabel('Rating')
        plt.ylabel('Number of Books')
        plt.title('Distribution of Books by Rating')
        plt.tight_layout()
        plt.savefig('static/books_by_rating.png')
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
        scraper = BookScraper()
        category = request.form.get('category', '') if request.method == 'POST' else ''
        
        books = scraper.scrape_books()
        books = filter_books(books, category if category else None)
        categories = get_unique_categories(books)

        export_to_csv(books)
        generate_visual_report(books)

        env = Environment(loader=FileSystemLoader('templates'))
        template = env.get_template('report.html')
        with open('report.html', 'w') as f:
            f.write(template.render(books=books, categories=categories))
        logging.info("Made HTML report")

        return app.send_static_file('report.html')
    except Exception as e:
        logging.error(f"Web app error: {e}")
        return f"Error: {e}", 500

@app.route('/download')
def download():
    return send_file('books.csv', as_attachment=True)

if __name__ == '__main__':
    app.run(debug=True)