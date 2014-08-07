from django.shortcuts import render
from django.views.decorators.clickjacking import xframe_options_exempt
from django.views.decorators.csrf import csrf_exempt
from django.views.decorators.http import require_GET, require_POST
from connection import create_hit, disable_hit, AMT_NO_ASSIGNMENT_ID
from django.http import HttpResponse
from django.conf import settings
from datetime import datetime
import pytz
import json
import os


from models import *
from callback import *
from blend import *
from store import *

        
# A separate view for generating HITs
@require_POST
@csrf_exempt
def hits_gen(request):
    '''
        See README.md        
    '''
    # Response dictionaries
    correct_response = {'status' : 'ok', 'map' : {}}
    wrong_response = {'status' : 'wrong'}
    
    # Parse information contained in the URL
    json_dict = request.POST.get('data')
    # Check if it has correct format
    if (not check_format(json_dict)) :
        return HttpResponse(json.dumps(wrong_response))

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

    # Store the current group into the database
    store_group(group_id, 0, callback_url);
    current_group = Group.objects.filter(group_id = group_id)[0]

    for i in range(len(content)) :
                
        # Using boto API to create an AMT HIT
        additional_options = {'num_responses' : num_assignment}
        current_hit_id = create_hit(additional_options)

        # identifier
        identifier = content[i].keys()[0]
        
        # update response
        correct_response['map'][identifier] = current_hit_id
        
        # Deal with delimiters
        current_content = str(convert(content[i][identifier])).replace("\'", "\"")
                
        # Save this HIT to the database
        store_hit(hit_type,
                  current_content,
                  pytz.utc.localize(datetime.now()),
                  current_hit_id,
                  current_group,
                  num_assignment,
                  identifier)
                
    return HttpResponse(json.dumps(correct_response))

def hits_del(request) :

    hit_set = HIT.objects.all()
    for hit in hit_set :
        disable_hit(hit.HITId)
    HIT.objects.all().delete()
    return HttpResponse('ok')


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

    # Retrieve the corresponding HIT from the database based on the HITId
    current_hit = HIT.objects.filter(HITId = hit_id)[0]

    # Retrieve the worker from the database based on the workerId
    current_worker = Worker.objects.filter(worker_id = worker_id)[0]

    # Store this response into the database
    store_response(current_hit, current_worker, answers, assignment_id)

    # Check if this HIT has been finished 
    if current_hit.response_set.count() == current_hit.num_assignment:

        make_em_answer(current_hit)

        current_hit.group.HIT_finished += 1
        current_hit.group.save()

        submit_callback_answer(current_hit)
        
    #    Check if the group to which this HIT belongs has been finished
    #    if current_hit.group.HIT_finished == current_hit.group.hit_set.count() :
    #        submit_callback_answer(current_hit.group)

    return HttpResponse('ok') # AJAX call succeded.
