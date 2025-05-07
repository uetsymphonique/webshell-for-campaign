import requests
import base64
import sys
import os
import urllib3
from requests.packages.urllib3.exceptions import InsecureRequestWarning
from urllib.parse import urlparse

# Disable SSL warnings
urllib3.disable_warnings(InsecureRequestWarning)

def normalize_url(url):
    # Remove trailing dots and spaces
    url = url.strip().rstrip('.')
    # Ensure URL has scheme
    if not url.startswith(('http://', 'https://')):
        url = 'http://' + url
    return url

def make_request(url, method='post', json=None, headers=None, verify_ssl=True, max_retries=3):
    url = normalize_url(url)
    for attempt in range(max_retries):
        try:
            response = requests.request(
                method,
                url, 
                json=json,
                headers=headers,
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

def upload_file(file_path, server_url, verify_ssl=True):
    # Read file and encode to base64
    with open(file_path, 'rb') as file:
        file_content = base64.b64encode(file.read()).decode('utf-8')
    
    # Get filename from path
    filename = os.path.basename(file_path)
    
    # Prepare JSON payload
    payload = {
        "filename": filename,
        "content": file_content
    }
    
    # Send POST request
    url = f"{server_url}/upload/json"
    headers = {
        "Content-Type": "application/json"
    }
    
    print(f"Uploading {filename}...")
    response = make_request(url, method='post', json=payload, headers=headers, verify_ssl=verify_ssl)
    
    if response:
        print(f"Status Code: {response.status_code}")
        print(f"Response: {response.text}")
    else:
        print("Upload failed")

if __name__ == "__main__":
    import argparse
    
    parser = argparse.ArgumentParser(description='Upload file using JSON endpoint')
    parser.add_argument('server_url', help='Server URL (e.g., https://example.com)')
    parser.add_argument('file_path', help='Path to file to upload')
    parser.add_argument('--insecure', action='store_true', help='Disable SSL verification')
    
    args = parser.parse_args()
    
    if not os.path.exists(args.file_path):
        print(f"Error: File {args.file_path} does not exist")
        sys.exit(1)
    
    upload_file(args.file_path, args.server_url, not args.insecure) 