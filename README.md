# 📊 FlexiFees: AI-Powered Student Finance & Fraud Monitor

FlexiFees is a smart financial management ecosystem designed for educational institutions. It leverages the M-Pesa API for seamless fee collection and utilizes Machine Learning to detect fraudulent payment patterns in real-time.

---

## 📖 About the Project
**The Problem:** Many schools in Kenya face challenges with manual fee tracking and "ghost" payment claims. Verification is slow, and financial leakage often goes unnoticed.

**The Solution:** FlexiFees digitizes the payment lifecycle. By integrating an **ML Anomaly Detection engine**, the platform automatically flags suspicious transaction behaviors—such as unusual payment velocities or amount outliers—allowing administrators to intervene before losses occur.

---

## 🚨 Key Features
- **M-Pesa STK Push:** Direct, secure fee payments from the app to the school's till.
- **ML Fraud Monitor:** Uses an **Isolation Forest** model to identify high-risk transactions based on Z-scores and time-of-day patterns.
- **Live Analytics Dashboard:** Real-time visualization of collection rates, outstanding balances, and flagged anomalies.
- **Automated Pipeline:** Self-training ML model that updates its baseline as more transaction data is ingested.

---

## 🛠️ Tech Stack & AI Tools
- **Backend:** FastAPI (Python), SQLAlchemy, SQLite.
- **Data Science:** Scikit-Learn (Isolation Forest), Pandas, NumPy, Joblib.
- **Frontend/Dashboard:** Streamlit, Plotly, Streamlit-Autorefresh.
- **DevOps:** Docker & Docker Compose (WSL 2 Optimized).
- **AI Collaborator:** Gemini 3 Flash (used for architecture optimization and code refactoring).

---

## 👥 The Team
| Name | Role | Contact |
| :--- | :--- | :--- |
| **Maxwell Oduor** | Data Science & MLOps | maxwelloduor55@gmail.com |
| **Salha Benazir** | Backend Engineer | salhabenazir@gmail.com |
| **Leonida Jeptoo** | Frontend/UX Designer | jeptooleonida@gmail.com |
| **Bevon Mokua** | Backend & Database | bevonmokuas@gmail.com |
| **Peter Maina** | Backend  | mainapeterkanyuku1@gmail.com |
| **Brian Kioko** |  Cybersecurity| lessusbrian7@gmail.com |

---

## ⚙️ Setup and Installation

### 1. Environment Configuration
Create a `.env` file in the root directory:
```env
MPESA_CONSUMER_KEY=your_key_here
MPESA_CONSUMER_SECRET=your_secret_here
MPESA_PASSKEY=your_passkey_here
DATABASE_URL=sqlite:///./flexifees.db
DEBUG=True
```


## ⚙️ Run the Project

### 2. Run with Docker (Recommended)

This command builds the environment, initializes the database, and trains the fraud model automatically:

```bash
docker compose up --build
```

### Access the Services

- **API Documentation:** http://localhost:8000/docs  
- **Analytics Dashboard:** http://localhost:8501  

---

## ⚙️ Running Locally (Alternative)

```bash
# Install dependencies
pip install -r backend/requirements.txt
```

# Start the Backend
```
cd backend
uvicorn app.main:app --reload
```

# Start the Dashboard (in a new terminal)
```
streamlit run app/analytics/dashboard/dashboard.py

```
## 🧠 How the Solution Works

The core of FlexiFees' intelligence is its **Anomaly Detection Pipeline**, designed to detect suspicious financial activity in real time.

### 1. Data Ingestion
Payments are initiated via **M-Pesa STK Push** and captured through the backend API. These transactions are then stored in a SQLite database using FastAPI.

### 2. Feature Engineering
Before feeding data into the model, the system derives meaningful features:

- **Amount Z-Scores**  
  Measures how much a transaction deviates from the average payment behavior.

- **Payment Velocity**  
  Tracks how many transactions occur within a short time window (e.g., 24 hours).

- **Night-Time Flags**  
  Identifies transactions occurring at unusual hours (e.g., 2 AM), which may indicate suspicious behavior.

### 3. Model Inference
An **Isolation Forest** model processes these features. Since fraudulent transactions are rare and structurally different, the model isolates them as anomalies from normal transaction clusters.

### 4. Real-Time Monitoring
Transactions flagged as anomalous are:

- Marked as **high-risk**  
- Highlighted in red on the dashboard  
- Available for immediate administrative review  

### 5. Continuous Learning Pipeline
As new transaction data is collected:

- The dataset grows  
- The model retrains periodically  
- Detection accuracy improves over time  

---

## 📸 Screenshots

- Admin Analytics Dashboard  
- ML Fraud Detection Insights  
- Visualizing school debt and collection trends  
- Real-time anomaly flagging by the ML model  

---

## 🔗 Project Links & Credentials

- **Live Demo Link:** [Insert Link Here]  
- **Walkthrough Video:** [Insert Drive/YouTube Link]  

### Test Account Details

- **Admin Role:** admin@flexifees.com / password123  
- **Student Role:** student@flexifees.com / password123  

---

## 📜 Collaboration Transparency

This project was developed as a collaborative effort within the Drift Team. All code, model training, and architectural decisions were made collectively, with specific focus areas assigned to leverage individual expertise in Backend Engineering, Data Science, and Frontend UX.

This repository is publicly accessible and follows clean code practices for maintainability.
