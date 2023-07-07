import json
import requests
import time
import logging

def load_config():
    """Load configuration from a JSON file."""
    with open('config.json') as f:
        return json.load(f)


def main():
    """Main function to start monitoring Plex server status."""
    config = load_config()
    poll_plex_status(config)


def poll_plex_status(config):
    """Continuously poll the Plex server status and update Hue lights accordingly."""
    # Hue light state for red light
    red_light_state = {
        "on": True,
        "bri": 254,
        "hue": 0,
        "sat": 254
    }

    previous_plex_offline = False
    pending_notification = False
    saved_light_state = None

    while True:
        time.sleep(config['POLL_INTERVAL_SECONDS'])  # Check every minute

        # Get new plex status
        plex_offline = get_plex_offline(config)

        if pending_notification:
            new_light_state = get_light_state(config)
            if new_light_state is not None and new_light_state['on']:
                saved_light_state = new_light_state
                set_light_state(red_light_state, config)
                pending_notification = False

        if plex_offline == previous_plex_offline:
            continue  # No change in status

        previous_plex_offline = plex_offline  # Update previous status

        if plex_offline:
            # We just went from online to offline
            # Save the current light state and set the red light
            new_light_state = get_light_state(config)
            if new_light_state is None or not new_light_state['on']:
                saved_light_state = new_light_state
                set_light_state(red_light_state, config)
                pending_notification = True
        else:
            # We just went from offline to online
            # Restore the light state
            set_light_state(saved_light_state, config)
            pending_notification = False


def get_plex_offline(config):
    """Check if the Plex server is offline."""
    plex_online_code = 200
    try:
        current_plex_code = requests.get(
            f"http://{config['PLEX_SERVER_IP']}:32400/status/sessions?X-Plex-Token={config['PLEX_TOKEN']}",
            timeout=3
        ).status_code
        
        return current_plex_code != plex_online_code
    except requests.exceptions.RequestException as e:
        logging.warning(f"Failed to get plex state with exception: {e}")
        return True


def get_light_state(config):
    """Get the current state of the Hue light."""
    try:
        response = requests.get(
            f"http://{config['HUE_BRIDGE_IP']}/api/{config['HUE_USERNAME']}/lights/{config['HUE_LIGHT_ID']}"
        ).json()['state']
        
        return {
            "on": response['on'],
            "bri": response['bri'],
            "hue": response['hue'],
            "sat": response['sat']
        }
    except requests.exceptions.RequestException as e:
        logging.warning(f"Failed to get light state with exception: {e}")
        return None


def set_light_state(state, config):
    """Set the state of the Hue light."""
    try:
        requests.put(
            f"http://{config['HUE_BRIDGE_IP']}/api/{config['HUE_USERNAME']}/lights/{config['HUE_LIGHT_ID']}/state",
            json=state
        )
    except requests.exceptions.RequestException as e:
        logging.warning(f"Failed to set light state with exception: {e}")

if __name__ == '__main__':
    main()
