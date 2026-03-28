import pandas as pd
import numpy as np
import warnings
warnings.filterwarnings('ignore')


#LOADING DATASET

print("=" * 60)
print("STEP 1: Loading datasets")
print("=" * 60)

main_df  = pd.read_csv('data/IND_and_Nep_AQI_Dataset.csv')
train_df = pd.read_csv('data/train_data.csv')
test_df  = pd.read_csv('data/testing_data.csv')

print(f"Main dataset   : {main_df.shape[0]:,} rows x {main_df.shape[1]} columns")
print(f"Train subset   : {train_df.shape[0]:,} rows x {train_df.shape[1]} columns")
print(f"Test subset    : {test_df.shape[0]:,} rows x {test_df.shape[1]} columns")

main_files  = set(main_df['Filename'])
train_files = set(train_df['Filename'])
test_files  = set(test_df['Filename'])
print(f"Overlap — Main & Train: {len(main_files & train_files):,} | Main & Test: {len(main_files & test_files):,}")
print("Train and test are subsets of main. Using main as master dataset.")

df = main_df.copy()

# INITIAL INSPECTION

print("\n" + "=" * 60)
print("STEP 2: Initial inspection")
print("=" * 60)

print("\nColumn data types:\n", df.dtypes)
nulls    = df.isnull().sum()
null_pct = (nulls / len(df) * 100).round(2)
null_report = pd.DataFrame({'Missing': nulls, 'Pct (%)': null_pct})
print("\nMissing values:\n", null_report[null_report['Missing'] > 0])
print("\nNumerical summary:\n",
      df[['PM2.5','AQI','PM10','O3','CO','SO2','NO2']].describe().round(2))

# DATA CLEANING


print("\n" + "=" * 60)
print("STEP 3: Data cleaning")
print("=" * 60)

df.drop(columns=['Filename'], inplace=True)
print("Dropped Filename column.")

# Parse Hour string to integer
def parse_hour(h):
    try:
        return int(str(h).split(':')[0])
    except:
        return np.nan

df['Hour_int'] = df['Hour'].apply(parse_hour)

# Build datetime column
df['Date'] = pd.to_datetime(
    df['Year'].astype(str) + '-' +
    df['Month'].astype(str).str.zfill(2) + '-' +
    df['Day'].astype(str).str.zfill(2),
    format='%Y-%m-%d', errors='coerce'
)
print(f"Date range: {df['Date'].min().date()} to {df['Date'].max().date()}")

# Clean AQI_Class labels
df['AQI_Class'] = (df['AQI_Class']
                   .str.replace(r'^[a-f]_', '', regex=True)
                   .str.replace('_', ' '))
print(f"AQI classes: {sorted(df['AQI_Class'].unique())}")

# Impute missing pollutants with location-level median
pollutants   = ['O3', 'CO', 'SO2', 'NO2']
before_nulls = df[pollutants].isnull().sum().sum()
print(f"\nMissing pollutant values before imputation: {before_nulls}")
for col in pollutants:
    n = df[col].isnull().sum()
    if n > 0:
        df[col] = df.groupby('Location')[col].transform(
            lambda x: x.fillna(x.median()))
        df[col] = df[col].fillna(df[col].median())
        print(f"  {col}: {n} nulls filled with location-median")
print(f"Missing after imputation: {df[pollutants].isnull().sum().sum()}")

# Outlier capping (IQR 1.5x)
print("\nOutlier treatment (IQR 1.5x):")
numeric_cols = ['PM2.5','PM10','AQI','O3','CO','SO2','NO2']
for col in numeric_cols:
    Q1, Q3  = df[col].quantile(0.25), df[col].quantile(0.75)
    IQR     = Q3 - Q1
    lo, hi  = Q1 - 1.5*IQR, Q3 + 1.5*IQR
    n_out   = ((df[col] < lo) | (df[col] > hi)).sum()
    df[col] = df[col].clip(lower=lo, upper=hi)
    if n_out > 0:
        print(f"  {col}: {n_out} outliers capped to [{lo:.1f}, {hi:.1f}]")

# 2.4 FEATURE ENGINEERING

print("\n" + "=" * 60)
print("STEP 4: Feature engineering")
print("=" * 60)

# Country
df['Country'] = df['Location'].apply(
    lambda x: 'Nepal' if 'Nepal' in str(x) else 'India')
print(f"Country: {df['Country'].value_counts().to_dict()}")

# Season
season_map = {1:'Winter',2:'Winter',3:'Winter',4:'Pre-Monsoon',
              5:'Pre-Monsoon',6:'Monsoon',7:'Monsoon',8:'Monsoon',
              9:'Monsoon',10:'Post-Monsoon',11:'Post-Monsoon',12:'Winter'}
df['Season'] = df['Month'].map(season_map)

# Time of day
def time_of_day(h):
    if pd.isna(h): return 'Unknown'
    h = int(h)
    if   5  <= h < 12: return 'Morning'
    elif 12 <= h < 17: return 'Afternoon'
    elif 17 <= h < 21: return 'Evening'
    else:              return 'Night'
df['TimeOfDay'] = df['Hour_int'].apply(time_of_day)

# WHO exceedance 
WHO_LIMIT = 15.0
df['WHO_Exceedance'] = (df['PM2.5'] > WHO_LIMIT).astype(int)
print(f"WHO PM2.5 exceedance: {df['WHO_Exceedance'].mean()*100:.1f}% of records")

# AQI severity bracket
def aqi_bracket(aqi):
    if   aqi <= 50:  return 1
    elif aqi <= 100: return 2
    elif aqi <= 150: return 3
    elif aqi <= 200: return 4
    elif aqi <= 300: return 5
    else:            return 6
df['AQI_Bracket'] = df['AQI'].apply(aqi_bracket)

# Composite Pollution Index 
def normalise(s):
    rng = s.max() - s.min()
    return (s - s.min()) / (rng if rng > 0 else 1)

df['Pollution_Index'] = (
    0.35 * normalise(df['PM2.5']) +
    0.25 * normalise(df['AQI'])  +
    0.15 * normalise(df['PM10']) +
    0.10 * normalise(df['NO2'])  +
    0.10 * normalise(df['SO2'])  +
    0.05 * normalise(df['O3'])
).round(4)

# Health risk label
risk_map = {1:'Low',2:'Moderate',3:'Elevated',4:'High',5:'Very High',6:'Hazardous'}
df['Health_Risk'] = df['AQI_Bracket'].map(risk_map)

# PM2.5 as multiple of WHO limit
df['PM25_WHO_Multiple'] = (df['PM2.5'] / WHO_LIMIT).round(2)

print(f"Pollution_Index: {df['Pollution_Index'].min():.3f} – {df['Pollution_Index'].max():.3f}")
print(f"PM25_WHO_Multiple (mean): {df['PM25_WHO_Multiple'].mean():.1f}x the safe limit")

#UNIQUE READINGS VIEW

print("\n" + "=" * 60)
print("STEP 5: Creating unique readings view (for trend analysis)")
print("=" * 60)

key_cols = ['Location','Year','Month','Day','Hour']
readings = df.drop_duplicates(subset=key_cols).copy().reset_index(drop=True)
print(f"Unique readings: {len(readings)} (from {len(df):,} total rows)")
print("Per location:\n", readings['Location'].value_counts().to_string())

#RESHAPING & AGGREGATION

print("\n" + "=" * 60)
print("STEP 6: Reshaping & aggregation")
print("=" * 60)

# Pivot: mean PM2.5 by Location x Month
pivot_monthly = readings.pivot_table(
    values='PM2.5', index='Location', columns='Month', aggfunc='mean').round(1)
print("\nPivot — Mean PM2.5 by Location x Month:\n", pivot_monthly.to_string())

# Daily averages
daily_avg = df.groupby(['Location','Country','Date']).agg(
    PM2_5_mean      = ('PM2.5','mean'),
    AQI_mean        = ('AQI','mean'),
    PM10_mean       = ('PM10','mean'),
    WHO_Exceed_pct  = ('WHO_Exceedance','mean'),
    Pollution_Index = ('Pollution_Index','mean'),
    Readings        = ('PM2.5','count')
).reset_index().round(3)

# Location summary with GPS
location_summary = readings.groupby(['Location','Country']).agg(
    PM2_5_mean      = ('PM2.5','mean'),
    PM2_5_max       = ('PM2.5','max'),
    AQI_mean        = ('AQI','mean'),
    WHO_Exceed_pct  = ('WHO_Exceedance','mean'),
    Pollution_Index = ('Pollution_Index','mean'),
    PM25_WHO_Multi  = ('PM25_WHO_Multiple','mean'),
    Readings        = ('PM2.5','count')
).reset_index().round(3)

coords = {
    'Biratnagar, Nepal'            : (26.4525, 87.2718),
    'Mumbai'                       : (19.0760, 72.8777),
    'ITO, Delhi'                   : (28.6280, 77.2410),
    'Bengaluru'                    : (12.9716, 77.5946),
    'Tamil Nadu'                   : (13.0827, 80.2707),
    'Knowledge park, Greater Noida': (28.4744, 77.5040),
    'New Ind Town, Faridabad'      : (28.4089, 77.3178),
    'Dimapur, Nagaland'            : (25.9044, 93.7271),
}
location_summary['Latitude']  = location_summary['Location'].map(
    lambda x: coords.get(x,(np.nan,np.nan))[0])
location_summary['Longitude'] = location_summary['Location'].map(
    lambda x: coords.get(x,(np.nan,np.nan))[1])

print("\nLocation summary:\n",
      location_summary[['Location','Country','PM2_5_mean','AQI_mean',
                         'WHO_Exceed_pct','PM25_WHO_Multi']].to_string(index=False))

# AQI class distribution
aqi_dist = df.groupby(['Location','AQI_Class']).size().reset_index(name='Count')
aqi_dist['Pct'] = (aqi_dist.groupby('Location')['Count']
                   .transform(lambda x: x/x.sum()*100)).round(1)

# Correlation matrix
corr_cols   = ['PM2.5','PM10','AQI','O3','CO','SO2','NO2','Pollution_Index']
corr_matrix = readings[corr_cols].corr().round(3)
print("\nCorrelation matrix (PM2.5 / AQI focus):\n",
      corr_matrix[['PM2.5','AQI']].round(2).to_string())


#  SAVE ALL OUTPUTS

print("\n" + "=" * 60)
print("STEP 7: Saving cleaned files")
print("=" * 60)

df.to_csv('data/cleaned_aqi.csv', index=False)
readings.to_csv('data/readings.csv', index=False)
daily_avg.to_csv('data/daily_avg.csv', index=False)
location_summary.to_csv('data/location_summary.csv', index=False)
aqi_dist.to_csv('data/aqi_distribution.csv', index=False)
corr_matrix.to_csv('data/correlation_matrix.csv')
pivot_monthly.to_csv('data/pivot_monthly.csv')

for f in ['cleaned_aqi.csv','readings.csv','daily_avg.csv',
          'location_summary.csv','aqi_distribution.csv',
          'correlation_matrix.csv','pivot_monthly.csv']:
    print(f"  Saved: data/{f}")

print(f"\nFull dataset   : {len(df):,} rows x {df.shape[1]} columns")
print(f"Unique readings: {len(readings)} rows x {readings.shape[1]} columns")
print("\nEngineered features added:")
for c in ['Hour_int','Date','Country','Season','TimeOfDay',
          'WHO_Exceedance','AQI_Bracket','Pollution_Index',
          'Health_Risk','PM25_WHO_Multiple']:
    print(f"  + {c}")

print("\nTask 2 complete.")
