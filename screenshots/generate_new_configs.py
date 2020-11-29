import os
import io
import pandas as pd
import requests
import yaml

def load_urls_from_live_info(url):

    content = requests.get(url).content
    state_info_df = pd.read_csv(io.StringIO(content.decode('utf-8')), keep_default_na=False)
    
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

    urls_df = pd.read_csv(csv_url, keep_default_na=False)

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
    destination_directory = "./configs/" + team + "/"
    os.makedirs(destination_directory, exist_ok=True)

    # walk through the states from the spreadsheet
    for state, urls in state_urls.items():

        # walk through the URLs for the state, and merge with config from the old YAMLs
        new_config_list = []
        for urlname, urltext in urls.items():
            
            # if there's no URL, that means there was an empty cell in the spreadsheet
            if(urltext):
                existing_state_config = existing_config[urlname].get(state)
                
                if(existing_state_config): # if there is a config from the previous yaml, use that and add name and url
                    existing_state_config["name"] = urlname
                    existing_state_config["url"] = urltext
                else:  # if not, create a new config with just name and url
                    existing_state_config = { "url": urltext, "name": urlname }

                new_config_list.append(existing_state_config)                
        
        # write the current state to its file, creating the file if it doesn't exist
        with open(destination_directory + state + '.yaml', 'w+') as file:
            documents = yaml.dump(new_config_list, file, default_flow_style=False)


def main(args_list=None):

    state_urls = load_urls_from_live_info('https://covidtracking.com/api/states/info.csv')
    output_yamls("taco", state_urls, 'core_screenshot_config.yaml')

    state_urls = load_urls_from_spreadsheet('https://docs.google.com/spreadsheets/d/1lfwMmo7q-faKfvh6phxQs9rEJXVnnyISFtiVbq9XJ7U/gviz/tq?tqx=out:csv&sheet=Sheet1')
    output_yamls("crdt", state_urls, 'crdt_screenshot_config.yaml')

    state_urls = load_urls_from_spreadsheet('https://docs.google.com/spreadsheets/d/1kB6lT0n4wJ2l8uP-lIOZyIVWCRJTPWLGf3Q4ZCC6pMQ/gviz/tq?tqx=out:csv&sheet=LTC_Screencap_Links')
    output_yamls("ltc", state_urls, 'ltc_screenshot_config.yaml')


    
if __name__ == "__main__":
    main()