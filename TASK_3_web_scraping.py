import logging
logging.basicConfig(
    filename='crypto_log.log',
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
                'DATABASE=CryptoDB;'
                'Trusted_Connection=yes;'
            )  # -> connect to SQL Server database
            self.cursor = self.conn.cursor()
            logging.info("Database connected successfully")  # -> write in log that we connected
        except Exception as e:
            logging.error(f"Failed to connect to database: {e}")  # -> write error if we cannot connect
            raise

    def insert_crypto(self, crypto: dict):
        try:
            query = """
            INSERT INTO Cryptocurrencies (Name, Price, Change24h, Change7d, MarketCap)
            VALUES (?, ?, ?, ?, ?)
            """
            self.cursor.execute(query, (
                crypto['name'],
                crypto['price'],
                crypto['change_24h'],
                crypto['change_7d'],
                crypto['market_cap']
            ))  # -> save cryptocurrency to database
            self.conn.commit()
            logging.info(f"Saved cryptocurrency {crypto['name']} to database")
        except Exception as e:
            logging.error(f"Failed to save cryptocurrency: {e}")  # -> write error if save fails
            raise

    def fetch_cryptos(self) -> list:
        try:
            query = """
            SELECT Name, Price, Change24h, Change7d, MarketCap
            FROM Cryptocurrencies
            """
            self.cursor.execute(query)  # -> get all cryptocurrencies from database
            rows = self.cursor.fetchall()
            cryptos = []
            for row in rows:
                cryptos.append({
                    'name': row[0],
                    'price': row[1],
                    'change_24h': row[2],
                    'change_7d': row[3],
                    'market_cap': row[4]
                })
            logging.info(f"Got {len(cryptos)} cryptocurrencies from database")
            return cryptos
        except Exception as e:
            logging.error(f"Failed to fetch cryptocurrencies: {e}")  # -> write error if fetch fails
            raise

    def clear_table(self):
        try:
            self.cursor.execute("DELETE FROM Cryptocurrencies")  # -> clear the cryptocurrencies table
            self.conn.commit()
            logging.info("Cleared cryptocurrencies table")
        except Exception as e:
            logging.error(f"Failed to clear table: {e}")  # -> write error if clear fails
            raise

    def close(self):
        self.conn.close()
        logging.info("Database closed")  # -> write in log that we closed


class CryptoScraper:
    def __init__(self, base_url: str = "https://coinmarketcap.com"):
        self.base_url = base_url

    def scrape_cryptos(self, max_cryptos: int = 20) -> list:
        import requests
        from bs4 import BeautifulSoup
        try:
            headers = {'User-Agent': 'Mozilla/5.0'}  # -> pretend to be a browser
            response = requests.get(self.base_url, headers=headers)  # -> get the web page
            response.raise_for_status()
            logging.info("Scraped CoinMarketCap page")
        except Exception as e:
            logging.error(f"Failed to scrape page: {e}")  # -> write error if scrape fails
            raise

        soup = BeautifulSoup(response.text, 'html.parser')  # -> read the web page
        table = soup.find('table', class_='cmc-table')
        if not table:
            raise ValueError("Could not find the table")

        rows = table.find('tbody').find_all('tr')[:max_cryptos]  # -> get top 20 rows from table
        cryptos = []
        for row in rows:
            try:
                name = row.find('p', class_='sc-71024e3e-0 ehyYKa').text
                price = float(row.find('div', class_='sc-b3fc6b7-0 dzgUIj').text.replace('$', '').replace(',', ''))
                change_24h = float(row.find_all('span', class_='sc-a59753b0-0')[0].text.replace('%', ''))
                change_7d = float(row.find_all('span', class_='sc-a59753b0-0')[1].text.replace('%', ''))
                market_cap = int(row.find('span', class_='sc-11478c5b-1').text.replace('$', '').replace(',', ''))

                crypto = {
                    'name': name,
                    'price': price,
                    'change_24h': change_24h,
                    'change_7d': change_7d,
                    'market_cap': market_cap
                }
                cryptos.append(crypto)
            except Exception as e:
                logging.warning(f"Failed to scrape cryptocurrency: {e}")
                continue

        logging.info(f"Scraped {len(cryptos)} cryptocurrencies")
        return cryptos


def generate_visual_report(cryptos: list):
    import matplotlib.pyplot as plt
    try:
        if not cryptos:
            return

        names = [c['name'] for c in cryptos]
        changes = [c['change_24h'] for c in cryptos]

        plt.figure(figsize=(10, 6))
        plt.bar(names, changes, color='lightcoral')  # -> make chart for 24h change
        plt.xlabel('Cryptocurrencies')
        plt.ylabel('24h Change (%)')
        plt.title('24h Change Percentages of Top 20 Cryptocurrencies')
        plt.xticks(rotation=45)
        plt.tight_layout()
        plt.savefig('static/change_24h.png')
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
        scraper = CryptoScraper()

        if request.method == 'POST':
            db.clear_table()
            cryptos = scraper.scrape_cryptos(max_cryptos=20)  # -> scrape new cryptocurrencies
            cryptos = sorted(cryptos, key=lambda x: x['market_cap'], reverse=True)  # -> sort by market cap
            for crypto in cryptos:
                db.insert_crypto(crypto)

        cryptos = db.fetch_cryptos()  # -> get cryptocurrencies from database
        generate_visual_report(cryptos)  # -> make chart

        env = Environment(loader=FileSystemLoader('templates'))
        template = env.get_template('report.html')
        with open('report.html', 'w') as f:
            f.write(template.render(cryptos=cryptos))
        logging.info("Made HTML report")

        db.close()
        return app.send_static_file('report.html')
    except Exception as e:
        logging.error(f"Web app error: {e}")
        return f"Error: {e}", 500


if __name__ == '__main__':
    app.run(debug=True)