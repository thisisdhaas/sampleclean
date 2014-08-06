import httplib
import socket
import ssl
import urllib
import urllib2

# custom HTTPS opener, django-sslserver supports SSLv3 only
class HTTPSConnectionV3(httplib.HTTPSConnection):
    def __init__(self, *args, **kwargs):
        httplib.HTTPSConnection.__init__(self, *args, **kwargs)

    def connect(self):
        sock = socket.create_connection((self.host, self.port), self.timeout)
        if self._tunnel_host:
            self.sock = sock
            self._tunnel()
        try:
            self.sock = ssl.wrap_socket(sock, self.key_file, self.cert_file, ssl_version=ssl.PROTOCOL_SSLv3)
        except ssl.SSLError, e:
            print("Trying SSLv3.")
            self.sock = ssl.wrap_socket(sock, self.key_file, self.cert_file, ssl_version=ssl.PROTOCOL_SSLv23)

class HTTPSHandlerV3(urllib2.HTTPSHandler):
    def https_open(self, req):
        return self.do_open(HTTPSConnectionV3, req)

# install custom opener
urllib2.install_opener(urllib2.build_opener(HTTPSHandlerV3()))

# make request
params = {'data' : '{"type":"sa","num_assignment":1,"group_id":"Dan","callback_url":"google.com","content":[{"hit1":["aa","bb"]}]}'}
response = urllib2.urlopen('https://127.0.0.1:8000/amt/hitsgen/',
                    urllib.urlencode(params))
print response.read()

