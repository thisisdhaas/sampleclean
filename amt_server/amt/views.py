from django.shortcuts import render
from django.views.decorators.clickjacking import xframe_options_exempt
from django.views.decorators.csrf import csrf_exempt
from django.views.decorators.http import require_GET, require_POST
from connection import create_hit, AMT_NO_ASSIGNMENT_ID
from django.http import HttpResponse
from django.conf import settings
from datetime import datetime
from models import *
import urllib2
import urllib
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

# Store the information of a response
def store_response(_hit, _worker, _content):
    
    current_response = Response(hit = _hit, worker = _worker, content = _content)
    current_response.save()
    
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
@require_GET
def hits_gen(request):
    '''
        This view receives GET parameters and creates corresponding HITs. (Temporarily use GET for debugging)
        GET parameters :
        
	    `type` : The type of this hit;
	    
	    `tweet_content` :

                The tweet content for sentiment analysis, a JSON array of JSON arrays, 
		e.g, the following JSON array :
                    ["[\"Arsenal won the 4th again!\", \"Theo Walcott broke the ligament in his knee last season.\"]", 
                    "[\"Lebron James went back to Cavaliers after he found his teammates in Heats no longer powerful.\"]"]
		will create two HITs in total. The first HIT consists of two tweets and the second one consists of one.
		Be careful on the delimeters :
                    1) No \ before the double quotes that surround the HITs;
                    2) Make sure to put a \ before the double quotes that surround the tweets.
		
	    'group_id' : An interger used to specify the ID of this group of HITs.
	    
	    'callback_url' : The call back url
		
    '''
    # Parse information contained in the URL
    hit_type = request.GET.get('type')
    tweet_content = request.GET.get('tweet_content')
    try :
        tweet_content = json.loads(tweet_content)
    except :
        return HttpResponse('Wrong format. Try again')

    for i in range(len(tweet_content)) :
        
        # Using boto API to create an AMT HIT
        additional_options = {}
        current_hit_id = create_hit(additional_options)

        # Save this HIT to the database
        store_hit(hit_type, tweet_content[i], datetime.now(), current_hit_id)
        
    return HttpResponse('%s HITs have been successfully created.' % len(tweet_content))


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
        tweet_content = current_hit.content
    else:
        current_hit = None
        tweet_content = '[No task available at this moment!]'

    tweet_content = json.loads(tweet_content)
    
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
    context = {'assignment_id' : assignment_id,
               'tweet_content' : tweet_content,
               'allow_submission' : allow_submission
                }
    return render(request, 'amt/assignment.html', context)


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
    
    # Retrieve the corresponding HIT from the database based on the HITId
    current_hit = HIT.objects.filter(HITId = hit_id)[0]

    # Retrieve the worker from the database based on the workerId
    current_worker = Worker.objects.filter(worker_id = worker_id)[0]

    # Store this response into the database
    store_response(current_hit, current_worker, answers)
    
    # TODO: decide if we're done with this HIT, and if so, publish the result.

    return HttpResponse('ok') # AJAX call succeded.
