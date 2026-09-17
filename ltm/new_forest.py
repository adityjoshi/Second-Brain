import pandas as pd
from sklearn.ensemble import RandomForestClassifier


def clean_data(input_path,output_path):
    df = pd.read_csv(input_path)
    
    booking_columns = ["order_id","dispatch_date","origin_warehouse_code", "destination_city", "courier_partner"]

    df = df.drop_duplicates().reset_index(drop=True)

    df = df.drop(columns=[booking_columns])

    num_col = ["distance_km","package_weight_kgs"]

    for col in num_col:
        df[col] = df[col].fillna(df[col].median())


    if "shipping_speed" in df.columns:
        df["shipping_speed"] = (df["shipping_speed"].astype(str).str.split().str.lower().map({"standard":0,"express":1,"priority":2}))

    if "is_weekend_dispatch" in df.columns:
        df["is_weekend_dispatch"] = (
            df["is_weekend_dispatch"] = df["is_weekend_dispatch"].astype(str).str.split().str.lower().map({"no":0,"yes":1})
        )


    df = df.to_csv(output_path,index=False)

    return df


def train_model(processed_path,model_path):
    df = pd.read_csv(processed_path)
    X = df.drop(df["is_delayed"])
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
    raw_processed = raw.drop_duplicates().reset_index(drop=True)

    order_id = raw_processed["order_id"].copy()

    cleaned_df = clean_data(input_path,processed_path)

    model = joblib.dump(model_path)

    predictions = model.predict(cleaned_df)

    result = pd.DataFrame({
        "order_id": order_id,
        "predicted_is_delayed": predictions
    })

    result.to_csv(output_path,index=False)

    return result

