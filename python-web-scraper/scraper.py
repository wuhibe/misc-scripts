import asyncio
import csv
import random
import aiohttp
from bs4 import BeautifulSoup
from googlesearch import search

BROWSERS = (
    "Mozilla/5.0 (Windows NT 6.1) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/41.0.2228.0 Safari/537.36",
    "Mozilla/5.0 (Macintosh; Intel Mac OS X 10_10_1) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/41.0.2227.1 Safari/537.36",
    "Mozilla/5.0 (Windows NT 6.1; WOW64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/41.0.2227.0 Safari/537.36",
    'Mozilla/5.0 (X11; Linux x86_64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/114.0.0.0 Safari/537.3',
)

headers = {'user-agent': random.choice(BROWSERS)}
session = None


async def make_requests(session, urls):
    tasks = []
    for index, url in enumerate(urls):
        await asyncio.sleep(2)
        task = asyncio.ensure_future(fetch_url(session, url, index))
        tasks.append(task)
    await asyncio.gather(*tasks)
    results = [task.result() for task in tasks]
    results.sort(key=lambda x: x[0])
    return results


async def fetch_url(session, url, index):
    try:
        print(f"\tFetching URL: {url}")
        async with session.get(url, timeout=30) as response:
            content = await response.read()
            soup = BeautifulSoup(content, 'html.parser')
            body = soup.find('body')
            if not body:
                return (index, None, None, None, None)
            # Extract the text from the <body> tag and exclude non-text elements
            text = ' '.join(element.string.strip()
                            for element in body.descendants if isinstance(element, str))
            # Count the words
            word_count = len(text.split())

            # Scrape page title
            title = soup.title.text.strip() if soup.title else ''
            if not title:
                og_title = soup.find('meta', property='og:title')
                title = og_title['content'].strip() if og_title else ''

            # Scrape meta description
            meta_description = soup.find('meta', attrs={'name': 'description'})
            meta_description = meta_description['content'].strip(
            ) if meta_description else ''

            # Scrape headings
            headings = ' |X| '.join(str(heading.text.strip()).replace('\n', ' ').replace('\r', ' ').replace('\t', ' ')
                                    for heading in soup.find_all(['h2', 'h3', 'h4']))

            return (index, title, meta_description, headings, word_count)
    except aiohttp.ClientResponseError as e:
        if e.status == 403:
            print(f"**Access Denied Error for URL: {url}**")
        else:
            print(f"**Error fetching URL: {url} - {e}**")
        return (index, None, None, None, None)
    except Exception as e:
        print(f"**Error fetching URL: {url} - {e}**")
        return (index, None, None, None, None)


def initialize():
    header = ['Keyword']
    for i in range(1, 11):
        header.append(f"Website {i}")
    for i in range(1, 5):
        header.append(f"People also ask {i}")
    for i in range(1, 9):
        header.append(f"Related searches {i}")
    for item in ['Title', 'Meta Description', 'Word Count', 'Heading']:
        for i in range(1, 6):
            header.append(f'{item} {i}')
    with open('output.csv', 'w', newline='', encoding='utf-8') as csvfile:
        writer = csv.writer(csvfile)
        writer.writerow(header)


def scrape_organic_results(keyword):
    print('\tGoogle Search: ' + keyword)
    organic_results = []
    domains = []
    try:
        for result in search(keyword, lang="en", stop=60):
            r = result.split('/')[2]
            if r not in domains:
                domains.append(r)
                organic_results.append(result)
            if len(organic_results) == 10:
                return organic_results
    except Exception as e:
        print(f"Read timeout occurred: {e}")
        exit()
    return organic_results


def write_to_csv(keyword, organic_results, people_also_ask, related_searches, details):
    row = [keyword] + organic_results + \
        people_also_ask + related_searches + details
    with open('output.csv', 'a', newline='', encoding='utf-8') as csvfile:
        writer = csv.writer(csvfile)
        writer.writerow(row)


async def scrape_paa_rs(keyword):
    url = f"https://www.google.com/search?q={keyword}&hl=en"
    print('\tPAA & RS: ' + url)
    people_also_ask_data = []
    search_strings = []
    response = None
    tries = 3
    while response is None and tries > 0:
        try:
            response = await session.get(url, headers=headers)
        except Exception:
            tries -= 1
            response = None
            pass
    content = await response.read()
    soup = BeautifulSoup(content, 'html.parser')
    tag = soup.body
    ask_result = soup(text=lambda t: "People also ask" in t.text)
    ask_search_stringsTmp = []
    if len(ask_result) > 0:
        check = 0
        for string in tag.strings:
            if string.strip() == 'People also ask':
                check = 1
            if string.strip() == 'Related searches':
                check = 2
            if string.strip() == 'Next >':
                check = 0
            if check < 1 or string.strip() == '':
                continue

            if check == 2:
                search_strings.append(string.strip())
            if check == 1:
                ask_search_stringsTmp.append(string.strip())
        loop = 0

        try:
            del search_strings[0:len(search_strings)-8]
        except Exception as e:
            pass

        for paask in ask_search_stringsTmp:
            if (loop > 4 or loop == 0):
                loop = loop + 1
                continue
            else:
                loop = loop + 1
                people_also_ask_data.append(paask)
    return (people_also_ask_data, search_strings)


async def main():
    initialize()

    try:
        with open('keywords.txt', 'r') as file:
            keywords = file.read().splitlines()
    except FileNotFoundError:
        print(
            "File not found. Please create a keywords.txt file with one keyword per line.")
        exit()
    global session
    async with aiohttp.ClientSession(headers=headers) as session:
        for keyword in keywords:
            print(f"Scraping {keyword}")

            organic_results = scrape_organic_results(keyword)
            await asyncio.sleep(random.randint(5, 15))
            paas_rss = await scrape_paa_rs(keyword)
            titles = []
            descriptions = []
            headings = []
            word_counts = []

            data = await make_requests(session, organic_results[0:5])
            for result in data:
                index, title, meta_description, heading, word_count = result
                titles.append(title)
                descriptions.append(meta_description)
                headings.append(heading)
                word_counts.append(word_count)

            details = titles + descriptions + word_counts + headings
            write_to_csv(keyword, organic_results,
                         paas_rss[0], paas_rss[1], details)

asyncio.run(main())
