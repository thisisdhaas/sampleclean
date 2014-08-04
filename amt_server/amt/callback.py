from models import *
import json


# Make a majority vote answer for a HIT
def make_mv_answer(current_hit) :

    answers = []

    for response in current_hit.response_set.all() :
        current_content = response.content.split(",")
        answers.append(current_content)
        
    if (len(answers) == 0) :
        current_hit.mv_answer = ''
    else :

        mv_answer = []
        # For each task
        for i in range(len(answers[0])) :
            
            count = {}
            # For each assignment
            for j in range(len(answers)) :
                if answers[j][i] in count :
                    count[answers[j][i]] += 1
                else :
                    count[answers[j][i]] = 1

            # Find the mode
            current_answer = ''
            max_count = -1
            for key, value in count.iteritems() :
                if (value > max_count) :
                    max_count = value
                    current_answer = key
            mv_answer.append(current_answer)

        current_hit.mv_answer = ','.join(mv_answer)
    current_hit.save()
        

# Submit the answers to the callback URL
def submit_callback_answer(current_hit) :

    url = current_hit.group.callback_url
    
    json_answer = {'group_id' : current_hit.group.group_id,
                   'identifier' : current_hit.identifier}

    current_mv_answer = current_hit.mv_answer.split(',')
    json_answer['answer'] = current_mv_answer

    print json_answer
    print json.dumps(json_answer)
