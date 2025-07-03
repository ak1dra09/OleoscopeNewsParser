from dataclasses import dataclass
from datetime import date, datetime
from typing import List
import requests
from bs4 import BeautifulSoup
import os


@dataclass
class NewsDTO:
    source_name: str = None
    source_url: str = None

    title: str = None
    public_date: date = None
    content: str = None
    tags: List[str] = None
    author: str = None
    external_id: str = None


class OleoscopeNewsParser:
    BASE_URL = 'https://oleoscope.com/news'
    SOURCE_NAME = 'Oleoscope'

    def parse_news_page(self, html: str, target_date: date) -> List[NewsDTO]:
        soup = BeautifulSoup(html, 'html.parser')
        news_items = soup.find_all('div', class_='archive-list__item')

        result = []
        for item in news_items:
            try:
                date_str = item.find('div', class_='card-small__date').text.strip()
                news_date = datetime.strptime(date_str, '%d.%m.%Y').date()

                if news_date != target_date:
                    continue

                title = item.find('a', class_="card-small__title").text.strip()
                source_url = item.find('a')['href']
                soup2 = BeautifulSoup(source_url, 'html.parser')
                content = soup2.find('div', class_='details__content content').text.strip()

                external_id = source_url.split('/')[-1]

                news_dto = NewsDTO(
                    source_name=self.SOURCE_NAME,
                    source_url=source_url,
                    title=title,
                    public_date=news_date,
                    content=content,
                    tags=self.parse_tags(item),
                    author=self.parse_author(content),
                    external_id=external_id
                )
                result.append(news_dto)
            except Exception as e:
                print(f"Ошибка при парсинге новости: {e}")
                continue

        return result

    def parse_tags(self, item) -> List[str]:
        tags = []
        tags_block = item.find('a', class_='card-small__tags')
        if tags_block:
            for tag in tags_block.find_all('li'):
                tags = tag.text.strip()
        return tags

    def parse_author(self, item) -> str:
        author_block = item.find('a')
        if author_block:
            return author_block.text.strip()
        else:
            return "None"

    def get_data(self, url: str, request_params: dict | None = None) -> str | None:
        user = requests.UserAgent().random
        request_params = request_params or {}
        headers = {
            'User-Agent': user,
            'Accept': 'text/html,application/xhtml+xml,application/xml;q=0.9,'
                      'image/avif,image/webp,*/*;q=0.8',
            'Accept-Language': 'ru-RU,ru;q=0.8,en-US;q=0.5,en;q=0.3',
        }
        html = requests.get(url, headers=headers, **request_params)
        if html.ok:
            return html.text
        else:
            message = f'ENVIRONMENT: {os.getenv("ENVIRONMENT")}\n'
            message += f'Ошибка парсера {self.__class__.__name__}\n'
            message += f'Код ошибки: {html.status_code}'
#            send_tg_parsers_notification(message=message)

    def parse(self, parse_date: date) -> List[NewsDTO]:
        url = self.BASE_URL
        html_data = self.get_data(url=url)

        if not html_data:
            return []
        return self.parse_news_page(html=html_data, target_date=parse_date)
