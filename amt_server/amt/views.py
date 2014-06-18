from django.shortcuts import render

# Create your views here.

# We'll need views for showing HITs to workers, for accepting responses, and for 
# publishing finished results

def display_task(request, task_id):
    # render a template!
    # Eventually, we probably want a line that looks like:
    # task = get_object_or_404(HIT, pk=task_id)
    return render(request, 'amt/task.html', {'task_id': task_id})
