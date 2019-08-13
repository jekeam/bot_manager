import requests
from retry_requests import requests_retry_session, requests_retry_session_post

# user13021:vj0n64@45.85.64.234:8786
resp = requests_retry_session_post(url='https://httpstat.us/200?sleep=5000', timeout=1)
print(resp.elapsed.total_seconds())