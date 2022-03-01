# usedcar-ml
Used car scraping script from popular italian websites 
##Warnings:  
* Website HTML can change overtime causing the code to not work in some areas
* Always check selenium ChromeDriver version compatibility with current browser version
* Proxy mode not stable as the proxies used are free and can sometimes not work.

## usage: 
usage: scraping.py [-h] [--scraping {update}] [--browsing {proxy,no-proxy}] [--site {automobileit}] [--database DATABASE]
  
optional arguments:  

  -h, --help            show this help message and exit  

  --scraping {update}   Goes through offer pages once, live mode to be added in the future  

  --browsing {proxy,no-proxy} whether to use proxy or not for scraping  

  --site {automobileit} site to scrape, more sites to be added in the future

  --database DATABASE   filepath to the database location eg < F:/DATABASE/USEDCARS/usedcars.db >

chromedrive.exe correct version for your chrome browser is required

## Dependencies
to install dependencies use pip install -r req.txt

## Roadmap
+ Handle all proxies exceptions and retry when not working
+ Multiple scraping sites support
+ scrape data for specific car models
+ command line argument to change waiting time between each scrape

                

