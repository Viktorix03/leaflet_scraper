import requests
import json
from bs4 import BeautifulSoup
from datetime import datetime
from dataclasses import dataclass

# Základné štruktúra pre leták
@dataclass
class Leaflet:
    title: str
    thumbnail: str
    shop_name: str
    valid_from: str
    valid_to: str
    parsed_time: str

class LeafletScraper:
    TARGET_URL = "https://www.prospektmaschine.de/hypermarkte/"

    def __init__(self):
        # Pre viac performant requests z URL (zachová sa TCP connection)
        self.session = requests.Session()

    def fetch_page(self):
        """Získa HTML obsah stránky."""
        response = self.session.get(self.TARGET_URL)
        response.raise_for_status()
        return response.text

    def parse_leaflets(self, content: str):
        """Parsuje letáky ako zoznam štrukturovaných dát."""
        soup = BeautifulSoup(content, "html.parser")
        leaflets = []
        # Prechádzanie všetkých letákov s classou "brochure-thumb" nachádzajúce sa v classe "letaky-grid"
        for container in soup.select(".letaky-grid .brochure-thumb"):
            desc = container.select_one(".letak-description")
            img_tag = container.select_one(".img-container img")

            if not desc or not img_tag:
                continue  # Ak chýbajú dáta, pokračujeme ďalej

            title_element = desc.select_one("p.grid-item-content strong")
            date_element = desc.select("p.grid-item-content small")
            logo_element = desc.select_one(".grid-logo img")

            if not title_element or not date_element or not logo_element:
                continue

            title = title_element.text.strip()
            shop_name = logo_element.get("alt", "").replace("Logo ", "").strip()

            # Spracovanie thumbnail obrázku
            thumbnail = img_tag.get("src", "").strip()
            if not thumbnail:
                thumbnail = img_tag.get("data-src", "").strip()  # Lazy-load obrázky

            # Spracovanie dátumov
            date_text = date_element[0].text.strip()
            try:
                valid_from, valid_to = date_text.split(" - ")
                valid_from = self.format_date(valid_from)
                valid_to = self.format_date(valid_to)
            except ValueError:
                continue
            

            # Uloženie dát do zoznamu 'leaflets' použítim dataclass Leaflet
            leaflets.append(Leaflet(
                title=title,
                thumbnail=thumbnail,
                shop_name=shop_name,
                valid_from=valid_from,
                valid_to=valid_to,
                parsed_time=datetime.now().strftime("%Y-%m-%d %H:%M:%S")
            ))

        return leaflets

    def format_date(self, date_str: str):
        """Prevedie dátum do formátu YYYY-MM-DD."""
        formats = ["%d.%m.%Y", "%d.%m.%y"]
        for fmt in formats:
            try:
                return datetime.strptime(date_str, fmt).strftime("%Y-%m-%d")
            except ValueError:
                pass
        return None  # Ak dátum nie je v očakávanom formáte

    def save_to_json(self, data: list[Leaflet], filename="leaflets.json"):
        """Uloží dáta do JSON súboru."""
        with open(filename, "w", encoding="utf-8") as f:
            json.dump([leaflet.__dict__ for leaflet in data], f, indent=4, ensure_ascii=False)
        return filename

    def run(self):
        """Spustí scraping a parsovanie."""
        html = self.fetch_page()
        leaflets = self.parse_leaflets(html)
        file = self.save_to_json(leaflets)
        print(f"Uložených {len(leaflets)} letákov do '{file}'")


if __name__ == "__main__":
    scraper = LeafletScraper()
    scraper.run()
