from __future__ import annotations

import json
import re
import unicodedata
from dataclasses import dataclass
from enum import Enum

from bs4 import BeautifulSoup


class StockStatus(str, Enum):
    IN_STOCK = "in_stock"
    OUT_OF_STOCK = "out_of_stock"
    UNKNOWN = "unknown"


@dataclass(frozen=True)
class ProductSnapshot:
    url: str
    status: StockStatus
    title: str | None = None


IN_STOCK_SCHEMA_VALUES = {
    "http://schema.org/instock",
    "https://schema.org/instock",
    "instock",
    "in_stock",
}

OUT_OF_STOCK_SCHEMA_VALUES = {
    "http://schema.org/outofstock",
    "https://schema.org/outofstock",
    "outofstock",
    "out_of_stock",
    "soldout",
    "sold_out",
}

OUT_OF_STOCK_TEXT_PATTERNS = [
    r"\bstokta\s+yok\b",
    r"\btukendi\b",
    r"\bmevcut\s+degil\b",
    r"\bout\s+of\s+stock\b",
    r"\bsold\s+out\b",
    r"\bnot\s+available\b",
]

IN_STOCK_TEXT_PATTERNS = [
    r"\bsepete\s+ekle\b",
    r"\bsepet(?:e)?\s+ekleyin\b",
    r"\badd\s+to\s+(?:bag|cart|basket)\b",
]


def detect_stock_status(html: str) -> StockStatus:
    soup = BeautifulSoup(html, "html.parser")

    schema_status = _status_from_json_ld(soup)
    if schema_status == StockStatus.IN_STOCK:
        return StockStatus.IN_STOCK

    if _has_in_stock_control(soup):
        return StockStatus.IN_STOCK

    text = _normalized_text(soup.get_text(" ", strip=True))
    if _matches_any(text, IN_STOCK_TEXT_PATTERNS):
        return StockStatus.IN_STOCK

    if schema_status == StockStatus.OUT_OF_STOCK:
        return StockStatus.OUT_OF_STOCK
    if _matches_any(text, OUT_OF_STOCK_TEXT_PATTERNS):
        return StockStatus.OUT_OF_STOCK

    return StockStatus.UNKNOWN


def extract_title(html: str) -> str | None:
    soup = BeautifulSoup(html, "html.parser")

    for selector in ('meta[property="og:title"]', 'meta[name="twitter:title"]'):
        tag = soup.select_one(selector)
        if tag and tag.get("content"):
            return tag["content"].strip()

    if soup.title and soup.title.string:
        return soup.title.string.strip()

    heading = soup.find(["h1", "h2"])
    if heading:
        return heading.get_text(" ", strip=True)

    return None


def _has_in_stock_control(soup: BeautifulSoup) -> bool:
    labels = []
    for tag in soup.find_all(["button", "a"]):
        labels.append(tag.get_text(" ", strip=True))
        for attr in ("aria-label", "title"):
            value = tag.get(attr)
            if value:
                labels.append(str(value))

    for label in labels:
        normalized = _normalized_text(label)
        if normalized in {"ekle", "sepete ekle", "sepete ekleyin", "add to bag", "add to cart", "add to basket"}:
            return True
        if _matches_any(normalized, IN_STOCK_TEXT_PATTERNS):
            return True

    return False


def _status_from_json_ld(soup: BeautifulSoup) -> StockStatus:
    for script in soup.find_all("script", attrs={"type": "application/ld+json"}):
        raw = script.string or script.get_text()
        if not raw:
            continue
        try:
            data = json.loads(raw)
        except json.JSONDecodeError:
            continue

        status = _walk_for_availability(data)
        if status != StockStatus.UNKNOWN:
            return status

    return StockStatus.UNKNOWN


def _walk_for_availability(value: object) -> StockStatus:
    if isinstance(value, dict):
        availability = value.get("availability")
        if availability:
            return _availability_to_status(str(availability))
        for child in value.values():
            status = _walk_for_availability(child)
            if status != StockStatus.UNKNOWN:
                return status
    elif isinstance(value, list):
        for child in value:
            status = _walk_for_availability(child)
            if status != StockStatus.UNKNOWN:
                return status

    return StockStatus.UNKNOWN


def _availability_to_status(value: str) -> StockStatus:
    normalized = value.strip().lower()
    if normalized in IN_STOCK_SCHEMA_VALUES:
        return StockStatus.IN_STOCK
    if normalized in OUT_OF_STOCK_SCHEMA_VALUES:
        return StockStatus.OUT_OF_STOCK
    return StockStatus.UNKNOWN


def _normalized_text(text: str) -> str:
    text = text.replace("ı", "i").replace("İ", "I")
    without_marks = "".join(
        char for char in unicodedata.normalize("NFKD", text) if not unicodedata.combining(char)
    )
    return re.sub(r"\s+", " ", without_marks.lower())


def _matches_any(text: str, patterns: list[str]) -> bool:
    return any(re.search(pattern, text) for pattern in patterns)
