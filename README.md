# Peer2Peer: Student Performance Evaluation Based on Peer Evaluation

Peer2Peer is a web-based peer evaluation system developed as a Final Year Project (FYP) at Universiti Sains Malaysia. It enables students to evaluate their groupmates anonymously, and leverages predictive analytics to assist educators in making fair and data-driven decisions about student contributions in group projects.

---

## 🔍 Features

- 🔒 **Anonymous Peer Evaluation**  
  Students evaluate each other based on 6 structured criteria using a Likert scale.

- 🧠 **Performance Prediction with ML**  
  Uses a Random Forest model to predict a student’s grade group (High or Mid) based on peer scores.

- 📊 **Educator Dashboard**  
  Visualizations including bar charts, radar charts, and donut charts to show group performance and completion status.

- 📥 **Self-Evaluation and Feedback**  
  Students receive feedback summaries and anonymous comments to reflect on their performance.

- 🧾 **PDF Report Export**  
  Educators can download summarized reports in PDF format.

---

## 🛠️ Tech Stack

- **Backend**: Python (Flask), SQLite
- **Frontend**: HTML, CSS, JavaScript
- **Machine Learning**: Scikit-learn (Random Forest), SMOTE for class balancing
- **Visualization**: Plotly
- **PDF Generation**: ReportLab

---

## 📁 Folder Structure

```
├── peer2peer/
│ ├── app.py
│ ├── models.py
│ ├── rf_classifier.py
│ ├── static/
│ ├── templates/
│ ├── peer_evaluation.db
│ └── grade_predict_rf_model.pkl
└── README.md
```

---

## 📈 Machine Learning Overview

- **Model Used**: Random Forest Classifier  
- **Target**: Grade group classification (High, Mid)  
- **Features**: Peer evaluation scores on 6 criteria  
- **Reason for Grouping**: Original grade data was imbalanced (e.g., few low-grade instances). Grades were grouped as:  
  - High: A, A-, B+  
  - Mid: B, B-, C+, C  

  If a student is predicted as "High", the output lists all possible grades in that group (e.g., A/A-/B+).

---

## 🚀 How to Run Locally

1. Clone the repository
2. Create a virtual environment
3. Install dependencies:
```
pip install -r requirements.txt
```
4. Run the app:
5. Visit `http://localhost:5000` in your browser

---

## 📚 Credits

- **Author**: Auni Nasuha Binti Md Noh  
- **Supervisor**: Dr. Nor Athiyah Abdullah  
- **University**: Universiti Sains Malaysia

---

## 📃 License

This project is for academic purposes only.
