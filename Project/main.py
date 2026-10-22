import os
import csv
import numpy as np
from PIL import Image
from tensorflow import keras

TRAIN_DIR = "data/train"
TEST_DIR = "data/test"
PREDICT_DIR = "data/predict"
TRAIN_PROCESSED_PATH = "processed_data/train_processed.npz"
TEST_PROCESSED_PATH = "processed_data/test_processed.npz"
PREDICT_PROCESSED_PATH = "processed_data/predict_processed.npz"
MODEL_PATH = "artifacts/casting_defect_model.keras"
PREDICTIONS_PATH = "output/casting_predictions.csv"


def preprocess_images(input_dir, output_path, labelled):
    images, values = [], []

    if labelled:
        categories = sorted(
            x for x in os.listdir(input_dir) if os.path.isdir(os.path.join(input_dir, x))
        )
        files = [
            (os.path.join(input_dir, c, f), i)
            for i, c in enumerate(categories)
            for f in sorted(os.listdir(os.path.join(input_dir, c)))
            if f.lower().endswith(".png")
        ]
    else:
        names = sorted(f for f in os.listdir(input_dir) if f.lower().endswith(".png"))
        files = [(os.path.join(input_dir, f), f) for f in names]

    for path, value in files:
        image = Image.open(path).convert("L").resize((48, 48))
        images.append(np.asarray(image, dtype=np.float32) / 255.0)
        values.append(value)

    images = np.asarray(images, dtype=np.float32)[..., None]
    values = np.asarray(values)
    os.makedirs(os.path.dirname(output_path), exist_ok=True)

    if labelled:
        np.savez_compressed(output_path, images=images, labels=values)
    else:
        np.savez_compressed(output_path, images=images, image_ids=values)

    return images, values


def build_model(input_shape, num_classes):
    model = keras.Sequential(
        [
            keras.layers.Input(shape=input_shape),
            keras.layers.Conv2D(32, 3, padding="same", activation="relu"),
            keras.layers.BatchNormalization(),
            keras.layers.Conv2D(32, 3, padding="same", activation="relu"),
            keras.layers.MaxPooling2D(),
            keras.layers.Conv2D(64, 3, padding="same", activation="relu"),
            keras.layers.BatchNormalization(),
            keras.layers.Conv2D(64, 3, padding="same", activation="relu"),
            keras.layers.MaxPooling2D(),
            keras.layers.Conv2D(128, 3, padding="same", activation="relu"),
            keras.layers.BatchNormalization(),
            keras.layers.MaxPooling2D(),
            keras.layers.Flatten(),
            keras.layers.Dense(256, activation="relu"),
            keras.layers.Dropout(0.3),
            keras.layers.Dense(num_classes, activation="softmax"),
        ]
    )
    model.compile(
        optimizer="adam",
        loss="sparse_categorical_crossentropy",
        metrics=["accuracy"],
    )
    return model


def train_model(processed_path, model_path, epochs):
    data = np.load(processed_path)
    x, y = data["images"], data["labels"]
    model = build_model(x.shape[1:], len(np.unique(y)))
    model.fit(
        x,
        y,
        epochs=epochs,
        batch_size=32,
        validation_split=0.2,
        shuffle=False,
        verbose=0,
    )
    os.makedirs(os.path.dirname(model_path), exist_ok=True)
    model.save(model_path)
    return model


def evaluate_model(model_path, processed_path):
    model = keras.models.load_model(model_path)
    data = np.load(processed_path)

    images = data["images"]
    labels = data["labels"]

    _, accuracy = model.evaluate(images, labels, verbose=0)
    return float(accuracy)


def predict_new_data(model_path, input_dir, processed_path, output_path):
    model = keras.models.load_model(model_path)
    images, ids = preprocess_images(input_dir, processed_path, False)
    pred = np.argmax(model.predict(images, verbose=0), axis=1)
    categories = sorted(
        x for x in os.listdir(TRAIN_DIR) if os.path.isdir(os.path.join(TRAIN_DIR, x))
    )
    verdicts = np.asarray([categories[i] for i in pred])

    os.makedirs(os.path.dirname(output_path), exist_ok=True)
    with open(output_path, "w", newline="") as f:
        writer = csv.writer(f)
        writer.writerow(["image_id", "predicted_class"])
        writer.writerows(zip(ids, verdicts))
    df = pd.DataFrame()
    df[""] = ids
    df[""] = verdicts
    
    return ids,verdicts




