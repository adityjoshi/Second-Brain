# 1. Naive Bayes

## Definition

Naive Bayes is a supervised probabilistic classification algorithm based on Bayes’ theorem. It assumes that the features are conditionally independent given the class, which is why it is called “naive.”

## Formula

$$
P(\text{Class} \mid X) \propto P(X \mid \text{Class})\, P(\text{Class})
$$

Where:

- $P(\text{Class} \mid X)$ → posterior probability
- $P(X \mid \text{Class})$ → likelihood
- $P(\text{Class})$ → prior probability

## Example

For spam detection, features could be words like “free”, “offer” and “money”. Naive Bayes calculates the probability that the email is Spam or Not Spam and chooses the class with the higher probability.

## Types

- **Gaussian NB** → continuous numerical data
- **Multinomial NB** → text/word counts
- **Bernoulli NB** → binary features

## Advantages

Fast, simple, works well with high-dimensional data and text classification.

## Disadvantage

The feature-independence assumption may not hold in real-world data.

## Interview answer

> Naive Bayes is a probabilistic supervised classification algorithm based on Bayes’ theorem. It assumes features are conditionally independent given the class and predicts the class with the highest posterior probability. It’s commonly used for text classification, spam detection, and sentiment analysis.

---

# 2. SVM — Support Vector Machine

## Definition

SVM is a supervised learning algorithm that finds the best hyperplane to separate classes while maximizing the margin between the classes.

## Basic equation

$$
w^T x + b = 0
$$

The points closest to the decision boundary are called **support vectors**, and they determine the position of the optimal boundary.

## Example

Suppose we classify students as Pass/Fail using study hours and attendance. SVM finds a line that separates Pass and Fail students while keeping the maximum possible margin from the closest points.

## Kernel Trick

If data is not linearly separable, SVM can use kernels to create a non-linear decision boundary.

### Common kernels

- Linear
- Polynomial
- RBF

### RBF formula

$$
K(x, x') = e^{-\gamma \|x - x'\|^2}
$$

**Gamma:** Controls how far the influence of each training point extends.

- High gamma → more complex boundary → possible overfitting
- Low gamma → smoother boundary → possible underfitting

### Important hyperparameter: $C$

- High $C$ → tries harder to classify training points correctly → narrower margin
- Low $C$ → allows more misclassification → wider margin

## Advantages

Effective in high-dimensional data and can handle non-linear data using kernels.

## Disadvantages

Can be computationally expensive for large datasets and requires feature scaling.

## Interview answer

> SVM is a supervised algorithm that finds a hyperplane separating classes while maximizing the margin. The closest points are called support vectors. For non-linear data, SVM uses kernels such as RBF. Important hyperparameters are $C$, kernel, and gamma.

## One-line difference

| Algorithm   | Idea                          |
| ----------- | ----------------------------- |
| Naive Bayes | Probability-based classification |
| SVM         | Maximum-margin classification |

---

# Deep Learning

## Definition

Deep Learning is a subset of Machine Learning that uses artificial neural networks with multiple layers to automatically learn complex patterns from large amounts of data. It is especially useful for images, text, speech, and other unstructured data.

## Neural Network

A neural network consists of:

**Input Layer → Hidden Layers → Output Layer**

Each neuron calculates:

$$
z = w^T x + b
$$

and then applies an activation function.

- **Weight** → controls the importance of an input
- **Bias** → shifts the activation/threshold
- **Activation function** → introduces non-linearity

## Common Activation Functions

- **ReLU:** $\max(0, x)$ → commonly used in hidden layers
- **Sigmoid:** outputs between 0 and 1 → binary classification
- **Softmax:** converts outputs into probabilities that sum to 1 → multi-class classification

## Forward Propagation

The input passes through the network from input → hidden layers → output to generate a prediction.

## Loss Function

Measures the difference between the actual value and prediction.

### Common losses

- **MSE** → regression
- **Binary Cross-Entropy** → binary classification
- **Categorical Cross-Entropy** → multi-class classification

## Backpropagation

Backpropagation calculates the gradients of the loss with respect to the model’s weights and biases, propagating the error backward through the network.

## Optimizer / Gradient Descent

An optimizer uses the calculated gradients to update weights and biases to minimize the loss.

The **learning rate** controls the size of each update:

- Too small → slow learning
- Too large → unstable/overshooting

## 4 Important Optimizers

### 1. Gradient Descent / SGD

Stochastic Gradient Descent (SGD) updates the model’s parameters using the gradient calculated from a single sample or a small mini-batch of data.

> **SGD** → simple and fast updates using small batches of data.

### 2. Momentum

Momentum improves SGD by using information from previous updates to maintain a velocity in the direction of consistent improvement.

It helps the optimizer move faster in useful directions and reduces unnecessary oscillations.

> **Momentum** → uses previous updates to accelerate and stabilize SGD.

### 3. RMSprop

RMSprop adapts the learning rate for each parameter based on the recent magnitude of its gradients. Parameters with consistently large gradients receive smaller updates, while those with smaller gradients can receive relatively larger updates.

> **RMSprop** → adaptive learning rate based on recent squared gradients.

### 4. Adam

Adam (Adaptive Moment Estimation) combines ideas from Momentum and RMSprop. It keeps track of both the moving average of gradients and the moving average of squared gradients, giving each parameter an adaptive learning rate.

> **Adam** → combines momentum + adaptive learning rates.

## Quick Comparison

| Optimizer | Main Idea                                              |
| --------- | ------------------------------------------------------ |
| SGD       | Updates using gradient from a sample/mini-batch        |
| Momentum  | Uses previous gradients to accelerate updates          |
| RMSprop   | Adapts learning rate using squared gradients           |
| Adam      | Combines Momentum + RMSprop                            |

## Interview one-liners

- **SGD:** “Updates weights using gradients from individual samples or mini-batches.”
- **Momentum:** “Uses past gradients to accelerate learning and reduce oscillations.”
- **RMSprop:** “Adapts the learning rate for each parameter based on recent squared gradients.”
- **Adam:** “Combines momentum with adaptive learning rates, making it a popular optimizer for deep learning.”

## Complete Deep Learning Flow

```text
Input
  ↓
Weights + Bias
  ↓
Activation Function
  ↓
Forward Propagation
  ↓
Prediction
  ↓
Loss Function
  ↓
Backpropagation
  ↓
Gradients
  ↓
Optimizer
  ↓
Update Weights
  ↓
Repeat
```

> **Deep Learning** → Neural networks with multiple layers that learn complex patterns from data.
