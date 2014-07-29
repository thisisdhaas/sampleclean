from django.shortcuts import render
from django.views.decorators.clickjacking import xframe_options_exempt
from django.views.decorators.csrf import csrf_exempt
from django.views.decorators.http import require_GET, require_POST
from connection import create_hit, AMT_NO_ASSIGNMENT_ID
from django.http import HttpResponse
from django.conf import settings
from datetime import datetime
from models import *
import json
import os

# Store a group into the database
def store_group(_group_id, _HIT_finished, _callback_url):

    current_group = Group(group_id = _group_id,
                          HIT_finished = _HIT_finished,
                          callback_url = _callback_url)
    current_group.save()
    
# Store a hit into the database
def store_hit(_type, _content, _create_time, _HITId, _group, _num_assignment, _group_number):

    current_hit = HIT(type = _type,
                      content = _content,
                      create_time = _create_time,
                      HITId = _HITId,
                      group = _group,
                      num_assignment = _num_assignment,
                      group_number = _group_number)
    current_hit.save()

# Store the information of a worker into the database
def store_worker(_worker_id):

    current_worker = Worker(worker_id = _worker_id)
    current_worker.save()

# Store the information of a response
def store_response(_hit, _worker, _content, _assignment_id):
    
    current_response = Response(hit = _hit,
                                worker = _worker,
                                content = _content,
                                assignment_id = _assignment_id)
    current_response.save()
    
# Store the information of an acceptance
def store_request(request):

    # Extract the POST, GET and META parameters
    request_dict = {}
    
    for key, value in request.GET.iteritems():
        request_dict[key] = value
    
    for key, value in request.POST.iteritems():
        request_dict[key] = value
      
    current_request = Request(path = request.get_full_path(),
                              post_json = json.dumps(request_dict),
                              recv_time = datetime.now())
    current_request.save()
    
# Check the format of a request
def check_format(json_dict):

    try :
        json_dict = json.loads(json_dict)
        if not 'type' in json_dict :
            return False
        if not 'group_id' in json_dict :
            return False
        if not 'callback_url' in json_dict :
            return False
        if not 'content' in json_dict :
            return False
    except :
        return False
    
    return True

# Deal with unicode
def convert(input):
    if isinstance(input, dict):
        return {convert(key): convert(value) for key, value in input.iteritems()}
    elif isinstance(input, list):
        return [convert(element) for element in input]
    elif isinstance(input, unicode):
        return input.encode('utf-8')
    else:
        return input

# Make a majority vote answer for a HIT
def make_mv_answer(current_hit) :

    answers = []

    for response in current_hit.response_set.all() :
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
        

# Submit the answers to the callback URL
def submit_callback_answer(current_group) :

    url = current_group.callback_url
    json_answer = {'group_id' : current_group.group_id}
    json_answer['answer'] = []

    for i in range(current_group.HIT_finished):
        
        HIT = current_group.hit_set.filter(group_number = i)[0]
        current_mv_answer = HIT.mv_answer.split(',')
        json_answer['answer'].append(current_mv_answer)
    
    print json.dumps(json_answer)
        
    
# A separate view for generating HITs
@require_GET
def hits_gen(request):
    '''
        See README.md        
    '''
    # Response dictionaries
    correct_response = json.dumps({'status' : 'ok'})
    wrong_response = json.dumps({'status' : 'wrong'})
    
    # Parse information contained in the URL
    json_dict = request.GET.get('data')
    # Check if it has correct format
    if (not check_format(json_dict)) :
        return HttpResponse(wrong_response)

    # Loads the JSON string to a dictionary
    json_dict = json.loads(json_dict)
    
    # Update num_assignment
    if not 'num_assignment' in json_dict :
        json_dict['num_assignment'] = 3

    # Retrieve specific data    
    hit_type = json_dict['type']
    num_assignment = json_dict['num_assignment']
    group_id = json_dict['group_id']
    callback_url = json_dict['callback_url']
    content = json_dict['content']
    if (len(content) == 0) :
        return HttpResponse(wrong_response)

    # Store the current group into the database
    store_group(group_id, 0, callback_url);
    current_group = Group.objects.filter(group_id = group_id)[0]

    for i in range(len(content)) :
        
        # Using boto API to create an AMT HIT
        additional_options = {'num_responses' : num_assignment}
        current_hit_id = create_hit(additional_options)

        # Sentiment Analysis
        if (hit_type == 'sa') :

            current_content = str(convert(content[i])).replace("\'", "\"")
            # Check format
            try :
                json.loads(current_content)
            except :
                return HttpResponse(wrong_response)

        # Entity Resolution
        elif (hit_type == 'er'):

            current_content = str(convert(content[i])).replace("\'", "\"")
            # Check format    
            try :                
                json.loads(current_content)
            except :
                return HttpResponse(wrong_response)
                
        # Save this HIT to the database
        store_hit(hit_type, current_content, datetime.now(), current_hit_id, current_group, num_assignment, i)
                
    return HttpResponse(correct_response)


# we need this view to load in AMT's iframe, so disable Django's built-in
# clickjacking protection.
@xframe_options_exempt
@require_GET
def get_assignment(request):

    # parse information from AMT in the URL
    hit_id = request.GET.get('hitId')
    worker_id = request.GET.get('workerId')
    submit_url = request.GET.get('turkSubmitTo')
    assignment_id = request.GET.get('assignmentId')

    # this request is for a preview of the task: we shouldn't allow submission.
    if assignment_id == AMT_NO_ASSIGNMENT_ID:
        assignment_id = None
        allow_submission = False
    else:
        allow_submission = True

    # Retrieve the tweet based on hit_id from the database
    
    current_hit = HIT.objects.filter(HITId = hit_id)
    if len(current_hit) != 0:
        current_hit = current_hit[0]
        content = current_hit.content
    else:
        current_hit = None
        content = '["No task available at this moment!"]'

    content = json.loads(content)
    
    # Save the information of this worker
    if worker_id != None:
        store_worker(worker_id)
        current_worker = Worker.objects.filter(worker_id = worker_id)[0]
    else:
        current_worker = None
    
    # Save the information of this request(only when it is an acceptance)
    if assignment_id != None:
        store_request(request)
    
    # Build relationships between workers and HITs (when a worker accepts this hit)
    if current_worker != None and assignment_id != None and current_hit != None:
        current_worker.hits.add(current_hit)

    # Check the number of HITs this worker has accepted. A threshold needs to be tuned.
    if current_worker != None:
        print current_worker.hits.count()
    else:
        print 0

    # Render the template
    if (current_hit != None and current_hit.type == 'sa') :
        context = {'assignment_id' : assignment_id,
                   'tweet_content' : content,
                   'allow_submission' : allow_submission
                    }
        return render(request, 'amt/sa.html', context)
    else :
        context = {'assignment_id' : assignment_id,
                   'er_content' : content,
                   'allow_submission' : allow_submission}
        return render(request, 'amt/er.html', context)


# When workers submit assignments, we should send data to this view via AJAX
# before submitting to AMT.
@require_POST
@csrf_exempt
def post_response(request):

    # Extract data from the request 
    answers = request.POST['answers']
    hit_id = request.POST['HITId']
    worker_id = request.POST['workerId']
    assignment_id = request.POST['assignmentId']

    # Check if this is a duplicate response
    if Response.objects.filter(assignment_id = assignment_id).count() > 0 :
        return HttpResponse('Duplicate!')

    print answers

    # Retrieve the corresponding HIT from the database based on the HITId
    current_hit = HIT.objects.filter(HITId = hit_id)[0]

    # Retrieve the worker from the database based on the workerId
    current_worker = Worker.objects.filter(worker_id = worker_id)[0]

    # Store this response into the database
    store_response(current_hit, current_worker, answers, assignment_id)

    # Check if this HIT has been finished 
    if current_hit.response_set.count() == current_hit.num_assignment  :
        make_mv_answer(current_hit)
        current_hit.group.HIT_finished += 1
        current_hit.group.save()
        
    # Check if the group to which this HIT belongs has been finished
    if current_hit.group.HIT_finished == current_hit.group.hit_set.count() :
        submit_callback_answer(current_hit.group)

    return HttpResponse('ok') # AJAX call succeded.
