#!/usr/bin/env python3
"""Builds the Lina S Lee Cards and Goods site into ./dist.

Run:  python3 build.py
Edit content in data/*.json, put photos in static/images/. No other dependencies.
"""
import json, shutil, datetime
from html import escape as e
from pathlib import Path

ROOT = Path(__file__).parent
DIST = ROOT / "dist"
load = lambda n: json.loads((ROOT / "data" / n).read_text())
C = load("site.config.json")
PRODUCTS = load("products.json")
EVENTS = load("events.json")
POSTS = load("posts.json")
SITE = C["siteUrl"].rstrip("/")
TODAY = datetime.date.today().isoformat()

# ---------- groups (categories) ----------
GOODS_BY_TYPE = {g["type"]: g for g in C.get("goods", [])}
THEMES = {t["slug"]: t for t in C["themes"]}


def group_of(p):
    if p["type"] == "card":
        return THEMES[p["theme"]]
    return GOODS_BY_TYPE[p["type"]]


for p in PRODUCTS:
    p["group"] = group_of(p)
    p["url"] = f"/shop/{p['group']['slug']}/{p['slug']}/"

GROUPS = []  # only groups that have products get pages
for g in list(THEMES.values()) + list(GOODS_BY_TYPE.values()):
    items = [p for p in PRODUCTS if p["group"] is g]
    if items:
        g["items"] = items
        GROUPS.append(g)

PAGES = []  # urls for sitemap
if DIST.exists():
    shutil.rmtree(DIST)
shutil.copytree(ROOT / "static", DIST)


def money(p):
    return f"${p['price']:g}" if p.get("price") not in (None, "") else "Email for price"


def write(url, html):
    out = DIST / url.lstrip("/") / "index.html" if url != "/404.html" else DIST / "404.html"
    out.parent.mkdir(parents=True, exist_ok=True)
    out.write_text(html)
    if url != "/404.html":
        PAGES.append(url)


def ld(obj):
    return '<script type="application/ld+json">' + json.dumps(obj, ensure_ascii=False) + "</script>"


ORG = {
    "@context": "https://schema.org", "@type": "Organization", "name": C["brand"],
    "url": SITE, "logo": f"{SITE}/images/logo-main.png", "email": C["email"],
    "founder": {"@type": "Person", "name": "Lina S Lee"},
    "address": {"@type": "PostalAddress", "addressLocality": "New York", "addressRegion": "NY", "addressCountry": "US"},
    **({"sameAs": [C["instagram"]]} if C.get("instagram") else {}),
}


def crumbs(items):
    return {"@context": "https://schema.org", "@type": "BreadcrumbList", "itemListElement": [
        {"@type": "ListItem", "position": i + 1, "name": n, "item": SITE + u} for i, (n, u) in enumerate(items)]}


# ---------- layout ----------
def layout(url, title, desc, body, schema=None, image=None, og_type="website", noindex=False):
    img = SITE + "/" + (image or "images/logo-main.png")
    nav = [("Shop", "/shop/"), ("About", "/about/"), ("Find me in NYC", "/find-me-in-nyc/")]
    if POSTS:
        nav.append(("Journal", "/journal/"))
    nav += [("FAQ", "/faq/"), ("Contact", "/contact/")]
    navhtml = "".join(
        f'<a href="{u}"{" aria-current=\"page\"" if url.startswith(u) else ""}>{n}</a>' for n, u in nav)
    return f"""<!doctype html>
<html lang="en"><head>
<meta charset="utf-8"><meta name="viewport" content="width=device-width,initial-scale=1">
<title>{e(title)}</title>
<meta name="description" content="{e(desc)}">
<link rel="canonical" href="{SITE}{url}">
{'<meta name="robots" content="noindex">' if noindex else ''}
<meta property="og:type" content="{og_type}"><meta property="og:title" content="{e(title)}">
<meta property="og:description" content="{e(desc)}"><meta property="og:url" content="{SITE}{url}">
<meta property="og:image" content="{img}"><meta property="og:site_name" content="{e(C['brand'])}">
<meta name="twitter:card" content="summary_large_image">
<link rel="icon" type="image/png" href="/images/logo-main.png">
<link rel="preconnect" href="https://fonts.googleapis.com"><link rel="preconnect" href="https://fonts.gstatic.com" crossorigin>
<link rel="stylesheet" href="https://fonts.googleapis.com/css2?family=Bricolage+Grotesque:opsz,wght@12..96,500;12..96,800&family=DM+Sans:wght@400;500;700&display=swap">
<link rel="stylesheet" href="/style.css">
{ld(ORG)}{ld(schema) if schema else ''}
</head><body>
<a class="skip" href="#main">Skip to content</a>
<header class="site-header"><div class="wrap">
<a class="brand" href="/"><img src="/images/logo-main.png" alt="" width="56" height="56"><span>Lina S Lee<br>Cards and Goods</span></a>
<nav class="nav" aria-label="Main">{navhtml}</nav></div></header>
<main id="main">{body}</main>
<footer class="site-footer"><div class="wrap">
<div><img src="/images/logo-hand-painted.png" alt="Hand painted in New York" width="84" height="84">
<p>{e(C['brand'])}<br>Hand painted in {e(C['city'])}</p></div>
<div><h3>Shop</h3><ul>{''.join(f'<li><a href="/shop/{g["slug"]}/">{e(g["name"])}</a></li>' for g in GROUPS)}</ul></div>
<div><h3>Say hello</h3><ul><li><a href="mailto:{e(C['email'])}">{e(C['email'])}</a></li>
{f'<li><a href="{e(C["instagram"])}" rel="me">Instagram</a></li>' if C.get('instagram') else ''}
<li><a href="/find-me-in-nyc/">Find me in NYC</a></li></ul></div>
<p class="small">&copy; {datetime.date.today().year} Lina S Lee. All artwork is hand painted and copyrighted.</p>
</div></footer></body></html>"""


def note(p, lazy=True):
    badge = '<span class="badge sold">Sold out</span>' if p.get("soldOut") else (
        '<span class="badge sample">Sample</span>' if p.get("sample") else "")
    return (f'<a class="note" href="{p["url"]}">{badge}<div class="ph"><img src="/{p["image"]}" alt="{e(p["alt"])}" '
            f'width="900" height="1125"{" loading=\"lazy\"" if lazy else ""}></div>'
            f'<h3>{e(p["name"])}</h3><p class="price">{money(p)}</p></a>')


def tab(g):
    n = len(g["items"])
    return (f'<a class="tab" href="/shop/{g["slug"]}/" style="background:{g["color"]};color:{g["text"]}">'
            f'<span class="tab-label" style="color:{g["text"]}">{e(g["short"])}</span>'
            f'<h3>{e(g["name"])}</h3><p>{e(g["blurb"])} {n} design{"s" if n != 1 else ""}.</p></a>')


def upcoming():
    return sorted([ev for ev in EVENTS if ev.get("date", "9999") >= TODAY], key=lambda x: x["date"])


def pretty(d):
    return datetime.date.fromisoformat(d).strftime("%a, %b %-d, %Y")


# ---------- home ----------
feat = [p for p in PRODUCTS if p.get("featured")] or PRODUCTS
hero_p = feat[0] if feat else None
hero_art = (f'<div class="hero-art"><a class="note" href="{hero_p["url"]}"><div class="ph"><img src="/{hero_p["image"]}" '
            f'alt="{e(hero_p["alt"])}" width="900" height="1125"></div><h3>{e(hero_p["name"])}</h3></a>'
            f'<img class="stamp" src="/images/logo-hand-painted.png" alt="Hand painted in New York" width="130" height="130"></div>'
            if hero_p else "")
ev = upcoming()[:3]
ev_html = ""
if ev:
    ev_html = ('<section><div class="wrap"><div class="section-head"><h2>Find me in person</h2>'
               '<a class="text-link" href="/find-me-in-nyc/">All dates</a></div><ul class="events">' +
               "".join(f'<li><span class="d">{pretty(x["date"])}</span><span><strong>{e(x["name"])}</strong><br>{e(x.get("location",""))}</span></li>' for x in ev) +
               "</ul></div></section>")
home_body = f"""
<section class="hero"><div class="wrap"><div>
<h1>{e(C['tagline'])}</h1>
<p class="lede">{e(C['homeIntro'])}</p>
<div class="btn-row"><a class="btn" href="/shop/">Shop the cards</a><a class="btn" href="/find-me-in-nyc/">Find me in NYC</a></div></div>
{hero_art}</div></section>
<section class="tabs"><div class="wrap"><div class="section-head"><h2>Pick a pile</h2></div>
{''.join(tab(g) for g in GROUPS)}</div></section>
<section><div class="wrap"><div class="section-head"><h2>New in the shop</h2><a class="text-link" href="/shop/">See everything</a></div>
<div class="grid">{''.join(note(p) for p in PRODUCTS[:8])}</div></div></section>
<section><div class="wrap two-col"><div class="prose"><h2>One painter, one table, many small batches</h2>
<p>{e(C['aboutParagraphs'][0])}</p><p><a class="text-link" href="/about/">More about Lina</a></p></div>
<img src="/images/logo-hand-painted.png" alt="Hand painted in New York badge" width="320" height="320" style="max-width:320px;margin:auto" loading="lazy"></div></section>
{ev_html}"""
home_schema = {"@context": "https://schema.org", "@type": "WebSite", "name": C["brand"], "url": SITE}
write("/", layout("/", f"Handmade Hand-Painted Cards | NYC Local Artist | {C['shortName']}",
                  "Handmade greeting cards, notebooks and goods hand painted in New York by local artist Lina S Lee. Shop online or find me at NYC craft fairs.",
                  home_body, home_schema, hero_p["image"] if hero_p else None))

# ---------- shop hub ----------
hub = f"""<div class="page-head"><div class="wrap"><h1>Shop</h1><p class="prose">Every card is hand painted in New York. Pick a pile to start.</p></div></div>
<section class="tabs"><div class="wrap">{''.join(tab(g) for g in GROUPS)}</div></section>
<section><div class="wrap"><div class="section-head"><h2>All pieces</h2></div><div class="grid">{''.join(note(p) for p in PRODUCTS)}</div></div></section>"""
write("/shop/", layout("/shop/", "Shop Handmade Hand-Painted Cards & Goods | NYC Artist | Lina S Lee",
                       "Shop hand-painted greeting cards, notebooks and small goods made in New York by local artist Lina S Lee.",
                       hub, crumbs([("Home", "/"), ("Shop", "/shop/")])))

# ---------- category pages ----------
for g in GROUPS:
    u = f"/shop/{g['slug']}/"
    body = f"""<div class="page-head colored" style="background:{g['color']};color:{g['text']}"><div class="wrap">
<p class="crumbs" style="color:inherit"><a href="/shop/">Shop</a> / {e(g['short'])}</p><h1>{e(g['h1'])}</h1></div></div>
<section><div class="wrap"><div class="prose">{''.join(f'<p>{e(t)}</p>' for t in g['intro'])}</div></div></section>
<section style="padding-top:0"><div class="wrap"><div class="grid">{''.join(note(p, False) for p in g['items'])}</div></div></section>"""
    schema = {"@context": "https://schema.org", "@type": "CollectionPage", "name": g["h1"], "url": SITE + u}
    write(u, layout(u, g["seoTitle"], g["metaDesc"], body,
                    {"@graph": [schema, crumbs([("Home", "/"), ("Shop", "/shop/"), (g["name"], u)])]}, g["items"][0]["image"]))

# ---------- product pages ----------
for p in PRODUCTS:
    g = p["group"]
    kind = "card" if p["type"] == "card" else p["type"].replace("tshirt", "t-shirt")
    title = f"{p['name']} | Hand-Painted in NYC | {C['shortName']}"
    desc = (p["description"] if not p.get("sample") else f"{p['name']}, hand painted in New York by Lina S Lee.")[:155]
    facts = "".join(f"<li><span>{e(k)}</span><span>{e(v)}</span></li>" for k, v in p.get("details", []))
    facts = f'<ul class="facts">{facts}</ul>' if facts else ""
    if p.get("soldOut"):
        buy = '<span class="btn dark disabled" aria-disabled="true">Sold out</span>'
    elif p.get("paymentLink"):
        buy = f'<a class="btn dark" href="{e(p["paymentLink"])}" rel="noopener">Buy now</a>'
    else:
        sub = e(f"Order: {p['name']}")
        buy = f'<a class="btn dark" href="mailto:{e(C["email"])}?subject={sub}">Email to order</a>'
    body = f"""<section><div class="wrap"><p class="crumbs"><a href="/shop/">Shop</a> / <a href="/shop/{g['slug']}/">{e(g['short'])}</a> / {e(p['name'])}</p>
<div class="product"><div class="photo"><img src="/{p['image']}" alt="{e(p['alt'])}" width="900" height="1125"></div>
<div><h1>{e(p['name'])}</h1><p class="price">{money(p)}</p>
<p>{e(p['description'])}</p>{facts}
<p>Hand painted in {e(C['city'])} by Lina S Lee.</p>
<div class="btn-row">{buy}<a class="btn dark" style="background:transparent;color:var(--cobalt)" href="/shop/{g['slug']}/">More {e(g['short'].lower())}</a></div></div></div></div></section>"""
    prod = {"@type": "Product", "name": p["name"], "description": p["description"], "image": f"{SITE}/{p['image']}",
            "brand": {"@type": "Brand", "name": C["brand"]}, "category": kind}
    if p.get("price") not in (None, ""):
        prod["offers"] = {"@type": "Offer", "priceCurrency": "USD", "price": str(p["price"]),
                          "url": SITE + p["url"], "availability": "https://schema.org/" + ("OutOfStock" if p.get("soldOut") else "InStock")}
    write(p["url"], layout(p["url"], title, desc, body,
                           {"@context": "https://schema.org", "@graph": [prod, crumbs([("Home", "/"), ("Shop", "/shop/"), (g["name"], f"/shop/{g['slug']}/"), (p["name"], p["url"])])]},
                           p["image"], og_type="product", noindex=bool(p.get("sample"))))

# ---------- about ----------
about = f"""<div class="page-head"><div class="wrap"><h1>About Lina S Lee</h1></div></div>
<section><div class="wrap two-col"><div class="prose">{''.join(f'<p>{e(t)}</p>' for t in C['aboutParagraphs'])}
<div class="btn-row"><a class="btn dark" href="/shop/">Shop</a><a class="btn dark" href="/contact/">Say hello</a></div></div>
<img src="/images/logo-main.png" alt="Lina S Lee Cards and Goods logo" width="360" height="360" style="max-width:360px;margin:auto"></div></section>"""
write("/about/", layout("/about/", "About Lina S Lee | Hand-Painted Card Artist in New York",
                        "Meet Lina S Lee, a New York artist who hand paints greeting cards, notebooks and goods in small batches.",
                        about, {"@context": "https://schema.org", "@type": "AboutPage", "mainEntity": {"@type": "Person", "name": "Lina S Lee", "jobTitle": "Artist", "address": {"@type": "PostalAddress", "addressLocality": "New York", "addressRegion": "NY"}}}))

# ---------- find me ----------
evs = upcoming()
if evs:
    lst = '<ul class="events">' + "".join(
        f'<li><span class="d">{pretty(x["date"])}</span><span><strong>{e(x["name"])}</strong><br>{e(x.get("location",""))}'
        f'{"<br>" + e(x["details"]) if x.get("details") else ""}'
        f'{"<br><a href=\"" + e(x["url"]) + "\">Event details</a>" if x.get("url") else ""}</span></li>' for x in evs) + "</ul>"
else:
    lst = f'<p>No market dates posted yet. Email <a href="mailto:{e(C["email"])}">{e(C["email"])}</a> and I will let you know when the next one is.</p>'
ev_schema = [{"@context": "https://schema.org", "@type": "Event", "name": f"{x['name']} (Lina S Lee, vendor)", "startDate": x["date"],
              "eventAttendanceMode": "https://schema.org/OfflineEventAttendanceMode",
              "location": {"@type": "Place", "name": x.get("location", "New York, NY"), "address": x.get("location", "New York, NY")}} for x in evs]
fm = f"""<div class="page-head"><div class="wrap"><h1>Find me in NYC</h1></div></div>
<section><div class="wrap"><div class="prose"><p>I sell hand-painted cards and goods at craft and maker markets around New York. Come say hi, pick a card in person, and meet the artist.</p></div>{lst}</div></section>"""
write("/find-me-in-nyc/", layout("/find-me-in-nyc/", "NYC Craft Fairs & Maker Markets | Lina S Lee Handmade Cards",
                                 "Where to find handmade, hand-painted cards by NYC artist Lina S Lee: upcoming craft fairs and maker markets in Manhattan and Brooklyn.",
                                 fm, ev_schema or None))

# ---------- faq ----------
faq = f"""<div class="page-head"><div class="wrap"><h1>Questions</h1></div></div><section><div class="wrap"><div class="prose faq">
{''.join(f'<details><summary>{e(f["q"])}</summary><p>{e(f["a"])}</p></details>' for f in C['faq'])}</div></div></section>"""
write("/faq/", layout("/faq/", "FAQ | Hand-Painted Cards by Lina S Lee, NYC", "Answers about ordering, custom cards and where to buy hand-painted cards by NYC artist Lina S Lee.", faq,
                      {"@context": "https://schema.org", "@type": "FAQPage", "mainEntity": [
                          {"@type": "Question", "name": f["q"], "acceptedAnswer": {"@type": "Answer", "text": f["a"]}} for f in C["faq"]]}))

# ---------- contact ----------
if C.get("formspreeUrl"):
    form = (f'<form action="{e(C["formspreeUrl"])}" method="post" class="card-paper"><p><label>Your name<br><input name="name" required></label></p>'
            '<p><label>Your email<br><input type="email" name="email" required></label></p>'
            '<p><label>Message<br><textarea name="message" rows="5" required></textarea></label></p><button class="btn dark" type="submit">Send message</button></form>')
else:
    form = f'<p><a class="btn dark" href="mailto:{e(C["email"])}">Email {e(C["email"])}</a></p>'
contact = f"""<div class="page-head"><div class="wrap"><h1>Contact</h1></div></div><section><div class="wrap two-col"><div class="prose">
<p>Questions, custom cards, or a bigger order for an event or shop? Send a note with the theme, the occasion and how many you need.</p>{form}</div></div></section>"""
write("/contact/", layout("/contact/", "Contact & Custom Orders | Lina S Lee, NYC Card Artist", "Contact NYC artist Lina S Lee about custom hand-painted cards, wholesale and event orders.", contact))

# ---------- journal ----------
if POSTS:
    ps = sorted(POSTS, key=lambda x: x["date"], reverse=True)
    items = "".join(f'<li><span class="d">{pretty(x["date"])}</span><span><a href="/journal/{x["slug"]}/"><strong>{e(x["title"])}</strong></a><br>{e(x["description"])}</span></li>' for x in ps)
    write("/journal/", layout("/journal/", "Journal | Lina S Lee, NYC Hand-Painted Cards", "Notes from the studio and the craft fair table.",
                              f'<div class="page-head"><div class="wrap"><h1>Journal</h1></div></div><section><div class="wrap"><ul class="events">{items}</ul></div></section>'))
    for x in ps:
        u = f"/journal/{x['slug']}/"
        body = f'<div class="page-head"><div class="wrap"><h1>{e(x["title"])}</h1><p>{pretty(x["date"])}</p></div></div><section><div class="wrap prose">{"".join(f"<p>{e(t)}</p>" for t in x["body"])}</div></section>'
        write(u, layout(u, f"{x['title']} | {C['shortName']}", x["description"], body,
                        {"@context": "https://schema.org", "@type": "BlogPosting", "headline": x["title"], "datePublished": x["date"], "author": {"@type": "Person", "name": "Lina S Lee"}}, og_type="article"))

# ---------- 404, sitemap, robots ----------
write("/404.html", layout("/404.html", "Page not found | Lina S Lee", "This page does not exist.",
                          '<section><div class="wrap prose"><h1>That page is not here</h1><p>Try the <a href="/shop/">shop</a> or go back <a href="/">home</a>.</p></div></section>', noindex=True))
(DIST / "sitemap.xml").write_text('<?xml version="1.0" encoding="UTF-8"?>\n<urlset xmlns="http://www.sitemaps.org/schemas/sitemap/0.9">\n' +
                                  "".join(f"<url><loc>{SITE}{u}</loc><lastmod>{TODAY}</lastmod></url>\n" for u in PAGES if not any(
                                      p.get("sample") and p["url"] == u for p in PRODUCTS)) + "</urlset>\n")
(DIST / "robots.txt").write_text(f"User-agent: *\nAllow: /\nSitemap: {SITE}/sitemap.xml\n")
print(f"Built {len(PAGES)} pages into {DIST}")
