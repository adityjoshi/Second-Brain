import os 
import pandas as pd 
from sklearn.ensemble import RandomForestClassifier
import pickle


def clean_data(input_path,output_path):
    df = pd.read_csv(input_path)

    booking_columns = [order_id,dispatch_date,origin,warehouse_code,destination_city]

    df = df.drop_duplicates().reset_index(drop=True)

    df = df.drop(columns=[booking_columns],errors="ignore")

    numeric_columns = df.select_dtypes(include="numbers").columns

    for columns in numeric_columns:
        df[columns] = df[columns].fillna(df[columns].median())



    if "shipping_speed" in df.columns:
        df["shipping_speed"] = (
            df["shipping_speed"].astype(str).str.strip().str.lower().map({"standard":0,"express":1,"priority":2})
        )

    if "is_weekend" in df.columns:
        df["is_weekend"] = (
            df["is_weekend"].astype(str).str.strip().str.lower().map({"no":0,"yes":1})
        )

    df.to_csv(output_path,index=False)

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



def predict_new_data(model_path,input_path,processed_path,output_path):
    raw_df = pd.read_csv(input_path)
    raw_unique = raw_df.drop_duplicates().reset_index(drop=True)

    order_id = raw_df["order_id"].copy()

    cleaned_df = clean_data(
        input_path,
        processed_path
    )

    model = joblib.dump(model_path)

    predictions = model.predict(cleaned_df)

    result = pd.DataFrame({
        "order_id":order_id.to_numpy(),
        "predicted_is_delayed":predictions
    })

    result.to_csv(output_path,index=False)

    return result
