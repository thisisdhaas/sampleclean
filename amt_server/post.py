import httplib


params = {'data' : '{"type":"sa","num_assignment":1,"group_id":"Dan","callback_url":"google.com","content":[{"hit1":["aa","bb"]}]}'}
headers = {'Content-Type' : 'application/x-www-form-urlencoded'}

conn = httplib.HTTPSConnection('localhost', port = 8000)
conn.request('POST', '/amt/hitsgen/', params, headers)

