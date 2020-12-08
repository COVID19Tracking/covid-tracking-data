import os
import io
import pandas as pd
import requests
import yaml
from datetime import date 
from datetime import timedelta

def load_urls_from_live_info(url):

    content = requests.get(url).content
    state_info_df = pd.read_csv(io.StringIO(content.decode('utf-8')), keep_default_na=False) # default_na=false so that empty cells -> empty strings
    
    state_urls = {}
    for idx, r in state_info_df.iterrows():
        state_urls[r["state"]] = {
            'primary': r["covid19Site"],
            'secondary': r["covid19SiteSecondary"],
            'tertiary': r["covid19SiteTertiary"],
            'quaternary': r["covid19SiteQuaternary"],
            'quinary': r["covid19SiteQuinary"],
        }

    return state_urls


def load_urls_from_spreadsheet(csv_url):

    urls_df = pd.read_csv(csv_url, keep_default_na=False) # default_na=false so that empty cells -> empty strings

    state_urls = {}
    for idx, row in urls_df.iterrows():
        state_urls[row['State']] = {
            'primary': row['Link 1'],
            'secondary': row['Link 2'],
            'tertiary': row['Link 3'],
        }

    return state_urls

# construct an array containing the URL configs (up to 5) for each state (including the URL, name and existing YAML config)
# then dump that dictionary to a new YAML file named after the state, in the appropriate directory
def output_yamls(team, state_urls, config_basename):
    
    screenshot_config_path = os.path.join(os.path.dirname(__file__), 'configs', config_basename)
    with open(screenshot_config_path) as f:
        existing_config = yaml.safe_load(f)

    # set up the output directory
    destination_directory =  os.path.join(os.path.dirname(__file__), 'configs', team)
    os.makedirs(destination_directory, exist_ok=True)

    # walk through the states from the spreadsheet
    for state, urls in state_urls.items():
 
        # open a file for the current state, creating the file if it doesn't exist
        with open(destination_directory + "/" + state + '.yaml', 'w+') as outfile:

            outfile.write("state: " + state + "\n")
            outfile.write("links: " + "\n\n")

            # walk through the URLs for the state, and merge with config from the old YAMLs
            new_config_list = []
            for url_name, url_text in urls.items():
                
                # if there's no URL, that means there was an empty cell in the spreadsheet
                if not url_text:
                    continue

                existing_state_config = existing_config[url_name].get(state)
                
                outfile.write("- name: " + url_name + "\n")
                outfile.write("  url: " + url_text + "\n")

                if existing_state_config:
                    if "overseerScript" in existing_state_config:
                        outfile.write("  overseerScript: |\n")
                        # strip newlines
                        overseer_script = existing_state_config["overseerScript"].strip()
                        # each statement on its own line
                        for command in overseer_script.split(';'):
                            command = command.strip()
                            if '{' in command:
                                command = command.replace('{', '{\n     ')
                            if command:
                                outfile.write("    %s;\n" % command)
                    if "renderSettings" in existing_state_config:
                        outfile.write("  renderSettings: \n    " + yaml.dump(
                            existing_state_config["renderSettings"], default_flow_style=False, indent=6))

                outfile.write("\n")
    


def main(args_list=None):

    state_urls = load_urls_from_live_info('https://covidtracking.com/api/states/info.csv')
    output_yamls("taco", state_urls, 'core_screenshot_config.yaml')

    state_urls = load_urls_from_spreadsheet('https://docs.google.com/spreadsheets/d/1lfwMmo7q-faKfvh6phxQs9rEJXVnnyISFtiVbq9XJ7U/gviz/tq?tqx=out:csv&sheet=Sheet1')
    output_yamls("crdt", state_urls, 'crdt_screenshot_config.yaml')

    state_urls = load_urls_from_spreadsheet('https://docs.google.com/spreadsheets/d/1kB6lT0n4wJ2l8uP-lIOZyIVWCRJTPWLGf3Q4ZCC6pMQ/gviz/tq?tqx=out:csv&sheet=LTC_Screencap_Links')
    output_yamls("ltc", state_urls, 'ltc_screenshot_config.yaml')


    
if __name__ == "__main__":
    main()
