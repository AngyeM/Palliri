import json
with open('config.json') as config_file:
    config = json.load(config_file)

MONGO=config["MONGO"]
REDIS=config["REDIS"]
MAIL=config["MAIL"]