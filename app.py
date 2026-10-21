import streamlit as st
import pandas as pd

st.set_page_config(page_title="LRN Lookup", layout="wide")

st.title("LRN Lookup")

uploaded_file = st.file_uploader(
    "Ladda upp exportfil (.csv)",
    type=["csv"]
)

if uploaded_file:

    df = pd.read_csv(
    uploaded_file,
    sep=";",
    encoding="utf-8",
    low_memory=False
)

    required_cols = [
        "Country",
        "Transaction quantity",
        "Item number",
        "EXPORT ID",
        "Export datum"
    ]

    missing = [c for c in required_cols if c not in df.columns]

    if missing:
        st.error(f"Saknade kolumner: {missing}")
        st.stop()

    exports = (
        df.groupby(
            ["Item number", "Country", "EXPORT ID", "Export datum"],
            as_index=False
        )["Transaction quantity"]
        .sum()
    )

    col1, col2, col3 = st.columns(3)

    with col1:
        item = st.text_input("Artikelnummer")

    with col2:
        countries = sorted(exports["Country"].dropna().unique())
        country = st.selectbox("Land", countries)

    with col3:
        qty = st.number_input(
            "Antal",
            min_value=1.0,
            step=1.0
        )

    if st.button("Hämta LRN"):

        search = exports[
            (exports["Item number"].astype(str) == item)
            & (exports["Country"] == country)
        ].copy()

        if search.empty:
            st.warning("Ingen träff hittades.")
            st.stop()

        try:
            search["Export datum"] = pd.to_datetime(
                search["Export datum"]
            )
        except:
            pass

        search = search.sort_values("Export datum")

        remaining = qty
        allocations = []

        for _, row in search.iterrows():

            available = row["Transaction quantity"]

            if available <= 0:
                continue

            take = min(available, remaining)

            allocations.append({
                "LRN": row["EXPORT ID"],
                "Antal": take
            })

            remaining -= take

            if remaining <= 0:
                break

        if len(allocations) == 0:
            st.error("Inga kvantiteter tillgängliga.")
        else:
            st.success("LRN hittades")

            result = pd.DataFrame(allocations)

            st.dataframe(
                result,
                use_container_width=True
            )

            if remaining > 0:
                st.warning(
                    f"Saknar {remaining} st för att täcka hela behovet."
                )
