import requests
import base64
import sys
import os
import urllib3
from requests.packages.urllib3.exceptions import InsecureRequestWarning
from urllib.parse import urlparse
import readline
import time
import re
import getpass

# Disable SSL warnings
urllib3.disable_warnings(InsecureRequestWarning)

def normalize_url(url):
    # Remove trailing dots and spaces
    url = url.strip().rstrip('.')
    # Ensure URL has scheme
    if not url.startswith(('http://', 'https://')):
        url = 'http://' + url
    return url

def encode_command(command):
    return base64.b64encode(command.encode()).decode()

def make_request(url, verify_ssl=True, max_retries=3):
    url = normalize_url(url)
    for attempt in range(max_retries):
        try:
            response = requests.get(
                url, 
                verify=verify_ssl, 
                timeout=30,
                headers={'User-Agent': 'Mozilla/5.0'}
            )
            return response
        except requests.exceptions.SSLError:
            print("SSL Error: If you trust the server, you can disable SSL verification with --insecure")
            return None
        except requests.exceptions.ConnectionError:
            if attempt < max_retries - 1:
                print(f"Connection error, retrying... (Attempt {attempt + 1}/{max_retries})")
                continue
            print("Connection error: Could not connect to the server")
            return None
        except requests.exceptions.Timeout:
            if attempt < max_retries - 1:
                print(f"Timeout, retrying... (Attempt {attempt + 1}/{max_retries})")
                continue
            print("Connection timeout: Server took too long to respond")
            return None
        except requests.exceptions.RequestException as e:
            print(f"Request Error: {str(e)}")
            return None
    return None

def clean_output(text):
    # Remove <pre> tags and their content
    text = re.sub(r'<pre>|</pre>', '', text)
    # Remove any leading/trailing whitespace
    return text.strip()

def execute_command(server_url, command, verify_ssl=True):
    # Encode the command
    encoded_cmd = encode_command(command)
    
    # Create the full command with base64 decode and bash
    full_cmd = f"echo {encoded_cmd} | base64 -d | bash"
    
    # Send request
    response = make_request(f"{server_url}/cmd?c={full_cmd}", verify_ssl)
    
    if response and response.status_code == 200:
        return clean_output(response.text)
    return None

class ShellSession:
    def __init__(self, server_url, verify_ssl=True):
        self.server_url = server_url
        self.verify_ssl = verify_ssl
        self.is_root = False
        self.root_password = None
    
    def execute(self, command):
        if self.is_root:
            # Execute command as root using su -c
            root_cmd = f"echo '{self.root_password}' | su -c '{command}'"
            return execute_command(self.server_url, root_cmd, self.verify_ssl)
        return execute_command(self.server_url, command, self.verify_ssl)
    
    def become_root(self, password, target_user="root"):
        self.root_password = password
        # Test root access with explicit target user
        test_cmd = f"echo '{password}' | su - {target_user} -c 'whoami'"
        result = execute_command(self.server_url, test_cmd, self.verify_ssl)
        if result and "root" in result:
            self.is_root = True
            return True
        return False

def handle_su_command(command):
    # Parse su command
    parts = command.split()
    if len(parts) == 1:  # just 'su'
        return "root", None
    elif len(parts) == 2 and parts[1] == "-":  # 'su -'
        return "root", None
    elif len(parts) == 3 and parts[1] == "-":  # 'su - root'
        return parts[2], None
    return None, "Invalid su command format"

def interactive_shell(server_url, verify_ssl=True):
    print(f"Connecting to {server_url}...")
    
    # Create shell session
    session = ShellSession(server_url, verify_ssl)
    
    # Test connection
    test_response = session.execute("echo 'Connection test'")
    if not test_response:
        print("Failed to connect to server")
        return
    
    print("Connected successfully!")
    print("Type 'exit' to quit")
    print("Type 'su' or 'su - root' to switch to root")
    print("-" * 50)
    
    # Command history
    history = []
    
    while True:
        try:
            # Get command from user
            command = input("shell> ").strip()
            
            # Handle exit command
            if command.lower() in ['exit', 'quit']:
                print("Goodbye!")
                break
            
            # Skip empty commands
            if not command:
                continue
            
            # Handle su command
            if command.startswith('su'):
                target_user, error = handle_su_command(command)
                if error:
                    print(error)
                    continue
                    
                password = getpass.getpass("Password: ")
                if session.become_root(password, target_user):
                    print("Successfully switched to root")
                else:
                    print("Failed to switch to root")
                continue
            
            # Add to history
            history.append(command)
            
            # Execute command
            start_time = time.time()
            result = session.execute(command)
            end_time = time.time()
            
            if result:
                print(result)
                print(f"\nCommand executed in {end_time - start_time:.2f} seconds")
            else:
                print("Command execution failed")
            
            print("-" * 50)
            
        except KeyboardInterrupt:
            print("\nUse 'exit' to quit")
        except Exception as e:
            print(f"Error: {str(e)}")

if __name__ == "__main__":
    import argparse
    
    parser = argparse.ArgumentParser(description='Interactive shell client using base64 encoded commands')
    parser.add_argument('server_url', help='Server URL (e.g., https://example.com)')
    parser.add_argument('--insecure', action='store_true', help='Disable SSL verification')
    
    args = parser.parse_args()
    
    interactive_shell(args.server_url, not args.insecure) 