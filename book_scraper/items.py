import scrapy
from itemloaders.processors import TakeFirst, MapCompose, Join


class BookScraperItem(scrapy.Item):
    title = scrapy.Field(output_processor=TakeFirst())
    # price = scrapy.Field(
    #     input_processor=MapCompose(str.strip)
    # )