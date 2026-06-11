#!/usr/bin/env python3
import json
import re
import time
import urllib.error
import textwrap
import urllib.parse
import urllib.request
from html import escape
from pathlib import Path

from PIL import Image, ImageOps


ROOT = Path(__file__).resolve().parents[1]
IMG_DIR = ROOT / "assets" / "images"
DATA_DIR = ROOT / "data"
TMP_DIR = ROOT / "assets" / "download-cache"
CACHE_FILE = TMP_DIR / "commons_lookup_cache.json"
PHOTO_REPLACEMENTS_FILE = DATA_DIR / "photo_replacements.json"
UA = "montimar-visual-menu/1.0 (local research)"


MENU_SOURCE = "https://www.montimar.nl/menukaart/"


OFFICIAL_IMAGES = {
    "Carpaccio": {
        "source_url": "https://www.montimar.nl/wp-content/uploads/2019/01/10.jpg",
        "local": ROOT / "assets" / "source" / "montimar" / "10.jpg",
        "title": "Montimar official beef carpaccio photo",
        "credit": "Montimar Restaurant",
        "license": "Restaurant website photo",
    },
    "Gambas Pil Pil": {
        "source_url": "https://www.montimar.nl//wp-content/uploads/2019/01/33.jpg",
        "local": ROOT / "assets" / "source" / "montimar" / "33.jpg",
        "title": "Montimar official shrimp dish photo",
        "credit": "Montimar Restaurant",
        "license": "Restaurant website photo",
    },
    "Risotto": {
        "source_url": "https://www.montimar.nl/wp-content/uploads/2019/11/81.jpg",
        "local": ROOT / "assets" / "source" / "montimar" / "81.jpg",
        "title": "Montimar official plated vegetarian dish photo",
        "credit": "Montimar Restaurant",
        "license": "Restaurant website photo",
    },
    "Semifreddo": {
        "source_url": "https://www.montimar.nl/wp-content/uploads/2023/07/25.jpg",
        "local": ROOT / "assets" / "source" / "montimar" / "25.jpg",
        "title": "Montimar official dessert-style plated dish photo",
        "credit": "Montimar Restaurant",
        "license": "Restaurant website photo",
    },
    "Vacherin": {
        "source_url": "https://www.montimar.nl/wp-content/uploads/2022/04/44.jpg",
        "local": ROOT / "assets" / "source" / "montimar" / "44.jpg",
        "title": "Montimar official ice cream dessert photo",
        "credit": "Montimar Restaurant",
        "license": "Restaurant website photo",
    },
    "Sopa de Basque": {
        "source_url": "https://www.montimar.nl//wp-content/uploads/2019/01/33.jpg",
        "local": ROOT / "assets" / "source" / "montimar" / "33.jpg",
        "title": "Montimar official seafood skillet photo",
        "credit": "Montimar Restaurant",
        "license": "Restaurant website photo",
    },
}


FILE_IMAGE_OVERRIDES = {
    "asian-grilled-chicken": "Chicken teriyaki, Fried chicken, Krasnoyarsk, Russia.jpg",
    "bread-and-herb-butter": "Bread and butter, Hechtsheim.jpg",
    "cod-bourride": "Dorschfilet Gemüse Rostock.jpg",
    "cheese-selection": "Cheese Platter.jpg",
    "dame-blanche": "Dame Blanche, Le 13, 2026.jpg",
    "mixed-tapas-tasting": "Tapas bar a Madrid (6267019130).jpg",
    "provencal-tomato-soup": "Basil and Organic Tomato Soup.jpg",
    "sea-bream-and-shrimp": "14-05-2017 Sea bream on a barbeque, Albufeira.JPG",
    "serrano-ham-and-melon": "Prosciutto con melone IMGP0936.jpg",
    "small-fried-white-fish": "Plate of fish and chips.jpg",
    "tomato-soup": "Basil and Organic Tomato Soup.jpg",
    "white-asparagus-with-ham-and-egg": "Asparagus NL.jpg",
}


FALLBACK_QUERIES = {
    "tuna tartare taco avocado": ["tuna tartare", "tuna taco"],
    "tempura chicken salad mango": ["chicken tempura", "fried chicken salad"],
    "tapas platter shrimp smoked salmon": ["tapas platter", "spanish tapas"],
    "sushi rice bowl asparagus avocado edamame": ["sushi bowl", "chirashi sushi"],
    "grilled vegetable salad parmesan": ["grilled vegetables", "vegetable salad"],
    "smoked salmon fennel salad": ["smoked salmon salad", "smoked salmon"],
    "white asparagus ham egg hollandaise": ["white asparagus ham", "asparagus hollandaise"],
    "grilled chicken soy sesame dumplings": ["grilled chicken", "chicken dumplings"],
    "lamb steak serrano ham aubergine": ["lamb steak", "lamb chop"],
    "steak shrimp bearnaise": ["surf and turf", "steak shrimp"],
    "pork tenderloin serrano ham sauce": ["pork tenderloin", "pork medallions"],
    "steak bordelaise red wine sauce": ["steak red wine sauce", "grilled steak"],
    "beef tenderloin pepper sauce": ["filet mignon pepper sauce", "beef tenderloin"],
    "plaice fillet capers lemon": ["plaice fillet", "fried fish fillet"],
    "cod fennel white wine sauce": ["cod fillet", "cod fish dish"],
    "black tiger shrimp garlic chili": ["garlic shrimp", "shrimp scampi"],
    "sea bream shrimp saffron sauce": ["sea bream", "dorade fish"],
    "cannelloni vegetables tomato sauce": ["cannelloni", "vegetable cannelloni"],
    "asparagus risotto peas parmesan": ["asparagus risotto", "risotto"],
    "semifreddo mascarpone red fruit": ["semifreddo dessert", "mascarpone dessert"],
    "vacherin strawberries meringue ice cream": ["vacherin dessert", "strawberry meringue ice cream"],
    "dame blanche ice cream chocolate sauce": ["dame blanche", "ice cream chocolate sauce"],
    "passion fruit cheesecake oreo crumble": ["passion fruit cheesecake", "cheesecake"],
    "serrano ham melon": ["prosciutto melon", "ham melon"],
    "shrimp skewer salad aioli": ["shrimp skewer", "grilled shrimp skewer"],
    "fried white fish fries": ["fish and chips", "fried fish fries"],
    "chicken breast fries salad": ["chicken and fries", "grilled chicken fries"],
    "frikandel fries": ["frikandel", "sausage and fries"],
    "steak fries": ["steak frites", "steak and fries"],
    "vanilla ice cream whipped cream sprinkles": ["vanilla ice cream", "ice cream sundae"],
    "liqueur coffee whipped cream": ["liqueur coffee", "coffee whipped cream"],
    "spanish coffee licor 43": ["spanish coffee", "liqueur coffee"],
    "french coffee grand marnier": ["french coffee", "liqueur coffee"],
}


GENERIC_CATEGORY_QUERIES = {
    "Starters": ["mediterranean appetizer", "restaurant appetizer"],
    "Soups": ["soup bowl", "restaurant soup"],
    "Meat": ["grilled meat dish", "restaurant steak"],
    "Fish": ["fish dish", "seafood dish"],
    "Vegetarian": ["vegetarian dish", "vegetable pasta"],
    "Desserts": ["restaurant dessert", "ice cream dessert"],
    "Kids": ["kids meal", "fries plate"],
    "Coffee": ["coffee cocktail", "coffee with whipped cream"],
}


MENU = [
    {
        "category": "Starters",
        "items": [
            ("Bread & herb butter", "Brood & boter pp", "1.20", "Fresh baked roll with herb butter", "fresh bread herb butter"),
            ("Beef carpaccio", "Carpaccio", "8.95", "Thin-sliced beef fillet with truffle mayonnaise, pine nuts, arugula and Parmesan", "beef carpaccio arugula parmesan"),
            ("Garlic shrimp pil pil", "Gambas Pil Pil", "8.25", "Sizzling shrimp in garlic-pepper oil, served with aioli and lemon", "gambas pil pil garlic shrimp"),
            ("Crispy tuna tacos", "Taco de atun", "7.25", "Crispy tacos with avocado cream and soy-marinated tuna tartare", "tuna tartare taco avocado"),
            ("Tempura chicken salad", "Pollo Crujiente", "7.45", "Tempura chicken thigh salad with mango chutney, yogurt dressing and pickled cucumber and carrot", "tempura chicken salad mango"),
            ("Escargots in garlic butter", "Escargots", "8.55", "Eight vineyard snails in herb butter and garlic, served with bread", "escargots garlic butter"),
            ("Mixed tapas tasting", "Tapas variadas", "6.85", "Small tasting of asparagus soup, shrimp pil pil and smoked salmon with fennel salad", "tapas platter shrimp smoked salmon"),
            ("Spring sushi rice bowl", "Primavera", "6.45", "Marinated sushi rice with roasted asparagus, avocado, pickled cucumber and carrot, edamame and paprika mayonnaise", "sushi rice bowl asparagus avocado edamame"),
            ("Provencal grilled vegetable salad", "Provencal", "7.15", "Salad of grilled Provencal vegetables, Parmesan, pistou and tomato salsa", "grilled vegetable salad parmesan"),
            ("Smoked salmon and fennel", "De la costa", "7.95", "Smoked salmon fillet with fresh fennel salad and citrus mayonnaise", "smoked salmon fennel salad"),
            ("White asparagus with ham and egg", "Asperges", "7.75", "White asparagus with farmhouse ham, farm egg and hollandaise sauce; vegetarian option available", "white asparagus ham egg hollandaise"),
        ],
    },
    {
        "category": "Soups",
        "items": [
            ("Provencal tomato soup", "Provencaalse tomaat", "3.15", "Hearty vine tomato soup with basil and cream", "tomato soup basil cream"),
            ("Creamy asparagus soup", "Aspergesoep", "4.55", "Creamy asparagus soup in the Brabant style", "cream asparagus soup"),
            ("Basque seafood soup", "Sopa de Basque", "7.15", "Northern Spanish fish soup with fish fillets, shellfish and crustaceans", "basque seafood soup fish shellfish"),
        ],
    },
    {
        "category": "Meat",
        "items": [
            ("Asian grilled chicken", "Pollo Asiatico", "14.20", "Grilled chicken breast with crispy chicken dumplings and soy, sesame and chili sauce", "grilled chicken soy sesame dumplings"),
            ("Lamb duo", "Cordero", "18.95", "Pan-fried lamb entrecote with lamb mince roll, serrano ham and aubergine, served with lamb jus", "lamb steak serrano ham aubergine"),
            ("Steak and shrimp", "Mont i Mar", "18.80", "Black Angus steak with shrimp and bearnaise sauce", "steak shrimp bearnaise"),
            ("Pork tenderloin with serrano", "Iberico", "14.35", "Roasted pork tenderloin with serrano ham and honey-thyme sauce", "pork tenderloin serrano ham sauce"),
            ("Black Angus rump steak Bordelaise", "Steak Bordelaise", "18.95", "Grilled Black Angus rump steak with red wine sauce", "steak bordelaise red wine sauce"),
            ("Tenderloin with pepper sauce", "Tournedos", "24.45", "Pan-fried beef tenderloin with pepper sauce", "beef tenderloin pepper sauce"),
        ],
    },
    {
        "category": "Fish",
        "items": [
            ("Pan-fried plaice", "El Mar", "16.40", "Fried plaice fillet with browned butter, capers and lemon sauce", "plaice fillet capers lemon"),
            ("Salmon with beurre blanc", "Salmon", "17.40", "Skin-on fried salmon fillet with beurre blanc sauce and herb oil", "salmon beurre blanc"),
            ("Cod bourride", "Cabillaud Bourride", "16.95", "Pan-fried cod fillet with white wine, fennel and tarragon sauce", "cod fennel white wine sauce"),
            ("Wok-fried black tiger shrimp", "Gamba's", "15.95", "Peeled black tiger shrimp wok-fried with garlic, pepper and soy-sesame marinade, served with chili mayonnaise", "black tiger shrimp garlic chili"),
            ("Sea bream and shrimp", "Dorade y Gamba", "16.25", "Pan-fried sea bream fillet with shrimp and saffron-orange sauce", "sea bream shrimp saffron sauce"),
        ],
    },
    {
        "category": "Vegetarian",
        "items": [
            ("Baked cannelloni", "Pasta di mama", "15.95", "Oven-baked cannelloni filled with Provencal vegetables and tomato sauce", "cannelloni vegetables tomato sauce"),
            ("Asparagus risotto", "Risotto", "12.95", "Creamy risotto with asparagus, peas, vine tomato, arugula and Parmesan", "asparagus risotto peas parmesan"),
        ],
    },
    {
        "category": "Desserts",
        "items": [
            ("Mascarpone semifreddo", "Semifreddo", "4.85", "Light mascarpone ice cream with red-fruit compote and yogurt foam", "semifreddo mascarpone red fruit"),
            ("Vacherin with strawberries", "Vacherin", "5.45", "Vanilla ice cream, strawberries, meringue and whipped cream", "vacherin strawberries meringue ice cream"),
            ("Dame Blanche", "Dame Blanche", "5.60", "Vanilla ice cream with whipped cream and warm chocolate sauce", "dame blanche ice cream chocolate sauce"),
            ("Lemon-passionfruit cheesecake", "Tarta de queso", "5.25", "Lemon and passionfruit cheesecake with Oreo crumble and passionfruit sauce", "passion fruit cheesecake oreo crumble"),
            ("Cheese selection", "Fromages", "7.15", "Selection of cheeses with garnishes", "cheese platter selection"),
        ],
    },
    {
        "category": "Kids",
        "items": [
            ("Serrano ham and melon", "Ham & meloen", "3.85", "Serrano ham with fresh melon", "serrano ham melon"),
            ("Shrimp skewer", "Spiesje met gamba's", "5.45", "Shrimp skewer with salad and aioli", "shrimp skewer salad aioli"),
            ("Tomato soup", "Tomatensoep", "1.50", "Tomato soup with cream", "tomato soup cream"),
            ("Mini beef carpaccio", "Mini carpaccio", "4.35", "Small beef carpaccio with arugula and Parmesan", "beef carpaccio arugula parmesan"),
            ("Small fried white fish", "Witvisje", "8.80", "Fried white fish with fries, applesauce and salad", "fried white fish fries"),
            ("Spaghetti with tomato sauce", "Spaghetti", "3.50", "Spaghetti with tomato sauce", "spaghetti tomato sauce"),
            ("Chicken fillet with fries", "Kipfilet", "5.45", "Chicken fillet with fries and salad", "chicken breast fries salad"),
            ("Frikandel with fries", "Frikandel", "3.70", "Dutch frikandel sausage with fries, applesauce and salad", "frikandel fries"),
            ("Small steak with fries", "Biefstuk", "8.35", "Small fried steak with fries, applesauce and salad", "steak fries"),
            ("Kids vanilla ice cream", "Kinderijsje", "2.20", "Vanilla ice cream with whipped cream and a surprise", "vanilla ice cream whipped cream sprinkles"),
        ],
    },
    {
        "category": "Coffee",
        "items": [
            ("Irish coffee", "Irish coffee", "5.00", "Coffee cocktail with Irish whiskey", "irish coffee"),
            ("La Chouffe coffee", "La Chouffe Coffee", "5.00", "Coffee with La Chouffe liqueur", "liqueur coffee whipped cream"),
            ("Spanish coffee", "Spanish coffee", "4.85", "Coffee with Licor 43", "spanish coffee licor 43"),
            ("French coffee", "French coffee", "5.80", "Coffee with Grand Marnier", "french coffee grand marnier"),
        ],
    },
]


def slugify(value):
    value = value.lower().replace("&", "and")
    value = re.sub(r"[^a-z0-9]+", "-", value).strip("-")
    return value or "item"


def request_json(url):
    req = urllib.request.Request(url, headers={"User-Agent": UA})
    for attempt in range(6):
        try:
            with urllib.request.urlopen(req, timeout=30) as response:
                time.sleep(0.8)
                return json.loads(response.read().decode("utf-8"))
        except urllib.error.HTTPError as exc:
            if exc.code != 429 or attempt == 5:
                raise
            time.sleep(10 + attempt * 8)
    raise RuntimeError(f"Could not fetch {url}")


def request_bytes(url):
    req = urllib.request.Request(url, headers={"User-Agent": UA})
    for attempt in range(5):
        try:
            with urllib.request.urlopen(req, timeout=60) as response:
                return response.read()
        except urllib.error.HTTPError as exc:
            if exc.code != 429 or attempt == 4:
                raise
            time.sleep(3 + attempt * 4)
    raise RuntimeError(f"Could not download {url}")


def external_image_replacements():
    if not PHOTO_REPLACEMENTS_FILE.exists():
        return {}
    replacements = json.loads(PHOTO_REPLACEMENTS_FILE.read_text(encoding="utf-8"))
    return {item["slug"]: item for item in replacements}


def commons_image(query):
    TMP_DIR.mkdir(parents=True, exist_ok=True)
    cache = {}
    if CACHE_FILE.exists():
        cache = json.loads(CACHE_FILE.read_text(encoding="utf-8"))
    if query in cache:
        return cache[query]

    params = {
        "action": "query",
        "generator": "search",
        "gsrsearch": query,
        "gsrnamespace": "6",
        "gsrlimit": "8",
        "prop": "imageinfo",
        "iiprop": "url|mime|extmetadata",
        "iiurlwidth": "900",
        "format": "json",
    }
    api = "https://commons.wikimedia.org/w/api.php?" + urllib.parse.urlencode(params)
    pages = request_json(api).get("query", {}).get("pages", {})
    for page in pages.values():
        info = (page.get("imageinfo") or [{}])[0]
        if not info.get("mime", "").startswith("image/"):
            continue
        url = info.get("thumburl") or info.get("url", "")
        if not url.lower().split("?")[0].endswith((".jpg", ".jpeg", ".png", ".webp")):
            continue
        meta = info.get("extmetadata", {})
        result = {
            "url": url,
            "title": page.get("title", "").removeprefix("File:"),
            "credit": clean_meta(meta.get("Artist", {}).get("value")) or clean_meta(meta.get("Credit", {}).get("value")) or "Wikimedia Commons contributor",
            "license": clean_meta(meta.get("LicenseShortName", {}).get("value")) or "Wikimedia Commons",
            "source_url": clean_meta(meta.get("ObjectURL", {}).get("value")) or "https://commons.wikimedia.org/wiki/" + urllib.parse.quote(page.get("title", "").replace(" ", "_")),
        }
        cache[query] = result
        CACHE_FILE.write_text(json.dumps(cache, indent=2, ensure_ascii=False) + "\n", encoding="utf-8")
        return result
    raise RuntimeError(f"No Commons image found for {query!r}")


def clean_meta(value):
    if not value:
        return ""
    value = re.sub(r"<[^>]+>", "", value)
    value = value.replace("\n", " ").strip()
    return re.sub(r"\s+", " ", value)


def optimize(src, dst):
    with Image.open(src) as im:
        im = ImageOps.exif_transpose(im).convert("RGB")
        im.thumbnail((640, 480), Image.Resampling.LANCZOS)
        canvas = Image.new("RGB", (640, 480), (244, 242, 238))
        canvas.paste(im, ((640 - im.width) // 2, (480 - im.height) // 2))
        canvas.save(dst, "JPEG", quality=84, optimize=True)


def commons_file_source(file_name):
    return "https://commons.wikimedia.org/wiki/File:" + urllib.parse.quote(file_name.replace(" ", "_"))


def commons_file_redirect(file_name):
    return "https://commons.wikimedia.org/wiki/Special:Redirect/file/" + urllib.parse.quote(file_name) + "?width=900"


def prepare_image(item):
    IMG_DIR.mkdir(parents=True, exist_ok=True)
    TMP_DIR.mkdir(parents=True, exist_ok=True)
    slug = item["slug"]
    output = IMG_DIR / f"{slug}.jpg"
    external_override = external_image_replacements().get(slug)
    if external_override:
        cached = TMP_DIR / f"external-{slug}.jpg"
        if not cached.exists():
            cached.write_bytes(request_bytes(external_override["image_url"]))
        if not output.exists() or cached.stat().st_mtime > output.stat().st_mtime:
            optimize(cached, output)
        return {
            "image": f"assets/images/{slug}.jpg",
            "image_title": external_override["title"],
            "image_credit": external_override["credit"],
            "image_license": external_override["license"],
            "image_source": external_override["source_url"],
            "image_search": external_override["search"],
        }

    file_override = FILE_IMAGE_OVERRIDES.get(slug)
    if file_override:
        cached = TMP_DIR / f"override-{slug}{Path(file_override).suffix or '.jpg'}"
        if not cached.exists():
            cached.write_bytes(request_bytes(commons_file_redirect(file_override)))
        if not output.exists() or cached.stat().st_mtime > output.stat().st_mtime:
            optimize(cached, output)
        return {
            "image": f"assets/images/{slug}.jpg",
            "image_title": file_override,
            "image_credit": "Wikimedia Commons contributor",
            "image_license": "See Commons file page",
            "image_source": commons_file_source(file_override),
            "image_search": "Exact Wikimedia Commons file override",
        }

    override = OFFICIAL_IMAGES.get(item["original_name"])
    if override and override["local"].exists():
        optimize(override["local"], output)
        return {
            "image": f"assets/images/{slug}.jpg",
            "image_title": override["title"],
            "image_credit": override["credit"],
            "image_license": override["license"],
            "image_source": override["source_url"],
            "image_search": "Official Montimar site",
        }

    queries = [item["image_query"], *FALLBACK_QUERIES.get(item["image_query"], []), item["name"]]
    query_words = [word for word in re.split(r"[^a-z0-9]+", item["image_query"].lower()) if len(word) > 3]
    if len(query_words) >= 2:
        queries.append(" ".join(query_words[:2]))
        queries.append(" ".join(query_words[-2:]))
    queries.extend(GENERIC_CATEGORY_QUERIES[item["category"]])
    queries = list(dict.fromkeys(queries))
    last_error = None
    for query in queries:
        try:
            meta = commons_image(query)
            break
        except RuntimeError as exc:
            last_error = exc
    else:
        raise last_error
    if not output.exists():
        cached = TMP_DIR / f"{slug}{Path(urllib.parse.urlparse(meta['url']).path).suffix or '.jpg'}"
        cached.write_bytes(request_bytes(meta["url"]))
        optimize(cached, output)
    return {
        "image": f"assets/images/{slug}.jpg",
        "image_title": meta["title"],
        "image_credit": meta["credit"],
        "image_license": meta["license"],
        "image_source": meta["source_url"],
        "image_search": item["image_query"],
    }


def build_data():
    DATA_DIR.mkdir(parents=True, exist_ok=True)
    items = []
    used = {}
    for section in MENU:
        for english, original, price, description, image_query in section["items"]:
            base = slugify(english)
            used[base] = used.get(base, 0) + 1
            slug = base if used[base] == 1 else f"{base}-{used[base]}"
            item = {
                "slug": slug,
                "category": section["category"],
                "name": english,
                "original_name": original,
                "price": f"EUR {price}",
                "description": description,
                "image_query": image_query,
            }
            item.update(prepare_image(item))
            items.append(item)
    (DATA_DIR / "menu.json").write_text(json.dumps(items, indent=2, ensure_ascii=False) + "\n", encoding="utf-8")
    sources = {
        "menu_source": MENU_SOURCE,
        "restaurant_source": "https://www.montimar.nl/",
        "notes": [
            "Dish text and prices translated from the Montimar menu page.",
            "Official Montimar images were used where they clearly represented a listed dish; Wikimedia Commons representative photos fill gaps.",
            "Photos are visual aids, not a guarantee of exact restaurant plating.",
        ],
        "photos": [
            {
                "dish": item["name"],
                "source": item["image_source"],
                "title": item["image_title"],
                "credit": item["image_credit"],
                "license": item["image_license"],
                "search": item["image_search"],
            }
            for item in items
        ],
    }
    (DATA_DIR / "photo_sources.json").write_text(json.dumps(sources, indent=2, ensure_ascii=False) + "\n", encoding="utf-8")
    return items


def write_html(items):
    categories = list(dict.fromkeys(item["category"] for item in items))
    buttons = "\n".join(
        f'<button class="filter-button" type="button" data-category="{escape(category)}">{escape(category)}</button>'
        for category in categories
    )
    sections = []
    for category in categories:
        cat_items = [item for item in items if item["category"] == category]
        cards = []
        for item in cat_items:
            price_value = float(item["price"].replace("EUR", "").strip())
            cards.append(
                f"""
                <article class="dish-card" data-slug="{escape(item['slug'])}" data-name="{escape(item['name'])}" data-original-name="{escape(item['original_name'])}" data-price="{price_value:.2f}" data-category="{escape(item['category'])}" data-search="{escape((item['name'] + ' ' + item['original_name'] + ' ' + item['description']).lower())}">
                  <a class="dish-image-link" href="{escape(item['image_source'])}" target="_blank" rel="noreferrer" title="Open photo source">
                    <img class="dish-image" src="{escape(item['image'])}" alt="{escape(item['name'])}">
                  </a>
                  <div class="dish-info">
                    <div class="dish-topline">
                      <h3>{escape(item['name'])}</h3>
                      <strong>{escape(item['price'])}</strong>
                    </div>
                    <p class="original-name">{escape(item['original_name'])}</p>
                    <p class="description">{escape(item['description'])}</p>
                    <p class="source-line">Photo: <a href="{escape(item['image_source'])}" target="_blank" rel="noreferrer">{escape(item['image_title'][:80])}</a></p>
                    <div class="dish-actions" aria-label="Cart controls for {escape(item['name'])}">
                      <button class="add-button" type="button" data-cart-add="{escape(item['slug'])}">Add</button>
                      <div class="quantity-control dish-quantity" data-cart-controls="{escape(item['slug'])}" hidden>
                        <button type="button" data-cart-decrease="{escape(item['slug'])}" aria-label="Decrease {escape(item['name'])}">-</button>
                        <span data-cart-quantity="{escape(item['slug'])}">0</span>
                        <button type="button" data-cart-increase="{escape(item['slug'])}" aria-label="Increase {escape(item['name'])}">+</button>
                      </div>
                    </div>
                  </div>
                </article>
                """
            )
        sections.append(
            f"""
            <section class="menu-section" id="{slugify(category)}" data-section="{escape(category)}">
              <div class="section-heading">
                <h2>{escape(category)}</h2>
                <span>{len(cat_items)} items</span>
              </div>
              <div class="dish-grid">
                {''.join(cards)}
              </div>
            </section>
            """
        )
    html = f"""<!doctype html>
<html lang="en">
<head>
  <meta charset="utf-8">
  <meta name="viewport" content="width=device-width, initial-scale=1">
  <title>Montimar Mierlo Visual Menu</title>
  <meta name="description" content="A practical English visual menu for Montimar Mierlo with prices, descriptions and representative dish images.">
  <link rel="icon" href="assets/images/beef-carpaccio.jpg">
  <link rel="stylesheet" href="styles.css">
</head>
<body>
  <header class="site-header">
    <div>
      <p class="eyebrow">Montimar Mierlo</p>
      <h1>Visual Menu</h1>
      <p class="summary">English dish names, original menu names, prices and one representative image per entry. Images help with choosing; plating may differ at the restaurant.</p>
    </div>
    <div class="facts">
      <div><span>Total</span><strong>{len(items)} items</strong></div>
      <div><span>Cuisine</span><strong>Mediterranean</strong></div>
      <div><span>Source</span><a href="{MENU_SOURCE}" target="_blank" rel="noreferrer">Montimar menu</a></div>
    </div>
  </header>

  <nav class="toolbar" aria-label="Menu controls">
    <label class="search-label" for="search">Search</label>
    <input id="search" type="search" placeholder="Search dishes, ingredients, original names">
    <div class="filter-row">
      <button class="filter-button active" type="button" data-category="All">All</button>
      {buttons}
    </div>
    <button class="cart-button" id="cart-button" type="button" aria-haspopup="dialog" aria-controls="cart-drawer">
      <span>Cart</span>
      <strong id="cart-button-count">0 items</strong>
      <span id="cart-button-total">EUR 0.00</span>
    </button>
  </nav>

  <main>
    {''.join(sections)}
    <p id="empty-state" hidden>No dishes match that search.</p>
  </main>

  <div class="cart-backdrop" id="cart-backdrop" hidden></div>
  <aside class="cart-drawer" id="cart-drawer" aria-labelledby="cart-title" aria-hidden="true" hidden>
    <div class="cart-header">
      <div>
        <p class="eyebrow">Local order list</p>
        <h2 id="cart-title">Order summary</h2>
      </div>
      <button class="icon-button" id="cart-close" type="button" aria-label="Close order summary">x</button>
    </div>
    <div class="cart-body">
      <p class="cart-empty" id="cart-empty">No dishes added yet.</p>
      <div class="cart-items" id="cart-items"></div>
    </div>
    <div class="cart-footer">
      <div class="cart-total">
        <span>Total</span>
        <strong id="cart-total">EUR 0.00</strong>
      </div>
      <button class="clear-button" id="cart-clear" type="button">Clear cart</button>
    </div>
  </aside>

  <footer>
    <p>Menu text and prices are translated from Montimar's public menu page. Photo attributions are stored in <a href="data/photo_sources.json">data/photo_sources.json</a>.</p>
  </footer>
  <script src="app.js"></script>
</body>
</html>
"""
    (ROOT / "index.html").write_text(textwrap.dedent(html), encoding="utf-8")


def write_css():
    css = """
    :root {
      color-scheme: light;
      --ink: #1f2528;
      --muted: #626c70;
      --line: #d8d6cf;
      --paper: #faf9f5;
      --panel: #ffffff;
      --accent: #116c5b;
      --accent-2: #7a251c;
      --shadow: 0 1px 4px rgba(0, 0, 0, 0.08);
    }

    * { box-sizing: border-box; }

    body {
      margin: 0;
      font-family: Arial, Helvetica, sans-serif;
      color: var(--ink);
      background: var(--paper);
      font-size: 15px;
      line-height: 1.35;
    }

    a { color: var(--accent); }

    .site-header {
      display: grid;
      grid-template-columns: minmax(0, 1fr) auto;
      gap: 24px;
      padding: 22px 24px 16px;
      border-bottom: 1px solid var(--line);
      background: #fff;
    }

    .eyebrow {
      margin: 0 0 3px;
      color: var(--accent-2);
      font-weight: 700;
      text-transform: uppercase;
      font-size: 12px;
    }

    h1 {
      margin: 0;
      font-size: 34px;
      line-height: 1;
      letter-spacing: 0;
    }

    .summary {
      max-width: 900px;
      margin: 8px 0 0;
      color: var(--muted);
    }

    .facts {
      display: grid;
      grid-template-columns: repeat(3, minmax(100px, 1fr));
      gap: 8px;
      align-self: end;
      min-width: 360px;
    }

    .facts div {
      border: 1px solid var(--line);
      background: var(--paper);
      padding: 9px 10px;
      border-radius: 6px;
    }

    .facts span {
      display: block;
      font-size: 11px;
      color: var(--muted);
      text-transform: uppercase;
      margin-bottom: 2px;
    }

    .facts strong,
    .facts a {
      display: block;
      font-size: 14px;
      font-weight: 700;
      white-space: nowrap;
    }

    .toolbar {
      position: sticky;
      top: 0;
      z-index: 10;
      display: grid;
      grid-template-columns: auto minmax(240px, 420px) minmax(0, 1fr) auto;
      align-items: center;
      gap: 10px;
      padding: 10px 24px;
      border-bottom: 1px solid var(--line);
      background: rgba(250, 249, 245, 0.96);
      backdrop-filter: blur(6px);
    }

    .search-label {
      font-weight: 700;
      color: var(--muted);
    }

    #search {
      width: 100%;
      height: 38px;
      border: 1px solid var(--line);
      border-radius: 6px;
      padding: 0 12px;
      font: inherit;
      background: #fff;
    }

    .filter-row {
      display: flex;
      flex-wrap: wrap;
      gap: 6px;
      justify-content: flex-end;
    }

    .filter-button {
      min-height: 32px;
      border: 1px solid var(--line);
      border-radius: 6px;
      padding: 0 10px;
      font: inherit;
      font-weight: 700;
      color: var(--ink);
      background: #fff;
      cursor: pointer;
    }

    .filter-button.active {
      border-color: var(--accent);
      background: var(--accent);
      color: #fff;
    }

    main {
      padding: 16px 24px 28px;
    }

    .menu-section {
      margin-bottom: 22px;
    }

    .section-heading {
      display: flex;
      justify-content: space-between;
      align-items: baseline;
      gap: 12px;
      padding: 8px 0;
      border-bottom: 2px solid var(--ink);
    }

    .section-heading h2 {
      margin: 0;
      font-size: 22px;
      letter-spacing: 0;
    }

    .section-heading span {
      color: var(--muted);
      font-size: 13px;
      white-space: nowrap;
    }

    .dish-grid {
      display: grid;
      grid-template-columns: repeat(2, minmax(0, 1fr));
      gap: 10px;
      margin-top: 10px;
    }

    .dish-card {
      display: grid;
      grid-template-columns: 150px minmax(0, 1fr);
      min-height: 148px;
      border: 1px solid var(--line);
      border-radius: 8px;
      background: var(--panel);
      overflow: hidden;
      box-shadow: var(--shadow);
    }

    .dish-image-link {
      display: block;
      width: 150px;
      height: 100%;
      min-height: 148px;
      background: #ece8df;
    }

    .dish-image {
      display: block;
      width: 100%;
      height: 100%;
      object-fit: cover;
    }

    .dish-info {
      min-width: 0;
      padding: 10px 12px;
    }

    .dish-topline {
      display: grid;
      grid-template-columns: minmax(0, 1fr) auto;
      gap: 10px;
      align-items: start;
    }

    .dish-topline h3 {
      margin: 0;
      font-size: 17px;
      line-height: 1.15;
      letter-spacing: 0;
    }

    .dish-topline strong {
      color: var(--accent-2);
      white-space: nowrap;
      font-size: 15px;
    }

    .original-name {
      margin: 3px 0 0;
      color: var(--muted);
      font-size: 13px;
      font-weight: 700;
    }

    .description {
      margin: 7px 0 0;
    }

    .source-line {
      margin: 8px 0 0;
      color: var(--muted);
      font-size: 12px;
      white-space: nowrap;
      overflow: hidden;
      text-overflow: ellipsis;
    }

    .dish-actions {
      display: flex;
      align-items: center;
      justify-content: flex-end;
      min-height: 34px;
      margin-top: 10px;
    }

    .add-button,
    .clear-button {
      min-height: 34px;
      border: 1px solid var(--accent);
      border-radius: 6px;
      padding: 0 14px;
      font: inherit;
      font-weight: 700;
      color: #fff;
      background: var(--accent);
      cursor: pointer;
    }

    .clear-button {
      width: 100%;
      border-color: var(--line);
      color: var(--accent-2);
      background: #fff;
    }

    .quantity-control {
      display: inline-grid;
      grid-template-columns: 34px 38px 34px;
      align-items: center;
      min-height: 34px;
      border: 1px solid var(--line);
      border-radius: 6px;
      overflow: hidden;
      background: #fff;
    }

    .quantity-control button,
    .icon-button {
      width: 34px;
      height: 34px;
      border: 0;
      font: inherit;
      font-weight: 700;
      color: var(--ink);
      background: #fff;
      cursor: pointer;
    }

    .quantity-control button:hover,
    .icon-button:hover,
    .add-button:hover,
    .clear-button:hover,
    .cart-button:hover {
      filter: brightness(0.96);
    }

    .quantity-control span {
      display: inline-flex;
      align-items: center;
      justify-content: center;
      min-width: 38px;
      font-weight: 700;
      border-right: 1px solid var(--line);
      border-left: 1px solid var(--line);
    }

    .cart-button {
      display: grid;
      grid-template-columns: auto auto;
      gap: 2px 12px;
      align-items: center;
      min-width: 174px;
      min-height: 44px;
      border: 1px solid var(--accent);
      border-radius: 8px;
      padding: 6px 12px;
      color: #fff;
      background: var(--accent);
      box-shadow: var(--shadow);
      cursor: pointer;
    }

    .cart-button span:first-child {
      font-weight: 700;
    }

    .cart-button strong {
      justify-self: end;
      font-size: 13px;
    }

    #cart-button-total {
      grid-column: 1 / -1;
      font-weight: 700;
      text-align: left;
    }

    .cart-backdrop {
      position: fixed;
      inset: 0;
      z-index: 35;
      background: rgba(31, 37, 40, 0.34);
    }

    .cart-drawer {
      position: fixed;
      top: 0;
      right: 0;
      z-index: 40;
      display: grid;
      grid-template-rows: auto minmax(0, 1fr) auto;
      width: min(420px, 100vw);
      height: 100vh;
      border-left: 1px solid var(--line);
      background: #fff;
      box-shadow: -12px 0 28px rgba(0, 0, 0, 0.16);
      transform: translateX(100%);
      transition: transform 160ms ease;
    }

    .cart-drawer.open {
      transform: translateX(0);
    }

    .cart-header {
      display: flex;
      align-items: flex-start;
      justify-content: space-between;
      gap: 16px;
      padding: 18px 18px 14px;
      border-bottom: 1px solid var(--line);
    }

    .cart-header h2 {
      margin: 0;
      font-size: 24px;
      letter-spacing: 0;
    }

    .icon-button {
      flex: 0 0 auto;
      border: 1px solid var(--line);
      border-radius: 6px;
      color: var(--muted);
    }

    .cart-body {
      min-height: 0;
      overflow: auto;
      padding: 14px 18px;
    }

    .cart-empty {
      margin: 0;
      padding: 14px;
      border: 1px solid var(--line);
      border-radius: 8px;
      color: var(--muted);
      background: var(--paper);
      font-weight: 700;
    }

    .cart-items {
      display: grid;
      gap: 10px;
    }

    .cart-item {
      display: grid;
      grid-template-columns: minmax(0, 1fr) auto;
      gap: 10px;
      padding: 12px;
      border: 1px solid var(--line);
      border-radius: 8px;
      background: #fff;
    }

    .cart-item h3 {
      margin: 0;
      font-size: 16px;
      line-height: 1.2;
      letter-spacing: 0;
    }

    .cart-item p {
      margin: 3px 0 0;
      color: var(--muted);
      font-size: 13px;
      font-weight: 700;
    }

    .cart-item strong {
      align-self: start;
      white-space: nowrap;
      color: var(--accent-2);
    }

    .cart-item .quantity-control {
      grid-column: 1 / -1;
      justify-self: start;
    }

    .cart-footer {
      display: grid;
      gap: 12px;
      padding: 14px 18px 18px;
      border-top: 1px solid var(--line);
      background: var(--paper);
    }

    .cart-total {
      display: flex;
      align-items: baseline;
      justify-content: space-between;
      gap: 16px;
      font-size: 18px;
    }

    .cart-total span {
      color: var(--muted);
      font-weight: 700;
    }

    #empty-state {
      margin: 30px 0;
      padding: 16px;
      border: 1px solid var(--line);
      border-radius: 8px;
      background: #fff;
      font-weight: 700;
    }

    footer {
      border-top: 1px solid var(--line);
      padding: 16px 24px 24px;
      color: var(--muted);
      background: #fff;
    }

    footer p {
      margin: 0;
      max-width: 1100px;
    }

    [hidden] { display: none !important; }

    @media (max-width: 1080px) {
      .site-header {
        grid-template-columns: 1fr;
      }

      .facts {
        min-width: 0;
      }

      .toolbar {
        grid-template-columns: auto minmax(160px, 1fr) auto;
      }

      .filter-row {
        grid-column: 1 / -1;
        justify-content: flex-start;
      }

      .dish-grid {
        grid-template-columns: 1fr;
      }
    }

    @media (max-width: 640px) {
      .site-header,
      .toolbar,
      main,
      footer {
        padding-left: 12px;
        padding-right: 12px;
      }

      h1 {
        font-size: 28px;
      }

      .facts {
        grid-template-columns: 1fr;
      }

      .dish-card {
        grid-template-columns: 112px minmax(0, 1fr);
        min-height: 142px;
      }

      .dish-image-link {
        width: 112px;
        min-height: 142px;
      }

      .dish-info {
        padding: 8px 9px;
      }

      .dish-topline {
        grid-template-columns: 1fr;
        gap: 3px;
      }

      .dish-topline h3 {
        font-size: 15px;
      }

      .description {
        font-size: 13px;
      }

      .source-line {
        display: none;
      }

      .dish-actions {
        justify-content: flex-start;
      }

      .cart-button {
        grid-column: 1 / -1;
        justify-self: stretch;
      }

      .cart-header,
      .cart-body,
      .cart-footer {
        padding-left: 14px;
        padding-right: 14px;
      }
    }
    """
    (ROOT / "styles.css").write_text(textwrap.dedent(css).strip() + "\n", encoding="utf-8")


def write_js():
    js = """
    const searchInput = document.querySelector('#search');
    const buttons = Array.from(document.querySelectorAll('.filter-button'));
    const cards = Array.from(document.querySelectorAll('.dish-card'));
    const sections = Array.from(document.querySelectorAll('.menu-section'));
    const empty = document.querySelector('#empty-state');
    const cartButton = document.querySelector('#cart-button');
    const cartButtonCount = document.querySelector('#cart-button-count');
    const cartButtonTotal = document.querySelector('#cart-button-total');
    const cartDrawer = document.querySelector('#cart-drawer');
    const cartBackdrop = document.querySelector('#cart-backdrop');
    const cartClose = document.querySelector('#cart-close');
    const cartItems = document.querySelector('#cart-items');
    const cartEmpty = document.querySelector('#cart-empty');
    const cartTotal = document.querySelector('#cart-total');
    const cartClear = document.querySelector('#cart-clear');

    const CART_STORAGE_KEY = 'montimar-cart-v1';
    const menuItems = new Map(
      cards.map((card) => [
        card.dataset.slug,
        {
          slug: card.dataset.slug,
          name: card.dataset.name,
          originalName: card.dataset.originalName,
          price: Number.parseFloat(card.dataset.price) || 0,
        },
      ]),
    );

    let activeCategory = 'All';
    let cart = loadCart();

    function formatMoney(value) {
      return `EUR ${value.toFixed(2)}`;
    }

    function loadCart() {
      try {
        const saved = JSON.parse(localStorage.getItem(CART_STORAGE_KEY) || '{}');
        return Object.fromEntries(
          Object.entries(saved)
            .filter(([slug, quantity]) => menuItems.has(slug) && Number.isInteger(quantity) && quantity > 0)
            .map(([slug, quantity]) => [slug, quantity]),
        );
      } catch {
        return {};
      }
    }

    function saveCart() {
      localStorage.setItem(CART_STORAGE_KEY, JSON.stringify(cart));
    }

    function getQuantity(slug) {
      return cart[slug] || 0;
    }

    function setQuantity(slug, quantity) {
      const nextQuantity = Math.max(0, quantity);
      if (!menuItems.has(slug)) return;
      if (nextQuantity === 0) {
        delete cart[slug];
      } else {
        cart[slug] = nextQuantity;
      }
      saveCart();
      renderCart();
    }

    function increaseItem(slug) {
      setQuantity(slug, getQuantity(slug) + 1);
    }

    function decreaseItem(slug) {
      setQuantity(slug, getQuantity(slug) - 1);
    }

    function getCartRows() {
      return Object.entries(cart)
        .map(([slug, quantity]) => {
          const item = menuItems.get(slug);
          return item ? { ...item, quantity, subtotal: item.price * quantity } : null;
        })
        .filter(Boolean);
    }

    function getCartSummary() {
      return getCartRows().reduce(
        (summary, item) => ({
          count: summary.count + item.quantity,
          total: summary.total + item.subtotal,
        }),
        { count: 0, total: 0 },
      );
    }

    function itemLabel(count) {
      return `${count} ${count === 1 ? 'item' : 'items'}`;
    }

    function renderCardControls() {
      cards.forEach((card) => {
        const quantity = getQuantity(card.dataset.slug);
        const addButton = card.querySelector('[data-cart-add]');
        const controls = card.querySelector('[data-cart-controls]');
        const quantityLabel = card.querySelector('[data-cart-quantity]');

        addButton.hidden = quantity > 0;
        controls.hidden = quantity === 0;
        quantityLabel.textContent = quantity;
      });
    }

    function renderCartItems(rows) {
      cartItems.replaceChildren();
      rows.forEach((item) => {
        const row = document.createElement('article');
        row.className = 'cart-item';
        row.innerHTML = `
          <div>
            <h3></h3>
            <p></p>
          </div>
          <strong></strong>
          <div class="quantity-control">
            <button type="button" data-cart-decrease="${item.slug}" aria-label="Decrease ${item.name}">-</button>
            <span>${item.quantity}</span>
            <button type="button" data-cart-increase="${item.slug}" aria-label="Increase ${item.name}">+</button>
          </div>
        `;
        row.querySelector('h3').textContent = item.name;
        row.querySelector('p').textContent = item.originalName;
        row.querySelector('strong').textContent = formatMoney(item.subtotal);
        cartItems.append(row);
      });
    }

    function renderCart() {
      const rows = getCartRows();
      const { count, total } = getCartSummary();

      cartButtonCount.textContent = itemLabel(count);
      cartButtonTotal.textContent = formatMoney(total);
      cartTotal.textContent = formatMoney(total);
      cartEmpty.hidden = rows.length !== 0;
      cartItems.hidden = rows.length === 0;
      cartClear.disabled = rows.length === 0;

      renderCardControls();
      renderCartItems(rows);
    }

    function openCart() {
      cartDrawer.hidden = false;
      cartDrawer.classList.add('open');
      cartDrawer.setAttribute('aria-hidden', 'false');
      cartBackdrop.hidden = false;
      cartClose.focus();
    }

    function closeCart() {
      cartDrawer.classList.remove('open');
      cartDrawer.setAttribute('aria-hidden', 'true');
      cartDrawer.hidden = true;
      cartBackdrop.hidden = true;
      cartButton.focus();
    }

    function update() {
      const query = searchInput.value.trim().toLowerCase();
      let visibleCount = 0;

      cards.forEach((card) => {
        const categoryMatches = activeCategory === 'All' || card.dataset.category === activeCategory;
        const searchMatches = !query || card.dataset.search.includes(query);
        const visible = categoryMatches && searchMatches;
        card.hidden = !visible;
        if (visible) visibleCount += 1;
      });

      sections.forEach((section) => {
        const hasVisibleCard = Array.from(section.querySelectorAll('.dish-card')).some((card) => !card.hidden);
        section.hidden = !hasVisibleCard;
      });

      empty.hidden = visibleCount !== 0;
    }

    buttons.forEach((button) => {
      button.addEventListener('click', () => {
        activeCategory = button.dataset.category;
        buttons.forEach((item) => item.classList.toggle('active', item === button));
        update();
      });
    });

    searchInput.addEventListener('input', update);
    document.addEventListener('click', (event) => {
      const addButton = event.target.closest('[data-cart-add]');
      const increaseButton = event.target.closest('[data-cart-increase]');
      const decreaseButton = event.target.closest('[data-cart-decrease]');

      if (addButton) increaseItem(addButton.dataset.cartAdd);
      if (increaseButton) increaseItem(increaseButton.dataset.cartIncrease);
      if (decreaseButton) decreaseItem(decreaseButton.dataset.cartDecrease);
    });

    cartButton.addEventListener('click', openCart);
    cartClose.addEventListener('click', closeCart);
    cartBackdrop.addEventListener('click', closeCart);
    cartClear.addEventListener('click', () => {
      cart = {};
      saveCart();
      renderCart();
    });
    document.addEventListener('keydown', (event) => {
      if (event.key === 'Escape' && cartDrawer.classList.contains('open')) closeCart();
    });

    update();
    renderCart();
    """
    (ROOT / "app.js").write_text(textwrap.dedent(js).strip() + "\n", encoding="utf-8")


def write_readme():
    readme = f"""# Montimar Mierlo Visual Menu

A practical English visual menu for Montimar Mierlo. It includes every listed menu entry from the public menu page, translated descriptions, prices, one image per dish, and a local cart for building an order summary.

Source menu: {MENU_SOURCE}

Photos are representative visual aids. Some come from Montimar's own public website where a matching image was available; the rest are representative external web or Wikimedia Commons images. Attribution and source details are in `data/photo_sources.json`.

## Local use

Open `index.html` in a browser, or serve the folder with:

```bash
python3 -m http.server 8000
```

The cart is stored only in your browser with the `montimar-cart-v1` localStorage key. It does not submit orders or send network requests.

## Regenerate

```bash
python3 scripts/build_visual_menu.py
```
"""
    (ROOT / "README.md").write_text(readme, encoding="utf-8")


def main():
    items = build_data()
    write_html(items)
    write_css()
    write_js()
    write_readme()
    print(f"Built {len(items)} menu items with images.")


if __name__ == "__main__":
    main()
