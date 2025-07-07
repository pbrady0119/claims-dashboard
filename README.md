Claims Data Dashboard with NQL Chatbot
An interactive Streamlit dashboard visualizing synthetic healthcare claims data, enabling dynamic filtering and GPT-powered natural language querying.

Features
Interactive filters: Filter by insurance plan, provider, claim status, service location, and turnaround days.

Dynamic visuals: KPI metrics, turnaround distribution, top providers, denial reasons, volume trends, and payment breakdowns.

Natural Language Query (NQL) Chatbot: Powered by OpenAI, allowing users to request charts or filtered views conversationally.

Safe query parsing: Column whitelisting prevents invalid or unsafe queries.

Powered by OpenAI: Secure integration using environment variables.

Project Structure
Home.py: Main dashboard with NQL chatbot.

data/: Stores the synthetic claims dataset.

scripts/generate_claims_data.py: Creates the synthetic dataset.

.env: Stores sensitive configurations (e.g., OPENAI_API_KEY).

Setup Instructions
Clone the repository:


git clone https://github.com/<your_username>/claims-dashboard.git
cd claims-dashboard
Create and activate a virtual environment:


python -m venv venv
source venv/bin/activate  # or venv\Scripts\activate on Windows
Install dependencies:


pip install -r requirements.txt
Create a .env file:


OPENAI_API_KEY=your_openai_key
CLAIMS_DATA_PATH=data/claims_data.csv
Run the dashboard:


streamlit run Home.py
Example Queries
Show denied claims from last month.

Show the top 10 claims with the highest billed amounts.

Show claims with turnaround days under 5.

License
This project is provided for educational and non-commercial demonstration purposes using synthetic data.

Contributing
If you wish to extend functionality, improve visuals, or add tests, feel free to open issues or submit pull requests.

✅ This version maintains clarity, professionalism, and clean readability aligned with BI / Data Engineering portfolios and GitHub best practices.

⚡ Let me know once you’ve added this to your repo so we can fully close out the claims dashboard and begin the semi-structured/unstructured pipeline project next.
