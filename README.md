# Book Scraper
## A Scrapy-based web scraper for books.toscrape.com


### Features

* **Data Extraction:** Scrapes title, price, stock status, UPC, category, and description.
* **Pagination Handling:** Automatically follows "next" page links to crawl the entire website.
* **Dockerized Environment:** Runs inside a Docker container for a clean, isolated, and consistent development environment.
* **JSON Output:** Exports all scraped data into a single `books.json` file.



### Build and start the container:
    
    docker compose up -d
    
    docker exec -it book_scraper_ct bash

### Generate

    scrapy crawl books -O books.json

### View the results:

  Once the crawl is complete, you can find the `books.json` file in your local project directory.
