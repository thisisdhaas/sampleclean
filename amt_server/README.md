AMT Server
==========

This package provides a django server for running data cleaning tasks on AMT

Thing to do to get up and running:

* install postgres, and create a user and a DB for this project.

* install RabbitMQ and start its server:

          $ sudo apt-get install rabbitmq-server
		  
		  $ rabbitmq-server
		  
* create a virtualenv for python dev (I like
  http://virtualenvwrapper.readthedocs.org/en/latest/).

* Install the python requirements:

          $ pip install -r requirements.txt

* Create your own private settings file:

          $ cp amt_server/private_settings.py.default amt_server/private_settings.py

* Sign up for a mechanical turk account, and put the credentials in
  `private_settings.py`. **NEVER CHECK THIS FILE INTO THE REPO.**

* Set up the database:

          $ ./reset_db.sh

* Run the server:

          $ ./run.sh

* Make sure it works: head to `https://localhost:8000/amt/assignments/` and you should
  see a 'Hello World' message. Then log into the AMT management interface
  (https://requestersandbox.mturk.com/mturk/manageHITs) and verify that you have
  just created an example HIT. Then log in as a worker
  (https://workersandbox.mturk.com/mturk/searchbar) and verify that you can
  accept the HIT and that it displays correctly in AMT's iframe.





Web Service APIs
=============
* Create a group of AMT HITs(**POST** method). 

  - There is only a single field, 'data', which maps to a json string:

    - **type** : The type of this hit, e.g, 'sa' for sentiment analysis, 'er' for entity resolution

    -  **content** :
    
      One of the following two things:
      
      1. The tweet content for sentiment analysis, a JSON array of JSON dictionaries, 
          
         e.g, the following JSON array :
          
               [{"hit1" : ["Arsenal won the 4th again!", "Theo Walcott broke the ligament in his knee last season."]}, 
                {"hit2" : ["Lebron James went back to Cavaliers after he found his teammates in Heats no longer powerful."]}]
           
         will create two HITs in total, the identifiers of which are "hit1" and "hit2" respectively. 
		 The first HIT consists of two tweets and the second one consists of one.
         
      2. Records for entity resolution, a JSON array of JSON dictionaries, 
         
             e.g, the following JSON array
			 
                [
					{ "hit1" : 
						[
							 {"fields":["price","location"],"record":[["5","LA"],["6","Berkeley"]]}, 
							 {"fields":["name","age"],"record":[["Jenkinson","22"],["wenbo","21"]]}
						]
					}
                ]
             will create one HIT with two entity resolution tasks.
    
    -  **num_assignment** : The number of assignments for each HIT.
    
    -  **group_id** : A string used to specify the ID of this group of HITs.
    
    -  **callback_url** : The call back url

  - Examples : 
    > data={"type":"sa","num_assignment":1,"group_id":"Dan","callback_url":"google.com","content":[{"hit1":["aa","bb"]}]}

	> data={"type":"er","num_assignment":1,"group_id":"haha","callback_url":"google.com",	
	  "content":[{"hit1":[{"fields":["f1"],"record":[["5"],["6"]]}]},{"hit2":[{"fields":["age","name"],"record":[["22","James"],["21","Wenbo"]]}]}]}
	
  - The direct response for this request is a simple JSON dictionary :
     
    > {"status":"ok", "map":{"identifier1":"HITId1","identifier2":"HITId2"}}
    
    means the format is correct. And the "map" field contains the AMT HITIds for each Hit.
     
    > {"status":"wrong"}
    
    means the format is incorrect, it may be attributed to the wrong format of the content field or omissions of other important fields.
  
  
* Send the results to the callback URL(**POST** method):
  
  When a HIT gets enough votes from the crowd, the EM/MV answer will be sent back to the call back url.
  
  - The results that are sent back consist of a single field, 'data', which maps to a json dictionary :
    - **group_id** : a string specify the group that this HIT belongs to
    
	- **identifier** : the identifier of the HIT
	
    - **answer** : a JSON array which contains the answer for this HIT
