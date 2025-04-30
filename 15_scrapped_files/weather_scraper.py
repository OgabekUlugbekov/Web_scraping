class WeatherScraper:
    def __init__(self, url: str = "https://weather.com/weather/today/l/New+York+NY+USNY0996:1:US"):
        self.url = url

    def scrape_weather(self) -> list:
        import requests
        from bs4 import BeautifulSoup
        weathers = []
        try:
            headers = {'User-Agent': 'Mozilla/5.0'}
            response = requests.get(self.url, headers=headers)
            response.raise_for_status()
            soup = BeautifulSoup(response.text, 'html.parser')
            city = soup.select_one('h1.CurrentConditions--location--1YWj_').text.strip()
            temperature = soup.select_one('span.CurrentConditions--tempValue--MHmYY').text.strip()
            details = soup.select('div.WeatherDetailsListItem--wxData--kK81o')
            humidity = details[2].select_one('span').text.strip() if len(details) > 2 else 'N/A'
            pressure = details[5].select_one('span').text.strip() if len(details) > 5 else 'N/A'

            weathers.append({
                'city': city,
                'temperature': temperature,
                'humidity': humidity,
                'pressure': pressure
            })
        except Exception as e:
            print(f"Error: {e}")
        return weathers

def export_to_json(weathers: list):
    import json
    with open('weather.json', 'w') as f:
        json.dump(weathers, f, indent=2)

from flask import Flask, render_template, send_file
app = Flask(__name__)

@app.route('/')
def index():
    try:
        scraper = WeatherScraper()
        weathers = scraper.scrape_weather()
        export_to_json(weathers)
        return render_template('report.html', weathers=weathers)
    except Exception as e:
        return f"Error: {e}", 500

@app.route('/download')
def download():
    return send_file('weather.json', as_attachment=True)

if __name__ == '__main__':
    app.run(debug=True)