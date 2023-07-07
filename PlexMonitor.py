import requests
import time
import json

# Load configuration
with open('config.json') as f:
    config = json.load(f)

# Plex details
plex_token = config['PLEX_TOKEN']
plex_server_ip = config['PLEX_SERVER_IP']

# Hue details
hue_bridge_ip = config['HUE_BRIDGE_IP']
hue_username = config['HUE_USERNAME']
hue_light_id = config['HUE_LIGHT_ID']


def main():
    PollPlexStatus()


def PollPlexStatus():
    # Hue light state for red light
    red_light_state = {
        "on": True,
        "bri": 254,
        "hue": 0,
        "sat": 254
    }

    previous_plex_offline = False
    user_light_state = red_light_state.copy()
    pending_notification = False

    while True:
        try:
            # Check every minute
            time.sleep(60)

            try:
                # Get new plex status
                plex_offline = 200 != requests.get(f'http://{plex_server_ip}:32400/status/sessions?X-Plex-Token={plex_token}', timeout=3).status_code
            except requests.ConnectTimeout as err:
                plex_offline = True
            
            if pending_notification:
                user_light_state = GetLightState()
                if user_light_state['on']:
                    SetLightState(red_light_state)
                    pending_notification = False

            if plex_offline == previous_plex_offline:
                # No change in status
                continue

            # Update previous status
            previous_plex_offline = plex_offline
            
            if plex_offline:
                # We just went from online to offline
                # Save the current light state and set the red light
                user_light_state = GetLightState()
                if user_light_state['on']:
                    SetLightState(red_light_state)
                else:
                    pending_notification = True
            else:
                # We just went from offline to online
                # Restore the light state
                SetLightState(user_light_state)
                pending_notification = False

        except:
            pass

def GetLightState():
    response = requests.get(
        f'http://{hue_bridge_ip}/api/{hue_username}/lights/{hue_light_id}'
    ).json()['state']
    
    return {
        "on": response['on'],
        "bri": response['bri'],
        "hue": response['hue'],
        "sat": response['sat']
    }


def SetLightState(state):
    requests.put(
        f'http://{hue_bridge_ip}/api/{hue_username}/lights/{hue_light_id}/state',
        json=state
    )


if __name__ == '__main__':
    main()