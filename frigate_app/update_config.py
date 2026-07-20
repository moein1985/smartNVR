import json

with open('full_config.json') as f:
    d = json.load(f)

d['go2rtc'] = {
    'streams': {
        'cam1': [
            'rtsp://admin:admin123@192.168.85.112:554/Streaming/Channels/101',
            'ffmpeg:cam1#audio=opus'
        ]
    },
    'webrtc': {
        'candidates': [
            '192.168.85.203:8555',
            'stun:8555'
        ]
    }
}

body = {'config_data': d, 'requires_restart': 1}
with open('full_config_update.json', 'w') as f:
    json.dump(body, f)

print('Written update config with go2rtc and restart')
