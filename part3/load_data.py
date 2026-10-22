"""Loads the Part 3 data.

Put the downloads into a data/ directory next to this file, then run:

    python load_data.py

Needs pandas (pip install pandas).
"""

from pathlib import Path
from sklearn.linear_model import LogisticRegression
from sklearn.feature_extraction.text import TfidfVectorizer
import pickle
import pandas as pd

DATA = Path(__file__).resolve().parent / "data"

MAPPINGS = {
    "gender": {"male": 0, "female": 1, "unknown": 2},
    "age": {"18-24": 0, "25-34": 1, "35-44": 2, "45-54": 3, "55-64": 4, "65+": 5},
    "education": {"high_school": 0, "some_college": 1, "bachelors": 2, "graduate": 3},
    "household_income": {
        "top_10": 0, "11_20": 1, "21_30": 2, "31_40": 3, "41_50": 4, "lower_50": 5, "unknown": 6
    },
    "industry": {
        "tech": 0, "healthcare": 1, "education": 2, "finance": 3, "retail": 4, "construction": 5, "hospitality": 6, "transport": 7, "government": 8, "manufacturing": 9, "arts_media": 10, "other": 11, "not_applicable": 12
    },
    "employment_status": {
        "employed_ft": 0, "employed_pt": 1, "self_employed": 2, "unemployed": 3, "student": 4, "retired": 5
    },
    "employer_size": {"solo": 0, "small_1_49": 1, "mid_50_999": 2, "large_1000_plus": 3, "not_applicable": 4},
    "home_ownership": {"own": 0, "rent": 1, "other": 2},
    "parental_status": {"parent": 0, "not_parent": 1}
}

REVERSE_MAPPING = {
    "gender": {"male": 0, "female": 1, "unknown": 2},
    "age": {"18-24": 0, "25-34": 1, "35-44": 2, "45-54": 3, "55-64": 4, "65+": 5},
    "education": {"high_school": 0, "some_college": 1, "bachelors": 2, "graduate": 3},
    "household_income": {
        "top_10": 0, "11_20": 1, "21_30": 2, "31_40": 3, "41_50": 4, "lower_50": 5, "unknown": 6
    },
    "industry": {
        "tech": 0, "healthcare": 1, "education": 2, "finance": 3, "retail": 4, "construction": 5, "hospitality": 6, "transport": 7, "government": 8, "manufacturing": 9, "arts_media": 10, "other": 11, "not_applicable": 12
    },
    "employment_status": {
        "employed_ft": 0, "employed_pt": 1, "self_employed": 2, "unemployed": 3, "student": 4, "retired": 5
    },
    "employer_size": {"solo": 0, "small_1_49": 1, "mid_50_999": 2, "large_1000_plus": 3, "not_applicable": 4},
    "home_ownership": {"own": 0, "rent": 1, "other": 2},
    "parental_status": {"parent": 0, "not_parent": 1}
}

REVERSE_MAPPING = {
    "gender": {0: "male", 1: "female", 2: "unknown"},
    "age": {0: "18-24", 1: "25-34", 2: "35-44", 3: "45-54", 4: "55-64", 5: "65+"},
    "education": {0: "high_school", 1: "some_college", 2: "bachelors", 3: "graduate"},
    "household_income": {
        0: "top_10", 1: "11_20", 2: "21_30", 3: "31_40", 4: "41_50", 5: "lower_50", 6: "unknown"
    },
    "industry": {
        0: "tech", 1: "healthcare", 2: "education", 3: "finance", 4: "retail", 5: "construction", 6: "hospitality", 7: "transport", 8: "government", 9: "manufacturing", 10: "arts_media", 11: "other", 12: "not_applicable"
    },
    "employment_status": {
        0: "employed_ft", 1: "employed_pt", 2: "self_employed", 3: "unemployed", 4: "student", 5: "retired"
    },
    "employer_size": {0: "solo", 1: "small_1_49", 2: "mid_50_999", 3: "large_1000_plus", 4: "not_applicable"},
    "home_ownership": {0: "own", 1: "rent", 2: "other"},
    "parental_status": {0: "parent", 1: "not_parent"}
}

models = {}
predictions = {}

# Nine predictive values. 
ATTRIBUTES = [
    "gender", "age", "education", "household_income", "industry",
    "employment_status", "employer_size", "home_ownership", "parental_status",
]

# Helper function for reading from *.jsonl.gz files
def load_users(split: str) -> pd.DataFrame:
    return pd.read_json(DATA / f"{split}.jsonl.gz", lines=True, dtype=False)

# Helper function for reading from *.csv files
def load_labels(split: str) -> pd.DataFrame:
    if split == "test":
        raise ValueError("test has no labels")
    return pd.read_csv(DATA / f"{split}_labels.csv", dtype=str,
                       keep_default_na=False)

def prepLabels(labels: pd.DataFrame):
    # Map attributes into values
    attrList = labels.columns.to_list()
    for attr in attrList:
        if attr != "client_id":
            labels[attr] = labels[attr].map(MAPPINGS[attr])

# Helper for adding user search queries into one array, one entry per user
def prepUserData(users: pd.DataFrame) -> list[str]:
    # Iterate through each user and add query to list
    allSearches = []
    for i in range(len(users["searches"].array)):
        userSearches = []
        for search in users["searches"].iloc[i]:
            userSearches.append(search["query"] + " ")
        result = "".join(userSearches)
        allSearches.append(result)
    
    return allSearches

# Helper function for fitting model
def fitModel(matrix):
    for key in MAPPINGS.keys():
        print("Training model for " + key)
        model = LogisticRegression()
        model.fit(matrix, labels[key])
        models[key] = model

# def saveModel(vectorizer: TfidfVectorizer):
#     with open("tfidf_vectorizer.pkl", "wb") as file:
#         pickle.dump(vectorizer, file)

# def loadModelIfSaved(vectorizer: TfidfVectorizer):
#     try:
#         loadedVectorizer = None
#         with open("tfidf_vectorizer.pkl", "rb") as file:
#             loadedVectorizer = pickle.load(file)
#         print("Loaded vectorizer from file")

#         # Populate models dictionary with
#         return loadedVectorizer
    
#     except FileNotFoundError:
#         return None

def reverseMap(key: str, value):
    return str(REVERSE_MAPPING[key][value])

def savePredictions():
    # Write labels to file
    with open("predictions.csv", "w") as file:
        # Create initial first line and write it
        labelLine = []
        for key in MAPPINGS.keys():
            labelLine.append(key)
        result = ",".join(labelLine)
        file.write(result + "\n")

        # Iterate through each user
        for i in range(predictions["gender"].size):
            # Iterate through each attribute
            labelLine = []
            for key in predictions:
                label = reverseMap(key, predictions[key][i])
                labelLine.append(label)
            result = ",".join(labelLine)
            print(result)
            file.write(result + "\n")

        file.close()


# -- ACTUAL FUNCTIONS -- #
# Function for initially training model using fit_transform
def trainModel(vectorizer: TfidfVectorizer, users: pd.DataFrame, labels: pd.DataFrame):
    print("-- Training model... --")
    # Iterate through each user and add query to list
    prepLabels(labels)
    allSearches = prepUserData(users)
    # Vectorize queries and perform initial fit + transformation
    matrix = vectorizer.fit_transform(allSearches)
    # Fit a model for each of the 9 attributes
    fitModel(matrix)

def updateModel(vectorizer: TfidfVectorizer, users: pd.DataFrame, labels: pd.DataFrame):
    print("-- Updating model... --")
    #allSearches = prepUserData(users)

def predictLabels(vectorizer: TfidfVectorizer, users: pd.DataFrame):
    print("-- Predicting labels... --")
    allSearches = prepUserData(users)
    matrix = vectorizer.transform(allSearches)

    # Make prediction of each attribute, add to dict
    for key in MAPPINGS.keys():
        predictions[key] = models[key].predict(matrix)
        print(predictions[key])

    # Write predictions into csv file
    savePredictions()
    
if __name__ == "__main__":
    vectorizer = TfidfVectorizer()
    for split in ("train", "dev", "test"):
        users = load_users(split)
        print(f"{split}: {len(users)} users")
        print(users["client_id"])
        
        if split != "test":
            labels = load_labels(split)
            if split == "train":
                trainModel(vectorizer, users, labels)
            else:
                updateModel(vectorizer, users, labels)
        else:
            predictLabels(vectorizer, users)