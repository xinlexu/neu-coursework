#!/usr/bin/env python3

import random, util, collections
import graderUtil

grader = graderUtil.Grader()
submission = grader.load('submission')

############################################################
# Problem 1

grader.addManualPart('1a', 3, description="Written question: value iteration in basic MDP")
grader.addManualPart('1b', 3, description="Written question: optimal policy in basic MDP")

############################################################
# Problem 2

class AddNoiseMDP(util.MDP):
    def __init__(self, originalMDP):
        self.originalMDP = originalMDP

    def startState(self):
        return self.originalMDP.startState()

    # Return set of actions possible from |state|.
    def actions(self, state):
        return self.originalMDP.actions(state)

    # Return a list of (newState, prob, reward) tuples corresponding to edges
    # coming out of |state|.
    def succAndProbReward(self, state, action):
        originalSuccAndProbReward = self.originalMDP.succAndProbReward(state, action)
        newSuccAndProbReward = []
        for state, prob, reward in originalSuccAndProbReward:
            newProb = 0.5 * prob + 0.5 / len(originalSuccAndProbReward)
            newSuccAndProbReward.append((state, newProb, reward))
        return newSuccAndProbReward

    # Return set of actions possible from |state|.
    def discount(self):
        return self.originalMDP.discount()

def test2a():
    mdp = submission.CounterexampleMDP()
    mdp.computeStates()
    algorithm = submission.ValueIteration()
    algorithm.solve(mdp, .001)
    originalVal = algorithm.V[mdp.startState()]
    mdp = AddNoiseMDP(mdp)
    mdp.computeStates()
    algorithm.solve(mdp, .001)
    newVal = algorithm.V[mdp.startState()]
grader.addHiddenPart('2a-hidden', test2a, 3, description="Hidden test for CounterexampleMDP. Ensure that V[startState] is greater after noise is added.")

grader.addManualPart('2b', 3, description="Written question: single-pass algorithm for node values in acyclic MDP")
grader.addManualPart('2c', 3, description="Written question: define new MDP solver for discounts < 1")

############################################################
# Problem 3

def test3a():
    mdp1 = submission.BlackjackMDP(cardValues=[1, 5], multiplicity=2,
                                   threshold=10, peekCost=1)
    startState = mdp1.startState()
    preBustState = (6, None, (1, 1))
    postBustState = (11, None, None)

    mdp2 = submission.BlackjackMDP(cardValues=[1, 5], multiplicity=2,
                                   threshold=15, peekCost=1)
    preEmptyState = (11, None, (1,0))

    # Make sure the succAndProbReward function is implemented correctly.
    tests = [
        ([((1, None, (1, 2)), 0.5, 0), ((5, None, (2, 1)), 0.5, 0)], mdp1, startState, 'Take'),
        ([((0, 0, (2, 2)), 0.5, -1), ((0, 1, (2, 2)), 0.5, -1)], mdp1, startState, 'Peek'),
        ([((0, None, None), 1, 0)], mdp1, startState, 'Quit'),
        ([((7, None, (0, 1)), 0.5, 0), ((11, None, None), 0.5, 0)], mdp1, preBustState, 'Take'),
        ([], mdp1, postBustState, 'Take'),
        ([], mdp1, postBustState, 'Peek'),
        ([], mdp1, postBustState, 'Quit'),
        ([((12, None, None), 1, 12)], mdp2, preEmptyState, 'Take')
    ]
    for gold, mdp, state, action in tests:
        if not grader.requireIsEqual(gold,
                                     mdp.succAndProbReward(state, action)):
            print(('   state: {}, action: {}'.format(state, action)))
grader.addBasicPart('3a-basic', test3a, 5, description="Basic test for succAndProbReward() that covers several edge cases.")

def test3aHidden():
    mdp = submission.BlackjackMDP(cardValues=[1, 3, 5, 8, 10], multiplicity=3,
                                  threshold=40, peekCost=1)
    startState = mdp.startState()
    alg = util.ValueIteration()
    alg.solve(mdp, .0001)
grader.addHiddenPart('3a-hidden', test3aHidden, 5, description="Hidden test for ValueIteration. Run ValueIteration on BlackjackMDP, then test if V[startState] is correct.")


def test3b():
    mdp = submission.peekingMDP()
    vi = submission.ValueIteration()
    vi.solve(mdp)
    grader.requireIsEqual(mdp.threshold, 20)
    grader.requireIsEqual(mdp.peekCost, 1)
    f = len([a for a in list(vi.pi.values()) if a == 'Peek']) / float(len(list(vi.pi.values())))
    grader.requireIsGreaterThan(.1, f)
    # Feel free to uncomment these lines if you'd like to print out states/actions
    # for k, v in vi.pi.iteritems():
    #     print k, v
grader.addBasicPart('3b-basic', test3b, 4, description="Test for peekingMDP().  Ensure that in at least 10% of states, the optimal policy is to peek.")

grader.grade()
