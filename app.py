import sqlite3
import pandas as pd
import plotly.express as px
import streamlit as st

st.title("Satellite communications dashboard")


@st.cache_data
def load():
    con = sqlite3.connect("satcom.db")
    df = pd.read_sql("""
        SELECT s.name, s.launch_date, s.decay_date, s.ops_status,
               o.name AS owner, c.name AS country, c.esa_member
        FROM satellite s
        JOIN organisation o ON o.code = s.owner_code
        JOIN country c ON c.code = o.country_code""", con)
    con.close()
    df["year"] = df["launch_date"].str[:4].astype(int)
    df["active"] = df["ops_status"].isin(["+", "P", "B", "S", "X"])
    return df


df = load()

country = st.sidebar.selectbox("Country", ["All"] + sorted(df["country"].unique()))
owner = st.sidebar.selectbox("Owner", ["All"] + sorted(df["owner"].unique()))
years = st.sidebar.slider("Launch year", 1958, 2026, (2000, 2026))

data = df[(df["year"] >= years[0]) & (df["year"] <= years[1])]
if country != "All":
    data = data[data["country"] == country]
if owner != "All":
    data = data[data["owner"] == owner]

st.write("Satellites launched:", len(data))
st.write("Still active:", data["active"].sum())

per_year = data.groupby("year").size().reset_index(name="launched")
st.plotly_chart(px.bar(per_year, x="year", y="launched", title="Launched per year"))

top = data[data["active"]].groupby("owner").size().nlargest(10).reset_index(name="active")
st.plotly_chart(px.bar(top, x="active", y="owner", orientation="h", title="Top 10 owners (active satellites)"))

rows = []
for y in range(2016, 2026):
    end = f"{y}-12-31"
    in_orbit = df[(df["launch_date"] <= end) & (df["decay_date"].isna() | (df["decay_date"] > end))]
    rows.append({"year": y, "esa_share": round(100 * in_orbit["esa_member"].mean(), 1)})
st.plotly_chart(px.line(pd.DataFrame(rows), x="year", y="esa_share", title="ESA member states, share of satellites in orbit (%)"))

st.dataframe(data)