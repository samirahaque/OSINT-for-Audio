from flask import Flask, render_template, request, redirect, url_for, session, flash
import requests
import os
import urllib3
from datetime import datetime, timedelta
import logging
from logging.handlers import RotatingFileHandler
import pytz  # Ensure pytz is installed for timezone management

app = Flask(__name__)
app.secret_key = os.environ.get('FLASK_SECRET_KEY', 'default-secret-key')

# Environment variables for configuration
wazuh_api_url = os.getenv('WAZUH_API_URL', 'https://199.200.240.249:55000')
wazuh_auth_url = "https://199.200.240.249/auth/login"

VERIFY_SSL = False  # Set to True in production and handle SSL certificate verification appropriately

# Disable SSL warnings from urllib3 in development environments
if not VERIFY_SSL:
    urllib3.disable_warnings(urllib3.exceptions.InsecureRequestWarning)

@app.before_request
def before_request():
    """Check if token is near expiration and refresh it if necessary."""
    if 'jwt_token' in session and 'token_expires' in session:
        if is_token_expiring(session['token_expires']):
            refresh_token()  # Placeholder for refresh token logic

def is_token_expiring(token_expires):
    """Check if the JWT token is expiring within the next 15 minutes."""
    # Ensure datetime comparison is timezone-aware
    utc_now = datetime.now(pytz.utc)
    if isinstance(token_expires, str):
        token_expires = datetime.fromisoformat(token_expires).replace(tzinfo=pytz.utc)
    return utc_now >= token_expires - timedelta(minutes=15)

def authenticate_with_wazuh_api(username, password):
    """Authenticate with Wazuh API and return the JWT token."""
    auth_endpoint = f"{wazuh_api_url}/security/user/authenticate"
    try:
        response = requests.post(auth_endpoint, auth=(username, password), verify=VERIFY_SSL)
        if response.status_code == 200:
            jwt_token = response.json().get('data', {}).get('token')
            # Ensure token_expires is timezone-aware
            token_expires = datetime.now(pytz.utc) + timedelta(seconds=900)
            return jwt_token, token_expires
        else:
            return None, None
    except requests.RequestException as e:
        app.logger.error(f"Authentication failed: {e}")
        return None, None

def refresh_token():
    """Placeholder function to refresh JWT token."""
    # Implement token refresh logic here
    pass

@app.route('/', methods=['GET', 'POST'])
@app.route('/login', methods=['GET', 'POST'])
def login():
    if 'jwt_token' in session and 'token_expires' in session and not is_token_expiring(session['token_expires']):
        return redirect(url_for('dashboard'))

    if request.method == 'POST':
        username = request.form.get('username')
        password = request.form.get('password')
        jwt_token, token_expires = authenticate_with_wazuh_api(username, password)

        if jwt_token:
            session['jwt_token'] = jwt_token
            session['token_expires'] = token_expires
            return redirect(url_for('dashboard'))
        else:
            flash('Authentication failed')
            return redirect(url_for('login'))

    return render_template('login.html')



@app.route('/wazuh-auth', methods=['POST'])
def wazuh_auth():
    username = request.form.get('username')
    password = request.form.get('password')

    if not username or not password:
        flash('Username and password are required')
        return redirect(url_for('login'))

    # Adjust this URL to the direct login endpoint if it's different
    direct_login_url = wazuh_auth_url  

    try:
        response = requests.post(
            direct_login_url,
            json={"username": username, "password": password},
            headers={"Content-Type": "application/json"},
            verify=False  # Adjust as per your SSL configuration
        )
        if response.status_code == 200:
            # Assuming the token is in the response. Adjust as needed.
            # The handling here depends on how Wazuh's direct login response is structured.
            jwt_token = response.json().get('token')  # Adjust the key as per actual response
            session['jwt_token'] = jwt_token
            session['token_expires'] = datetime.now() + timedelta(seconds=900)
            return redirect(url_for('dashboard'))
        else:
            app.logger.error(f'Direct Wazuh Auth Failed: {response.status_code}, {response.text}')
            flash('Authentication with Wazuh failed')
            return redirect(url_for('login'))
    except requests.RequestException as e:
        app.logger.error(f'Request Exception: {e}')
        flash('An error occurred during authentication')
        return redirect(url_for('login'))

# Define other routes like '/dashboard', '/active-agents', etc. here
@app.route('/dashboard')
def dashboard():
    if 'jwt_token' not in session:
        flash('Please log in to view the dashboard')
        return redirect(url_for('login'))

    jwt_token = session['jwt_token']
    headers = {'Authorization': f'Bearer {jwt_token}'}

    # Fetching the overall summary of agents
    summary_endpoint = f"{wazuh_api_url}/agents/summary/status"
    summary_response = requests.get(summary_endpoint, headers=headers, verify=False)
    summary_data = summary_response.json().get('data', {}).get('connection', {})
    total_agents_count = summary_data.get('total', 0)
    active_agents_count = summary_data.get('active', 0)
    disconnected_agents_count = summary_data.get('disconnected', 0)
    pending_agents_count = summary_data.get('pending', 0)
    never_connected_count = summary_data.get('never_connected', 0)

    return render_template('dashboard.html',
                           total_agents_count=total_agents_count,
                           active_agents_count=active_agents_count,
                           disconnected_agents_count=disconnected_agents_count,
                           pending_agents_count=pending_agents_count,
                           never_connected_count=never_connected_count)
                           #top_active_agents_info=top_active_agents_info,
                           #top_disconnected_agents_info=top_disconnected_agents_info)


@app.route('/active-agents')
def active_agents():
    jwt_token = session.get('jwt_token')
    if not jwt_token:
        flash('Please log in to view active agents')
        return redirect(url_for('login'))

    headers = {'Authorization': f'Bearer {jwt_token}'}

    # Fetching all active agents data
    active_agents_endpoint = f"{wazuh_api_url}/agents?status=active&select=name,ip,os.name,status"
    active_agents_response = requests.get(active_agents_endpoint, headers=headers, verify=False)
    active_agents_data = active_agents_response.json().get('data', {}).get('affected_items', [])
    return render_template('active_agents.html', active_agents=active_agents_data)


@app.route('/disconnected-agents')
def disconnected_agents():
    jwt_token = session.get('jwt_token')
    if not jwt_token:
        flash('Please log in to view disconnected agents')
        return redirect(url_for('login'))
    headers = {'Authorization': f'Bearer {jwt_token}'}
    # Fetching all disconnected agents data
    disconnected_agents_endpoint = f"{wazuh_api_url}/agents?status=disconnected&select=name,ip,os.name,status"
    disconnected_agents_response = requests.get(disconnected_agents_endpoint, headers=headers, verify=False)
    disconnected_agents_data = disconnected_agents_response.json().get('data', {}).get('affected_items', [])
    return render_template('disconnected_agents.html', disconnected_agents=disconnected_agents_data)

@app.route('/total-agents')
def total_agents():
    jwt_token = session.get('jwt_token')
    if not jwt_token:
        flash('Please log in to view total agents')
        return redirect(url_for('login'))
    headers = {'Authorization': f'Bearer {jwt_token}'}

    # Fetching all agents' data
    total_agents_endpoint = f"{wazuh_api_url}/agents?select=name,ip,os.name,status"
    total_agents_response = requests.get(total_agents_endpoint, headers=headers, verify=False)
    
    # Checking if the request was successful
    if total_agents_response.status_code == 200:
        total_agents_data = total_agents_response.json().get('data', {}).get('affected_items', [])
    else:
        flash('Failed to retrieve agents data')
        total_agents_data = []
    return render_template('total_agents.html', total_agents=total_agents_data)



# New Feature: Handle Forbidden Access (403 Error)
@app.errorhandler(403)
def forbidden_page(e):
    """
    Render a custom template when a 403 forbidden error occurs.
    """
    with open('app.log', 'r') as f:
        log_lines = f.readlines()
    # Get the last 4 log lines
    recent_logs = log_lines[-4:]
    return render_template('403_forbidden.html', logs=recent_logs)


@app.errorhandler(404)
def page_not_found(e):
    """
    Render a custom template when a 404 not found error occurs.
    """
    with open('app.log', 'r') as f:
        log_lines = f.readlines()
    # Get the last 4 log lines
    recent_logs = log_lines[-4:]
    return render_template('404_not_found.html', logs=recent_logs)



@app.route('/favicon.ico')
def favicon():
    return url_for('static', filename='favicon.ico')



@app.route('/logout')
def logout():
    """Clear user session and logout."""
    session.pop('jwt_token', None)
    session.pop('token_expires', None)
    session.pop('username', None)  # If used for token refresh, consider keeping it based on your logic
    session.pop('password', None)  # Highly recommend not storing password in session for security reasons
    flash('You have been logged out')
    return redirect(url_for('login'))


# Setup logging
if not app.debug:
    handler = RotatingFileHandler('app.log', maxBytes=10000, backupCount=1)
    handler.setLevel(logging.INFO)
    app.logger.addHandler(handler)

if __name__ == '__main__':
    app.run(debug=False, ssl_context='adhoc')  # Consider removing ssl_context='adhoc' in production





