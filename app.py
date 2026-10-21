import streamlit as st
import pandas as pd
import os

DATA_FILE = "current_stock.csv"
USED_FILE = "used_lrn.csv"

st.set_page_config(
    page_title="LRN Lookup",
    layout="wide"
)

st.markdown("""
<style>

@import url('https://fonts.googleapis.com/css2?family=Inter:wght@300;400;500;600;700&display=swap');

html, body, [class*="css"] {
    font-family: 'Inter', sans-serif !important;
}

/* Background */
.stApp {
    background: linear-gradient(180deg, #071220 0%, #0F1D34 100%);
}

/* Text */
h1, h2, h3,
label {
    color: white !important;
}

p {
    color: #d7dce3;
}

/* KPI Cards */
.metric-card {
    background: #14233f;
    padding: 20px;
    border-radius: 12px;
    border-left: 4px solid #00AAE7;
    text-align: center;
}

.metric-title {
    color: #AFC1D6;
    font-size: 14px;
}

.metric-value {
    color: white;
    font-size: 28px;
    font-weight: bold;
}

/* Buttons */
.stButton button {
    background-color: #00AAE7 !important;
    color: white !important;
    border: none !important;
    border-radius: 10px !important;
    font-weight: 600 !important;
    height: 45px !important;
}

.stButton button:hover {
    background-color: #0091c8 !important;
}

/* Tables */
[data-testid="stDataFrame"] {
    background-color: white;
    border-radius: 10px;
    padding: 5px;
}

/* Expanders */
.streamlit-expanderHeader {
    color: white !important;
    font-weight: bold !important;
}

/* Inputs */
input {
    border-radius: 8px !important;
}

/* Header */
.main-header {
    background: linear-gradient(90deg, #08213D, #0B335E);
    padding: 30px;
    border-radius: 15px;
    margin-bottom: 20px;
}

.main-title {
    color: white;
    font-size: 32px;
    font-weight: 700;
}

.main-subtitle {
    color: #c7d2df;
    font-size: 16px;
}

</style>
""", unsafe_allow_html=True)

st.markdown("""
<div class="main-header">
    <div class="main-title">
        EPIROC RETURN LOOKUP
    </div>
    <div class="main-subtitle">
        Customs Support Group • Import Operations
    </div>
</div>
""", unsafe_allow_html=True)

# ==================================================
# HJÄLPFUNKTIONER
# ==================================================

def normalize_item(value):

    try:

        value = str(value).strip()

        if value.endswith(".0"):
            value = value[:-2]

        return value

    except:

        return str(value)

# ==================================================
# ADMIN
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

            df["Item number"] = (
                df["Item number"]
                .astype(str)
                .apply(normalize_item)
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

stock["Item number"] = (
    stock["Item number"]
    .astype(str)
    .apply(normalize_item)
)
active_lrn = stock["EXPORT ID"].nunique()
active_items = stock["Item number"].nunique()
active_countries = stock["Country"].nunique()

used_count = 0

if os.path.exists(USED_FILE):
    try:
        used_count = len(pd.read_csv(USED_FILE))
    except:
        pass

c1, c2, c3, c4 = st.columns(4)

with c1:
    st.markdown(
        f'''
        <div class="metric-card">
            <div class="metric-title">
                Artiklar
            </div>
            <div class="metric-value">
                {active_items}
            </div>
        </div>
        ''',
        unsafe_allow_html=True
    )

with c2:
    st.markdown(
        f'''
        <div class="metric-card">
            <div class="metric-title">
                Aktiva LRN
            </div>
            <div class="metric-value">
                {active_lrn}
            </div>
        </div>
        ''',
        unsafe_allow_html=True
    )

with c3:
    st.markdown(
        f'''
        <div class="metric-card">
            <div class="metric-title">
                Länder
            </div>
            <div class="metric-value">
                {active_countries}
            </div>
        </div>
        ''',
        unsafe_allow_html=True
    )

with c4:
    st.markdown(
        f'''
        <div class="metric-card">
            <div class="metric-title">
                Använda tullid
            </div>
            <div class="metric-value">
                {used_count}
            </div>
        </div>
        ''',
        unsafe_allow_html=True
    )
# ==================================================
# SÖKRADER
# ==================================================

st.subheader("Sök artiklar")

if "search_rows" not in st.session_state:
    st.session_state.search_rows = 1

countries = sorted(
    stock["Country"]
    .dropna()
    .unique()
)

for i in range(
    st.session_state.search_rows
):

    c1, c2, c3 = st.columns([4, 2, 2])

    with c1:

        st.text_input(
            f"Artikelnummer {i+1}",
            key=f"item_{i}"
        )

    with c2:

        st.selectbox(
            f"Land {i+1}",
            countries,
            key=f"country_{i}"
        )

    with c3:

        st.number_input(
            f"Antal {i+1}",
            min_value=1.0,
            step=1.0,
            key=f"qty_{i}"
        )

col1, col2 = st.columns(2)

with col1:

    if st.button("➕ Lägg till rad"):

        st.session_state.search_rows += 1
        st.rerun()

with col2:

    search_all = st.button(
        "🔍 Sök alla"
    )

# ==================================================
# SÖKNING
# ==================================================

if search_all:

    allocations = []

    missing_items = []

    for i in range(
        st.session_state.search_rows
    ):

        item = normalize_item(
            st.session_state.get(
                f"item_{i}",
                ""
            )
        )

        if item == "":
            continue

        country = st.session_state.get(
            f"country_{i}"
        )

        qty = st.session_state.get(
            f"qty_{i}"
        )

        search = stock[
            (
                stock["Item number"]
                ==
                item
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

            missing_items.append(
                f"{item} ({country})"
            )

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

            take = min(
                available,
                remaining
            )

            allocations.append(
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

    st.session_state["allocations"] = allocations
    st.session_state["missing_items"] = missing_items

# ==================================================
# RESULTAT
# ==================================================

if "missing_items" in st.session_state:

    if len(
        st.session_state["missing_items"]
    ) > 0:

        st.warning(
            "Följande artiklar hittades inte:\n\n"
            +
            "\n".join(
                st.session_state[
                    "missing_items"
                ]
            )
        )

if "allocations" in st.session_state:

    allocations = (
        st.session_state[
            "allocations"
        ]
    )

    if len(allocations) == 0:

        st.info(
            "Inga tullid hittades."
        )

    else:

        result = pd.DataFrame(
            allocations
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

        if st.button(
            "✅ Plocka alla"
        ):

            used_rows = []

            for row in allocations:

                stock.loc[
                    row["row_index"],
                    "Remaining"
                ] -= row["Antal"]

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

            del st.session_state[
                "allocations"
            ]

            st.success(
                "Plockning genomförd."
            )

            st.rerun()

# ==================================================
# STOCK
# ==================================================

with st.expander(
    "📦 Aktuell stock",
    expanded=False
):

    st.dataframe(
        stock,
        use_container_width=True
    )

# ==================================================
# HISTORIK
# ==================================================

#if os.path.exists(
 #   USED_FILE
#):

 #   used = pd.read_csv(
  #      USED_FILE
 #   )

with st.expander(
    "📋 Använda tullid",
    expanded=False
):

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
