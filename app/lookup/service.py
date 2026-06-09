import os
import uuid
import requests
from urllib.parse import quote_plus
from flask import current_app

try:
    from bs4 import BeautifulSoup
    BS4_AVAILABLE = True
except ImportError:
    BS4_AVAILABLE = False

HEADERS = {
    'User-Agent': (
        'Mozilla/5.0 (Windows NT 10.0; Win64; x64) '
        'AppleWebKit/537.36 (KHTML, like Gecko) '
        'Chrome/120.0.0.0 Safari/537.36'
    ),
    'Accept-Language': 'en-US,en;q=0.9',
}


def _scrape_homedepot(query):
    """Scrape Home Depot search for first result."""
    try:
        url = f"https://www.homedepot.com/s/{quote_plus(query)}"
        resp = requests.get(url, headers=HEADERS, timeout=8)
        if resp.status_code != 200:
            return None
        soup = BeautifulSoup(resp.text, 'html.parser')

        # Try to find product card
        card = soup.select_one('[data-testid="product-header"]')
        if not card:
            card = soup.select_one('.product-header')
        if not card:
            # Try JSON-LD
            import json
            scripts = soup.find_all('script', type='application/ld+json')
            for s in scripts:
                try:
                    data = json.loads(s.string)
                    if isinstance(data, list):
                        data = data[0]
                    if data.get('@type') in ('Product', 'ItemList'):
                        items = data.get('itemListElement', [data])
                        item = items[0] if items else data
                        product = item.get('item', item)
                        return {
                            'name': product.get('name'),
                            'brand': (product.get('brand') or {}).get('name') if isinstance(product.get('brand'), dict) else product.get('brand'),
                            'model_number': product.get('model'),
                            'image_url': (product.get('image') or [None])[0] if isinstance(product.get('image'), list) else product.get('image'),
                            'retailer_url': product.get('url') or url,
                            'source': 'homedepot',
                        }
                except Exception:
                    pass

        # Fallback: parse product title
        title_el = soup.select_one('h2.product-title, .product-header__title, [data-testid="product-title"]')
        if title_el:
            return {
                'name': title_el.get_text(strip=True),
                'brand': None,
                'model_number': None,
                'image_url': None,
                'retailer_url': url,
                'source': 'homedepot',
            }
    except Exception:
        pass
    return None


def _scrape_lowes(query):
    """Scrape Lowes search for first result."""
    try:
        url = f"https://www.lowes.com/search?searchTerm={quote_plus(query)}"
        resp = requests.get(url, headers=HEADERS, timeout=8)
        if resp.status_code != 200:
            return None
        soup = BeautifulSoup(resp.text, 'html.parser')

        import json
        scripts = soup.find_all('script', type='application/ld+json')
        for s in scripts:
            try:
                data = json.loads(s.string)
                if isinstance(data, list):
                    data = data[0]
                if data.get('@type') in ('Product', 'ItemList'):
                    items = data.get('itemListElement', [data])
                    item = items[0] if items else data
                    product = item.get('item', item)
                    return {
                        'name': product.get('name'),
                        'brand': (product.get('brand') or {}).get('name') if isinstance(product.get('brand'), dict) else product.get('brand'),
                        'model_number': product.get('model'),
                        'image_url': (product.get('image') or [None])[0] if isinstance(product.get('image'), list) else product.get('image'),
                        'retailer_url': product.get('url') or url,
                        'source': 'lowes',
                    }
            except Exception:
                pass

        title_el = soup.select_one('.art-pd-title, [data-testid="product-title"], h2.sc-bdnxRM')
        if title_el:
            return {
                'name': title_el.get_text(strip=True),
                'brand': None,
                'model_number': None,
                'image_url': None,
                'retailer_url': url,
                'source': 'lowes',
            }
    except Exception:
        pass
    return None


def search_product(query, source='auto'):
    """Search retailer sites for product info. Returns dict or None."""
    if not BS4_AVAILABLE:
        return None

    if source in ('auto', 'homedepot'):
        result = _scrape_homedepot(query)
        if result:
            return result

    if source in ('auto', 'lowes'):
        result = _scrape_lowes(query)
        if result:
            return result

    return None


def fetch_product_image(image_url, user_id):
    """Download image from URL, save locally. Returns filename or None."""
    try:
        from PIL import Image
        import io

        resp = requests.get(image_url, headers=HEADERS, timeout=10, stream=True)
        if resp.status_code != 200:
            return None

        img = Image.open(io.BytesIO(resp.content))
        img = img.convert('RGB')
        img.thumbnail((800, 800), Image.LANCZOS)

        filename = f"{uuid.uuid4().hex}.jpg"
        user_dir = os.path.join(current_app.root_path, 'static', 'uploads', str(user_id))
        os.makedirs(user_dir, exist_ok=True)
        filepath = os.path.join(user_dir, filename)
        img.save(filepath, 'JPEG', quality=85)
        return f"{user_id}/{filename}"
    except Exception:
        return None
