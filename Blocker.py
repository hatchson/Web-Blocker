import tkinter as tk
from tkinter import messagebox, ttk
import json
import os
import sys
import requests
import winreg
import threading
from http.server import HTTPServer, BaseHTTPRequestHandler

CONFIG_FILE = 'config.json'
HOSTS_PATH = r'C:\Windows\System32\drivers\etc\hosts'

class RedirectHandler(BaseHTTPRequestHandler):
    def __init__(self, *args, org=None, **kwargs):
        self.org = org
        super().__init__(*args, **kwargs)

    def do_GET(self):
        host = self.headers.get('Host')
        print("Working")
        if host:
            location = f'https://hatchson.github.io/webblocker/uhoh.html?website={host}&organization={self.org}'
            self.send_response(302)
            self.send_header('Location', location)
            self.end_headers()

    def do_HEAD(self):
        self.do_GET()

    def log_message(self, format, *args):
        return  # Suppress logging for background run

def update_hosts(blocked_sites):
    # Remove existing webblocker block
    if os.path.exists(HOSTS_PATH):
        with open(HOSTS_PATH, 'r') as f:
            lines = f.readlines()
        
        new_lines = []
        in_block = False
        for line in lines:
            stripped = line.strip()
            if stripped == '# webblocker start':
                in_block = True
                continue
            if stripped == '# webblocker end':
                in_block = False
                continue
            if not in_block:
                new_lines.append(line)
        
        with open(HOSTS_PATH, 'w') as f:
            f.writelines(new_lines)
    
    # Add new block
    with open(HOSTS_PATH, 'a') as f:
        f.write('\n# webblocker start\n')
        for site in blocked_sites:
            f.write(f'127.0.0.1 {site}\n')
        f.write('# webblocker end\n')

def add_to_startup():
    script_path = os.path.abspath(__file__)
    key = winreg.OpenKey(winreg.HKEY_CURRENT_USER, r'Software\Microsoft\Windows\CurrentVersion\Run', 0, winreg.KEY_SET_VALUE)
    winreg.SetValueEx(key, 'WebBlocker', 0, winreg.REG_SZ, f'pythonw "{script_path}"')
    winreg.CloseKey(key)

def run_server(org):
    handler = lambda *args, **kwargs: RedirectHandler(*args, org=org, **kwargs)
    server = HTTPServer(('', 80), handler)
    server.serve_forever()

def main():
    if os.path.exists(CONFIG_FILE):
        # Load config and run silently
        with open(CONFIG_FILE, 'r') as f:
            config = json.load(f)
        dashboard_url = config['dashboard']
        org = config['org']
    else:
        # Show config GUI
        root = tk.Tk()
        root.title('Web Blocker Config')
        
        tk.Label(root, text='Dashboard URL:').grid(row=0, column=0)
        url_entry = tk.Entry(root)
        url_entry.grid(row=0, column=1)
        
        tk.Label(root, text='Organization:').grid(row=1, column=0)
        org_entry = tk.Entry(root)
        org_entry.grid(row=1, column=1)
        
        startup_var = tk.BooleanVar(value=True)
        tk.Checkbutton(root, text='Add to Windows Startup', variable=startup_var).grid(row=2, columnspan=2)
        
        def save():
            dashboard = url_entry.get().rstrip('/')
            org = org_entry.get()
            if not dashboard or not org:
                messagebox.showerror('Error', 'All fields required')
                return
            with open(CONFIG_FILE, 'w') as f:
                json.dump({'dashboard': dashboard, 'org': org}, f)
            if startup_var.get():
                add_to_startup()
            root.destroy()
        
        tk.Button(root, text='Save', command=save).grid(row=3, columnspan=2)
        root.mainloop()
        
        # Reload config after save
        with open(CONFIG_FILE, 'r') as f:
            config = json.load(f)
        dashboard_url = config['dashboard']
        org = config['org']
    
    # Fetch blocked sites
    try:
        response = requests.get(f'{dashboard_url}/api/blocked/{org}')
        blocked_sites = response.json()
    except Exception as e:
        print(f'Error fetching blocked sites: {e}')  # For debugging; won't show in pythonw
        sys.exit(1)
    
    # Update hosts
    update_hosts(blocked_sites)
    
    # Run server in background
    server_thread = threading.Thread(target=run_server, args=(org,), daemon=True)
    server_thread.start()
    
    # Keep the script running (server is in thread)
    server_thread.join()

if __name__ == '__main__':
    main()