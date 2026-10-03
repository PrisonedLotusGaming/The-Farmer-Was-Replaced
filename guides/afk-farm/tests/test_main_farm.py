"""Host-side regression tests; this file is NOT imported by the game script."""
import ast
import copy
from pathlib import Path
import random
import threading
import time
import unittest


class Symbols:
    def __getattr__(self, name):
        return name


SOURCE = Path(__file__).resolve().parents[1] / "afk_farm.txt"


class DroneHandle:
    def __init__(self, fn, state):
        self.fn = fn
        self.state = copy.deepcopy(state)
        self.done = threading.Event()
        self.error = None
        self.joined = False

    def __deepcopy__(self, memo):
        # Drone handles keep identity when passed to another game drone.
        return self


class Farm:
    def __init__(self, size=8, drones=1, locked=()):
        self.size = size
        self.drones = drones
        self.locked = set(locked)
        self.local = threading.local()
        self.lock = threading.RLock()
        self.pos = (0, 0)
        self.time = 0
        self.cells = {}
        self.ground = {}
        self.events = []
        self.jobs = []
        self.max_jobs = 0
        self.random = random.Random(42)
        tree = ast.parse(SOURCE.read_text())
        tree.body = [n for n in tree.body if not isinstance(n, ast.While)]
        self.ns = {name: Symbols() for name in ("Unlocks", "Items", "Entities", "Grounds", "Hats")}
        self.ns.update({d: d for d in ("East", "West", "North", "South")})
        self.ns.update({
            "num_unlocked": lambda u: int(u not in self.locked and (u != "Megafarm" or drones > 1)),
            "num_items": lambda item: 100000,
            "get_cost": lambda entity: {"Hay": 1, "Wood": 1},
            "get_world_size": lambda: size,
            "max_drones": lambda: drones,
            "get_pos_x": lambda: self.pos[0],
            "get_pos_y": lambda: self.pos[1],
            "move": self.move,
            "get_entity_type": self.entity,
            "get_ground_type": lambda: self.ground.get(self.pos, "Grassland"),
            "get_water": lambda: 1,
            "use_item": lambda *args: False,
            "change_hat": lambda hat: None,
            "quick_print": lambda *args: None,
            "can_harvest": self.ready,
            "harvest": self.harvest,
            "plant": self.plant,
            "till": self.till,
            "measure": self.measure,
            "swap": self.swap,
            "spawn_drone": self.spawn,
            "has_finished": self.finished,
            "wait_for": self.wait,
        })
        exec(compile(tree, str(SOURCE), "exec"), self.ns)
        self.states = self.ns["main_farm_states"](size)
        self.owner = {tuple(p): s["kind"] for s in self.states for p in s["tiles"]}

    @property
    def pos(self):
        return getattr(self.local, "pos", (0, 0))

    @pos.setter
    def pos(self, value):
        self.local.pos = value

    def neighbor(self, direction):
        dx, dy = {"East": (1, 0), "West": (-1, 0), "North": (0, 1), "South": (0, -1)}[direction]
        return ((self.pos[0] + dx) % self.size, (self.pos[1] + dy) % self.size)

    def move(self, direction):
        self.time += 1
        self.pos = self.neighbor(direction)
        return True

    def entity(self):
        self.time += 1
        if self.pos not in self.cells and self.ground.get(self.pos, "Grassland") == "Grassland":
            self.cells[self.pos] = ["Grass", self.time + 8, 0]
        return self.cells.get(self.pos, [None])[0]

    def ready(self):
        self.entity()
        cell = self.cells.get(self.pos)
        return bool(cell and cell[0] != "Dead_Pumpkin" and self.time >= cell[1])

    def till(self):
        old = self.ground.get(self.pos, "Grassland")
        self.ground[self.pos] = "Soil" if old == "Grassland" else "Grassland"
        if self.cells.get(self.pos, [None])[0] == "Grass":
            self.cells.pop(self.pos)

    def plant(self, entity):
        if self.cells.get(self.pos, [None])[0] == "Dead_Pumpkin":
            self.cells.pop(self.pos)
        if self.pos in self.cells:
            return False
        self.cells[self.pos] = [entity, self.time + 12, self.random.randrange(10)]
        self.events.append(("plant", entity, self.pos, self.time))
        return True

    def harvest(self):
        entity = self.entity()
        if entity is None:
            return False
        ripe = self.ready()
        if ripe:
            self.events.append(("harvest", entity, self.pos, self.time))
        if ripe and entity in ("Cactus", "Pumpkin"):
            kind = 2 if entity == "Cactus" else 1
            points = [tuple(p) for p in self.states[kind]["tiles"]]
            # Fail on partial or premature special harvests.
            assert all(p in self.cells and self.cells[p][0] == entity and self.cells[p][1] <= self.time for p in points)
            if kind == 2:
                for x, y in points:
                    for q in ((x + 1, y), (x, y + 1)):
                        if q in points:
                            assert self.cells[(x, y)][2] <= self.cells[q][2], "unsorted chain harvest"
            for p in points:
                self.cells.pop(p)
        else:
            self.cells.pop(self.pos, None)
        return True

    def measure(self, direction=None):
        p = self.pos if direction is None else self.neighbor(direction)
        cell = self.cells.get(p)
        return cell[2] if cell and cell[0] in ("Cactus", "Sunflower") else None

    def swap(self, direction):
        q = self.neighbor(direction)
        assert self.owner[self.pos] == self.owner[q] == 2, "cross-region swap"
        self.cells[self.pos], self.cells[q] = self.cells[q], self.cells[self.pos]
        return True

    def spawn(self, fn, state):
        with self.lock:
            if sum(not j.done.is_set() for j in self.jobs) >= self.drones - 1:
                return None
            job = DroneHandle(fn, state)
            self.jobs.append(job)
            self.max_jobs = max(self.max_jobs, sum(not j.done.is_set() for j in self.jobs))
        start = self.pos

        def run():
            self.pos = start
            try:
                job.result = fn(job.state)
            except BaseException as error:
                job.error = error
            finally:
                job.done.set()

        job.thread = threading.Thread(target=run, daemon=True)
        job.thread.start()
        return job

    def finished(self, job):
        if job.error:
            raise job.error
        return job.done.is_set()

    def wait(self, job):
        assert job.done.wait(20), "worker failed to finish"
        if job.error:
            raise job.error
        job.joined = True
        return copy.deepcopy(job.result)


def atomic_game_call(method):
    def wrapped(self, *args):
        # Yield only between API calls, so actual resident loops can overlap.
        if self.drones > 1 and not getattr(self.local, "inside_call", False):
            time.sleep(0)
        with self.lock:
            previous = getattr(self.local, "inside_call", False)
            self.local.inside_call = True
            try:
                assert self.time < 500000, "simulation exceeded its progress budget"
                return method(self, *args)
            finally:
                self.local.inside_call = previous
    return wrapped


for _method in ("move", "entity", "ready", "till", "plant", "harvest", "measure", "swap"):
    setattr(Farm, _method, atomic_game_call(getattr(Farm, _method)))


class MainFarmTests(unittest.TestCase):
    def test_layout_partition(self):
        for size in (1, 3, 4, 8, 10, 12, 16, 32):
            for locked in ((), ("Pumpkins",), ("Cactus",), ("Sunflowers",), ("Pumpkins", "Cactus", "Sunflowers")):
                f = Farm(size, locked=locked)
                points = [tuple(p) for s in f.states for p in s["tiles"]]
                self.assertEqual(len(points), size * size)
                self.assertEqual(len(set(points)), len(points))
                if size >= 3:
                    self.assertTrue(f.states[0]["tiles"])
        f = Farm(8)
        self.assertEqual(len(f.states[1]["tiles"]), 36)
        self.assertEqual(len(f.states[2]["tiles"]), 12)

    def test_sort_converges_for_random_and_reverse_rectangles(self):
        for size in (3, 4, 8, 12, 16):
            for seed in range(12):
                f = Farm(size)
                s = f.states[2]
                rng = random.Random(seed)
                for i, p in enumerate(s["tiles"]):
                    f.ground[tuple(p)] = "Soil"
                    value = rng.randrange(10) if seed else len(s["tiles"]) - i
                    f.cells[tuple(p)] = ["Cactus", 0, value]
                f.ns["main_cactus_start_sort"](s, "rows")
                bound = len(s["tiles"]) * (s["width"] + s["height"] + 8)
                for _ in range(bound):
                    f.ns["main_special_step"](s)
                    if s["cycles"]:
                        break
                self.assertGreater(s["cycles"], 0, (size, seed))
                self.assertTrue(all(f.cells[tuple(p)][0] == "Cactus" for p in s["tiles"]))

    def test_regions_progress_and_workers_drain(self):
        for drones in (1, 2, 3, 4, 8):
            f = Farm(8, drones)
            f.ns["farm_pass"]()
            harvests = [e for e in f.events if e[0] == "harvest"]
            for entity in ("Grass", "Carrot", "Tree", "Pumpkin", "Cactus", "Sunflower"):
                self.assertTrue(any(e[1] == entity for e in harvests), (drones, entity))
            cactus_time = next(e[3] for e in harvests if e[1] == "Cactus")
            self.assertGreater(sum(e[1] == "Sunflower" and e[3] < cactus_time for e in harvests), 1)
            self.assertTrue(all(j.done.is_set() and j.joined for j in f.jobs))
            self.assertLessEqual(f.max_jobs, drones - 1)

    def test_residents_are_spawned_once_and_remaining_capacity_goes_to_cactus(self):
        f = Farm(16, 8)
        calls = []
        original = f.ns["main_farm_work"]

        def work(state):
            calls.append((threading.get_ident(), state["kind"]))
            return original(state)

        f.ns["main_farm_work"] = work
        f.ns["farm_pass"]()
        leaders = [j for j in f.jobs if j.fn.__name__ == "main_farm_leader"]
        residents = [j for j in f.jobs if j.fn.__name__ == "main_farm_resident"]
        batches = [j for j in f.jobs if j.fn.__name__ == "main_cactus_batch"]
        self.assertEqual(len(leaders), 1)
        self.assertEqual(leaders[0].state["team"], 5)
        self.assertEqual(leaders[0].state["state"]["cycles"], 3)
        self.assertEqual(len(residents), 2)
        self.assertEqual(sorted(j.state["states"][0]["kind"] for j in residents), [1, 3])
        for kind in (0, 1, 3):
            self.assertEqual(len({drone for drone, k in calls if k == kind}), 1)
            self.assertGreater(sum(k == kind for _, k in calls), 3)
        # Three full cactus cycles, four coarse phases, four helpers per phase.
        self.assertEqual(len(batches), 3 * 4 * 4)
        self.assertEqual(len(f.jobs), len(batches) + 3)
        self.assertTrue(all(j.done.is_set() and j.joined for j in f.jobs))

    def test_ratio_allocation_counts_main_drone_and_gives_remainder_to_cactus(self):
        f = Farm(32)
        expected = {4: [1, 1, 1, 1], 8: [1, 1, 5, 1],
                    16: [2, 2, 10, 2], 32: [5, 5, 19, 3], 64: [10, 10, 38, 6]}
        for capacity, counts in expected.items():
            self.assertEqual(f.ns["main_farm_allocation"](f.states, capacity), counts)
        for capacity in range(4, 100):
            counts = f.ns["main_farm_allocation"](f.states, capacity)
            self.assertEqual(sum(counts), capacity)
            self.assertTrue(all(n >= 1 for n in counts))
        tiny = Farm(3)
        counts = tiny.ns["main_farm_allocation"](tiny.states, 64)
        for kind in (0, 1, 3):
            self.assertLessEqual(counts[kind], len(tiny.states[kind]["tiles"]))
        self.assertEqual(sum(counts), 64)
        locked = Farm(16, locked=("Sunflowers",))
        self.assertEqual(locked.ns["main_farm_allocation"](locked.states, 32), [5, 5, 22, 0])

    def test_region_partitions_are_disjoint_and_queues_are_private(self):
        f = Farm(16)
        for kind, count in ((0, 5), (1, 5), (3, 3)):
            parts = f.ns["main_region_parts"](f.states[kind], count)
            all_tiles = [tuple(p) for part in parts for p in part["tiles"]]
            self.assertEqual(all_tiles, [tuple(p) for p in f.states[kind]["tiles"]])
            self.assertEqual(len(all_tiles), len(set(all_tiles)))
            self.assertTrue(all(part["tiles"] for part in parts))
            parts[0]["next_pending"].append([-1, -1])
            self.assertTrue(all(not part["next_pending"] for part in parts[1:]))

    def test_32_drone_teams_harvest_and_drain_without_duplicate_region_owners(self):
        f = Farm(16, 32)
        f.ns["farm_pass"]()
        leaders = [j for j in f.jobs if j.fn.__name__ == "main_farm_leader"]
        residents = [j for j in f.jobs if j.fn.__name__ == "main_farm_resident"]
        pumpkin = [j for j in f.jobs if j.fn.__name__ == "main_pumpkin_resident"]
        self.assertEqual(len(leaders), 1)
        self.assertEqual(leaders[0].state["team"], 19)
        self.assertEqual(len(pumpkin), 1)
        self.assertEqual(pumpkin[0].state["team"], 5)
        self.assertGreaterEqual(pumpkin[0].state["state"]["cycles"], 1)
        # Four spawned feed residents plus the main drone, three sunflowers.
        self.assertEqual(sum(j.state["states"][0]["kind"] == 0 for j in residents), 4)
        self.assertEqual(sum(j.state["states"][0]["kind"] == 3 for j in residents), 3)
        for kind in (0, 3):
            owned = [tuple(p) for j in residents for s in j.state["states"]
                     if s["kind"] == kind for p in s["tiles"]]
            self.assertEqual(len(owned), len(set(owned)))
            self.assertTrue(all(f.owner[p] == kind for p in owned))
        for entity in ("Grass", "Carrot", "Tree", "Pumpkin", "Sunflower", "Cactus"):
            self.assertTrue(any(e[:2] == ("harvest", entity) for e in f.events), entity)
        self.assertTrue(all(j.done.is_set() and j.joined for j in f.jobs))
        self.assertLessEqual(f.max_jobs, 31)

    def test_pumpkin_helpers_track_pending_without_harvesting_partial_giants(self):
        f = Farm(8, 8)
        state = f.states[1]
        parts = f.ns["main_region_parts"](state, 5)
        for p in state["tiles"]:
            f.ground[tuple(p)] = "Soil"
            f.cells[tuple(p)] = ["Pumpkin", 0, 0]
        slow = tuple(parts[2]["tiles"][-1])
        f.cells[slow][1] = 1000
        visited = []
        care = f.ns["pumpkin_care_tile"]

        def record():
            visited.append(f.pos)
            return care()

        f.ns["pumpkin_care_tile"] = record
        parts = f.ns["main_pumpkin_stage"](parts, "grow")
        self.assertTrue(all(p["phase"] == "harvest" for p in parts))
        self.assertFalse(any(e[0] == "harvest" for e in f.events))
        for p in state["tiles"]:
            if tuple(p) != slow:
                self.assertEqual(visited.count(tuple(p)), 1)
        self.assertGreater(visited.count(slow), 1)
        f.pos = tuple(state["tiles"][0])
        self.assertTrue(f.harvest())

    def test_parallel_cactus_stages_sort_rectangles(self):
        for size in (3, 8, 12, 16):
            for seed in range(3):
                f = Farm(size, 8)
                s = f.states[2]
                rng = random.Random(seed)
                for i, p in enumerate(s["tiles"]):
                    f.ground[tuple(p)] = "Soil"
                    f.cells[tuple(p)] = ["Cactus", 0, rng.randrange(10) if seed else len(s["tiles"]) - i]
                f.ns["main_cactus_stage"](s, 5, "rows")
                self.assertTrue(all(j.done.is_set() and j.joined for j in f.jobs))
                f.ns["main_cactus_stage"](s, 5, "cols")
                self.assertTrue(f.ns["main_cactus_verified"](s), (size, seed))
                f.pos = (s["x0"], 0)
                self.assertTrue(f.harvest())

    def test_growing_cactus_helpers_remain_alive_across_scans(self):
        f = Farm(12, 8)
        s = f.states[2]
        for p in s["tiles"]:
            f.ground[tuple(p)] = "Soil"
            f.cells[tuple(p)] = ["Cactus", 2000, 0]
        f.ns["main_cactus_stage"](s, 5, "grow")
        self.assertGreaterEqual(f.time, 2000)
        self.assertEqual(len(f.jobs), 4)
        self.assertTrue(all(j.done.is_set() and j.joined for j in f.jobs))

    def test_no_cactus_uses_pumpkin_as_phase_leader(self):
        f = Farm(8, 4, locked=("Cactus",))
        f.ns["farm_pass"]()
        leaders = [j for j in f.jobs if j.fn.__name__ == "main_farm_leader"]
        self.assertEqual(leaders[0].state["state"]["kind"], 1)
        self.assertGreaterEqual(sum(e[:2] == ("harvest", "Pumpkin") for e in f.events), 3)
        self.assertTrue(all(j.done.is_set() and j.joined for j in f.jobs))

    def test_dead_pumpkin_repair_and_replant(self):
        f = Farm(8)
        s = f.states[1]
        for p in s["tiles"]:
            f.ground[tuple(p)] = "Soil"
            f.cells[tuple(p)] = ["Pumpkin", 0, 0]
        f.cells[(2, 2)][0] = "Dead_Pumpkin"
        for _ in range(300):
            f.ns["main_farm_work"](s)
            if s["cycles"] >= 2:
                break
        self.assertGreaterEqual(s["cycles"], 2)
        self.assertTrue(all(f.cells[tuple(p)][0] == "Pumpkin" for p in s["tiles"]))

    def test_pumpkin_tracks_only_unready_tiles_after_initial_scan(self):
        f = Farm(8)
        s = f.states[1]
        for p in s["tiles"]:
            f.ground[tuple(p)] = "Soil"
            f.cells[tuple(p)] = ["Pumpkin", 0, 0]
        slow = [(1, 1), (4, 4)]
        for p in slow:
            f.cells[p][1] = 100000
        visited = []
        care = f.ns["pumpkin_care_tile"]

        def record_care():
            visited.append(f.pos)
            return care()

        f.ns["pumpkin_care_tile"] = record_care
        for _ in s["tiles"]:
            f.ns["main_special_step"](s)
        self.assertEqual(visited, [tuple(p) for p in s["tiles"]])
        self.assertEqual(s["pending"], [list(p) for p in slow])
        visited.clear()
        for _ in range(8):
            f.ns["main_special_step"](s)
        self.assertEqual(visited, slow * 4)
        f.cells[slow[0]][1] = 0
        for _ in range(2):
            f.ns["main_special_step"](s)
        self.assertEqual(s["pending"], [list(slow[1])])
        visited.clear()
        # A pending pumpkin can die; its replacement must stay pending.
        f.cells[slow[1]][0] = "Dead_Pumpkin"
        f.ns["main_special_step"](s)
        self.assertEqual(s["pending"], [list(slow[1])])
        self.assertEqual(f.cells[slow[1]][0], "Pumpkin")
        f.cells[slow[1]][1] = 0
        f.ns["main_special_step"](s)
        self.assertEqual(visited, [slow[1], slow[1]])
        self.assertEqual(s["phase"], "harvest")
        self.assertFalse(any(e[0] == "harvest" for e in f.events))
        f.ns["main_special_step"](s)
        self.assertEqual(s["phase"], "refill")
        self.assertEqual(s["pending"], s["tiles"])
        self.assertEqual(sum(e[:2] == ("harvest", "Pumpkin") for e in f.events), 1)

    def test_pumpkin_refill_retries_only_failed_planting(self):
        f = Farm(8)
        s = f.states[1]
        for p in s["tiles"]:
            f.ground[tuple(p)] = "Soil"
            f.cells[tuple(p)] = ["Pumpkin", 0, 0]
        for _ in range(len(s["tiles"]) + 1):
            f.ns["main_special_step"](s)
        self.assertEqual(s["phase"], "refill")
        missing = (3, 3)
        allowed = False
        plant = f.ns["plant"]

        def limited_plant(entity):
            if f.pos == missing and not allowed:
                return False
            result = plant(entity)
            if result:
                f.cells[f.pos][1] = 100000
            return result

        f.ns["plant"] = limited_plant
        for _ in s["tiles"]:
            f.ns["main_special_step"](s)
        self.assertEqual(s["pending"], [list(missing)])
        self.assertEqual(s["cycles"], 0)
        visited = []
        care = f.ns["pumpkin_care_tile"]

        def record_care():
            visited.append(f.pos)
            return care()

        f.ns["pumpkin_care_tile"] = record_care
        for _ in range(5):
            f.ns["main_special_step"](s)
        self.assertEqual(visited, [missing] * 5)
        allowed = True
        f.ns["main_special_step"](s)
        self.assertEqual(s["cycles"], 1)
        self.assertEqual(s["phase"], "grow")
        self.assertIn(list(missing), s["pending"])
        self.assertEqual(len(s["pending"]), len({tuple(p) for p in s["pending"]}))
        for p in s["tiles"]:
            f.cells[tuple(p)][1] = 0
        for _ in range(len(s["pending"]) + 1):
            f.ns["main_special_step"](s)
        self.assertEqual(sum(e[:2] == ("harvest", "Pumpkin") for e in f.events), 2)

    def test_immature_feed_is_not_destroyed_when_preference_changes(self):
        f = Farm(8)
        f.pos = tuple(f.states[0]["tiles"][0])
        f.cells[f.pos] = ["Carrot", 10000, 0]
        f.ns["main_feed_wanted"] = lambda x, y: "Grass"
        f.ns["main_regular_tile"](0, *f.pos)
        self.assertEqual(f.cells[f.pos][0], "Carrot")

    def test_locked_special_regions(self):
        f = Farm(3, locked=("Pumpkins", "Cactus", "Sunflowers", "Carrots", "Trees"))
        f.ns["farm_pass"]()
        self.assertFalse(any(e[1] in ("Pumpkin", "Cactus", "Sunflower") for e in f.events))

    def test_carrot_input_buffer_scales_with_upgrade_cost(self):
        f = Farm(8)
        f.ns["get_cost"] = lambda entity: {"Hay": 500, "Wood": 200}
        stocks = {"Hay": 150, "Wood": 100000, "Carrot": 0}
        f.ns["num_items"] = lambda item: stocks.get(item, 0)
        self.assertEqual(f.ns["main_feed_wanted"](0, 0), "Grass")
        stocks.update(Hay=100000, Wood=150)
        self.assertEqual(f.ns["main_feed_wanted"](0, 0), "Tree")
        stocks.update(Hay=100000, Wood=100000)
        self.assertEqual(f.ns["main_feed_wanted"](0, 0), "Carrot")

    def test_verification_rejects_unsorted_cactus(self):
        f = Farm(8)
        s = f.states[2]
        for p in s["tiles"]:
            f.ground[tuple(p)] = "Soil"
            f.cells[tuple(p)] = ["Cactus", 0, 0]
        f.cells[tuple(s["tiles"][0])][2] = 9
        s["phase"] = "verify"
        for _ in s["tiles"]:
            f.ns["main_special_step"](s)
        self.assertEqual(s["phase"], "grow")
        self.assertFalse(any(e[0] == "harvest" for e in f.events))


if __name__ == "__main__":
    unittest.main()
