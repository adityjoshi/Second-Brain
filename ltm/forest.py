import pandas as pd 
from sklearn.ensemble import RandomForestClassifier

def clean_data(input_path,output_path):
    df = pd.read_csv(input_path)

    booking_columns = ["order_id","dispatch_date","origin","warehouse_code","destination_city"]

    df = df.drop_duplicates().reset_index(drop=True)

    df.drop(columns = [booking_columns])

    numerical_columns = ["distance_km","package_weight_kg"]

    for col in numerical_columns:
        df[col] = df[col].fillna(df[col].median())


    if "shipping_speed" in df.columns:
        df["shipping_speed"] = (
            df["shipping_speed"].astype(str).str.strip().str.lower().map({"standard":0,"express":1,"priority":2})
        )

    if "is_weekend_dispatch" in df.columns:
        df["is_weekend_dispatch"] = (
            df["is_weekend_dispatch"].astype(str).str.strip().str.lower().map({"no":0,"yes":1})
        )

    df.to_csv(output_path)

    return df

def train_model(processed_path,model_path):
    df = pd.read_csv(processed_path)
    X = df.drop(columns=["is_delayed"])
    y = df["is_delayed"]

    model = RandomForestClassifier(
        n_estimator=100,
        max_depth=10,
        random_state=42
    )

    model.fit(X,y)

    joblib.dump(model,model_path)

    return model


def predict_new_data(model_path, input_path, processed_path, output_path):
    raw = pd.read_csv(input_path)
    raw_unique = raw.drop_duplicates().reset_index(drop=True)

    order_id = raw["order_id"].copy()

    cleaned_data = clean_data(
        input_path,
        processed_path
    )

    model = joblib.dump(model_path)

    predictions = model.predict(cleaned_data)

    result = pd.DataFrame({
        "order_id": order_id,
        "predicted_is": predictions
    })

    result.to_csv(output_path,index=False)


    return result
