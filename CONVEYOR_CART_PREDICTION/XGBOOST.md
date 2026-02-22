# XGBoost in 3 Trees

##  Problem

Predict:

y = {Available Carts}


### Features:

*  x_1  = Loaded carts
*  x_2 = Maintenance carts

Example data:

| Loaded | Maintenance | Available |
| ------ | ----------- | --------- |
| 10     | 2           | 28        |
| 15     | 3           | 22        |
| 20     | 5           | 15        |

We use squared error loss:

L = (y - ypred)^2

---

#  Tree 1 (First Split)

### Step 1: Initial Prediction

Start with mean of target:

ypred0 = (28 + 22 + 15)/3 = 21.67

---

### Step 2: Residuals

r = y - ypred0

[+6.33, +0.33, -6.67]

---

### Step 3: Tree 1 Split

Tree finds best split using features.

Suppose we test: Maintenance<=3


Left Node (Maintenance ≤ 3)
2 → residual 6.33  3 → residual 0.33
leaf values= (6.33+0.33)/2 = 3.33  approx

Right Node (Maintenance > 3)
5 → residual −6.67 = -6 approx

```
If Maintenance <= 3 → +3
Else → -6
```

This split reduces squared error the most.

Update (learning rate η = 0.5):

[
\hat{y}^{(1)} = 21.67 + 0.5 \times tree_1


New predictions:

[
[23.17,\ 23.17,\ 18.67]
]

---

# 🌳 Tree 2 (Second Split)

### New Residuals

[
[4.83,\ -1.17,\ -3.67]
]

Tree 2 finds new split:

```
If Loaded <= 15 → +2
Else → -3
```

Update:

[
\hat{y}^{(2)} = \hat{y}^{(1)} + 0.5 \times tree_2
]

New predictions:

[
[24.17,\ 24.17,\ 17.17]
]

---

# 🌳 Tree 3 (Refinement)

Residuals now:

[
[3.83,\ -2.17,\ -2.17]
]

Tree 3 makes small correction:

```
If Maintenance > 4 → -2
Else → +1
```

Update again:

Predictions move closer to:

[
[28,\ 22,\ 15]
]

---

# 🔍 What Is Happening Mathematically?

Each step:

[
\hat{y}^{(t)} = \hat{y}^{(t-1)} + \eta f_t(x)
]

Where:

* ( f_t(x) ) = tree trained on residuals
* Residuals = gradient of loss
* Splits chosen to minimize squared error

---

# 🔎 What Is a Split?

A split is:

> A rule like: “If Maintenance ≤ 3”

It divides data into two groups and assigns each group a prediction value (leaf weight).

The split chosen is the one that **maximally reduces loss**.

---

# 🧠 Key Idea

* Tree 1 learns major pattern.
* Tree 2 corrects remaining mistake.
* Tree 3 fine-tunes.

Final model:

[
\hat{y} = f_1(x) + f_2(x) + f_3(x)
]

---

# 🎤 20-Second Interview Explanation

> XGBoost builds trees sequentially. The first tree makes an initial prediction. Then we compute residuals, and the next tree learns those residuals using feature-based splits. Each new tree corrects the remaining error until predictions converge.

---

That’s it.
Compact. Clear. Mathematical.

If you want, I can now make an even tighter 60-second whiteboard version.
