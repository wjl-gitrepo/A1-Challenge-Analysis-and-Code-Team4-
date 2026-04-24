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

| Target city | Scenario | Best model | Gap (spatial holdout) | F1 macro (spatial holdout) |
|---|---|---|---|---|
| Freetown | Blind (train Santiago + Rio) | Random Forest | 0.003 | 0.689 |
| Santiago | Mixed training (all 3 cities) | Random Forest | 0.18 (expected — target in training) | 0.66 |
| Rio | Mixed training (all 3 cities) | see notebook | — | — |

Freetown's near-zero gap plus F1 macro of 0.69 was achieved with no target labels during training — a strong demonstration that per-city normalization + stratified pseudo-labeling enables meaningful cross-climate transfer.

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
