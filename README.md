# 📊 Predictive Churn & Retention CRM

An enterprise-grade CRM analytics dashboard engineered to monitor account health, identify early churn signals, and automate personalized retention workflows for subscription-based customers.

This project bridges the gap between backend data pipelines and highly interactive frontend user experiences, providing a clear visual representation of customer risk across a portfolio.

## 🚀 Key Features

*   **Interactive Dashboard UI:** Built with Streamlit, featuring a modern glassmorphism aesthetic, custom CSS, and responsive metric cards.
*   **Persistent Data Pipeline:** Utilizes a local SQLite database for robust, secure storage of customer records, subscription plans, and usage metrics.
*   **Dynamic Risk Scoring:** Implements a rule-based algorithm using Pandas to calculate 0-100% churn probabilities based on support ticket volume, account age, and platform usage gaps.
*   **Automated Retention Action:** Extracts live database parameters to instantly generate context-specific, personalized outreach emails for high-risk accounts.

## 💻 Tech Stack

*   **Backend:** Python 3
*   **Database:** SQLite3
*   **Data Manipulation:** Pandas
*   **Frontend:** Streamlit, Custom CSS
*   **Version Control:** Git & GitHub

## ⚙️ Local Installation & Setup

To run this CRM locally on your machine, follow these steps:

1. **Clone the repository:**
```bash
   git clone https://github.com/ChillOutFam-17/predictive-churn-crm.git
   cd predictive-churn-crm
```
2. **Install the required dependencies:**
```bash
   pip install -r requirements.txt
```
3. **Launch the application:**
```bash
   streamlit run app.py
```
## 🗺️ Project Roadmap

**Phase 1: Architecture & Rule-Based Scoring (Current)**
- [x] Full-stack UI implementation
- [x] SQLite database architecture and CRUD operations
- [x] Pandas-driven rule-based churn calculation
- [x] Automated email generation workflow

**Phase 2: Machine Learning Integration (Upcoming)**
- [ ] Transition from rule-based scoring to predictive machine learning.
- [ ] Implement Scikit-Learn to train a Random Forest Classifier on historical churn data.
- [ ] Add dynamic hyperparameter tuning and model confidence scores to the dashboard.


## 👤 Author

**Utkarsh Pratap Singh**
*B.Tech Computer Science & Engineering, VIT-AP University*  
*Diploma in Data Science, IIT Guwahati*  
[Connect on LinkedIn](https://www.linkedin.com/in/utkarsh-pratap-singh-129b62383)
