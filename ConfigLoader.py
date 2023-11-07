import os
import json


class ConfigLoader:
    def __init__(self, configPath: str = "config"):
        self.configPath = configPath
        self.config = {}
        self.loadConfig()

    def loadConfig(self):
        for root, dirs, files in os.walk(self.configPath):
            for file in files:
                if file.endswith(".json"):
                    filePath = os.path.join(root, file)
                    with open(filePath, "r") as jsonFile:
                        try:
                            data = json.load(jsonFile)
                            self.config[file.split(".")[0]] = data
                        except:
                            print(f"Error loading JSON file {file}")

    def saveConfig(self, firstKey: str, data: dict):
        path="{}/{}.json".format(self.configPath, firstKey)
        print(path)
        with open(path, "w") as file:
            json.dump(data, file, indent=4)
        self.loadConfig()
