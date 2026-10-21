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
# FLERA ARTIKLAR
# ==================================================

st.subheader("Sök artiklar")

if "search_rows" not in st.session_state:
    st.session_state.search_rows = 1

for i in range(st.session_state.search_rows):

    st.markdown(f"### Artikel {i+1}")

    col1, col2, col3 = st.columns(3)

    with col1:
        st.text_input(
            "Artikelnummer",
            key=f"item_{i}"
        )

    with col2:

        countries = sorted(
            stock["Country"]
            .dropna()
            .unique()
        )

        st.selectbox(
            "Land",
            countries,
            key=f"country_{i}"
        )

    with col3:

        st.number_input(
            "Antal",
            min_value=1.0,
            step=1.0,
            key=f"qty_{i}"
        )

st.divider()

col1, col2 = st.columns(2)

with col1:

    if st.button("Lägg till fler"):

        st.session_state.search_rows += 1
        st.rerun()

with col2:

    search_all = st.button(
        "Sök alla"
    )

# ==================================================
# SÖK ALLA
# ==================================================

if search_all:

    all_allocations = []

    for i in range(
        st.session_state.search_rows
    ):

        item = st.session_state.get(
            f"item_{i}",
            ""
        )

        country = st.session_state.get(
            f"country_{i}",
            ""
        )

        qty = st.session_state.get(
            f"qty_{i}",
            0
        )

        if item == "":
            continue

        search = stock[
            (
                stock["Item number"]
                .astype(str)
                ==
                str(item)
            )
            &
            (
                stock["Country"]
                ==
                country
            )
            &
            (
                stock["Remaining"]
                >
                0
            )
        ].copy()

        if search.empty:
            continue

        search["Export datum"] = pd.to_datetime(
            search["Export datum"],
            errors="coerce"
        )

        search = search.sort_values(
            "Export datum"
        )

        remaining = qty

        for index, row in search.iterrows():

            available = row["Remaining"]

            if available <= 0:
                continue

            take = min(
                available,
                remaining
            )

            all_allocations.append(
                {
                    "row_index": index,
                    "Artikelnummer": item,
                    "Land": country,
                    "LRN": row["EXPORT ID"],
                    "Antal": take
                }
            )

            remaining -= take

            if remaining <= 0:
                break

    st.session_state["allocations"] = (
        all_allocations
    )

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
                "Artikelnummer",
                "Land",
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
                    row["Artikelnummer"],

                    "Land":
                    row["Land"],

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
