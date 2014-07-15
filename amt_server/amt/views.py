from django.shortcuts import render
from django.views.decorators.clickjacking import xframe_options_exempt
from django.views.decorators.http import require_GET, require_POST
from connection import create_hit, AMT_NO_ASSIGNMENT_ID
from django.http import HttpResponse
from datetime import datetime
from models import *
import json
import os

# A separate view for generating HITs
# Currently, this is a only test view for creating HITs with sample tweets
def hits_gen(request):
    
    # Read from file
    input_file_name = os.path.join(os.path.dirname(__file__), 'tweets.json')
    input_file = file(input_file_name, 'r')
    
    lines = input_file.readlines()
    json_array = lines[0]
    
    json_array = json.loads(json_array)
    
    # Create a sample HIT
    for i in range(5) :
        
        # Create a new hit and get its HIT Id
        additional_options = {}
        current_hit_id = create_hit(additional_options)
            
        # Save this hit to the database
        current_hit = HIT(type = 'sa', content = json_array[i], create_time = datetime.now(), HITId = current_hit_id)
        current_hit.save()
        
    return HttpResponse('ok')

# Create your views here.
# We'll need (at a minimum) views for showing HITs to workers and
# accepting their responses

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
    current_hit = HIT.objects.filter(HITId = hit_id)[0]
    tweet_content = current_hit.content
    
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
