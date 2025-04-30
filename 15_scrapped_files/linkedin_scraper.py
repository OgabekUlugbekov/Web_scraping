from selenium import webdriver
from selenium.webdriver.chrome.service import Service
from selenium.webdriver.chrome.options import Options
from selenium.webdriver.common.by import By

class LinkedInScraper:
    def __init__(self, url: str = "https://www.linkedin.com/jobs/search/?keywords=python%20developer"):
        self.url = url
        chrome_options = Options()
        chrome_options.add_argument("--headless")
        from webdriver_manager.chrome import ChromeDriverManager
        self.driver = webdriver.Chrome(service=Service(ChromeDriverManager().install()), options=chrome_options)

    def scrape_jobs(self) -> list:
        jobs = []
        try:
            self.driver.get(self.url)
            job_elements = self.driver.find_elements(By.CSS_SELECTOR, 'div.base-card')
            for job_elem in job_elements:
                try:
                    position = job_elem.find_element(By.CSS_SELECTOR, 'h3.base-search-card__title').text
                    location = job_elem.find_element(By.CSS_SELECTOR, 'span.job-search-card__location').text
                    company = job_elem.find_element(By.CSS_SELECTOR, 'h4.base-search-card__subtitle').text

                    jobs.append({
                        'position': position,
                        'location': location,
                        'company': company
                    })
                except Exception as e:
                    continue
        except Exception as e:
            print(f"Error: {e}")
        finally:
            self.driver.quit()
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
        scraper = LinkedInScraper()
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