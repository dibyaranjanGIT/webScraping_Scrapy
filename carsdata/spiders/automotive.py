import os
import random
from pathlib import Path
from datetime import datetime
from urllib.parse import urljoin
import scrapy
from scrapy import Selector
from carsdata.items import AutomotiveItem
import logging


class CarsSpider(scrapy.Spider):
    name = "automotive"
    # deltafetch_enabled = True
    allowed_domains = ["www.theautomotiveindia.com"]

    def __init__(self, *args, **kwargs):
        super(CarsSpider, self).__init__(*args, **kwargs)
        # Define the directory name
        self.urls_dir = 'urls_directory'
        # Create the directory if it doesn't exist
        os.makedirs(self.urls_dir, exist_ok=True)
        self.urls_file = os.path.join(self.urls_dir, f'{self.name}_scraped_urls.txt')
        self.scraped_urls = set()
        self.load_scraped_urls()

        # Ensure logs directory exists
        logs_dir = "logs"
        os.makedirs(logs_dir, exist_ok=True)

        # Create log file name based on current date and time
        log_file_name = self.name + '_' + datetime.now().strftime("%Y-%m-%d_%H-%M-%S") + ".log"
        log_file_path = os.path.join(logs_dir, log_file_name)

        # Configure logging
        logging.basicConfig(filename=log_file_path, filemode='w',
                            format='%(asctime)s,%(msecs)d %(name)s %(levelname)s %(message)s',
                            datefmt='%H:%M:%S',
                            level=logging.INFO)

        # Set user agent list
        self.user_agent_list = [
            'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/91.0.4472.124 Safari/537.36',
            'Mozilla/5.0 (Windows NT 10.0; Win64; x64; rv:89.0) Gecko/20100101 Firefox/89.0',
            'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/91.0.4472.124 Safari/537.36 Edg/91.0.864.59',
            'Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/605.1.15 (KHTML, like Gecko) Version/14.1.1 Safari/605.1.15',
            'Mozilla/5.0 (Linux; Android 11; Pixel 5) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/91.0.4472.120 Mobile Safari/537.36',
            'Mozilla/5.0 (iPhone; CPU iPhone OS 14_6 like Mac OS X) AppleWebKit/605.1.15 (KHTML, like Gecko) Version/14.0.3 Mobile/15E148 Safari/604.1',
            'Mozilla/5.0 (X11; Linux x86_64; rv:89.0) Gecko/20100101 Firefox/89.0',
            'Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/91.0.4472.124 Safari/537.36',
            'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/74.0.3729.169 Safari/537.36 OPR/76.0.4017.123',
            'Mozilla/5.0 (Windows NT 10.0; WOW64; Trident/7.0; rv:11.0) like Gecko'
        ]

    def load_scraped_urls(self):
        try:
            with open(self.urls_file, 'r') as f:
                for url in f:
                    self.scraped_urls.add(url.strip())
        except FileNotFoundError:
            pass

    def mark_url_as_scraped(self, url):
        with open(self.urls_file, 'a') as f:
            f.write(url + '\n')
        self.scraped_urls.add(url)

    def start_requests(self):
        logging.info("Starting requests")
        urls = [
            "https://www.theautomotiveindia.com/forums/node/indian-auto-sector.5/",
            "https://www.theautomotiveindia.com/forums/node/ownership-reviews.12/"
        ]

        self.base_url = 'https://www.theautomotiveindia.com'
        for url in urls:
            yield scrapy.Request(url=url, callback=self.parse, headers={
                "User-Agent": self.user_agent_list[random.randint(0, len(self.user_agent_list) - 1)]})

    def parse(self, response):
        logging.info(f"Processing URL: {response.url}")
        try:
            # Extract URLs from parent page
            xpath_query = '//div[contains(@class, "structItem-title") and not(.//span[contains(text(), "2-Wheeler")])]//a[not(contains(@href, "prefix"))]/@href'
            links = response.xpath(xpath_query).extract()

            for link in links:
                full_link_url = urljoin(self.base_url, link)
                yield response.follow(full_link_url, self.parse_child_page, meta={'deltafetch_key': full_link_url},
                                      headers={"User-Agent": random.choice(self.user_agent_list)})

            # Follow pagination on parent page
            next_page_link = response.xpath(
                '//a[contains(@class, "pageNav-jump") and contains(@class, "pageNav-jump--next")]/@href').get()
            if next_page_link is not None:
                full_next_page_link = urljoin(self.base_url, next_page_link)
                yield response.follow(full_next_page_link, self.parse, headers={
                    "User-Agent": self.user_agent_list[random.randint(0, len(self.user_agent_list) - 1)]})
        except Exception as e:
            logging.error(f"Error occur at {str(e)}")

    def parse_child_page(self, response):
        logging.info(f"Processing child page: {response.url}")
        if response.url in self.scraped_urls:
            logging.info(f"Skipping already scraped URL: {response.url}")
            return
        try:
            # sel = Selector(response)
            articles = response.xpath('//article[starts-with(@id, "js-post-")]')
            for article in articles:
                automotive_data = AutomotiveItem()
                automotive_data['url'] = response.url
                automotive_data['Location'] = ''
                automotive_data['Source'] = 'Automotiveindia'

                # To get the comment time
                date_time = article.xpath('.//time[@class="u-dt"]/@title').get()
                date_object = datetime.strptime(date_time, "%b %d, %Y at %I:%M %p")

                Month = date_object.strftime("%B")
                Year = date_object.strftime("%Y")
                automotive_data['Date'] = date_object
                automotive_data['Month'] = Month
                automotive_data['Year'] = Year

                # # To find the Parent quote and post message text
                quote_text = article.xpath(
                    '//div[@class="bbCodeBlock bbCodeBlock--expandable bbCodeBlock--quote"]//text()').getall()
                quote_text = ''.join(quote_text).strip()
                all_text_except_quote = response.xpath(
                    '//div[@class="bbWrapper"]//text()[not(ancestor::div[contains(@class, "bbCodeBlock bbCodeBlock--expandable bbCodeBlock--quote")])]') \
                    .getall()
                post_message_text = ''.join([text.strip() for text in all_text_except_quote])

                # print("Quote Text:", quote_text)
                # print("Post Message Text:", post_message_text)
                automotive_data['ParentComment'] = quote_text
                automotive_data['UserComment'] = post_message_text

                # Mark the URL as scraped
                self.mark_url_as_scraped(response.url)

                yield automotive_data

            # Follow pagination on child page
            next_page_link = response.xpath('//a[@class="pageNav-jump pageNav-jump--next"]/@href').get()
            if next_page_link is not None:
                full_next_page_child_link = urljoin(self.base_url, next_page_link)
                yield response.follow(full_next_page_child_link, self.parse_child_page,
                                      headers={"User-Agent": random.choice(self.user_agent_list)})
        except Exception as e:
            logging.error(f"Error occur at {str(e)}")
