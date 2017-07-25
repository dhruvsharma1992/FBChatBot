import json
import datetime
import time
import os
import dateutil.parser
import logging

logger = logging.getLogger()
logger.setLevel(logging.DEBUG)
import csv
with open('roles.csv', mode='rU') as infile:
    reader = csv.DictReader(infile)
    mydict = dict((rows['Role'],rows) for rows in reader)

# --- Helpers that build all of the responses ---


def elicit_slot(session_attributes, intent_name, slots, slot_to_elicit, message):
    return {
        'sessionAttributes': session_attributes,
        'dialogAction': {
            'type': 'ElicitSlot',
            'intentName': intent_name,
            'slots': slots,
            'slotToElicit': slot_to_elicit,
            'message': message
        }
    }


def confirm_intent(session_attributes, intent_name, slots, message):
    return {
        'sessionAttributes': session_attributes,
        'dialogAction': {
            'type': 'ConfirmIntent',
            'intentName': intent_name,
            'slots': slots,
            'message': message
        }
    }


def close(session_attributes, fulfillment_state, message):
    response = {
        'sessionAttributes': session_attributes,
        'dialogAction': {
            'type': 'Close',
            'fulfillmentState': fulfillment_state,
            'message': message
        }
    }

    return response


def delegate(session_attributes, slots):
    return {
        'sessionAttributes': session_attributes,
        'dialogAction': {
            'type': 'Delegate',
            'slots': slots
        }
    }


# --- Helper Functions ---


def safe_int(n):
    """
    Safely convert n value to int.
    """
    if n is not None:
        return int(n)
    return n


def try_ex(func):
    """
    Call passed in function in try block. If KeyError is encountered return None.
    This function is intended to be used to safely access dictionary.

    Note that this function would have negative impact on performance.
    """

    try:
        return func()
    except KeyError:
        return None


# t


def build_validation_result(isvalid, violated_slot, message_content, slots, session_attributes):
    return {
        'isValid': isvalid,
        'violatedSlot': violated_slot,
        'message': {'contentType': 'PlainText', 'content': message_content},
        'slots': slots,
        'session_attributes':session_attributes,
    }


def isValid(key,val,slots,session_attributes):
    if key == 'LoE' and key not in session_attributes:
        if not val in ['Graduate','Grad','graduate','grad','Undergraduate','undergraduate','Undergrad','undergrad','PhD','phd','Phd','Ph.D','High School','High school','high school']:

            print  'error', key, val
            return build_validation_result(False,key,'Unable to associate your level of education to one among the options',slots,session_attributes)
        else:
            if val in ['Graduate', 'Grad', 'graduate','grad']:
                slots['LoE'] = 'Graduate'
            elif val in ['Undergraduate','undergraduate','Undergrad','undergrad']:
                slots['LoE'] = 'Undergrad'
            elif val in ['PhD','phd','Phd','Ph.D']:
                slots['LoE'] = 'PhD'
            else:
                slots['LoE'] = 'High School'
            val = slots['LoE']
            session_attributes['LoE'] = ['High School', 'Undergrad', 'Graduate', 'PhD'].index(val)
            session_attributes['Undergrad'] = 1
            if val == 'Graduate':
                slots['PlanMasters'] = 'Yes'
                session_attributes['Masters'] = 1
            elif val == 'PhD':
                slots['PlanMasters'], session_attributes['Masters'], slots['PlanPhD'], session_attributes[
                    'PhD'] = 'Yes', 1, 'Yes', 1

            if val == 'High School':
                session_attributes['Undergrad'] = -1

    elif key == 'PlanMasters' and 'Masters' not in session_attributes:
        if val not in ['Yes','yes','No','no', 'maybe', 'Maybe','perhaps','Perhaps']:
            print  'error',key,val
            return build_validation_result(False,key, 'Unable to understand response. Reply with either a Yes or No',slots,session_attributes)
        else:
            if val in ['Yes', 'yes']:
                slots[key] = 'Yes'
            elif val in ['maybe', 'Maybe', 'perhaps', 'Perhaps']:
                slots[key] = 'Maybe'
            else:
                slots[key] = 'No'
            val = slots[key]
            if val == 'Yes':
                session_attributes['Masters'] = 1
            elif val in ['Perhaps', 'Maybe']:
                session_attributes['Masters'] = 0
                slots['PlanPhD'], session_attributes['PhD'] = 'No', -1
            else:
                session_attributes['Masters'] = -1
                slots['PlanPhD'], session_attributes['PhD'] = 'No', -1

    elif key == 'PlanPhD' and 'PhD' not in session_attributes:
        if val not in ['Yes','yes','No','no', 'maybe', 'Maybe','perhaps','Perhaps']:
            print  'error',key,val
            return build_validation_result(False,key, 'Unable to understand response. Reply with either a Yes or No',slots,session_attributes)
        else:
            if val in ['Yes', 'yes']:
                slots[key] = 'Yes'
            elif val in ['maybe', 'Maybe', 'perhaps', 'Perhaps']:
                slots[key] = 'Maybe'
            else:
                slots[key] = 'No'
            val = slots[key]
            if val == 'Yes':
                session_attributes['PhD'] = 1
            elif val in ['Perhaps', 'Maybe']:
                session_attributes['PhD'] = 0
            else:
                session_attributes['PhD'] = -1

    elif key == 'OS' and key not in session_attributes:
        if not val.isdigit():
            print  'error', key, val
            return build_validation_result(False, key, 'Please enter a valid number', slots,session_attributes)
        else:
            _n = int(val)
            if _n < 0:
                print  'error', key, val
                return build_validation_result(False, key, 'Please enter a number greater than 0', slots,session_attributes)

        session_attributes['OS'] = int(val)
        if val == 0:
            slots['Linux'] = 'No'
            session_attributes['Linux'] = -1

    elif (key == 'MobileApp' or key == 'Frontend' or key == 'Backend'  or key == 'API' or key == 'Linux' or key == 'Team' or key == 'JAVA' or key == 'SystemSw' or key == 'CCNA') and key not in session_attributes:
        if val not in ['Yes','yes','No','no', 'maybe', 'Maybe','perhaps','Perhaps']:
            print  'error',key,val
            return build_validation_result(False,key, 'Unable to understand response. Reply with either a Yes or No',slots,session_attributes)
        else:
            if val in ['Yes','yes']:
                slots [key] = 'Yes'
            elif val in ['maybe','Maybe','perhaps','Perhaps']:
                slots[key] = 'Maybe'
            else:
                slots[key] = 'No'
            val = slots[key]
            session_attributes[key] = -1 if val == 'No' else (1 if val == 'Yes' else 0)

    elif (key == 'Specialization' or key == 'Projects' or key == 'Math') and key not in session_attributes:
        num = list(val)
        for n in num :
            if not n.isdigit():
                print 'error',key,val
                return build_validation_result(False,key,'One of the numbers is invalid. Please try again',slots,session_attributes)
            else:
                _n = int(n)
                if _n < 0 or _n > 5:
                    print 'error', key, val, _n
                    return build_validation_result(False, key, 'Enter the numbers between 0-5',slots,session_attributes)

        if key == 'Projects':

                session_attributes['Projects'] = [-1] * 6
                index = [str(v) for v in val]
                for i in index:
                    session_attributes['Projects'][int(i)] = 1
                session_attributes['Projects'] = session_attributes['Projects'][1:]
                if '0' in index:
                    slots['MobileApp'], slots['Frontend'], slots['Backend'], slots['CCNA'], slots['Math'], \
                    slots['API'] = 'No', 'No', 'No', 'No', '0', 'No'
                    session_attributes['MobileApp'], session_attributes['Frontend'], session_attributes[
                        'Backend'], session_attributes['CCNA'], \
                    session_attributes['Math'], session_attributes['API'] = -1, -1, -1, -1, 0, -1
                else:
                    if '1' not in index:
                        slots['Math'] = '0'
                        session_attributes['Math'] = 0
                    if '2' not in index and '5' not in index:
                        slots['Frontend'], slots['MobileApp'] = 'No', 'No'
                        session_attributes['Frontend'], session_attributes['MobileApp'] = -1, -1
                    if '3' not in index:
                        slots['CCNA'] = 'No'
                        session_attributes['CCNA'] = -1
                    if '4' not in index:
                        slots['SystemSw'] = 'No'
                        session_attributes['SystemSw'] = -1
                session_attributes['Projects'] = ",".join([str(i) for i in session_attributes['Projects']])
        elif key == 'Specialization':
                session_attributes['Specialization'] = [-1]*6
                index = [int(v) for v in list(val)]
                for i in index:
                    session_attributes['Specialization'][i] = 1
                session_attributes['Specialization'] = ",".join(map(str,session_attributes['Specialization'] [1:]))
        elif key == 'Math':

                session_attributes['Math'] = int(val)
        # slots[key] = " ".join(num)

    return build_validation_result(True, key, None, slots, session_attributes)

def next_action(intent_request):
    slots = intent_request['currentIntent']['slots']
    session_attributes = intent_request['sessionAttributes'] if intent_request['sessionAttributes'] is not None else {}
    return delegate(session_attributes,slots)

def dot_product(session,role):
    # print 'session',session, '\nrole',role
    _sum = 0
    for key,val  in role.items():
        if key not in ['Role','Message']:
            _sum += float(val) * float(session[key])
    return _sum


def generate_career(session):
    for key in ['Projects','Specialization','OS','Math']:
        if key == 'Projects':
            li = map(int,session[key].split(","))
            for i in range(len(li)):
                session['P_'+str(i)] = li[i]
        elif key == 'Specialization':
            li = map(int,session[key].split(","))
            for i in range(len(li)):
                session['S_'+str(i)] = li[i]
        elif key == 'OS':
            val = int(session[key])
            val = min(6,val)
            _map = { 0:-1, 1:-0.5, 2:0, 3:0.25, 4:0.6, 5:0.8, 6:1}
            val = _map[val]
            session[key] = val
        elif key == 'Math':
            _map = {0: -1, 1: -0.5, 2: 0.25, 3: 0.5, 4: 0.8, 5: 1}
            session[key] = _map[int(session[key])]
    # print session
    roles = {}
    for key,val in mydict.items():
        roles[key] = dot_product(session,val)
    _max = max(roles.items(), key=lambda x: x[1])


    return 'Thanks for answering my questions. Looking at them I believe {}. Thanks for using our Career bot. If you wish to come again, just sai "hi" :)'.format(mydict[_max[0]]['Message'])

def career_advise(intent_request):
    print 'coming in', intent_request
    slots = intent_request['currentIntent']['slots']
    session_attributes = intent_request['sessionAttributes'] if intent_request['sessionAttributes'] is not None else {}
    complete = True
    for key,val in slots.items():
        if val is None :
            complete = False
        else:
            validation_result = isValid(key, val, slots,session_attributes)
            slots = validation_result['slots']
            session_attributes = validation_result['session_attributes']
            if not validation_result['isValid']:
                return elicit_slot(
                    session_attributes,
                    intent_request['currentIntent']['name'],
                    slots,
                    key,
                    validation_result['message']
                )
    if complete:
        msg = generate_career(session_attributes)
        return close(
            {},
            'Fulfilled',
            {
                'contentType': 'PlainText',
                'content': msg
            }
        )
    return delegate(session_attributes,slots)


def dispatch(intent_request):
    """
    Called when the user specifies an intent for this bot.
    """

    logger.debug(
        'dispatch userId={}, intentName={}'.format(intent_request['userId'], intent_request['currentIntent']['name']))

    intent_name = intent_request['currentIntent']['name']

    # Dispatch to your bot's intent handlers
    if intent_name == 'CareerIntent':
        return career_advise(intent_request)
    elif intent_name == 'Help_intent':
        return close(
            intent_request['sessionAttributes'] if intent_request['sessionAttributes'] is not None else {},
            'Fulfilled',
            {
                'contentType': 'PlainText',
                'content': 'I can help you navigate your thoughts and choose a career suitable for you. As mentioned, I am currently restricted towards careers in Computer Science. You may answer a couple of quick questions, and I will try to suggest you a good path. Type ok to conitnue.'
            }
        )
    elif intent_name == "GreetIntent":
        return close(
            {},
            'Fulfilled',
            {
                'contentType': 'PlainText',
                'content': 'Hi. I am a bot and I can help you choose a path in Computer Science based on your profile. We will go over a set of questions to understand your interests. Shall we start? Type ok to start.'
            }
        )
    return book_car(intent_request)

    # raise Exception('Intent with name ' + intent_name + ' not supported')


# --- Main handler ---


def lambda_handler(event, context):
    """
    Route the incoming request based on intent.
    The JSON body of the request is provided in the event slot.
    """
    # By default, treat the user request as coming from the America/New_York time zone.
    os.environ['TZ'] = 'America/New_York'
    time.tzset()
    logger.debug('event.bot.name={}'.format(event['bot']['name']))

    return dispatch(event)


# if __name__ == "__main__":
#
#         session = {u'Masters': u'1', u'Undergrad': u'1',
#                    u'Frontend': u'1', u'Specialization':
#                        u'1,-1,-1,-1,-1', u'LoE': u'2',
#                    u'SystemSw': u'-1', u'MobileApp': u'1',
#                    u'Team': u'-1', u'PhD': u'-1', u'API': u'1',
#                    u'CCNA': u'-1', u'Linux': u'1', u'Backend': u'1',
#                    u'OS': u'3', u'Math': u'3',
#                    u'Projects': u'1,1,-1,-1,1',
#                    'JAVA':'1'}
#         print generate_career(session)
