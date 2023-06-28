import asyncio
import csv
import random
import aiohttp
from bs4 import BeautifulSoup
from googlesearch import search
from urllib.parse import unquote, urlparse, parse_qs

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


def clean_str(s: str):
    return s.strip().replace('\n', ' ').replace('\r', ' ').replace('\t', ' ')


def get_youtube_links(content):
    soup = BeautifulSoup(content, 'html.parser')
    youtube_links = []
    for link in soup.find_all("a"):
        if len(youtube_links) == 3:
            break
        try:
            href = link.get("href")
            href = unquote(href)  # Decode the URL
            parsed_url = urlparse(href)
            query_params = parse_qs(parsed_url.query)
            href = query_params.get('url')
            if href:
                href = href[0]
            if href and "youtube.com" in href and "watch?v=" in href and href not in youtube_links:
                youtube_links.append(href)
        except Exception:
            pass
    yt_links = youtube_links[:3]
    while len(yt_links) < 3:
        yt_links.append('-')
    return yt_links


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
            text = ' '.join(clean_str(element.string)
                            for element in body.descendants if isinstance(element, str))
            # Count the words
            word_count = len(text.split())

            # Scrape page title
            title = clean_str(soup.title.text) if soup.title else ''
            if not title:
                og_title = soup.find('meta', property='og:title')
                title = clean_str(og_title['content']) if og_title else ''

            # Scrape meta description
            meta_description = soup.find('meta', attrs={'name': 'description'})
            meta_description = clean_str(
                meta_description['content']) if meta_description else ''

            # Scrape headings
            headings = ' |X| '.join(clean_str(heading.text)
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
    for i in range(1, 4):
        header.append(f'Youtube Link {i}')
    with open('output.csv', 'w', newline='', encoding='utf-8') as csvfile:
        writer = csv.writer(csvfile)
        writer.writerow(header)


def is_not_image(url):
    filetypes = ['jpg', 'jpeg', 'png', 'gif']
    return not any([x in url for x in filetypes])


def scrape_organic_results(keyword):
    print('\tGoogle Search: ' + keyword)
    organic_results = []
    domains = []
    try:
        for result in search(keyword, lang="en", stop=60):
            r = result.split('/')[2]
            if r not in domains and 'youtube.com' not in result and is_not_image(result):
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
    youtube_links = get_youtube_links(content)
    tag = soup.body
    ask_result = soup(text=lambda t: 'People also ask' in t.text)
    rss = soup(text=lambda t: 'Related searches' in t.text)
    ask_search_stringsTmp = []
    if len(ask_result) > 0 or len(rss) > 0:
        check = 0
        for string in tag.strings:
            if clean_str(string) == 'People also ask':
                check = 1
            if clean_str(string) == 'Related searches':
                check = 2
            if clean_str(string) == 'Next >':
                check = 0
            if check < 1 or clean_str(string) == '':
                continue

            if check == 2:
                search_strings.append(clean_str(string))
            if check == 1:
                ask_search_stringsTmp.append(clean_str(string))
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

    while len(people_also_ask_data) < 4:
        people_also_ask_data.append(None)
    while len(search_strings) < 8:
        search_strings.append(None)
    return (people_also_ask_data, search_strings, youtube_links)


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
            await asyncio.sleep(random.randint(7, 22))
            paas, rss, yt_links = await scrape_paa_rs(keyword)
            await asyncio.sleep(random.randint(10, 20))
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

            details = titles + descriptions + word_counts + headings + yt_links
            write_to_csv(keyword, organic_results,
                         paas, rss, details)

asyncio.run(main())
