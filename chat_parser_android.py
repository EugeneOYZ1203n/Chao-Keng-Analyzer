from pathlib import Path
import re
from alive_progress import alive_bar
from datetime import datetime, timedelta 
from collections import defaultdict, Counter

CHAT_LOG_PATH = Path("./input/_chat.txt")

LOG_MSG_LEN = 40

LOG_FILTERED_MSG = False ## Logs the filtered messages
LOG_MC_MSG = False ## Logs the mc messages
LOG_STATUS_MSG = False ## Logs the status messages

LOG_PARSING_ERRORS = False ## Logs messages that had difficulty being parsed


Chat_log = open(CHAT_LOG_PATH, mode="r", encoding='utf8')

## Splitting Chat into individual msgs
msgs = []

MSG_HEADER_REGEX = "[0-9]*/[0-9]*/[0-9]*, [0-9]*:[0-9]* -"

current = ""
with alive_bar(0) as bar:
    for line in Chat_log:
        if re.search(MSG_HEADER_REGEX, line):
            if re.search(MSG_HEADER_REGEX, current):
                msgs.append(current.lower())
                current = ""
        current += line + " "
        bar()
if re.search(MSG_HEADER_REGEX, current):
    msgs.append(current.lower())

print(f'\nFound a total of {len(msgs)} messages in chat log\n')

## Categorizing msgs into MC and Status types

MC_MSG_REGEXs = ["what", "who", "when", "where", "why", "mc"]
STATUS_MSG_REGEXs = [":.*/.*/.*"]
FILTER_REGEXs = ["http", "duty swap", "tagging", "si parade"]

mc_msgs = []
status_msgs = []
filtered_msgs = []

with alive_bar(0) as bar:
    for msg in msgs:
        if any([re.search(regex, msg) for regex in FILTER_REGEXs]):
            filtered_msgs.append(msg)
        elif all([re.search(regex, msg) for regex in MC_MSG_REGEXs]):
            mc_msgs.append(msg)
        elif all([re.search(regex, msg) for regex in STATUS_MSG_REGEXs]):
            status_msgs.append(msg)
        else:
            filtered_msgs.append(msg)
        
        bar()

print(f'Filtered {len(filtered_msgs)} messages in chat log\n')

if LOG_FILTERED_MSG:
    print('Displaying Filtered Message Examples')

    gap = len(filtered_msgs) // LOG_MSG_LEN

    for i in range(LOG_MSG_LEN):
        print(i+1, filtered_msgs[i * gap])

print(f'Found a total of {len(mc_msgs)} MC messages in chat log')

if LOG_MC_MSG:
    print('Displaying MC Message Examples')

    gap = len(mc_msgs) // LOG_MSG_LEN

    for i in range(LOG_MSG_LEN):
        print(i+1, mc_msgs[i * gap])

print(f'Found a total of {len(status_msgs)} Status messages in chat log\n')

if LOG_STATUS_MSG:
    print('Displaying Status Message Examples')

    gap = len(status_msgs) // LOG_MSG_LEN

    for i in range(LOG_MSG_LEN):
        print(i+1, status_msgs[i * gap])

## Misc Functions

def get_weekdays_in_period(start_date, dur):
    dates = (start_date + timedelta(idx)
         for idx in range(dur))

    return sum(1 for day in dates if day.weekday() < 5)

## Handling MC Messages

rso_Count = 0
ma_Count = 0
mc_Days = 0
mc_Workdays = 0

for msg in mc_msgs:
    try:
        sent_date = msg.split(',')[0]
        identifier = msg.split('-')[1].split(':')[0]
        fullname = msg.split('who')[1].split('what')[0].lstrip(": *").rstrip("* ").replace('\n','')
        mc_duration = int(msg.split('what')[1].split('when')[0].split('for')[1].split('day')[0])
        where_mc = msg.split('where')[1].split('why')[0].lstrip(": *").rstrip("* ").replace('\n','')
        why_mc = msg.split('why')[1].split('how')[0].lstrip(": *").rstrip("* ").replace('\n','')

        mc_start_date = datetime.strptime(sent_date, "%d/%m/%Y")
        mc_work_days = get_weekdays_in_period(mc_start_date, mc_duration)

        try:
            mc_type = msg.split('from tsb')[1].split('who')[0]

            if re.search("reported sick|rso", mc_type):
                mc_type = "rso"
            elif re.search("medical appointment|\sma\s", mc_type):
                mc_type = "ma"
            else:
                if LOG_PARSING_ERRORS:
                    print(f'Format of this msg is weird, {msg}')
                    break
                else:
                    mc_type = "ma"
        except Exception as error:
            if LOG_PARSING_ERRORS:
                print(f'Format of this msg is weird, {msg} \n {error}')
                break
            else:
                if "ma" in msg:
                    mc_type = "ma"
                else:
                    mc_type = "rso"

        if mc_type == "ma":
            ma_Count += 1
        else:
            rso_Count += 1
        
        mc_Days += mc_duration
        mc_Workdays += mc_work_days

    except Exception as error:
        if LOG_PARSING_ERRORS:
            print(f'Format of this msg is weird, {msg} \n {error}')
            break
        else:
            continue

print(f'Out of {len(mc_msgs)} MC messages, {rso_Count} ({rso_Count * 10000//len(mc_msgs)/100}%) were RSO, {ma_Count} ({ma_Count * 10000//len(mc_msgs)/100}%) were MA')

## Handling status messages

word_count_in_details = Counter()

rso_list = ["rso"]
leave_list = ["ol", "ll", "leave"]
ma_list = ["ma"]
off_list = ["off"]
other_reason_list = ["rsi", "mr", "ord", "course"]
reductions_list = ["pm", "am"]
dates_list = [
    "[0-9]*/[0-9]*/[0-9]*\s*-\s*[0-9]*/[0-9]*/[0-9]*",
    "[0-9]{6,8}\s*-\s*[0-9]{6,8}",
    "[0-9]*/[0-9]*/[0-9]*", "[0-9]{6,8}"
]

status_counts = defaultdict(int)

for i, msg in enumerate(status_msgs):
    try:
        sent_date = msg.split(',')[0]
        identifier = msg.split('-')[1].split(':')[0]
        fullname = msg.split(':')[2].split('/')[0].strip(" ")
        
        details = "/".join(msg.split(':')[2].split('/')[2:]).strip(" ")

        ## Debugging Purposes
        for word in details.split(" "):
            word = word.strip("\n()<>")
            if re.search("[0-9]", word):
                continue
            word_count_in_details[word] += 1

        keywords = re.findall("|".join(rso_list + leave_list + ma_list + off_list + other_reason_list + reductions_list + dates_list), details)
        if len(keywords) == 0:
            keywords.append("rso")

        current_type = ""
        current_total = 1.0
        current_start = datetime.strptime(sent_date, "%d/%m/%Y")

        ## Handles the type of status and duration of status in format "rso": [dur, startdate]
        type_and_dur = defaultdict(list)

        def update(current_type, current_total, current_start):
            if current_type == "":
                return
            if len(type_and_dur[current_type]) == 0:
                type_and_dur[current_type].append(current_total)
                type_and_dur[current_type].append(current_start)
            else:
                type_and_dur[current_type][0] += current_total

            status_counts[current_type] += current_total
            current_type = ""
            current_total -= max(current_total, 1)

        for keyword in keywords:
            if keyword in rso_list:
                current_type = "rso"
                update(current_type, 1, current_start)
            elif keyword in leave_list:
                update(current_type, current_total, current_start)
                current_type = "leave"
            elif keyword in ma_list:
                update(current_type, current_total, current_start)
                current_type = "ma"
            elif keyword in off_list:
                update(current_type, current_total, current_start)
                current_type = "off"
            elif keyword in reductions_list:
                current_total -= 0.5
            else:
                if "/" in keyword:
                    dates = re.findall("[0-9]*/[0-9]*/[0-9]*", keyword)

                    for j in range(len(dates)):
                        try:
                            if len(dates[j]) == 10:
                                dates[j] = datetime.strptime(dates[j], "%d/%m/%Y")
                            elif len(dates[j]) == 8:
                                dates[j] = datetime.strptime(dates[j], "%d/%m/%y")
                        except:
                            dates = []
                            break
                else:
                    dates = re.findall("[0-9]{6,8}", keyword)

                    for j in range(len(dates)):
                        try:
                            if len(dates[j]) == 8:
                                dates[j] = datetime.strptime(dates[j], "%d%m%Y")
                            elif len(dates[j]) == 6:
                                dates[j] = datetime.strptime(dates[j], "%d%m%y")
                        except:
                            if LOG_PARSING_ERRORS:
                                print(f'Format of this msg is weird, {msg} \n {error}')
                                break
                            else:
                                dates = []
                                break

                if len(dates) == 0:
                    update(current_type, current_total, current_start)
                elif len(dates) == 1:
                    current_start = dates[0]
                    current_total += 1
                    update(current_type, current_total, current_start)
                elif len(dates) == 1:
                    current_start = dates[0]
                    current_total += (dates[1] - dates[0]).days + 1
                    update(current_type, current_total, current_start)
        
        print(keywords)

    except Exception as error:
        if LOG_PARSING_ERRORS:
            print(f'Format of this msg is weird, {msg} \n {error}')
            break
        else:
            continue

print(status_counts)

    

    

