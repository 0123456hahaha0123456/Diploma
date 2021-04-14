import scrapy

class ReviewItem(scrapy.Item):
    name = scrapy.Field()
    reviewTitle = scrapy.Field()
    reviewBody = scrapy.Field()
    verifiedPurchase = scrapy.Field()
    postDate = scrapy.Field()
    starRating = scrapy.Field()
    helpful = scrapy.Field()

