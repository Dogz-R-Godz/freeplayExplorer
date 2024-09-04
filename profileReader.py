import json

with open("Decrypted_Profile.json", "rb") as f:
    Profile=json.load(f)

logsSave=Profile["savedMaps"]["Logs"]

placedTowers=logsSave["placedTowers"]

totalPopCount=0

for tower in placedTowers:
    popCount=tower["damageDealt"]
    totalPopCount+=popCount

x=0
with open("Decrypted_Profile.json", "rb") as f:
    ProfileOld=json.load(f)

logsSaveOld=ProfileOld["savedMaps"]["Logs"]

placedTowersOld=logsSaveOld["placedTowers"]

totalPopCountOld=0

for tower in placedTowersOld:
    popCount=tower["damageDealt"]
    totalPopCountOld+=popCount

x=0