import csv
import os
import re
# Define your item pipelines here
#
# Don't forget to add your pipeline to the ITEM_PIPELINES setting
# See: https://docs.scrapy.org/en/latest/topics/item-pipeline.html


# useful for handling different item types with a single interface
from itemadapter import ItemAdapter


class CarsdataPipeline:
    def process_item(self, item, spider):
        return item


class WriteCsvPipeline(object):
    def open_spider(self, spider):
        file_name = f'{spider.name}_output.csv'
        self.file = open(file_name, 'w', newline='', encoding='utf-8')
        self.writer = csv.writer(self.file)
        self.file_name = file_name
        self.header_written = False

    def close_spider(self, spider):
        self.file.close()

    def process_item(self, item, spider):
        if not self.header_written:
            self.writer.writerow(item.keys())  # Write headers
            self.header_written = True
        self.writer.writerow(item.values())
        return item


class TextCleaningPipeline(object):
    def process_item(self, item, spider):
        if item.get('text_field'):
            # Replace more than two spaces with a single space
            item['text_field'] = re.sub(r' {3,}', ' ', item['text_field'])

        # Preprocess item fields to remove or replace newline characters
        for key, value in item.items():
            if isinstance(value, str):
                # Remove newline characters
                item[key] = value.replace('\n', ' ').replace('\r', ' ')
                # Alternatively, you could replace newline characters with a space
                # item[key] = value.replace('\n', ' ').replace('\r', ' ')

        return item
