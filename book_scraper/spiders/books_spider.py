import scrapy
import re

class BooksSpider(scrapy.Spider):
    name = "books"

    allowed_domains = ["books.toscrape.com"]
    start_urls = ["https://books.toscrape.com/index.html"]
    
    def parse(self, response):
        books_urls = response.xpath('//article[contains(@class, "product_pod")]//a/@href').getall()

        pagination = response.xpath('//li[@class="current"]/text()')
        pagination_number = None

        if pagination:
            pagination_text = response.xpath('//li[@class="current"]/text()').get().strip()
            match = re.search(r'Page (\d+) of', pagination_text)

            if match:
                pagination_number = int(match.group(1))

        # yield from response.follow_all(books, self.parse_book)

        for url in books_urls:
            yield response.follow(
                url,
                self.parse_book,
                meta={'page_number': pagination_number}
            )

        if pagination_number is not None and pagination_number < 1:
            next_page_url = response.xpath("//li[contains(@class, 'next')]//a/@href").get()

            yield response.follow(next_page_url, self.parse)
            

        

    def parse_book(self, response):
        stock_status = "unavailable"
        stock_quantity = 0
        page_number = response.meta.get('page_number')

        def extract_with_xpath(query):
            return response.xpath(query).get(default="").strip()

        stock_text = response.xpath("//div[contains(@class, 'product_main')]//p[contains(@class, 'availability')]").xpath('string(.)').get().strip()

        if "In stock" in stock_text:
            stock_status = "available"

            quantity_match = re.search(r'\((\d+) available\)', stock_text)

            if quantity_match:
                stock_quantity = int(quantity_match.group(1))

                # only contains selectors, not dirrect classes
        
        yield {
            "page_number": page_number,
            "title": extract_with_xpath("//h1/text()"),
            "price": extract_with_xpath("//div[contains(@class, 'product_main')]//p[contains(@class, 'price_color')]/text()"),
            "stock_status": stock_status,
            "stock_quantity": stock_quantity,
            "upc": extract_with_xpath("//th[text()='UPC']/following-sibling::td/text()"),
            "category": extract_with_xpath('//ul[contains(@class, "breadcrumb")]/li[last()-1]/a/text()'),
            "description": extract_with_xpath("//div[@id='product_description']/following-sibling::p/text()")
        }
