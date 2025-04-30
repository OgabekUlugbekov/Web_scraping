class CoinMarketCapScraper:
    def __init__(self, url: str = "https://coinmarketcap.com/"):
        self.url = url

    def scrape_cryptos(self) -> list:
        import requests
        from bs4 import BeautifulSoup
        cryptos = []
        try:
            headers = {'User-Agent': 'Mozilla/5.0'}
            response = requests.get(self.url, headers=headers)
            response.raise_for_status()
            soup = BeautifulSoup(response.text, 'html.parser')
            crypto_rows = soup.select('tr')[1:21]
            for row in crypto_rows:
                try:
                    name = row.select_one('p.sc-71024e3e-0').text.strip()
                    price = row.select_one('div.sc-b3fc6db-0 a span').text.strip()
                    change = row.select_one('span.sc-6a540de-0').text.strip()

                    cryptos.append({
                        'name': name,
                        'price': price,
                        'change': change
                    })
                except Exception as e:
                    continue
        except Exception as e:
            print(f"Error: {e}")
        return cryptos

def export_to_json(cryptos: list):
    import json
    with open('cryptos.json', 'w') as f:
        json.dump(cryptos, f, indent=2)

from flask import Flask, render_template, send_file
app = Flask(__name__)

@app.route('/')
def index():
    try:
        scraper = CoinMarketCapScraper()
        cryptos = scraper.scrape_cryptos()
        export_to_json(cryptos)
        return render_template('report.html', cryptos=cryptos)
    except Exception as e:
        return f"Error: {e}", 500

@app.route('/download')
def download():
    return send_file('cryptos.json', as_attachment=True)

if __name__ == '__main__':
    app.run(debug=True)