# -*- coding: utf-8 -*-
import copy
import json
import re
import time

import scrapy
from scrapy import Request

from autohomebot.items import AutohomebotItem
import random

def add_schema(url):
    if url.startswith('//'):
        return 'https:'+url
    return url

def get_comment_headers(referer):
    comment_header={
        'Accept': '*/*',
        'Accept-Encoding': 'gzip, deflate, br',
        'Accept-Language': 'zh-CN,zh;q=0.9',
        'Cache-Control': 'no-cache',
        'Connection': 'keep-alive',
        'Host': 'reply.autohome.com.cn',
        'Pragma': 'no-cache',
        'Referer':referer
    }
    return comment_header


class KoubeiSpider(scrapy.Spider):
    name = 'koubei'
    allowed_domains =['k.autohome.com.cn','reply.autohome.com.cn','i.autohome.com.cn']
    start_urls = ['https://k.autohome.com.cn/4554',
                'https://k.autohome.com.cn/4428',
                'https://k.autohome.com.cn/3993',
                'https://k.autohome.com.cn/4073',
                'https://k.autohome.com.cn/2761',
                'https://k.autohome.com.cn/2761',
                'https://k.autohome.com.cn/4240',
                'https://k.autohome.com.cn/4394',
                'https://k.autohome.com.cn/4343',
                'https://k.autohome.com.cn/4238',
                'https://k.autohome.com.cn/4320',
                'https://k.autohome.com.cn/4291',
                'https://k.autohome.com.cn/3529',
                'https://k.autohome.com.cn/4264',
                'https://k.autohome.com.cn/3779',
                'https://k.autohome.com.cn/4355',
                'https://k.autohome.com.cn/3827',
                'https://k.autohome.com.cn/3395',
                'https://k.autohome.com.cn/4444',
                'https://k.autohome.com.cn/2955',
                'https://k.autohome.com.cn/4088',
                'https://k.autohome.com.cn/4380',
                'https://k.autohome.com.cn/4218',
                'https://k.autohome.com.cn/2779',
                'https://k.autohome.com.cn/3648',
                'https://k.autohome.com.cn/4262',
                'https://k.autohome.com.cn/4341',
                'https://k.autohome.com.cn/3706',
                'https://k.autohome.com.cn/2357',
                'https://k.autohome.com.cn/2664',
                'https://k.autohome.com.cn/4342',
                'https://k.autohome.com.cn/4624',
                'https://k.autohome.com.cn/2805',
                'https://k.autohome.com.cn/3575',
                'https://k.autohome.com.cn/4597',
                'https://k.autohome.com.cn/3533',
                'https://k.autohome.com.cn/4264',
                'https://k.autohome.com.cn/4104',
                'https://k.autohome.com.cn/4015',
                'https://k.autohome.com.cn/3884',
                'https://k.autohome.com.cn/3537/stopselling']

    def parse(self, response): #index page
        self.logger.info('{}返回索引页.状态码:{}'.format(response.url,response.status))
        if response.xpath("//a[@class='btn btn-small fn-left']/@href"):#查看全部
            detail_urls=response.xpath("//a[@class='btn btn-small fn-left']/@href").extract()
            for url in detail_urls:
                url=add_schema(url)
                yield Request(url,callback=self.parse_detail,priority=50)

            if response.xpath("//a[@class='page-item-next']//@href"):#下一页
                next_page=response.xpath("//a[@class='page-item-next']//@href").extract_first()
                self.logger.info('【加载下一页索引页...】')
                yield response.follow(next_page,callback=self.parse)        
        else:
            print('加载列表页失败.{}'.format(response.url))
            if '暂无符合该列表的口碑' not in response.text:
                yield Request(response.url,callback=self.parse,dont_filter=True,meta={'retry':time.time()})

    def parse_detail(self, response):
        self.logger.info('{}返回详情页.状态码:{}'.format(response.url,response.status))
        if response.xpath("//div[contains(@class,'koubei-final')]//div[contains(@class,'title-name')]/b"):#发表时间
            try:
                publish_date=response.xpath("//div[contains(@class,'koubei-final')]//div[contains(@class,'title-name')]/b/text()").extract_first()[1:]
                publish_addr=response.xpath("//dl[@class='choose-dl' and dt[contains(text(),'购买地点')]]/dd/text()").extract_first().strip()
                buy_date=response.xpath("//dl[@class='choose-dl' and dt[contains(text(),'购买时间')]]/dd/text()").extract_first().strip()
                brand=response.xpath("//dl[@class='choose-dl' and dt[contains(text(),'购买车型')]]/dd/a/text()").extract_first().strip()
                brand=brand+' '+response.xpath("//dl[@class='choose-dl' and dt[contains(text(),'购买车型')]]/dd/a[2]/text()").extract_first()
                title=response.xpath("//title/text()").extract_first()
                url=response.url
                content=response.xpath("//div[@class='mouth-main']").extract_first()
                content=re.sub(r"(<style(.|\r|\n)+?</style>)|(<script(.|\r|\n)+?</script>)|(<!--(.|\r|\n)+?-->)|(<[^>]*>)|(\r|\n)|(\s+)|(&nbsp;)", "", content)
                item=AutohomebotItem()
                for field in item.fields:
                    try:
                        item[field]=eval(field)
                    except NameError:
                        pass
                #print('【AutohomebotItem】',item)
                #评论
                koubei_id=response.xpath("//input[@id='hidEvalId']/@value").extract_first()
                comment_url="https://reply.autohome.com.cn/ShowReply/ReplyJsonredis.ashx?count=10&page=1&id={}&datatype=jsonp&appid=5{}".format(koubei_id,self.get_comment_callback())
                print('【评论url】',comment_url)
                yield Request(comment_url,priority=100,callback=self.parse_comment,headers=get_comment_headers(response.url),meta={'item':item,'page_index':1,'koubei_id':koubei_id})
            except Exception as e:
                self.logger.error('【parse_detail出错】{},{}'.format(response.url,e))
    
    def get_comment_callback(self):
        def get_timestamp_str():
            return str(time.time()*1000)[:13]
        def get_random_digital_str():
            return str(random.random())[2:]
        return "&callback=jQuery1720{}_{}&_={}".format(get_random_digital_str(),get_timestamp_str(),get_timestamp_str())

    def parse_comment(self, response):
        self.logger.info('{}返回评论内容.状态码:{}'.format(response.url,response.status))
        print('【评论response status】',response.status)
        if response.status==200 and 'jQuery' in response.text:
            #print('【jQuery】',response.text)
            tmp=re.search(r"\{[\s\S]*\}", response.text)
            if tmp:
                jsonObj=json.loads(tmp.group())
                try:
                    if jsonObj['commentlist'] is not None and len(jsonObj['commentlist']) != 0:#有评论返回
                        self.logger.info('【评论数】{}'.format(len(jsonObj['commentlist'])))
                        try:
                            print('【Commentlist len>0】')
                            page_index=int(response.meta['page_index'])+1
                            koubei_id=response.meta['koubei_id']
                            item=response.meta['item'] #AutohomebotItem
                            
                            for obj in jsonObj['commentlist']:
                                item1=copy.deepcopy(item)
                                member_id=obj['RMemberId']
                                member_home_url="https://i.autohome.com.cn/{}".format(member_id)
                                item1['comment_date']=obj['replydate']
                                item1['comment_content']=obj['RContent']
                                #print('【Item】',item1)
                                print('评论内容:',obj['RContent'])
                                yield Request(member_home_url,priority=101,dont_filter=True,callback=self.parse_member_home,meta={'item':item1}) #从评论者主页找到其所在地
                        except Exception as e:
                            print('【获取CommentList出错】',e)
                        #获取下一页评论
                        item2=copy.deepcopy(item)
                        comment_url="https://reply.autohome.com.cn/ShowReply/ReplyJsonredis.ashx?count=10&page={}&id={}&datatype=jsonp&appid=5{}".format(page_index,koubei_id,self.get_comment_callback())
                        print('【评论url】',comment_url)
                        yield Request(comment_url,priority=100,callback=self.parse_comment,headers=get_comment_headers(response.url),meta={'item':item2,'page_index':page_index,'koubei_id':koubei_id})               
                except Exception as e:
                    print('Commentlist is null',response.text)


    def parse_member_home(self, response):
        self.logger.info('{}返回评论者主页.状态码:{}'.format(response.url,response.status))
        if response.status == 200 and response.xpath("//a[@class='state-pos']"):
            member_addr=response.xpath("//a[@class='state-pos']/text()").extract_first()
            item=response.meta['item']#AutohomebotItem
            item['comment_addr']=member_addr
            item['update_datetime']=time.strftime("%Y-%m-%d %H:%M:%S", time.localtime())
            item['collection']='autohomekoubei'
            self.logger.info('成功抓取一条数据!')
            #print('成功抓取一条数据!')
            yield item
        return None
