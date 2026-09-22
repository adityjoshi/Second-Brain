# Deep Learning

Deep Learning is a subset of Machine Learning that uses artificial neural networks with multiple layers to automatically learn complex patterns from large amounts of data. Instead of manually designing features, a deep-learning model can learn useful features directly from raw data. It is called “deep” because the neural network contains multiple layers between the input and output. Deep learning is especially useful for problems involving images, speech, natural language, and other complex data where traditional machine-learning algorithms may require extensive feature engineering.

## Example

Suppose we want to build a system that can recognize whether an image contains a cat or a dog.

Instead of manually telling the model:

- Has four legs
- Has fur
- Has two ears
- Has a tail

we provide many labeled images:

| Image   | Label |
| ------- | ----- |
| Image 1 | Cat   |
| Image 2 | Dog   |
| Image 3 | Cat   |
| Image 4 | Dog   |

A neural network gradually learns patterns from these images. Early layers might learn simple patterns such as edges and shapes, while deeper layers can learn more complex patterns such as eyes, ears, faces, and overall animal structure. Finally, the output layer produces something like:

| Class | Probability |
| ----- | ----------- |
| Cat   | 0.90        |
| Dog   | 0.10        |

The model would therefore classify the image as **Cat**.

---

# Neural Network

A Neural Network is the basic building block of deep learning. It is inspired loosely by the way biological neurons process information. A neural network consists of an input layer, one or more hidden layers, and an output layer. Each neuron receives inputs, multiplies them by weights, adds a bias, and then passes the result through an activation function.

A simplified neuron works like this:

```text
Input → Weighted Sum → Activation Function → Output
```

For example:

```text
x₁ ──× w₁ ──┐
x₂ ──× w₂ ──┼──> Σ + bias ──> Activation ──> Output
x₃ ──× w₃ ──┘
```

The basic calculation is:

$$
z = w_1 x_1 + w_2 x_2 + w_3 x_3 + b
$$

where:

- $x$ = input
- $w$ = weight
- $b$ = bias
- $z$ = weighted sum

---

# What is a Weight?

A weight determines how important an input feature is to a neuron. During training, the neural network adjusts the weights so that its predictions become more accurate.

## Example

Suppose we want to predict whether a student will pass based on:

- $x_1$ = Study Hours
- $x_2$ = Attendance

The model might initially assign:

| Feature     | Weight |
| ----------- | ------ |
| Study Hours | 0.7    |
| Attendance  | 0.3    |

This means the model currently considers study hours more influential than attendance.

During training, these weights are continuously updated.

> **Weight** → Controls the importance of an input.

---

# What is Bias?

A bias allows a neuron to shift its activation function and adjust the threshold at which the neuron becomes activated.

For example:

$$
z = wx + b
$$

Without the bias, the model is more restricted in the functions it can represent. The bias gives the neuron an additional parameter that can shift the output.

| Term   | Role                         |
| ------ | ---------------------------- |
| Weight | Controls the importance/slope |
| Bias   | Shifts the activation/threshold |

This is an important distinction for exams.

---

# Activation Function

An activation function determines whether and how strongly a neuron should activate after calculating its weighted sum and bias. Activation functions also introduce non-linearity into the neural network. Without nonlinear activation functions, stacking many neural-network layers would still essentially behave like a linear transformation, limiting the kinds of complex patterns the network could learn.

## Common activation functions

### ReLU

$$
\text{ReLU}(x) = \max(0, x)
$$

So:

| $x$ | ReLU($x$) |
| --- | --------- |
| -5  | 0         |
| 3   | 3         |

ReLU is commonly used in hidden layers.

### Sigmoid

Sigmoid converts a value into a range between 0 and 1.

It is commonly useful for binary classification output probabilities.

For example:

- $0.9$ → high probability of class 1
- $0.2$ → low probability of class 1

### Softmax

Softmax is commonly used in the output layer for multi-class classification.

For example:

| Class | Probability |
| ----- | ----------- |
| Cat   | 0.70        |
| Dog   | 0.20        |
| Horse | 0.10        |

The probabilities sum to 1.

---

# Forward Propagation

Forward propagation is the process of passing the input data through the neural network from the input layer → hidden layers → output layer to produce a prediction.

For example:

```text
Input
  ↓
Hidden Layer 1
  ↓
Hidden Layer 2
  ↓
Output
  ↓
Prediction
```

If we give the network an image of a cat, forward propagation processes the image through the network and eventually produces something like:

| Class | Probability |
| ----- | ----------- |
| Cat   | 0.92        |
| Dog   | 0.08        |

---

# Loss Function

After making a prediction, the model needs to know how wrong its prediction was. A loss function measures the difference between the actual answer and the model’s prediction.

For example:

- Actual = 1
- Predicted = 0.8

The loss function calculates an error based on this difference.

The objective during training is generally:

> **Minimize the loss.**

## Common loss functions

- **Mean Squared Error (MSE)** → regression
- **Binary Cross-Entropy** → binary classification
- **Categorical Cross-Entropy** → multi-class classification

---

# Backpropagation

Backpropagation is the process used to calculate how much each weight and bias contributed to the prediction error. The error information is propagated backward from the output layer toward the earlier layers, and the resulting gradients are used by an optimization algorithm to update the model’s parameters.

The basic training cycle is:

```text
Input
  ↓
Forward Propagation
  ↓
Prediction
  ↓
Calculate Loss
  ↓
Backpropagation
  ↓
Calculate Gradients
  ↓
Update Weights/Biases
  ↓
Repeat
```

This process happens repeatedly over many training examples.

---

# Gradient Descent

Gradient Descent is an optimization algorithm used to update the weights and biases in order to reduce the loss.

The basic idea is:

```text
Current weights
      ↓
Calculate gradient
      ↓
Move weights in direction that reduces loss
      ↓
Repeat
```

The **learning rate** controls how large each update is.

- Small learning rate → slower learning
- Large learning rate → potentially unstable/overshooting

---

# Machine Learning vs Deep Learning

| Machine Learning                              | Deep Learning                                          |
| --------------------------------------------- | ------------------------------------------------------ |
| Often requires feature engineering            | Can automatically learn features                       |
| Can work well with smaller datasets           | Often benefits from large datasets                     |
| Algorithms include Decision Tree, KNN, SVM    | Uses neural networks with multiple layers              |
| Usually less computationally expensive        | Often computationally expensive                        |
| Can work well on structured/tabular data      | Particularly powerful for images, audio, text, etc.    |

## Easy example

For traditional ML, to classify an image of a cat, you might manually create features such as:

- Ear shape
- Eye shape
- Color
- Texture
- Edges

For Deep Learning, you can give the neural network the images directly, and it can learn useful representations automatically.

---

# The Most Important Deep Learning Terms

Remember this flow for exams:

```text
Input
  ↓
Weights + Bias
  ↓
Activation Function
  ↓
Prediction
  ↓
Loss Function
  ↓
Backpropagation
  ↓
Gradient Descent
  ↓
Update Weights
  ↓
Repeat
```

## Easiest definitions to remember

| Term                   | Definition                                              |
| ---------------------- | ------------------------------------------------------- |
| Weight                 | Importance of an input                                  |
| Bias                   | Shifts the activation/threshold                         |
| Activation Function    | Adds non-linearity                                      |
| Forward Propagation    | Produces the prediction                                 |
| Loss Function          | Measures prediction error                               |
| Backpropagation        | Calculates gradients for updating parameters            |
| Gradient Descent       | Uses gradients to reduce the loss                       |
| Deep Learning          | Neural networks with multiple layers that learn complex patterns from data |
