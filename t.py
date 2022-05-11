import requests, threading, re, json, time

totalValues = None
lock = threading.Lock()

with open('config.json','r') as config:
    config = json.load(config)

def rolimons():
    global totalValues
    while True:
        items, data = [], []
        try:
            itemDetails = json.loads(
                re.findall('item_details = (.*?);', requests.get('https://www.rolimons.com/deals').text)[0]
            )
            for item in itemDetails:
                if itemDetails[item][5] == None:
                    items.append(item)
                    data.append(f'{itemDetails[item][2]}/{itemDetails[item][0]}')
                elif itemDetails[item][5] != None:
                    items.append(item)
                    data.append(f'{itemDetails[item][5]}/{itemDetails[item][0]}')
            totalValues = dict(zip(items, data))
            time.sleep(600)
        except:
            continue

threading.Thread(target=rolimons).start()
time.sleep(2)

class Player:
    def __init__(self, userName):
        self.userName = userName
        self.userId = requests.get(f'https://api.roblox.com/users/get-by-username?username={userName}').json()['Id']
        self.firstInventory = []
        self.secondInventory = []

    def firstInventoryCheck(self):
        r = requests.get(f'https://inventory.roblox.com/v1/users/{self.userId}/assets/collectibles?sortOrder=Asc&limit=100').json()
        self.firstInventory = [f"{item['assetId']}:{item['userAssetId']}" for item in r['data']]
        print(self.firstInventory)

    def mainInventoryCheck(self):
        r = requests.get(f'https://inventory.roblox.com/v1/users/{self.userId}/assets/collectibles?sortOrder=Asc&limit=100').json()
        self.secondInventory = [f"{item['assetId']}:{item['userAssetId']}" for item in r['data']]
        print(self.secondInventory)
        self.compareInventories()

    def compareInventories(self):
        itemLost = [item for item in self.firstInventory if not item in self.secondInventory]
        itemGained = [item for item in self.secondInventory if not item in self.firstInventory]
        if itemLost != [] and itemGained != []:
            self.calculateTrade(itemLost, itemGained)

    def calculateTrade(self, itemLost, itemGained):
        myValue = theirValue = 0
        myOffer, theirOffer = [], []

        for item in itemLost:
            assetId, userAssetId = item.split(':',2)
            itemValue, itemName = totalValues[assetId].split('/',2)
            myValue += int(itemValue)
            myOffer.append(f'(**{"{:,}".format(int(itemValue))}**) {itemName}')

        for item in itemGained:
            assetId, userAssetId = item.split(':',2)
            itemValue, itemName = totalValues[assetId].split('/',2)
            theirValue += int(itemValue)
            theirOffer.append(f'(**{"{:,}".format(int(itemValue))}**) {itemName}')

        myOffer, theirOffer = '\n'.join(myOffer), '\n'.join(theirOffer)
        profitAmount, profitPercentage = int(theirValue) - int(myValue), (1 - int(myValue) / int(theirValue)) * 100

        if '.' in str(profitPercentage):
            if len(str(profitPercentage).split('.')[1]) >= 3:
                profitPercentage = round(profitPercentage, 2)

        data = {
            'content': f'<@{config["discordId"]}>',
            'embeds':[{
                'author': {
                    'name': f'New completed on {self.userName}\n\u200b',
                    'url': f'https://www.roblox.com/users/{self.userId}/profile'
                    },
                'color': int('00FF00',16),
                'fields': [
                    {'name': f'📤 Gave: [{"{:,}".format(int(myValue))}]','value': f'{myOffer}\n\u200b','inline':False},
                    {'name': f'📥 Received: [{"{:,}".format(int(theirValue))}]','value': f'{theirOffer}\n\u200b','inline':False},
                    {'name': 'Details:','value': f'\nProfit: {profitAmount} ({profitPercentage}%)','inline':False},
                        ]
                }]
            }
        requests.post(config['discordWebhook'], json=data)
        self.firstInventory = self.secondInventory

    def looping(self):
        self.firstInventoryCheck()
        while True:
            time.sleep(120)
            self.mainInventoryCheck()


for userName in config['userNames']:
    c = Player(userName)
    threading.Thread(target=c.looping).start()
