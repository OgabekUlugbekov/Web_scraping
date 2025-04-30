from selenium import webdriver
from selenium.webdriver.chrome.service import Service
from selenium.webdriver.chrome.options import Options
from selenium.webdriver.common.by import By

class AmazonScraper:
    def __init__(self, url: str = "https://www.amazon.com/s?k=mobile+phones"):
        self.url = url
        chrome_options = Options()
        chrome_options.add_argument("--headless")
        from webdriver_manager.chrome import ChromeDriverManager
        self.driver = webdriver.Chrome(service=Service(ChromeDriverManager().install()), options=chrome_options)

    def scrape_products(self) -> list:
        products = []
        try:
            self.driver.get(self.url)
            product_elements = self.driver.find_elements(By.CSS_SELECTOR, 'div.s-result-item')
            for product_elem in product_elements:
                try:
                    name = product_elem.find_element(By.CSS_SELECTOR, 'h2 a span').text
                    price_whole = product_elem.find_element(By.CSS_SELECTOR, 'span.a-price-whole').text
                    price_fraction = product_elem.find_element(By.CSS_SELECTOR, 'span.a-price-fraction').text
                    price = float(f"{price_whole.replace(',', '')}.{price_fraction}") if price_whole and price_fraction else 0
                    rating = product_elem.find_element(By.CSS_SELECTOR, 'span.a-icon-alt').text
                    rating = float(rating.split(' ')[0]) if rating else 0

                    products.append({
                        'name': name,
                        'price': price,
                        'rating': rating
                    })
                except Exception as e:
                    continue
        except Exception as e:
            print(f"Error: {e}")
        finally:
            self.driver.quit()
        return products

def export_to_json(products: list):
    import json
    with open('products.json', 'w') as f:
        json.dump(products, f, indent=2)

from flask import Flask, render_template, send_file
app = Flask(__name__)

@app.route('/')
def index():
    try:
        scraper = AmazonScraper()
        products = scraper.scrape_products()
        export_to_json(products)
        return render_template('report.html', products=products)
    except Exception as e:
        return f"Error: {e}", 500

@app.route('/download')
def download():
    return send_file('products.json', as_attachment=True)

if __name__ == '__main__':
    app.run(debug=True)