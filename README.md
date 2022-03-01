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
import argparse  
import datetime  
import json  
import logging  
import random  
import re  
import time  
from logging.handlers import RotatingFileHandler  
import pandas as pd  
from bs4 import BeautifulSoup, SoupStrainer  
from fake_useragent import UserAgent  
from selenium import webdriver  
from selenium.webdriver.chrome.options import Options  
from selenium.webdriver.common.by import By  
from selenium.webdriver.support import expected_conditions as EC  
from selenium.webdriver.support.ui import WebDriverWait  
from sqlalchemy import create_engine  
from sqlite_db import Database  
import sqlite3

## Roadmap
+ Handle all proxies exceptions and retry when not working
+ Multiple scraping sites support
+ scrape data for specific car models
+ command line argument to change waiting time between each scrape

                

