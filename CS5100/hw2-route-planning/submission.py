# Xinle Xu (NUID: 002335847)
from typing import List, Tuple

from mapUtil import (
    CityMap,
    computeDistance,
    createSanJoseMap,
    locationFromTag,
    makeTag, getTotalCost,
)
from util import Heuristic, SearchProblem, State, UniformCostSearch


# *IMPORTANT* :: A key part of this assignment is figuring out how to model states
# effectively. We've defined a class `State` to help you think through this, with a
# field called `memory`.
#
# As you implement the different types of search problems below, think about what
# `memory` should contain to enable efficient search!
#   > Please read the docstring for `State` in `util.py` for more details and code.

# Please also read the docstrings for the relevant classes and functions defined in `mapUtil.py`

########################################################################################
# Problem 1a: Modeling the Shortest Path Problem.


class ShortestPathProblem(SearchProblem):
    """
    Defines a search problem that corresponds to finding the shortest path
    from `startLocation` to any location with the specified `endTag`.
    """

    def __init__(self, startLocation: str, endTag: str, cityMap: CityMap):
        self.startLocation = startLocation
        self.endTag = endTag
        self.cityMap = cityMap

    def startState(self) -> State:
        # BEGIN_YOUR_CODE
        s = State(self.startLocation)
        return s
        raise Exception("Not implemented yet")
        # END_YOUR_CODE

    def isEnd(self, state: State) -> bool:
        # BEGIN_YOUR_CODE
        return self.endTag in self.cityMap.tags[state.location]
        raise Exception("Not implemented yet")
        # END_YOUR_CODE

    def successorsAndCosts(self, state: State) -> List[Tuple[str, State, float]]:
        """
        Note we want to return a list of *3-tuples* of the form:
            (successorLocation: str, successorState: State, cost: float)
        """
        # BEGIN_YOUR_CODE
        result: List[Tuple[str, State, float]] = []
        here = state.location
        for nxt, dist in self.cityMap.distances[here].items():
            result.append((nxt, State(nxt), dist))
        return result
        raise Exception("Not implemented yet")
        # END_YOUR_CODE


########################################################################################
# Problem 1b: Custom -- Plan a Route through San Jose


def getSanJoseShortestPathProblem() -> ShortestPathProblem:
    """
    Create your own search problem using the map of San Jose, specifying your own
    `startLocation`/`endTag`. If you prefer, you may create a new map using via
    `createCustomMap()`.

    Run `python mapUtil.py > readableSanJoseMap.txt` to dump a file with a list of
    locations and associated tags; you might find it useful to search for the following
    tag keys (amongst others):
        - `landmark=` - Hand-defined landmarks (from `data/sanjose-landmarks.json`)
        - `amenity=`  - Various amenity types (e.g., "parking_entrance", "food")
        - `parking=`  - Assorted parking options (e.g., "underground")
    """
    # Or, if you would rather use a custom map, you can uncomment the following!
    # cityMap = createCustomMap("data/custom.pbf", "data/custom-landmarks".json")

    # BEGIN_YOUR_CODE (our solution is 2 lines of code, but don't worry if you deviate from this)
    cityMap = createSanJoseMap()
    start = locationFromTag(makeTag("landmark", "northeastern_building"), cityMap)
    endTag = makeTag("landmark", "starbucks")
    return ShortestPathProblem(start, endTag, cityMap)
    raise Exception("Not implemented yet")
    # END_YOUR_CODE


########################################################################################
# Problem 2a: Modeling the Waypoints Shortest Path Problem.


class WaypointsShortestPathProblem(SearchProblem):
    """
    Defines a search problem that corresponds to finding the shortest path from
    `startLocation` to any location with the specified `endTag` such that the path also
    traverses locations that cover the set of tags in `waypointTags`.

    Hint: naively, your `memory` representation could be a list of all locations visited.
    However, that would be too large of a state space to search over! Think
    carefully about what `memory` should represent.
    """
    def __init__(
        self, startLocation: str, waypointTags: List[str], endTag: str, cityMap: CityMap
    ):
        self.startLocation = startLocation
        self.endTag = endTag
        self.cityMap = cityMap

        # We want waypointTags to be consistent/canonical (sorted) and hashable (tuple)
        self.waypointTags = tuple(sorted(waypointTags))

    def startState(self) -> State:
        # BEGIN_YOUR_CODE
        covered = {t for t in self.waypointTags if t in self.cityMap.tags[self.startLocation]}
        return State(self.startLocation, frozenset(covered))
        raise Exception("Not implemented yet")
        # END_YOUR_CODE

    def isEnd(self, state: State) -> bool:
        # BEGIN_YOUR_CODE
        at_goal = self.endTag in self.cityMap.tags[state.location]
        all_done = state.memory == frozenset(self.waypointTags)
        return at_goal and all_done
        raise Exception("Not implemented yet")
        # END_YOUR_CODE

    def successorsAndCosts(self, state: State) -> List[Tuple[str, State, float]]:
        # BEGIN_YOUR_CODE
        result: List[Tuple[str, State, float]] = []
        here = state.location
        covered = set(state.memory) if state.memory is not None else set()
        for nxt, dist in self.cityMap.distances[here].items():
            newCovered = covered.union(t for t in self.waypointTags if t in self.cityMap.tags[nxt])
            result.append((nxt, State(nxt, frozenset(newCovered)), dist))
        return result
        raise Exception("Not implemented yet")
        # END_YOUR_CODE


########################################################################################
# Problem 2b: Custom -- Plan a Route with Unordered Waypoints through San Jose


def getSanJoseWaypointsShortestPathProblem() -> WaypointsShortestPathProblem:
    """
    Create your own search problem using the map of San Jose, specifying your own
    `startLocation`/`waypointTags`/`endTag`.

    Similar to Problem 1b, use `readableSanJoseMap.txt` to identify potential
    locations and tags.
    """
    cityMap = createSanJoseMap()
    # BEGIN_YOUR_CODE (our solution is 4 lines of code, but don't worry if you deviate from this)
    start = locationFromTag(makeTag("landmark", "philz"), cityMap)
    waypointTags = [makeTag("landmark", "northeastern_building")]
    endTag = makeTag("landmark", "bus_station")
    return WaypointsShortestPathProblem(start, waypointTags, endTag, cityMap)
    raise Exception("Not implemented yet")
    # END_YOUR_CODE
    # return WaypointsShortestPathProblem(startLocation, waypointTags, endTag, cityMap)

########################################################################################
# Problem 4a: A* to UCS reduction

# Turn an existing SearchProblem (`problem`) you are trying to solve with a
# Heuristic (`heuristic`) into a new SearchProblem (`newSearchProblem`), such
# that running uniform cost search on `newSearchProblem` is equivalent to
# running A* on `problem` subject to `heuristic`.
#
# This process of translating a model of a problem + extra constraints into a
# new instance of the same problem is called a reduction; it's a powerful tool
# for writing down "new" models in a language we're already familiar with.
# See util.py for the class definitions and methods of Heuristic and SearchProblem.


def aStarReduction(problem: SearchProblem, heuristic: Heuristic) -> SearchProblem:
    class NewSearchProblem(SearchProblem):
        def startState(self) -> State:
            # BEGIN_YOUR_CODE
            s = problem.startState()
            return s
            raise Exception("Not implemented yet")
            # END_YOUR_CODE

        def isEnd(self, state: State) -> bool:
            # BEGIN_YOUR_CODE
            return problem.isEnd(state)
            raise Exception("Not implemented yet")
            # END_YOUR_CODE

        def successorsAndCosts(self, state: State) -> List[Tuple[str, State, float]]:
            # BEGIN_YOUR_CODE
            result: List[Tuple[str, State, float]] = []
            h_s = heuristic.evaluate(state)
            for action, succ, cost in problem.successorsAndCosts(state):
                h_succ = heuristic.evaluate(succ)
                result.append((action, succ, cost + (h_succ - h_s)))
            return result
            raise Exception("Not implemented yet")
            # END_YOUR_CODE

    return NewSearchProblem()


########################################################################################
# Problem 4b: "straight-line" heuristic for A*


class StraightLineHeuristic(Heuristic):
    """
    Estimate the cost between locations as the straight-line distance.
        > Hint: you might consider using `computeDistance` defined in `mapUtil.py`
    """
    def __init__(self, endTag: str, cityMap: CityMap):
        self.endTag = endTag
        self.cityMap = cityMap
        # Precompute all the Geolocations associated with endTag
        # BEGIN_YOUR_CODE
        self._goal_geos = [
            self.cityMap.geoLocations[label]
            for label, tags in self.cityMap.tags.items()
            if self.endTag in tags
        ]
        return
        raise Exception("Not implemented yet")
        # END_YOUR_CODE

    def evaluate(self, state: State) -> float:
        # BEGIN_YOUR_CODE
        if not hasattr(self, "_goal_geos") or not self._goal_geos:
            return 0.0
        here = self.cityMap.geoLocations[state.location]
        return min(computeDistance(here, g) for g in self._goal_geos)
        raise Exception("Not implemented yet")
        # END_YOUR_CODE
