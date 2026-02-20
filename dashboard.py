from flask import Flask, request, redirect, url_for, session, jsonify
import json
import os

app = Flask(__name__)
app.secret_key = 'super_secret_key'  # Change this to a secure key in production

DATA_FILE = 'blocked.json'
ADMIN_KEYS = ['admin_key1', 'admin_key2']  # Define your admin keys here

# Load blocked data from file
if os.path.exists(DATA_FILE):
    with open(DATA_FILE, 'r') as f:
        blocked = json.load(f)
else:
    blocked = {}  # org: list of websites

def save_data():
    with open(DATA_FILE, 'w') as f:
        json.dump(blocked, f)

@app.route('/', methods=['GET', 'POST'])
def login():
    if request.method == 'POST':
        key = request.form.get('key')
        if key in ADMIN_KEYS:
            session['authenticated'] = True
            return redirect(url_for('dashboard'))
        else:
            return 'Invalid key', 401
    return '''
        <form method="post">
            <label>Admin Key: <input type="password" name="key"></label>
            <button type="submit">Login</button>
        </form>
    '''

@app.route('/dashboard', methods=['GET', 'POST'])
def dashboard():
    if not session.get('authenticated'):
        return redirect(url_for('login'))
    
    if request.method == 'POST':
        org = request.form.get('org')
        website = request.form.get('website')
        if org and website:
            if org not in blocked:
                blocked[org] = []
            if website not in blocked[org]:
                blocked[org].append(website)
            save_data()
    
    # Display current blocked sites
    org_list = ''
    for org, sites in blocked.items():
        org_list += f'<h3>{org}</h3><ul>' + ''.join(f'<li>{site}</li>' for site in sites) + '</ul>'
    
    return f'''
        <h1>Admin Dashboard</h1>
        <form method="post">
            <label>Organization: <input type="text" name="org" required></label><br>
            <label>Website to Block: <input type="text" name="website" required></label><br>
            <button type="submit">Add</button>
        </form>
        <h2>Current Blocked Sites</h2>
        {org_list}
    '''

@app.route('/api/blocked/<org>')
def get_blocked(org):
    return jsonify(blocked.get(org, []))

if __name__ == '__main__':
    app.run(debug=True)