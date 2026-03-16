import unittest

from reverb_sold_links import (
    normalize_item_url,
    parse_listings_from_html,
    parse_listings_from_next_data,
)


class ParseListingsTests(unittest.TestCase):
    def test_excludes_brand_new_cards(self):
        html = '''
        <ul>
          <li data-test="listing-grid-card">
            <a href="/item/1000-old-guitar">Old Guitar</a>
            <span>Mint</span>
          </li>
          <li data-test="listing-grid-card">
            <a href="/item/2000-new-guitar">New Guitar</a>
            <span>Brand New</span>
          </li>
        </ul>
        '''
        links = parse_listings_from_html(html)
        self.assertEqual(links, ["https://reverb.com/item/1000-old-guitar?show_sold=true"])

    def test_fallback_excludes_brand_new_slug(self):
        html = '''
        <a href="/item/3000-vintage-bass">Vintage Bass</a>
        <a href="/item/4000-cool-guitar-brand-new">New Guitar</a>
        '''
        links = parse_listings_from_html(html)
        self.assertEqual(links, ["https://reverb.com/item/3000-vintage-bass?show_sold=true"])

    def test_preserves_existing_query(self):
        self.assertEqual(
            normalize_item_url('/item/1-something?foo=bar'),
            'https://reverb.com/item/1-something?foo=bar&show_sold=true',
        )

    def test_next_data_parse(self):
        html = '''
        <script id="__NEXT_DATA__" type="application/json">
        {"props":{"pageProps":{"listings":[
            {"id": 10, "slug": "vintage-guitar", "condition": {"display_name": "Excellent"}},
            {"id": 11, "slug": "new-guitar", "condition": {"display_name": "Brand New"}}
        ]}}}
        </script>
        '''
        links = parse_listings_from_next_data(html)
        self.assertEqual(links, ["https://reverb.com/item/10-vintage-guitar?show_sold=true"])


if __name__ == '__main__':
    unittest.main()
