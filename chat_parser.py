from pathlib import Path
import re
from datetime import datetime
from collections import defaultdict

CHAT_LOG_PATH = Path("./input/_chat.txt")

Chat_log = open(CHAT_LOG_PATH, mode="r", encoding='utf8')

data = defaultdict(list)
nameList = defaultdict(set)

for line in Chat_log:
    
    isNotImage = not "image omitted" in line
    isNotLink = not "http" in line

    if isNotImage & isNotLink:
        continue

    isStatusMsg = bool(re.search(".*/.*/.*/.*/.*", line))
    hasDate = bool(re.search("[0-9]*/[0-9]*/[0-9]*", line))

    shortMsg = isStatusMsg & hasDate

    

    if shortMsg:
        date_str = re.findall('[0-9]*/[0-9]*/[0-9]*', line)[0]
        status = re.findall('].*/.*/.*', line)[0]

        ## Handling the date
        day, month, year = date_str.split('/')
        date_object = datetime(int(year), int(month), int(day))

        ## Day of the week
        weekday = date_object.weekday()

        ## Status Splitting
        status = status.lstrip('] ')
        name1 = re.findall(".*:", status)[0].rstrip(':')
        name2, location, status_type = re.findall(": .*/.*/.*", status)[0].lstrip(': ').split('/')[:3]

        ## Status Type Identification
        status_type = status_type.lower()

        if re.search(".*rso .*", status_type):
            status_type = "RSO"
        elif re.search(".*ma .*", status_type):
            status_type = "MA"
        elif re.search(".*off .*", status_type):
            status_type = "OFF"
        elif re.search(".*ll .*", status_type):
            status_type = "LL"
        elif re.search(".*ol .*", status_type):
            status_type = "OL"

        data[name1].append((date_object, location, status_type))
        nameList[name1].add(name2)

consolidated_info = defaultdict(list)

print(data)
