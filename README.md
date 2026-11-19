# PlayScope — Play Store Category Intelligence Dashboard
A premium-style Streamlit dashboard that compares the **average app rating** and **total review count** for the top 10 Google Play Store categories by installs.

## Features
- Reads the supplied Google Play Store dataset.
- Filters individual apps using all three rules:
  - Average app rating is **4.0 or higher**.
  - App size is **10 MB or larger**.
  - Last updated month is **January** (any year).
- Removes duplicate app names, keeping the record with the latest valid update date.
- Aggregates the filtered apps by category.
- Selects the top 10 categories by total installs.
- Displays a grouped bar chart with:
  - Average rating on the left axis (0–5).
  - Total review count on the right axis.
- Hides the chart outside **3:00 PM to 5:00 PM India Standard Time (IST)**.
- Checks the schedule every 30 seconds while the Streamlit app is open.
- Includes KPI cards and an expandable category data table.

## Project structure
```text
play_store_analytics_dashboard/
│
├── app.py
├── requirements.txt
├── README.md
├── .gitignore
├── .streamlit/
│   └── config.toml
└── data/
    ├── Play Store Data.csv
    └── User Reviews.csv
```
`User Reviews.csv` is included because it was supplied with the project, but the requested chart is based on the Play Store app-level fields and does not require review-text sentiment data.

## Requirements
- Python 3.9 or newer (Python 3.10+ recommended)
- pip
- Streamlit
- pandas
- Plotly

## Setup and run
### 1. Extract the project
Extract the ZIP file and open a terminal in the `play_store_analytics_dashboard` folder.

### 2. Create a virtual environment (recommended)

**Windows**
```bash
python -m venv .venv
.venv\Scripts\activate
```
**macOS / Linux**
```bash
python3 -m venv .venv
source .venv/bin/activate
```

### 3. Install dependencies

```bash
pip install -r requirements.txt
```

### 4. Run the dashboard

```bash
streamlit run app.py
```

Streamlit will print a local URL, usually `http://localhost:8501`. Open it in your browser.

## Data file placement

Keep the CSV files in the `data/` directory with these exact names:

- `Play Store Data.csv`
- `User Reviews.csv`

The app requires these columns in `Play Store Data.csv`:

- `App`
- `Category`
- `Rating`
- `Reviews`
- `Size`
- `Installs`
- `Last Updated`

## Important implementation notes

### Time restriction

The app uses the `Asia/Kolkata` timezone, so the schedule does not depend on the computer's configured timezone. The chart is visible from **15:00 inclusive to 17:00 exclusive**. At exactly 5:00 PM IST it is hidden.

The Streamlit page must remain open and connected for the 30-second fragment refresh to update the visibility automatically. A user can still inspect other dashboard content outside the scheduled window; only the chart is hidden.

### January filter

The current implementation interprets “last update should be Jan month” as **any date in January**, irrespective of year. If your requirement means January of a specific year, update the filter in `app.py` to include the desired year.

### Chart axes

Average ratings range from 0 to 5, while review counts can be very large. The grouped chart therefore uses two y-axes so both metrics remain readable. Bar heights should be interpreted against their own labeled axis.

### Aggregation

Filters are applied to individual app records before category aggregation. Category average rating is the arithmetic mean of the qualifying apps' ratings. Total reviews and installs are summed. Duplicate app names are counted once, using the most recently updated record.

## Troubleshooting

- **Dataset not found:** confirm the CSV is inside `data/` and the filename matches exactly.
- **Missing column error:** check the column names in the Play Store CSV.
- **No categories displayed:** the selected filters may exclude all rows. Verify rating, size, and January update values.
- **Chart not visible:** check India time. It only appears from 3 PM to before 5 PM IST.
- **Port already in use:** run `streamlit run app.py --server.port 8502`.

## License and data

This project is an educational analytics dashboard. Keep the dataset's original attribution and license information when redistributing it.
