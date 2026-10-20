# RNN vs LSTM vs Attention — Interview Preparation

These three concepts are connected. To understand them properly, we should start with the problem they solve: **how does a neural network process sequential data and understand relationships between elements in a sequence?**

For example, consider this sentence:

> *"The server crashed because it ran out of memory."*

A model needs to understand the relationship between **server**, **crashed**, and **memory**. The order of words matters, and information from earlier words can help interpret later ones.

RNNs, LSTMs, and attention mechanisms approach this problem differently.

---

## 1. RNN (Recurrent Neural Network)

### What is an RNN?

A Recurrent Neural Network (RNN) is a neural network designed to process sequential data by maintaining a hidden state that carries information from previous time steps.

Unlike a standard feedforward neural network, which typically processes each input independently, an RNN uses information from previous steps when processing the current input.

RNNs are commonly used to explain early neural network approaches to:

* Text processing
* Time-series forecasting
* Speech recognition
* Sequential pattern recognition

### How does an RNN work?

Consider this sentence:

> *"I love machine learning."*

The RNN processes the words sequentially:

1. It receives the word **"I"**.
2. It processes **"love"** while retaining information from the previous word.
3. It processes **"machine"** using the current word and the previous hidden state.
4. It processes **"learning"** using the information carried forward.

The central idea is that each time step receives the current input and information from the previous time step.

An RNN maintains a hidden state, usually represented by $h_t$. Its basic equations are:

$$
h_t = \tanh(W_x x_t + W_h h_{t-1} + b_h)
$$

$$
y_t = W_y h_t + b_y
$$

**Where:**

* $x_t$: Input at the current time step.
* $h_t$: Hidden state at the current time step.
* $h_{t-1}$: Hidden state from the previous time step.
* $W_x, W_h, W_y$: Learnable weight matrices.
* $b_h, b_y$: Bias terms.
* $y_t$: Output at the current time step.
* $\tanh$: Activation function that introduces non-linearity.

$$
\begin{aligned}
\text{Current hidden state}
&= \text{information from current input} \\
&\quad + \text{information carried from previous step}
\end{aligned}
$$

### A Practical Example

Suppose you want to predict tomorrow’s temperature using the previous seven days of temperatures.

* An RNN processes the temperature sequence one day at a time.
* At each step, it updates its hidden state using the current day’s temperature and the previous hidden state.
* After processing the sequence, the model uses the resulting representation to predict the next day’s temperature.

### What is the Main Problem with RNNs?

The primary limitation is difficulty in learning **long-term dependencies**.

Consider:

> *"I grew up in India. ... I speak Hindi fluently."*

The earlier mention of **India** helps the model interpret the second sentence. In a much longer passage where relevant context appeared hundreds of words prior, a basic RNN struggles to preserve that information due to two training dynamics:

1. **Vanishing Gradients:** Backpropagation Through Time (BPTT) propagates gradients backward across many time steps. Repeated multiplications by weight matrices and derivative terms shrink gradients exponentially toward zero, depriving earlier steps of meaningful weight updates.
2. **Exploding Gradients:** Repeated multiplications can cause gradients to grow uncontrollably large, destabilizing training. *(Commonly controlled via gradient clipping).*

> **Interview Takeaway:** RNNs introduce recurrence and hidden states to process sequences, but vanilla RNNs struggle with long-term dependencies due to vanishing gradients during BPTT.

---

## 2. LSTM (Long Short-Term Memory)

### What is an LSTM?

LSTM is a specialized RNN architecture designed to learn long-term dependencies more effectively by explicitly regulating how information is retained, updated, and discarded.

While a vanilla RNN repeatedly overwrites its single hidden state, an LSTM adds a dedicated **cell state** along with **three gating mechanisms**. The cell state acts as an information highway where signals can flow with minimal disruption.

### Why do we need LSTM?

Consider this sentence:

> *"The book that I borrowed from the library several weeks ago was fascinating."*

To agree the singular verb **"was"** with the subject **"The book"**, the network must preserve singular noun information across all intermediate clauses. An LSTM learns to selectively preserve this subject information while ignoring irrelevant noise.

### How does an LSTM work?

An LSTM maintains two states:

* **Hidden State ($h_t$):** The working memory exposed at the current time step, used to generate step outputs and compute subsequent state transitions.
* **Cell State ($C_t$):** The long-term memory carrying signals linearly across time steps with minimal additive updates.

```text
x_t  and  h_{t-1}
        |
        +-- Forget gate f_t --> keep or drop C_{t-1}
        |
        +-- Input gate i_t  --> scale the new candidate
        |         |
        |         +-- candidate C~_t
        |
        v
C_t = (f_t * C_{t-1}) + (i_t * C~_t)
        |
        v
Output gate o_t filters tanh(C_t)
        |
        v
h_t
```

#### Gate 1: Forget Gate

Determines how much of the previous cell state $C_{t-1}$ to retain:

$$
f_t = \sigma(W_f [h_{t-1}, x_t] + b_f)
$$

The sigmoid activation ($\sigma$) outputs values between $0$ and $1$:

* Close to $0$: Discard the information.
* Close to $1$: Retain the information.

#### Gate 2: Input Gate

Controls which new information is written into the cell state. It combines an input gate activation with candidate cell values ($\widetilde{C}_t$):

$$
i_t = \sigma(W_i [h_{t-1}, x_t] + b_i)
$$

$$
\widetilde{C}_t = \tanh(W_C [h_{t-1}, x_t] + b_C)
$$

#### Gate 3: Cell-State Update

The cell state updates by combining the retained old state with the scaled candidate state via element-wise multiplication ($\odot$):

$$
C_t = f_t \odot C_{t-1} + i_t \odot \widetilde{C}_t
$$

$$
\begin{aligned}
\text{New cell state}
&= (\text{retained prior info}) + (\text{selected new info})
\end{aligned}
$$

#### Output Gate

Determines what part of the updated cell state should be exposed through the new hidden state $h_t$:

$$
o_t = \sigma(W_o [h_{t-1}, x_t] + b_o)
$$

$$
h_t = o_t \odot \tanh(C_t)
$$

### Understanding LSTM through an Example

Sentence: *"The movie started slowly, but the ending was absolutely brilliant."*

1. **Forget Gate:** Learns to downweight the negative sentiment from the initial clause after encountering transition signals like *"but"*.
2. **Input Gate:** Writes the strongly positive context introduced by *"absolutely brilliant"* into the cell state.
3. **Cell State:** Carries this updated context forward.
4. **Output Gate:** Exposes a positive sentiment representation to the output classifier.

### RNN vs LSTM Comparison

| Feature | RNN | LSTM |
| --- | --- | --- |
| **Architecture** | Single recurrent hidden state | Hidden state, cell state, and 3 gating units |
| **Long-Term Dependencies** | Fails over long horizons | Mitigates vanishing gradient to learn longer dependencies |
| **Information Control** | Uncontrolled recurrent overwrite | Explicit gating: Forget, Input, and Output gates |
| **Vanishing Gradients** | Severe structural issue | Substantially mitigated via additive cell state updates |
| **Computational Cost** | Low (few parameters) | High ($\sim 4\times$ parameter count of vanilla RNN) |
| **Sequential Dependency** | Yes ($O(N)$ sequential steps) | Yes ($O(N)$ sequential steps) |

> **Interview Takeaway:** LSTMs solve vanilla RNN gradient decay by introducing an additive cell state pathway ($C_t$) regulated by learned forget, input, and output gates.

---

## 3. Attention Mechanism

### What is Attention?

Attention is a mechanism that allows a model to dynamically weight different elements of a sequence based on their relevance to a target context, rather than compressing an entire history into a fixed-size vector.

### Why do we need Attention?

Consider this pronoun disambiguation problem:

> *"The animal didn’t cross the road because it was too tired."*

What does **"it"** refer to? The model must connect **"it"** with **"the animal"** rather than **"the road"**.

In an RNN or LSTM, tokens are processed step by step; distant dependencies must survive every intermediate recurrent transition. Attention bypasses recurrence by establishing a direct connection between every token pair regardless of positional distance.

### The Core Concept: Query, Key, and Value

Attention functions like an information retrieval system:

* **Query ($Q$):** What the current token is looking for.
* **Key ($K$):** The identifier/label of each token being evaluated.
* **Value ($V$):** The actual content or information payload delivered if the Query matches the Key.

These vectors are calculated via learned linear projections:


$$
Q = X W_Q, \quad K = X W_K, \quad V = X W_V
$$

### The Mathematics of Scaled Dot-Product Attention

$$
\begin{aligned}
\operatorname{Attention}(Q, K, V)
&= \operatorname{softmax}\!\left(\frac{Q K^T}{\sqrt{d_k}}\right) V
\end{aligned}
$$

#### Step-by-Step Breakdown:

1. **Similarity Computation:** Compute raw compatibility scores by taking the dot product of queries with all keys:

   $$
   S = Q K^T
   $$

2. **Scaling Factor:** Divide by the square root of key dimension ($d_k$):

   $$
   S_{\text{scaled}} = \frac{Q K^T}{\sqrt{d_k}}
   $$

   *Why scale?* When $d_k$ is large, dot products grow large in magnitude, pushing the softmax function into regions with extremely small gradients. Dividing by $\sqrt{d_k}$ preserves stable gradient dynamics.

3. **Softmax Normalization:** Convert scalar scores into normalized probability distributions across tokens:

   $$
   A = \operatorname{softmax}(S_{\text{scaled}})
   $$

   *(Every row sums to 1, where weights represent relative attention).*

4. **Weighted Value Aggregation:** Multiply the attention weights by the value representations:

   $$
   O = A V
   $$

#### Illustrative Attention Weight Distribution for *"it"*:

| Token | Attention Weight |
| --- | --- |
| The | $0.05$ |
| animal | **$0.70$** |
| didn't | $0.02$ |
| cross | $0.03$ |
| road | $0.10$ |
| tired | $0.10$ |

---

## 4. What Is Self-Attention?

Self-attention (or intra-attention) is an attention variation where the **Queries, Keys, and Values are all derived from the same sequence**:

$$
\begin{aligned}
\operatorname{SelfAttention}(X)
&= \operatorname{softmax}\!\left(\frac{(X W_Q)(X W_K)^T}{\sqrt{d_k}}\right)(X W_V)
\end{aligned}
$$

* **Unmasked Self-Attention:** Every token attends to every other token in the sequence (standard in bidirectional encoders like BERT).
* **Causal/Masked Self-Attention:** A upper-triangular mask ensures a token at position $t$ can only attend to positions $\le t$, preventing future information leakage in autoregressive decoders (e.g., GPT).

---

## 5. What Is Multi-Head Attention?

Rather than computing a single set of attention weights, Multi-Head Attention projects $Q, K,$ and $V$ into $h$ distinct subspaces, computes attention in parallel for each head, and concatenates the outputs:

$$
\begin{aligned}
\operatorname{MultiHead}(Q, K, V)
&= \operatorname{Concat}(\mathrm{head}_1, \ldots, \mathrm{head}_h)\, W_O \\
\mathrm{head}_i
&= \operatorname{Attention}(Q W_i^Q, K W_i^K, V W_i^V)
\end{aligned}
$$

### Why use multiple heads?

A single head tends to average out multiple contextual signals. Multi-head attention allows different heads to simultaneously track distinct relationship patterns:

* **Head 1:** Syntactic/grammatical bindings (verbs with their direct objects).
* **Head 2:** Coreference resolution (pronouns to antecedents).
* **Head 3:** Long-range contextual conditions.

---

## 6. How Are RNN, LSTM, and Attention Different?

| Dimension | RNN | LSTM | Attention |
| --- | --- | --- | --- |
| **Core Paradigm** | Recurrent hidden state compression | Gated cell state preservation | Direct associative addressing via $Q, K, V$ |
| **Sequential Constraint** | Strict sequential loop ($O(N)$ depth) | Strict sequential loop ($O(N)$ depth) | Non-sequential across positions |
| **Long-Range Handling** | Poor (vanishing gradients) | Moderate (mitigated by gates) | Direct ($O(1)$ path length between any two tokens) |
| **Training Parallelism** | No (step $t$ requires $t-1$) | No (step $t$ requires $t-1$) | Highly parallel across token sequence |
| **Time Complexity per Layer** | $O(N \cdot d^2)$ | $O(N \cdot d^2)$ | $O(N^2 \cdot d)$ (standard attention) |
| **Primary Domain** | Historical baseline / low compute | Time series / legacy NLP | Transformers, Modern LLMs, Vision Transformers |

> **Architectural Note:** RNN and LSTM are **complete network architectures**, while Attention is a **mechanism**. Attention can be used on top of recurrent models (such as in classic seq2seq with attention) or standalone (as in Transformers).

---

## 7. Evolutionary Timeline: RNN $\to$ LSTM $\to$ Transformers

```text
1. Vanilla RNN
   Processes one step at a time.
   Vanishing gradients limit long memory.
        |
        v
2. LSTM
   Gates and a cell state carry information further.
   Still sequential, so training cannot run in parallel.
        |
        v
3. Recurrent + Attention
   Attention reads encoder states directly,
   instead of squeezing them into one vector.
        |
        v
4. Transformer
   Drops recurrence. Self-attention plus positional
   encodings train across the sequence in parallel.
```

---

## 8. Common Interview Follow-Up Questions

### Q1. Why does an RNN suffer from vanishing gradients?

During Backpropagation Through Time (BPTT), the gradient of the loss at step $T$ with respect to the hidden state at step $t$ involves a chain product of Jacobian matrices:

$$
\frac{\partial h_T}{\partial h_t} = \prod_{j=t+1}^T \frac{\partial h_j}{\partial h_{j-1}}
$$

Because each term contains $W_h^T \operatorname{diag}(1 - \tanh^2(\ldots))$, eigenvalues of $W_h$ less than 1 or saturated $\tanh$ derivatives cause this product to shrink exponentially as $(T - t)$ increases.

### Q2. How does an LSTM alleviate vanishing gradients?

The cell state update is additive:

$$
C_t = f_t \odot C_{t-1} + i_t \odot \widetilde{C}_t
$$

When differentiating $C_t$ with respect to $C_{t-1}$:

$$
\frac{\partial C_t}{\partial C_{t-1}} = f_t
$$

If the forget gate $f_t$ is close to 1, the gradient flows across time steps without exponential decay factors, mitigating the vanishing gradient effect.

### Q3. What is the difference between Cell State and Hidden State?

* **Cell State ($C_t$):** The internal long-term linear memory bus that receives additive updates. It is not directly exposed as output.
* **Hidden State ($h_t$):** The working short-term memory computed by filtering the cell state through the output gate ($h_t = o_t \odot \tanh(C_t)$). It serves as the output representation at that step.

### Q4. Why do Transformers require Positional Encoding?

Self-attention is **permutation-equivariant**:


$$
\operatorname{Attention}(P Q, P K, P V) = P \operatorname{Attention}(Q, K, V)
$$

*(where $P$ is a permutation matrix)*.

Without explicit positional information added to token embeddings, the model cannot distinguish between *"dog bit man"* and *"man bit dog"*. Positional encodings (sinusoidal, learned, or RoPE) inject sequence order into the representations.

### Q5. What is the computational bottleneck of Attention vs RNNs?

* **RNN:** Computation scales linearly with sequence length ($O(N)$), but cannot be parallelized along the time axis during training.
* **Standard Self-Attention:** Computes an $N \times N$ matrix ($Q K^T$), which requires **$O(N^2)$ memory and time complexity**. While highly parallelizable on GPUs during training, long sequences become memory-prohibitive without optimizations like FlashAttention or linear attention variants.

---

## 9. The Definitive Interview Answer

If an interviewer asks: *"Explain RNN, LSTM, and Attention, and how they differ,"* structure your answer as follows:

> "RNN, LSTM, and Attention are three distinct approaches to modeling sequential data:
> 1. **RNN** processes tokens sequentially, passing a single hidden state forward. Because of repeated matrix multiplications during backpropagation, it suffers from vanishing gradients and struggles with long-range dependencies.
> 2. **LSTM** resolves this by separating memory into a **cell state** and a **hidden state**, regulated by three learned gates (**forget, input, and output**). Its additive cell-state updates prevent gradients from quickly vanishing, but execution remains strictly sequential ($O(N)$).
> 3. **Attention** removes the sequential bottleneck entirely. By treating representations as **Queries, Keys, and Values**, it calculates pairwise relevance scores across all sequence positions simultaneously.
> 
> 
> Transformers replaced recurrent models by combining self-attention with positional encodings, unlocking full GPU parallelization during training and direct token-to-token associative lookups."
