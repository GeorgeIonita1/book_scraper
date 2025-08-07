import scrapy
import re

class BooksSpider(scrapy.Spider):
    name = "books2"
    allowed_domains = ["books.toscrape.com"]
    start_urls = ["https://books.toscrape.com/index.html"]

    BOOK_URLS = "//article[contains(@class, 'product_pod')]//a/@href"
    NEXT_PAGE = "//ul[contains(@class, 'pager')]/li[contains(@class, 'next')]//a/@href"
    CURRENT_PAGE = "//ul[contains(@class, 'pager')]/li[contains(@class, 'current')]/text()"
    STOCK = "//div[contains(@class, 'product_main')]//p[contains(@class, 'availability')]"

    def parse(self, response):
        page_number = self._extract_page_number(response)
        book_urls = response.xpath(self.BOOK_URLS).getall()

        yield from response.follow_all(
            book_urls,
            self.parse_book,
            meta={'page_number': page_number}
        )

        next_page_url = response.xpath(self.NEXT_PAGE).get()
        
        if next_page_url:
            yield response.follow(next_page_url, self.parse)

    def parse_book(self, response):
        TITLE = "//h1/text()"
        PRICE = "//div[contains(@class, 'product_main')]//p[contains(@class, 'price_color')]/text()"
        UPC = "//th[text()='UPC']/following-sibling::td/text()"
        CATEGORY = "//ul[contains(@class, 'breadcrumb')]/li[last()-1]//a/text()"
        DESCRIPTION = "//div[@id='product_description']/following-sibling::p/text()"

        page_number = response.meta.get('page_number')
        stock_status, stock_quantity = self._parse_stock(response)
        price_stripped = self._parse_price(response, PRICE)
        
        yield {
            "page_number": page_number,
            "title": self._extract_with_xpath(response, TITLE),
            "price": price_stripped,
            "stock_status": stock_status,
            "stock_quantity": stock_quantity,
            "upc": self._extract_with_xpath(response, UPC),
            "category": self._extract_with_xpath(response, CATEGORY),
            "description": self._extract_with_xpath(response, DESCRIPTION)
        }

    def _extract_with_xpath(self, response, query):
        return response.xpath(query).get(default="").strip()
    
    def _extract_page_number(self, response):
        pagination_text = self._extract_with_xpath(response, self.CURRENT_PAGE)
        match = re.search(r'Page (\d+) of', pagination_text)

        return int(match.group(1)) if match else None

    def _parse_stock(self, response):
        stock_status = "unavailable"
        stock_quantity = 0
        stock_text = self._extract_with_xpath(response, self.STOCK)

        if "In stock" in stock_text:
            stock_status = "available"
            quantity_match = re.search(r'\((\d+) available\)', stock_text)

            if quantity_match:
                stock_quantity = int(quantity_match.group(1))
        
        return stock_status, stock_quantity
    
    def _parse_price(self, response, price):
        raw_price = self._extract_with_xpath(response, price)
        return float(raw_price.replace('£', '')) if raw_price else None