# TO create a scrapy project

scrapy startproject tutorial

tutorial/
    scrapy.cfg            # deploy configuration file

    tutorial/             # project's Python module, you'll import your code from here
        __init__.py

        items.py          # project items definition file

        middlewares.py    # project middlewares file

        pipelines.py      # project pipelines file

        settings.py       # project settings file

        spiders/          # a directory where you'll later put your spiders
            __init__.py

# To create a spider
scrapy genspider my_spider test.com

# To run the scrapy
  Navigate to tutorial project
scrapy crawl spider_name
