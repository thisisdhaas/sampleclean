from djcelery import celery

@celery.task
def add(x, y) :
    return x + y

