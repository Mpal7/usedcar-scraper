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


class Scraper:
    # generates the logger
    logger = logging.getLogger("automobili_logger")
    # when the log reaches a certain number of bytes, it gets “rolled over”.
    # this occurs when the file size is about to be exceeded.
    handler = RotatingFileHandler("automobileit.log", 'a', maxBytes=10000, backupCount=1)  # maybe try 1mb
    # allocate handler for logging
    logger.addHandler(handler)

    def __init__(self, sysargv):
        self.db_location=sysargv.database
        self.sites = sysargv.site
        self.mode = sysargv.scraping  # update-->oneshot scrape, live-->continous scrape
        self.use_proxy = sysargv.browsing
        self.url_automobileit = 'https://www.automobile.it/'
        self.url_autoscout24 = 'https://www.autoscout24.it/'
        self.driver_path = r'C:\PycharmProjects\usedcar-ml\chromedriver.exe'
        self.df_proxy_check = pd.DataFrame(columns=['proxy', 'datetime'])
        self.proxy_list = None

    def start_driver(self, tries=5):
        """
        The User-Agent header helps the server identify the device, or say the source of the request. By changing
        the agent after some requests and by using a proxy we increase the chances that the sites doesn't block the
        device
        """
        # se c'è qualche driver aperto provo a chiuderlo
        driver = None
        found = False
        for i in range(0, tries):
            if self.use_proxy == 'proxy':
                if not self.proxy_list:
                    self.proxy_list = self.get_proxy_list()
                    for proxy in self.proxy_list:
                        # returns true if proxy has to rotate
                        rotate = self.check_proxy_rotation(proxy)
                        rotate = self.check_proxy_rotation(proxy)
                        if rotate:
                            print('proxy already used recently,checking next proxy')
                        else:
                            ip_port_proxy = proxy[0] + ':' + proxy[1]
                            options = Options()
                            ua = UserAgent()
                            user_agent = ua.random
                            options.add_argument(f'user-agent={user_agent}')
                            options = webdriver.ChromeOptions()
                            options.add_argument('--proxy-server={}'.format(ip_port_proxy))
                            options.add_argument('--disable-blink-features=AutomationControlled')
                            options.add_experimental_option('excludeSwitches', ['enable-logging'])
                            options.add_experimental_option("excludeSwitches", ["enable-automation"])
                            options.add_experimental_option('useAutomationExtension', False)
                            driver = webdriver.Chrome(options=options,
                                                      executable_path=self.driver_path)
                            self.set_viewport_size(driver, 800, 600)
                            try:
                                # checks if proxy is working
                                print("checking if proxy is working...")
                                driver.get(self.url_automobileit)
                                time.sleep(4)
                                driver.get(self.url_automobileit)
                                # the following line looks for the automobile.it logo jsx-2181658497 to check if the page was loaded
                                if WebDriverWait(driver, 5).until(
                                        EC.visibility_of_element_located(
                                            (By.CLASS_NAME, "jsx-1084726123"))).is_displayed():
                                    print('proxy is working')
                                    found = True
                                    break
                                else:
                                    print("non sta facendo nulla?")
                            except Exception:
                                if self.proxy_list.index(proxy) == len(self.proxy_list) - 1:
                                    print("Could not find a working proxy in this list")
                                else:
                                    print('Current proxy {} not working...trying next one'.format(proxy))
                                driver.quit()
            else:
                ua = UserAgent()
                options = Options()
                user_agent = ua.random
                options.add_argument(f'user-agent={user_agent}')
                options.add_argument('--disable-blink-features=AutomationControlled')
                options.add_experimental_option("excludeSwitches", ["enable-automation"])
                options.add_experimental_option('excludeSwitches', ['enable-logging'])
                options.add_experimental_option('useAutomationExtension', False)
                options = webdriver.ChromeOptions()
                driver = webdriver.Chrome(options=options,
                                          executable_path=self.driver_path)
                driver.execute_script("Object.defineProperty(navigator, 'webdriver', {get: () => undefined})")
                self.set_viewport_size(driver, 800, 600)
                found = True
                break
        return driver

    def scrape(self):
        if 'autoscout24' in self.sites:
            self.scrape_autoscout24()
        if 'automobileit' in self.sites:
            self.scrape_automobileit('automobileit')

    def scrape_autoscout24(self):
        """on hold since autoscout doesn't allow to scrape more than 20 pages ie 400 cars"""
        try:
            with Database(self.db_location) as db:
                db.create_table_data('autoscout24')
                db.add_column_urls('autoscout24')
            car_counter = 1  # counter for number of offers scraped
            cycle_counter = 0  # counter for the number of cycles performed in scraping
        except Exception as ex:
            self.logger.exception(ex)

    def scrape_automobileit(self, site_name):
        links = []
        driver = None
        try:
            populated = False
            with Database(self.db_location) as db:
                # print(db.chk_conn()) if true --> estabilished connection
                db.create_table_data(site_name)
                # checking if db is populated already
                db.execute("SELECT COUNT(*) FROM {}".format(site_name))
                if db.cur.fetchone()[0] > 0:
                    populated = True
            # first page example https://www.automobile.it/annunci/page-1?b=data&d=DESC
            car_counter_ai = 0  # counter for number of offers scraped
            cycle_counter_ai = 0  # counter for the number of cycles performed in scraping
            print("##### EXTRACTING NUMBER OF PAGES ON THE SITE #####")
            page_n = self.page_number_extractor(site_name)
            time.sleep(10)
            # for testing purposes to 3 but in reality page_n+1
            count_ua = 0
            start_time = datetime.datetime.now()
            print('started scraping {}'.format(start_time))
            for page in range(1, page_n):
                driver, count_ua = self.check_count_ua(driver, count_ua)
                print("#####PAGE NUMBER: ", page)
                # mi recupero i link di ogni offerta
                links = self.links_finder(driver, site_name, "usate/page-" + str(page) + "?b=data&d=DESC")
                if len(links) == 0 or links is None:
                    raise ValueError("couldn't get a list of links\n")
                for offer_link in links:
                    # this regex finds the offer id in the string with the link to the offer
                    offer_id = re.findall('(?<=\/)(\w+)', offer_link)[1]
                    if not self.check_offer_id_existance(site_name, offer_id):
                        time.sleep(random.randint(3, 6))
                        self.scrape_offer(driver, offer_link, offer_id)
                        car_counter_ai += 1
                        # driver.close()
                    else:
                        print("##### Offer already in the database, processing the next one #####\n")
                    count_ua += 1
                    # check_count_ua controlla quante offerte ho scrapato per effettuare reset driver evdentualmente
                    driver, count_ua = self.check_count_ua(driver, count_ua)
                    if car_counter_ai % 50 == 0:
                        print("####Scraped ", car_counter_ai, " offers.#####\n")
        except Exception as ex:
            self.logger.exception(ex)

    def set_viewport_size(self, driver, width, height):
        '''
        Sometimes webdriver get's blocked by detection of standard viewport
        :param width:
        :param height:
        :return:
        '''
        window_size = driver.execute_script("""
            return [window.outerWidth - window.innerWidth + arguments[0],
              window.outerHeight - window.innerHeight + arguments[1]];
            """, width, height)
        driver.set_window_size(*window_size)

    def check_count_ua(self, driver, count_ua):
        if count_ua > random.randint(random.randint(20, 30),
                                     random.randint(50, 60)):  # randomly reinitialize session with different UA and IP
            count_ua = 0
            driver.close()
            print("reinitializing UA and IP")
        if count_ua == 0:
            for i in range(0, 10):
                driver = self.start_driver()
                if driver is not None:
                    break
                else:
                    # wait 2.5 minutes before trying again
                    time.sleep(150)
        count_ua = 1
        return driver, count_ua

    def check_proxy_rotation(self, proxy):
        '''
        da finire,serve a controllare che non utilizzi sempre lo stesso proxy confrontandolo con una lista di proxy
        già usata e aggiornandola periodicamente
        :param start_time:
        :return:
        '''
        curr_time = datetime.datetime.now()
        bool_rotation = False
        try:
            # checking if proxy is already enlisted in proxy check df
            print('\nchecking if proxy ', proxy, ' has to be rotated...')
            mask = [x == proxy for x in self.df_proxy_check.proxy.values]
            row_proxy = self.df_proxy_check[mask].index[0]
            # se non è passata almeno un'ora e mezza dall'utilizzo del proxy usane un altro
            if (curr_time - self.df_proxy_check.loc[self.df_proxy_check.index[row_proxy], 'datetime']) < 5400:
                print("proxy still inside one hour and half rotation range, rotating!")
                bool_rotation = True
            else:
                # update time of last usage for proxy
                self.df_proxy_check.loc[self.df_proxy_check.index[row_proxy], 'datetime'] = curr_time

        except IndexError:
            dict = {'proxy': proxy, 'datetime': curr_time}
            self.df_proxy_check = self.df_proxy_check.append(dict, ignore_index=True)
            print("\n proxy doesn't have to rotate, added proxy to rotation control dataframe:\n ", self.df_proxy_check)

        return bool_rotation

    def flatten_json(self, json):
        out = {}

        def flatten(x, name=''):
            if type(x) is dict:
                for a in x:
                    flatten(x[a], name + a + '_')
            elif type(x) is list:
                i = 0
                for a in x:
                    flatten(a, name + str(i) + '_')
                    i += 1
            else:
                out[name[:-1]] = x

        flatten(json)
        return out

    def scrape_offer(self, driver, offer_link, offer_id):
        '''

        :param site_name:
        :param offer_id:
        :return:
        '''
        today = datetime.date.today()
        d3 = today.strftime("%m-%y")

        for i in range(10):
            if i > 0:
                time.sleep(random.randint(1, 3))
            try:
                driver.get("https://www.automobile.it" + offer_link)
                break
            except Exception:
                driver.quit()
                print("driver: " + str(driver) + " couldn't open offer page to scrape, trying to reinitialize browser")
                driver = self.start_driver()
                pass
            if i == 4:
                raise ValueError("webdriver keeps getting blocked, shutting down script")

        # sometimes loads a different page, uncomment the following in case if you want to be safe
        # driver.get("https://www.automobile.it" + offer_link)
        try:
            if WebDriverWait(driver, 10).until(
                    EC.visibility_of_element_located((By.CLASS_NAME, "jsx-1084726123"))).is_displayed():
                html_source = driver.page_source  # \<span class="jsx-2352758194 LastPage">7500\</span>
                soup = BeautifulSoup(html_source, 'lxml')
        except Exception:
            print('page did not load correctly')
            driver.quit()
        for script in soup.find_all('script'):
            if "__NEXT_DATA__" in str(script.get('id')):
                match = re.findall(r'"shift":5}},(.*?)},"structuredData"', str(script))
                match_price = re.findall(r'"price":"(.*?)","content_type"', str(script))
        try:
            sub_html_p = "{" + match[0] + "}}"
            d = json.loads(sub_html_p.replace("'", ''))
            flattened_json = self.flatten_json(d)
            # popping keys with links that do not contains either column name or values
            for key in list(flattened_json.keys()):
                if 'link' in key:
                    flattened_json.pop('vehicleInformation_basicInfo_0_link', None)
            # preparing dictionary --> dataframe
            out = {}
            for key, value in flattened_json.items():
                if 'title' in key:
                    col_name = value
                else:
                    out[col_name] = value
            out['scraping_date'] = d3
            out['prezzo'] = match_price[0]
            out['offer_id'] = offer_id
            df = pd.DataFrame.from_dict(out, orient='index').T
            df.columns = df.columns.str.lower()
            df.columns = df.columns.str.replace(" ", "_")
            with Database(self.db_location) as db:
                engine = create_engine(r'sqlite:///F:\DATABASE\USEDCARS\usedcars.db', echo=False)
                df.to_sql('automobileit', con=engine, if_exists='append', index=False)
        except Exception:
            print("couldn't scrape this offer")
            pass
        # inserisco il dataframe nel db sql

    def check_offer_id_existance(self, table_name, value):
        # checking if offer is already in the DB
        found = False
        with Database(self.db_location) as db:
            db.cur.execute("SELECT EXISTS(SELECT 1 FROM {} WHERE offer_id={})".format(table_name, value))
            # return (0,) if doesn't exists, otherwise (1,)
            check = str(db.cur.fetchone())
            if "1" in check:
                found = True
        return found

    def links_finder(self, driver, site_name, page_url):
        for i in range(5):
            time.sleep(random.randint(2, 5))
            try:
                driver.get(self.url_automobileit + page_url)
                break
            except Exception:
                driver.quit()
                time.sleep(5)
                print("driver: " + str(
                    driver) + " couldn't get offer links from the page, trying to reinitialize browser")
                driver = self.start_driver()
                pass
            if i == 4:
                raise ValueError("webdriver keeps getting blocked, shutting down script")
        time.sleep(random.randint(3, 6))
        # driver.get(self.url_automobileit + page_url)
        html = driver.page_source
        # soup = BeautifulSoup(html)  # make BeautifulSoup
        # prettyHTML = soup.prettify()
        # print(prettyHTML)
        links = []
        if site_name == 'automobileit':
            only_a_tags = SoupStrainer("a")
            soup = BeautifulSoup(html, 'lxml', parse_only=only_a_tags)
            for div in soup.find_all('a'):
                data_link = div.get("href")
                # di tutti gli href tiene solo quelli che finiscon con più di 5 numeri e quindi sono sicuro i link interessati
                if data_link is not None:
                    if data_link[-5:].isdigit():
                        links.append(
                            data_link)  # ex /napoli-peugeot-bipper-bipper-tepee-1-3-hdi-75-s-s-rob-prem/162177573
        driver.close()
        return links

    def page_number_extractor(self, site_name):
        match = 0
        page_number = 0
        # triying 10 times
        for i in range(0, 10):
            driver = self.start_driver()
            driver.get("https://automobile.it/usate/page-1?valutazione_del_venditore=tutti&b=data&d=DESC")
            html = driver.page_source
            if site_name == 'automobileit':
                try:
                    only_span_tags = SoupStrainer("span")  # \<span class="jsx-2352758194 LastPage">7500\</span>
                    soup = BeautifulSoup(html, 'lxml', parse_only=only_span_tags)
                    for span in soup.find_all('span'):
                        if 'LastPage' in str(span.get('class')):
                            match = re.findall(r'(?<=>)(.*?)(?=<)', str(span))
                except Exception as ex:
                    print("Overview:" + str(ex) + "" * 50, end="\ r")
            driver.close()
            if len(match) == 0:
                raise ValueError("could not find number of pages in automobile.it")
            else:
                page_number = int(match[0])
            if page_number > 0:
                break
            else:
                # wait 1 minutes before trying again
                time.sleep(60)
        if not page_number > 0:
            raise ValueError("could not find number of pages in automobile.it")
        print("\n#### Number of pages with offers found: ", page_number)
        return page_number

    def get_proxy_list(self):
        '''
        :return filtered:
        :rtype: list

        if opens and closes immediately without doing anything check chrome version and chromedriver.exe
        or extraction from the site
        '''
        print("sto prendendo la lista dei server proxy")
        loop = True
        filtered = None
        accepted_countries = ['DE', 'NL', 'PL', 'RU', 'UA', 'BE', 'FR', 'US']
        options = webdriver.ChromeOptions()
        options.add_argument("start-maximized")
        options.add_experimental_option("excludeSwitches", ["enable-automation"])
        options.add_experimental_option('useAutomationExtension', False)
        while loop:
            driver = webdriver.Chrome(options=options,
                                      executable_path=r'C:\PycharmProjects\usedcar-ml\chromedriver.exe')
            driver.get("https://sslproxies.org/")
            driver.execute_script("return arguments[0].scrollIntoView(true);", WebDriverWait(driver, 20).until(
                EC.visibility_of_element_located((By.XPATH,
                                                  "//table[@class='table table-striped table-bordered']//th[contains(., 'IP Address')]"))))
            ips = [my_elem.get_attribute("innerHTML") for my_elem in WebDriverWait(driver, 5).until(
                EC.visibility_of_all_elements_located((By.XPATH,
                                                       "//table[@class='table table-striped table-bordered']//tbody//tr/td[position() = 1]")))]
            ports = [my_elem.get_attribute("innerHTML") for my_elem in WebDriverWait(driver, 5).until(
                EC.visibility_of_all_elements_located((By.XPATH,
                                                       "//table[@class='table table-striped table-bordered']//tbody//tr/td[position() = 2]")))]
            countries = [my_elem.get_attribute("innerHTML") for my_elem in WebDriverWait(driver, 5).until(
                EC.visibility_of_all_elements_located((By.XPATH,
                                                       "//table[@class='table table-striped table-bordered']//tbody//tr/td[position() = 3]")))]
            driver.quit()
            filtered = []
            proxies = []
            for i in range(0, len(ips)):
                proxies.append([ips[i], ports[i], countries[i]])
            for elem in proxies:
                if not set(accepted_countries).isdisjoint(elem):
                    filtered.append(elem)
            if filtered:
                loop = False
        return filtered


# deprecated using argparse library
'''def check_inputs(args):
    list_sites = ['autoscout24', 'automobileit']
    try:
        arg1 = args[1]
    except IndexError:
        raise IndexError('Please provide a compatible functioning mode, either <update> or <live>')
    if (arg1 != 'update') and (arg1 != 'live'):
        raise ValueError('Please provide a compatible functioning mode, either <update> or <live>')
    try:
        arg2 = args[2]
    except IndexError:
        raise IndexError('Please provide <proxy> or <notproxy> for proxy usage mode')
    if (arg2 != 'false') and (arg2 != 'true'):
        raise ValueError('Please provide a compatible functioning mode, either <update> or <live>')
    try:
        args[3]
    except IndexError:
        raise IndexError('Please provide at least one compatible site, either <autoscout24> or <automobileit>')
    for arg in args[3:]:
        if arg not in list_sites:
            raise ValueError('Please provide a compatible site, either <autoscout24> or <automobileit>')
'''

if __name__ == "__main__":
    parser = argparse.ArgumentParser()
    parser.add_argument('--scraping', choices=['update'], help='Goes through offer pages once, live mode to be added '
                                                               'in the future')
    parser.add_argument('--browsing', choices=['proxy', 'no-proxy'], help='whether  to use proxy or not for scraping')
    parser.add_argument('--site', choices=['automobileit'], help='site to scrape, more sites to be added in the future')
    parser.add_argument('--database', help='filepath to the database location eg <F:/DATABASE/USEDCARS/usedcars.db>')
    args = parser.parse_args()
    scraper = Scraper(args)
    scraper.scrape()
