Absolutely. Add these under Decision Tree, because Gini Index and Entropy are criteria used by classification Decision Trees to decide the best split.

Gini Index

The Gini Index is a measure of impurity or disorder in a node of a Decision Tree. It tells us how mixed the classes are in that node. A Gini value of 0 means the node is completely pure, meaning all observations belong to the same class. As the classes become more mixed, the Gini Index increases. During tree construction, the Decision Tree considers different possible splits and generally prefers the split that produces lower impurity in the resulting child nodes.

The formula for Gini Index is:

Gini = 1 - Σ(pᵢ)²

where pᵢ is the proportion of observations belonging to class i.

Example: Suppose a node contains 10 students:

Pass = 8
Fail = 2

The probabilities are:

P(Pass) = 8/10 = 0.8
P(Fail) = 2/10 = 0.2

Therefore:

Gini = 1 - (0.8² + 0.2²)
     = 1 - (0.64 + 0.04)
     = 1 - 0.68
     = 0.32

So the Gini Index is 0.32. If all 10 students were Pass, then:

Gini = 1 - (1²)
     = 0

That means the node is completely pure.

Easy memory:

Gini Index → Measures how impure/mixed a node is. Lower Gini = purer node.

⸻

Entropy

Entropy is another measure of impurity or uncertainty used by classification Decision Trees. It measures how uncertain or mixed the classes are within a node. When all observations belong to one class, there is no uncertainty and the entropy is 0. When the classes are evenly distributed, the uncertainty is higher. A Decision Tree evaluates possible splits and generally prefers splits that produce a greater reduction in entropy, which is called Information Gain.

The formula for Entropy is:

Entropy = -Σ pᵢ log₂(pᵢ)

where pᵢ represents the proportion of observations belonging to class i.

Example: Suppose a node contains 10 students:

Pass = 8
Fail = 2

Therefore:

P(Pass) = 0.8
P(Fail) = 0.2

The entropy is:

Entropy = -(0.8 × log₂(0.8) + 0.2 × log₂(0.2))
        ≈ 0.72

So the entropy is approximately 0.72.

If all 10 students were Pass:

P(Pass) = 1
P(Fail) = 0

Then:

Entropy = 0

because there is no uncertainty—the node contains only one class.

Easy memory:

Entropy → Measures uncertainty/disorder. Lower Entropy = less uncertainty.

⸻

Gini vs Entropy

Both Gini Index and Entropy are used by Decision Trees to measure how good a classification split is.

	Gini Index	Entropy
Measures	Impurity	Uncertainty/impurity
Best value	0	0
Higher value	More mixed	More uncertain
Used in	Classification trees	Classification trees
Formula	1 - Σp²	-Σp log₂(p)
Related concept	Gini impurity	Information Gain

Very simple way to remember

Imagine a box containing 10 balls.

Case 1:

10 Red
0 Blue

The box is completely pure:

Gini = 0
Entropy = 0

Case 2:

5 Red
5 Blue

The box is highly mixed:

Gini = 0.5
Entropy = 1

So:

Pure node → Gini = 0, Entropy = 0
Mixed node → Higher Gini, Higher Entropy

And when a Decision Tree chooses a split, it tries to create child nodes that are as pure as possible.
