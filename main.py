__author__ = "Surendhar A"
# coding: utf-8

from playwright.sync_api import sync_playwright
from bs4 import BeautifulSoup
from urllib.parse import urlparse
import re
import getpass


def orders_iter(order_cards, target_url):
    order_list = []
    for order_iter in order_cards:
        order_dict = {}
        order_card = BeautifulSoup(order_iter.inner_html().strip(), features='html.parser')

        # Attempt to find product price in either 'order-header' or 'order-info' for product price
        product_price = None
        if order_card.select('.order-header'):
            product_price = order_card.select_one('.order-header .a-column.a-span2').text.strip()
        elif order_card.select('.order-info'):
            product_price = order_card.select_one('.order-info .a-column.a-span2').text.strip()

        # Clean up the product price
        product_price = re.sub(r'Total|^\s*|\s*$', '', product_price or 'n/a').strip()

        # Extract product title, link and price
        product_title = order_card.select_one('.a-fixed-left-grid-col.a-col-right a.a-link-normal').text.strip()
        product_link = 'https://' + urlparse(target_url).netloc + order_card.select_one('.a-fixed-left-grid-col.a-col-right a.a-link-normal').get('href')

        order_dict['product_title'] = product_title
        order_dict['product_price'] = product_price
        order_dict['product_link'] = product_link

        order_list.append(order_dict)
    if not order_list:
        order_list.append({'info': 'No orders'})
    return order_list


def login_to_amazon(username, password, target_url):
    retry_count = 0
    retry_limit = 1

    while retry_count < retry_limit:
        with sync_playwright() as p:
            try:
                # Launch a chrome browser
                browser = p.chromium.launch(headless=False)
                context = browser.new_context()
                page = context.new_page()

                page.goto(target_url)
                page.wait_for_timeout(2000)

                # Check if login is required
                if page.is_visible("input#ap_email"):
                    page.fill("input#ap_email", username)

                    # Check if 'Continue' button is present
                    if page.is_visible("input#continue"):
                        page.click("input#continue")

                    page.wait_for_timeout(2000)
                    page.fill("input#ap_password", password)
                    page.wait_for_timeout(2000)
                    page.click("input#signInSubmit")
                    page.wait_for_timeout(5000)

                    # Check if login was successful
                    if page.locator("h1:has-text('Your Orders')").is_visible():
                        print("Login successful")
                        order_cards = page.query_selector_all(".order-card")
                        print(orders_iter(order_cards, target_url))

                    # Check for 'Enter verification code'
                    elif page.is_visible("text=Enter verification code") or page.is_visible("text=Solve this puzzle to protect your account"):
                        print("Enter verification code is required. Waiting for 30 seconds...")
                        page.wait_for_timeout(30000)
                        print("Please enter the verification code manually and submit it.")

                        # Wait until the user has manually submitted the verification code
                        page.wait_for_timeout(5000)

                        # Check for successful login
                        if page.locator("h1:has-text('Your Orders')").is_visible():
                            print("Login successful after verification code")
                            order_cards = page.query_selector_all(".order-card")
                            print(orders_iter(order_cards, target_url))
                        else:
                            print("Unable to load orders page after verification code.")
                    else:
                        print("Login failed or redirected to an unexpected page.")
                elif page.is_visible("text=Looking for something"):
                    print("Invalid URL")
                else:
                    print("Unable to initiate login.")

                retry_count += 1
                browser.close()
            except Exception as e:
                # Exception handling and shows error with description
                if 'ERR_NAME_NOT_RESOLVED' in str(e).strip():
                    print("Invalid domain", target_url)
                    retry_count = retry_limit
                else:
                    print("Error description: ",str(e).strip())
                    retry_count = retry_limit


# Prompt user to enter username and password. Password won't visible in terminal
username = input("Enter username: ")
password = getpass.getpass("Enter password: ")

# Amazon purchased items for year 2023
# target_url = "https://www.amazon.in/your-orders/orders?timeFilter=year-2023&ref_=ppx_yo2ov_dt_b_filter_all_y2023"

# Amazon purchased items for year 2024
target_url = "https://www.amazon.in/your-orders/orders?timeFilter=year-2024&ref_=ppx_yo2ov_dt_b_filter_all_y2024"

#Invoke login_to_amazon() method
login_to_amazon(username, password, target_url)
