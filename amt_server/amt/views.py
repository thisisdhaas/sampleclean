from django.shortcuts import render
from django.views.decorators.clickjacking import xframe_options_exempt
from django.views.decorators.http import require_GET, require_POST

from connection import create_hit, AMT_NO_ASSIGNMENT_ID

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

    # create a dummy hit (example usage)
    if not hit_id:
        additional_options = {}
        create_hit(additional_options)

    # render a template for the assignment
    # TODO: make this template real!
    return render(request, 'amt/assignment.html',
                  {'assignment_id': assignment_id})

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
