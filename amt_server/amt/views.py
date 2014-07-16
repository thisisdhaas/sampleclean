from django.shortcuts import render
from django.views.decorators.clickjacking import xframe_options_exempt
from django.views.decorators.http import require_GET, require_POST
from connection import create_hit, AMT_NO_ASSIGNMENT_ID
from django.http import HttpResponse
from datetime import datetime
from models import *
import json
import os

# Store a hit into the database
def store_hit(_type, _content, _create_time, _HITId):

    current_hit = HIT(type = _type, content = _content, create_time = _create_time, HITId = _HITId)
    current_hit.save()

# Store the information of a worker into the database
def store_worker(_worker_id):

    current_worker = Worker(worker_id = _worker_id)
    current_worker.save()

# Store the information of an acceptance
def store_request(request):

    # Extract the POST, GET and META parameters
    request_dict = {}
    
    for key, value in request.GET.iteritems():
        request_dict[key] = value
    
    for key, value in request.POST.iteritems():
        request_dict[key] = value
      
    current_request = Request(path = request.get_full_path(), post_json = json.dumps(request_dict), recv_time = datetime.now())
    current_request.save()
    
    
# A separate view for generating HITs
# Currently, this is a only test view for creating HITs with sample tweets
def hits_gen(request):
    
    # Read from file
    input_file_name = os.path.join(os.path.dirname(__file__), 'tweets.json')
    input_file = file(input_file_name, 'r')
    
    lines = input_file.readlines()
    json_array = lines[0]
    
    json_array = json.loads(json_array)
    
    # Create sample HITs
    for i in range(5) :
        
        # Create a new hit and get its HIT Id
        additional_options = {}
        current_hit_id = create_hit(additional_options)
            
        # Save this hit to the database
        store_hit('sa', json_array[i], datetime.now(), current_hit_id)
        
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

    # Retrieve the tweet based on hit_id from the database
    
    current_hit = HIT.objects.filter(HITId = hit_id)
    if len(current_hit) != 0:
        current_hit = current_hit[0]
        tweet_content = current_hit.content
    else:
        current_hit = None
        tweet_content = 'No task available at this moment!'
    
    # Save the information of this worker
    if worker_id != None:
        store_worker(worker_id)
        current_worker = Worker.objects.filter(worker_id = worker_id)[0]
    else:
        current_worker = None
    
    # Save the information of this request
    if assignment_id != None:
        store_request(request)
    
    # Build relationships between workers and HITs
    if current_worker != None:
        current_worker.hits.add(current_hit)

    # Check the number of HITs this worker has accepted. A threshold needs to be tuned.
    if current_worker != None:
        print current_worker.hits.count()
    else:
        print 0
    
    # Render the template
    context = {'assignment_id': assignment_id, 'tweet_content': tweet_content}
    return render(request, 'amt/assignment.html', context)




# When workers submit assignments, we should send data to this view via AJAX
# before submitting to AMT.
@require_POST
def post_response(request):

    # TODO: extract data from the request--must correspond to the format of the
    # frontend AJAX call.
    data = request.POST.get('important_data_field')

    # TODO: convert to model objects and write to the database

    # TODO: decide if we're done with this HIT, and if so, publish the result.

    return HttpResponse('ok') # AJAX call succeded.
