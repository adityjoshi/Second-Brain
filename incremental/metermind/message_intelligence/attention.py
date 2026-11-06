import numpy as np


def softmax_rows(scores):
    scores = np.asarray(scores, dtype=float)
    # Taking off each row's largest score keeps exp() from overflowing and
    # leaves the weights unchanged.
    shifted = scores - np.max(scores, axis=-1, keepdims=True)
    exponentiated = np.exp(shifted)
    return exponentiated / np.sum(exponentiated, axis=-1, keepdims=True)


def attention_weights(queries, keys):
    queries = np.asarray(queries, dtype=float)
    keys = np.asarray(keys, dtype=float)
    key_size = keys.shape[-1]
    scores = queries @ np.swapaxes(keys, -1, -2) / np.sqrt(key_size)
    return softmax_rows(scores)


def scaled_dot_product_attention(queries, keys, values):
    values = np.asarray(values, dtype=float)
    return attention_weights(queries, keys) @ values


if __name__ == "__main__":
    generator = np.random.default_rng(0)
    weights = softmax_rows(generator.normal(size=(3, 3)))
    print(f"every row of a softmax adds to one: {weights.sum(axis=1)}")
    queries = generator.normal(size=(3, 4))
    keys = generator.normal(size=(3, 4))
    values = generator.normal(size=(3, 4))
    attended = scaled_dot_product_attention(queries, keys, values)
    print(f"three positions attending over three, four numbers each -> {attended.shape}")
