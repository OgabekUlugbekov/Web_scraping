class GoodreadsScraper:
    def __init__(self, url: str = "https://www.goodreads.com/list/show/1.Best_Books_Ever"):
        self.url = url

    def scrape_books(self) -> list:
        import requests
        from bs4 import BeautifulSoup
        books = []
        try:
            headers = {'User-Agent': 'Mozilla/5.0'}
            response = requests.get(self.url, headers=headers)
            response.raise_for_status()
            soup = BeautifulSoup(response.text, 'html.parser')
            book_elements = soup.select('tr[itemtype="http://schema.org/Book"]')
            for book_elem in book_elements:
                try:
                    title = book_elem.select_one('a.bookTitle').text.strip()
                    author = book_elem.select_one('a.authorName').text.strip()
                    rating = book_elem.select_one('span.minirating').text.strip().split(' ')[0]

                    books.append({
                        'title': title,
                        'author': author,
                        'rating': rating
                    })
                except Exception as e:
                    continue
        except Exception as e:
            print(f"Error: {e}")
        return books

def export_to_json(books: list):
    import json
    with open('books.json', 'w') as f:
        json.dump(books, f, indent=2)

from flask import Flask, render_template, send_file
app = Flask(__name__)

@app.route('/')
def index():
    try:
        scraper = GoodreadsScraper()
        books = scraper.scrape_books()
        export_to_json(books)
        return render_template('report.html', books=books)
    except Exception as e:
        return f"Error: {e}", 500

@app.route('/download')
def download():
    return send_file('books.json', as_attachment=True)

if __name__ == '__main__':
    app.run(debug=True)