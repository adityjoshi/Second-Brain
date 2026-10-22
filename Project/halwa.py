from multiprocessing import process
import os
from turtle import mode
import joblib
import pandas as pd
import numpy as np
from sklearn import tree
from sklearn.pipeline import make_pipeline
from sklearn.preprocessing import StandardScaler
from sklearn.tree import DecisionTreeClassifier
from sklearn.svm import SVC
from sklearn.metrics import f1_score, accuracy_score


TRAIN_DIR = "data/service_ticket_train.csv"
TEST_DIR = "data/service_ticket_test.csv"
PREDICT_DIR = "data/service_ticket_predict.csv"
TRAIN_PROCESSED = "processed_data/service_ticket_train.csv"
TEST_PROCESSED = "processed_data/service_ticket_test.csv"
PREDICT_PROCESSED_DIR = "processed_data/service_ticket_predict.csv"
TREE_MODEL = "artifacts/decision_tree_model.pkl"
SVC_MODEL = "artifacts/svc_model.pkl"
OUTPUT_PATH = "output/predicted_priority_levels.csv"


RECORD_COLUMNS = [
    "ticket_id",
    "raised_date",
    "reporting_location",
    "assigned_group",
    "requester_department",
]

def clean_data(input_path,output_path):
    df = pd.read_csv(input_path)
    df = df.drop(columns=RECORD_COLUMNS)
    df = df.drop_duplicates(keep="first")

    for col in ["affected_user_count","average_resolution_hours"]:
        df[col] = df[col].fillna(df[col].median())

    df["service_criticality"] = df["service_criticality"].str.strip().str.lower().map({
        "low":0,
        "medium":1,
        "high":2
    })

    df["is_business_hours"] = df["is_business_hours"].str.strip().str.lower().map({
        "no":0,
        "yes":1
    })

    df["priority_level"] = df["priority_level"].str.strip().str.upper().map({
        "P1":0,
        "P2":1,
        "P3":2,
        "P4":3
    })

    df.to_csv(output_path,index=False)

    return df


def train_tree_model(processed_path, model_path):
    df = pd.read_csv(processed_path)
    X = df.drop(columns="priority_level")
    y = df["priority_level"]

    model = DecisionTreeClassifier(max_depth=10,random_state=42)

    model.fit(X,y)

    joblib.dump(model,model_path)

    return model


def train_svc_model(processed_path,model_path):
    df = pd.read_csv(processed_path)
    X = df.drop(columns="priority_level")
    y = df["priority_level"]

    model = make_pipeline(StandardScaler(),SVC(kernel="rbf",C=1.0,random_state=42))

    model.fit(X,y)

    joblib.dump(model,model_path)

    return model


def compare_models(tree_model_path,svc_model_path,features_test,target_test):
    tree_load = joblib.load(tree_model_path)
    svc_load = joblib.load(svc_model_path)

    models = [("DecisionTreeClassifier",tree_load),("SVC",svc_load)]

    results = []

    for name, model in models:
        prediction = model.predict(features_test)

        results.append({
            "model_name":name,
            "accuracy": accuracy_score(target_test,prediction),
            "f1_score": f1_score(target_test,prediction,average="macro")
        })

    result_df = pd.DataFrame(results)

    return result_df.sort_values(by="accuracy",ascending=False).reset_index(drop=True)


def evaluate_model(model_path, features_test, target_test):
    model = joblib.load(model_path)
    predictions = model.predict(features_test)
    acc = accuracy_score(target_test,predictions)
    f1 = f1_score(target_test,predictions,average="macro")

    return float(acc),float(f1)


def predict_new_data(model_path, input_path, processed_path, output_path):
    model = joblib.load(model_path)
    df = pd.read_csv(input_path)
    ticket_id = df["ticket_id"]

    cleaned_df = clean_data(input_path,processed_path)
    pred = model.predict(cleaned_df)
    BANDS = ["P1", "P2", "P3", "P4"]
    result = pd.DataFrame({
        "ticket_id":ticket_id,
        "predicted_priority_level": [BANDS[x] for x in pred]
    })

    result.to_csv(output_path,index=False)
    return result


if __name__ == "__main__":
    train_df = clean_data(TRAIN_DIR,TRAIN_PROCESSED)
    print(train_df.shape)
    test_df = clean_data(TEST_DIR,TEST_PROCESSED)
    print(test_df.shape)
    features_test = test_df.drop(columns="priority_level")
    target_test = test_df["priority_level"]

    train_tree_model(TRAIN_PROCESSED,TREE_MODEL)
    train_svc_model(TRAIN_PROCESSED,SVC_MODEL)

    compare = compare_models(TREE_MODEL,SVC_MODEL,features_test,target_test)
    print(compare)
    best_model = compare.iloc[0]["model_name"]
    top_model = TREE_MODEL if compare ==
