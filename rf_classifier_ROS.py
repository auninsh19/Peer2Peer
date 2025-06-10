import os
import pandas as pd
import numpy as np
from sklearn.model_selection import train_test_split, cross_val_score
from sklearn.ensemble import RandomForestClassifier
from sklearn.metrics import accuracy_score, classification_report, confusion_matrix
from sklearn.preprocessing import LabelEncoder
from imblearn.over_sampling import SMOTE
import seaborn as sns
import matplotlib.pyplot as plt
import joblib

# Optional: XGBoost and LightGBM
#from xgboost import XGBClassifier
#from lightgbm import LGBMClassifier

# Step 1: Load data from Excel
os.chdir('/Users/auninasuha/Documents/USM/CAT405/peer2peer')
data = pd.read_excel('Data for training.xlsx', sheet_name='Sheet1')

# Step 2: Feature engineering
data['ScoreStd'] = data[['Pavg', 'Lavg', 'Cavg', 'TMavg', 'CommAvg', 'PSavg']].std(axis=1)
features = ['Pavg', 'Lavg', 'Cavg', 'TMavg', 'CommAvg', 'PSavg', 'ScoreStd']
X = data[features]

# Step 3: Grade grouping function
def map_grade_to_group(grade):
    high = ['A', 'A-', 'B+']
    mid = ['B', 'B-', 'C+', 'C']
    low = ['C-', 'D+', 'D', 'D-', 'F']
    
    if grade in high:
        return 'High'
    elif grade in mid:
        return 'Mid'
    elif grade in low:
        return 'Low'
    else:
        return 'Unknown'  # Catch any unexpected values

# Step 4: Apply grade grouping
data['GradeGroup'] = data['Grade'].apply(map_grade_to_group)
y = data['GradeGroup']

# Group to grade mapping (for inference)
group_to_grades = {
    'High': ['A', 'A-', 'B+'],
    'Mid': ['B', 'B-', 'C+', 'C'],
    'Low': ['C-', 'D+', 'D', 'D-', 'F']
}

# Check class distribution before filtering
#print("Class distribution before sampling:")
#print(pd.Series(y).value_counts()) ##

# Step 5: Filter out classes with < 2 samples
min_samples = 2
class_counts = y.value_counts()
classes_to_keep = class_counts[class_counts >= min_samples].index
X = X[y.isin(classes_to_keep)]
y = y[y.isin(classes_to_keep)]


# Step 7: Stratified train-test split ##
X_train, X_test, y_train, y_test = train_test_split(
    X, y, test_size=0.2, random_state=42, stratify=y 
)

# Check class distribution after sampling
print("y_train Class distribution:")
print(pd.Series(y_train).value_counts()) ##

# Step 8: Apply SMOTE
smote = SMOTE(random_state=42)
X_resampled, y_resampled = smote.fit_resample(X_train, y_train)


# ==========================
# CLASSIFIER OPTIONS
# ==========================

# ✅ Option 1: Random Forest with class_weight
rf_classifier = RandomForestClassifier(
    n_estimators=150,
    max_depth=6,
    min_samples_split=4,
    min_samples_leaf=2,
    class_weight='balanced',
    random_state=42
)
rf_classifier.fit(X_resampled, y_resampled)
model = rf_classifier

# 🔵 Option 2: XGBoost (uncomment to use)
#xgb_classifier = XGBClassifier(
#    n_estimators=150,
#    max_depth=6,
#    learning_rate=0.1,
#    objective='multi:softmax',
#    num_class=len(le.classes_),
#    eval_metric='mlogloss',
    #use_label_encoder=False,
#    random_state=42
#)
#xgb_classifier.fit(X_resampled, y_resampled)
#model = xgb_classifier

#🟡 Option 3: LightGBM (uncomment to use)
#lgbm_classifier = LGBMClassifier(
#    n_estimators=150,
#    max_depth=6,
#    learning_rate=0.1,
#    class_weight='balanced',
#    random_state=42
#)
#lgbm_classifier.fit(X_resampled, y_resampled)
#model = lgbm_classifier


# ==========================
# Evaluation
# ==========================

# Cross-validation
cv_scores = cross_val_score(model, X_resampled, y_resampled, cv=5)
print("Cross-validated accuracy (mean):", round(cv_scores.mean(), 2))

# Prediction
y_pred = model.predict(X_test)
#y_test_decoded = le.inverse_transform(y_test)
#y_pred_decoded = le.inverse_transform(y_pred)

# Accuracy
accuracy = accuracy_score(y_test, y_pred)
print(f'Accuracy of Grade Prediction: {accuracy:.2f}')

# Classification report
print("Classification Report:")
print(classification_report(y_test, y_pred))

# Confusion matrix
conf_matrix = confusion_matrix(y_test, y_pred, labels=['High', 'Mid', 'Low'])
print("Confusion Matrix:")
print(conf_matrix)

# Visualize confusion matrix
#plt.figure(figsize=(10, 7))
#sns.heatmap(conf_matrix, annot=True, fmt='d', cmap='Blues',
            #xticklabels=['High', 'Mid', 'Low'], yticklabels=['High', 'Mid', 'Low'])
#plt.ylabel('Actual Grades')
#plt.xlabel('Predicted Grades')
#plt.title('Confusion Matrix')
#plt.show()

# ========== Show Multiple Probable Grades ==========

#print("\n--- Inference with Possible Actual Grades ---")
#for i, group in enumerate(y_pred_decoded):
    #probable_grades = group_to_grades.get(group, ['Unknown'])
    #print(f"Sample {i+1}: Predicted Group = {group} → Possible Grades: {probable_grades}")

# Step 10: Save the model ✅

import joblib

joblib.dump(model, 'grade_predict_rf_model.pkl')
print("\n✅ Model saved as 'grade_predict_rf_model.pkl'")

