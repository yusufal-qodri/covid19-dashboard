import os
import streamlit as st
import pandas as pd
import plotly.express as px

# ==============================
# PAGE CONFIG
# ==============================
st.set_page_config(
    page_title="COVID-19 Global Analytics Dashboard",
    layout="wide"
)

# ==============================
# LOAD DATA (CACHED)
# ==============================
@st.cache_data
def load_data():
    path = os.path.join("data", "covid_clean.csv.gz")

    df = pd.read_csv(
        path,
        compression="gzip",
        parse_dates=["tanggal"]
    )

    # Pastikan tipe data numerik
    df["kasus_harian"] = pd.to_numeric(df["kasus_harian"], errors="coerce")
    df["kasus_kumulatif"] = pd.to_numeric(df["kasus_kumulatif"], errors="coerce")

    return df


df = load_data()

# ==============================
# SIDEBAR - FILTERS
# ==============================
st.sidebar.title("Filter Data")

negara_list = sorted(df["negara"].unique())
default_negara = ["Indonesia", "US", "India"]

negara_selected = st.sidebar.multiselect(
    "Pilih Negara",
    negara_list,
    default=[n for n in default_negara if n in negara_list]
)

min_date = df["tanggal"].min()
max_date = df["tanggal"].max()

date_range = st.sidebar.date_input(
    "Rentang Tanggal",
    [min_date, max_date],
    min_value=min_date,
    max_value=max_date
)

# ==============================
# FILTER DATA
# ==============================
df_filtered = df[
    (df["negara"].isin(negara_selected)) &
    (df["tanggal"] >= pd.to_datetime(date_range[0])) &
    (df["tanggal"] <= pd.to_datetime(date_range[1]))
].copy()

# ==============================
# HEADER
# ==============================
st.title("COVID-19 Global Analytics Dashboard")
st.markdown(
    """
    Dashboard ini menyajikan analisis perkembangan COVID-19 secara global,
    mencakup tren kasus harian dan distribusi geografis antar negara.
    """
)

# ==============================
# KPI SECTION
# ==============================
latest_date = df_filtered["tanggal"].max()

total_cases = int(df_filtered["kasus_kumulatif"].max())
avg_daily = int(df_filtered["kasus_harian"].mean())
total_countries = df_filtered["negara"].nunique()

col1, col2, col3 = st.columns(3)

col1.metric("Total Kasus", f"{total_cases:,}")
col2.metric("Rata-rata Kasus Harian", f"{avg_daily:,}")
col3.metric("Jumlah Negara", total_countries)

st.divider()

# ==============================
# MAP - GLOBAL DISTRIBUTION
# ==============================
st.subheader("Sebaran Global Kasus COVID-19")

df_map = (
    df_filtered[df_filtered["tanggal"] == latest_date]
    .groupby(["negara", "latitude", "longitude"], as_index=False)
    .agg({"kasus_kumulatif": "max"})
)

fig_map = px.scatter_geo(
    df_map,
    lat="latitude",
    lon="longitude",
    size="kasus_kumulatif",
    color="kasus_kumulatif",
    hover_name="negara",
    size_max=50,
    projection="natural earth",
    title=f"Sebaran Kasus COVID-19 Global (per {latest_date.date()})",
    color_continuous_scale="Reds"
)

st.plotly_chart(fig_map, use_container_width=True)

st.markdown(
    """
    **Insight:**  
    Peta menunjukkan pola distribusi kasus COVID-19 yang tidak merata secara global. 
    Titik-titik dengan ukuran besar (kasus tinggi) terkonsentrasi di wilayah dengan 
    populasi padat dan mobilitas tinggi seperti Amerika Serikat, India, dan Brasil. 
    Distribusi ini mencerminkan bagaimana faktor kepadatan penduduk dan konektivitas global 
    mempercepat penyebaran virus dibandingkan negara-negara dengan populasi lebih kecil 
    atau lokasi yang lebih terisolasi.
    """
)

st.divider()

# ==============================
# TIME SERIES - TREND KASUS HARIAN
# ==============================
st.subheader("Tren Kasus Harian COVID-19")

fig_trend = px.line(
    df_filtered,
    x="tanggal",
    y="kasus_harian",
    color="negara",
    title="Tren Kasus Harian COVID-19 (Data Aktual)",
    labels={
        "kasus_harian": "Kasus Harian",
        "tanggal": "Tanggal"
    },
    line_shape="spline"
)

st.plotly_chart(fig_trend, use_container_width=True)

# ==============================
# DYNAMIC INSIGHT - TREND KASUS HARIAN
# ==============================
# Temukan puncak kasus harian tertinggi
if not df_filtered.empty:
    peak_global = df_filtered.loc[df_filtered["kasus_harian"].idxmax()]
    negara_peak = peak_global["negara"]
    tanggal_peak = peak_global["tanggal"].strftime("%d %B %Y")
    nilai_peak = int(peak_global["kasus_harian"])
    
    # Analisis tren terkini
    latest_data = df_filtered[df_filtered["tanggal"] == latest_date]
    trend_analysis = []
    
    for negara in negara_selected:
        country_data = df_filtered[df_filtered["negara"] == negara]
        if len(country_data) >= 7:
            latest_week = country_data.tail(7)["kasus_harian"].mean()
            prev_week = country_data.tail(14).head(7)["kasus_harian"].mean()
            
            if prev_week > 0:
                change_pct = ((latest_week - prev_week) / prev_week) * 100
                if change_pct > 20:
                    trend = f"meningkat {change_pct:.0f}%"
                elif change_pct < -20:
                    trend = f"menurun {abs(change_pct):.0f}%"
                else:
                    trend = "stabil"
                trend_analysis.append(f"{negara} ({trend})")
    
    trend_text = ", ".join(trend_analysis) if trend_analysis else "tidak cukup data untuk analisis tren"
    
    st.markdown(
        f"""
        **Insight Tren Kasus Harian:**  
        **{negara_peak}** mencatat **rekor kasus harian tertinggi** pada **{tanggal_peak}** dengan **{nilai_peak:,} kasus dalam satu hari**. 
        Puncak ini terjadi karena kombinasi faktor: varian baru yang lebih menular, pelonggaran pembatasan sosial, 
        atau peningkatan kapasitas testing. Analisis tren 7 hari terakhir menunjukkan: {trend_text}. 
        Fluktuasi kasus harian yang tajam menunjukkan sensitivitas pandemi terhadap perubahan kebijakan 
        dan perilaku masyarakat.
        """
    )
else:
    st.info("Tidak ada data yang tersedia untuk analisis tren.")

st.divider()

# ==============================
# PEAK ANALYSIS - DATA HARIAN
# ==============================
st.subheader("Rekor Kasus Harian Tertinggi per Negara")

if not df_filtered.empty:
    df_peak = (
        df_filtered
        .loc[df_filtered.groupby("negara")["kasus_harian"].idxmax()]
        .sort_values("kasus_harian", ascending=False)
    )
    
    df_peak_display = df_peak[[
        "negara", "tanggal", "kasus_harian"
    ]].rename(columns={
        "negara": "Negara",
        "tanggal": "Tanggal Rekor",
        "kasus_harian": "Kasus Harian Tertinggi"
    })
    
    st.dataframe(
        df_peak_display,
        use_container_width=True
    )
    
    # Analisis pola waktu rekor
    if len(df_peak) > 1:
        # Konversi tanggal ke quarter
        df_peak["quarter"] = df_peak["tanggal"].dt.to_period("Q")
        quarter_counts = df_peak["quarter"].value_counts().sort_index()
        
        peak_quarter = quarter_counts.idxmax().strftime("Q%q %Y")
        peak_count = quarter_counts.max()
        
        # Hitung rentang waktu antar rekor
        date_range_days = (df_peak["tanggal"].max() - df_peak["tanggal"].min()).days
        
        st.markdown(
            f"""
            **Insight Analisis Rekor Harian:**  
            Negara-negara mencapai rekor kasus harian dalam rentang **{date_range_days} hari**, 
            dengan konsentrasi tertinggi pada **{peak_quarter}** ({peak_count} negara). 
            Perbedaan waktu pencapaian rekor ini menunjukkan: (1) Gelombang pandemi yang tidak sinkron, 
            (2) Efektivitas respons awal yang berbeda, (3) Waktu masuknya varian baru yang bervariasi. 
            Negara dengan rekor lebih awal cenderung mengalami gelombang pertama lebih cepat, 
            sementara yang lebih lambat mungkin mendapat manfaat dari pembelajaran negara lain.
            """
        )
else:
    st.info("Tidak ada data untuk analisis rekor harian.")

st.divider()

# ==============================
# KONTRIBUSI GLOBAL - DATA KUMULATIF
# ==============================
st.subheader("Kontribusi Kasus COVID-19 terhadap Total Dunia (%)")

# Tanggal global terbaru
latest_global_date = df["tanggal"].max()

# Data global (TIDAK TERFILTER SIDEBAR)
df_global_pie = (
    df[df["tanggal"] == latest_global_date]
    .groupby("negara", as_index=False)
    .agg({"kasus_kumulatif": "max"})
)

# Hitung total global
total_global_cases = df_global_pie["kasus_kumulatif"].sum()
df_global_pie["persentase"] = (
    df_global_pie["kasus_kumulatif"] / total_global_cases * 100
)

# Ambil top 10 negara
top_n = 10
df_top = df_global_pie.sort_values(
    "kasus_kumulatif", ascending=False
).head(top_n)

df_others = pd.DataFrame({
    "negara": ["Lainnya"],
    "kasus_kumulatif": [
        total_global_cases - df_top["kasus_kumulatif"].sum()
    ],
    "persentase": [
        100 - df_top["persentase"].sum()
    ]
})

df_pie_final = pd.concat([df_top, df_others], ignore_index=True)

# Pie (Donut) chart
fig_pie = px.pie(
    df_pie_final,
    values="kasus_kumulatif",
    names="negara",
    hole=0.45,
    title=f"Distribusi Kasus COVID-19 Global (per {latest_global_date.date()})"
)

fig_pie.update_traces(
    textinfo="label+percent",
    hovertemplate="<b>%{label}</b><br>"
                  "Total Kasus: %{value:,}<br>"
                  "Kontribusi: %{percent}<extra></extra>"
)

fig_pie.update_layout(
    legend_title_text="Negara",
    margin=dict(t=80, b=40)
)

st.plotly_chart(fig_pie, use_container_width=True)

# Analisis distribusi kontribusi
if not df_top.empty:
    top5_contribution = df_top.head(5)["persentase"].sum()
    top10_contribution = df_top["persentase"].sum()
    
    # Hitung Gini coefficient sederhana
    sorted_pct = sorted(df_top["persentase"])
    n = len(sorted_pct)
    cum_sum = sum(sorted_pct)
    gini_numerator = sum((i + 1) * sorted_pct[i] for i in range(n))
    gini_coefficient = (2 * gini_numerator) / (n * cum_sum) - (n + 1) / n
    
    st.markdown(
        f"""
        **Insight Distribusi Global:**  
        **10 negara teratas** menyumbang **{top10_contribution:.1f}%** kasus global, 
        dengan **5 teratas** saja mencapai **{top5_contribution:.1f}%**. 
        Konsentrasi ekstrem ini (koefisien Gini: {gini_coefficient:.3f}) menunjukkan ketimpangan besar 
        dalam beban pandemi. Faktor penyebab: (1) Populasi besar (China, India), 
        (2) Mobilitas global tinggi (AS, Eropa), (3) Kapasitas testing yang berbeda, 
        (4) Kerentanan sistem kesehatan. "Lainnya" ({180-top_n}+ negara) hanya berkontribusi **{100-top10_contribution:.1f}%**, 
        yang bisa mengindikasikan keberhasilan pengendalian atau keterbatasan pelaporan.
        """
    )

st.divider()

# ==============================
# TOP 10 COUNTRIES - TOTAL KASUS
# ==============================
st.subheader("10 Negara dengan Total Kasus Tertinggi")

top10 = (
    df
    .groupby("negara")["kasus_kumulatif"]
    .max()
    .sort_values(ascending=False)
    .head(10)
    .reset_index()
)

fig_top10 = px.bar(
    top10,
    x="kasus_kumulatif",
    y="negara",
    orientation="h",
    title="10 Negara dengan Total Kasus COVID-19 Tertinggi",
    labels={"kasus_kumulatif": "Total Kasus", "negara": "Negara"},
    color="kasus_kumulatif",
    color_continuous_scale="Blues"
)

fig_top10.update_layout(
    yaxis=dict(categoryorder="total ascending"),
    height=500
)

st.plotly_chart(fig_top10, use_container_width=True)

# Analisis top 10
if not top10.empty:
    # Hitung rasio antara peringkat 1 dan 10
    ratio_1_to_10 = top10.iloc[0]["kasus_kumulatif"] / top10.iloc[9]["kasus_kumulatif"]
    
    # Hitung rata-rata kasus per kapita (estimasi)
    population_estimates = {
        "US": 331000000, "India": 1380000000, "Brazil": 213000000,
        "Russia": 146000000, "UK": 67000000, "France": 65000000,
        "Turkey": 84000000, "Italy": 60000000, "Spain": 47000000,
        "Germany": 83000000
    }
    
    # Hitung kasus per 1000 penduduk untuk negara yang ada data
    cases_per_capita = []
    for idx, row in top10.iterrows():
        country = row["negara"]
        if country in population_estimates:
            per_1000 = (row["kasus_kumulatif"] / population_estimates[country]) * 1000
            cases_per_capita.append((country, per_1000))
    
    cases_per_capita.sort(key=lambda x: x[1], reverse=True)
    highest_per_capita = cases_per_capita[0] if cases_per_capita else ("N/A", 0)
    
    st.markdown(
        f"""
        **Insight Ranking Global:**  
        **{top10.iloc[0]['negara']}** memiliki **{ratio_1_to_10:.1f}x** lebih banyak kasus dibanding peringkat ke-10. 
        Dari segi kepadatan kasus (per 1000 penduduk), **{highest_per_capita[0]}** memimpin dengan **{highest_per_capita[1]:.1f} kasus/1000 penduduk**. 
        Ranking ini tidak mencerminkan keseluruhan situasi karena: (1) Variasi kapasitas testing, 
        (2) Perbedaan definisi kasus, (3) Strategi pelaporan yang berbeda. 
        Negara dengan testing lebih agresif cenderung memiliki angka kasus lebih tinggi.
        """
    )

st.divider()

# ==============================
# DISTRIBUSI NEGARA TERPILIH
# ==============================
st.subheader("Distribusi Kasus di Negara Terpilih")

if not df_filtered.empty:
    # Ambil data terbaru per negara berdasarkan filter
    df_pie_filtered = (
        df_filtered[df_filtered["tanggal"] == latest_date]
        .groupby("negara", as_index=False)
        .agg({"kasus_kumulatif": "max"})
    )
    
    # Hitung persentase
    total_filtered = df_pie_filtered["kasus_kumulatif"].sum()
    if total_filtered > 0:
        df_pie_filtered["persentase"] = (df_pie_filtered["kasus_kumulatif"] / total_filtered) * 100
        
        # Bar chart untuk perbandingan lebih jelas
        fig_bar_filtered = px.bar(
            df_pie_filtered.sort_values("kasus_kumulatif", ascending=True),
            x="kasus_kumulatif",
            y="negara",
            orientation="h",
            title=f"Perbandingan Total Kasus ({len(negara_selected)} Negara Terpilih)",
            labels={"kasus_kumulatif": "Total Kasus", "negara": "Negara"},
            color="kasus_kumulatif",
            color_continuous_scale="Viridis"
        )
        
        st.plotly_chart(fig_bar_filtered, use_container_width=True)
        
        # Analisis distribusi terfilter
        if len(df_pie_filtered) > 1:
            max_country = df_pie_filtered.loc[df_pie_filtered["kasus_kumulatif"].idxmax()]
            min_country = df_pie_filtered.loc[df_pie_filtered["kasus_kumulatif"].idxmin()]
            ratio = max_country['kasus_kumulatif'] / min_country['kasus_kumulatif']
            
            # Hitung kasus harian rata-rata terakhir
            recent_daily = []
            for negara in df_pie_filtered["negara"]:
                country_recent = df_filtered[df_filtered["negara"] == negara].tail(30)
                avg_daily = country_recent["kasus_harian"].mean() if not country_recent.empty else 0
                recent_daily.append((negara, avg_daily))
            
            recent_daily.sort(key=lambda x: x[1], reverse=True)
            highest_daily = recent_daily[0] if recent_daily else ("N/A", 0)
            
            st.markdown(
                f"""
                **Insight Perbandingan Negara Terpilih:**  
                **{max_country['negara']}** memiliki **{ratio:.1f}x** lebih banyak kasus total dibanding **{min_country['negara']}**. 
                Dalam 30 hari terakhir, **{highest_daily[0]}** mencatat rata-rata **{highest_daily[1]:.0f} kasus/hari** (tertinggi). 
                Perbedaan ini dipengaruhi oleh: ukuran populasi, fase pandemi saat ini, 
                kebijakan testing, dan efektivitas program vaksinasi di masing-masing negara.
                """
            )
    else:
        st.info("Total kasus pada negara terpilih adalah nol.")
else:
    st.info("Silakan pilih negara untuk melihat distribusi kasus.")


st.divider()
# ==============================
# PIE CHART NEGARA TERPILIH
# ==============================
st.subheader("Distribusi Kasus di Negara Terpilih")

if not df_filtered.empty:
    # Ambil data terbaru per negara berdasarkan filter
    df_pie_filtered = (
        df_filtered[df_filtered["tanggal"] == latest_date]
        .groupby("negara", as_index=False)
        .agg({"kasus_kumulatif": "max"})
    )
    
    # Hitung persentase
    total_filtered = df_pie_filtered["kasus_kumulatif"].sum()
    if total_filtered > 0:
        df_pie_filtered["persentase"] = (df_pie_filtered["kasus_kumulatif"] / total_filtered) * 100
        
        # PIE CHART untuk negara terpilih
        fig_pie_filtered = px.pie(
            df_pie_filtered,
            values="kasus_kumulatif",
            names="negara",
            hole=0.4,
            title=f"Distribusi Kasus COVID-19 ({len(negara_selected)} Negara Terpilih)",
            color_discrete_sequence=px.colors.qualitative.Set3
        )
        
        fig_pie_filtered.update_traces(
            textinfo="label+percent",
            hovertemplate="<b>%{label}</b><br>"
                          "Total Kasus: %{value:,}<br>"
                          "Kontribusi: %{percent}<extra></extra>",
            pull=[0.05 if i == df_pie_filtered["kasus_kumulatif"].idxmax() else 0 for i in range(len(df_pie_filtered))]
        )
        
        fig_pie_filtered.update_layout(
            legend_title_text="Negara",
            margin=dict(t=80, b=40),
            showlegend=True
        )
        
        st.plotly_chart(fig_pie_filtered, use_container_width=True)
        
        # Analisis distribusi terfilter
        if len(df_pie_filtered) > 1:
            max_country = df_pie_filtered.loc[df_pie_filtered["kasus_kumulatif"].idxmax()]
            min_country = df_pie_filtered.loc[df_pie_filtered["kasus_kumulatif"].idxmin()]
            ratio = max_country['kasus_kumulatif'] / min_country['kasus_kumulatif']
            
            # Hitung kasus harian rata-rata terakhir
            recent_daily = []
            for negara in df_pie_filtered["negara"]:
                country_recent = df_filtered[df_filtered["negara"] == negara].tail(30)
                avg_daily = country_recent["kasus_harian"].mean() if not country_recent.empty else 0
                recent_daily.append((negara, avg_daily))
            
            recent_daily.sort(key=lambda x: x[1], reverse=True)
            highest_daily = recent_daily[0] if recent_daily else ("N/A", 0)
            
            st.markdown(
                f"""
                **Insight Distribusi Negara Terpilih:**  
                **{max_country['negara']}** mendominasi dengan **{max_country['persentase']:.1f}%** kasus total, 
                atau **{ratio:.1f}x** lebih banyak dibanding **{min_country['negara']}** ({min_country['persentase']:.1f}%). 
                Dalam 30 hari terakhir, **{highest_daily[0]}** mencatat rata-rata **{highest_daily[1]:.0f} kasus/hari** (tertinggi). 
                Distribusi ini dipengaruhi oleh: ukuran populasi, fase pandemi saat ini, 
                kebijakan testing, dan efektivitas program vaksinasi.
                """
            )
    else:
        st.info("Total kasus pada negara terpilih adalah nol.")
else:
    st.info("Silakan pilih negara untuk melihat distribusi kasus.")



# ==============================
# ANALISIS TAMBAHAN: VOLATILITAS HARIAN
# ==============================
st.divider()
st.subheader("Analisis Volatilitas Kasus Harian")

if not df_filtered.empty and len(negara_selected) > 0:
    volatility_data = []
    
    for negara in negara_selected:
        country_data = df_filtered[df_filtered["negara"] == negara]
        if len(country_data) > 1:
            # Hitung standar deviasi kasus harian
            std_dev = country_data["kasus_harian"].std()
            mean_val = country_data["kasus_harian"].mean()
            cv = (std_dev / mean_val * 100) if mean_val > 0 else 0
            
            # Hitung range (max-min)
            max_val = country_data["kasus_harian"].max()
            min_val = country_data["kasus_harian"].min()
            
            volatility_data.append({
                "Negara": negara,
                "Rata-rata Harian": f"{mean_val:,.0f}",
                "Standar Deviasi": f"{std_dev:,.0f}",
                "Koefisien Variasi": f"{cv:.1f}%",
                "Rentang (Max-Min)": f"{max_val:,.0f} - {min_val:,.0f}"
            })
    
    if volatility_data:
        df_volatility = pd.DataFrame(volatility_data)
        st.dataframe(
            df_volatility,
            use_container_width=True,
            hide_index=True
        )
        
        # Insight volatilitas
        highest_cv = max(volatility_data, key=lambda x: float(x["Koefisien Variasi"].replace("%", "")))
        
        st.markdown(
            f"""
            **Insight Volatilitas:**  
            **{highest_cv['Negara']}** menunjukkan volatilitas tertinggi (CV: {highest_cv['Koefisien Variasi']}), 
            mengindikasikan fluktuasi kasus harian yang sangat tidak stabil. 
            Volatilitas tinggi biasanya disebabkan oleh: (1) Perubahan drastis kebijakan, 
            (2) Gelombang infeksi yang tajam, (3) Variasi kapasitas testing harian, 
            (4) Pelaporan yang tidak konsisten. Negara dengan CV rendah cenderung memiliki 
            pola kasus yang lebih stabil dan predictable.
            """
        )
    else:
        st.info("Data tidak cukup untuk analisis volatilitas.")
else:
    st.info("Pilih minimal satu negara untuk analisis volatilitas.")

# ==============================
# FOOTER
# ==============================
st.divider()
st.caption(
    f"""
    **COVID-19 Global Analytics Dashboard**  
    Dibangun dengan Python, Pandas,  Plotly, Streamlit  
    Data terakhir diperbarui: {latest_global_date.date()}  
    Total negara dalam dataset: {len(df['negara'].unique())}  
    Rentang data: {df['tanggal'].min().date()} hingga {df['tanggal'].max().date()}
    """
)

st.markdown(
    """
    <style>
    .stDataFrame {
        font-size: 14px;
    }
    .metric {
        text-align: center;
    }
    .stMarkdown h3 {
        color: #1f77b4;
    }
    </style>
    """,
    unsafe_allow_html=True

)
