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
peer2peer/
├── README.md
├── app.py
├── models.py
├── rf_classifier.py
├── static/
├── templates/
├── peer_evaluation.db
└── grade_predict_rf_model.pkl
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

1. Clone the repository navigate to the project folder
   ```
   git clone https://github.com/auninsh/peer2peer.git
   cd /your/path/to/peer2peer
   ```
3. Create a virtual environment and activate it (recommended). The name can be anything
   ```
   python -m venv myenv
   source myenv/bin/activate   # On Windows: myenv\Scripts\activate
   ```
5. Install dependencies
   ```
   pip install -r requirements.txt
   ```
4. Set Flask app environment variable
   ```
   export FLASK_APP=app.py          # On Windows: set FLASK_APP=app.py
   export FLASK_ENV=development     # Optional: for debug mode
   ```
5. Run the application
   ```
   flask run
   ```
6. Access the system:  
   After running the app, Flask will display a local link in the terminal such as:
   ```
   Running on http://127.0.0.1:5000
   ```
   You can click the link or copy and paste it into your browser to use the system.


---

## 📚 Credits

- **Author**: Auni Nasuha Binti Md Noh  
- **Supervisor**: Dr. Nor Athiyah Abdullah  
- **University**: Universiti Sains Malaysia

---

## 📃 License

This project is for academic purposes only.
