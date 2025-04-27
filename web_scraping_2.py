
import logging
logging.basicConfig(
    filename='job_log.log',
    level=logging.INFO,
    format='%(asctime)s - %(levelname)s - %(message)s'
)


class DatabaseManager:
    def __init__(self):
        import pyodbc
        try:
            self.conn = pyodbc.connect(
                'DRIVER={SQL Server};'
                'SERVER=DESKTOP-XXXX\\SQLEXPRESS;'
                'DATABASE=JobsDB;'
                'Trusted_Connection=yes;'
            )  # -> conect to sql server databse
            self.cursor = self.conn.cursor()
            logging.info("Databse conected sucessfully")
        except Exception as e:
            logging.error(f"Failed to conect to databse: {e}")
            raise

    def insert_job(self, job: dict):
        try:
            query = """
            INSERT INTO Jobs (JobTitle, Company, Location, PostDate, Description)
            VALUES (?, ?, ?, ?, ?)
            """
            self.cursor.execute(query, (
                job['job_title'],
                job['company'],
                job['location'],
                job['post_date'],
                job['description']
            ))  # -> save job to database
            self.conn.commit()
            logging.info(f"Saved job {job['job_title']} to databse")
        except Exception as e:
            logging.error(f"Failed to save job: {e}")  # -> write error if save fails
            raise

    def fetch_jobs(self) -> list:
        try:
            query = """
            SELECT JobTitle, Company, Location, PostDate, Description
            FROM Jobs
            """
            self.cursor.execute(query)  # -> get all jobs from databse
            rows = self.cursor.fetchall()
            jobs = []
            for row in rows:
                jobs.append({
                    'job_title': row[0],
                    'company': row[1],
                    'location': row[2],
                    'post_date': row[3],
                    'description': row[4]
                })
            logging.info(f"Got {len(jobs)} jobs from databse")
            return jobs
        except Exception as e:
            logging.error(f"Failed to fetch jobs: {e}")  # -> write error if fetch fails
            raise

    def clear_table(self):
        try:
            self.cursor.execute("DELETE FROM Jobs")  # -> clear the jobs tabel
            self.conn.commit()
            logging.info("Cleared jobs tabel")
        except Exception as e:
            logging.error(f"Failed to clear tabel: {e}")  # -> write error if clear fails
            raise

    def close(self):
        self.conn.close()
        logging.info("Databse closed")  # -> write in diary we closed


class JobScraper:
    def __init__(self):
        from selenium import webdriver  # -> to use browser for skraping
        from selenium.webdriver.chrome.service import Service  # -> to set up browser service
        from webdriver_manager.chrome import ChromeDriverManager  # -> to get browser driver
        from selenium.webdriver.common.by import By  # -> to find stuff on web page
        try:
            service = Service(ChromeDriverManager().install())
            self.driver = webdriver.Chrome(service=service)  # -> start the browser
            logging.info("Browser started for skraping")
        except Exception as e:
            logging.error(f"Failed to start browser: {e}")  # -> write error if browser fails
            raise

    def scrape_jobs(self, max_jobs: int = 20) -> list:
        from selenium.webdriver.common.by import By  # -> already imported, but needed here
        import time  # -> to wait while scraping
        jobs = []
        url = "https://www.linkedin.com/jobs/search/?keywords=Python%20Developer"
        self.driver.get(url)  # -> go to linkedin jobs page
        logging.info("Opened LinkedIn jobs page")

        last_height = self.driver.execute_script("return document.body.scrollHeight")
        while len(jobs) < max_jobs:
            job_cards = self.driver.find_elements(By.CSS_SELECTOR, "div.job-search-card")  # -> find job cards on page
            for card in job_cards:
                try:
                    job_title = card.find_element(By.CSS_SELECTOR, "h3.base-search-card__title").text
                    company = card.find_element(By.CSS_SELECTOR, "h4.base-search-card__subtitle").text
                    location = card.find_element(By.CSS_SELECTOR, "span.job-search-card__location").text
                    post_date = card.find_element(By.CSS_SELECTOR, "time.job-search-card__listdate").text
                    description = card.find_element(By.CSS_SELECTOR,
                                                    "div.job-search-card__snippet").text if card.find_elements(
                        By.CSS_SELECTOR, "div.job-search-card__snippet") else "No description"

                    job = {
                        'job_title': job_title,
                        'company': company,
                        'location': location,
                        'post_date': post_date,
                        'description': description
                    }
                    if job not in jobs:  # -> dont add same job twice
                        jobs.append(job)
                except Exception as e:
                    logging.warning(f"Failed to skrap job: {e}")
                    continue

            if len(jobs) >= max_jobs:
                break

            self.driver.execute_script("window.scrollTo(0, document.body.scrollHeight);")  # -> scroll to load more jobs
            time.sleep(2)  # -> wait for page to load
            new_height = self.driver.execute_script("return document.body.scrollHeight")
            if new_height == last_height:
                break
            last_height = new_height

        logging.info(f"Skraped {len(jobs)} jobs")
        return jobs

    def close(self):
        self.driver.quit()
        logging.info("Browser closed")  # -> write in diary we closed browser


def export_to_csv(jobs: list):
    import pandas as pd  # -> to make csv file
    try:
        df = pd.DataFrame(jobs)
        df.to_csv('jobs.csv', index=False)  # -> save jobs to csv file
        logging.info("Saved jobs to csv")
    except Exception as e:
        logging.error(f"Failed to save csv: {e}")  # -> write error if csv fails
        raise


def generate_visual_report(jobs: list):
    import matplotlib.pyplot as plt  # -> to make charts in generate_visual_report
    try:
        if not jobs:
            return

        companies = {}
        for job in jobs:
            company = job['company']
            companies[company] = companies.get(company, 0) + 1

        top_companies = dict(sorted(companies.items(), key=lambda x: x[1], reverse=True)[:5])  # -> get top 5 companiyas
        names = list(top_companies.keys())
        counts = list(top_companies.values())

        plt.figure(figsize=(8, 6))
        plt.bar(names, counts, color='lightblue')  # -> make chart for jobs by companies
        plt.xlabel('Companies')
        plt.ylabel('Number of Jobs')
        plt.title('Top 5 Companies with Python Developer Jobs')
        plt.xticks(rotation=45)
        plt.tight_layout()
        plt.savefig('static/jobs_by_company.png')  # -> save the chart
        plt.close()
        logging.info("Made chart for report")
    except Exception as e:
        logging.error(f"Failed to make chart: {e}")
        raise



from flask import Flask, render_template, send_file  # -> to make web page and send csv

app = Flask(__name__)


@app.route('/', methods=['GET', 'POST'])
def index():
    from jinja2 import Environment, FileSystemLoader  # -> to make html report in index function
    try:
        db = DatabaseManager()
        scraper = JobScraper()

        if request.method == 'POST':
            db.clear_table()  # -> clear old data
            jobs = scraper.scrape_jobs(max_jobs=20)  # -> scrap new jobs
            for job in jobs:
                db.insert_job(job)

        jobs = db.fetch_jobs()
        export_to_csv(jobs)
        generate_visual_report(jobs)

        env = Environment(loader=FileSystemLoader('templates'))
        template = env.get_template('report.html')
        with open('report.html', 'w') as f:
            f.write(template.render(jobs=jobs))
        logging.info("Made html report")

        scraper.close()
        db.close()
        return app.send_static_file('report.html')
    except Exception as e:
        logging.error(f"Web app error: {e}")
        return f"Error: {e}", 500


if __name__ == '__main__':
    app.run(debug=True)