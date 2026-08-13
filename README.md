# The Farmer Was Replaced — AFK starters + afk_farm

Zero-to-AFK scripts for [The Farmer Was Replaced](https://store.steampowered.com/app/2060160/The_Farmer_Was_Replaced/).

**GitHub repo:** https://github.com/PrisonedLotus/the-farmer-was-replaced-afk-farm

Steam guide companion: paste each starter when that crop unlocks, then use **`afk_farm.txt`** once you own **Auto Unlock**.

## Important

`unlock()` / **Auto Unlock** is late on the coding tree:

- **Dictionaries** — 2.5k pumpkins  
- **Costs** (`get_cost()`) — 2.5k pumpkins  
- **Auto Unlock** (`unlock()`) — 5k pumpkins  

Until then, buy unlocks on the tree. Starters 1–5 only farm.

## Files (match in-game window names)

| File | Window name | When to use |
|------|-------------|-------------|
| `starter_1.txt` | `starter_1` | After **Loops** + **Speed** (single-tile hay; no Expand yet) |
| `starter_2.txt` | `starter_2` | **1x3**: bushes → Watering → mixed hay/bush/carrot + water |  
| `starter_3.txt` | `starter_3` | **3x3+**: hay/bush/carrot maintain (after Variables) |  
| `starter_4.txt` | `starter_4` | After **Trees**: sparse tree / hay / carrot |  
| `starter_5.txt` | `starter_5` | After **Pumpkins**: 6x6 pumpkin square + hay-heavy feed rim |  
| `starter_6.txt` | `starter_6` | Only after **Auto Unlock** (auto-buy + deficiency farm) |  
| `afk_farm.txt` | `afk_farm` | Full AFK after `starter_6` (Megafarm optional) |

Also in this repo:

- `steam-guide/` — Steam BBCode sections (one `.txt` per Steam subsection)
- `steam-guide/README.txt` — map of Steam section titles to files
- `NOTES.txt` — maintainer notes for `afk_farm.txt`

## Unlock order (first costs)

1. Loops  
2. Speed — 20 hay  
3. Plant — 50 hay → **starter_1** finishes  
4. Expand 1st — 30 hay → **1x3** (Step 2 bushes / carrots)  
5. Watering — ~50 wood (buy ASAP; faster growth)  
6. Carrots — 50 wood → mixed **1x3** hay + bush + carrot + water  
7. Operators — 150 hay + 10 wood  
8. Senses — 100 hay  
9. Variables — 35 carrots  
10. Expand 2nd — **3x3** → **starter_3** full-farm  
11. Functions — 40 carrots  
12. Trees — 50 wood + 70 carrots → **starter_4**  
13. Lists — 500 carrots  
14. Pumpkins — 500 wood + 200 carrots → **starter_5**  
15. Dictionaries — 2.5k pumpkins  
16. Costs — 2.5k pumpkins  
17. Auto Unlock — 5k pumpkins → **starter_6**, then **afk_farm**  

## How to install afk_farm

1. Finish Unlock Order through **Auto Unlock**.  
2. Confirm `starter_6` runs (buys unlocks + refills hay/wood when low).  
3. Open `afk_farm.txt` → Raw → copy all.  
4. In game, rename a code window to `afk_farm`, paste, run.  
5. **Megafarm is not required** to start; extra drones turn on after you unlock it.

## License

Scripts are provided as-is for players of The Farmer Was Replaced. Do what you want with them in your own save.
