# Reverb Sold Links Tool 

<<<<<< codex/create-tool-to-retrieve-sold-reverb-products-lj3rel
This repo includes:
- a **CLI tool** (`reverb_sold_links.py`)
- a **Streamlit web app** (`app.py`)

Both collect links to **sold** Reverb listings while excluding **Brand New** items.
=======
This repo includes a CLI tool that collects links to **sold** Reverb listings while excluding **Brand New** items.
>>>>>> main

## Requirements

- Python 3.9+
<<<<<< codex/create-tool-to-retrieve-sold-reverb-products-lj3rel
- `streamlit` (for the web UI only)

## Streamlit app (works on streamlit.app)

Local run:

```bash
pip install -r requirements.txt
streamlit run app.py
```

On Streamlit Community Cloud:
- Main file path: `app.py`
- Dependencies file: `requirements.txt`

## CLI usage
=======
- No third-party packages required

## Usage
>>>>>> main

```bash
python reverb_sold_links.py --count 100 --min-price 10000
```

### Common examples

Get 500 sold items over $5,000:

```bash
python reverb_sold_links.py --count 500 --min-price 5000
```

Get 1000 sold items in a price range ($3,000 to $12,000), save to file:

```bash
python reverb_sold_links.py --count 1000 --min-price 3000 --max-price 12000 --output sold_links.txt
```

Start from page 2 (similar to your example link):

```bash
python reverb_sold_links.py --count 100 --min-price 10000 --start-page 2
```

## Output format

The tool prints one item URL per line, like:

```text
https://reverb.com/item/91347312-mint-martin-d-42-modern-deluxe-acoustic-guitar-136?show_sold=true
https://reverb.com/item/91347270-mint-taylor-50th-anniversary-924ce-k-ltd-36-month-no-interest-financing-circa-74-amp-limited-099?show_sold=true
```

## Notes

- `--count` must be one of: `100`, `500`, `1000`.
- Filtering out Brand New items is done by listing metadata from marketplace cards, with URL-based fallback filtering.
- If Reverb rate-limits or blocks requests, the tool may return fewer results.
