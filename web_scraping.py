
import logging  
logging.basicConfig(
    filename='book_log.log',
    level=logging.INFO,
    format='%(asctime)s - %(levelname)s - %(message)s'  # -> to track every important step of this program
)


class DatabaseManager:
    def __init__(self):
        import pyodbc
        try:
            self.conn = pyodbc.connect(
                'DRIVER={SQL Server};'
                'SERVER=DESKTOP-XXXX\\SQLEXPRESS;'
                'DATABASE=BooksDB;'
                'Trusted_Connection=yes;'
            )  # -> conect to sql server databse
            self.cursor = self.conn.cursor()
            logging.info("Databse conected sucessfully")
        except Exception as e:
            logging.error(f"Failed to conect to databse: {e}")
            raise

    def insert_book(self, book: dict):
        try:
            query = """
            INSERT INTO Books (Title, Price, Rating, Category, Availability, ReviewCount)
            VALUES (?, ?, ?, ?, ?, ?)
            """
            self.cursor.execute(query, (
                book['title'],
                book['price'],
                book['rating'],
                book['category'],
                book['availability'],
                book['review_count']
            ))  # -> save book to databse
            self.conn.commit()
            logging.info(f"Saved book {book['title']} to databse")
        except Exception as e:
            logging.error(f"Failed to save book: {e}")  # -> write error if save fails
            raise

    def fetch_books(self) -> list:
        import pandas as pd
        try:
            query = """
            SELECT Title, Price, Rating, Category, Availability, ReviewCount, ValueScore
            FROM Books
            """
            self.cursor.execute(query)  # -> get all books from databse
            rows = self.cursor.fetchall()
            books = []
            for row in rows:
                books.append({
                    'title': row[0],
                    'price': row[1],
                    'rating': row[2],
                    'category': row[3],
                    'availability': row[4],
                    'review_count': row[5],
                    'value_score': row[6]
                })
            logging.info(f"Got {len(books)} books from databse")
            return books
        except Exception as e:
            logging.error(f"Failed to fetch books: {e}")
            raise

    def clear_table(self):
        try:
            self.cursor.execute("DELETE FROM Books")  # -> clear the books tabel
            self.conn.commit()
            logging.info("Cleared books tabel")
        except Exception as e:
            logging.error(f"Failed to clear tabel: {e}")
            raise

    def close(self):
        self.conn.close()
        logging.info("Databse closed")


class BookScraper:
    def __init__(self, base_url: str = "http://books.toscrape.com"):
        self.base_url = base_url

    def scrape_books(self, max_pages: int = 2) -> list:
        import requests
        from bs4 import BeautifulSoup
        books = []
        page = 1
        while page <= max_pages:
            url = f"{self.base_url}/catalogue/page-{page}.html" if page > 1 else f"{self.base_url}/index.html"
            try:
                response = requests.get(url)  # -> get the web page
                response.raise_for_status()
                logging.info(f"Skraped page {page}")
            except Exception as e:
                logging.error(f"Failed to skrap page {page}: {e}")  # -> write error if scrap fails
                break

            soup = BeautifulSoup(response.text, 'html.parser')  # -> read the web page
            book_elements = soup.select('article.product_pod')
            if not book_elements:
                break

            for book_elem in book_elements:
                title = book_elem.select_one('h3 a')['title']
                price = float(book_elem.select_one('.price_color').text.replace('£', ''))

                rating_elem = book_elem.select_one('p.star-rating')
                rating_classes = rating_elem['class']
                rating = {'One': 1, 'Two': 2, 'Three': 3, 'Four': 4, 'Five': 5}.get(rating_classes[1],
                                                                                    0)  # -> get ratings

                book_url = book_elem.select_one('h3 a')['href']
                book_page = requests.get(f"{self.base_url}/catalogue/{book_url}")
                book_soup = BeautifulSoup(book_page.text, 'html.parser')  # -> go to book page for more info

                category = book_soup.select_one('.breadcrumb li:nth-child(3) a').text
                availability = book_soup.select_one('.availability').text.strip()
                review_count = int(book_soup.select_one('.product_page > p:nth-last-child(2)').text.split()[
                                       0]) if book_soup.select_one('.product_page > p:nth-last-child(2)') else 0

                book = {
                    'title': title,
                    'price': price,
                    'rating': rating,
                    'category': category,
                    'availability': availability,
                    'review_count': review_count
                }
                books.append(book)
            page += 1

        logging.info(f"Skraped {len(books)} books")
        return books


def generate_visual_report(books: list):
    import matplotlib.pyplot as plt  # -> to make charts in generate_visual_report
    try:
        if not books:
            return

        top_books = sorted(books, key=lambda x: x['value_score'], reverse=True)[:5]  # -> sort by value score
        titles = [b['title'][:20] for b in top_books]
        value_scores = [b['value_score'] for b in top_books]

        plt.figure(figsize=(8, 6))
        plt.bar(titles, value_scores, color='lightgreen')  # -> make chart for top books
        plt.xlabel('Books')
        plt.ylabel('Value Score (Rating/Price)')
        plt.title('Top 5 Books by Value Score')
        plt.xticks(rotation=45)
        plt.tight_layout()
        plt.savefig('static/top_books.png')  # -> save the chart
        plt.close()
        logging.info("Made chart for report")
    except Exception as e:
        logging.error(f"Failed to make chart: {e}")  # -> write error if chart fails
        raise

from flask import Flask, render_template

app = Flask(__name__)


@app.route('/', methods=['GET', 'POST'])
def index():
    from jinja2 import Environment, FileSystemLoader
    try:
        db = DatabaseManager()
        scraper = BookScraper()

        if request.method == 'POST':
            db.clear_table()  # -> clear old data
            books = scraper.scrape_books(max_pages=2)  # -> scrap new books
            for book in books:
                db.insert_book(book)  # -> save each book to databse

        books = db.fetch_books()
        generate_visual_report(books)

        env = Environment(loader=FileSystemLoader('templates'))
        template = env.get_template('report.html')
        with open('report.html', 'w') as f:
            f.write(template.render(books=books))
        logging.info("Made html report")

        db.close()
        return app.send_static_file('report.html')
    except Exception as e:
        logging.error(f"Web app error: {e}")
        return f"Error: {e}", 500


if __name__ == '__main__':
    app.run(debug=True)