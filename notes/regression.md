# L1, L2, and Elastic Net Regularization

### Both are used to reduce overfitting in machine learning.

### They add a penalty for large model weights to the loss function.

## 1. L1 Regularization (Lasso)

L1 adds the **absolute values of the weights** to the loss function.

$$
Total\ Loss = Loss + \lambda \sum |w_i|
$$

- Can make some weights **exactly 0**
- Performs **feature selection**
- Less important features can effectively be removed from the model

**Example:**

If a feature has:

$$
w = 0
$$

the model effectively ignores that feature.

---

## 2. L2 Regularization (Ridge)

L2 adds the **squares of the weights** to the loss function.

$$
Total\ Loss = Loss + \lambda \sum w_i^2
$$

- Takes the **square of each weight**
- Adds the squared weights as a penalty to the loss
- Encourages large weights to become **smaller**
- Usually does **not** make weights exactly 0
- Helps reduce overfitting
- Helps make the model more stable when features are correlated

**Example:**

If:

$$
w_1 = 10,\quad w_2 = 8
$$

Then:

$$
L2\ Penalty = 10^2 + 8^2
$$

$$
= 100 + 64 = 164
$$

The optimizer uses this penalty along with the original loss to adjust the weights.

---

## 3. Elastic Net

Elastic Net combines **L1 and L2 regularization**.

$$
Total\ Loss =
Loss + \lambda_1\sum|w_i| + \lambda_2\sum w_i^2
$$

Therefore:

- **L1 →** can make some weights exactly 0 → feature selection
- **L2 →** shrinks weights toward 0 → better stability
- **Elastic Net →** combines both behaviors

---

## Easy Way to Remember

| Regularization | Effect on weights |
|---|---|
| **L1 (Lasso)** | Some weights become **0** |
| **L2 (Ridge)** | Weights become **smaller** |
| **Elastic Net** | Some become **0**, others become **smaller** |

### One-line answer

> **L1 selects features by making some coefficients zero, L2 controls large coefficients by shrinking them toward zero, and Elastic Net combines both L1 and L2 regularization.**
