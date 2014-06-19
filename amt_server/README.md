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

* Make sure it works: head to `https://localhost:8000/assignments/` and you should
  see a 'Hello World' message. Then log into the AMT management interface
  (https://requestersandbox.mturk.com/mturk/manageHITs) and verify that you have
  just created an example HIT. Then log in as a worker
  (https://workersandbox.mturk.com/mturk/searchbar) and verify that you can
  accept the HIT and that it displays correctly in AMT's iframe.
