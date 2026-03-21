import httpx
import feedparser
import os
from typing import List
from dataclasses import dataclass


@dataclass
class Article:
    title: str
    summary: str
    url: str
    authors: List[str]
    domain: str


DOMAIN_QUERIES = {
    "machine_learning": "cat:cs.LG",
    "computer_vision": "cat:cs.CV",
    "nlp": "cat:cs.CL",
    "robotics": "cat:cs.RO",
    "ai_general": "cat:cs.AI",
}

ARXIV_BASE_URL = "https://export.arxiv.org/api/query"


def fetch_arxiv_articles(domain: str = "machine_learning", max_results: int = 5) -> List[Article]:
    query = DOMAIN_QUERIES.get(domain, DOMAIN_QUERIES["machine_learning"])
    params = {
        "search_query": query,
        "sortBy": "submittedDate",
        "sortOrder": "descending",
        "max_results": max_results,
    }

    response = httpx.get(ARXIV_BASE_URL, params=params, timeout=30)
    response.raise_for_status()

    feed = feedparser.parse(response.text)
    articles = []

    for entry in feed.entries:
        article = Article(
            title=entry.title.replace("\n", " ").strip(),
            summary=entry.summary.replace("\n", " ").strip(),
            url=entry.link,
            authors=[a.name for a in entry.get("authors", [])],
            domain=domain,
        )
        articles.append(article)

    return articles


def fetch_all_domains(max_per_domain: int = 2) -> List[Article]:
    all_articles = []
    for domain in DOMAIN_QUERIES:
        try:
            articles = fetch_arxiv_articles(domain=domain, max_results=max_per_domain)
            all_articles.extend(articles)
        except Exception as e:
            print(f"Failed to fetch domain {domain}: {e}")
    return all_articles
