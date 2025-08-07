import scrapy
from scrapy.loader import ItemLoader
from book_scraper.items import BookScraperItem

class BooksSpider(scrapy.Spider):
    name = "books3"
    allowed_domains = ["books.toscrape.com"]
    start_urls = ["https://books.toscrape.com/index.html"]

    def parse(self, response):
        book_links = response.xpath("//article[contains(@class, 'product_pod')]//a/@href")

        yield from response.follow_all(
            book_links,
            self.parse_book
        )

    def parse_book(self, response):
        l = ItemLoader(item=BookScraperItem(), response=response)

        l.add_xpath("title", "//h1/text()")

        return l.load_item()