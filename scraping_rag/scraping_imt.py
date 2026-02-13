import requests
from bs4 import BeautifulSoup
from urllib.parse import urljoin, urlparse

BASE_URL = "https://www.imt.sn"

def get_internal_links():
    response = requests.get(BASE_URL, timeout=10)
    soup = BeautifulSoup(response.text, "html.parser")

    links = set()

    for a in soup.find_all("a", href=True):
        href = a["href"]
        full_url = urljoin(BASE_URL, href)

        # garder seulement les liens du site IMT
        if urlparse(full_url).netloc == urlparse(BASE_URL).netloc:
            links.add(full_url)

    return list(links)


def scrape_page(url):
    response = requests.get(url, timeout=10)
    soup = BeautifulSoup(response.text, "html.parser")

    # supprimer les parties inutiles
    for tag in soup(["script", "style", "nav", "footer", "header"]):
        tag.decompose()

    text = soup.get_text(separator=" ")
    text = " ".join(text.split())

    return text


def scrape_site():
    all_texts = []
    links = get_internal_links()

    print(f"🔍 {len(links)} pages trouvées")

    for link in links:
        try:
            text = scrape_page(link)
            if len(text) > 300:
                all_texts.append(text)
        except Exception as e:
            print(f"❌ Erreur sur {link}")

    return all_texts


if __name__ == "__main__":
    data = scrape_site()
    print(f"✅ Pages scrapées : {len(data)}")

    print(data[0][:500])

