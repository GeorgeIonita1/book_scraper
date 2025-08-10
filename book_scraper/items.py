import scrapy
from itemloaders.processors import TakeFirst, MapCompose
import re

def parse_stock_status(value):
    return "Available" if "In stock" in value else "Unavailable"

def parse_stock_qty(value):
    match = re.search(r'\((\d+) available\)', value)

    return int(match.group(1)) if match else 0

class BookScraperItem(scrapy.Item):
    page_number = scrapy.Field(output_processor=TakeFirst())
    title = scrapy.Field(output_processor=TakeFirst())
    price = scrapy.Field(
        input_processor=MapCompose(str.strip, lambda v: v.replace('£', '')),
        output_processor=TakeFirst()
    )
    stock_status = scrapy.Field(
        input_processor=MapCompose(str.strip, parse_stock_status),
    output_processor=TakeFirst()
    )
    stock_qty = scrapy.Field(
        input_processor=MapCompose(str.strip, parse_stock_qty),
    output_processor=TakeFirst()
    )
    upc = scrapy.Field(output_processor=TakeFirst())
    category = scrapy.Field(output_processor=TakeFirst())
    description = scrapy.Field(output_processor=TakeFirst())