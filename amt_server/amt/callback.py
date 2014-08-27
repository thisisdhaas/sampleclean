from models import *
from em import *
import json
import pytz
from datetime import datetime
import httplib
import socket
import ssl
import json
import urllib
import urllib2
import operator
    
# Make a majority vote answer for a HIT
def make_mv_answer(current_hit) :

    answers = []

    responses = current_hit.response_set.all()
    for response in responses :
        current_content = response.content.split(",")
        answers.append(current_content)
        
    if (len(answers) == 0) :
        current_hit.mv_answer = ''
    else :

        mv_answer = []
        # For each task
        for i in range(len(answers[0])) :
            
            count = {}
            # For each assignment
            for j in range(len(answers)) :
                if answers[j][i] in count :
                    count[answers[j][i]] += 1
                else :
                    count[answers[j][i]] = 1

            # Find the mode
            current_answer = ''
            max_count = -1
            for key, value in count.iteritems() :
                if (value > max_count) :
                    max_count = value
                    current_answer = key
            mv_answer.append(current_answer)

        current_hit.mv_answer = ','.join(mv_answer)
    current_hit.save()

# Make an Expectation Maximization answer for a HIT
def make_em_answer(current_hit) :

    example_to_worker_label = {}
    worker_to_example_label = {}
    label_set=[]
    answers = []
    
    # Make label set
    
    label_set = []
    # Build up initial variables for em
    responses = Response.objects.filter(hit__type = current_hit.type)
    for response in responses :

            answer_list = response.content.split(",")
            for i in range(len(answer_list)) :

                worker_id = response.workerId
                unique_id = response.HITId + str(i)
                current_label = answer_list[i]

                example_to_worker_label.setdefault(unique_id, []).append((worker_id, current_label))
                worker_to_example_label.setdefault(worker_id, []).append((unique_id, current_label))
                
                if current_label not in label_set :
                    label_set.append(current_label)

    # EM algorithm
    iterations = 20

    ans, b, c = EM(example_to_worker_label,worker_to_example_label,label_set).ExpectationMaximization(iterations)

    # Gather answer
    
    num_task = len(current_hit.response_set.all()[0].content.split(","))
    answer_label = []
    
    for i in range(num_task) :
        unique_id = current_hit.HITId + str(i)
        soft_label = ans[unique_id]
        maxv = 0
        cur_label = label_set[0]
        for label, weight in soft_label.items() :
            if weight > maxv :
                maxv = weight
                cur_label = label
        answer_label.append(cur_label)

    current_hit.em_answer = ','.join(answer_label)
    current_hit.save()

# Submit the answers to the callback URL
def submit_callback_answer(current_hit) :

    url = current_hit.group.callback_url
    
    json_answer = {'group_id' : current_hit.group.group_id,
                   'identifier' : current_hit.identifier}

    tmp = current_hit.em_answer.split(',')
    current_em_answer = []

    for str in tmp :
        current_em_answer.append(float(str))

#    current_em_answer = current_hit.em_answer.split(',')
    json_answer['answer'] = current_em_answer
    # Send back data using urllib2
    
    params = {'data' : json.dumps(json_answer)}
    urllib2.urlopen(url, urllib.urlencode(params))
