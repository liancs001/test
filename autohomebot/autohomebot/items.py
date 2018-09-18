# -*- coding: utf-8 -*-

# Define here the models for your scraped items
#
# See documentation in:
# https://doc.scrapy.org/en/latest/topics/items.html

import scrapy


class AutohomebotItem(scrapy.Item):
    # define the fields for your item here like:
    # name = scrapy.Field()
    collection=scrapy.Field() #表名
    publish_date=scrapy.Field()
    publish_addr=scrapy.Field()
    buy_date=scrapy.Field()
    brand=scrapy.Field()
    title=scrapy.Field()
    content=scrapy.Field()
    url=scrapy.Field()
    comment_date=scrapy.Field()
    comment_content=scrapy.Field()
    comment_addr=scrapy.Field()
    #comment_list=scrapy.Field()
    update_datetime=scrapy.Field()#插入记录的时间
