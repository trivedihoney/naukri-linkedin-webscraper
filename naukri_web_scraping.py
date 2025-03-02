import os
import time
import datetime
import sqlite3
from selenium import webdriver
from selenium.webdriver.chrome.options import Options
from selenium.webdriver.remote.webdriver import WebDriver
from bs4 import BeautifulSoup
import pandas as pd
from dataclasses import dataclass

@dataclass
class JobListing:
    job_title : str
    job_location : str
    site : str
    title : str
    company : str
    ratings : str
    reviews : str
    experience : str
    salary : str
    location : str
    description : str
    job_post_date : datetime.date
    url : str

    def dict(self):
        return self.__dict__
    
job_title = 'Data Scientist'
job_location = ''
number_of_pages = 10

def naukri_url_maker(job_title: str, job_location: str | None = None, no_of_pages: int = 1):
    urls = []
    job_title1 = f'{job_title.strip().replace(" ", "-").lower()}-jobs'
    job_title2 = job_title.replace(" ", "%20").lower()
    job_location1 = job_location.strip().replace(" ", "-").lower() if job_location else ""
    job_location2 = job_location.replace(" ", "%20").lower() if job_location else ""

    for i in range(no_of_pages):
        page_no = f'-{i+1}' if i > 0 else ""
        location_part = f'-in-{job_location1}' if job_location else ""
        url = f'https://www.naukri.com/{job_title1}{location_part}{page_no}?k={job_title2}'
        if job_location:
            url += f'&l={job_location2}'
        urls.append(url)
    return urls

def get_naukri_listings(driver : WebDriver, urls : list):
    results = []
    for url in urls:
        print(f'Getting data from {url}')
        driver.get(url)
        time.sleep(3)
        soup = BeautifulSoup(driver.page_source, 'html5lib')
        page_results = soup.find_all(class_= 'cust-job-tuple layout-wrapper lay-2 sjw__tuple')
        if not results:
            results = page_results
        else:
            results.extend(page_results)

    job_listings = []
    
    for result in results:
        title = result.find('a', class_='title')
        company = result.select_one('a.comp-name')
        rating = result.find('a', class_='rating')
        job_post_day = result.find('span', class_='job-post-day')
        description = result.find('span', class_='job-desc ni-job-tuple-icon ni-job-tuple-icon-srp-description')
        review = result.find('a', class_='review ver-line')
        experience = result.find('span', class_='expwdth')
        salary = result.find('span', class_='ni-job-tuple-icon ni-job-tuple-icon-srp-rupee sal')
        location = result.find('span', class_='locWdth')


        job_post_date = None
        if job_post_day:
            job_post_day = str(job_post_day.text)
            if 'few' in job_post_day.lower():
                job_post_date = datetime.date.today()
            elif 'today' in job_post_day.lower():
                job_post_date = datetime.date.today()
            elif 'yesterday' in job_post_day.lower():
                job_post_date = datetime.date.today() - datetime.timedelta(days=1)
            elif 'just' in job_post_day.lower():
                job_post_date = datetime.date.today()
            else:
                job_post_day = job_post_day.split()[0]
                # Remove '+' sign from the day if present
                if '+' in job_post_day:
                    job_post_day =job_post_day.replace('+', '')
                job_post_date = datetime.date.today() - datetime.timedelta(days=int(job_post_day))
                    

        job_listing = JobListing(
            site = 'Naukri',
            job_title = job_title,
            job_location = job_location,
            title = title.text if title else None,
            company = company.text if company else None,
            ratings = rating.text if rating else None,
            reviews = review.text if review else None,
            experience = experience.text if experience else None,
            salary = salary.text if salary else None,
            location = location.text if location else None,
            description = description.text if description else None,
            job_post_date = str(job_post_date),
            url = title.get('href') if title else None
        )

        job_listings.append(job_listing)
    print(f'Found {len(job_listings)} job listings')
    return job_listings

def init_db():
    conn = sqlite3.connect('naukri_jobs.db')
    cursor = conn.cursor()
    cursor.execute('''
        CREATE TABLE IF NOT EXISTS jobs (
            id INTEGER PRIMARY KEY,
            applied BOOLEAN DEFAULT FALSE,
            reject BOOLEAN DEFAULT FALSE,
            job_title TEXT,
            job_location TEXT,
            site TEXT,
            title TEXT,
            company TEXT,
            ratings TEXT,
            reviews TEXT,
            experience TEXT,
            salary TEXT,
            location TEXT,
            description TEXT,
            job_post_date TEXT,
            url TEXT UNIQUE,
            date_added TIMESTAMP DEFAULT CURRENT_TIMESTAMP
        )
    ''')
    conn.commit()
    conn.close()

def save_to_db(job_listings: list[JobListing]):
    conn = sqlite3.connect('naukri_jobs.db')
    cursor = conn.cursor()
    duplicate_count = 0
    for job in job_listings:
        try:
            cursor.execute('''
                INSERT INTO jobs (job_title, job_location, site, title, company, ratings, reviews, experience, salary, location, description, job_post_date, url)
                VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
            ''', (job.job_title, job.job_location, job.site, job.title, job.company, job.ratings, job.reviews, job.experience, job.salary, job.location, job.description, job.job_post_date, job.url))
        except sqlite3.IntegrityError:
            # Skip duplicate URLs
            duplicate_count += 1
    conn.commit()
    conn.close()
    print(f'Found {duplicate_count} duplicate job listings')
    print(f'Saved {len(job_listings) - duplicate_count} new job listings to the database')

def export_to_xlsx():
    conn = sqlite3.connect('naukri_jobs.db')
    df = pd.read_sql_query('SELECT * FROM jobs', conn)
    df.to_excel('naukri_jobs.xlsx', index=False)
    conn.close()

def scrape_naukri(job_title: str, job_location: str | None = None, no_of_pages: int = 1):
    urls = naukri_url_maker(job_title, job_location, no_of_pages)
    options = Options()
    # options.add_argument('--headless')
    if urls:
        driver = webdriver.Edge(options=options)
        job_listings: list[JobListing] = get_naukri_listings(driver, urls)
        driver.quit()
        save_to_db(job_listings)

def update_db_from_xlsx():
    """
    Updates the reject and applied columns in the database from the xlsx file
    """
    # Check if the xlsx file exists
    if not os.path.exists('naukri_jobs.xlsx'):
        return

    conn = sqlite3.connect('naukri_jobs.db')
    df = pd.read_excel('naukri_jobs.xlsx', engine='calamine')
    cursor = conn.cursor()
    for index, row in df.iterrows():
        cursor.execute('''
            UPDATE jobs
            SET applied = ?, reject = ?
            WHERE url = ?
        ''', (row['applied'], row['reject'], row['url']))
    conn.commit()
    conn.close()


def main():
    init_db()
    update_db_from_xlsx()
    scrape_naukri(job_title, job_location, number_of_pages)
    export_to_xlsx()

if __name__ == '__main__':
    main()