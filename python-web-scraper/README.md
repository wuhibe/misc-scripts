# Web Scraper - Google Keyword Search

This Python web scraper is designed to read keywords from a `keywords.txt` file, iterate through each word, and search it on Google. It then collects the top 10 websites with distinct domains, along with 4 "People Also Ask" questions and 8 related searches for that word. Finally, it scrapes the first 5 websites for each search term and retrieves their title, meta description, word count, and headers.

## Prerequisites

Before running the web scraper, ensure that you have the following prerequisites installed:

* Python 3.11
* pip 23.0.1

You can install Python and pip from the official Python website: [python.org](https://www.python.org/downloads/)
> **Note**
> While the script may work with other versions of Python and pip, it has not been tested and may not work as it was intended.

To install the required dependencies, run the following command:

```bash
pip install -r requirements.txt
```

## Usage

Clone this repository or download the source code files.

Create a text file named `keywords.txt` and add one keyword per line.

* I have added an example file. You can modify it for your use-case.

Run the `scraper.py` script using the following command:

```bash
python3 scraper.py
```

The scraper will read each keyword from `keywords.txt` and perform a Google search for it.

For each keyword, the scraper will collect the top 10 websites with distinct domains, 4 "People Also Ask" questions, and 8 related searches.

Next, it will scrape the first 5 websites for each search term and retrieve their title, meta description, word count, and headers.

The scraped data will be stored in separate CSV files for each keyword, following the specified output format.

## Output

The scraped data will be saved in CSV files named `output.csv` in the same directory.

## Disclaimer

Please note that web scraping Google's search results may potentially violate Google's terms of service. Use this web scraper responsibly and ensure that your scraping activities comply with applicable laws and regulations. The author of this scraper is not responsible for any misuse or violation of terms.

## License

This project is licensed under the MIT License. See the LICENSE file in the root repository for more.
