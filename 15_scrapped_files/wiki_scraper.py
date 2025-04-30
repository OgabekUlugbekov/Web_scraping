import logging
logging.basicConfig(
    filename='wiki_log.log',
    level=logging.INFO,
    format='%(asctime)s - %(levelname)s - %(message)s'
)

class WikiScraper:
    def __init__(self, base_url: str = "https://en.wikipedia.org/wiki/", article: str = "Python_(programming_language)"):
        self.url = f"{base_url}{article}"

    def scrape_article(self) -> tuple:
        import requests
        from bs4 import BeautifulSoup
        contents = []
        infobox = {}
        images = []
        try:
            headers = {'User-Agent': 'Mozilla/5.0'}
            response = requests.get(self.url, headers=headers)
            response.raise_for_status()
            logging.info("Scraped Wikipedia page")
        except Exception as e:
            logging.error(f"Failed to scrape page: {e}")
            return contents, infobox, images

        soup = BeautifulSoup(response.text, 'html.parser')

        current_heading = "Introduction"
        for element in soup.select('#mw-content-text .mw-parser-output > *'):
            if element.name in ['h2', 'h3']:
                heading_span = element.select_one('.mw-headline')
                if heading_span:
                    current_heading = heading_span.text
            elif element.name == 'p' and element.text.strip():
                contents.append({
                    'heading': current_heading,
                    'paragraph': element.text.strip()
                })

        infobox_table = soup.select_one('.infobox')
        if infobox_table:
            rows = infobox_table.select('tr')
            for row in rows:
                th = row.select_one('th')
                td = row.select_one('td')
                if th and td:
                    key = th.text.strip()
                    value = td.text.strip()
                    infobox[key] = value

        image_elements = soup.select('.mw-parser-output img')
        for img in image_elements:
            src = img.get('src', '')
            if src.startswith('//'):
                src = f"https:{src}"
            elif src.startswith('/'):
                src = f"https://en.wikipedia.org{src}"
            if src and src not in images:
                images.append(src)

        logging.info(f"Scraped {len(contents)} paragraphs, {len(infobox)} infobox items, {len(images)} images")
        return contents, infobox, images

def get_unique_headings(contents: list) -> list:
    headings = set()
    for content in contents:
        headings.add(content['heading'])
    return sorted(headings)

def filter_contents(contents: list, heading: str = None) -> list:
    if not heading:
        return contents
    return [content for content in contents if content['heading'] == heading]

def export_to_csv(contents: list, infobox: dict, images: list):
    import pandas as pd
    try:
        content_df = pd.DataFrame(contents)
        content_df.to_csv('articles.csv', index=False, mode='w')

        infobox_df = pd.DataFrame(list(infobox.items()), columns=['Key', 'Value'])
        with open('articles.csv', 'a') as f:
            f.write("\nInfobox Data\n")
            infobox_df.to_csv(f, index=False)

        images_df = pd.DataFrame(images, columns=['Image URL'])
        with open('articles.csv', 'a') as f:
            f.write("\nImage Links\n")
            images_df.to_csv(f, index=False)

        logging.info("Saved data to CSV")
    except Exception as e:
        logging.error(f"Failed to save CSV: {e}")
        raise

def generate_visual_report(contents: list):
    import matplotlib.pyplot as plt
    try:
        if not contents:
            return

        heading_counts = {}
        for content in contents:
            heading = content['heading']
            heading_counts[heading] = heading_counts.get(heading, 0) + 1

        top_headings = dict(sorted(heading_counts.items(), key=lambda x: x[1], reverse=True)[:5])
        headings = list(top_headings.keys())
        counts = list(top_headings.values())

        plt.figure(figsize=(10, 6))
        plt.bar(headings, counts, color='lightgreen')
        plt.xlabel('Headings')
        plt.ylabel('Number of Paragraphs')
        plt.title('Top 5 Headings by Number of Paragraphs')
        plt.xticks(rotation=45)
        plt.tight_layout()
        plt.savefig('static/paragraphs_per_heading.png')
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
        scraper = WikiScraper()
        heading = request.form.get('heading', '') if request.method == 'POST' else ''
        
        contents, infobox, images = scraper.scrape_article()
        contents = filter_contents(contents, heading if heading else None)
        headings = get_unique_headings(contents)

        export_to_csv(contents, infobox, images)
        generate_visual_report(contents)

        env = Environment(loader=FileSystemLoader('templates'))
        template = env.get_template('report.html')
        with open('report.html', 'w') as f:
            f.write(template.render(contents=contents, infobox=infobox, images=images, headings=headings))
        logging.info("Made HTML report")

        return app.send_static_file('report.html')
    except Exception as e:
        logging.error(f"Web app error: {e}")
        return f"Error: {e}", 500

@app.route('/download')
def download():
    return send_file('articles.csv', as_attachment=True)

if __name__ == '__main__':
    app.run(debug=True)