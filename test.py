import sys
import re

for arg in sys.argv:
    if arg[-3:] == '.py':
        continue
    if arg == 'ipv6' or arg == 'IPv6' or arg == 'v6' or arg == '6':
        getip = 'ipv6'
        continue
    if arg == 'ipv4' or arg == 'IPv4' or arg == 'v4' or arg == '4':
        getip = 'ipv4'
        continue
    if re.findall(r'[0-9a-f]{32}', arg) != []:
        ZONE_ID = re.findall(r'[0-9a-f]{32}', arg)[0]
        continue
    if len(arg.split('.')) > 1:
        name = arg
    elif len(arg)>32:
        TOKEN = arg

print(getip)
print(ZONE_ID)
print(name)
print(TOKEN)