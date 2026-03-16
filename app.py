import io
from typing import List

import streamlit as st

from reverb_sold_links import FetchConfig, collect_links


st.set_page_config(page_title="Reverb Sold Links Collector", page_icon="🎸", layout="wide")
st.title("🎸 Reverb Sold Links Collector")
st.caption("Collect sold Reverb item links while excluding Brand New listings.")

with st.sidebar:
    st.header("Filters")
    count = st.selectbox("How many links", options=[100, 500, 1000], index=0)
    min_price = st.number_input("Minimum price (USD)", min_value=0, value=10000, step=100)
    use_max = st.checkbox("Use maximum price")
    max_price = st.number_input("Maximum price (USD)", min_value=0, value=20000, step=100, disabled=not use_max)
    start_page = st.number_input("Start page", min_value=1, value=1, step=1)
    query = st.text_input("Search query (optional)", value="")
    delay = st.slider("Delay between requests (seconds)", min_value=0.0, max_value=2.0, value=0.25, step=0.05)

run = st.button("Get sold links", type="primary")

if run:
    if use_max and min_price > max_price:
        st.error("Minimum price cannot be greater than maximum price.")
    else:
        config = FetchConfig(
            count=int(count),
            min_price=int(min_price),
            max_price=int(max_price) if use_max else None,
            query=query,
            start_page=int(start_page),
            delay=float(delay),
        )

        with st.spinner("Collecting links from Reverb..."):
            links: List[str] = collect_links(config)

        if not links:
            st.warning(
                "No links were returned. Reverb may have blocked the request from this environment, "
                "or no listings matched your filters."
            )
        else:
            st.success(f"Collected {len(links)} sold links.")
            st.text_area("Sold item links", value="\n".join(links), height=350)

            output = io.StringIO()
            output.write("\n".join(links))
            st.download_button(
                label="Download links as TXT",
                data=output.getvalue(),
                file_name="reverb_sold_links.txt",
                mime="text/plain",
            )

st.markdown("---")
st.markdown(
    "Example filter: `min price = 10000`, `count = 100`, `start page = 2` "
    "(similar to your marketplace URL)."
)
