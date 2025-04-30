class IndeedScraper:
    def __init__(self, url: str = "https://www.indeed.com/jobs?q=software+developer"):
        self.url = url

    def scrape_jobs(self) -> list:
        import requests
        from bs4 import BeautifulSoup
        jobs = []
        try:
            headers = {'User-Agent': 'Mozilla/5.0'}
            response = requests.get(self.url, headers=headers)
            response.raise_for_status()
            soup = BeautifulSoup(response.text, 'html.parser')
            job_elements = soup.select('div.jobsearch-SerpJobCard')
            for job_elem in job_elements:
                try:
                    name = job_elem.select_one('h2.title a').text.strip()
                    location = job_elem.select_one('div.recJobLoc').get('data-rc-loc') or 'N/A'
                    salary = job_elem.select_one('span.salaryText').text.strip() if job_elem.select_one('span.salaryText') else 'N/A'
                    description = job_elem.select_one('div.summary').text.strip() if job_elem.select_one('div.summary') else 'N/A'

                    jobs.append({
                        'name': name,
                        'location': location,
                        'salary': salary,
                        'description': description
                    })
                except Exception as e:
                    continue
        except Exception as e:
            print(f"Error: {e}")
        return jobs

def export_to_json(jobs: list):
    import json
    with open('jobs.json', 'w') as f:
        json.dump(jobs, f, indent=2)

from flask import Flask, render_template, send_file
app = Flask(__name__)

@app.route('/')
def index():
    try:
        scraper = IndeedScraper()
        jobs = scraper.scrape_jobs()
        export_to_json(jobs)
        return render_template('report.html', jobs=jobs)
    except Exception as e:
        return f"Error: {e}", 500

@app.route('/download')
def download():
    return send_file('jobs.json', as_attachment=True)

if __name__ == '__main__':
    app.run(debug=True)