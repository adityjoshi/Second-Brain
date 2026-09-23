import os

os.environ["TF_CPP_MIN_LOG_LEVEL"] = "2"

import numpy as np
import pandas as pd
from PIL import Image
from tensorflow import keras
from tensorflow.keras import layers

TRAIN_DIR, TEST_DIR, PREDICT_DIR = "data/train", "data/test", "data/predict"
TRAIN_FILE = "processed_data/train_processed.npz"
TEST_FILE = "processed_data/test_processed.npz"
PREDICT_FILE = "processed_data/predict_processed.npz"
MODEL_FILE = "artifacts/casting_defect_model.keras"
OUTPUT_FILE = "output/casting_predictions.csv"

# for _dir in ("processed_data", "artifacts", "output"):
#    os.makedirs(_dir, exist_ok=True)


def load_image(path):
    # NEAREST only ever reuses real pixel values, so scaling stays exactly proportional.
    with Image.open(path) as image:
        resized = image.convert("L").resize((48, 48), Image.Resampling.NEAREST)
    return (np.asarray(resized, dtype=np.float32) / 255.0)[..., None]


def preprocess_images(input_dir, output_path, labelled):
    if labelled:
        categories = sorted(c for c in os.listdir(input_dir) if os.path.isdir(os.path.join(input_dir, c)))
        images, labels = [], []
        for label, category in enumerate(categories):
            folder = os.path.join(input_dir, category)
            for name in sorted(os.listdir(folder)):
                if name.lower().endswith((".png", ".jpg", ".jpeg")):
                    images.append(_load_image(os.path.join(folder, name)))
                    labels.append(label)
        images, labels = np.array(images, dtype=np.float32), np.array(labels, dtype=np.int64)
        np.savez_compressed(output_path, images=images, labels=labels)
        return images, labels

    names = sorted(n for n in os.listdir(input_dir) if n.lower().endswith((".png", ".jpg", ".jpeg")))
    images = np.array([_load_image(os.path.join(input_dir, n)) for n in names], dtype=np.float32)
    image_ids = np.array(names)
    np.savez_compressed(output_path, images=images, image_ids=image_ids)
    return images, image_ids


def build_model(input_shape, num_classes):
    model = keras.Sequential([
        keras.Input(shape=input_shape),
        layers.Conv2D(32, 3, activation="relu"), layers.MaxPooling2D(),
        layers.Conv2D(64, 3, activation="relu"), layers.MaxPooling2D(),
        layers.Conv2D(128, 3, activation="relu"), layers.MaxPooling2D(),
        layers.Flatten(),
        layers.Dense(128, activation="relu"),
        layers.Dropout(0.25),
        layers.Dense(num_classes, activation="softmax"),
    ])
    model.compile(optimizer="adam", loss="sparse_categorical_crossentropy", metrics=["accuracy"])
    return model


def train_model(processed_path, model_path, epochs):
    data = np.load(processed_path)
    images, labels = data["images"], data["labels"]
    order = np.random.default_rng(42).permutation(len(images))  # shuffle before Keras's validation_split slices it
    images, labels = images[order], labels[order]
    model = build_model(images.shape[1:], len(np.unique(labels)))
    model.fit(images, labels, epochs=epochs, batch_size=32, validation_split=0.2, verbose=0)
    model.save(model_path)
    return model


def evaluate_model(model_path, processed_path):
    model = keras.models.load_model(model_path)
    data = np.load(processed_path)
    return float(model.evaluate(data["images"], data["labels"], verbose=0)[1])


def predict_new_data(model_path, input_dir, processed_path, output_path):
    model = keras.models.load_model(model_path)
    images, image_ids = preprocess_images(input_dir, processed_path, labelled=False)
    class_names = sorted(c for c in os.listdir(TRAIN_DIR) if os.path.isdir(os.path.join(TRAIN_DIR, c)))
    predicted = [class_names[i] for i in model.predict(images, verbose=0).argmax(axis=1)]
    results = pd.DataFrame({"image_id": image_ids, "predicted_class": predicted})
    results.to_csv(output_path, index=False)
    return results


if __name__ == "__main__":
    preprocess_images(TRAIN_DIR, TRAIN_FILE, True)
    preprocess_images(TEST_DIR, TEST_FILE, True)
    train_model(TRAIN_FILE, MODEL_FILE, epochs=10)
    print("Test accuracy:", evaluate_model(MODEL_FILE, TEST_FILE))
    predict_new_data(MODEL_FILE, PREDICT_DIR, PREDICT_FILE, OUTPUT_FILE)
