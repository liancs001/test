# -*- coding: utf-8 -*-

# Define here the models for your spider middleware
#
# See documentation in:
# https://doc.scrapy.org/en/latest/topics/spider-middleware.html

from scrapy import signals,Request
import time


class AutohomebotSpiderMiddleware(object):
    # Not all methods need to be defined. If a method is not defined,
    # scrapy acts as if the spider middleware does not modify the
    # passed objects.

    @classmethod
    def from_crawler(cls, crawler):
        # This method is used by Scrapy to create your spiders.
        s = cls()
        crawler.signals.connect(s.spider_opened, signal=signals.spider_opened)
        return s

    def process_spider_input(self, response, spider):
        # Called for each response that goes through the spider
        # middleware and into the spider.

        # Should return None or raise an exception.
        return None

    def process_spider_output(self, response, result, spider):
        # Called with the results returned from the Spider, after
        # it has processed the response.

        # Must return an iterable of Request, dict or Item objects.
        for i in result:
            yield i

    def process_spider_exception(self, response, exception, spider):
        # Called when a spider or process_spider_input() method
        # (from other spider middleware) raises an exception.

        # Should return either None or an iterable of Response, dict
        # or Item objects.
        pass

    def process_start_requests(self, start_requests, spider):
        # Called with the start requests of the spider, and works
        # similarly to the process_spider_output() method, except
        # that it doesn’t have a response associated.

        # Must return only requests (not items).
        for r in start_requests:
            yield r

    def spider_opened(self, spider):
        spider.logger.info('Spider opened: %s' % spider.name)

from fake_useragent import UserAgent
import requests

class AutohomebotDownloaderMiddleware(object):
    # Not all methods need to be defined. If a method is not defined,
    # scrapy acts as if the downloader middleware does not modify the
    # passed objects.
    def __init__(self, crawler):
        self.proxy=None #默认代理
        self.ua = UserAgent()
        # 若settings中没有设置RANDOM_UA_TYPE的值默认值为random，
        # 从settings中获取RANDOM_UA_TYPE变量，值可以是 random ie chrome firefox safari opera msie
        self.ua_type = crawler.settings.get('RANDOM_UA_TYPE', 'random')
        self.proxy_pool_url=crawler.settings.get('PROXY_POOL_URL')

    def get_ua(self):
        '''根据settings的RANDOM_UA_TYPE变量设置每次请求的User-Agent'''
        return getattr(self.ua, self.ua_type)

    def get_proxy(self):
        '''获取代理'''
        try:
            response = requests.get(self.proxy_pool_url)
            if response.status_code == 200:
                return "http://{}".format(response.text)
        except ConnectionError:  
            print('【获取代理失败!】')
            return None

    @classmethod
    def from_crawler(cls, crawler):
        # This method is used by Scrapy to create your spiders.
        s = cls(crawler)
        crawler.signals.connect(s.spider_opened, signal=signals.spider_opened)
        return s

    def process_request(self, request, spider):
        print('【请求Url】',request.url)
        # ua=self.get_ua()
        # request.headers['User-Agent']=ua #.setdefault('User-Agent', ua)
        print('【是否重试】:','是' if request.meta.get('retry') else '否')
        old_proxy=request.meta.get('proxy')
        if self.proxy is None or old_proxy is None or self.proxy==request.meta.get('proxy'): #请求被重来,换代理
            print('【更换代理中...】')
            proxy=self.get_proxy()
            if proxy:
                self.proxy=proxy
        print('代理:',self.proxy)
        request.meta['proxy']=self.proxy #"http://wyiyxpjw-2:shxrrlwfql0n@95.216.1.195:80"


    def process_response(self, request, response, spider):
        if response.status != 200: #如果返回不正确则重新请求
            print('middlewares response状态码为{},{}'.format(response.status,response.url))            
            return self.get_retry_request(request)
        elif '用户访问安全认证' in response.text:
            print('【出现安全认证】',response.url)
            return self.get_retry_request(request)
            
        #print('【响应200】',response.text)
        return response

    def process_exception(self, request, exception, spider):
        # Called when a download handler or a process_request()
        # (from other downloader middleware) raises an exception.

        # Must either:
        # - return None: continue processing this exception
        # - return a Response object: stops process_exception() chain
        # - return a Request object: stops process_exception() chain
        print('【请求出错,重试...】',exception)
        return self.get_retry_request(request)

    def spider_opened(self, spider):
        spider.logger.info('Spider opened: %s' % spider.name)

    def get_retry_request(self,request):
        '''获取要重试的请求'''
        try:
            self.proxy=None #重置代理
            retry_request=request.copy()
            retry_request.dont_filter=True #禁止去重
            retry_request.meta['retry']=time.time()
            #print('【获取要重试的请求...dont_filter:】',retry_request.dont_filter)
            return retry_request
        except Exception as e:
            print('【获取要重试的请求出错】',e)
            return None