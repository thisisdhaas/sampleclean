import httplib
import socket
import ssl
import json
import urllib
import urllib2
import operator

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

# Create batches of HIT        
def create_hit() :

    # install custom opener
    urllib2.install_opener(urllib2.build_opener(HTTPSHandlerV3()))

    # Read in the lines
    
    filename = 'product'
    file = open(filename)
    
    hit_ids = {}
    num_assignments = {}
    hit_contents = []
    
    for line in file.readlines():
    
        line = line.strip()
        
        if not line:
            continue
        items =  line.split("\t")
        
        if items[1] in num_assignments :
            num_assignments[items[1]] += 1
        else :
            num_assignments[items[1]] = 1
    
    # Sort the HIts according to the number of assignments
    sort_num_assignments = sorted(num_assignments.iteritems(), key = operator.itemgetter(1))
    
    # Make the hit_content
    for hit_content, num_assignment in sort_num_assignments :
        hit_contents.append(hit_content)
        
    # Partition the HITs into groups & Send hitsgen requests
    current_start = 0
    group_id = 0
    group_size = 10
    print str(len(hit_contents)) + '\n'
    
    while current_start < len(hit_contents) :
        
        group_id += 1
        data = {}
        data['type'] = 'er'
        data['num_assignment'] = num_assignments[hit_contents[current_start]]
        data['group_id'] = 'product' + str(group_id)
        data['callback_url'] = 'google.com'
        data['content'] = []
        
        for j in range(current_start, current_start + group_size) :        
                        
            if j >= len(hit_contents) :                
                break            
            if num_assignments[hit_contents[j]] != num_assignments[hit_contents[current_start]] :                                
                break
            
            cur_identifier = hit_contents[j]
            cur_dict = {cur_identifier : []}
            
            id1 = hit_contents[j].split('_')[0]
            id2 = hit_contents[j].split('_')[1]
            
            # Parse content
            cur_dict[cur_identifier].append({'fields' : ['id'], 'record' : [[id1], [id2]]})
            
            data['content'].append(cur_dict)
        
        current_start += len(data['content'])
        
        # Send request
        params = {'data' : json.dumps(data)}
        
        response = urllib2.urlopen('https://127.0.0.1:8000/amt/hitsgen/',
                                    urllib.urlencode(params))
        
        res = json.loads(response.read())
        if res['status'] != 'ok' :
            print 'Got something wrong!!!!!!!!!!!!!!!!!!!!!!!!!!!!'
        
        for id in res['map'].keys() :
            hit_ids[id] = res['map'][id]
            
        print len(hit_ids.keys())

    file.close()
    return hit_ids


def simulate_worker(hit_ids) :

    filename = 'product'
    file = open(filename)
    
    convert = {'0' : 'diff', '1' : 'same'}
    
    for line in file.readlines() :
    
        items = line.split("\t")
        
        answers = convert[items[2][0]]
        hit_id = hit_ids[items[1]]
        worker_id = items[0]
        assignment_id = worker_id + hit_id
        
        # Post a response
        params = {}
        params['answers'] = answers
        params['HITId'] = hit_id
        params['workerId'] = worker_id
        params['assignmentId'] = assignment_id
        
        response = urllib2.urlopen('https://127.0.0.1:8000/amt/responses/',
                                    urllib.urlencode(params))

if __name__ == "__main__":


    hit_ids = create_hit()
    simulate_worker(hit_ids)

