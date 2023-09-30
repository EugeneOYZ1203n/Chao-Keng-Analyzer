from pathlib import Path
import re
from datetime import datetime
from collections import defaultdict

CHAT_LOG_PATH = Path("./input/_chat.txt")

Chat_log = open(CHAT_LOG_PATH, mode="r", encoding='utf8')

## Splitting Chat into individual msgs
msgs = []

current = ""
for line in Chat_log:
    if re.search("\[.*].*:", line):
        if re.search("\[.*].*:", current):
            msgs.append(current)
            current = ""
    current += line + " "

MC_MSG_COUNT = 0
STATUS_MSG_COUNT = 0

filtered_msgs = []

for msg in msgs:

    isStatusMsg = re.search("\[.*].*:.*/.*/.*", msg)
    isMCMsg = all([x in msg for x in ["Who", "What", "When", "Where", "Why"]])

    if isStatusMsg:
        STATUS_MSG_COUNT += 1
    elif isMCMsg:
        MC_MSG_COUNT += 1
    else:
        filtered_msgs.append(msg)

print(filtered_msgs)



    

##name = re.findall("\[.*].*:", msg)[0].split(']')[1].rstrip(':')
    

