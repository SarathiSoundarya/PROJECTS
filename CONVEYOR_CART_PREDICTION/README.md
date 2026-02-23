# 🚀 Conveyor Cart Availability Prediction — XGBoost

Predict the **number of available carts** in a conveyor system of 25 carts using machine learning.

This project uses **XGBoost regression models** trained on conveyor status signals with time-series feature engineering to forecast cart availability for multiple future horizons.

The repository also contains an intuitive **Streamlit app** for running predictions and visualizing results.

---

# 📌 Project Overview

Industrial conveyor systems continuously change state:

* Full carts
* Empty carts
* Maintenance carts

Understanding these patterns allows us to predict **future cart availability**, which helps in:

✅ Production planning
✅ Throughput optimization
✅ Bottleneck detection
✅ Maintenance awareness

---

# 🎯 Prediction Targets

The system predicts available carts at:

* 15 minutes
* 30 minutes
* 45 minutes
* 60 minutes

Each horizon has its own trained XGBoost model.

---

# 🎥 Demo

<img src="images/cartprediction_gif.gif" width="750"/>

[Click to Watch the full working demo](https://drive.google.com/file/d/15Msch47yB5oHBq4iHv0eoUzRWXawmY_i/view?usp=sharing)

---

# 🧠 XGBoost Intuition (Simple)

XGBoost builds trees sequentially:

1. First tree learns the major pattern.
2. Next tree learns the residual error.
3. Additional trees refine predictions.

Mathematically:

ŷᵗ = ŷᵗ⁻¹ + η fₜ(x)

---

# 📊 Exploratory Data Analysis (EDA) Findings

EDA was performed on conveyor state durations after removing outliers using the **P10–P80 percentile range** to obtain stable estimates.

Average duration per state:

* **Step 0 — Occupied carts:** **390.52 minutes**
* **Step 1 — Empty carts:** **157.71 minutes**
* **Step 2 — Maintenance carts:** **90.96 minutes**

### Key Observations

✅ Occupied state dominates operational time
✅ Empty cycles are shorter and more dynamic
✅ Maintenance periods are sparse but impactful
✅ Strong temporal continuity exists in the system
✅ Historical behavior strongly influences future state

These insights directly guided the feature engineering strategy.

---

# ⚙️ Feature Engineering Strategy

Raw conveyor status signals were first aggregated into:

* Number of full carts
* Number of empty carts
* Number of carts under maintenance

From these base signals, several time-series features were engineered to capture system dynamics:

### Temporal Memory (Lag Features)

Previous time-step values were added to capture **short-term dependency and inertia** in cart movement.

### Rolling Statistics

Rolling mean and rolling standard deviation were computed over a sliding time window to represent:

* Local trends
* Stability vs variability
* Operational smoothness

### Momentum / Change Features

First-order differences were calculated to capture **rate of change** in cart counts.

### Future Target Creation

For supervised learning, the target variable was created by shifting the future cart availability by the required prediction horizon (15/30/45/60 minutes).

---

# 📈 Model Evaluation

Models were trained separately for each prediction horizon using a time-aware train/test split.

| Horizon (Minutes) | Training Samples | Testing Samples | MAE   | R² Train | R² Test |
| ----------------- | ---------------- | --------------- | ----- | -------- | ------- |
| 15                | 21,087           | 5,272           | 0.624 | 0.898    | 0.867   |
| 30                | 21,075           | 5,269           | 0.903 | 0.835    | 0.791   |
| 45                | 21,063           | 5,266           | 1.160 | 0.768    | 0.689   |
| 60                | 21,051           | 5,263           | 1.321 | 0.717    | 0.609   |

### 📌 Interpretation

* Shorter horizons achieve higher accuracy due to stronger temporal correlation.
* Performance gradually decreases as horizon increases (expected behavior).
* Even at 60 minutes, the model retains meaningful predictive power.

---

# 🏗️ Architecture Flow

Data → Resampling → Feature Engineering → XGBoost Models → Predictions → Visualization

---

# 🖥️ Streamlit Application

The UI allows:

* CSV upload
* Prediction execution
* Result visualization
* Time-series prediction plots

---

# ⚡ Installation

```bash
pip install -r requirements.txt
```

---

# ▶️ Run Application

```bash
streamlit run app.py --server.port 8700
```

---

# 👩‍💻 Author

Soundarya Sarathi
