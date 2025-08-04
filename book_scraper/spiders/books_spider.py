import scrapy
import re

class BooksSpider(scrapy.Spider):
    name = "books"
    allowed_domains = ["books.toscrape.com"]
    start_urls = ["https://books.toscrape.com/index.html"]

    # Assumption 1:
        # I always use // to target child elements because using a single / would restrict the relation to direct children only
        # And over time, relations could change and break the xpath selector
        # But i do agree that there are certain scenarios where we would want to use direct child relations with /

    # Assumption 2:
        # Book urls are inside <article> elements with a class that contains "product_pod", where we can further select the href of the <a> element
        # The <a> element is not specific enough to be targeted individually, so I selected it through the <article> element context
        # I'm always using contains because other classes can be added later, which would brake the code if not using contains
        # Learned that the hard way, naturally :))
        # Also agree that there could be cases where we would want to use the specific [@class="example"] selector
    BOOK_URLS = "//article[contains(@class, 'product_pod')]//a/@href"
    # Assumption 3:
        # Next page element can be found inside the <ul> that contains the pager class.
        # I think it's safe to assume that the <li> element is the direct child, with a class of next, where we can firther select the href of the <a> element
        # The 'next' class of the <li> element was not specific enough (there could be other unrelated elements to use this class)
        # And the <a> element wasn't either specific enough to be targeted directly
    NEXT_PAGE = "//ul[contains(@class, 'pager')]/li[contains(@class, 'next')]//a/@href"
    # Assumption 4:
        # Same as previous assumption basically
        # Here i am targeting the text of the <li> element with the 'current' class in order to get the text inside, in order to get the current page number
        # I know that the current page number wasn't specified in the original requirement, but it helped me to better visualise the data
    CURRENT_PAGE = "//ul[contains(@class, 'pager')]/li[contains(@class, 'current')]/text()"
    # Assumption 5:
        # This is actually used in the query for the product page, not on the listing page
        # The stock element can be found in the <div> with a "product_main" class, inside a <p> with a 'availability' class
        # The <p> element was not specific enough because it can also be found on the 'Products you recently viewed' section
    STOCK = "//div[contains(@class, 'product_main')]//p[contains(@class, 'availability')]"

    def parse(self, response):
        # -- Parse the main page, extracts book links, and handle pagination

        # Get the current page number
        page_number = self._extract_page_number(response)
        book_urls = response.xpath(self.BOOK_URLS).getall()

        # I'm also passing the page_number to add it in the json
        yield from response.follow_all(
            book_urls,
            self.parse_book,
            meta={'page_number': page_number}
        )

        # Check for next page and add it to the query if exists
        next_page_url = response.xpath(self.NEXT_PAGE).get()
        
        # I'm just limiting the number of iterations for testing
        # Please remove "and page_number < 2" to scrape everything to the last page
        if next_page_url and page_number < 2:
            yield response.follow(next_page_url, self.parse)

    def parse_book(self, response):
        # -- Parse a individual book page and extract item data

        # Asumption 6:
            # <h1> element is specific enough to be selected directly by the tag name, and by doing so, we do not depend on any other DOM strcture
            # There can be only one <h1> element on the page (theoretically, but very probable, to follow best a11y practices)
        TITLE = "//h1/text()"
        # Asumption 7:
            # Price element can be found in the <div class="product-main"> element, inside the <p class="price_color"> element
            # <p> element is not specific enough, we can also find this in the "Products you recently viewed" section.
        PRICE = "//div[contains(@class, 'product_main')]//p[contains(@class, 'price_color')]/text()"
        UPC = "//th[text()='UPC']/following-sibling::td/text()"
        # Asumption 8:
            # The category can be found in the <ul class="breadcrumb"> element, in the last -1 <li> element, inside an <a> element
            # It's safe to assume that the <li> is the direct child of the <ul> element
            # We need to target the .breadcrumb class, because there are other ul elements in the page
        CATEGORY = "//ul[contains(@class, 'breadcrumb')]/li[last()-1]//a/text()"
        # Asumption 9:
            # Description can be found in the <div id="product_description">, inside the next sibling <p> element
            # <p> is not specific enough, so we can target based on the id of the previous sibling
        DESCRIPTION = "//div[@id='product_description']/following-sibling::p/text()"

        page_number = response.meta.get('page_number')
        stock_status, stock_quantity = self._parse_stock(response)
        
        yield {
            "page_number": page_number,
            "title": self._extract_with_xpath(response, TITLE),
            "price": self._extract_with_xpath(response, PRICE),
            "stock_status": stock_status,
            "stock_quantity": stock_quantity,
            "upc": self._extract_with_xpath(response, UPC),
            "category": self._extract_with_xpath(response, CATEGORY),
            "description": self._extract_with_xpath(response, DESCRIPTION)
        }

    # --- Helper methods

    def _extract_with_xpath(self, response, query):
        # Seems this is a safe and recommended way to extract values
        return response.xpath(query).get(default="").strip()
    
    def _extract_page_number(self, response):
        # Assumption:
            # The current page text will be in the format 'Page X of Y'
            # Im using regex to match 'Page X of' sequence and return the number, or None
        pagination_text = self._extract_with_xpath(response, self.CURRENT_PAGE)
        match = re.search(r'Page (\d+) of', pagination_text)

        return int(match.group(1)) if match else None

    def _parse_stock(self, response):
        # Parse the stock status and quantity
        stock_status = "unavailable"
        stock_quantity = 0
        stock_text = self._extract_with_xpath(response, self.STOCK)

        if "In stock" in stock_text:
            stock_status = "available"
            quantity_match = re.search(r'\((\d+) available\)', stock_text)

            if quantity_match:
                stock_quantity = int(quantity_match.group(1))
        
        return stock_status, stock_quantity