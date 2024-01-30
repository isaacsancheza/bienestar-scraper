#!/usr/bin/env python3
import logging
from typing import Any
from locale import setlocale, LC_TIME
from decimal import Decimal
from datetime import timedelta

from dateutil import parser
from selenium.webdriver import Chrome, ChromeOptions
from selenium.webdriver.common.by import By


setlocale(LC_TIME, 'es_MX.UTF-8')
logging.basicConfig()
logger = logging.getLogger('scraper')
logger.setLevel(logging.INFO)


def get_entries() -> list[dict[str, Any]]:
    logger.info('starting webdriver...')
    options = ChromeOptions()
    options.add_argument('--headless')
    options.add_argument('--no-sandbox')
    options.add_argument('--disable-gpu')
    options.add_argument('--disable-dev-shm-usage')
    driver = Chrome(options=options)

    entries = []
    try:
        url = 'https://www.gob.mx/bienestar/archivo/prensa?idiom=es'
        logger.info(f'visiting: {url}')
        driver.get(url)
        prensa = driver.find_element(By.XPATH, '//div[@id="prensa"]')
        articles = prensa.find_elements(By.XPATH, './/article')
        
        logger.info('obtaning articles...')
        for article in articles:
            p = article.find_element(By.XPATH, './p')
            time = p.find_element(By.XPATH, './time')

            h2 = article.find_element(By.XPATH, './h2')
            a = article.find_element(By.XPATH, './a')

            title = h2.text.strip()
            href = a.get_attribute('href')
            datetime = time.get_attribute('datetime')
            if not title:
                logger.info('article has no title')
                continue
            if not href:
                logger.info(f'article has no href attribute: {title}')
                continue
            if not datetime:
                logger.info(f'article has no datetime attribute: {title}')
                continue
            datetime = parser.parse(datetime)
            ttl = datetime + timedelta(weeks=4 * 6)
            date = datetime.strftime('%d de %B de %Y')
            entry = {
                'ttl': Decimal(ttl.timestamp()),
                'date': date,
                'link': href.strip(),
                'title': title,
                'timestamp': Decimal(datetime.timestamp()),
            }
            entries.append(entry)
        logger.info(f'found {len(entries)} entries')
    except Exception as e:
        logger.exception(e)
    except KeyboardInterrupt:
        logger.info('aborting...')
    finally:
        try:
            driver.quit()
        except:
            pass
    return sorted(entries, key=lambda d: d['timestamp'])


if __name__ == '__main__':
    get_entries()
