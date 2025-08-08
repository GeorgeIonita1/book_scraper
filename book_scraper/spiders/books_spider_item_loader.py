import scrapy
from scrapy.loader import ItemLoader
from book_scraper.items import BookScraperItem
import re

class BooksSpider(scrapy.Spider):
    name = "books3"
    allowed_domains = ["books.toscrape.com"]
    start_urls = ["https://books.toscrape.com/catalogue/page-3.html"]

    def parse(self, response):
        book_links = response.xpath("//article[contains(@class, 'product_pod')]//a/@href")
        current_page_number = self.extract_current_page_number(response)

        yield from response.follow_all(
            book_links,
            self.parse_book,
            meta={"page_number": current_page_number}
        )

        NEXT_PAGE = "//ul[contains(@class, 'pager')]/li[contains(@class, 'next')]//a/@href"
        next_page_url = self.extract_xpath_safely(response, NEXT_PAGE)

        if next_page_url and current_page_number < 3:
            yield response.follow(next_page_url, self.parse)

    def parse_book(self, response):
        l = ItemLoader(item=BookScraperItem(), response=response)

        l.add_value("page_number", response.meta.get("page_number"))
        l.add_xpath("title", "//h1/text()")
        l.add_xpath("price", "//div[contains(@class, 'product_main')]//p[contains(@class, 'price_color')]/text()")
        # Because the stock <p> element contains an <i>, the returned value when using /text() will be a new line first, and then the rest
        # So turns out its a good practice to let the processor handle the HTML
        l.add_xpath("stock_status", "//div[contains(@class, 'product_main')]//p[contains(@class, 'availability')]")
        l.add_xpath("stock_qty", "//div[contains(@class, 'product_main')]//p[contains(@class, 'availability')]")
        l.add_xpath("upc", "//th[text()='UPC']/following-sibling::td/text()")
        l.add_xpath("category", "//ul[contains(@class, 'breadcrumb')]/li[last()-1]//a/text()")
        l.add_xpath("description", "//div[@id='product_description']/following-sibling::p/text()")

        return l.load_item()
    
    def extract_current_page_number(self, response):
        CURRENT_PAGE = "//ul[contains(@class, 'pager')]/li[contains(@class, 'current')]/text()"
        pagination_text = self.extract_xpath_safely(response, CURRENT_PAGE)
        match = re.search(r'Page (\d+) of', pagination_text)

        return int(match.group(1)) if match else 1
    
    def extract_xpath_safely(self, response, query):
        return response.xpath(query).get(default="").strip()