# Define here the models for your scraped items
#
# See documentation in:
# https://docs.scrapy.org/en/latest/topics/items.html

import scrapy


class CarsdataItem(scrapy.Item):
    # define the fields for your item here like:
    # name = scrapy.Field()
    pass

class TeamBhpItem(scrapy.Item):
    url = scrapy.Field()
    Location = scrapy.Field()
    Source = scrapy.Field()
    Date = scrapy.Field()
    Month = scrapy.Field()
    Year = scrapy.Field()
    ParentComment = scrapy.Field()
    UserComment = scrapy.Field()

class AutomotiveItem(scrapy.Item):
    url = scrapy.Field()
    Location = scrapy.Field()
    Source = scrapy.Field()
    Date = scrapy.Field()
    Month = scrapy.Field()
    Year = scrapy.Field()
    ParentComment = scrapy.Field()
    UserComment = scrapy.Field()


