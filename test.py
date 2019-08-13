import requests

# user13021:vj0n64@45.85.64.234:8786
resp = requests.get('https://www.fonbet-30099.com/urls.json?123123', proxies={'https':'https://user13021:vj0n64@45.85.64.234:8786'})
print(resp.elapsed.total_seconds())