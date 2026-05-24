# Data-Driven Load Flow Analyzer

An open-source, ML-based load flow analyser for the **IEEE 14-bus** power system, packaged as an interactive web dashboard. The tool replaces iterative Newton–Raphson load flow calculations with a gradient-boosting ensemble that produces near-instantaneous predictions for bus voltages, phase angles, line currents, power flows, and system losses across 32 contingency topologies.

This repository is the companion to the SoftwareX submission:

> **"Data-Driven Load Flow Analyser — An AI-Based Power System Monitoring Tool"**
> S. Uddin, M. Waleed, H. Babar, M. Ali — NED University of Engineering & Technology, Department of Electrical Engineering. *SoftwareX*, 2026 (under review).

---

## Key features

- **7-model gradient-boosting ensemble** — XGBoost, LightGBM, and CatBoost models (one per output group)
- **Memory-efficient inference** — stream-loads one model at a time; peak RAM bounded at a single model regardless of batch size
- **32 contingency topologies** — base case, 4 generator outages, 15 line outages, 11 load outages, 1 shunt outage
- **Three-tab interactive dashboard** — manual data entry, time-series results explorer, and ML-vs-NR comparison
- **Batch processing** — annual hourly profiles (up to 8,760 rows) processed in under a minute
- **Robust handling of NR divergence** — ML predictions remain available when the traditional solver fails
- **CSV export** — full results exportable for downstream analysis in MATLAB, Python, or spreadsheets

---

## Quick start

### Prerequisites

- Python **3.12 or later**
- ~200 MB free disk space (for trained models)
- A modern web browser (Chrome, Firefox, Edge)

### Installation

```bash
# 1. Clone the repository
git clone https://github.com/<your-username>/data-driven-load-flow-analyser.git
cd data-driven-load-flow-analyser

# 2. Install Python dependencies
pip install -r requirements.txt

# 3. (Optional) Install pandapower for the NR validation feature
pip install pandapower

# 4. Download the trained models (60–70 MB each, hosted as GitHub Release assets)
python download_models.py
```

### Running the dashboard

```bash
python main.py
```

The dashboard starts on `http://127.0.0.1:8000`. Open this URL in your browser.

---

## Usage

### 1. Single-scenario prediction

1. Open the **Data Entry** tab
2. Enter active (P₁–P₁₁) and reactive (Q₁–Q₁₁) power demands for each load bus
3. Select a contingency topology from the dropdown
4. Click **Run Load Flow Analysis**
5. View the results in the **Dashboard & Results** tab

### 2. Batch annual analysis

1. On the **Data Entry** tab, drag your annual profile file (CSV, XLSX, or Parquet) into the upload zone
   - Maximum 8,760 rows × 23 columns: `P1..P11, Q1..Q11, topology_code`
2. Click **Upload & Run Batch Inference**
3. Navigate the results using the time-series slider, autoplay, or keyboard arrows (←/→/Space)
4. Use the worst-hour / best-hour summary cards to jump to extremes
5. Export results with the **Export CSV** button

A sample test dataset is included at [`examples/chunk_1.parquet`](examples/chunk_1.parquet) (1 MB, 8,760 hourly rows).

### 3. ML vs Newton–Raphson validation

1. Open the **AI vs Newton-Raphson** tab
2. Enter a scenario manually or upload a small batch (max 10 rows)
3. Click **Run Comparison**
4. Review the side-by-side error metrics, charts, and per-bus/per-line tables
5. When NR fails to converge, the dashboard automatically shows the ML-only result in a dedicated divergence panel

---

## Repository structure

```
data-driven-load-flow-analyser/
│
├── main.py                          FastAPI backend with all REST endpoints
├── requirements.txt                 Python dependencies
├── download_models.py               Helper script to fetch trained models from GitHub Releases
│
├── templates/
│   └── index.html                   Single-page web frontend
│
├── static/
│   ├── script.js                    Frontend logic and Chart.js bindings
│   ├── style.css                    Stylesheet
│   └── images/                      32 single-line topology diagrams (one per contingency code)
│
├── scalers/                         Preprocessing transformers (committed; ~1 KB each)
│   ├── numerical_scaler.pkl         StandardScaler for P/Q inputs
│   ├── categorical_encoder.pkl      OneHotEncoder for topology code
│   └── *_target_scaler.pkl          Per-output inverse-transform scalers
│
├── models/                          (Not committed — downloaded via `download_models.py`)
│   ├── Voltage_Model.joblib         Bus voltage predictor
│   ├── Angle_Model.joblib           Phase angle predictor
│   ├── SendingP_Model.joblib        Sending-end active-power predictor
│   ├── ReceivingP_Model.joblib      Receiving-end active-power predictor
│   ├── SendingQ_Model.joblib        Sending-end reactive-power predictor
│   ├── ReceivingQ_Model.joblib      Receiving-end reactive-power predictor
│   └── Iline_Model.joblib           Line-current predictor
│
├── examples/
│   └── chunk_1.parquet              Sample annual load profile (8,760 hours)
│
├── scripts/
│   └── nr_baseline_benchmark.py     Reproduces the NR baseline timing reported in the paper
│
├── README.md                        This file
└── LICENSE                          MIT License
```

---

## Reproducing the SoftwareX results

The paper reports a 6.4× speed-up of the ML pipeline over the Newton–Raphson baseline on an 8,760-hour annual analysis. To reproduce the NR baseline measurement:

```bash
python scripts/nr_baseline_benchmark.py
```

The script reads `examples/chunk_1.parquet`, runs `pandapower`'s Newton–Raphson solver on every hour in base-case topology, and prints the total wall-clock time. Edit the `PARQUET_PATH` constant at the top of the script if you want to point it at a different input file.

To reproduce the ML inference timing, upload the same file through the **Batch processing** workflow in the dashboard and observe the response time.

---

## Architecture overview

```
   ┌─────────────────────────────────────────┐
   │  User (Web Browser)                     │
   └─────────────────┬───────────────────────┘
                     │  HTTPS / JSON
   ┌─────────────────┴───────────────────────┐
   │  Presentation Layer (Frontend)          │
   │  HTML/CSS/JS · Bootstrap 5 · Chart.js   │
   └─────────────────┬───────────────────────┘
                     │  REST / JSON
   ┌─────────────────┴───────────────────────┐
   │  Application Layer (FastAPI Backend)    │
   │  /predict_single  /predict_batch        │
   │  /compare  /compare_batch  /health      │
   └─────────┬────────────────────┬──────────┘
             │ predict()          │ subprocess
   ┌─────────┴───────┐  ┌─────────┴──────────┐
   │ Inference Layer │  │ Validation Layer   │
   │ ML Ensemble     │  │ Newton–Raphson     │
   │ (7 models)      │  │ (pandapower)       │
   └─────────────────┘  └────────────────────┘
```

See **Figure 1** of the SoftwareX paper for the full architecture diagram.

---

## Citation

If you use this software in your research, please cite:

```bibtex
@article{uddin2026loadflow,
  title   = {Data-Driven Load Flow Analyser — An AI-Based Power System Monitoring Tool},
  author  = {Uddin, Sohaib and Waleed, Muhammad and Babar, Hammad and Ali, Mubashir},
  journal = {SoftwareX},
  year    = {2026},
  note    = {Under review}
}
```

(BibTeX with the final DOI and volume to be updated once the paper is published.)

---

## Contributors

| Name | Role | Contact |
|---|---|---|
| **Sohaib Uddin** | Lead developer, ML pipeline, dashboard integration | — |
| **Muhammad Waleed** | Dataset development, contingency formulation | — |
| **Hammad Babar** | Result interpretation, documentation | — |
| **Mubashir Ali** | Code review, simulation support | — |

**Supervision**: Engr. Shariq Shaikh (Supervisor), Dr. Shehnila Zardari (Co-supervisor).
Department of Electrical Engineering, **NED University of Engineering and Technology**, Karachi, Pakistan.

---

## Roadmap

Planned extensions:

- [ ] Integration with live SCADA / PMU streams for real-time monitoring
- [ ] Online learning to adapt models as the grid evolves
- [ ] Generalization to larger transmission networks via graph neural networks
- [ ] N-2 contingency analysis and transient stability prediction
- [ ] Uncertainty quantification for ML predictions

Contributions and feature requests are welcome — please open a GitHub Issue.

---

## License

This project is released under the **MIT License** — see [`LICENSE`](LICENSE) for the full text.

---

## Acknowledgements

The authors gratefully acknowledge the Department of Electrical Engineering at NED University of Engineering and Technology for providing academic environment that made this work possible.
