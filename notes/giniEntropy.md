# Gini Index & Entropy

Add these under Decision Tree, because Gini Index and Entropy are criteria used by classification Decision Trees to decide the best split.

---

# Gini Index

The Gini Index is a measure of impurity or disorder in a node of a Decision Tree. It tells us how mixed the classes are in that node. A Gini value of 0 means the node is completely pure, meaning all observations belong to the same class. As the classes become more mixed, the Gini Index increases. During tree construction, the Decision Tree considers different possible splits and generally prefers the split that produces lower impurity in the resulting child nodes.

## Formula

$$
\text{Gini} = 1 - \sum (p_i)^2
$$

where $p_i$ is the proportion of observations belonging to class $i$.

## Example

Suppose a node contains 10 students:

| Class | Count |
| ----- | ----- |
| Pass  | 8     |
| Fail  | 2     |

The probabilities are:

$$
P(\text{Pass}) = \frac{8}{10} = 0.8, \quad P(\text{Fail}) = \frac{2}{10} = 0.2
$$

Therefore:

$$
\begin{align*}
\text{Gini} &= 1 - (0.8^2 + 0.2^2) \\
&= 1 - (0.64 + 0.04) \\
&= 1 - 0.68 \\
&= 0.32
\end{align*}
$$

So the Gini Index is **0.32**. If all 10 students were Pass, then:

$$
\text{Gini} = 1 - (1^2) = 0
$$

That means the node is completely pure.

> **Gini Index** → Measures how impure/mixed a node is. Lower Gini = purer node.

---

# Entropy

Entropy is another measure of impurity or uncertainty used by classification Decision Trees. It measures how uncertain or mixed the classes are within a node. When all observations belong to one class, there is no uncertainty and the entropy is 0. When the classes are evenly distributed, the uncertainty is higher. A Decision Tree evaluates possible splits and generally prefers splits that produce a greater reduction in entropy, which is called **Information Gain**.

## Formula

$$
\text{Entropy} = -\sum p_i \log_2(p_i)
$$

where $p_i$ represents the proportion of observations belonging to class $i$.

## Example

Suppose a node contains 10 students:

| Class | Count |
| ----- | ----- |
| Pass  | 8     |
| Fail  | 2     |

Therefore:

$$
P(\text{Pass}) = 0.8, \quad P(\text{Fail}) = 0.2
$$

The entropy is:

$$
\begin{align*}
\text{Entropy} &= -(0.8 \times \log_2(0.8) + 0.2 \times \log_2(0.2)) \\
&\approx 0.72
\end{align*}
$$

So the entropy is approximately **0.72**.

If all 10 students were Pass:

$$
P(\text{Pass}) = 1, \quad P(\text{Fail}) = 0
$$

Then:

$$
\text{Entropy} = 0
$$

because there is no uncertainty—the node contains only one class.

> **Entropy** → Measures uncertainty/disorder. Lower Entropy = less uncertainty.

---

# Gini vs Entropy

Both Gini Index and Entropy are used by Decision Trees to measure how good a classification split is.

| Feature         | Gini Index              | Entropy                |
| --------------- | ----------------------- | ---------------------- |
| Measures        | Impurity                | Uncertainty/impurity   |
| Best value      | 0                       | 0                      |
| Higher value    | More mixed              | More uncertain         |
| Used in         | Classification trees    | Classification trees   |
| Formula         | $1 - \sum p^2$          | $-\sum p \log_2(p)$    |
| Related concept | Gini impurity           | Information Gain       |

## Very simple way to remember

Imagine a box containing 10 balls.

### Case 1

| Color | Count |
| ----- | ----- |
| Red   | 10    |
| Blue  | 0     |

The box is completely pure:

- Gini = 0
- Entropy = 0

### Case 2

| Color | Count |
| ----- | ----- |
| Red   | 5     |
| Blue  | 5     |

The box is highly mixed:

- Gini = 0.5
- Entropy = 1

So:

- **Pure node** → Gini = 0, Entropy = 0
- **Mixed node** → Higher Gini, Higher Entropy

And when a Decision Tree chooses a split, it tries to create child nodes that are as pure as possible.
