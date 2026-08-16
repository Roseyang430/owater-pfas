# O.Water PFAS Analysis

Analysis of PFAS detections in U.S. drinking water systems using EPA UCMR5 public monitoring data.

This project processes EPA UCMR5 PFAS public monitoring data.

## What's Inside
- `process_epa_ucmr5_data.py` - Converts the EPA UCMR5 zip into the analysis-ready CSV
- `pfas_data.csv` - Processed system-level PFAS detection data across US water systems
- `pfas-report.html` - Interactive report with visualizations
- `chart_*.png` - Data visualizations

## Reproduce the Data

Download the EPA UCMR5 PFAS data zip and either place it at:

```bash
data/EPA_UCMR5_PFAS_data.zip
```

or point the script to it:

```bash
UCMR5_ZIP_PATH=/path/to/EPA_UCMR5_PFAS_data.zip python3 process_epa_ucmr5_data.py
python3 analysis_overview.py
python3 analysis_deep.py
python3 build_report.py
```

The raw EPA zip is ignored by git because it is large. The committed CSV is aggregated at the water-system and PFAS-compound level, using the maximum detected result for each regulated compound.

## License
MIT
