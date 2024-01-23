import os
import random
from pathlib import Path
from datetime import datetime
import scrapy
from scrapy import Selector
from carsdata.items import TeamBhpItem
import logging


class CarsSpider(scrapy.Spider):
    name = "teambhp"
    # deltafetch_enabled = True
    allowed_domains = ["www.team-bhp.com"]

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
            "https://www.team-bhp.com/forum/official-new-car-reviews/",
        ]
        for url in urls:
            yield scrapy.Request(url=url, callback=self.parse, headers={
                "User-Agent": self.user_agent_list[random.randint(0, len(self.user_agent_list) - 1)]})

    def parse(self, response):
        logging.info(f"Processing URL: {response.url}")
        try:
            # Extract URLs from parent page
            links = response.xpath('//a[starts-with(@id, "thread_title_")]/@href').extract()
            for link in links:
                yield response.follow(link, self.parse_child_page, meta={'deltafetch_key': link}, headers={
                    "User-Agent": self.user_agent_list[random.randint(0, len(self.user_agent_list) - 1)]})

            # Follow pagination on parent page
            next_page_link = response.xpath('//a[contains(@title, "Next Page")]/@href').get()
            if next_page_link is not None:
                yield response.follow(next_page_link, self.parse, headers={
                    "User-Agent": self.user_agent_list[random.randint(0, len(self.user_agent_list) - 1)]})
        except Exception as e:
            logging.error(f"Error occured {str(e)}")

    def parse_child_page(self, response):
        logging.info(f"Processing child page: {response.url}")
        if response.url in self.scraped_urls:
            logging.info(f"Skipping already scraped URL: {response.url}")
            return
        try:
            sel = Selector(response)
            posts_div = response.xpath('//div[@id="posts"]')
            if posts_div:
                matching_tables = posts_div.xpath('.//table[starts-with(@id, "post")]')
                for table in matching_tables:
                    team_bhp_data = TeamBhpItem()
                    team_bhp_data['url'] = response.url
                    team_bhp_data['Location'] = ''
                    team_bhp_data['Source'] = 'Teambhp'

                    # To get the comment time
                    td_text = table.xpath('.//td[@class="thead mod2022-radius-tl"]/text()').getall()
                    date_time = ''.join(td_text).strip()
                    date_object = date_time.split(",")[0]
                    if 'th' in date_object:
                        date_object = date_object.replace('th', '')
                    elif 'rd' in date_object:
                        date_object = date_object.replace('rd', '')
                    elif 'nd' in date_object:
                        date_object = date_object.replace('nd', '')
                    elif 'st' in date_object:
                        date_object = date_object.replace('st', '', 1)
                    date_object = datetime.strptime(date_object, "%d %B %Y")
                    Month = date_object.strftime("%B")
                    Year = date_object.strftime("%Y")
                    team_bhp_data['Date'] = date_object
                    team_bhp_data['Month'] = Month
                    team_bhp_data['Year'] = Year
                    # print(Year)

                    # To find the Parent quote
                    main_divs = posts_div.xpath('//div[contains(@id, "post_message_")]')
                    for main_div in main_divs:
                        # Find all inner divs with the specified class
                        quote_divs = main_div.xpath('.//div[contains(@class, "mod2022-radius-all-less")]')

                        quote_text = ''
                        for quote_div in quote_divs:
                            quote_text += ''.join(quote_div.xpath('.//text()').getall()).strip()

                        # Extract text from the main div (excluding the removed inner divs)
                        all_text_except_quote = main_div.xpath(
                            './/text()[not(ancestor::div[contains(@class, "mod2022-radius-all-less")])]').getall()
                        post_message_text = ''.join(all_text_except_quote).strip()

                        # print("Quote Text:", quote_text)
                        # print("Post Message Text:", post_message_text)
                        team_bhp_data['ParentComment'] = quote_text
                        team_bhp_data['UserComment'] = post_message_text

                        # Mark the URL as scraped
                        self.mark_url_as_scraped(response.url)

                        yield team_bhp_data

            # Follow pagination on child page
            next_page = response.css('a.next_page::attr(href)').get()
            if next_page is not None:
                yield response.follow(next_page, self.parse_child_page, meta={'deltafetch_key': next_page}, headers={
                    "User-Agent": self.user_agent_list[random.randint(0, len(self.user_agent_list) - 1)]})
        except Exception as e:
            logging.error(f"Error occured at {str(e)}")