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
    if re.search("\[[0-9]*/[0-9]*/[0-9]*", line):
        msgs.append(current)
        current = ""
    current += line + " "

for i in range(40):
    msg = msgs[i]

    isStatusMsg = re.search("\[.*].*:.*/.*/.*", msg)
    isMCMsg = all([x in msg for x in ["Who", "What", "When", "Where", "Why"]])