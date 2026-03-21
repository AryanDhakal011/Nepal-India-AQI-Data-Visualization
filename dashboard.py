# STREAMLIT DASHBOARD

import streamlit as st
import pandas as pd
import numpy as np
import plotly.graph_objects as go
import plotly.express as px
from plotly.subplots import make_subplots
import folium
from streamlit_folium import st_folium
import warnings
warnings.filterwarnings('ignore')

#PAGE CONFIG
st.set_page_config(
    page_title="South Asia AQI Dashboard",
    page_icon="🌫️",
    layout="wide",
    initial_sidebar_state="expanded"
)

st.markdown("""
<style>
    .metric-card {
        background: #f8f9fa; border-radius: 10px;
        padding: 16px; text-align: center;
        border-left: 4px solid #E63946;
    }
    .who-warning {
        background: #fff3cd; border-left: 4px solid #ffc107;
        padding: 10px 14px; border-radius: 6px; font-size: 14px;
    }
    .sdg-badge {
        display: inline-block; padding: 3px 10px;
        border-radius: 12px; font-size: 12px; font-weight: bold;
        margin: 2px;
    }
    section[data-testid="stSidebar"] { background: #1a1a2e; }
    section[data-testid="stSidebar"] * { color: white !important; }
</style>
""", unsafe_allow_html=True)

# LOAD DATA

@st.cache_data
def load_data():
    df       = pd.read_csv('data/cleaned_aqi.csv', parse_dates=['Date'])
    readings = pd.read_csv('data/readings.csv',    parse_dates=['Date'])
    loc_sum  = pd.read_csv('data/location_summary.csv')
    return df, readings, loc_sum

df, readings, loc_sum = load_data()

WHO_LIMIT = 15.0

LOCATION_COLORS = {
    'Biratnagar, Nepal'            : '#E63946',
    'ITO, Delhi'                   : '#F4A261',
    'Knowledge park, Greater Noida': '#E9C46A',
    'Mumbai'                       : '#2A9D8F',
    'New Ind Town, Faridabad'      : '#264653',
    'Tamil Nadu'                   : '#6A994E',
    'Bengaluru'                    : '#A8DADC',
    'Dimapur, Nagaland'            : '#9B5DE5',
}

AQI_CLASS_ORDER = ['Good','Moderate','Unhealthy for Sensitive Groups',
                   'Unhealthy','Very Unhealthy','Severe']
AQI_CLASS_COLORS = {
    'Good':'#2ECC71','Moderate':'#F1C40F',
    'Unhealthy for Sensitive Groups':'#F39C12',
    'Unhealthy':'#E74C3C','Very Unhealthy':'#9B59B6','Severe':'#641E16'
}

# SIDEBAR — FILTERS

with st.sidebar:
    st.title("🌫️ AQI Dashboard")
    st.markdown("**South Asia Air Quality** — Nepal & India | 2022–2023")
    st.divider()

    st.markdown("### 🎛️ Filters")

    all_locs = sorted(df['Location'].unique())
    sel_locs = st.multiselect(
        "Select Cities",
        options=all_locs,
        default=all_locs,
        help="Filter all charts by city"
    )

    all_months = sorted(df['Month'].unique())
    month_map  = {2:'February',3:'March',10:'October'}
    sel_months = st.multiselect(
        "Select Months",
        options=all_months,
        default=all_months,
        format_func=lambda x: month_map.get(x, str(x)),
        help="Filter by month"
    )

    country_filter = st.radio(
        "Country Focus",
        options=['All','Nepal Only','India Only'],
        index=0
    )

    st.divider()
    st.markdown("### ℹ️ About")
    st.markdown("""
    **Dataset:** India & Nepal AQI 2022–2023  
    **Records:** 12,240 rows | 8 cities  
    **SDG:** 🔵 SDG 13: Climate Action
    """)

# --- Apply filters ---
if not sel_locs:
    sel_locs = all_locs
if not sel_months:
    sel_months = all_months

df_f = df[df['Location'].isin(sel_locs) & df['Month'].isin(sel_months)].copy()
rd_f = readings[readings['Location'].isin(sel_locs) &
                readings['Month'].isin(sel_months)].copy()

if country_filter == 'Nepal Only':
    df_f = df_f[df_f['Country'] == 'Nepal']
    rd_f = rd_f[rd_f['Country'] == 'Nepal']
elif country_filter == 'India Only':
    df_f = df_f[df_f['Country'] == 'India']
    rd_f = rd_f[rd_f['Country'] == 'India']


# HEADER

st.title("🌫️ South Asia Air Quality Dashboard")
st.markdown(
    "**Nepal & India | 2022–2023** &nbsp;|&nbsp; "
    "🔵 **SDG 13: Climate Action** — Strengthening resilience through air quality monitoring"
)

st.markdown(f"""
<div style="background:#2a2000;border-left:4px solid #f0a500;padding:12px 16px;
border-radius:6px;font-size:14px;color:#f5e6c0;margin-bottom:12px;">
    ⚠️ <b style="color:#f0a500;">WHO Alert:</b> The WHO 24-hour PM2.5 guideline is {WHO_LIMIT} µg/m³.
    In this dataset, <b>{df['WHO_Exceedance'].mean()*100:.1f}%</b> of all readings
    exceed this threshold. Average PM2.5 is
    <b>{df['PM2.5'].mean():.0f} µg/m³</b> — <b>{df['PM2.5'].mean()/WHO_LIMIT:.1f}×</b> the safe limit.
</div>
""", unsafe_allow_html=True)

st.divider()

# SECTION 1 — KEY METRICS

st.subheader("📊 Key Metrics")

if len(df_f) > 0:
    m1, m2, m3, m4, m5 = st.columns(5)

    avg_pm25   = df_f['PM2.5'].mean()
    avg_aqi    = df_f['AQI'].mean()
    who_pct    = df_f['WHO_Exceedance'].mean() * 100
    who_mult   = avg_pm25 / WHO_LIMIT
    worst_city = df_f.groupby('Location')['PM2.5'].mean().idxmax() if len(df_f) > 0 else 'N/A'

    m1.metric("Mean PM2.5 (µg/m³)", f"{avg_pm25:.1f}",
              delta=f"{avg_pm25 - WHO_LIMIT:+.1f} vs WHO limit",
              delta_color="inverse")
    m2.metric("Mean AQI", f"{avg_aqi:.0f}")
    m3.metric("WHO Exceedance Rate", f"{who_pct:.1f}%")
    m4.metric("PM2.5 × WHO Limit", f"{who_mult:.1f}×")
    m5.metric("Most Polluted City",
              worst_city.split(',')[0] if ',' in worst_city else worst_city)
else:
    st.warning("No data matches current filter selection.")

st.divider()

# SECTION 2 — PM2.5 TREND + AQI DISTRIBUTION

st.subheader("📈 PM2.5 Trends & AQI Distribution")

col_left, col_right = st.columns([3, 2])

with col_left:
    # Time series — one line per city
    fig_ts = go.Figure()
    for loc in sel_locs:
        grp = rd_f[rd_f['Location'] == loc].sort_values('Date')
        if len(grp) == 0: continue
        color = LOCATION_COLORS.get(loc, '#888')
        fig_ts.add_trace(go.Scatter(
            x=grp['Date'], y=grp['PM2.5'],
            name=loc.replace(', Nepal','').replace('Knowledge park, Greater Noida','Noida'),
            mode='lines+markers',
            line=dict(color=color, width=1.8),
            marker=dict(size=4),
            hovertemplate='%{x|%b %d}<br>PM2.5: %{y:.1f}<extra>' + loc + '</extra>'
        ))
    fig_ts.add_hline(y=WHO_LIMIT, line_dash='dash', line_color='red',
                    annotation_text=f'WHO ({WHO_LIMIT})',
                    annotation_position='top right',
                    annotation_font_size=10)
    fig_ts.update_layout(
        title='PM2.5 Over Time by City',
        xaxis_title='Date', yaxis_title='PM2.5 (µg/m³)',
        height=360, template='plotly_dark',
        legend=dict(font=dict(size=8), x=1.01, y=1,
                    bgcolor='rgba(0,0,0,0)', borderwidth=0),
        margin=dict(r=140, t=40, b=40, l=50),
        xaxis=dict(tickformat='%b %Y', nticks=6)
    )
    st.plotly_chart(fig_ts, use_container_width=True)

with col_right:
    # AQI class donut
    aqi_counts = df_f['AQI_Class'].value_counts()
    aqi_counts = aqi_counts.reindex(
        [c for c in AQI_CLASS_ORDER if c in aqi_counts.index])
    label_map = {
        'Unhealthy for Sensitive Groups': 'USG*',
        'Very Unhealthy': 'Very Unhealthy',
        'Good': 'Good',
        'Moderate': 'Moderate',
        'Unhealthy': 'Unhealthy',
        'Severe': 'Severe',
    }
    short_labels = [label_map.get(l, l) for l in aqi_counts.index]

    fig_donut = go.Figure(go.Pie(
        labels=short_labels,
        values=aqi_counts.values,
        hole=0.5,
        marker_colors=[AQI_CLASS_COLORS.get(c,'#888') for c in aqi_counts.index],
        textinfo='percent+label',
        textfont_size=10,
        insidetextorientation='radial',
    ))
    fig_donut.update_layout(
        title='AQI Category Breakdown<br><sup>*USG = Unhealthy for Sensitive Groups</sup>',
        height=360, template='plotly_dark',
        showlegend=False,
        margin=dict(l=10, r=10, t=60, b=10)
    )
    
    st.plotly_chart(fig_donut, use_container_width=True)

# SECTION 3 — CITY COMPARISON (MULTI-LAYER)

st.subheader("🏙️ City Comparison — PM2.5, AQI & Pollution Index")

if len(loc_sum) > 0:
    loc_f = loc_sum[loc_sum['Location'].isin(sel_locs)].copy()

    fig_ml = make_subplots(specs=[[{'secondary_y': True}]])
    loc_sorted = loc_f.sort_values('PM2_5_mean', ascending=False)
    colors_bar = [LOCATION_COLORS.get(l,'#888') for l in loc_sorted['Location']]

    fig_ml.add_trace(go.Bar(
        x=loc_sorted['Location'], y=loc_sorted['PM2_5_mean'],
        name='Mean PM2.5 (µg/m³)', marker_color=colors_bar, opacity=0.8,
        text=loc_sorted['PM2_5_mean'].round(0), textposition='outside'
    ), secondary_y=False)

    fig_ml.add_trace(go.Scatter(
        x=loc_sorted['Location'], y=loc_sorted['AQI_mean'],
        name='Mean AQI', mode='lines+markers',
        line=dict(color='#264653', width=2.5, dash='dot'),
        marker=dict(size=9, symbol='diamond')
    ), secondary_y=False)

    fig_ml.add_trace(go.Scatter(
        x=loc_sorted['Location'], y=loc_sorted['Pollution_Index'],
        name='Pollution Index (0–1)', mode='lines+markers',
        line=dict(color='#E63946', width=2, dash='dash'),
        marker=dict(size=8)
    ), secondary_y=True)

    fig_ml.add_hline(y=WHO_LIMIT, line_dash='dash', line_color='green',
                     annotation_text='WHO limit', secondary_y=False)
    fig_ml.update_layout(
        height=420, template='plotly_white',
        legend=dict(x=0.01, y=0.99),
        hovermode='x unified',
        xaxis=dict(tickangle=25)
    )
    fig_ml.update_yaxes(title_text='PM2.5 / AQI', secondary_y=False)
    fig_ml.update_yaxes(title_text='Pollution Index', secondary_y=True)
    st.plotly_chart(fig_ml, use_container_width=True)

# SECTION 4 — GEOSPATIAL MAP

st.subheader("🗺️ Geospatial Map — City-Level AQI")

def aqi_color(aqi):
    if   aqi <= 50:  return '#2ECC71'
    elif aqi <= 100: return '#F1C40F'
    elif aqi <= 150: return '#F39C12'
    elif aqi <= 200: return '#E74C3C'
    elif aqi <= 300: return '#9B59B6'
    else:            return '#641E16'

m = folium.Map(location=[22.5, 82.0], zoom_start=5,
               tiles='CartoDB positron')

loc_map = loc_sum[loc_sum['Location'].isin(sel_locs)].copy()
for _, row in loc_map.iterrows():
    if pd.isna(row['Latitude']): continue
    color  = aqi_color(row['AQI_mean'])
    radius = max(10, min(55, row['PM2_5_mean'] / 4.5))

    popup_html = f"""
    <div style="font-family:Arial;font-size:12px;width:210px;">
        <b>{row['Location']}</b><br><hr style="margin:3px 0;">
        <b>Country:</b> {row['Country']}<br>
        <b>Mean PM2.5:</b> {row['PM2_5_mean']:.1f} µg/m³
        ({row['PM25_WHO_Multi']:.1f}× WHO)<br>
        <b>Mean AQI:</b> {row['AQI_mean']:.0f}<br>
        <b>WHO safe rate:</b> {(1-row['WHO_Exceed_pct'])*100:.1f}%
    </div>"""

    folium.CircleMarker(
        location=[row['Latitude'], row['Longitude']],
        radius=radius, color=color,
        fill=True, fill_color=color, fill_opacity=0.7,
        weight=1.5,
        popup=folium.Popup(popup_html, max_width=230),
        tooltip=f"{row['Location'].split(',')[0]}: PM2.5={row['PM2_5_mean']:.0f} AQI={row['AQI_mean']:.0f}"
    ).add_to(m)

legend_html = """
<div style="position:fixed;bottom:20px;left:20px;z-index:9999;
background:#ffffff;padding:12px 14px;border-radius:8px;border:2px solid #999;
font-size:12px;font-family:Arial;line-height:2.0;color:#000000;">
<b style="font-size:13px;color:#000000;">AQI Scale</b><br>
<span style="display:inline-block;width:14px;height:14px;background:#2ECC71;
border-radius:50%;vertical-align:middle;margin-right:6px;"></span>
<span style="color:#000000;">Good (0–50)</span><br>
<span style="display:inline-block;width:14px;height:14px;background:#F1C40F;
border-radius:50%;vertical-align:middle;margin-right:6px;"></span>
<span style="color:#000000;">Moderate (51–100)</span><br>
<span style="display:inline-block;width:14px;height:14px;background:#F39C12;
border-radius:50%;vertical-align:middle;margin-right:6px;"></span>
<span style="color:#000000;">Unhealthy SG (101–150)</span><br>
<span style="display:inline-block;width:14px;height:14px;background:#E74C3C;
border-radius:50%;vertical-align:middle;margin-right:6px;"></span>
<span style="color:#000000;">Unhealthy (151–200)</span><br>
<span style="display:inline-block;width:14px;height:14px;background:#9B59B6;
border-radius:50%;vertical-align:middle;margin-right:6px;"></span>
<span style="color:#000000;">Very Unhealthy (201–300)</span><br>
<span style="display:inline-block;width:14px;height:14px;background:#641E16;
border-radius:50%;vertical-align:middle;margin-right:6px;"></span>
<span style="color:#000000;">Severe (300+)</span><br>
<br><i style="font-size:11px;color:#333333;">Circle size ∝ PM2.5 level<br>Click circles for details</i>
</div>"""

m.get_root().html.add_child(folium.Element(legend_html))

st_folium(m, width=None, height=450)

# SECTION 5 — SCENARIO COMPARISON

st.subheader("🔄 Scenario Comparison — February vs March 2023")

sc = readings[readings['Location'].isin(sel_locs)].copy()
sc = sc[sc['Month'].isin([2, 3])]
sc_agg = sc.groupby(['Location','Month'])[['PM2.5','AQI']].mean().reset_index()
sc_agg['Period'] = sc_agg['Month'].map({2:'Feb 2023',3:'Mar 2023'})

# Only locations with both months
both = sc_agg.groupby('Location').filter(lambda x: len(x)==2)['Location'].unique()
sc_agg = sc_agg[sc_agg['Location'].isin(both)]

if len(sc_agg) > 0:
    fig_sc = go.Figure()
    for loc in sc_agg['Location'].unique():
        grp   = sc_agg[sc_agg['Location']==loc].sort_values('Month')
        color = LOCATION_COLORS.get(loc,'#888')
        change = grp['PM2.5'].iloc[-1] - grp['PM2.5'].iloc[0]
        fig_sc.add_trace(go.Scatter(
            x=grp['Period'], y=grp['PM2.5'],
            mode='lines+markers+text',
            name=loc, line=dict(color=color,width=2.5),
            marker=dict(size=12, color=color),
            text=[f"{grp['PM2.5'].iloc[0]:.0f}", f"{grp['PM2.5'].iloc[1]:.0f}"],
            textposition=['middle left','middle right'],
            textfont=dict(size=10,color=color),
            hovertemplate='%{x}<br>PM2.5: %{y:.1f} µg/m³<extra>'+loc+'</extra>'
        ))
    fig_sc.add_hline(y=WHO_LIMIT, line_dash='dash', line_color='green',
                     annotation_text='WHO limit (15 µg/m³)',
                     annotation_position='top left')
    fig_sc.update_layout(
        height=400, template='plotly_white',
        xaxis_title='Period', yaxis_title='Mean PM2.5 (µg/m³)',
        legend=dict(x=1.01,y=1), margin=dict(r=160)
    )
    st.plotly_chart(fig_sc, use_container_width=True)
else:
    st.info("Select cities with readings in both Feb and Mar for scenario comparison.")

# SECTION 6 — UNCERTAINTY BANDS

st.subheader("📉 PM2.5 Trend with Uncertainty Bands")

def hex_to_rgba(h, a=0.15):
    h = h.lstrip('#')
    r, g, b = int(h[0:2],16), int(h[2:4],16), int(h[4:6],16)
    return f'rgba({r},{g},{b},{a})'

fig_unc = go.Figure()
for loc in sel_locs:
    grp = rd_f[rd_f['Location']==loc].sort_values('Date').copy()
    if len(grp) < 3: continue
    color = LOCATION_COLORS.get(loc,'#888888')
    grp['rm']    = grp['PM2.5'].rolling(3,min_periods=1).mean()
    grp['rsd']   = grp['PM2.5'].rolling(3,min_periods=1).std().fillna(0)
    grp['upper'] = grp['rm'] + 1.5*grp['rsd']
    grp['lower'] = (grp['rm'] - 1.5*grp['rsd']).clip(lower=0)

    x_band = list(grp['Date']) + list(grp['Date'].iloc[::-1])
    y_band = list(grp['upper']) + list(grp['lower'].iloc[::-1])
    fig_unc.add_trace(go.Scatter(
        x=x_band, y=y_band, fill='toself',
        fillcolor=hex_to_rgba(color,0.15),
        line=dict(color='rgba(0,0,0,0)'),
        showlegend=False, hoverinfo='skip'
    ))
    fig_unc.add_trace(go.Scatter(
        x=grp['Date'], y=grp['rm'],
        name=loc, mode='lines+markers',
        line=dict(color=color,width=2.5),
        marker=dict(size=5),
        hovertemplate='%{x|%b %d}<br>PM2.5: %{y:.1f}<extra>'+loc+'</extra>'
    ))

fig_unc.add_hline(y=WHO_LIMIT, line_dash='dash', line_color='red',
                  annotation_text='WHO limit', annotation_position='top right')
fig_unc.update_layout(
    height=400, template='plotly_white',
    xaxis_title='Date', yaxis_title='PM2.5 (µg/m³)',
    legend=dict(x=1.01,y=1,font=dict(size=9)),
    margin=dict(r=160)
)
st.plotly_chart(fig_unc, use_container_width=True)


# SECTION 7 — ETHICAL ANALYSIS

st.subheader("⚖️ Ethical Analysis — Health Burden by Country")

col_e1, col_e2 = st.columns(2)

with col_e1:
    country_stats = rd_f.groupby('Country').agg(
        PM2_5_mean=('PM2.5','mean'),
        WHO_exceed=('WHO_Exceedance','mean')
    ).reset_index()
    country_stats['WHO_pct'] = country_stats['WHO_exceed']*100
    country_stats['WHO_mult'] = country_stats['PM2_5_mean']/WHO_LIMIT

    fig_eth = go.Figure(go.Bar(
        x=country_stats['Country'],
        y=country_stats['WHO_pct'],
        marker_color=['#E63946','#2A9D8F'][:len(country_stats)],
        text=[f"{v:.1f}%" for v in country_stats['WHO_pct']],
        textposition='outside'
    ))
    fig_eth.add_hline(y=100, line_dash='dash', line_color='red', opacity=0.5)
    fig_eth.update_layout(
        title='WHO Exceedance by Country',
        yaxis_title='% Readings Exceeding Limit',
        height=320, template='plotly_white',
        yaxis_range=[0,115]
    )
    st.plotly_chart(fig_eth, use_container_width=True)

with col_e2:
    loc_f2 = loc_sum[loc_sum['Location'].isin(sel_locs)].sort_values('PM25_WHO_Multi')
    colors_eth = ['#E63946' if c=='Nepal' else '#2A9D8F' for c in loc_f2['Country']]
    fig_mult = go.Figure(go.Bar(
        x=loc_f2['PM25_WHO_Multi'],
        y=loc_f2['Location'],
        orientation='h',
        marker_color=colors_eth,
        text=[f"{v:.1f}×" for v in loc_f2['PM25_WHO_Multi']],
        textposition='outside'
    ))
    fig_mult.add_vline(x=1, line_dash='dash', line_color='green')
    fig_mult.update_layout(
        title='PM2.5 as Multiple of WHO Limit',
        xaxis_title='× WHO Guideline',
        height=320, template='plotly_white'
    )
    st.plotly_chart(fig_mult, use_container_width=True)

st.markdown("""
<div style="background:#1e1a00;padding:12px 16px;border-radius:8px;
border-left:4px solid #f0a500;font-size:13px;margin-top:8px;color:#f5e6c0;">
<b style="color:#f0a500;">⚖️ Ethical Insight:</b> 100% of Nepal's Biratnagar readings exceed WHO limits.
Yet Biratnagar is Nepal's <i>only</i> monitored city — the true national burden is invisible.
Unmonitored cities likely face <b>equal or worse</b> pollution with zero policy response.
This is a structural data equity failure that must inform SDG 11 and SDG 13 policy.
</div>
""", unsafe_allow_html=True)

# SECTION 8 — DATA EXPLORER

with st.expander("🔍 Raw Data Explorer"):
    st.markdown("**Filtered readings dataset** (unique station-time readings)")
    st.dataframe(
        rd_f[['Location','Country','Date','Month','Season',
               'PM2.5','AQI','AQI_Class','WHO_Exceedance',
               'Pollution_Index','PM25_WHO_Multiple']].sort_values('Date'),
        use_container_width=True, height=280
    )

# FOOTER

st.divider()
st.markdown("""
<div style="text-align:center;color:#888;font-size:12px;">
    South Asia Air Quality Dashboard &nbsp;|&nbsp;
    Data: Kaggle — India & Nepal AQI Dataset (2022–2023) &nbsp;|&nbsp;
    SDG 3 · SDG 11 · SDG 13 &nbsp;|&nbsp;
    Built with Python · Streamlit · Plotly · Folium
</div>
""", unsafe_allow_html=True)
