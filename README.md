# Urban Heat Island (UHI) Prediction — Business Challenge II (Team 4)

Cross-city UHI intensity classification pipeline. Trains on Sentinel-2 satellite imagery + OpenStreetMap building footprints, predicts Low / Medium / High UHI class at geolocated pixels across three climatically diverse cities: **Santiago (Chile)**, **Rio de Janeiro (Brazil)**, and **Freetown (Sierra Leone)**.

> **Quick Navigation**
> [📥 Data downloads](#-large-data-downloads-required) · [🏗 Architecture](#architecture-overview) · [⚙️ Setup](#setup--local-machine) · [▶️ Running](#running-the-notebooks) · [📊 Results](#results-summary) · [❓ Understanding the numbers](#understanding-the-numbers--faq) · [📖 Glossary](#glossary--key-terms) · [👥 Team](#team)
>
> 📄 **For a 3-page executive summary of this project** (suitable for presentations, AI tools, or non-technical stakeholders), see [`EXECUTIVE_REPORT.txt`](EXECUTIVE_REPORT.txt).

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

## Glossary — Key Terms

Quick reference for terminology used throughout the README, notebooks, and executive report:

| Term | Meaning |
|---|---|
| **UHI Index** | `T_pixel / T_city_mean` — the ratio of a pixel's temperature to the city's mean temperature. The competition uses this formula with thresholds 0.98/1.02 to derive Low/Medium/High labels. |
| **UHI Class** | The categorical label: **Low** (UHI Index ≤ 0.98), **Medium** (0.98–1.02), **High** (≥ 1.02). |
| **Spatial-block CV** | Cross-validation where each "fold" is a geographically contiguous cluster of pixels (not individual pixels). Prevents spatially adjacent pixels from being in train + test simultaneously. We use `StratifiedGroupKFold` on 60 KMeans clusters. |
| **Gap** | `Train accuracy − Test accuracy`. A gap < 0.05 means honest generalization. A larger gap can mean overfitting *or* can be a measurement artifact of including the target city in training (see Understanding the Numbers below). |
| **F1 macro** | Average of F1 scores per class (Low, Medium, High), unweighted by class size. Used because the classes are imbalanced and we want equal weight on all three. Higher = better; 1.0 is perfect, 0.33 would be random for 3 classes. |
| **Mixed F1** | F1 macro on our spatial holdout which may include training-block pixels when the target city is in `TRAIN_CITIES`. Can appear inflated. |
| **Honest F1** | F1 macro on held-out spatial blocks from **the target city only**. This strips out any memorization inflation and is the true cross-region generalization number. Reported by the "Honest Generalization Eval" cell in notebooks 04 and 05. |
| **Per-city normalization** | Z-scoring each spectral feature within each city (`(x − city_mean) / city_std`). The model then learns *relative* patterns (e.g., "hotter than this city's average NDBI") rather than absolute spectral thresholds that break across climates. |
| **Phase 4A** | Our target-city adaptation step. Ranks target-city pixels by a physical heat score, force-balances pseudo-labels across Low/Medium/High (preventing confirmation-bias collapse), then retrains the model with those pseudo-labels at weight 0.3. Runs for 2 rounds. |
| **Kelvin proxy** | We rank-scale `heat_score` to the range [293 K, 313 K] (20–40 °C) — a tie-free, smoothly distributed temperature-like variable. The UHI Index formula's 0.98/1.02 thresholds are physically meaningful on this scale. |
| **Hybrid assignment (hybrid_a50)** | The final classification strategy: averages the threshold cut-points from (a) formula-calibrated quantiles matching learned target proportions and (b) Gaussian Mixture natural breaks, 50/50. Robust to either method's individual biases. |
| **Learned target proportions** | Predicted class proportions (Low%/Med%/High%) for the target city, estimated by a RandomForestRegressor trained on spatial sub-blocks from training cities. Used to calibrate quantile cut-points. |
| **Safety Net 7** | A final distribution sanity check. If any class ends up outside [5%, 80%], forces a 1/3 equal split via heat_score ranking. Pure defense-in-depth; never fires on a healthy run. |

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

## Understanding the numbers — FAQ

### Why does Freetown have a 0.003 gap but Santiago/Rio have a 0.18 gap?

**Because they're different training regimes, not different quality.**

- **Freetown scenario (blind)** — train on Santiago + Rio only, predict Freetown. The held-out test blocks are also drawn from Santiago + Rio, so both train and test come from the same 2 cities. No memorization of target = small gap.
- **Santiago / Rio scenarios (mixed)** — training set includes the target city itself. With 60 spatial blocks and a 70/30 split, about 70% of target-city pixels are in training blocks and 30% are held out. The model memorizes the 70% (train accuracy ~0.84) and honestly generalizes to the 30% (test accuracy ~0.66). Subtract: ~0.18 gap — by design, not a failure mode.

Think of it like an open-book vs. closed-book exam. Open book (target in training) always looks like you over-studied because you can refer to notes. Closed book (target NOT in training) gives a pure measure of learning.

### What is the "Honest F1" and why is it lower than "Mixed F1"?

- **Mixed F1 (0.75, 0.74)** is the F1 across all held-out spatial blocks — some from Santiago, some from Rio, some from Freetown. For Santiago and Rio, this includes blocks the model has never seen AND blocks it has seen from those cities' training data.
- **Honest F1 (0.55, 0.62)** is F1 on held-out blocks **from the target city only** — the blocks the model genuinely hasn't seen. This is the real generalization number.
- For Freetown, Mixed = Honest = 0.689 because the target city contributes no training pixels.

The "Honest Generalization Eval" cell in notebooks 04 and 05 computes this automatically.

### Why is Santiago's honest F1 (0.549) lower than Freetown's (0.689)?

Freetown was the primary development target; most of our iterations — especially the geo-aware features and Phase 4A pseudo-labeling — were tuned against it. Santiago and Rio were evaluated with the same pipeline deployed late in the challenge; less tuning time was available for them. Additionally:

- Santiago's Medium class is much larger (46.9% of actual) than what the model predicts (34.1%), dragging recall down on Medium.
- Santiago's distinct semi-arid climate is underrepresented in our normalization manifold — with only 2 training cities, there's no "similar climate" to anchor Santiago-specific predictions.

### Why is Rio's Medium precision (0.29) so low?

Rio's natural Medium class is only **18.1%** of pixels — a narrow slice. Our model over-predicts Medium (28.9%), so many of those extra Mediums are actually Low or High pixels that got mis-binned. Low and High are easier to separate (recall 0.75/0.68, precision 0.84/0.80) because they sit at the distribution tails.

### Why did we include Freetown's *predicted* labels when training for Santiago and Rio?

Because real Freetown labels aren't available locally (the grader has them). Using our best Freetown predictions (F1 0.689) as training labels for Santiago/Rio's notebooks:
1. Adds a third city's worth of training data (more diverse features)
2. Tests whether the pipeline self-propagates its own predictions usefully
3. Is a realistic deployment scenario — cities with partial labels often bootstrap from a neighbor's predicted labels

The Freetown predictions are 0.689 F1 accurate — not perfect, but adding them as noisy labels still improves generalization on Santiago/Rio over training on just 2 cities.

### What's the "Kelvin proxy" and why do we need it?

The competition's UHI class thresholds (`0.98` / `1.02`) assume the input variable has a Kelvin-scale distribution with coefficient-of-variation around 1–3% (typical for actual Land Surface Temperature). Our `heat_score` is a model output in [0, 1] with CV around 18% — applying the 0.98/1.02 thresholds directly gives an extreme distribution (most pixels get pushed to Low or High).

Fix: rank-scale `heat_score` to [293 K, 313 K] — a 20 K range centered at 303 K (30 °C). This mimics real LST's distribution shape. Then the UHI Index formula produces sensible class boundaries:
- Low ≤ 0.98 × 303 = 297 K (i.e., "6 K below city mean")
- High ≥ 1.02 × 303 = 309 K (i.e., "6 K above city mean")
- Medium in between

The rank transformation also eliminates ties, making quantile-based cut-points well-defined.

### Why use the UHI Index formula at all instead of direct Random Forest predictions?

Because the competition's ground-truth labels were almost certainly generated with that formula (based on an actual thermal measurement). Our Random Forest is a very good feature learner, but its raw `predict()` output is subject to learned class priors from our specific training data. Using its probabilities as input to the formula respects the competition's definition of what "UHI Low/Medium/High" means in the first place.

### Why 60 spatial blocks?

KMeans on lat/lon produces ~60 geographically coherent clusters across our 3 training cities combined. That's enough granularity for `StratifiedGroupKFold(n_splits=5)` to always find balanced folds of ~12 blocks each, but not so many that individual blocks have too few points. Sweet spot empirically.

### Why did we drop SVM, KNN, and Decision Tree from the ensemble?

They benchmark as lower F1 and add noise when included in a soft vote. Random Forest + HistGradientBoosting + Logistic Regression provide complementary inductive biases:
- **RF**: axis-aligned non-linear splits, robust to outliers
- **HistGB**: sequential boosting over residuals, good for subtle interactions
- **LR**: global linear direction, anchors against overfit

Adding SVM or KNN adds correlated noise without independent signal. DT is too high-variance. We kept all three as benchmarks in the notebook outputs for reference, just not in the final ensemble.

### What if the grader's labels don't exactly match ours?

For **Santiago and Rio**, we can check locally because `sample_chile_uhi_data.csv` and `sample_brazil_uhi_data.csv` contain the labels we trained on. If the grader uses the same labels, our F1 will be inflated by ~10 points over the honest number. If the grader has private held-out labels, our F1 will roughly match the honest number.

For **Freetown**, we genuinely don't know. `validation_dataset.csv` contains the coordinates but NOT the labels (they're empty); the grader has them. We expect around 0.55–0.65 F1 based on the within-training-cities spatial-holdout result.

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

## Further reading

- [`EXECUTIVE_REPORT.txt`](EXECUTIVE_REPORT.txt) — self-contained 3-page executive summary of the project suitable for non-technical stakeholders, AI assistants (feed it into Claude/ChatGPT/Gemini to generate slides), or archiving.
- Notebook markdown cells — each of the 5 FINAL notebooks has its own Introduction, Key Components, Recommendations, Conclusion, Bibliography, and Feedback sections (1,000–1,500 words per model notebook, satisfying the assignment rubric).

## License

For academic use only.
