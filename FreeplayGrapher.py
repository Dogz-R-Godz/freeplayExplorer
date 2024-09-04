import json
import random
import matplotlib.pyplot as plt
import numpy as np

# Load JSON data
with open("Decrypted_Profile.json", "rb") as f:
    Profile = json.load(f)
logsSave = Profile["savedMaps"]["Logs"]

bloon_data: dict
with open("bloonData.json") as f:
    bloon_data = json.load(f)

freeplay_groups: list[dict]
with open("cleanedFreeplayGroups.json") as f:
    freeplay_groups = json.load(f)

# Define the Calculator class with static methods
class Calculator:
    @staticmethod
    def cash_multiplier(round: int) -> float:
        if round <= 50: return 1
        if round <= 60: return 0.5
        if round <= 85: return 0.2
        if round <= 100: return 0.1
        if round <= 120: return 0.05
        return 0.02
    
    @staticmethod
    def speed_multiplier(round: int) -> float:
        if round <= 80: return 1
        if round <= 100: return 1 + (round - 80) * 0.02
        if round <= 150: return 1.6 + (round - 101) * 0.02
        if round <= 200: return 3 + (round - 151) * 0.02
        if round <= 250: return 4.5 + (round - 201) * 0.02
        return 6 + (round - 252) * 0.02

    @staticmethod
    def health_multiplier(round: int) -> float:
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
    def get_bloon_cash(bloon: str, round: int) -> float:
        freeplay = round > 80
        bloon = bloon.replace("Fortified", "").replace("Camo", "").replace("Regrow", "")
        mult = Calculator.cash_multiplier(round)
        data = bloon_data[bloon]
        if data['isMoab']:
            return mult * data['cash']
        return mult * data["superCash" if freeplay else "cash"]

    @staticmethod
    def get_RBE(bloon: str, round: int) -> int:
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
            return (moab['sumMoabHealth'] * health_mult + moab['numCeramics'] * ceramic_health)
        bloon_d: dict = bloon_data[bloon + ("Fortified" if fortified else "")]
        return bloon_d["superRBE" if freeplay else "RBE"]

# Define the seeded random class
class seeded_random:
    def __init__(self, seed):
        self.seed = seed

    def get_next_seed(self):
        self.seed = (self.seed * 0x41a7) % 0x7FFFFFFF
        value = self.seed / 0x7FFFFFFE
        return value

# Define other helper functions
def shuffle_seeded(l: list, seed: float):
    rand = seeded_random(seed)
    list_len: int = len(l) - 1
    i: int = list_len
    while i >= 0:
        value = rand.get_next_seed()
        index = int(list_len * value)
        l[i], l[index] = l[index], l[i]
        i -= 1

def get_budget(round: int) -> float:
    if round > 100:
        return round * 4000 - 225000
    budget = round ** 7.7
    helper = round ** 1.75
    if round > 50:
        return budget * 5e-11 + helper + 20
    return ((1 + round * 0.01) * (round * -3 + 400) * ((budget * 5e-11 + helper + 20) / 160) * 0.6)

def get_score(model: dict, round: int) -> float:
    bloon: str = model["group"]["bloon"]
    count: int = model["group"]["count"]
    mult: float = 1.0
    if "Camo" in bloon:
        mult += 0.1
        bloon = bloon.replace("Camo", "")
    if "Regrow" in bloon:
        mult += 0.1
        bloon = bloon.replace("Regrow", "")
    RBE: float = Calculator.get_RBE(bloon, round) * mult * count
    if count == 1: return RBE
    spacing: float = model["group"]["end"] / (60 * count)
    if spacing >= 1: return 0.8 * RBE
    if spacing >= 0.5: return RBE
    if spacing > 0.1: return 1.1 * RBE
    if spacing > 0.08: return 1.4 * RBE
    return 1.8 * RBE

rounds = range(logsSave['round'], START = logsSave['round']+50)
average_RBE = {round: 0 for round in rounds}
average_BADs = {round: 0 for round in rounds}
average_FBADs = {round: 0 for round in rounds}
average_Cash = {round: 0 for round in rounds}
average_total_cash=0
average_seed=0
maxSeed=2**31

for x in range(100):
    SEED = random.randint(0, maxSeed)
    average_seed+=SEED
    for ROUND in rounds:
        rand = seeded_random(SEED + ROUND)
        budget = get_budget(ROUND) * (1.5 - rand.get_next_seed())
        round_RBE = 0
        round_cash = 0.0
        round_BADs = 0
        round_FBADs = 0
        test_groups = list(range(529))
        shuffle_seeded(test_groups, SEED + ROUND)
        for i in test_groups:
            obj = freeplay_groups[i]
            bounds = obj["bounds"]
            for j in range(len(bounds)):
                if bounds[j]["lowerBounds"] <= ROUND <= bounds[j]["upperBounds"]:
                    break
            else:
                continue
            score = get_score(obj, ROUND) if obj['score'] == 0 else obj['score']
            if score > budget: continue
            bloon = obj["group"]["bloon"]
            count = obj["group"]["count"]
            round_RBE += Calculator.get_RBE(bloon, ROUND) * count
            round_cash += Calculator.get_bloon_cash(bloon, ROUND) * count
            average_total_cash+=round_cash
            if bloon == "Bad":
                round_BADs += count
            if bloon == "BadFortified":
                round_FBADs += count
            budget -= score
        average_RBE[ROUND] += round_RBE
        average_Cash[ROUND] += round_cash
        average_BADs[ROUND] += round_BADs
        average_FBADs[ROUND] += round_FBADs
    if x%50==0:
        print(x)

# Divide by the number of seeds to get averages
for ROUND in rounds:
    average_RBE[ROUND] /= 100
    average_Cash[ROUND] /= 100
    average_BADs[ROUND] /= 100
    average_FBADs[ROUND] /= 100
average_total_cash/=100
average_seed/=100

# Compute values using the seed from the save file
seed_values_RBE = []
seed_values_BADs = []
seed_values_FBADs = []
seed_values_Cash = []
totalCash=0
SEED = logsSave['freeplayRoundSeed']
START = logsSave['round']

for ROUND in rounds:
    rand = seeded_random(SEED + ROUND)
    budget = get_budget(ROUND) * (1.5 - rand.get_next_seed())
    round_RBE = 0
    round_cash = 0.0
    round_BADs = 0
    round_FBADs = 0 
    test_groups = list(range(529))
    shuffle_seeded(test_groups, SEED + ROUND)
    for i in test_groups:
        obj = freeplay_groups[i]
        bounds = obj["bounds"]
        for j in range(len(bounds)):
            if bounds[j]["lowerBounds"] <= ROUND <= bounds[j]["upperBounds"]:
                break
        else:
            continue
        score = get_score(obj, ROUND) if obj['score'] == 0 else obj['score']
        if score > budget: continue
        bloon = obj["group"]["bloon"]
        count = obj["group"]["count"]
        round_RBE += Calculator.get_RBE(bloon, ROUND) * count
        round_cash += Calculator.get_bloon_cash(bloon, ROUND) * count
        totalCash += round_cash
        if bloon == "Bad":
            round_BADs += count
        if bloon == "BadFortified":
            round_FBADs += count
        budget -= score
    seed_values_RBE.append(round_RBE)
    seed_values_BADs.append(round_BADs)
    seed_values_FBADs.append(round_FBADs)
    seed_values_Cash.append(round_cash)


print(f"Average money between 141 and 200: {average_total_cash}. Money between 141 and 200 on this seed: {totalCash}. You get {totalCash-average_total_cash} more money than the average on this seed. Average seed tested: {average_seed} vs seed of the run: {SEED}")
# Plot the results using Matplotlib
fig = plt.figure(figsize=(14, 10))



# Plot RBE
plt.subplot(2, 2, 1)
plt.plot(rounds, [average_RBE[round] for round in rounds], color='green', label='Average RBE')
plt.plot(rounds, seed_values_RBE, color='red', label='Seed RBE')
plt.xlabel('Round')
plt.ylabel('RBE')
plt.title('RBE per Round')
plt.grid()
plt.legend()

# Plot BADs
plt.subplot(2, 2, 2)
plt.plot(rounds, [average_BADs[round] for round in rounds], color='green', label='Average BADs')
plt.plot(rounds, seed_values_BADs, color='red', label='Seed BADs')
plt.xlabel('Round')
plt.ylabel('BADs (#)')
plt.title('BADs per Round')
plt.grid()
plt.legend()

# Plot F-BADs
plt.subplot(2, 2, 3)
plt.plot(rounds, [average_FBADs[round] for round in rounds], color='green', label='Average F-BADs')
plt.plot(rounds, seed_values_FBADs, color='red', label='Seed F-BADs')
plt.xlabel('Round')
plt.ylabel('F-BADs (#)')
plt.title('F-BADs per Round')
plt.grid()
plt.legend()

# Plot Cash
plt.subplot(2, 2, 4)
plt.plot(rounds, [average_Cash[round] for round in rounds], color='green', label='Average Cash')
plt.plot(rounds, seed_values_Cash, color='red', label='Seed Cash')
plt.xlabel('Round')
plt.ylabel('Cash')
plt.title('Cash per Round')
plt.grid()
plt.legend()

plt.tight_layout()
plt.show()
