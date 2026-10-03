# AFK farm — starters + afk_farm

Scripts for the AFK path in The Farmer Was Replaced. Full walkthrough lives in the Steam guide.

**Steam guide:** (https://steamcommunity.com/sharedfiles/filedetails/?id=3782754112)

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

## Main-farm drone teams

The mixed-crop, pumpkin, sunflower, and cactus regions run independently during
main-farm mode. Mixed crops and sunflowers use resident drones assigned to
non-overlapping tile ranges. Pumpkin and cactus helpers work on whole growth,
planting, or sorting stages rather than being recreated every few tiles.

The default allocation includes the main drone:

| Region | Target | Example with 32 drones |
|--------|--------|------------------------|
| Mixed crops | 15% | 5 |
| Pumpkins | 15% | 5 |
| Sunflowers | 10% | 3 |
| Cactus | Remaining capacity | 19 |

Adjust `FARM_FEED_PERCENT`, `FARM_PUMPKIN_PERCENT`, and
`FARM_SUNFLOWER_PERCENT` near the top of `afk_farm.txt`. Percentages round to
nearest whole drones; active regions receive at least one when capacity permits.
Locked/empty regions receive none. With fewer drones, the script shares local
work without repeatedly spawning small tasks. Sorting concurrency is limited
to the number of independent rows or columns.

Pumpkin workers scan their ranges once, then revisit only unresolved tiles.
One coordinator harvests after every range is ready. Cactus workers finish all
row sorts before column sorts, verify the complete rectangle, then chain-harvest.
Both regions replant after harvest; sunflowers harvest and replant continuously.
On 8x8 farms, the 6x6 pumpkin square and 2x6 cactus rectangle do not overlap.

The main-farm phase spans `farm_pass_count()` leader cycles (cactus when active),
then drains all workers before upgrades, expansion, dinosaurs, or mazes.
Every active region completes at least one cycle before exit. The standalone
power-restock, dinosaur, and maze routines are unchanged.

## Host-side regression tests

Run from the repository root with Python 3:

```sh
python -m unittest discover -s guides/afk-farm/tests -v
```

These tests simulate the game API, isolated drone state, crop readiness, and
harvest ordering. They are development tools, not files to paste into the game.
Passing them does not replace in-game compatibility and performance testing.

## License

Scripts are provided as-is for players of The Farmer Was Replaced. Do what you want with them in your own save.
