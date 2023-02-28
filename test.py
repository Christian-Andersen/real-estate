from selenium import webdriver
from selenium.webdriver.firefox.options import Options
from selenium.webdriver.firefox.service import Service
from webdriver_manager.firefox import GeckoDriverManager
import time

webpages = [
    'https://www.domain.com.au/sold-listings/',
    'https://www.domain.com.au/sold-listings/?state=qld'
]
start_time = time.time()
options = Options()
options.add_argument('-headless')
service=Service('geckodriver.exe')
driver = webdriver.Firefox(options=options, service=service)
for webpage in webpages:
    driver.get(webpage)
    html_content = driver.page_source
    driver.quit()
    print(len(html_content))
driver.quit()
print(time.time()-start_time)
