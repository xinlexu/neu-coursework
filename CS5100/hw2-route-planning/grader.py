#!/usr/bin/python3

import json
from typing import List, Optional, Type
from math import radians

import graderUtil
import util
from mapUtil import (
    CityMap,
    checkValid,
    createGridMap,
    createGridMapWithCustomTags,
    createSanJoseMap,
    getTotalCost,
    locationFromTag,
    makeGridLabel,
    makeTag, RADIUS_EARTH
)

grader = graderUtil.Grader()
submission = grader.load("submission")


def extractPath(startLocation: str, search: util.SearchAlgorithm) -> List[str]:
    """
    Assumes that `solve()` has already been called on the `searchAlgorithm`.

    We extract a sequence of locations from `search.path` (see util.py to better
    understand exactly how this list gets populated).
    """
    return [startLocation] + search.actions


def printPath(
    path: List[str],
    waypointTags: List[str],
    cityMap: CityMap,
    outPath: Optional[str] = "path.json",
):
    # doneWaypointTags = set()
    # for location in path:
    #     for tag in cityMap.tags[location]:
    #         if tag in waypointTags:
    #             doneWaypointTags.add(tag)
    #     tagsStr = " ".join(cityMap.tags[location])
    #     doneTagsStr = " ".join(sorted(doneWaypointTags))
    #     print(f"Location {location} tags:[{tagsStr}]; done:[{doneTagsStr}]")
    # print(f"Total distance: {getTotalCost(path, cityMap)}")

    # (Optional) Write path to file, for use with `visualize.py`
    if outPath is not None:
        with open(outPath, "w") as f:
            data = {"waypointTags": waypointTags, "path": path}
            json.dump(data, f, indent=2)


# Instantiate the San Jose Map as a constant --> just load once!
sanJoseMap = createSanJoseMap()

########################################################################################
# Problem 0: Grid City

grader.add_manual_part("0a", max_points=2, description="minimum cost path")
grader.add_manual_part("0b", max_points=3, description="UCS basic behavior")
grader.add_manual_part("0c", max_points=3, description="UCS search behavior")

########################################################################################
# Problem 1a: Modeling the Shortest Path Problem.


def t_1a(
    cityMap: CityMap,
    startLocation: str,
    endTag: str,
    expectedCost: Optional[float] = None,
):
    """
    Run UCS on a ShortestPathProblem, specified by
        (startLocation, endTag).
    Check that the cost of the minimum cost path is `expectedCost`.
    """
    ucs = util.UniformCostSearch(verbose=0)
    ucs.solve(submission.ShortestPathProblem(startLocation, endTag, cityMap))
    path = extractPath(startLocation, ucs)
    grader.require_is_true(checkValid(path, cityMap, startLocation, endTag, []))
    if expectedCost is not None:
        # print(getTotalCost(path, cityMap))
        grader.require_is_equal(expectedCost, getTotalCost(path, cityMap))



grader.add_basic_part(
    "1a-1-basic",
    lambda: t_1a(
        cityMap=createGridMap(3, 5),
        startLocation=makeGridLabel(0, 0),
        endTag=makeTag("label", makeGridLabel(2, 2)),
        expectedCost=4,
    ),
    max_points=0.5,
    max_seconds=1,
    description="shortest path on small grid",
)


grader.add_basic_part(
    "1a-2-basic",
    lambda: t_1a(
        cityMap=createGridMap(30, 30),
        startLocation=makeGridLabel(20, 10),
        endTag=makeTag("x", "5"),
        expectedCost=15,
    ),
    max_points=0.5,
    max_seconds=1,
    description="shortest path with multiple end locations",
)

grader.add_hidden_part(
    "1a-3-hidden",
    lambda: t_1a(
        cityMap=createGridMap(100, 100),
        startLocation=makeGridLabel(0, 0),
        endTag=makeTag("label", makeGridLabel(99, 99)),
    ),
    max_points=0.5,
    max_seconds=1,
    description="shortest path with larger grid",
)

# Problem 1a (continued): full SanJose map...
grader.add_basic_part(
    "1a-4-basic",
    lambda: t_1a(
        cityMap=sanJoseMap,
        startLocation=locationFromTag(makeTag("landmark", "northeastern_building"), sanJoseMap),
        endTag=makeTag("landmark", "starbucks"),
        expectedCost=408.4764735275154,
    ),
    max_points=0.5,
    max_seconds=1,
    description="basic shortest path test case (1a-4)",
)

grader.add_basic_part(
    "1a-5-basic",
    lambda: t_1a(
        cityMap=sanJoseMap,
        startLocation=locationFromTag(makeTag("landmark", "san_pedro_market"), sanJoseMap),
        endTag=makeTag("landmark", "bus_station"),
        expectedCost=452.80327743516983,
    ),
    max_points=0.5,
    max_seconds=1,
    description="basic shortest path test case (1a-5)",
)

grader.add_basic_part(
    "1a-6-basic",
    lambda: t_1a(
        cityMap=sanJoseMap,
        startLocation=locationFromTag(makeTag("landmark", "philz"), sanJoseMap),
        endTag=makeTag("landmark", "northeastern_building"),
        expectedCost=776.188935771376,
    ),
    max_points=0.5,
    max_seconds=1,
    description="basic shortest path test case (1a-6)",
)

grader.add_hidden_part(
    "1a-7-hidden",
    lambda: t_1a(
        cityMap=sanJoseMap,
        startLocation=locationFromTag(makeTag("landmark", "grocery_outlet"), sanJoseMap),
        endTag=makeTag("landmark", "cathedral_basilica"),
    ),
    max_points=0.5,
    max_seconds=1,
    description="hidden shortest path test case (1a-7)",
)

grader.add_hidden_part(
    "1a-8-hidden",
    lambda: t_1a(
        cityMap=sanJoseMap,
        startLocation=locationFromTag(makeTag("landmark", "city_hall"), sanJoseMap),
        endTag=makeTag("landmark", "seven_eleven"),
    ),
    max_points=0.5,
    max_seconds=1,
    description="hidden shortest path test case (1a-8)",
)

########################################################################################
# Problem 1b: Custom -- Plan a Route through San Jose


def t_1b_custom():
    """Given custom ShortestPathProblem, output path for visualization."""
    problem = submission.getSanJoseShortestPathProblem()
    ucs = util.UniformCostSearch(verbose=0)
    ucs.solve(problem)
    path = extractPath(problem.startLocation, ucs)
    printPath(path=path, waypointTags=[], cityMap=problem.cityMap)
    grader.require_is_true(
        checkValid(path, problem.cityMap, problem.startLocation, problem.endTag, [])
    )


grader.add_basic_part(
    "1b-custom",
    t_1b_custom,
    max_points=3,
    max_seconds=10,
    description="customized shortest path through San Jose",
)


# ########################################################################################
# Problem 1c: Externalities
grader.add_manual_part("1c", max_points=3, description="externalities of algorithm")


########################################################################################
# Problem 2a: Modeling the Waypoints Shortest Path Problem.


def t_2ab(
    cityMap: CityMap,
    startLocation: str,
    endTag: str,
    waypointTags: List[str],
    expectedCost: Optional[float] = None,
):
    """
    Run UCS on a WaypointsShortestPathProblem, specified by
        (startLocation, waypointTags, endTag).
    """
    ucs = util.UniformCostSearch(verbose=0)
    problem = submission.WaypointsShortestPathProblem(
        startLocation,
        waypointTags,
        endTag,
        cityMap,
    )
    ucs.solve(problem)
    grader.require_is_true(ucs.pathCost is not None)
    path = extractPath(startLocation, ucs)
    grader.require_is_true(
        checkValid(path, cityMap, startLocation, endTag, waypointTags)
    )
    if expectedCost is not None:
        # print(getTotalCost(path, cityMap))
        grader.require_is_equal(expectedCost, getTotalCost(path, cityMap))



grader.add_basic_part(
    "2a-1-basic",
    lambda: t_2ab(
        cityMap=createGridMap(3, 5),
        startLocation=makeGridLabel(0, 0),
        waypointTags=[makeTag("y", 4)],
        endTag=makeTag("label", makeGridLabel(2, 2)),
        expectedCost=8,
    ),
    max_points=0.5,
    max_seconds=3,
    description="shortest path on small grid with 1 waypoint",
)

grader.add_basic_part(
    "2a-2-basic",
    lambda: t_2ab(
        cityMap=createGridMap(30, 30),
        startLocation=makeGridLabel(20, 10),
        waypointTags=[makeTag("x", 5), makeTag("x", 7)],
        endTag=makeTag("label", makeGridLabel(3, 3)),
        expectedCost=24.0,
    ),
    max_points=0.5,
    max_seconds=3,
    description="shortest path on medium grid with 2 waypoints",
)

grader.add_basic_part(
    "2a-3-basic",
    lambda: t_2ab(
        cityMap=createGridMapWithCustomTags(2, 2, {(0,0): [], (0,1): ["food", "fuel", "books"], (1,0): ["food"], (1,1): ["fuel"]}),
        startLocation=makeGridLabel(0, 0),
        waypointTags=[
            "food", "fuel", "books"
        ],
        endTag=makeTag("label", makeGridLabel(0, 1)),
        expectedCost=1.0,
    ),
    max_points=0.5,
    max_seconds=3,
    description="shortest path with 3 waypoints and some locations covering multiple waypoints",
)

grader.add_basic_part(
    "2a-4-basic",
    lambda: t_2ab(
        cityMap=createGridMapWithCustomTags(2, 2, {(0,0): ["food"], (0,1): ["fuel"], (1,0): ["food"], (1,1): ["food", "fuel"]}),
        startLocation=makeGridLabel(0, 0),
        waypointTags=[
            "food", "fuel"
        ],
        endTag=makeTag("label", makeGridLabel(0, 1)),
        expectedCost=1.0,
    ),
    max_points=0.5,
    max_seconds=3,
    description="shortest path with 3 waypoints and start location covering some waypoints",
)

grader.add_hidden_part(
    "2a-5-hidden",
    lambda: t_2ab(
        cityMap=createGridMap(100, 100),
        startLocation=makeGridLabel(0, 0),
        waypointTags=[
            makeTag("x", 90),
            makeTag("x", 95),
            makeTag("label", makeGridLabel(3, 99)),
            makeTag("label", makeGridLabel(99, 3)),
        ],
        endTag=makeTag("y", 95),
    ),
    max_points=1,
    max_seconds=3,
    description="shortest path with 4 waypoints and multiple end locations",
)

# Problem 2a (continued): full San Jose map...
grader.add_basic_part(
    "2a-6-basic",
    lambda: t_2ab(
        cityMap=sanJoseMap,
        startLocation=locationFromTag(makeTag("landmark", "philz"), sanJoseMap),
        waypointTags=[makeTag("landmark", "northeastern_building")],
        endTag=makeTag("landmark", "bus_station"),
        expectedCost=988.5491769095205,
    ),
    max_points=0.5,
    max_seconds=3,
    description="basic waypoints test case (2a-4)",
)

grader.add_basic_part(
    "2a-7-basic",
    lambda: t_2ab(
        cityMap=sanJoseMap,
        startLocation=locationFromTag(makeTag("landmark", "city_hall"), sanJoseMap),
        waypointTags=[
            makeTag("landmark", "northeastern_building"),
            makeTag("landmark", "dac_phunk"),
            makeTag("landmark", "seven_eleven"),
        ],
        endTag=makeTag("landmark", "bus_station"),
        expectedCost=1799.284736048278,
    ),
    max_points=0.5,
    max_seconds=3,
    description="basic waypoints test case (2a-5)",
)

grader.add_basic_part(
    "2a-8-basic",
    lambda: t_2ab(
        cityMap=sanJoseMap,
        startLocation=locationFromTag(makeTag("landmark", "grocery_outlet"), sanJoseMap),
        waypointTags=[
            makeTag("landmark", "olla_cocina"),
            makeTag("landmark", "seven_eleven"),
            makeTag("landmark", "philz"),
            makeTag("landmark", "city_hall"),
        ],
        endTag=makeTag("landmark", "san_jose_state"),
        expectedCost=2299.2920486046605,
    ),
    max_points=1,
    max_seconds=3,
    description="basic waypoints test case (2a-6)",
)

grader.add_hidden_part(
    "2a-9-hidden",
    lambda: t_2ab(
        cityMap=sanJoseMap,
        startLocation=locationFromTag(makeTag("landmark", "grocery_outlet"), sanJoseMap),
        waypointTags=[
            makeTag("landmark", "dac_phunk"),
            makeTag("landmark", "seven_eleven"),
            makeTag("landmark", "san_pedro_market"),
        ],
        endTag=makeTag("landmark", "northeastern_building"),
    ),
    max_points=0.5,
    max_seconds=3,
    description="hidden waypoints test case (2a-7)",
)

grader.add_hidden_part(
    "2a-10-hidden",
    lambda: t_2ab(
        cityMap=sanJoseMap,
        startLocation=locationFromTag(makeTag("landmark", "cathedral_basilica"), sanJoseMap),
        waypointTags=[
            makeTag("landmark", "starbucks"),
            makeTag("landmark", "philz"),
            makeTag("landmark", "bus_station"),
        ],
        endTag=makeTag("landmark", "starbucks"),
    ),
    max_points=0.5,
    max_seconds=3,
    description="hidden waypoints test case (2a-8)",
)


########################################################################################
# Problem 2b: Maximum states with waypoints
grader.add_manual_part("2b", max_points=2, description="max states with waypoints")


########################################################################################
# Problem 2c: Custom -- Plan a Route with Unordered Waypoints through San Jose


def t_2c_custom():
    """Given custom WaypointsShortestPathProblem, output path for visualization."""
    problem = submission.getSanJoseWaypointsShortestPathProblem()
    ucs = util.UniformCostSearch(verbose=0)
    ucs.solve(problem)
    path = extractPath(problem.startLocation, ucs)
    printPath(path=path, waypointTags=problem.waypointTags, cityMap=sanJoseMap)
    grader.require_is_true(
        checkValid(
            path,
            sanJoseMap,
            problem.startLocation,
            problem.endTag,
            problem.waypointTags,
        )
    )


grader.add_basic_part(
    "2c-custom",
    t_2c_custom,
    max_points=3,
    max_seconds=10,
    description="customized shortest path with waypoints through San Jose",
)

########################################################################################
# Problem 3a: A* to UCS reduction

class ZeroHeuristic(util.Heuristic):
    """Estimates the cost between locations as 0 distance."""
    def __init__(self, endTag: str, cityMap: CityMap):
        self.endTag = endTag
        self.cityMap = cityMap

    def evaluate(self, state: util.State) -> float:
        return 0.0

# Calculates distance only along the north south direction
class NorthSouthHeuristic(util.Heuristic):
    def __init__(self, endTag: str, cityMap: CityMap):
        self.endTag = endTag
        self.cityMap = cityMap
        self.endGeoLocations = [
            self.cityMap.geoLocations[location]
            for location, tags in self.cityMap.tags.items()
            if endTag in tags
        ]

    def evaluate(self, state: util.State) -> float:
        currentGeoLocation = self.cityMap.geoLocations[state.location]
        return min(
            RADIUS_EARTH * radians(abs(endGeoLocation.latitude - currentGeoLocation.latitude))
            for endGeoLocation in self.endGeoLocations
        )


def t_3a(
    cityMap: CityMap,
    startLocation: str,
    endTag: str,
    expectedCost: Optional[float] = None,
    heuristic_cls: Optional[Type[util.Heuristic]] = ZeroHeuristic,
):
    """
    Run UCS on the A* Reduction of a ShortestPathProblem, specified by
        (startLocation, endTag).
    """
    heuristic = heuristic_cls(endTag, cityMap)

    # Define the baseProblem and corresponding reduction (using `zeroHeuristic`)
    baseProblem = submission.ShortestPathProblem(startLocation, endTag, cityMap)
    aStarProblem = submission.aStarReduction(baseProblem, heuristic)

    # Solve the reduction via a call to `ucs.solve` (similar to prior tests)
    ucs = util.UniformCostSearch(verbose=0)
    ucs.solve(aStarProblem)
    path = extractPath(startLocation, ucs)
    grader.require_is_true(checkValid(path, cityMap, startLocation, endTag, []))
    if expectedCost is not None:
        grader.require_is_equal(expectedCost, getTotalCost(path, cityMap), tolerance=1e-2)



grader.add_basic_part(
    "3a-1-basic",
    lambda: t_3a(
        cityMap=createGridMap(3, 5),
        startLocation=makeGridLabel(0, 0),
        endTag=makeTag("label", makeGridLabel(2, 2)),
        expectedCost=4,
    ),
    max_points=1,
    max_seconds=1,
    description="A* shortest path on small grid",
)

grader.add_basic_part(
    "3a-2-basic",
    lambda: t_3a(
        cityMap=createGridMap(30, 30),
        startLocation=makeGridLabel(20, 10),
        endTag=makeTag("x", "5"),
        expectedCost=15,
    ),
    max_points=1,
    max_seconds=1,
    description="A* shortest path with multiple end locations",
)

grader.add_hidden_part(
    "3a-3-hidden",
    lambda: t_3a(
        cityMap=createGridMap(100, 100),
        startLocation=makeGridLabel(0, 0),
        endTag=makeTag("label", makeGridLabel(99, 99)),
    ),
    max_points=2,
    max_seconds=2,
    description="A* shortest path with larger grid",
)


########################################################################################
# Problem 3b: "straight-line" heuristic for A*


def t_3b_heuristic(
    cityMap: CityMap,
    startLocation: str,
    endTag: str,
    expectedCost: Optional[float] = None,
):
    """Targeted test for `StraightLineHeuristic` to ensure correctness."""
    heuristic = submission.StraightLineHeuristic(endTag, cityMap)
    heuristicCost = heuristic.evaluate(util.State(startLocation))
    if expectedCost is not None:
        grader.require_is_equal(expectedCost, heuristicCost)



grader.add_basic_part(
    "3b-heuristic-1-basic",
    lambda: t_3b_heuristic(
        cityMap=createGridMap(3, 5),
        startLocation=makeGridLabel(0, 0),
        endTag=makeTag("label", makeGridLabel(2, 2)),
        expectedCost=3.145067466556296,
    ),
    max_points=0.5,
    max_seconds=1,
    description="basic straight line heuristic unit test",
)

grader.add_hidden_part(
    "3b-heuristic-2-hidden",
    lambda: t_3b_heuristic(
        cityMap=createGridMap(100, 100),
        startLocation=makeGridLabel(0, 0),
        endTag=makeTag("label", makeGridLabel(99, 99)),
    ),
    max_points=0.5,
    max_seconds=1,
    description="hidden straight line heuristic unit test",
)

if __name__ == "__main__":
    grader.grade()
