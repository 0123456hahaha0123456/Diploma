import scrapy
import re
from Crawler.reviews_spider import ReviewSpider
from scrapy.crawler import CrawlerProcess
from scrapy.crawler import CrawlerRunner
import json
import os
import pathlib 
from multiprocessing import Process, Queue
from twisted.internet import reactor

def get_code(url):
    sub = re.split(r'[/?]+',url)
    for item in sub:
        if len(item) == 10:
            return item
    return ""

def crawl_reviews(url):
    # url = 'https://www.amazon.com/Sennheiser-HD280PRO-Headphone-new-model/dp/B00IT0IHOY?ref_=ast_sto_dp'
    code = get_code(url)
    
    file_name = '{code}.csv'.format(code = code) 
    path_file_name = str(pathlib.Path.cwd()) +'/Crawler/data/' + file_name
    
    def f(q):
        try:
            # c = CrawlerProcess({
            #     'USER_AGENT' : 'Mozilla/5.0 (Windows NT 6.1; WOW64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/34.0.1847.131 Safari/537.36',
            #     'FEED_FORMAT' : 'csv',
            #     'FEED_URI' : path_file_name
            # })    
            # c.crawl(ReviewSpider, start_url = url)
            # c.start(stop_after_crawl=False)
            
            # Use CrawlRunner
            runner = CrawlerRunner({
                'USER_AGENT' : 'Mozilla/5.0 (Windows NT 6.1; WOW64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/34.0.1847.131 Safari/537.36',
                'FEED_FORMAT' : 'csv',
                'FEED_URI' : path_file_name
            })    
            deferred = runner.crawl(ReviewSpider, start_url = url)
            deferred.addBoth(lambda _: reactor.stop())
            reactor.run()
            q.put(None)
            # c.start(stop_after_crawl=False)
        except Exception as e:
            q.put(e)

    q = Queue()
    p = Process(target=f, args=(q,))
    p.start()
    q.get()
    p.join()

    return path_file_name


def process(url):
    file_data = open('Crawler/data/listProduct.txt','r')
    code = get_code(url)
    try:
        data = json.load(file_data)
        if code not in data:
            path_file =  crawl_reviews(url)
            data[code] = path_file
            written_data_file = open('Crawler/data/listProduct.txt','w')
            json.dump(data, written_data_file)
    except json.JSONDecodeError:
        data = {}
        path_file =  crawl_reviews(url)
        data[code] = path_file
        written_data_file = open('Crawler/data/listProduct.txt','w')
        json.dump(data, written_data_file)
    return data[code]


# url_product = 'https://www.amazon.com/Apple-MWP22AM-A-AirPods-Pro/dp/B07ZPC9QD4'
# 
# url_product = 'https://www.amazon.com/Crucial-PC3-12800-Unbuffered-SODIMM-204-Pin/dp/B007B5S52C/?_encoding=UTF8&pd_rd_w=ZF57t&pf_rd_p=efec9084-7cd8-4122-9b80-914999cb4a82&pf_rd_r=3X1YP2CF71BYDBKWTSFY&pd_rd_r=1d386b7e-66e4-4794-8864-8ba8d72fe860&pd_rd_wg=g2vAz&ref_=pd_gw_cr_cartx'
# url_product = 'https://www.amazon.com/SanDisk-128GB-Extreme-microSD-Adapter/dp/B07FCMKK5X/ref=pd_rhf_cr_s_pd_crcd_6?pd_rd_w=oIPrd&pf_rd_p=8019ba47-0a12-4976-b76b-5c932d60db6f&pf_rd_r=2NF0S495DBV1XXJ9XQYE&pd_rd_r=f9fad01d-18b9-4ff3-b2f0-e274a1c6d823&pd_rd_wg=HIXoP&pd_rd_i=B07FCMKK5X&psc=1'
# url_product = 'https://www.amazon.com/Nintendo-Switch-Pro-Controller/dp/B01NAWKYZ0/?_encoding=UTF8&pd_rd_w=8rk4v&pf_rd_p=bb22ba69-5d1f-46eb-b0be-d8e50852ca56&pf_rd_r=KZ6EX5Y2D4SVRCTJV6V9&pd_rd_r=ea1eed6b-eeb3-4dd4-9170-817dab7724d7&pd_rd_wg=HAd4t&ref_=pd_gw_crs_zg_bs_468642'
# print(get_reviews(url_product))
# process(url_product)
