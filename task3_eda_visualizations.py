import pandas as pd
import numpy as np
import matplotlib.pyplot as plt
import matplotlib.patches as mpatches
import seaborn as sns
import warnings
warnings.filterwarnings('ignore')

#load cleaned datasets 
df       = pd.read_csv('data/cleaned_aqi.csv', parse_dates=['Date'])
readings = pd.read_csv('data/readings.csv',    parse_dates=['Date'])
loc_sum  = pd.read_csv('data/location_summary.csv')

# Consistent colour palette per location
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
WHO_LIMIT = 15.0

plt.rcParams.update({
    'font.family'    : 'DejaVu Sans',
    'font.size'      : 11,
    'axes.titlesize' : 13,
    'axes.titleweight': 'bold',
    'axes.spines.top': False,
    'axes.spines.right': False,
    'figure.dpi'     : 120,
})

print("Generating EDA charts...")

#Bar chart 

fig, ax = plt.subplots(figsize=(11, 5))

loc_sorted = loc_sum.sort_values('PM2_5_mean', ascending=True)
colors = [LOCATION_COLORS.get(l, '#888') for l in loc_sorted['Location']]
bars   = ax.barh(loc_sorted['Location'], loc_sorted['PM2_5_mean'],
                 color=colors, edgecolor='white', linewidth=0.5, height=0.6)

# WHO limit line
ax.axvline(WHO_LIMIT, color='red', linestyle='--', linewidth=1.8,
           label=f'WHO 24-hr limit ({WHO_LIMIT} µg/m³)')

# Value labels
for bar, val in zip(bars, loc_sorted['PM2_5_mean']):
    ax.text(val + 2, bar.get_y() + bar.get_height()/2,
            f'{val:.0f}', va='center', fontsize=9.5, color='#333')

ax.set_xlabel('Mean PM2.5 (µg/m³)', labelpad=8)
ax.set_title('Chart 1: Mean PM2.5 Concentration by City\n'
             'All 8 cities exceed WHO safe limits — Delhi is 23× over threshold',
             pad=12)
ax.legend(loc='lower right', fontsize=9)
ax.set_xlim(0, 400)

# Nepal highlight annotation
nep_val = loc_sorted.loc[loc_sorted['Location']=='Biratnagar, Nepal','PM2_5_mean'].values
if len(nep_val):
    ax.annotate('Nepal (only monitored city)',
                xy=(nep_val[0], loc_sorted[loc_sorted['Location']=='Biratnagar, Nepal'].index[0]),
                xytext=(180, loc_sorted[loc_sorted['Location']=='Biratnagar, Nepal'].index[0]),
                fontsize=8.5, color='#E63946',
                arrowprops=dict(arrowstyle='->', color='#E63946', lw=1.2))

plt.tight_layout()
plt.savefig('outputs/chart1_pm25_by_city.png', bbox_inches='tight')
plt.close()
print("  Chart 1 saved.")

# Line chart 

fig, ax = plt.subplots(figsize=(13, 6))

for loc, grp in readings.groupby('Location'):
    grp_sorted = grp.sort_values('Date')
    ax.plot(grp_sorted['Date'], grp_sorted['PM2.5'],
            marker='o', markersize=4, linewidth=1.8,
            color=LOCATION_COLORS.get(loc, '#888'),
            label=loc, alpha=0.85)

ax.axhline(WHO_LIMIT, color='red', linestyle='--', linewidth=1.5,
           label=f'WHO limit ({WHO_LIMIT} µg/m³)', alpha=0.7)
ax.set_xlabel('Date', labelpad=8)
ax.set_ylabel('PM2.5 (µg/m³)', labelpad=8)
ax.set_title('Chart 2: PM2.5 Trends Over Time by City\n'
             'Delhi consistently highest; Nepal persistently above WHO limit',
             pad=12)
ax.legend(loc='upper right', fontsize=8, ncol=2)
ax.xaxis.set_major_formatter(plt.matplotlib.dates.DateFormatter('%b %d'))
plt.xticks(rotation=30)
ax.fill_between(readings['Date'].sort_values().unique(),
                0, WHO_LIMIT, alpha=0.07, color='green',
                label='WHO safe zone')
plt.tight_layout()
plt.savefig('outputs/chart2_pm25_trend.png', bbox_inches='tight')
plt.close()
print("  Chart 2 saved.")

# Heatmap 

# Build pivot from readings
pivot = readings.pivot_table(values='PM2.5', index='Location',
                             columns='Month', aggfunc='mean').round(1)
month_names = {2:'Feb', 3:'Mar', 10:'Oct'}
pivot.columns = [month_names.get(c, str(c)) for c in pivot.columns]

fig, ax = plt.subplots(figsize=(9, 5))
mask = pivot.isnull()
sns.heatmap(pivot, annot=True, fmt='.0f', cmap='YlOrRd',
            mask=mask, linewidths=0.5, linecolor='white',
            ax=ax, cbar_kws={'label': 'Mean PM2.5 (µg/m³)'},
            annot_kws={'size': 10})

ax.set_title('Chart 3: Mean PM2.5 by City × Month (Heatmap)\n'
             'Delhi peaks in Feb; Nepal shows consistent elevated levels',
             pad=12)
ax.set_xlabel('Month', labelpad=8)
ax.set_ylabel('')
plt.tight_layout()
plt.savefig('outputs/chart3_heatmap_city_month.png', bbox_inches='tight')
plt.close()
print("  Chart 3 saved.")

#Box plot 
fig, ax = plt.subplots(figsize=(12, 6))

# Use full df for better distributions
order = (df.groupby('Location')['AQI'].median()
           .sort_values(ascending=False).index.tolist())

box_colors = [LOCATION_COLORS.get(l, '#888') for l in order]
bp = ax.boxplot(
    [df[df['Location'] == l]['AQI'].values for l in order],
    patch_artist=True, notch=False, vert=True,
    medianprops=dict(color='black', linewidth=2),
    whiskerprops=dict(linewidth=1.2),
    capprops=dict(linewidth=1.2),
    flierprops=dict(marker='o', markersize=2, alpha=0.4)
)
for patch, color in zip(bp['boxes'], box_colors):
    patch.set_facecolor(color)
    patch.set_alpha(0.75)

ax.axhline(150, color='orange', linestyle='--', linewidth=1.4,
           label='Unhealthy threshold (AQI 150)')
ax.axhline(200, color='red', linestyle='--', linewidth=1.4,
           label='Very Unhealthy threshold (AQI 200)')

ax.set_xticks(range(1, len(order)+1))
ax.set_xticklabels([l.replace(', Nepal','*\n(Nepal)').replace(
    'Knowledge park, ','Noida\n') for l in order],
    fontsize=8.5, rotation=15, ha='right')
ax.set_ylabel('AQI Value', labelpad=8)
ax.set_title('Chart 4: AQI Distribution by City (Box Plot)\n'
             'Delhi and Noida show widest range — most unpredictable air quality',
             pad=12)
ax.legend(fontsize=9)
plt.tight_layout()
plt.savefig('outputs/chart4_boxplot_aqi.png', bbox_inches='tight')
plt.close()
print("  Chart 4 saved.")

# Scatter Plot

fig, ax = plt.subplots(figsize=(9, 6))

country_colors = {'Nepal': '#E63946', 'India': '#2A9D8F'}
for country, grp in readings.groupby('Country'):
    ax.scatter(grp['PM2.5'], grp['AQI'],
               c=country_colors[country], alpha=0.75,
               s=60, label=country, edgecolors='white', linewidths=0.4)

# Regression line
m, b = np.polyfit(readings['PM2.5'], readings['AQI'], 1)
x_line = np.linspace(readings['PM2.5'].min(), readings['PM2.5'].max(), 100)
ax.plot(x_line, m*x_line + b, color='#333', linewidth=1.5,
        linestyle='--', label=f'Trend (r={readings["PM2.5"].corr(readings["AQI"]):.2f})')

ax.axvline(WHO_LIMIT, color='red', linestyle=':', linewidth=1.3,
           label=f'WHO limit ({WHO_LIMIT} µg/m³)', alpha=0.7)
ax.set_xlabel('PM2.5 (µg/m³)', labelpad=8)
ax.set_ylabel('AQI', labelpad=8)
ax.set_title('Chart 5: PM2.5 vs AQI Correlation by Country\n'
             f'Strong positive correlation (r={readings["PM2.5"].corr(readings["AQI"]):.2f}) — '
             'PM2.5 is the dominant AQI driver',
             pad=12)
ax.legend(fontsize=9)
plt.tight_layout()
plt.savefig('outputs/chart5_scatter_pm25_aqi.png', bbox_inches='tight')
plt.close()
print("  Chart 5 saved.")

# Stacked bar

aqi_dist = df.groupby(['Location','AQI_Class']).size().unstack(fill_value=0)

# Reorder columns by severity
severity_order = ['Good','Moderate','Unhealthy for Sensitive Groups',
                  'Unhealthy','Very Unhealthy','Severe']
aqi_dist = aqi_dist.reindex(columns=[c for c in severity_order if c in aqi_dist.columns])

# Convert to percentage
aqi_pct = aqi_dist.div(aqi_dist.sum(axis=1), axis=0) * 100

# Reorder rows by % Good descending
aqi_pct = aqi_pct.loc[aqi_pct.get('Good', pd.Series(0, index=aqi_pct.index))
                       .sort_values(ascending=False).index]

aqi_colors = {
    'Good'                          : '#2ECC71',
    'Moderate'                      : '#F1C40F',
    'Unhealthy for Sensitive Groups': '#F39C12',
    'Unhealthy'                     : '#E74C3C',
    'Very Unhealthy'                : '#9B59B6',
    'Severe'                        : '#641E16',
}

fig, ax = plt.subplots(figsize=(13, 6))
bottom = np.zeros(len(aqi_pct))

for col in aqi_pct.columns:
    color = aqi_colors.get(col, '#888')
    bars  = ax.bar(aqi_pct.index, aqi_pct[col], bottom=bottom,
                   color=color, label=col, edgecolor='white', linewidth=0.3)
    # Add percentage label if segment > 8%
    for i, (bar, val) in enumerate(zip(bars, aqi_pct[col])):
        if val > 8:
            ax.text(bar.get_x() + bar.get_width()/2,
                    bottom[i] + val/2, f'{val:.0f}%',
                    ha='center', va='center', fontsize=8, color='white',
                    fontweight='bold')
    bottom += aqi_pct[col].values

ax.set_ylabel('Percentage of Readings (%)', labelpad=8)
ax.set_title('Chart 6: AQI Category Distribution by City (Stacked Bar)\n'
             'Bengaluru has most "Good" days; Delhi has zero — 100% hazardous range',
             pad=12)
ax.set_xticklabels([l.replace(', Nepal','\n(Nepal)').replace(
    'Knowledge park, Greater Noida','Noida\n(Knowledge Park)')
    for l in aqi_pct.index], rotation=20, ha='right', fontsize=8.5)
ax.legend(loc='upper right', fontsize=8.5, bbox_to_anchor=(1.18, 1))
ax.set_ylim(0, 105)
plt.tight_layout()
plt.savefig('outputs/chart6_stacked_aqi_class.png', bbox_inches='tight')
plt.close()
print("  Chart 6 saved.")

# Correlation heatmap — all pollutants

corr_cols  = ['PM2.5','PM10','AQI','O3','CO','SO2','NO2']
corr_matrix = readings[corr_cols].corr()

fig, ax = plt.subplots(figsize=(8, 6))
mask = np.triu(np.ones_like(corr_matrix, dtype=bool))
sns.heatmap(corr_matrix, annot=True, fmt='.2f', cmap='coolwarm',
            center=0, mask=mask, linewidths=0.5, ax=ax,
            cbar_kws={'label': 'Pearson r'},
            annot_kws={'size': 9})
ax.set_title('Chart 7: Pollutant Correlation Matrix\n'
             'PM2.5–PM10 (r=0.84) and PM2.5–NO2 (r=0.72) show strong co-occurrence',
             pad=12)
plt.tight_layout()
plt.savefig('outputs/chart7_correlation_heatmap.png', bbox_inches='tight')
plt.close()
print("  Chart 7 saved.")

print("\nAll EDA charts saved to outputs/")
print("Task 3 complete.")
