import json


# Check the format of a request
def check_format(json_dict):

    try :
        json_dict = json.loads(json_dict)
        if not 'type' in json_dict :
            return False
        if not 'group_id' in json_dict :
            return False
        if not 'callback_url' in json_dict :
            return False
        if not 'content' in json_dict :
            return False

        content = json_dict['content']
        if (len(content) == 0) :
            return False
        
        for i in range(len(content)) :

            # Check if it is a dictionary
            if not isinstance(content[i], dict) :
                return False
            
            # Check if it contains only a key
            if (len(content[i].keys()) != 1) :
                return False

            current_content = content[i][content[i].keys()[0]]
            current_content = str(convert(current_content)).replace("\'", "\"")
            json.loads(current_content)
        
    except :
        return False
    
    return True

# Deal with unicode
def convert(input):
    if isinstance(input, dict):
        return {convert(key): convert(value) for key, value in input.iteritems()}
    elif isinstance(input, list):
        return [convert(element) for element in input]
    elif isinstance(input, unicode):
        return input.encode('utf-8')
    else:
        return input
