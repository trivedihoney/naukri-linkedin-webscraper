# Naukri-LinkedIn-WebScraper

This project contains scripts to scrape job listings from Naukri and LinkedIn using Selenium and BeautifulSoup. The scraped data is stored in a SQLite database and can be exported to an Excel file.

## Features

- Scrape job listings from Naukri
- Store job listings in a SQLite database
- Export job listings to an Excel file
- Update database from an Excel file
- LinkedIn Webscraping method shown

## Requirements

- Python 3.12 or higher
- UV package Manager

## Installation

1. Clone the repository
2. Install the dependencies:
    ```sh
    uv sync
    ```

## Usage

- For Naukri Webscraping, Change the job title and job positions as required, the run the script:
    ```
    python naukri_web_scraping.py
    ```
- A db file is created on first run. The data is stored in the db file. And exported as xlsx.
- Upon new run, new data will be appended to the bottom.
- Changes made in xlsx file in `applied` and `reject` columns are saved in db when the script is run again.
