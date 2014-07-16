from django.db import models

# Create your models here.

# We'll need, at a minimum:
#
# a model for Workers
# a model for worker Responses
# a model for HITs


# Model for HITs
class HIT(models.Model):

    # The type of the task, Sentiment Analysis, Deduplication, etc
    type = models.CharField(max_length = 64)  
    
    # The content of the tweet
    content = models.TextField()
    
    # Creating time
    create_time = models.DateTimeField() 
    
    # HITId 
    HITId = models.TextField(primary_key = True)
    
    def __unicode__(self):
        return self.type + " : " + self.content

# Model for workers
class Worker(models.Model):
    
    # The id of the worker
    worker_id = models.TextField(primary_key = True)
    
    # The HITs that accepted by this worker, a many-to-many relationship
    hits = models.ManyToManyField(HIT)
    
    def __unicode__(self):
        return self.worker_id

# Model for responses
class Response(models.Model):
    
    # The HIT that is responsed to, a many-to-one relationship
    hit = models.ForeignKey(HIT)
    
    # The worker that gave the response, a many-to-one relationship
    worker = models.ForeignKey(Worker)
    
    # The content of the response (currently only a text, e.g, 'Positive' or 'Negative' for sentiment analysis)
    content = models.TextField()
    
    def __unicode__(self):
        return self.hit + " " + self.worker


# Model for storing requests 
class Request(models.Model):
    
    # Path of this request
    path = models.CharField(max_length = 1024)
    
    # Json array of this request
    post_json = models.TextField()
    
    # Receiving time
    recv_time = models.DateTimeField()
    
    def __unicode__(self):
        return self.post_json 
