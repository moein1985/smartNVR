import json
with open('full_config.json') as f:
    d = json.load(f)
print('go2rtc' in d)
print(list(d.keys())[:10])
if 'go2rtc' in d:
    print(json.dumps(d['go2rtc'], indent=2))
