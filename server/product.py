# Product from the perspective of the web scraper
# This WILL have to be parsed later to provide useful info
# TODO: images
# from server import Database

from enum import Enum, unique
@unique
class Store(Enum):
    LIDL = 1
    COOP = 2
    ICA = 3
    WILLYS = 4
    def __str__(self):
        match self:
            case self.LIDL:
                return "LIDL"
            case self.COOP:
                return "COOP"
            case self.ICA:
                return "ICA"
            case self.WILLYS:
                return "WILLYS"

class Product:
    #TODO: create function that may return product if it's valid
    def __init__(self,
            name: str,
            price: str,
            store: Store,
            description: str = "",
            category: str = "",
            image_url: str = "",
            #product_url: str = "",
            amount: str = "",
            modifier: str = "",
            ):
        self.amount = amount
        self.category = category
        self.description = description
        self.image_url = image_url
        self.modifier = modifier
        self.name = name
        self.price = price
        #self.product_url = product_url
        self.store = store

    def __str__(self):
        return self.name + ": (" + self.price + ") at " + str(self.store) + " " + self.description

    def __repr__(self):
        return self.name + ": (" + self.price + ") at " + str(self.store) + " " + self.description

    def print(self):
        attrs = vars(self)
        print('\n'.join("%s: %s" % item for item in attrs.items()))


