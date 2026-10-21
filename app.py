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

# ==================================================
# ADMINISTRATION
# ==================================================

with st.expander("Administration"):

    uploaded_file = st.file_uploader(
        "Ladda upp ny exportfil",
        type=["csv"]
    )

    if uploaded_file is not None:

        if st.button("Läs in ny exportfil"):

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

            stock.to_csv(
                DATA_FILE,
                index=False
            )

            pd.DataFrame(
                columns=[
                    "Artikelnummer",
                    "Land",
                    "LRN",
                    "Plockat antal"
                ]
            ).to_csv(
                USED_FILE,
                index=False
            )

            st.success(
                "Ny fil inläst. Historik nollställd."
            )

# ==================================================
# KONTROLL
# ==================================================

if not os.path.exists(DATA_FILE):

    st.info(
        "Ladda upp en exportfil under Administration."
    )

    st.stop()

stock = pd.read_csv(
    DATA_FILE,
    low_memory=False
)

# ==================================================
# SÖKFÄLT
# ==================================================

st.subheader("Sök artikel")

col1, col2, col3 = st.columns(3)

with col1:

    item = st.text_input(
        "Artikelnummer"
    )

with col2:

    countries = sorted(
        stock["Country"]
        .dropna()
        .unique()
    )

    country = st.selectbox(
        "Land",
        countries
    )

with col3:

    qty = st.number_input(
        "Antal",
        min_value=1.0,
        step=1.0
    )

# ==================================================
# HÄMTA LRN
# ==================================================

if st.button("Hämta LRN"):

    search = stock[
        (stock["Item number"].astype(str) == item)
        &
        (stock["Country"] == country)
        &
        (stock["Remaining"] > 0)
    ].copy()

    if search.empty:

        st.warning(
            "Ingen träff hittades."
        )

    else:

        search["Export datum"] = pd.to_datetime(
            search["Export datum"],
            errors="coerce"
        )

        search = search.sort_values(
            "Export datum"
        )

        remaining = qty
        allocations = []

        for index, row in search.iterrows():

            available = row["Remaining"]

            if available <= 0:
                continue

            take = min(
                available,
                remaining
            )

            allocations.append(
                {
                    "row_index": index,
                    "LRN": row["EXPORT ID"],
                    "Antal": take
                }
            )

            remaining -= take

            if remaining <= 0:
                break

        st.session_state["allocations"] = allocations
        st.session_state["item"] = item
        st.session_state["country"] = country

# ==================================================
# VISA FÖRSLAG
# ==================================================

if "allocations" in st.session_state:

    result = pd.DataFrame(
        st.session_state["allocations"]
    )

    st.subheader(
        "Föreslagna tullid"
    )

    st.dataframe(
        result[
            [
                "LRN",
                "Antal"
            ]
        ],
        use_container_width=True
    )

    if st.button("Plocka"):

        used_rows = []

        for row in st.session_state["allocations"]:

            stock.loc[
                row["row_index"],
                "Remaining"
            ] = (
                stock.loc[
                    row["row_index"],
                    "Remaining"
                ]
                -
                row["Antal"]
            )

            used_rows.append(
                {
                    "Artikelnummer":
                    st.session_state["item"],

                    "Land":
                    st.session_state["country"],

                    "LRN":
                    row["LRN"],

                    "Plockat antal":
                    row["Antal"]
                }
            )

        stock = stock[
            stock["Remaining"] > 0
        ]

        stock.to_csv(
            DATA_FILE,
            index=False
        )

        if os.path.exists(
            USED_FILE
        ):

            used = pd.read_csv(
                USED_FILE
            )

        else:

            used = pd.DataFrame()

        used = pd.concat(
            [
                used,
                pd.DataFrame(
                    used_rows
                )
            ],
            ignore_index=True
        )

        used.to_csv(
            USED_FILE,
            index=False
        )

        del st.session_state["allocations"]

        st.success(
            "Plockning genomförd."
        )

        st.rerun()

# ==================================================
# STOCK
# ==================================================

st.subheader(
    "Aktuell stock"
)

st.dataframe(
    stock,
    use_container_width=True
)

# ==================================================
# ANVÄNDA TULLID
# ==================================================

if os.path.exists(USED_FILE):

    used = pd.read_csv(
        USED_FILE
    )

    st.subheader(
        "Använda tullid"
    )

    st.dataframe(
        used,
        use_container_width=True
    )

    st.download_button(
        label="Exportera använda tullid",
        data=used.to_csv(index=False),
        file_name="used_lrn.csv",
        mime="text/csv"
    )
