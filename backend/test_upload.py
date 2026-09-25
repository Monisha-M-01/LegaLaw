import requests

url = "http://127.0.0.1:8000/api/upload"
files = {'file': open('test.docx', 'rb')}
data = {'target_language': 'en', 'session_id': 'test-session'}

print("Uploading test.docx...")
response = requests.post(url, files=files, data=data)

if response.status_code == 200:
    print("Upload successful!")
    print(response.json())
else:
    print("Upload failed!")
    print(f"Status code: {response.status_code}")
    print(response.text)
