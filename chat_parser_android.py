from pathlib import Path
import re
from alive_progress import alive_bar
from datetime import datetime, timedelta 
from collections import defaultdict, Counter
import csv
import os

CHAT_LOG_PATH = Path("./input/_chat.txt")

LOG_MSG_LEN = 40

LOG_FILTERED_MSG = False ## Logs the filtered messages
LOG_MC_MSG = False ## Logs the mc messages
LOG_STATUS_MSG = False ## Logs the status messages

LOG_ASSUME_ERROR = False
LOG_SKIP_ERRORS = False


Chat_log = open(CHAT_LOG_PATH, mode="r", encoding='utf8')

## Splitting Chat into individual msgs
msgs = []

MSG_HEADER_REGEX = "[0-9]*/[0-9]*/[0-9]*, [0-9]*:[0-9]* -"

print('\n')

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

MC_MSG_REGEXs = ["what", "who", "when", "where", "why", "mc|leave"]
STATUS_MSG_REGEXs = [":.*/.*/.*"]
FILTER_REGEXs = ["http", "duty swap", "tagging", "si parade"]

mc_msgs = []
status_msgs = []
filtered_msgs = []

format_error_skipped = 0
format_error_assumed = 0

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

print(f'\nFiltered {len(filtered_msgs)} messages in chat log\n')

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
    
    return sum([1 for day in dates if day.weekday() < 5])

def get_startdur_from_keyword(keyword, backup):
    if "/" in keyword:
        dates = re.findall("[0-9]*/[0-9]*/[0-9]*", keyword)

        for j in range(len(dates)):
            try:
                if len(dates[j]) == 10:
                    dates[j] = datetime.strptime(dates[j], "%d/%m/%Y")
                elif len(dates[j]) == 8:
                    dates[j] = datetime.strptime(dates[j], "%d/%m/%y")
            except:
                if LOG_ASSUME_ERROR:
                    print(f'Date Parse error, {msg} \n {error}')
                
                format_error_assumed += 1
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
                if LOG_ASSUME_ERROR:
                    print(f'Date Parse error, {msg} \n {error}')

                format_error_assumed += 1
                dates = []
                break

    if len(dates) == 1:
        return (dates[0], 1, get_weekdays_in_period(dates[0], 1))
    elif len(dates) == 2:
        start_date = min(dates)
        end_date = max(dates)

        return (start_date, (end_date - start_date).days + 1, get_weekdays_in_period(dates[0], (end_date - start_date).days + 1))
    else:
        return (backup, 1, 1)

namelist = set()

## Handling MC Messages

mc_data = defaultdict(list)

rso_Count = 0
ma_Count = 0
mc_Days = 0
mc_Workdays = 0

with alive_bar(0) as bar:
    for msg in mc_msgs:
        bar()
        msg = msg.replace('\n', ' ')

        try:
            sent_date = msg.split(',')[0]
            identifier = msg.split('-')[1].split(':')[0]

            namelist.add(identifier)

            fullname = msg.split('who')[1].split('what')[0].lstrip(": *").rstrip("* ")
            mc_duration = int(msg.split('what')[1].split('when')[0].split('for')[1].split('day')[0])
            where_mc = msg.split('where')[1].split('why')[0].lstrip(": *").rstrip("* ")
            why_mc = msg.split('why')[1].split('how')[0].lstrip(": *").rstrip("* ")

            mc_start_date = datetime.strptime(sent_date, "%d/%m/%Y")
            mc_work_days = get_weekdays_in_period(mc_start_date, mc_duration)

            try:
                mc_type = msg.split('the following')[1].split('who')[0]

                if re.search("ted sick|rso", mc_type):
                    mc_type = "rso mc"
                elif re.search("medical appointment|[!a-zA-Z]*ma[!a-zA-Z]*", mc_type):
                    mc_type = "ma mc"
                else:
                    if LOG_ASSUME_ERROR:
                        print(f'Message had to be assumed - did not find rso or ma, {msg}')
                    
                    format_error_assumed += 1
                    if re.search("medical appointment|[!a-zA-Z]*ma[!a-zA-Z]*", msg):
                        mc_type = "ma mc"
                    else:
                        mc_type = "rso mc"
            except Exception as error:
                if LOG_ASSUME_ERROR:
                    print(f'Message had to be assumed - error occured in searching, {msg} {error}')
                
                format_error_assumed += 1
                if re.search("medical appointment|[!a-zA-Z]*ma[!a-zA-Z]*", msg):
                    mc_type = "ma mc"
                else:
                    mc_type = "rso mc"

            if mc_type == "ma mc":
                ma_Count += 1
            else:
                rso_Count += 1

            mc_Days += mc_duration
            mc_Workdays += mc_work_days

            mc_data[identifier].append([fullname, mc_type, mc_start_date, mc_duration, mc_work_days, where_mc, why_mc, ''.join(char for char in msg if ord(char) < 128)])

        except Exception as error:
            if LOG_SKIP_ERRORS:
                print(f'Message was skipped, {msg} {error}')
            
            format_error_skipped += 1
            continue

print(f'\nOut of {len(mc_msgs)} MC messages,')
print(f'\t{rso_Count} ({rso_Count * 10000//len(mc_msgs)/100}%) were RSO')
print(f'\t{ma_Count} ({ma_Count * 10000//len(mc_msgs)/100}%) were MA')
print(f'\t{mc_Days} days of MC total, with only {mc_Workdays} ({mc_Workdays*10000//mc_Days/100}%) being on work days\n')

## Handling status messages

status_data = defaultdict(list)

word_count_in_details = Counter()

rso_list = ["rso"]
leave_list = ["ol", "ll", "leave"]
ma_list = ["ma"]
off_list = ["off", "oil"]
reductions_list = ["pm", "am"]
dates_list = [
    "[0-9]*/[0-9]*/[0-9]*\s*-\s*[0-9]*/[0-9]*/[0-9]*",
    "[0-9]{6,8}\s*-\s*[0-9]{6,8}",
    "[0-9]*/[0-9]*/[0-9]*", "[0-9]{6,8}"
]

status_counts = defaultdict(int)

with alive_bar(0) as bar:
    for i, msg in enumerate(status_msgs):
        try:
            sent_date = msg.split(',')[0]
            identifier = msg.split('-')[1].split(':')[0]

            namelist.add(identifier)

            fullname = msg.split(':')[2].split('/')[0].strip(" ")
            
            details = "/".join(msg.split(':')[2].split('/')[2:]).strip(" ")

            ## Debugging Purposes
            for word in details.split(" "):
                word = word.strip("\n()<>")
                if re.search("[0-9]", word):
                    continue
                word_count_in_details[word] += 1

            keywords = re.findall("|".join(rso_list + leave_list + ma_list + off_list + reductions_list + dates_list), details)
            if len(keywords) == 0:
                continue

            ## Handles the type of status and duration of status in format "rso": [dur, workdays, startdate]
            type_and_dur = defaultdict(list)

            check = [0.0, "", datetime.strptime(sent_date, "%d/%m/%Y"), 1.0, 1.0]

            for keyword in keywords + [" "]:
                ## Handling Update Conditions
                isNewType = (keyword in rso_list + leave_list + ma_list + off_list) and (check[1] != "")
                isDateAndTypeGiven = (keyword not in rso_list + leave_list + ma_list + off_list + reductions_list) and (check[1] != "")
                isEnd = keyword == " "

                if isNewType or isDateAndTypeGiven and isEnd:
                    if check[1] == "":
                        continue

                    if check[1] == "ma" or check[1] == "rso":
                        check[0] = 0.0
                        check[3] = 1.0

                    if len(type_and_dur[check[1]]) != 2:
                        type_and_dur[check[1]] = [check[3] - check[0],check[4] - check[0], check[2]]
                    else:
                        type_and_dur[check[1]][0] += check[3] - check[0]
                        type_and_dur[check[1]][1] += check[4] - check[0]
                    status_counts[check[1]+" days"] += check[3] - check[0]
                    status_counts[check[1]+" workdays"] += check[4] - check[0]
                    status_counts[check[1]+" msgs"] += 1
                    check = [0.0, "", datetime.strptime(sent_date, "%d/%m/%Y"), 1.0, 1.0]
                
                ## Handling Type
                if keyword in rso_list:
                    check[1] = "rso"
                elif keyword in leave_list:
                    check[1] = "leave"
                elif keyword in ma_list:
                    check[1] = "ma"
                elif keyword in off_list:
                    check[1] = "off"

                ## Handling Half days
                elif keyword in reductions_list:
                    check[0] = 0.5

                ## Ignoring " " as it is the end identifier
                elif keyword == " ":
                    continue
                
                ## Handling Dates
                else:
                    start, dur, work_dur = get_startdur_from_keyword(keyword, datetime.strptime(sent_date, "%d/%m/%Y"))
                    check[2] = start
                    check[3] = dur
                    check[4] = work_dur
            
            for key in type_and_dur.keys():
                status_data[identifier].append([fullname, key, type_and_dur[key][2], type_and_dur[key][0], type_and_dur[key][1], "-", details, ''.join(char for char in msg if ord(char) < 128)])

        except Exception as error:
            if LOG_SKIP_ERRORS:
                print(f'Message was skipped, {msg} \n {error}')
            
            format_error_skipped += 1
            continue
        
        bar()

print(f'\nOut of {len(status_msgs)} Status messages,') 
print(f'\tRSO: {status_counts["rso msgs"]} ({status_counts["rso msgs"] * 10000//len(status_msgs)/100}%) msgs, {status_counts["rso days"]} days, {status_counts["rso workdays"]} ({status_counts["rso workdays"]*10000//status_counts["rso days"]/100}%) workdays')
print(f'\tLeave: {status_counts["leave msgs"]} ({status_counts["leave msgs"] * 10000//len(status_msgs)/100}%) msgs, {status_counts["leave days"]} days, {status_counts["leave workdays"]} ({status_counts["leave workdays"]*10000//status_counts["leave days"]/100}%) workdays')
print(f'\tOff: {status_counts["off msgs"]} ({status_counts["off msgs"] * 10000//len(status_msgs)/100}%) msgs, {status_counts["off days"]} days, {status_counts["off workdays"]} ({status_counts["off workdays"]*10000//status_counts["off days"]/100}%) workdays')
print(f'\tMA: {status_counts["ma msgs"]} ({status_counts["ma msgs"] * 10000//len(status_msgs)/100}%) msgs, {status_counts["ma days"]} days, {status_counts["ma workdays"]} ({status_counts["ma workdays"]*10000//status_counts["ma days"]/100}%) workdays')
print('Note: Some people apply for multiple leave, off, ma using the same message\n')


print(f'Total of {format_error_skipped} messages were skipped and {format_error_assumed} messages were assumed due to formatting issues\n')

## removing all previous output

for filename in os.listdir('output'):
    file_path = os.path.join('output', filename)
    try:
        if os.path.isfile(file_path) or os.path.islink(file_path):
            os.unlink(file_path)
    except Exception as e:
        print('Failed to delete %s. Reason: %s' % (file_path, e))

## Generating all Csv files

list_of_summary_headers = [X + Y for X in ["rso", "ma", "leave", "off", "rso mc", "ma mc"] for Y in [" count", " Mon", " Tues", " Wed", " Thu", " Fri", " Sat", " Sun", " duration", " workdays duration"]]

with alive_bar(0) as bar:
    summary_sheet = open(f'output/summary.csv', 'w')
    summary_writer = csv.writer(summary_sheet)

    summary_writer.writerow(["name", "othernames"] + list_of_summary_headers)

    for name in namelist:
        file_name = ''.join(char for char in name.title().strip(' ') if ord(char) < 128).replace(" ", "_")
        summarised_data = defaultdict(int)
        other_names = set([])

        with open(f'output/{file_name}.csv', 'w') as file:
            writer = csv.writer(file)

            writer.writerow(["name", "type", "start_date", "duration", "workdays duration", "location", "reason", "message"])

            for entry in mc_data[name] + status_data[name]:
                summarised_data[entry[1] + " count"] += 1
                summarised_data[entry[1] + " " + entry[2].strftime('%a')] += 1
                summarised_data[entry[1] + " duration"] += entry[3]
                summarised_data[entry[1] + " workdays duration"] += entry[4]
                other_names.add(''.join(char for char in entry[0] if ord(char) < 128))

                try:
                    writer.writerow(entry)
                except UnicodeEncodeError as error:
                    print(f'Failed to write line as {entry} has {error}')
            
            file.close()
    
        try:
            summary_writer.writerow([file_name, ' '.join(other_names)] + [summarised_data[X] for X in list_of_summary_headers])
        except UnicodeEncodeError as error:
            print(f'Failed to write line as {[file_name, " ".join(other_names)] + [summarised_data[X] for X in list_of_summary_headers]} has {error}')
        
        
        bar()

    summary_sheet.close()

print(f'\nGenerated {len(namelist)} .csv files documenting all mc, off, rso, leave, ma of each unique individual (Categorised by Phone number)')
print(f'Generated a summary.csv file containing numerical values for each individual')