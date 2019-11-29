# import requests
#
# browser_headers = {
#     "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/63.0.3239.132 Safari/537.36"
# }
#
#
# def req(url):
#     res = requests.post(url=url,
#                         headers=browser_headers,
#                         verify=False,
#                         timeout=5,
#                         proxies=proxies)
#     return res
#
#
# url_test_s = "https://httpbin.org/delay/3"
# url_test = "http://httpbin.org/delay/3"
# url = "http://fonbet.com"
# urls = "https://fonbet.com"
#
# proxies = {}
#
# url = url_test_s
# res = req(url)
# print('запрос на ' + url + ', ответ: ' + str(res.status_code == 200))
#
# url = url_test
# res = req(url)
# print('запрос на ' + url + ', ответ: ' + str(res.status_code == 200))
#
# url = urls
# res = req(url)
# print('запрос на ' + url + ', ответ: ' + str(res.status_code == 200))
#
# url = url
# res = req(url)
# print('запрос на ' + url + ', ответ: ' + str(res.status_code == 200))
