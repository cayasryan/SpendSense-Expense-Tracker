# SpendSense - Expense Tracker

SpendSense is a **Dash-based** expense tracking application that connects to a **PostgreSQL** database for secure and efficient financial record-keeping. It provides interactive visualizations and tools to help users monitor their spending habits.

## Features
- **Expense Tracking**: Effortlessly add, edit, or remove transactions.
- **Account Monitoring**: Keep track of balances across multiple accounts in real-time.
- **Interactive Summaries**: Filter and customize summary tables to focus on the data that matters most.
- **Secure Data Storage**: Uses PostgreSQL for structured, reliable, and secure data management.

## Installation & Setup

### 1. Clone the Repository
```bash
git clone https://github.com/your-username/SpendSense-Expense-Tracker.git
cd SpendSense-Expense-Tracker
```

### 2. Install Dependencies
Make sure you have Python installed, then install the required packages:

```bash
pip install -r requirements.txt
```

### 3. Set Up PostgreSQL
Ensure you have a PostgreSQL database running. Create a database and update your .env file with the correct credentials:

```plaintext
DB_NAME=your_database
DB_USER=your_username
DB_PASSWORD=your_password
DB_HOST=localhost
DB_PORT=5432
```

4. Run the Application
```
python app.py
```
Then, open http://localhost:8050/ in your browser.



## Application Screenshots
### Log-in Page
<img width="1386" alt="image" src="https://github.com/user-attachments/assets/1242dc0e-9b76-4222-9abb-dd5218c4ce16" />

### Home Page
<img width="1238" alt="image" src="https://github.com/user-attachments/assets/672560f1-ccdb-40f3-8f3a-8ce1a55b68d4" />

### Transactions Page
<img width="1488" alt="image" src="https://github.com/user-attachments/assets/7a015a1a-3ff7-40cd-b23f-bc6fae65ad94" />

### Accounts Page
<img width="1536" alt="image" src="https://github.com/user-attachments/assets/d470be9a-7ea9-435c-b990-73b1ca5598b4" />


## Entity-Relationship Diagram
<img width="1540" alt="image" src="https://github.com/user-attachments/assets/c53e8349-ef95-46a0-b311-1a6bb6a338b0" />

## Relational Database
<img width="1757" alt="image" src="https://github.com/user-attachments/assets/eab81a0b-cff0-474c-913d-5a1b0a1a7589" />
