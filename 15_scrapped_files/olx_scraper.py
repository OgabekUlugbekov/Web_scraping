import logging
logging.basicConfig(
    filename='olx_log.log',
    level=logging.INFO,
    format='%(asctime)s - %(levelname)s - %(message)s'
)

class OLXScraper:
    def __init__(self, base_url: str = "https://www.olx.uz/d/elektronika/telefony-i-aksesuary/"):
        self.base_url = base_url

    def scrape_phones(self, max_pages: int = 3) -> list:
        import requests
        from bs4 import BeautifulSoup
        phones = []
        page = 1
        while page <= max_pages:
            url = f"{self.base_url}?page={page}" if page > 1 else self.base_url
            try:
                headers = {'User-Agent': 'Mozilla/5.0'}
                response = requests.get(url, headers=headers)
                response.raise_for_status()
                logging.info(f"Scraped page {page}")
            except Exception as e:
                logging.error(f"Failed to scrape page {page}: {e}")
                break

            soup = BeautifulSoup(response.text, 'html.parser')
            phone_elements = soup.select('div.css-1sw7q4x')
            if not phone_elements:
                break

            for phone_elem in phone_elements:
                try:
                    name = phone_elem.select_one('h6').text.strip()
                    price_elem = phone_elem.select_one('p[data-testid="ad-price"]')
                    price = price_elem.text.strip() if price_elem else "N/A"
                    location_elem = phone_elem.select_one('p[data-testid="location-date"]')
                    location = location_elem.text.split(' - ')[0].strip() if location_elem else "N/A"

                    phone = {
                        'name': name,
                        'price': price,
                        'location': location
                    }
                    phones.append(phone)
                except Exception as e:
                    logging.warning(f"Failed to scrape phone: {e}")
                    continue

            page += 1

        logging.info(f"Scraped {len(phones)} phones")
        return phones

def get_unique_locations(phones: list) -> list:
    locations = set()
    for phone in phones:
        if phone['location'] != "N/A":
            locations.add(phone['location'])
    return sorted(locations)

def filter_phones(phones: list, location: str = None) -> list:
    if not location:
        return phones
    return [phone for phone in phones if phone['location'] == location]

def export_to_csv(phones: list):
    import pandas as pd
    try:
        df = pd.DataFrame(phones)
        df.to_csv('phones.csv', index=False)
        logging.info("Saved phones to CSV")
    except Exception as e:
        logging.error(f"Failed to save CSV: {e}")
        raise

def generate_visual_report(phones: list):
    import matplotlib.pyplot as plt
    try:
        if not phones:
            return

        prices = []
        for phone in phones:
            try:
                price = float(''.join(filter(str.isdigit, phone['price'])))
                prices.append(price)
            except (ValueError, TypeError):
                continue

        if not prices:
            return

        bins = [0, 500000, 1000000, 2000000, 5000000, 10000000]
        labels = ['<500K', '500K-1M', '1M-2M', '2M-5M', '>5M']
        price_ranges = [0] * len(labels)
        for price in prices:
            for i, bin_max in enumerate(bins[1:]):
                if price <= bin_max:
                    price_ranges[i] += 1
                    break

        plt.figure(figsize=(8, 6))
        plt.bar(labels, price_ranges, color='lightblue')
        plt.xlabel('Price Range (UZS)')
        plt.ylabel('Number of Phones')
        plt.title('Price Distribution of Phone Listings')
        plt.tight_layout()
        plt.savefig('static/price_distribution.png')
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
        scraper = OLXScraper()
        location = request.form.get('location', '') if request.method == 'POST' else ''
        
        phones = scraper.scrape_phones(max_pages=3)
        phones = filter_phones(phones, location if location else None)
        locations = get_unique_locations(phones)

        export_to_csv(phones)
        generate_visual_report(phones)

        env = Environment(loader=FileSystemLoader('templates'))
        template = env.get_template('report.html')
        with open('report.html', 'w') as f:
            f.write(template.render(phones=phones, locations=locations))
        logging.info("Made HTML report")

        return app.send_static_file('report.html')
    except Exception as e:
        logging.error(f"Web app error: {e}")
        return f"Error: {e}", 500

@app.route('/download')
def download():
    return send_file('phones.csv', as_attachment=True)

if __name__ == '__main__':
    app.run(debug=True)