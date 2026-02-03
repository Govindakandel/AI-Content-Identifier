import scrapy
import re
import unicodedata
import json
import random


urls_data = json.load(open("wiki_start_urls.json"))

def clean_text(text):
    # Remove citations like [1], [2]
    text = re.sub(r'\[.*?\]', '', text)
    # Remove "citation needed"
    text = re.sub(r'\(citation needed\)', '', text, flags=re.IGNORECASE)
    # Remove extra whitespace/newlines
    text = re.sub(r'\s+', ' ', text)
    # Normalize unicode characters
    text = unicodedata.normalize('NFKC', text)
    return text.strip()

class WikiDatasetSpider(scrapy.Spider):
    name = "wiki"
    allowed_domains = ["wikipedia.org"]

    MAX_PARAGRAPHS_PER_PAGE = 4
    MIN_CHARS = 120

    custom_settings = {
        "DOWNLOAD_DELAY": 1.0,  # 1 second delay between requests
        "AUTOTHROTTLE_ENABLED": True,
        "AUTOTHROTTLE_START_DELAY": 1.0,
        "AUTOTHROTTLE_MAX_DELAY": 3.0,
        "AUTOTHROTTLE_TARGET_CONCURRENCY": 1.0
    }

    def start_requests(self):
        for url in urls_data:
           yield scrapy.Request(url=url, callback=self.parse)

    def parse(self, response):
        paragraphs = response.css("div.mw-parser-output p")
        cleaned_paragraphs = []
        topic = response.url.split("/wiki/")[-1]
        categories_on_page = response.css("#mw-normal-catlinks ul li a::text").getall()

        # Clean and filter paragraphs
        for p in paragraphs:
            raw = p.xpath("string(.)").get()
            text = clean_text(raw)
            if len(text) >= self.MIN_CHARS and "may refer to" not in text.lower():
                cleaned_paragraphs.append(text)

        # Randomly pick MAX_PARAGRAPHS_PER_PAGE paragraphs
        selected_paragraphs = random.sample(
            cleaned_paragraphs,
            min(self.MAX_PARAGRAPHS_PER_PAGE, len(cleaned_paragraphs))
        )

        for text in selected_paragraphs:
            yield {
                "text": text,
                "label": "human",
                "source": "wikipedia",
                "url": response.url,
                "topic": topic,
                "categories_on_page": categories_on_page
            }

        self.logger.info(f"Scraped {len(selected_paragraphs)} paragraphs from {response.url}")
