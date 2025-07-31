from sklearn.linear_model import LogisticRegression
from sklearn.tree import DecisionTreeClassifier
from sklearn.model_selection import train_test_split
from sklearn.metrics import classification_report
import pandas as pd

def train_and_predict(csv_path, model_type='logistic'):
    df = pd.read_csv(csv_path)

    df.dropna(inplace=True)
    X = df[['gpa', 'attendance']]  # Must match your columns
    y = df['label']  # 0 = Fail, 1 = Pass

    X_train, X_test, y_train, y_test = train_test_split(X, y, test_size=0.2)

    model = LogisticRegression() if model_type == 'logistic' else DecisionTreeClassifier()
    model.fit(X_train, y_train)

    predictions = model.predict(X_test)
    report = classification_report(y_test, predictions, output_dict=True)

    df['prediction'] = model.predict(X)
    return df, report
