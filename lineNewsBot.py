from selenium import webdriver
from bs4 import BeautifulSoup
import requests
import time
import re

class LineNewsCrawler:
    driver = None
    options = webdriver.ChromeOptions()
    options.add_experimental_option("excludeSwitches", ["enable-automation"])
    filter_source_keywords = ['中台灣生活網', 'LINE TV', 'LINE TODAY', 'TODAY 看世界', 'LINE TODAY 話題', 'TVBS新聞台', '民視新聞台',
                              '東森新聞台', '華視影音']
    filter_title_keywords = ['TVBS新聞台', '民視新聞台', '中台灣生活網', '東森新聞台', '華視影音']

    @staticmethod
    def parser_article_time(url):
        headers = {
            'user-agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/89.0.4389.82 Safari/537.36',
        }

        res = requests.get(url=url, headers=headers, timeout=10)
        soup = BeautifulSoup(res.content, 'lxml')
        publish_time_text = soup.find(
            attrs={'class': 'entityPublishInfo-meta-info text text--f text--greyLighten12 text--regular'}).text.strip()

        update_time = "".join(re.findall('發布於.*前', publish_time_text))
        if bool(update_time) is False:
            update_time = "".join(re.findall('發布於.*•', publish_time_text)).replace(' •', '')

        return update_time


    @classmethod
    def open_browser(cls):
        driver = webdriver.Chrome(options=cls.options)
        driver.get('https://today.line.me/tw/v2/tab')
        time.sleep(3)

        for i in range(0, 25000, 2000):
            js = "var q=document.documentElement.scrollTop=" + str(i)
            driver.execute_script(js)
            time.sleep(2)

        cls.driver = driver

    @classmethod
    def parserNews(cls):

        soup = BeautifulSoup(cls.driver.page_source, 'lxml')
        element = soup.find_all('div', attrs={'class': 'listModule'})

        title_list = []
        link_list = []
        source_list_1 = []
        for ele in element:
            link_ls = [links.get('href') for links in ele.find_all('a')]
            link_list += [link_ls]

            news_title_class = ele.find_all(attrs={'class': 'articleCard-content'})
            title_list += [[news_title.text.strip().replace('\u3000', '').split('\n')[0] for news_title in news_title_class]]

            news_source_class = ele.find_all(attrs={'class': 'articleCard-bottomWrap'})
            source_list_1 += [news_source.text.strip() for news_source in news_source_class]

        title_ls_1 = sum(title_list, [])
        link_ls_1 = sum(link_list, [])

        ele = soup.find('div', attrs={'class': 'foryou-list'})
        link_ls_2 = [links.get('href') for links in ele.find_all('a')]

        # clear data
        news_title_class = ele.find_all(attrs={'class': 'articleCard-content'})
        title_ls_2 = [news_title.text.strip().replace('\u3000', '').replace('\xa0', '').split('\n')[0] for news_title in
                      news_title_class]

        news_source_class = ele.find_all(attrs={'class': 'foryou-publisher'})
        source_ls_2 = [news_source.text.strip() for news_source in news_source_class]

        total_title = title_ls_1 + title_ls_2
        total_link = link_ls_1 + link_ls_2
        total_source = source_list_1 + source_ls_2

        news_dict_format = [{"title": title, "url": link, "source": source} for title, link, source in
                            zip(total_title, total_link, total_source)]
        news_dict_format = [news_dict for news_dict in news_dict_format if
                            news_dict.get('source') not in cls.filter_source_keywords]

        article_time_ls = []
        for news_dict in news_dict_format:
            url = news_dict.get('url')
            article_time = cls.parser_article_time(url)
            article_time_ls += [article_time]

        result_news_dict = [{"title": title, "url": link, "source": source, "article_time": article_time} for
                            title, link, source, article_time in zip(total_title, total_link, total_source, article_time_ls)]
        result = [result_news for result_news in result_news_dict if result_news.get('title') not in cls.filter_title_keywords]

        return result


    @classmethod
    def close_browser(cls):
        cls.driver.close()
        cls.driver.quit()

def main():
    LineNewsCrawler.open_browser()
    result = LineNewsCrawler.parserNews()
    LineNewsCrawler.close_browser()
    for news in result:
        print(news)

if __name__ == '__main__':
    main()