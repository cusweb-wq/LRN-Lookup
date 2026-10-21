import streamlit as st
import pandas as pd
import os

DATA_FILE = "current_stock.csv"
USED_FILE = "used_lrn.csv"

st.set_page_config(
    page_title="LRN Lookup",
    layout="wide"
)

st.title("LRN Lookup")

# ==========================
# Ladda upp ny fil
# ==========================

with st.expander("Administration"):

    uploaded_file = st.file_uploader(
        "Ladda upp ny exportfil",
        type=["csv"]
    )

    if uploaded_file:

        df = pd.read_csv(
            uploaded_file,
            sep=";",
            encoding="utf-8",
            low_memory=False
        )

        stock = (
            df.groupby(
                [
                    "Item number",
                    "Country",
                    "EXPORT ID",
                    "Export datum"
                ],
                as_index=False
            )["Transaction quantity"]
            .sum()
        )

        stock.rename(
            columns={
                "Transaction quantity": "Remaining"
            },
            inplace=True
        )

        stock.to_csv(DATA_FILE, index=False)

        pd.DataFrame(
            columns=[
                "Artikelnummer",
                "Land",
                "LRN",
                "Plockat antal"
            ]
        ).to_csv(USED_FILE, index=False)

        st.success("Ny fil inläst. Historik nollställd.")

# ==========================
# Kontroll
# ==========================

if not os.path.exists(DATA_FILE):

    st.info(
        "Ladda upp en exportfil under Administration."
    )

    st.stop()

stock = pd.read_csv(DATA_FILE)

# ==========================
# Sökning
# ==========================

col1, col2, col3 = st.columns(3)

with col1:
    item = st.text_input("Artikelnummer")

