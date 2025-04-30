import logging
logging.basicConfig(
    filename='flipkart_log.log',
    level=logging.INFO,
    format='%(asctime)s - %(levelname)s - %(message)s'
)

class FlipkartScraper:
    def __init__(self, base_url: str = "https://www.flipkart.com/mobiles/pr?sid=tyy%2C4io"):
        self.base_url = base_url

    def scrape_products(self, max_pages: int = 2) -> list:
        import requests
        from bs4 import BeautifulSoup
        products = []
        page = 1
        while page <= max_pages:
            url = f"{self.base_url}&page={page}" if page > 1 else self.base_url
            try:
                headers = {'User-Agent': 'Mozilla/5.0'}
                response = requests.get(url, headers=headers)
                response.raise_for_status()
                logging.info(f"Scraped page {page}")
            except Exception as e:
                logging.error(f"Failed to scrape page {page}: {e}")
                break

            soup = BeautifulSoup(response.text, 'html.parser')
            product_elements = soup.select('div._1AtVbE')
            if not product_elements:
                break

            for product_elem in product_elements:
                try:
                    name_elem = product_elem.select_one('div._4rR01T')
                    name = name_elem.text.strip() if name_elem else "N/A"
                    price_elem = product_elem.select_one('div._30jeq3')
                    price = float(price_elem.text.replace('₹', '').replace(',', '')) if price_elem else 0
                    rating_elem = product_elem.select_one('div._3LWZlK')
                    rating = float(rating_elem.text) if rating_elem else 0

                    if name == "N/A":
                        continue

                    product = {
                        'name': name,
                        'price': price,
                        'rating': rating
                    }
                    products.append(product)
                except Exception as e:
                    logging.warning(f"Failed to scrape product: {e}")
                    continue

            page += 1

        logging.info(f"Scraped {len(products)} products")
        return products

def get_price_ranges(products: list) -> list:
    price_ranges = ['<10000', '10000-20000', '20000-30000', '30000-50000', '>50000']
    return price_ranges

def filter_products(products: list, price_range: str = None) -> list:
    if not price_range:
        return products
    if price_range == '<10000':
        return [p for p in products if p['price'] < 10000]
    elif price_range == '10000-20000':
        return [p for p in products if 10000 <= p['price'] < 20000]
    elif price_range == '20000-30000':
        return [p for p in products if 20000 <= p['price'] < 30000]
    elif price_range == '30000-50000':
        return [p for p in products if 30000 <= p['price'] < 50000]
    else:
        return [p for p in products if p['price'] >= 50000]

def export_to_csv(products: list):
    import pandas as pd
    try:
        df = pd.DataFrame(products)
        df.to_csv('products.csv', index=False)
        logging.info("Saved products to CSV")
    except Exception as e:
        logging.error(f"Failed to save CSV: {e}")
        raise

def generate_visual_report(products: list):
    import matplotlib.pyplot as plt
    try:
        if not products:
            return

        ratings = {'1-2': 0, '2-3': 0, '3-4': 0, '4-5': 0}
        for product in products:
            rating = product['rating']
            if 1 <= rating < 2:
                ratings['1-2'] += 1
            elif 2 <= rating < 3:
                ratings['2-3'] += 1
            elif 3 <= rating < 4:
                ratings['3-4'] += 1
            elif 4 <= rating <= 5:
                ratings['4-5'] += 1

        labels = list(ratings.keys())
        counts = list(ratings.values())

        plt.figure(figsize=(8, 6))
        plt.bar(labels, counts, color='lightblue')
        plt.xlabel('Rating Range')
        plt.ylabel('Number of Products')
        plt.title('Ratings Distribution of Mobile Phones')
        plt.tight_layout()
        plt.savefig('static/ratings_distribution.png')
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
        scraper = FlipkartScraper()
        price_range = request.form.get('price_range', '') if request.method == 'POST' else ''
        
        products = scraper.scrape_products(max_pages=2)
        products = filter_products(products, price_range if price_range else None)
        price_ranges = get_price_ranges(products)

        export_to_csv(products)
        generate_visual_report(products)

        env = Environment(loader=FileSystemLoader('templates'))
        template = env.get_template('report.html')
        with open('report.html', 'w') as f:
            f.write(template.render(products=products, price_ranges=price_ranges))
        logging.info("Made HTML report")

        return app.send_static_file('report.html')
    except Exception as e:
        logging.error(f"Web app error: {e}")
        return f"Error: {e}", 500

@app.route('/download')
def download():
    return send_file('products.csv', as_attachment=True)

if __name__ == '__main__':
    app.run(debug=True)