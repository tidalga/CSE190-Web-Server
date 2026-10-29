from sklearn.feature_extraction.text import TfidfVectorizer
from sklearn.linear_model import LogisticRegression
import load_data as ld # part3/load_data.py

class Classifier:
    def __init__(self):
        self.models: dict[str, LogisticRegression] = ld.loadModels("models")
        self.vectorizer: TfidfVectorizer  = ld.loadVectorizer("tfidf_vectorizer")

    def generateLabels(self, searches: list[str]) -> dict[str, str]:
        # Combine searches into list of one string
        combinedSearches = [" ".join(searches)]
        # Call predict labels
        predictions = ld.predictLabels(self.vectorizer, self.models, combinedSearches)
        # Remap predictions
        ld.remapPredictions(predictions)

        return predictions