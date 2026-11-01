# Lina S Lee Cards and Goods: site guide

## Add a new card or product
1. Crop the photo to 4:5 (portrait) and put it in `static/images/` (example: `peach-card.jpg`). Keep it under about 1200px wide.
2. Open `data/products.json` and copy one entry. Change:
   - `slug`: lowercase-with-dashes, unique (becomes the page address)
   - `name`, `description`, `alt` (describe the photo for search and screen readers)
   - `type`: `card`, `notebook`, `tshirt` or `scarf`
   - `theme`: cards only: `flowers`, `fruits`, `cats`, `dogs` or `wine`
   - `price`: a number like `6`, or `null` to show "Email for price"
   - `image`: `images/peach-card.jpg`
   - `paymentLink`: your Square or Stripe payment link (leave `""` for an "Email to order" button)
   - `soldOut`: `true` keeps the page up but turns off the buy button
   - `featured`: `true` puts it at the top of the homepage
   - optional `details`: `[["Size","5 x 7 in"],["Paper","Cotton"],["Envelope","Included"]]`
3. Save. The site rebuilds in about a minute. A category with no products has no page, so a new theme (like fruits) appears as soon as you add its first card.

## Add a market date
Add to `data/events.json`:
`{"date":"2026-12-06","name":"Market name","location":"Address, Brooklyn, NY","details":"Booth 12","url":"https://..."}`
Past dates hide automatically.

## Before going live
- `data/site.config.json`: set `siteUrl` (your real domain), `email`, `instagram`.
- Add prices, sizes and paper details to the three products.

## Publish for free (Cloudflare Pages)
Upload this folder to a GitHub repo. In Cloudflare Pages: connect the repo, build command `python3 build.py`, output directory `dist`. Add your domain under Custom domains. Then submit `/sitemap.xml` in Google Search Console.

Preview locally: run `python3 build.py`, then serve the `dist` folder with any static server.
