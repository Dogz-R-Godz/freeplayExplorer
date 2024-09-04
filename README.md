written in java because at least its not python (it is now <:3)

compile with ``javac -cp libs/*; FreeplayExplorer.java``, it likely works on all java versions but my intellij is java 17 while my actual java is java 11 and they both work

for the python version, it relies on the cryptography library ```pip install cryptography```, the zlib library ```pip install zlib```, and the matplotlib library ```pip install matplotlib```

run with  ``java -cp libs/*; FreeplayExplorer 1 263 270``
this shows all rounds between 263 and 270(inclusive) using the seed ``1``

depends on the [Java JSON Library](https://github.com/stleary/JSON-java), in my case i put it in libs/ so thats why its in the classpath

### Files
- ``FreeplayGroups.json``: the raw freeplay groups data from the game
- ``cleanedFreeplayGroups.json``: ``FreeplayGroups.json`` but with the useless fields removed(most importantly each emission is removed, since they are always the same bloon and evenly spaced)(if they're not evenly spaced, the game doesnt care), you can generate the cleaned JSON by running the CleanJSON function in the java file
- ``bloonData.json``: data for the bloons such as cash, rbe, and health

tldr: basically there is no group cap but since the score of spawns is larger than expected

## ok but how does freeplay work, really oversimplified
### if you actually care, just look at the code
- set the ``seed`` to ``round + initialSeed``(the initialSeed is provided in the 1st argument above)
- the ``SeededRandom`` class contains the bare minimum code for the code to run, for full code, look at [here](https://github.com/1330-Studios/SeededRandom_Decomp)
- get the freeplayGroups from the GameModel(if you don't know what GameModel is, don't worry about it)
- shuffle the freeplayGroups using the ``seed``(the ShuffleSeeded function)
- calculate the budget(it starts at 175000 at r100, and increases by 4000 per round after)(pre-round 100 budget is a sight to behold so just look at the code, ``CalculateBudget`` method)
- the budget is multiplied by 0.5 up to 1.5 depending on the ``seed``
- for each freeplayGroup:
  - if it can spawn on the current round(its bounds), continue, otherwise go on to next freeplayGroup
  - calculate the freeplayGroup's score if it is zero, otherwise use the given score(CalculateScore method)
    - start with the base RBE of the bloon(the takes the r1 RBE, so no super ceramics and ramping, even though spawns like BADs can never appear before super cerams do)
    - this is multiplied by the number of spawns
    - if the bloon is ``Camo``, multiply the RBE by 1.1, if the bloon is ``Regrow``, multiply it by 1.1(if it is both, multiply by 1.2)
    - ``spacing = lengthOfFreeplayGroup / 60 / numSpawns``(basically how many seconds between each spawn)
        - spacing on (1, ∞), return RBE * 0.8
        - spacing on [0.5, 1), return RBE
        - spacing on (0.1, 0.5), return RBE * 1.1
        - spacing on (0.08, 0.1], return RBE * 1.4
        - else return RBE * 1.8
        - i prob messed up somewhere but this is just guesswork and seems to be correct since ghidra doesn't show the correct output
  - if the score of the spawn is more than budget remaining, continue to next spawn
  - otherwise accept the spawn and decrease the budget
