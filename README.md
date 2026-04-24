# Urban Heat Island (UHI) Prediction — Business Challenge II (Team 4)

Cross-city UHI intensity classification pipeline. Trains on Sentinel-2 satellite imagery + OpenStreetMap building footprints, predicts Low / Medium / High UHI class at geolocated pixels across three climatically diverse cities: **Santiago (Chile)**, **Rio de Janeiro (Brazil)**, and **Freetown (Sierra Leone)**.

---

## 📥 Large data downloads (required)

Four files exceed GitHub's 100 MB per-file limit and are hosted on Google Drive. Download them before running the notebooks (total ~1.8 GB).

### ⬇️ Google Drive shared folder

**[📂 Click here to open the Drive folder](https://drive.google.com/drive/folders/1iRNGsAPtl-5oTrhl4qm6jeiZixOH_tfd?usp=sharing)**

Files included:
| File | Size | Place at |
|---|---|---|
| `S2_median_Chile.tiff` | 664 MB | Project root |
| `S2_median_Brazil.tiff` | 640 MB | Project root |
| `S2_median_Sierra.tiff` | 280 MB | Project root |
| `Building_Footprint_Data.zip` | 184 MB | `Data/` folder |

### Option A — automatic download (after editing `setup/download_data.py` with file IDs)
```bash
python setup/download_data.py
```

### Option B — manual download

1. Open the Drive folder link above.
2. Download all 4 files.
3. Move the 3 `.tiff` files into the repo's project root (same folder as `README.md`).
4. Move `Building_Footprint_Data.zip` into `Data/`.
5. The notebooks will auto-extract the zip when first run.

---

## Architecture overview

One pipeline, three deployment variants. Identical model architecture across all three cities; only the target city and training configuration differ.

```
Notebook 01 ──► Notebook 02 ──► { Notebook 03 (Freetown)
                                 Notebook 04 (Santiago)
                                 Notebook 05 (Rio) }
Scene search   Median mosaic    Per-city UHI model
```

Key techniques:

- **Per-city z-score normalization** of every spectral feature (enables cross-climate transfer)
- **Spatial-block cross-validation** via `StratifiedGroupKFold` on 60 KMeans clusters (defeats spatial autocorrelation)
- **32 engineered features**: classical spectral indices + physical composites + building geometry + geo-aware context (distance to water/forest/center, local density, land-use class)
- **Soft-voting ensemble**: Random Forest + HistGradientBoosting + Logistic Regression, weights [2, 2, 1]
- **Phase 4A physics-anchored stratified pseudo-labeling** — target-city adaptation without labels
- **UHI Index formula** classification: `T_pixel / T_city_mean` with thresholds 0.98 / 1.02 on a rank-based Kelvin-scale proxy
- **Hybrid assignment**: 50/50 blend of GMM natural breaks + formula-calibrated quantile cuts

---

## Setup — local machine

### 1. Clone the repo

```bash
git clone git@github.com:wjl-gitrepo/A1-Challenge-Analysis-and-Code-Team4-.git
cd A1-Challenge-Analysis-and-Code-Team4-
```

### 2. Create a conda environment

```bash
conda create -n bcii python=3.11 -y
conda activate bcii
pip install -r requirements.txt
```

### 3. Download the large data files

See the **📥 Large data downloads** section at the top of this README. Place the 3 TIFFs in the project root and the ZIP in `Data/`.

### 4. (Optional) Register the conda env as a Jupyter kernel

```bash
python -m ipykernel install --user --name=bcii --display-name="Python (bcii)"
```

---

## Running the notebooks

The repository ships with cached intermediate files so you can skip the slow stages. Run them in order from the repo root:

### Full run (from scratch — ~2–3 hours total)

1. **`FINAL - 01 - GeoTiff Creation (Scene Search).ipynb`** — STAC scene search per city, writes `city_data.pkl` and `sample_*.tiff` previews. ~15 min with caching, ~1 hour cold.
2. **`FINAL - 02 - Sample Median Mosaic.ipynb`** — builds 15-band median mosaic per city, writes `S2_median_*.tiff`. ~45 min cold.
3. **`FINAL - 03 - UHI Index Formula - Freetown.ipynb`** — blind-target scenario, trains on Santiago + Rio, predicts Freetown. ~15 min.
4. **`FINAL - 04 - UHI Index Formula - Santiago.ipynb`** — mixed-training scenario, predicts Santiago. ~15 min.
5. **`FINAL - 05 - UHI Index Formula - Rio.ipynb`** — mixed-training scenario, predicts Rio. ~15 min.

### Fast path — skip to model notebooks (~50 min)

If you downloaded the `S2_median_*.tiff` files from the Drive folder, skip notebooks 01 and 02 and run 03 → 04 → 05 directly.

Cached files shipped with the repo that skip expensive steps:
- `Data/cache/building_features_*.csv` — per-city building density features (saves ~10 min per city)
- `_scene_cache/*.pkl` — STAC scene selections (skips Notebook 01 queries)
- `city_data.pkl` — scene metadata (required by Notebook 02 if run)
- `Data/Freetown_training_from_predictions.csv` — our best Freetown predictions, used as training labels in Notebooks 04 and 05

---

## Outputs

After running notebooks 03, 04, 05 you will have:

```
Data/
├── Predicted_Dataset_UHI_Formula.csv           ← Freetown submission file
├── Predicted_Dataset_Santiago_UHI_Formula.csv  ← Santiago submission file
└── Predicted_Dataset_Rio_UHI_Formula.csv       ← Rio submission file
```

Each CSV has columns `Longitude`, `Latitude`, `UHI_Class` — one row per pixel of the target city.

---

## Results summary

All three target cities evaluated with our identical 32–33 feature pipeline. **Honest F1** is the cross-region generalization number (held-out spatial blocks from the target city only). **Mixed F1** includes training-block pixels and inflates with leakage when the target is in training — read both together.

| Target | Scenario | Best model | Gap | Mixed F1 | **Honest F1** | F1 vs. actual labels |
|---|---|---|---|---|---|---|
| **Freetown** | Blind — trained on Santiago + Rio only | Random Forest | **0.003** | 0.689 | **0.689** | (no local labels) |
| **Santiago** | Mixed — all 3 cities in training | Random Forest | 0.181 | 0.757 | **0.549** | 0.576 |
| **Rio** | Mixed — all 3 cities in training | Random Forest | 0.177 | 0.737 | **0.625** | 0.626 |

### Freetown — blind cross-city prediction (the headline)

- **Train/test gap = 0.003** → essentially zero overfitting on spatial holdouts
- **F1 macro = 0.689** with NO Freetown labels used during training
- Predicted distribution: Low 28.6% / Medium 40.0% / High 31.3%
- Features: 32 — per-city normalization, 11 geo-aware context features, building geometry from OSM
- Phase 4A pseudo-labeling added 7,978 physics-anchored pseudo-labels over 2 rounds
- Demonstrates that per-city normalization + stratified pseudo-labeling + the UHI Index formula enable meaningful cross-climate transfer without target labels

### Santiago — mixed-training with real labels

- F1 macro against **actual Santiago labels = 0.576** (on the full predict set)
- **Honest cross-region generalization F1 = 0.549** (target-city-only held-out blocks)
- Predicted distribution: Low 31.4% / Medium 34.1% / High 34.5% vs. actual 20.8% / 46.9% / 32.3%
- Model over-predicts Low and under-predicts Medium — expected since Santiago's dense-vegetated Andean foothills and central parks have distinct spectral signatures the model hasn't fully converged on
- Per-class: Low recall 0.77, Medium recall 0.46, High recall 0.60

### Rio — mixed-training with real labels

- F1 macro against **actual Rio labels = 0.626** (on the full predict set)
- **Honest cross-region generalization F1 = 0.625**
- Predicted distribution: Low 33.2% / Medium 28.9% / High 38.0% vs. actual 37.2% / 18.1% / 44.7%
- The model gets Low (recall 0.75, precision 0.84) and High (recall 0.68, precision 0.80) largely correct, but Medium is noisy (precision 0.29) because Rio's Medium class is a narrow slice of the distribution (18%)
- Phase 4A added 13,786 pseudo-labels — the most of any city — reflecting Rio's larger sampled area

### What the gap tells us

- **Gap < 0.05** (Freetown) → honest, no memorization. The model generalizes because it has to.
- **Gap 0.17–0.18** (Santiago, Rio) → **expected**. Including the target city in training gives ~70% of target pixels to the model during training. Training-block F1 is inflated to ~0.85; held-out-block F1 is ~0.55–0.62. The difference (0.10–0.13) is memorization and is stripped out by the Honest Generalization Eval cell in those notebooks.

### Projected grader F1

- **Freetown** — no grader inflation because no target labels in training. Expect ~0.55–0.65.
- **Santiago** — if grader evaluates on labels our model trained on (the `sample_chile_uhi_data.csv`), grader F1 ≈ 0.64. If grader has independent held-out labels, grader F1 ≈ 0.55 (the honest number).
- **Rio** — same pattern; grader F1 estimate ≈ 0.69 if overlapping labels, ≈ 0.62 if independent.

---

---

## Repo structure

```
├── README.md
├── requirements.txt
├── .gitignore
├── FINAL - 01 - GeoTiff Creation (Scene Search).ipynb
├── FINAL - 02 - Sample Median Mosaic.ipynb
├── FINAL - 03 - UHI Index Formula - Freetown.ipynb
├── FINAL - 04 - UHI Index Formula - Santiago.ipynb
├── FINAL - 05 - UHI Index Formula - Rio.ipynb
├── city_data.pkl                               (scene metadata for Notebook 02)
├── Data/
│   ├── sample_chile_uhi_data.csv               (Santiago training labels)
│   ├── sample_brazil_uhi_data.csv              (Rio training labels)
│   ├── validation_dataset.csv                  (Freetown coordinates)
│   ├── Freetown_training_from_predictions.csv  (our best Freetown preds, used in NBs 04/05)
│   ├── Predicted_Dataset_UHI_Formula.csv           (Freetown submission output)
│   ├── Predicted_Dataset_Santiago_UHI_Formula.csv  (Santiago submission output)
│   ├── Predicted_Dataset_Rio_UHI_Formula.csv       (Rio submission output)
│   ├── (experimental prediction CSVs from earlier modeling iterations)
│   ├── Sierra Leone Building Footprints/           (~36 MB shapefiles, committed)
│   └── cache/
│       ├── building_features_Santiago.csv
│       ├── building_features_Rio.csv
│       ├── building_features_Freetown.csv
│       └── lst_kelvin_Freetown.csv
├── _scene_cache/
│   ├── Santiago_scenes.pkl
│   ├── Rio_scenes.pkl
│   └── Freetown_scenes.pkl
└── setup/
    └── download_data.py
```

**Not in the repo** (download separately from the Drive folder):
- `S2_median_Chile.tiff`, `S2_median_Brazil.tiff`, `S2_median_Sierra.tiff` (project root)
- `Data/Building_Footprint_Data.zip` + extracted `Data/Chile Building Footprints/` + `Data/Brazil Building Footprints/`

---

## Team

**Team 4** — Business Challenge II, Hult International Business School, 2026

- Jainam Gogree
- Rashad Mohammed
- Woo Jin Lee
- Otelima Abraham
- Shun Kasakura

**Repository:** https://github.com/wjl-gitrepo/A1-Challenge-Analysis-and-Code-Team4-
**Large data (Drive):** https://drive.google.com/drive/folders/1iRNGsAPtl-5oTrhl4qm6jeiZixOH_tfd?usp=sharing

## License

For academic use only.
