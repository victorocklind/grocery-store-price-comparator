import colorama
import product

import requests
import re

from bs4 import BeautifulSoup
import bs4

from selenium import webdriver
from selenium.webdriver.chrome.service import Service
#from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support.wait import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC
from webdriver_manager.chrome import ChromeDriverManager
from selenium.webdriver.common.by import By
from typing import AnyStr, Iterable
import typing

import time

#does this string contain amount, eg "Ca 200g", or not, eg "Klass 1"
def is_amount(amount_str: str) -> bool:
    #TODO: implement
    return True

#remove surrounding whitespace and empty elements
def remove_whitespace_elements(original: Iterable[str]) -> list[str]:
    return [el.strip() for el in original if len(el.strip()) != 0]

def clean_join(separator: str, strings: Iterable[str]) -> str:
    return separator.join(remove_whitespace_elements(strings))

def filter_price_string(price_string: str) -> str:
    return re.sub(r"[^\d.,]*", "", price_string.strip())

# wrapper around http request to prevent errors
def safe_request(http_str: str) -> bytes:
    try:
        r = requests.get(http_str)
        return r.content
    except requests.exceptions.ConnectionError:
        return bytes()

def safe_none_str(maybe_string: None | str) -> str:
    if maybe_string == None:
        return ""
    else:
        return maybe_string.strip()

def soup_get_str(soup: BeautifulSoup | bs4.Tag | bs4.NavigableString | None) -> str:
    match soup:
        case BeautifulSoup() | bs4.Tag():
            return safe_none_str(soup.string)
        case _:
            return ""

def soup_safe_strs(soup: BeautifulSoup | bs4.Tag | bs4.NavigableString | None) -> Iterable[str]:
    match soup:
        case BeautifulSoup() | bs4.Tag():
            return soup.strings
        case _:
            return []

def soup_find(soup: BeautifulSoup | bs4.Tag | bs4.NavigableString | None, kind: str, class_tag: str) -> bs4.Tag | bs4.NavigableString | None:
    match soup:
        case BeautifulSoup() | bs4.Tag():
            return soup.find(kind, class_=class_tag)
        case _:
            return None

def soup_find_all(soup: BeautifulSoup | bs4.Tag, kind: str, class_tag: str) -> list[bs4.Tag | bs4.NavigableString]:
    return soup.find_all(kind, class_=class_tag)

# get arbitrary attribute safetly
def soup_get_attr(soup: BeautifulSoup | bs4.Tag | bs4.NavigableString | None, attribute: str) -> str:
    match soup:
        case None:
            return ""
        case bs4.NavigableString():
            return soup
        case _:
            res: str | list[str] = soup[attribute]
            match res:
                case str():
                    return res
                case list():
                    if len(res) > 0:
                        return res[0]
                    else:
                        return ""

def soup_find_str(soup: BeautifulSoup | bs4.Tag | bs4.NavigableString | None, kind: str, class_tag: str) -> str:
    el: BeautifulSoup | bs4.Tag | bs4.NavigableString | None = soup_find(soup, kind, class_tag)
    return soup_get_str(el)

def soup_find_attr(soup: BeautifulSoup | bs4.Tag | bs4.NavigableString | None, attribute: str, kind: str, class_tag: str) -> str:
    el: BeautifulSoup | bs4.Tag | bs4.NavigableString | None = soup_find(soup, kind, class_tag)
    return soup_get_attr(el, attribute)

def soup_find_strs_joined(soup: BeautifulSoup | bs4.Tag | bs4.NavigableString | None, separator: str, kind: str, class_tag: str) -> str:
    el: BeautifulSoup | bs4.Tag | bs4.NavigableString | None = soup_find(soup, kind, class_tag)
    return clean_join(separator, soup_safe_strs(el))

# make request from http address and return soup object
def address_to_soup(address: str) -> BeautifulSoup:
    content: bytes = safe_request(address)
    return BeautifulSoup(content, "html.parser")

# Parse Lidl offers from html
def lidl_parse(soup: BeautifulSoup) -> list[product.Product]:
    offers: list[bs4.Tag | bs4.NavigableString] = soup_find_all(soup, "div",  "nuc-a-flex-item nuc-a-flex-item--width-6 nuc-a-flex-item--width-4@sm")
    product_list: list[product.Product] = []
    for offer_el in offers:
        product_list.append(product.Product(
            name        = soup_find_str( offer_el,        "h3",   "ret-o-card__headline"), 
            price       = soup_find_str( offer_el,        "span", "lidl-m-pricebox__price"), 
            image_url   = soup_find_attr(offer_el, "src", "img",  "nuc-m-picture__image nuc-a-image"),
            modifier    = soup_find_str( offer_el,        "div",  "lidl-m-pricebox__highlight"),
            amount      = soup_find_str( offer_el,        "div",  "lidl-m-pricebox__basic-quantity"),
            description = soup_find_str( offer_el,        "span", "lidl-m-pricebox__discount-prefix"),
            store       = product.Store.LIDL,
            ))
    return product_list

# Parse Coop offers from html
def coop_parse(soup: BeautifulSoup) -> list[product.Product]:
    offers: list[bs4.Tag | bs4.NavigableString] = soup.find_all("article", class_ = "ItemTeaser")
    product_list: list[product.Product] = []
    for offer_el in offers:
        price = clean_join(" ", soup_safe_strs(soup_find(offer_el, "span", "Splash-content")))
        price_el: str = " ".join(remove_whitespace_elements(list(offer_el.find("span", class_ = "Splash-content").strings)))
        description: str = " ".join(remove_whitespace_elements(list(offer_el.find("p", class_ = "ItemTeaser-description").strings)));
        product_list.append(product.Product(
            name        = soup_find_str(offer_el, "h3", "ItemTeaser-heading"), 
            price       = price_el, 
            store       = product.Store.COOP,
            description = description))
    return product_list

def ica_parse(soup: BeautifulSoup) -> list[product.Product]:
    #<section class="offer-category details open">
    offer_groups: list[BeautifulSoup] = soup.find_all("section", class_ = "offer-category details open")
    product_list: list[product.Product] = []
    for offer_group in offer_groups:
        header_soup = offer_group.find("header", class_ = "offer-category__header summary active")
        category: str = soup_get_str(header_soup)
        offers = offer_group.find_all("div", class_="offer-category__item")
        print("category:", category, "offers:", len(offers))
        for offer_el in offers:
            title: str = soup_get_str(offer_el.find("h2", class_="offer-type__product-name splash-bg icon-store-pseudo"))
            description: str = soup_get_str(offer_el.find("p", class_="offer-type__product-info"))
            price: str = soup_get_str(offer_el.find("div", class_="product-price__price-value"))\
            + " " +      soup_get_str(offer_el.find("div", class_="product-price__decimal"))\
            + " " +      soup_get_str(offer_el.find("div", class_="product-price__unit-item benefit-more-info"))
            price = price.strip()
            #print(offer.prettify())
            #exit()

            print("    title:", title)
            print("    description:", description)
            print("    price:", price)
            product_list.append(product.Product(
                name=title, 
                price=price, 
                store=product.Store.ICA,
                description=description,
                category=category))

    return product_list

def willys_parse(soup: BeautifulSoup) -> list[product.Product]:
    #print(soup.prettify())
    #<div class="Productstyles__StyledProduct-sc-16nua0l-0 aRuiG" itemscope="" itemtype="https://schema.org/Product">
    offers = soup_find_all(soup, "div", "Productstyles__StyledProduct-sc-16nua0l-0 aRuiG")
    #print(elements)
    product_list: list[product.Product] = []
    for offer_el in offers:
        price_el = soup_find(offer_el, "div", "PriceLabelstyles__StyledProductPrice-sc-koui33-0 dCxjnV") # "yellow" price
        if price_el == None: # "red" price
            price_el = soup_find(offer_el, "div", "PriceLabelstyles__StyledProductPriceTextWrapper-sc-koui33-1 fHVyJs")
        if price_el == None:
            assert False
        price: str = " ".join(remove_whitespace_elements(price_el.strings))
        price_modifier_el = soup_find(offer_el, "div", "Productstyles__StyledProductSavePrice-sc-16nua0l-13 iyjqpG")
        price_modifier: str = ""
        if price_modifier_el!=None:
            price_modifier = " ".join(remove_whitespace_elements(price_modifier_el.strings))

        final_price_str = price_modifier + " " + price
        print("price:", final_price_str)

        name_el = soup_find(offer_el, "div", "Productstyles__StyledProductName-sc-16nua0l-5 dqhhbm")
        if name_el == None:
            assert False
        name = " ".join(remove_whitespace_elements(name_el.strings))
        print("name:", name)

        description_el = soup_find(offer_el, "div", "Productstyles__StyledProductManufacturer-sc-16nua0l-6 ksPmCk")
        if description_el == None:
            assert False
        description = " ".join(remove_whitespace_elements(description_el.strings))
        print("description:", description)
        product_list.append(product.Product(
            name=name, 
            price=price, 
            store=product.Store.WILLYS,
            description=description))
        print()

    return product_list


def get_willys_html(url: str) -> str:
    driver=webdriver.Chrome(service=Service(ChromeDriverManager().install()))
    wait = WebDriverWait(driver, 10)
    driver.get(url)
    get_url = driver.current_url
    wait.until(EC.url_to_be(url))
    fac = 0.5

    # Decline cookies
    time.sleep(3) # a bit of a hack
    cookie_buttons = driver.find_elements(By.XPATH, "//body/div/div/div/div/div/div/div/button")
    decline_cookies_button = next((x for x in cookie_buttons if x.text == "Avvisa alla"),None)
    webdriver.ActionChains(driver).click(decline_cookies_button).perform()

    # repeatedly scroll down, click "view more" and wait
    for _ in range(100): #TODO: 100
        webdriver.ActionChains(driver).scroll_by_amount(0, 100000).perform()
        time.sleep(2*fac) # a bit of a hack
        view_more_button_candidates = driver.find_elements(By.XPATH, "//main//section//button")
        view_more_button = next((x for x in view_more_button_candidates if x.text == "Visa alla"),None)
        if view_more_button == None:
            break # no more view more => done
        webdriver.ActionChains(driver).click(view_more_button).perform()
        time.sleep(3*fac) # a bit of a hack

    page_source: str = driver.page_source
    print(BeautifulSoup(page_source, "html.parser").prettify())
    #driver.quit()
    if get_url == url:
        return page_source
    else:
        return ""

#willys_html: str = get_willys_html("https://www.willys.se/erbjudanden/butik?StoreID=2117")
#cached_willys_html = open("willys.html", "r") 
#print(willys_html)
#exit(0)
#willys_html: str = cached_willys_html.read()
#soup: BeautifulSoup = BeautifulSoup(willys_html, "html.parser")
#print(willys_parse(soup))


#print(BeautifulSoup(page_source, "html.parser").prettify())

#<button data-testid="load-more-btn" class="Buttonstyles__StyledButton-sc-1g4oxwr-0 dLUxJp LoadMore__LoadMoreBtn-sc-16fjaj7-3 bnbvpm" type="button">Visa alla</button>


#soup = address_to_soup("https://www.willys.se/erbjudanden/butik?StoreID=2117")
#willys_parse(soup)

#soup = address_to_soup("https://www.ica.se/butiker/maxi/orebro/maxi-ica-stormarknad-universitetet-orebro-15088/erbjudanden/")
#print(ica_parse(soup))
soup = address_to_soup("https://www.coop.se/butiker-erbjudanden/coop/coop-kronoparken/")
output = (coop_parse(soup))
#soup = address_to_soup("https://www.lidl.se/veckans-erbjudanden")
#output = (lidl_parse(soup))

for el in output:
    el.print()
    print()
