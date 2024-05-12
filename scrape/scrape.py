from scrapy import Selector
import requests

url = 'https://slay-the-spire.fandom.com/wiki/Relics'
headers = {}
response = requests.get(url, headers=headers)
selector = Selector(text=response.content.decode())
rows = selector.xpath('//table/tbody/tr')
for row in rows:
    name = row.xpath('td[2]/a/text()').extract_first()
    if name is None:
        continue
    name = name.strip()
    rarity = row.xpath('td[3]/text()').extract_first()
    rarity = rarity.strip()
    description = ''.join(row.xpath('td[4]/text()').extract())
    print(name, rarity)
    print(description.replace(u'\xa0', u' '))
