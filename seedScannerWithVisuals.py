from FreeplayExplorer import *
import multiprocessing
import time

def getMeanValues(start, end, tests, load):
    rounds = range(start, end)
    average_RBE = {round: 0 for round in rounds}
    average_BADs = {round: 0 for round in rounds}
    average_FBADs = {round: 0 for round in rounds}
    average_Cash = {round: 0 for round in rounds}
    average_Cash_By_Round = {round: 0 for round in rounds}
    average_total_cash=0
    average_seed=0
    maxSeed=2**31
    if not load:
        for x in range(tests):
            gameCash=0
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
                    gameCash+=round_cash
                    
                    if bloon == "Bad":
                        round_BADs += count
                    if bloon == "BadFortified":
                        round_FBADs += count
                    budget -= score
                average_RBE[ROUND] += round_RBE
                average_Cash[ROUND] += round_cash
                average_Cash_By_Round[ROUND] += gameCash
                average_BADs[ROUND] += round_BADs
                average_FBADs[ROUND] += round_FBADs
            if x%50==0:
                print(x)

        # Divide by the number of seeds to get averages
        input("here")
        for ROUND in rounds:
            average_RBE[ROUND] /= tests
            average_Cash[ROUND] /= tests
            average_BADs[ROUND] /= tests
            average_FBADs[ROUND] /= tests
            average_Cash_By_Round[ROUND] /= tests
        average_total_cash/=tests
        print(f"Got the average values from round {start} to {end}")
        with open("meanValues.json", "w") as f:
            json.dump([average_Cash, average_BADs, average_FBADs, average_Cash_By_Round], f)
    with open("meanValues.json", "r") as f:
        average_Cash, average_BADs, average_FBADs, average_Cash_By_Round = json.load(f)
    return average_Cash, average_BADs, average_FBADs, average_Cash_By_Round

def doSeeds(start, end, avgValues, coreNum, secondsBetweenUpdate, startTime, load, queue):

    while time.perf_counter() < startTime:
        time.sleep(0.5)

    avgCash=avgValues[0]
    avgBADs=avgValues[1]
    avgFBADs=avgValues[2]
    avgTotalCash=avgValues[3]
    highestRoundWithoutBAD=0
    highestRoundWithoutBADSeeds=[]
    allGoodSeeds={}

    initialStart=start
    
    
    if load:
        with open(f"seedScannerJsons2/seedsScanned_{coreNum}.json", "r") as f:
            thing=json.load(f)
            start=thing["seed"]
            highestRoundWithoutBAD=thing["round"]
            highestRoundWithoutBADSeeds=thing["seeds"]
            allGoodSeeds=thing['allGoodSeeds']

    iterable=range(start, end) #tqdm(range(start, end), ascii=True) if doTQDM else range(start, end)
    print(f"Doing from {initialStart}-{end} on core num {coreNum}")

    nextUpdate=time.perf_counter() + secondsBetweenUpdate
    
    for x in iterable:
        if len(allGoodSeeds) == 0:
            print(f"{coreNum} Len of iterable: {len(iterable)}")
        SEED:int = x
        START:int = 141 #logsSave['round']#args.start
        END:int = 600 #logsSave['round']+1#args.end
        ROUND:int = START
        totalCash=0
        
        prev10RoundCash=[]
        avgPrev10RoundCash=[avgCash[f'{i+ROUND}'] for i in range(25)]

        prev10RoundFBADs=[]
        avgPrev10RoundFBADs=[avgFBADs[f'{i+ROUND}'] for i in range(25)]

        prev10RoundBADs=[]
        avgPrev10RoundBADs=[avgBADs[f'{i+ROUND}'] for i in range(25)]

        prev10RoundBADAmount=0
        avgPrev10RoundBADAmount=0
        prev10RoundFBADAmount=0
        avgPrev10RoundFBADAmount=0
        prev10RoundCashAmount=0
        avgPrev10RoundCashAmount=0
        for i in range(25): avgPrev10RoundCashAmount += avgPrev10RoundCash[i]
        for i in range(25): avgPrev10RoundFBADAmount += avgPrev10RoundFBADs[i]
        for i in range(25): avgPrev10RoundBADAmount += avgPrev10RoundBADs[i]
        invalidSeed=False

        if x % 5000 == 0 or x == start:
            
            with open(f"seedScannerJsons2/seedsScanned_{coreNum}.json", "w") as f:
                json.dump({'seed': x, 'round': highestRoundWithoutBAD, 'seeds': highestRoundWithoutBADSeeds, 'allGoodSeeds': allGoodSeeds}, f)
            
        #if x % 10000 == 0:
        #    print(f"Done another 10000 seeds. Up to seed {x} now ({coreNum})")
        if time.perf_counter() > nextUpdate:
            nextUpdate+=secondsBetweenUpdate
            queue.put((coreNum, x, initialStart, end, highestRoundWithoutBAD))
            

        
        while ROUND <= END and not invalidSeed:
            rand = seeded_random(SEED + ROUND)
            budget:float
            if ROUND > 1:
                v = rand.get_next_seed()
                budget = get_budget(ROUND) * (1.5 - v)
            else:
                budget = get_budget(ROUND)
            round_BADs:int = 0
            round_FBADs:int = 0
            round_cash:float = 0.0
            test_groups = list(range(529))
            shuffle_seeded(test_groups, SEED + ROUND)
            for i in test_groups:
                obj:dict = freeplay_groups[i]
                bounds:list = obj["bounds"]
                for j in range(len(bounds)):
                    if bounds[j]["lowerBounds"] <= ROUND <= bounds[j]["upperBounds"]:
                        break
                else:
                    continue
                score:float = get_score(obj, ROUND) if obj['score'] == 0 else obj['score']
                if score > budget: continue
                bloon:str = obj["group"]["bloon"]
                count:int = obj["group"]["count"]
                round_cash += Calculator.get_bloon_cash(bloon, ROUND) * count
                totalCash += round_cash
                if bloon == "Bad":
                    round_BADs+=count
                if bloon == "BadFortified":
                    round_FBADs+=count
                budget -= score
                #print(format_group(i, obj))
            if len(prev10RoundCash) == 25:
                prev10RoundCashAmount=round((prev10RoundCashAmount-prev10RoundCash[0])+round_cash)
                prev10RoundCash.pop(0)
                prev10RoundCash.append(round_cash)
                avgPrev10RoundCashAmount=round((avgPrev10RoundCashAmount-avgPrev10RoundCash[0])+avgCash[f'{ROUND}'])
                avgPrev10RoundCash.pop(0)
                avgPrev10RoundCash.append(avgCash[f'{ROUND}'])

                prev10RoundFBADs.pop(0)
                prev10RoundFBADs.append(round_FBADs)
                prev10RoundFBADAmount=round((prev10RoundFBADAmount-prev10RoundFBADs[0])+round_FBADs)
                avgPrev10RoundFBADAmount=round((avgPrev10RoundFBADAmount-avgPrev10RoundFBADs[0])+avgFBADs[f'{ROUND}'])
                avgPrev10RoundFBADs.pop(0)
                avgPrev10RoundFBADs.append(avgFBADs[f'{ROUND}'])

                prev10RoundBADs.pop(0)
                prev10RoundBADs.append(round_BADs)
                prev10RoundBADAmount=round((prev10RoundBADAmount-prev10RoundBADs[0])+round_BADs)
                avgPrev10RoundBADAmount=round((avgPrev10RoundBADAmount-avgPrev10RoundBADs[0])+avgBADs[f'{ROUND}'])
                avgPrev10RoundBADs.pop(0)
                avgPrev10RoundBADs.append(avgBADs[f'{ROUND}'])
                


                if ROUND < 300:
                    if prev10RoundCashAmount < avgPrev10RoundCashAmount:
                        invalidSeed=True


                    if ROUND < 180:
                        if prev10RoundBADAmount > avgPrev10RoundBADAmount*1.1: #*(1+(0.01*(ROUND-140))):
                            invalidSeed=True
                    elif ROUND > 210:
                        if prev10RoundFBADAmount > avgPrev10RoundFBADAmount:#*0.975:
                            invalidSeed=True
                    
                    #if ROUND > 170:
                        #if totalCash < avgTotalCash[f'{ROUND}'] and prev10RoundCashAmount < avgPrev10RoundCashAmount:
                            #nvalidSeed=True
                        
                            #print(f"Too many FBADs. Got: {prev10RoundFBADAmount} vs avg: {avgPrev10RoundFBADAmount}")

                elif ROUND == 450:
                    if totalCash < avgTotalCash[f'{ROUND}']:
                        invalidSeed=True
                    #if prev10RoundCashAmount < avgPrev10RoundCashAmount*0.8:
                    #    invalidSeed=True
                    #if prev10RoundFBADAmount > avgPrev10RoundFBADAmount*0.9:
                        #invalidSeed=True

                elif ROUND > 450:
                    if prev10RoundFBADAmount > avgPrev10RoundFBADAmount:#*0.98: #max(avgPrev10RoundFBADAmount*0.95, avgPrev10RoundFBADAmount-1.5):
                        invalidSeed=True
                        #print(f"[ Dies because {prev10RoundFBADAmount} vs {avgPrev10RoundFBADAmount}. round: {ROUND} ({coreNum})")
            else:
                prev10RoundCashAmount=round(prev10RoundCashAmount+round_cash)
                prev10RoundCash.append(round_cash)
                prev10RoundFBADAmount=round(prev10RoundFBADAmount+round_FBADs)
                prev10RoundFBADs.append(round_FBADs)
                prev10RoundBADAmount=round(prev10RoundBADAmount+round_BADs)
                prev10RoundBADs.append(round_BADs)
                
            
            if invalidSeed:
                if ROUND > highestRoundWithoutBAD:
                    highestRoundWithoutBAD = ROUND
                    highestRoundWithoutBADSeeds=[SEED]
                    allGoodSeeds[ROUND]=[SEED]
                    with open("highestRound.json", "r") as f:
                        r=json.load(f)
                    with open(f"seedScannerJsons2/seedsScanned_{coreNum}.json", "w") as f:
                        json.dump({'seed': x, 'round': highestRoundWithoutBAD, 'seeds': highestRoundWithoutBADSeeds, 'allGoodSeeds': allGoodSeeds}, f)
                    if ROUND > r["round"]:
                        print(f"-> New overall highest round found: {ROUND} from seed: {SEED} ({coreNum})")
                        with open("highestRound.json", "w") as f:
                            json.dump({"round":ROUND}, f)
                    else:
                        print(f" > New local highest round found: {ROUND} from seed: {SEED} ({coreNum})")
                elif ROUND >= highestRoundWithoutBAD*0.98 and ROUND >= 200:
                    
                    if ROUND in allGoodSeeds:
                        allGoodSeeds[ROUND].append(SEED)
                    else:
                        allGoodSeeds[ROUND]=[SEED]
                    with open("highestRound.json", "r") as f:
                        r=json.load(f)
                    #if ROUND == r["round"]:
                    if ROUND == highestRoundWithoutBAD:
                        highestRoundWithoutBADSeeds.append(SEED)
                        print(f"|Tied for highest round again ({ROUND})! New seed: {SEED}, Amount of seeds: {len(highestRoundWithoutBADSeeds)} ({coreNum})")
                    with open(f"seedScannerJsons2/seedsScanned_{coreNum}.json", "w") as f:
                        json.dump({'seed': x, 'round': highestRoundWithoutBAD, 'seeds': highestRoundWithoutBADSeeds, 'allGoodSeeds': allGoodSeeds}, f)

            if ROUND == 599 and not invalidSeed:
                
                highestRoundWithoutBAD = ROUND
                highestRoundWithoutBADSeeds=[SEED]
                if ROUND in allGoodSeeds:
                    allGoodSeeds[ROUND].append(SEED)
                else:
                    allGoodSeeds[ROUND]=[SEED]
                with open(f"seedScannerJsons2/seedsScanned_{coreNum}.json", "w") as f:
                        json.dump({'seed': x, 'round': highestRoundWithoutBAD, 'seeds': highestRoundWithoutBADSeeds, 'allGoodSeeds': allGoodSeeds}, f)
                print(allGoodSeeds[ROUND])
                print(f"GOT TO ROUND 600! ({coreNum})")
                invalidSeed=True #to break out of the loop

            
            ROUND += 1
    print(f"Highest round without a BAD: {highestRoundWithoutBAD}")
    print(f"Seeds for that round: {highestRoundWithoutBADSeeds}")

def ui_process(queue):
    import pygame as pg

    class coreProgressBar:
        def __init__(self, rect, coreNum):
            self.rect=rect
            self.currSeed=0
            self.coreNum=coreNum
            self.start=0
            self.end=0
            self.bestRound=0
            self.barPercentage=0
        def updateBar(self, seedUpTo, start, end, bestRound):
            self.currSeed=seedUpTo
            self.start=start
            self.end=end
            self.bestRound=bestRound
            self.barPercentage=(self.currSeed-self.start)/(self.end-self.start)
        def renderBar(self, screen:pg.Surface):
            font = pg.font.Font(None, 20)
            coreText = font.render(f"Core #{self.coreNum}", True, (0, 0, 0))
            textRect = coreText.get_rect()
            textRect.center = (self.rect[0]+self.rect[2]/2, self.rect[1]+self.rect[3]*(1/6))
            screen.blit(coreText, textRect)
            surroundingBarRect=[self.rect[0]+self.rect[2]/10, self.rect[1]+(self.rect[3]/3), self.rect[2]-self.rect[2]/5, self.rect[3]/3]
            
            width=self.rect[2]-self.rect[2]/5
            barWidth=width*self.barPercentage
            barRect=[self.rect[0]+self.rect[2]/10, self.rect[1]+(self.rect[3]/3), barWidth, self.rect[3]/3]
            pg.draw.rect(screen, (0, 255, 0), barRect)
            pg.draw.rect(screen, (0, 0, 0), surroundingBarRect, 1)
            percentageDone = font.render(f"{self.barPercentage*100:.4f}%", True, (0, 0, 0))
            textRect = percentageDone.get_rect()
            textRect.center = (self.rect[0]+self.rect[2]/2, self.rect[1]+self.rect[3]/2)
            screen.blit(percentageDone, textRect)
            

            highestRound = font.render(f"Highest round reached: {self.bestRound}", True, (0, 0, 0))
            textRect = highestRound.get_rect()
            textRect.center = (self.rect[0]+self.rect[2]/2, self.rect[1]+self.rect[3]*(3/4))
            screen.blit(highestRound, textRect)

            seedUpToText = font.render(f"Seed: {((self.currSeed-self.start)/1000000):.2f}m/{((self.end-self.start)/1000000):.2f}m", True, (0, 0, 0))
            textRect = seedUpToText.get_rect()
            textRect.center = (self.rect[0]+self.rect[2]/2, self.rect[1]+self.rect[3]*(11/12))
            screen.blit(seedUpToText, textRect)

            pg.draw.rect(screen, (0, 0, 0), self.rect, 1)
    pg.init()

    progressBars=[]
    for x in range(4):
        for y in range(4):
            progressBars.append(coreProgressBar([x*200, y*150, 200, 150], (y*4)+x))

    screen = pg.display.set_mode((800, 600))
    clock = pg.time.Clock()
    pg.display.set_caption("Seed Scanner")

    while True:
        for event in pg.event.get():
            if event.type == pg.QUIT:
                pg.quit()
                return

        # Check if there's data in the queue
        screen.fill((255, 255, 255))
        for bar in progressBars:
            bar.renderBar(screen)
        # Draw your UI elements here
        # ...

        pg.display.flip()
        pg.display.update()
        while not queue.empty():
            #queue.put((coreNum, x, start, end, coreNum, highestRoundWithoutBAD))
            process_id, seedUpTo, start, end, bestRound = queue.get()
            progressBars[process_id].updateBar(seedUpTo, start, end, bestRound)
        
            # Update the UI based on the received data
            # ...

        # Update the pg window
        
        clock.tick(60)

class WorkerProcess(multiprocessing.Process):
    def __init__(self, target, args, queue):
        super().__init__(target=target, args=args)
        self.queue = queue

    def run(self):
        self._target(*self._args, self.queue)

if __name__ == "__main__":

    random.seed(100) #Random seed for consistancy
    cores=16 #Change this to the amount of cores you have
    values = getMeanValues(141, 600, 1000, True) #Change the False to True after the first run
    step=round(((2**31)-1)/cores)

    queue = multiprocessing.Queue()
    ui_process_args = (queue,)
    ui_process_obj = multiprocessing.Process(target=ui_process, args=ui_process_args)
    ui_process_obj.start()

    loadSave = True  # Change to True after the first run if you want to keep going where you left off
    worker_processes = []
    startTime=time.perf_counter()+20
    for x in range(cores):
        args = (step*x, step*(x+1), values, x, 5, startTime, loadSave)
        worker_process = WorkerProcess(target=doSeeds, args=args, queue=queue)
        worker_processes.append(worker_process)

    for worker_process in worker_processes:
        worker_process.start()

    for worker_process in worker_processes:
        worker_process.join()

    ui_process_obj.join()
    