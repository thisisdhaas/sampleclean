AMT Server
==========

This package provides a django server for running data cleaning tasks on AMT

Thing to do to get up and running:

* install postgres, and create a user and a DB for this project.

* create a virtualenv for python dev (I like
  http://virtualenvwrapper.readthedocs.org/en/latest/).

* Install the python requirements:

          $ pip install -r requirements.txt

* Create your own private settings file:

          $ cp amt_server/private_settings.py.default amt_server/private_settings.py

* Sign up for a mechanical turk account, and put the credentials in
  `private_settings.py`. **NEVER CHECK THIS FILE INTO THE REPO.**

* Set up the database:

          $ python manage.py syncdb

* Run the server:

          $ python manage.py runsslserver

* Make sure it works: head to `https://localhost:8000/amt/assignments/` and you should
  see a 'Hello World' message. Then log into the AMT management interface
  (https://requestersandbox.mturk.com/mturk/manageHITs) and verify that you have
  just created an example HIT. Then log in as a worker
  (https://workersandbox.mturk.com/mturk/searchbar) and verify that you can
  accept the HIT and that it displays correctly in AMT's iframe.





Web Service APIs
=============
* Create a group of AMT HITs(**GET** method). 

  - There is only a single field, 'data', which maps to a json string:

    - **type** : The type of this hit, e.g, 'sa' for sentiment analysis, 'er' for entity resolution

    -  **content** :
    
      One of the following two things:
      
      1. The tweet content for sentiment analysis, a JSON array of JSON arrays, 
          
         e.g, the following JSON array :
          
               [["Arsenal won the 4th again!", "Theo Walcott broke the ligament in his knee last season."], 
               ["Lebron James went back to Cavaliers after he found his teammates in Heats no longer powerful."]]
           
         will create two HITs in total. The first HIT consists of two tweets and the second one consists of one.
         
      2. Records for entity resolution, a JSON array of JSON arrays, 
         
             e.g, the following JSON dictionary
			 
                [
                    [
                         {"fields":["price","location"],"record":[["5","LA"],["6","Berkeley"]]}, 
                         {"fields":["name","age"],"record":[["Jenkinson","22"],["wenbo","21"]]}
                    ]
                ]
             will create one HIT with two entity resolution tasks.
    
    -  **num_assignment** : The number of assignments for each HIT.
    
    -  **group_id** : A string used to specify the ID of this group of HITs.
    
    -  **callback_url** : The call back url

  - An example : 
    > https://localhost:8000/amt/hitsgen/?data={"type":"er","group_id":"haha","callback_url":"google.com","content":[[{"fields":["price","location"],"record":[["5","LA"],["6","Berkeley"]]}]]}
     
  - The direct response for this request is a simple JSON dictionary :
     
    > {"status":"ok"}
    
    means the format is correct;
     
    > {"status":"wrong"}
    
    means the format is incorrect, may be attributed to wrong format of the content field or miss of other important fields.
  
  
* Send the results to the callback URL(**POST** method):

  - The results that are sent back consist of a single field, 'data', which maps to a json string :
    - **group_id** : a string specify a group of HITs the results answer
    
    - **answer** : a JSON array consists of the answers for each HIT, exactly in the same order as the corresponding HITs are in the creating process