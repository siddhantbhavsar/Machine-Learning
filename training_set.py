import json
import decimal

# Helper class to convert a DynamoDB item to JSON.
class DecimalEncoder(json.JSONEncoder):
    def default(self, o):
        if isinstance(o, decimal.Decimal):
            if o % 1 > 0:
                return float(o)
            else:
                return int(o)
        return super(DecimalEncoder, self).default(o)

class TrainingSet:
    def __init__(self, training_data=None):
        if training_data is not None:
            self.trainingData = training_data
        else:
            self.trainingData = {}

    def get_dict(self):
        return self.trainingData

    def add_image(self, clientId, imageInfo, entryMatch):
        if clientId in self.trainingData:
            self.trainingData[clientId]['images'].append(imageInfo['imageKey'])
            self.trainingData[clientId]['imageCnt'] += 1
        else:
            self.trainingData[clientId] = {}
            self.trainingData[clientId]['images'] = [imageInfo['imageKey']]
            self.trainingData[clientId]['itemName'] = entryMatch['itemName']
            self.trainingData[clientId]['imageCnt'] = 1

    def rm_image(self, clientId, imageKey):
        if clientId in self.trainingData and imageKey in self.trainingData[clientId]['images']:
            self.trainingData[clientId]['images'].remove(imageKey)
            self.trainingData[clientId]['imageCnt'] = len(self.trainingData[clientId]['images'])
        if self.trainingData[clientId]['imageCnt'] == 0:
            del(self.trainingData[clientId])

    def dump_stats(self, sorting='imageCnt', reverse=True):
        if sorted is not None:
            data = list(sorted(self.trainingData, key=lambda x: self.trainingData[x][sorting], reverse=reverse))
        else:
            data = self.trainingData

        for clientId in data:
            print(f"{clientId}: {self.trainingData[clientId]['imageCnt']:3} images - \"{self.trainingData[clientId]['itemName'].strip()}\"")

    def save(self, filename):
        with open(filename, 'w') as outputFile:
            json.dump(self.trainingData, outputFile, indent=4, sort_keys=True)
