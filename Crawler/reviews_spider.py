import scrapy

from .reviewItem import ReviewItem

class ReviewSpider(scrapy.Spider):
    name = 'reviews'
   
    def __init__(self, start_url = None, *args, **kwargs):
        super(ReviewSpider, self).__init__(*args, **kwargs)

        self.start_urls = [start_url]    

    '''
    start_urls = [
        # 'https://www.amazon.com/Sennheiser-Professional-Headphone-Black-HD25/dp/B01CRI3UOU/ref=bmx_2/138-5579462-9820049?_encoding=UTF8&pd_rd_i=B01CRI3UOU&pd_rd_r=d7ea1d36-211b-4a21-8ef2-bc8697fdc292&pd_rd_w=reA68&pd_rd_wg=qR3IH&pf_rd_p=04f8298a-a324-416e-a108-788274fceb3a&pf_rd_r=G1A5ZBC7F3YRVDEZEPP2&psc=1&refRID=G1A5ZBC7F3YRVDEZEPP2'
        'https://www.amazon.com/Sennheiser-HD280PRO-Headphone-new-model/dp/B00IT0IHOY?ref_=ast_sto_dp'
    ]
    '''
    ok = True
    count = 0
    # This part is used to avoid get blacklisted on Amazon    
    custom_settings = {
        'DOWNLOAD_TIMEOUT' : 540,
        'DOWNLOAD_DELAY' : 1,

        'DEPTH_LIMIT' : 0,

        'EXTENSIONS' : {
            'scrapy.extensions.telnet.TelnetConsole' : None,
            'scrapy.extensions.closespider.CloseSpider' : 1
        }
    }

    def parse(self, response):
        # print("START URL IS :" , self.start_urls)
        all_reviews_page = response.xpath('//*[@id="reviews-medley-footer"]/div[2]/a/@href').get()
        if all_reviews_page is not None:
            yield response.follow(all_reviews_page, callback=self.parse_page)
       
        #for review in response.xpath('//div[has-class("review-text-content")]/span')
          

    def parse_page(self, response):
        # if self.count > 20 : return
        # print("Return to parse")
        
        # Get all the items of all reviews
        names=response.xpath('//div[@data-hook="review"]//span[@class="a-profile-name"]/text()').extract()  
        reviewTitles=response.xpath('//a[@data-hook="review-title"]/span/text()').extract()
        reviewBody=response.xpath('//span[@data-hook="review-body"]/span').xpath('normalize-space()').getall()
        verifiedPurchase=response.xpath('//span[@data-hook="avp-badge"]/text()').extract()
        postDate=response.xpath('//span[@data-hook="review-date"]/text()').extract()
        starRating=response.xpath('//i[@data-hook="review-star-rating"]/span[@class="a-icon-alt"]/text()').extract()
        helpful = response.xpath('//span[@class="cr-vote"]//span[@data-hook="helpful-vote-statement"]/text()').extract()

        # Extracting details of review
        for (name, title, body, verified, date, rating, helpful_count) in zip(names, reviewTitles, reviewBody, verifiedPurchase, postDate, starRating, helpful):
            yield ReviewItem(name = name, reviewTitle = title, reviewBody = body, verifiedPurchase = verified, postDate = date, starRating=rating, helpful = helpful_count)
        

        next_page = response.xpath('//*[@id="cm_cr-pagination_bar"]/ul/li[2]/a/@href').get()
        if next_page is not None:
            # self.count += 1
            yield response.follow(next_page, callback=self.parse_page, dont_filter = True)        
            

#command : scrapy runspider reviews_spider.py -o reviews.json
