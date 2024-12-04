import json
import argparse
import random

with open("tempSave.json", "rb") as f:
    Profile=json.load(f)
#logsSave=Profile["savedMaps"]["Logs"]

number = int|float

bloon_data:dict
with open("bloonDataOld.json") as f:
    bloon_data = json.load(f)

freeplay_groups:list[dict]
with open("cleanedFreeplayGroups.json") as f:
    freeplay_groups = json.load(f)

class Calculator:
    @staticmethod
    def cash_multiplier(round:int) -> number:
        if round <= 50: return 1
        if round <= 60: return 0.5
        if round <= 85: return 0.2
        if round <= 100: return 0.1
        if round <= 120: return 0.05
        return 0.02
    @staticmethod
    def speed_multiplier(round:int) -> number:
        if round <= 80: return 1
        if round <= 100: return 1 + (round - 80) * 0.02
        if round <= 150: return 1.6 + (round - 101) * 0.02
        if round <= 200: return 3 + (round - 151) * 0.02
        if round <= 250: return 4.5 + (round - 201) * 0.02
        return 6 + (round - 252) * 0.02
    @staticmethod
    def health_multiplier(round) -> number:
        if round <= 80: return 1
        if round <= 100: return (round - 30) / 50
        if round <= 124: return (round - 72) / 20
        if round <= 150: return (3 * round - 320) / 20
        if round <= 250: return (7 * round - 920) / 20
        if round <= 300: return round - 208.5
        if round <= 400: return (3 * round - 717) / 2
        if round <= 500: return (5 * round - 1517) / 2
        return 5 * round - 2008.5
    @staticmethod
    def get_bloon_cash(bloon:str, round:int) -> number:
        freeplay = round > 80
        bloon = bloon.replace("Fortified", "").replace("Camo", "").replace("Regrow", "")
        mult = Calculator.cash_multiplier(round)
        data = bloon_data[bloon]
        if data['isMoab']:
            return mult * data['cash']
        return mult * data["superCash" if freeplay else "cash"]
    @staticmethod
    def get_RBE(bloon:str, round:int) -> int:
        health_mult = Calculator.health_multiplier(round)
        fortified = "Fortified" in bloon
        freeplay = round > 80
        bloon = bloon.replace("Fortified", "").replace("Camo", "").replace("Regrow", "")
        moab = bloon_data[bloon]
        if fortified:
            health_mult *= 2
            ceramic_health = bloon_data['CeramicFortified']["superRBE" if freeplay else "RBE"]
        else:
            ceramic_health = bloon_data['Ceramic']["superRBE" if freeplay else "RBE"]
        if moab['isMoab']:
            return (moab['sumMoabHealth'] * health_mult +
                    moab['numCeramics'] * ceramic_health)
        bloon_d:dict = bloon_data[bloon + ("Fortified" if fortified else "")]
        return bloon_d["superRBE" if freeplay else "RBE"]

class seeded_random:
    def __init__(self, seed):
        self.seed = seed
    def get_next_seed(self):
        self.seed = (self.seed * 0x41a7) % 0x7FFFFFFF
        value = self.seed / 0x7FFFFFFE
        return value

def format_group(i:int, obj:dict) -> str:
    group = obj["group"]
    return f"| {group['bloon']:<16} |{i:<5}|{group['count']:<10} |{group['end']:<16} |"

def shuffle_seeded(l:list, seed:number):
    rand = seeded_random(seed)
    list_len:int = len(l) - 1
    i:int = list_len
    while True:
        value = rand.get_next_seed()
        index = int(list_len * value)
        liOld = l[i]
        lIndexOld = l[index]
        l[i] = lIndexOld
        l[index] = liOld
        #l[i], l[index] = lIndexOld, liOld
        i -= 1
        if (i < 0):
            return

def get_budget(round:int):
    if round > 100:
        return round * 4000 - 225000
    budget = round ** 7.7
    helper = round ** 1.75
    if round > 50:
        return budget * 5e-11 + helper + 20
    return ((1 + round * 0.01) * (round * -3 + 400) * ((budget * 5e-11 + helper + 20) / 160) * 0.6)


def get_score(model:dict, round:int) -> number:
    bloon:str = model["group"]["bloon"]
    count:int = model["group"]["count"]
    mult:float = 1.0
    if "Camo" in bloon:
        mult += 0.1
        bloon = bloon.replace("Camo", "")
    if "Regrow" in bloon:
        mult += 0.1
        bloon = bloon.replace("Regrow", "")
    RBE:number = Calculator.get_RBE(bloon, round) * mult * count
    if count == 1: return RBE
    spacing:float = model["group"]["end"] / (60 * count)
    if spacing >= 1: return 0.8 * RBE
    if spacing >= 0.5: return RBE
    if spacing > 0.1: return 1.1 * RBE
    if spacing > 0.08: return 1.4 * RBE
    return 1.8 * RBE

def main() -> None:
    #parser = argparse.ArgumentParser()
    #parser.add_argument("seed", type=int)
    #parser.add_argument("start", type=int)
    #parser.add_argument("end", type=int)
    #args = parser.parse_args()
    SEED:int = int(input("Put in your seed here -> "))#178515437 #134_535_324  #logsSave['freeplayRoundSeed']#args.seed
    START:int = 140 #logsSave['round']#args.start
    END:int = 145    #logsSave['round']+10#args.end
    ROUND:int = START
    total_RBE:int = 0
    total_cash:float = 0.0
    total_time:int = 0
    total_BADs:int = 0
    total_FBADs:int = 0
    while ROUND <= END:
        rand = seeded_random(SEED + ROUND)
        budget:float
        if ROUND > 1:
            v = rand.get_next_seed()
            initialBudget = get_budget(ROUND) 
            budget = (initialBudget - (v - 0.5))*initialBudget
            #budget = get_budget(ROUND) * (v-0.5)
        else:
            budget = get_budget(ROUND)
        original_budget = budget
        round_RBE:int = 0
        round_BADs:int = 0
        round_FBADs:int = 0
        round_cash:float = 0.0
        round_time:int = 0
        test_groups = list(range(529))
        seedPlusRound=SEED + ROUND
        shuffle_seeded(test_groups, seedPlusRound)
        print("+"+"-"*54+"+")
        print(f"| ROUND {ROUND:<46} |")
        print(f"+{'-'*18}+{'-'*17}+{'-'*17}+")
        print(f"|{' '*12}Bloon |Group|     Count |{' '*10}Length |")
        print(f"+{'-'*18}+{'-'*17}+{'-'*17}+")
        for i in test_groups:
            obj:dict = freeplay_groups[i]
            bounds:list = obj["bounds"]
            for j in range(len(bounds)):
                if bounds[j]["lowerBounds"] <= ROUND and ROUND <= bounds[j]["upperBounds"]:
                    break
            else:
                continue
            score:float = get_score(obj, ROUND) if obj['score'] == 0 else obj['score']
            if score > budget: continue
            bloon:str = obj["group"]["bloon"]
            count:int = obj["group"]["count"]
            round_RBE += Calculator.get_RBE(bloon, ROUND) * count
            round_cash += Calculator.get_bloon_cash(bloon, ROUND) * count

            if bloon == "Bad":
                round_BADs+=count
            if bloon == "BadFortified":
                round_FBADs+=count
            round_time += obj["group"]["end"]
            budget -= score
            print(format_group(i, obj))
        print("+"+"-"*54+"+")
        print(f"| {f'Score budget: {original_budget-budget:,.2f}/{original_budget:,.2f}':<52} |")
        print(f"| {f'Score Multiplier: {v:,.5f}':<52} |")
        print(f"| {f'Round RBE: {round_RBE:,}':<52} |")
        print(f"| {f'Round Cash: {round_cash:,.2f}':<52} |")
        print(f"| {f'Round BADs: {round_BADs:,}':<52} |")
        print(f"| {f'Round FBADs: {round_FBADs:,}':<52} |")
        print(f"| {f'Round Length: {round_time:,}':<52} |")
        print(f"| {f'Health Multiplier: {Calculator.health_multiplier(ROUND)}':<52} |")
        print(f"| {f'Speed Multiplier: {Calculator.speed_multiplier(ROUND)}':<52} |")
        ROUND += 1
        total_cash += round_cash
        total_RBE += round_RBE
        total_time += round_time
        total_FBADs += round_FBADs
        total_BADs += round_BADs
    print("+"+"-"*54+"+")
    print(f"| {f'Total RBE: {total_RBE:,}':<52} |")
    print(f"| {f'Total Cash: {total_cash:,.2f}':<52} |")
    print(f"| {f'Total BADs: {total_BADs:,}':<52} |")
    print(f"| {f'Total FBADs: {total_FBADs:,}':<52} |")
    print(f"| {f'Total Length: {total_time:,}':<52} |")
    print(f"| {f'Health Multiplier: {Calculator.health_multiplier(ROUND)}':<52} |")
    print(f"| {f'Speed Multiplier: {Calculator.speed_multiplier(ROUND)}':<52} |")
    print("+"+"-"*54+"+")

if __name__ == "__main__":
    main()
