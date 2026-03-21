import pandas as pd
import numpy as np
import matplotlib.pyplot as plt
import matplotlib.patches as mpatches
import seaborn as sns
import plotly.graph_objects as go
import plotly.express as px
from plotly.subplots import make_subplots
import folium
from folium.plugins import HeatMap
import warnings
warnings.filterwarnings('ignore')

df       = pd.read_csv('data/cleaned_aqi.csv', parse_dates=['Date'])
readings = pd.read_csv('data/readings.csv',    parse_dates=['Date'])
loc_sum  = pd.read_csv('data/location_summary.csv')

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

print("Generating advanced visualizations...")

#MULTI-LAYER VISUALIZATION 

print("  [1/6] Multi-layer visualization...")

fig = make_subplots(specs=[[{'secondary_y': True}]])

locs    = loc_sum.sort_values('PM2_5_mean', ascending=False)['Location'].tolist()
colors  = [LOCATION_COLORS.get(l, '#888') for l in locs]

# Layer 1: PM2.5 bars
fig.add_trace(go.Bar(
    x=locs, y=loc_sum.set_index('Location').loc[locs, 'PM2_5_mean'],
    name='Mean PM2.5 (µg/m³)', marker_color=colors,
    opacity=0.85, text=loc_sum.set_index('Location').loc[locs,'PM2_5_mean'].round(0),
    textposition='outside'
), secondary_y=False)

# Layer 2: AQI line overlay
fig.add_trace(go.Scatter(
    x=locs, y=loc_sum.set_index('Location').loc[locs,'AQI_mean'],
    name='Mean AQI', mode='lines+markers',
    line=dict(color='#264653', width=2.5, dash='dot'),
    marker=dict(size=9, symbol='diamond', color='#264653')
), secondary_y=False)

# Layer 3: Pollution Index on secondary axis
fig.add_trace(go.Scatter(
    x=locs, y=loc_sum.set_index('Location').loc[locs,'Pollution_Index'],
    name='Composite Pollution Index (0–1)', mode='lines+markers',
    line=dict(color='#E63946', width=2, dash='dash'),
    marker=dict(size=8, color='#E63946')
), secondary_y=True)

# WHO line
fig.add_hline(y=WHO_LIMIT, line_dash='dash', line_color='green',
              annotation_text=f'WHO limit ({WHO_LIMIT} µg/m³)',
              annotation_position='top right', secondary_y=False)

fig.update_layout(
    title=dict(
        text='Advanced Viz 1: Multi-Layer — PM2.5, AQI & Pollution Index by City<br>'
             '<sup>Three pollution metrics confirm Delhi as South Asia\'s most polluted monitored city</sup>',
        font=dict(size=15)),
    xaxis_title='City',
    legend=dict(x=0.01, y=0.99, bgcolor='rgba(255,255,255,0.8)'),
    height=520, template='plotly_white',
    hovermode='x unified'
)
fig.update_yaxes(title_text='PM2.5 / AQI Value', secondary_y=False)
fig.update_yaxes(title_text='Composite Pollution Index', secondary_y=True)
fig.update_xaxes(tickangle=30)

fig.write_html('outputs/adv1_multilayer.html')
print("    Saved: adv1_multilayer.html")

# FACETED SMALL-MULTIPLE CHARTS 

print("  [2/6] Faceted small-multiple charts...")

locs_with_data = readings.groupby('Location').filter(lambda x: len(x) >= 3)['Location'].unique()

n_cols = 3
n_rows = int(np.ceil(len(locs_with_data) / n_cols))

fig2, axes = plt.subplots(n_rows, n_cols,
                           figsize=(15, 4.5 * n_rows),
                           sharex=False, sharey=False)
axes = axes.flatten()

plt.rcParams.update({'font.size': 10})

for i, loc in enumerate(sorted(locs_with_data)):
    ax  = axes[i]
    grp = readings[readings['Location'] == loc].sort_values('Date')
    col = LOCATION_COLORS.get(loc, '#888')

    # Rolling mean for trend line
    if len(grp) >= 3:
        grp = grp.copy()
        grp['rolling'] = grp['PM2.5'].rolling(3, min_periods=1).mean()
        ax.plot(grp['Date'], grp['PM2.5'],
                'o-', color=col, alpha=0.5, markersize=4, linewidth=1.2, label='Daily')
        ax.plot(grp['Date'], grp['rolling'],
                '-', color=col, linewidth=2.2, label='3-pt avg')
    else:
        ax.plot(grp['Date'], grp['PM2.5'], 'o-', color=col, markersize=5)

    ax.axhline(WHO_LIMIT, color='red', linestyle='--', linewidth=1, alpha=0.7)
    ax.fill_between(grp['Date'], 0, WHO_LIMIT, alpha=0.06, color='green')
    ax.set_title(loc.replace(', Nepal', '\n(Nepal)')
                    .replace('Knowledge park, Greater Noida', 'Noida (Knowledge Pk)'),
                 fontsize=9.5, fontweight='bold', pad=4)
    ax.set_ylabel('PM2.5', fontsize=8)
    ax.tick_params(axis='x', labelsize=7.5, rotation=25)
    ax.tick_params(axis='y', labelsize=8)
    ax.spines['top'].set_visible(False)
    ax.spines['right'].set_visible(False)

# Hide unused subplots
for j in range(len(locs_with_data), len(axes)):
    axes[j].set_visible(False)

fig2.suptitle('Advanced Viz 2: Faceted — PM2.5 Trend per City (Small Multiples)\n'
              'Red dashed = WHO limit | Green zone = safe range',
              fontsize=13, fontweight='bold', y=1.01)
plt.tight_layout()
plt.savefig('outputs/adv2_faceted_pm25.png', bbox_inches='tight', dpi=130)
plt.close()
print("    Saved: adv2_faceted_pm25.png")

# GEOSPATIAL HEATMAP 

print("  [3/6] Geospatial visualization...")

m = folium.Map(location=[22.5, 82.0], zoom_start=5,
               tiles='CartoDB positron')

# Colour scale by AQI severity
def aqi_color(aqi):
    if   aqi <= 50:  return '#2ECC71'
    elif aqi <= 100: return '#F1C40F'
    elif aqi <= 150: return '#F39C12'
    elif aqi <= 200: return '#E74C3C'
    elif aqi <= 300: return '#9B59B6'
    else:            return '#641E16'

# Add circle markers
for _, row in loc_sum.iterrows():
    if pd.isna(row['Latitude']): continue
    color   = aqi_color(row['AQI_mean'])
    radius  = max(10, min(50, row['PM2_5_mean'] / 5))
    exceed_pct = row['WHO_Exceed_pct'] * 100
    who_x = row['PM25_WHO_Multi']

    popup_html = f"""
    <div style="font-family:Arial; width:220px; font-size:12px;">
        <b style="font-size:13px;">{row['Location']}</b><br>
        <hr style="margin:4px 0;">
        <b>Country:</b> {row['Country']}<br>
        <b>Mean PM2.5:</b> {row['PM2_5_mean']:.1f} µg/m³
            &nbsp;<span style="color:red">({who_x:.1f}× WHO limit)</span><br>
        <b>Mean AQI:</b> {row['AQI_mean']:.0f}<br>
        <b>WHO exceedance:</b> {exceed_pct:.0f}% of readings<br>
        <b>Pollution Index:</b> {row['Pollution_Index']:.3f}
    </div>"""

    folium.CircleMarker(
        location=[row['Latitude'], row['Longitude']],
        radius=radius,
        color=color, fill=True, fill_color=color, fill_opacity=0.7,
        weight=1.5,
        popup=folium.Popup(popup_html, max_width=240),
        tooltip=f"{row['Location']}: AQI {row['AQI_mean']:.0f}"
    ).add_to(m)

    # City label
    folium.Marker(
        location=[row['Latitude'] + 0.4, row['Longitude']],
        icon=folium.DivIcon(
            html=f'<div style="font-size:9px;font-weight:bold;'
                 f'color:{color};white-space:nowrap;">'
                 f'{row["Location"].split(",")[0]}</div>',
            icon_size=(150, 20)
        )
    ).add_to(m)

# WHO legend
legend_html = """
<div style="position:fixed;bottom:30px;left:30px;z-index:9999;
            background:white;padding:12px;border-radius:8px;
            border:1px solid #ccc;font-size:11px;font-family:Arial;">
    <b>AQI Colour Scale</b><br>
    <span style="background:#2ECC71;padding:2px 10px;border-radius:3px;">&nbsp;</span> Good (0–50)<br>
    <span style="background:#F1C40F;padding:2px 10px;border-radius:3px;">&nbsp;</span> Moderate (51–100)<br>
    <span style="background:#F39C12;padding:2px 10px;border-radius:3px;">&nbsp;</span> Unhealthy Sensitive (101–150)<br>
    <span style="background:#E74C3C;padding:2px 10px;border-radius:3px;">&nbsp;</span> Unhealthy (151–200)<br>
    <span style="background:#9B59B6;padding:2px 10px;border-radius:3px;">&nbsp;</span> Very Unhealthy (201–300)<br>
    <span style="background:#641E16;color:white;padding:2px 10px;border-radius:3px;">&nbsp;</span> Severe (300+)<br>
    <br><i>Circle size ∝ PM2.5 level<br>Click circles for details</i>
</div>"""
m.get_root().html.add_child(folium.Element(legend_html))

title_html = """
<div style="position:fixed;top:10px;left:50%;transform:translateX(-50%);
            z-index:9999;background:white;padding:8px 18px;border-radius:8px;
            border:1px solid #ccc;font-family:Arial;font-size:13px;font-weight:bold;">
    South Asia Air Quality — City-Level AQI Map (2022–2023)
</div>"""
m.get_root().html.add_child(folium.Element(title_html))

m.save('outputs/adv3_geospatial_map.html')
print("    Saved: adv3_geospatial_map.html")

# SCENARIO COMPARISON — Feb 2023 vs Mar 2023 (period shift)

print("  [4/6] Scenario comparison...")

# Aggregate by location and period
scenario = readings.groupby(['Location','Month'])[['PM2.5','AQI']].mean().reset_index()
scenario = scenario[scenario['Month'].isin([2, 3])]
scenario['Period'] = scenario['Month'].map({2: 'February 2023', 3: 'March 2023'})
scenario = scenario[scenario['Location'].isin(
    scenario.groupby('Location').filter(lambda x: len(x) >= 2)['Location'].unique()
)]

fig3 = go.Figure()

for loc in scenario['Location'].unique():
    grp   = scenario[scenario['Location'] == loc].sort_values('Month')
    color = LOCATION_COLORS.get(loc, '#888')
    if len(grp) < 2: continue

    # Arrow line between months
    fig3.add_trace(go.Scatter(
        x=['February 2023', 'March 2023'],
        y=grp.sort_values('Month')['PM2.5'].tolist(),
        mode='lines+markers+text',
        name=loc,
        line=dict(color=color, width=2),
        marker=dict(size=11, color=color),
        text=[f"{grp.sort_values('Month')['PM2.5'].iloc[0]:.0f}",
              f"{grp.sort_values('Month')['PM2.5'].iloc[1]:.0f}"],
        textposition=['middle left', 'middle right'],
        textfont=dict(size=10, color=color)
    ))

fig3.add_hline(y=WHO_LIMIT, line_dash='dash', line_color='green',
               annotation_text='WHO limit (15 µg/m³)',
               annotation_position='top left')

fig3.update_layout(
    title=dict(
        text='Advanced Viz 4: Scenario Comparison — February vs March 2023<br>'
             '<sup>Most cities show PM2.5 improvement Feb→Mar; Nepal remains consistently elevated</sup>',
        font=dict(size=14)),
    xaxis_title='Period',
    yaxis_title='Mean PM2.5 (µg/m³)',
    height=500, template='plotly_white',
    legend=dict(x=1.01, y=0.99)
)
fig3.write_html('outputs/adv4_scenario_comparison.html')
print("    Saved: adv4_scenario_comparison.html")

# ETHICAL BIAS VISUALIZATION — Health burden by country

print("  [5/6] Ethical bias visualization...")

fig4, axes4 = plt.subplots(1, 2, figsize=(14, 6))

# Panel A: WHO exceedance % by country
country_exc = readings.groupby('Country').agg(
    WHO_Exceed_pct  = ('WHO_Exceedance', 'mean'),
    PM2_5_mean      = ('PM2.5', 'mean'),
    Pollution_Index = ('Pollution_Index', 'mean')
).reset_index()
country_exc['WHO_Exceed_pct'] *= 100

colors_c = ['#E63946' if c == 'Nepal' else '#2A9D8F' for c in country_exc['Country']]
bars = axes4[0].bar(country_exc['Country'], country_exc['WHO_Exceed_pct'],
                    color=colors_c, edgecolor='white', width=0.5)
axes4[0].axhline(100, color='red', linestyle='--', linewidth=1.2,
                 label='100% exceedance (all readings unsafe)', alpha=0.7)
for bar, val in zip(bars, country_exc['WHO_Exceed_pct']):
    axes4[0].text(bar.get_x() + bar.get_width()/2, val + 0.5,
                  f'{val:.1f}%', ha='center', va='bottom', fontweight='bold')
axes4[0].set_ylabel('% of Readings Exceeding WHO Limit', labelpad=8)
axes4[0].set_title('WHO Exceedance Rate by Country\n'
                   'Nepal: 100% of readings above safe limit', fontsize=11, pad=8)
axes4[0].set_ylim(0, 115)
axes4[0].spines['top'].set_visible(False)
axes4[0].spines['right'].set_visible(False)
axes4[0].legend(fontsize=8.5)

# Panel B: PM2.5 multiple of WHO limit per city — ranked
loc_sorted = loc_sum.sort_values('PM25_WHO_Multi', ascending=True)
colors_b   = ['#E63946' if c == 'Nepal' else '#2A9D8F'
              for c in loc_sorted['Country']]
bars2 = axes4[1].barh(loc_sorted['Location'], loc_sorted['PM25_WHO_Multi'],
                      color=colors_b, edgecolor='white', height=0.6)
axes4[1].axvline(1, color='red', linestyle='--', linewidth=1.5,
                 label='1× = exactly at WHO limit')
for bar, val in zip(bars2, loc_sorted['PM25_WHO_Multi']):
    axes4[1].text(val + 0.2, bar.get_y() + bar.get_height()/2,
                  f'{val:.1f}×', va='center', fontsize=9)
axes4[1].set_xlabel('PM2.5 as Multiple of WHO 24-hr Guideline', labelpad=8)
axes4[1].set_title('How Many Times Over WHO Limit?\n'
                   'Delhi = 22.9×; Nepal = 4.1× — nobody is safe', fontsize=11, pad=8)
axes4[1].spines['top'].set_visible(False)
axes4[1].spines['right'].set_visible(False)
axes4[1].legend(fontsize=8.5)

nepal_patch = mpatches.Patch(color='#E63946', label='Nepal')
india_patch = mpatches.Patch(color='#2A9D8F', label='India')
fig4.legend(handles=[nepal_patch, india_patch],
            loc='lower center', ncol=2, fontsize=10, frameon=False,
            title='Country', title_fontsize=10)

fig4.suptitle('Advanced Viz 5: Ethical Bias — Unequal Health Burden Across Cities\n'
              'ALL cities exceed WHO safety thresholds; monitoring gaps hide the true scale of Nepal\'s crisis',
              fontsize=12, fontweight='bold')
plt.tight_layout(rect=[0, 0.06, 1, 0.97])
plt.savefig('outputs/adv5_ethical_bias.png', bbox_inches='tight', dpi=130)
plt.close()
print("    Saved: adv5_ethical_bias.png")


# ADV 6: UNCERTAINTY VISUALIZATION — Rolling mean + confidence band

print("  [6/6] Uncertainty visualization...")

def hex_to_rgba(h, a=0.15):
    h = h.lstrip('#')
    r, g, b = int(h[0:2], 16), int(h[2:4], 16), int(h[4:6], 16)
    return f'rgba({r},{g},{b},{a})'

focus_locs = ['Mumbai', 'Biratnagar, Nepal', 'Bengaluru',
              'Knowledge park, Greater Noida']
focus_locs = [l for l in focus_locs if l in readings['Location'].values]

fig5 = go.Figure()

for loc in focus_locs:
    grp = readings[readings['Location'] == loc].sort_values('Date').copy()
    if len(grp) < 4:
        continue
    color    = LOCATION_COLORS.get(loc, '#888888')
    rgba_col = hex_to_rgba(color, 0.15)

    grp['roll_mean'] = grp['PM2.5'].rolling(3, min_periods=1).mean()
    grp['roll_std']  = grp['PM2.5'].rolling(3, min_periods=1).std().fillna(0)
    grp['upper']     = grp['roll_mean'] + 1.5 * grp['roll_std']
    grp['lower']     = (grp['roll_mean'] - 1.5 * grp['roll_std']).clip(lower=0)

    x_band = list(grp['Date']) + list(grp['Date'].iloc[::-1])
    y_band = list(grp['upper']) + list(grp['lower'].iloc[::-1])

    fig5.add_trace(go.Scatter(
        x=x_band, y=y_band,
        fill='toself', fillcolor=rgba_col,
        line=dict(color='rgba(0,0,0,0)'),
        showlegend=False, hoverinfo='skip'
    ))
    fig5.add_trace(go.Scatter(
        x=grp['Date'], y=grp['roll_mean'],
        name=loc, mode='lines+markers',
        line=dict(color=color, width=2.5),
        marker=dict(size=6),
        hovertemplate='%{x|%b %d}<br>PM2.5: %{y:.1f}<extra>' + loc + '</extra>'
    ))
    fig5.add_trace(go.Scatter(
        x=grp['Date'], y=grp['PM2.5'],
        mode='markers', marker=dict(size=4, color=color, opacity=0.35),
        showlegend=False, hoverinfo='skip'
    ))

fig5.add_hline(y=WHO_LIMIT, line_dash='dash', line_color='green',
               annotation_text='WHO 24-hr limit (15 ug/m3)',
               annotation_position='top right')
fig5.update_layout(
    title=dict(
        text='Advanced Viz 6: Uncertainty — PM2.5 Trend with Confidence Bands<br>'
             '<sup>Shaded band = rolling ±1.5 SD | Dots = raw readings | Lines = 3-pt rolling mean</sup>',
        font=dict(size=14)),
    xaxis_title='Date',
    yaxis_title='PM2.5 (ug/m3)',
    height=520, template='plotly_white',
    legend=dict(x=0.01, y=0.99, bgcolor='rgba(255,255,255,0.85)'),
    hovermode='x unified'
)
fig5.write_html('outputs/adv6_uncertainty.html')
print("    Saved: adv6_uncertainty.html")


print("\nAll advanced visualizations saved to outputs/")
print("Task 4 complete.")
