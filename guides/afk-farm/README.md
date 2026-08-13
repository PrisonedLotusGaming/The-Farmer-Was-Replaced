# AFK farm — starters + afk_farm

Scripts for the AFK path in The Farmer Was Replaced. Full walkthrough lives in the Steam guide.

**Steam guide:** _link coming soon_ 

**Repo path:** `guides/afk-farm/`

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
| `starter_5.txt` | `starter_5` | After **Pumpkins**: pumpkin square + hay-heavy feed rim |
| `starter_6.txt` | `starter_6` | Only after **Auto Unlock** (auto-buy + deficiency farm) |
| `afk_farm.txt` | `afk_farm` | Full AFK after `starter_6` (Megafarm optional) |

## How to install afk_farm

1. Finish Unlock Order through **Auto Unlock**.  
2. Confirm `starter_6` runs (buys unlocks + refills hay/wood when low).  
3. Open `afk_farm.txt` → Raw → copy all.  
4. In game, rename a code window to `afk_farm`, paste, run.  
5. **Megafarm is not required** to start; extra drones turn on after you unlock it.

## License

Scripts are provided as-is for players of The Farmer Was Replaced. Do what you want with them in your own save.
