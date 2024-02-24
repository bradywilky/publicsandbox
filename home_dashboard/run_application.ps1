# Check if the virtual environment exists, and create it if it doesn't
if (-Not (Test-Path home_dashboard_venv)) {
    python -m venv home_dashboard_venv
}

# Activate the virtual environment
. .\home_dashboard_venv\Scripts\Activate.ps1

# Install all required Python libraries
pip install -r requirements.txt

# Run the application
python run_application.py