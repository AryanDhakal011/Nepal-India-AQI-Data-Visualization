# South Asia AQI Dashboard

**🌍 Air Pollution Data Visualization (Nepal & India)**

This project analyzes and visualizes air pollution trends across major cities in Nepal and India using Python. By transforming raw environmental data into meaningful visual insights, the project highlights pollution severity, seasonal patterns, and health risks—supporting data-driven decision-making aligned with Sustainable Development Goal 13: Climate Action.

The analysis is based on 12,240 air quality observations across 8 cities, focusing on key pollutants such as PM2.5, PM10, NO₂, SO₂, CO, and O₃.

## Objectives
- Analyze air pollution trends across South Asian cities
- Compare pollution levels against WHO safety standards
- Identify seasonal and geographic patterns
- Build interactive and static visualizations
- Provide actionable insights for policymakers and stakeholders

## Key Insights
- Over 97% of PM2.5 readings exceed WHO safe limits
- Cities like Delhi show pollution levels up to 23× higher than safe thresholds
- Northern Indian cities exhibit extreme and volatile pollution spikes
- Nepal (Biratnagar) shows consistent long-term exposure rather than spikes
- Pollution peaks significantly during winter seasons

## Tech Stack
- Python
- Pandas – Data manipulation & cleaning
- NumPy – Numerical computations
- Matplotlib & Seaborn – Statistical visualizations
- Plotly – Interactive charts
- Streamlit – Dashboard development
- Folium – Geospatial mapping

## What is included
- `dashboard.py` — Streamlit app entrypoint
- `data/` — CSV datasets used by the dashboard
- `requirements.txt` — pinned Python dependencies

## Run locally
1. Open a terminal in this repository.
2. Create a virtual environment (recommended):
   - `python -m venv .venv`
   - `.\.venv\Scripts\Activate`
3. Install dependencies:
   - `pip install -r requirements.txt`
4. Run the app:
   - `streamlit run dashboard.py`

## Free deployment on Streamlit Community Cloud
1. Push this repository to GitHub.
2. Open https://share.streamlit.io and sign in with GitHub.
3. Click **New app**.
4. Select this repository and choose `main` (or your branch) as the branch.
5. Set the app file path to `streamlit_app.py`.
6. Click **Deploy**.

Streamlit Cloud will install dependencies from `requirements.txt`, and it will also install system packages from `packages.txt`.

## Runtime pin
A `runtime.txt` file has been added to force Streamlit Cloud to use Python 3.11.18 instead of the default Python 3.14 environment.

## Fix for the current build failure
If deployment gets stuck while installing `pandas` or `streamlit`, stop the app and redeploy after these changes.

The build error was caused by `pillow` needing zlib/JPEG system headers. `packages.txt` now installs:
- `build-essential`
- `python3-dev`
- `zlib1g-dev`
- `libjpeg-dev`
- `libpng-dev`
- `gfortran`
- `libopenblas-dev`
- `liblapack-dev`
- `pkg-config`
- `libopenblas-dev`
- `liblapack-dev`

These packages ensure the Streamlit Cloud build environment can compile any dependencies that need native extensions during install.

## Redeploy after changes
1. Stop the current app deployment on Streamlit Cloud.
2. Refresh the app page.
3. Click **Deploy** again.
4. Wait for the build logs to finish and the app to launch.

## Notes
- The dashboard loads data from `data/cleaned_aqi.csv`, `data/readings.csv`, and `data/location_summary.csv`.
- If you update the data files, repush the repo and Streamlit Cloud will redeploy automatically.
