import logging
logging.basicConfig(
    filename='imdb_log.log',
    level=logging.INFO,
    format='%(asctime)s - %(levelname)s - %(message)s'
)

class IMDBScraper:
    def __init__(self, base_url: str = "https://www.imdb.com/chart/top/"):
        self.base_url = base_url

    def scrape_movies(self, max_movies: int = 100) -> list:
        import requests
        from bs4 import BeautifulSoup
        movies = []
        try:
            headers = {'User-Agent': 'Mozilla/5.0'}
            response = requests.get(self.base_url, headers=headers)
            response.raise_for_status()
            logging.info("Scraped IMDB Top 250 page")
        except Exception as e:
            logging.error(f"Failed to scrape page: {e}")
            return movies

        soup = BeautifulSoup(response.text, 'html.parser')
        movie_elements = soup.select('li.ipc-metadata-list-summary-item')[:max_movies]
        
        for movie_elem in movie_elements:
            try:
                title = movie_elem.select_one('h3').text.split('. ')[1]
                year = int(movie_elem.select_one('.sc-b189961a-8').text)
                rating = float(movie_elem.select_one('.ipc-rating-star--imdb').text.split('\xa0')[0])

                movie = {
                    'title': title,
                    'year': year,
                    'rating': rating
                }
                movies.append(movie)
            except Exception as e:
                logging.warning(f"Failed to scrape movie: {e}")
                continue

        logging.info(f"Scraped {len(movies)} movies")
        return movies

def get_unique_decades(movies: list) -> list:
    decades = set()
    for movie in movies:
        decade = (movie['year'] // 10) * 10
        decades.add(decade)
    return sorted(decades)

def filter_movies(movies: list, decade: str = None) -> list:
    if not decade:
        return movies
    decade = int(decade)
    return [movie for movie in movies if (movie['year'] // 10) * 10 == decade]

def export_to_csv(movies: list):
    import pandas as pd
    try:
        df = pd.DataFrame(movies)
        df.to_csv('movies.csv', index=False)
        logging.info("Saved movies to CSV")
    except Exception as e:
        logging.error(f"Failed to save CSV: {e}")
        raise

def generate_visual_report(movies: list):
    import matplotlib.pyplot as plt
    try:
        if not movies:
            return

        ratings_by_decade = {}
        for movie in movies:
            decade = (movie['year'] // 10) * 10
            if decade not in ratings_by_decade:
                ratings_by_decade[decade] = []
            ratings_by_decade[decade].append(movie['rating'])

        decades = sorted(ratings_by_decade.keys())
        avg_ratings = [sum(ratings_by_decade[decade]) / len(ratings_by_decade[decade]) for decade in decades]

        plt.figure(figsize=(8, 6))
        plt.bar([str(decade) for decade in decades], avg_ratings, color='lightcoral')
        plt.xlabel('Decade')
        plt.ylabel('Average Rating')
        plt.title('Average Rating of Top 100 Movies by Decade')
        plt.tight_layout()
        plt.savefig('static/ratings_by_decade.png')
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
        scraper = IMDBScraper()
        decade = request.form.get('decade', '') if request.method == 'POST' else ''
        
        movies = scraper.scrape_movies(max_movies=100)
        movies = filter_movies(movies, decade if decade else None)
        decades = get_unique_decades(movies)

        export_to_csv(movies)
        generate_visual_report(movies)

        env = Environment(loader=FileSystemLoader('templates'))
        template = env.get_template('report.html')
        with open('report.html', 'w') as f:
            f.write(template.render(movies=movies, decades=decades))
        logging.info("Made HTML report")

        return app.send_static_file('report.html')
    except Exception as e:
        logging.error(f"Web app error: {e}")
        return f"Error: {e}", 500

@app.route('/download')
def download():
    return send_file('movies.csv', as_attachment=True)

if __name__ == '__main__':
    app.run(debug=True)