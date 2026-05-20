import util, math, random
from collections import defaultdict
from util import ValueIteration

############################################################
# Problem 2.2

# If you decide 2.2 is true, prove it in your submission and put "return None" for
# the code blocks below.  If you decide that 2.2 is false, construct a counterexample.
class CounterexampleMDP(util.MDP):
    # Return a value of any type capturing the start state of the MDP.
    def startState(self):
        # BEGIN_YOUR_CODE
        return 'start'
        # END_YOUR_CODE

    # Return a list of strings representing actions possible from |state|.
    def actions(self, state):
        # BEGIN_YOUR_CODE
        if state in ('good', 'bad'):
            return []
        return ['go']
        # END_YOUR_CODE

    # Given a |state| and |action|, return a list of (newState, prob, reward) tuples
    # corresponding to the states reachable from |state| when taking |action|.
    # Remember that if |state| is an end state, you should return an empty list [].
    def succAndProbReward(self, state, action):
        # BEGIN_YOUR_CODE
        if state in ('good', 'bad') or action != 'go':
            return []
        return [('good', 0.1, 10.0), ('bad', 0.9, 0.0)]
        # END_YOUR_CODE

    # Set the discount factor (float or integer) for your counterexample MDP.
    # Return the discount factor
    def discount(self):
        # BEGIN_YOUR_CODE
        return 1
        # END_YOUR_CODE

############################################################
# Problem 3

class BlackjackMDP(util.MDP):
    def __init__(self, cardValues, multiplicity, threshold, peekCost):
        """
        cardValues: list of integers (face values for each card included in the deck)
        multiplicity: single integer representing the number of cards with each face value
        threshold: maximum number of points (i.e. sum of card values in hand) before going bust
        peekCost: how much it costs to peek at the next card
        """
        self.cardValues = cardValues
        self.multiplicity = multiplicity
        self.threshold = threshold
        self.peekCost = peekCost

    # Return the start state.
    # Look closely at this function to see an example of state representation for our Blackjack game.
    # Each state is a tuple with 3 elements:
    #   -- The first element of the tuple is the sum of the cards in the player's hand.
    #   -- If the player's last action was to peek, the second element is the index
    #      (not the face value) of the next card that will be drawn; otherwise, the
    #      second element is None.
    #   -- The third element is a tuple giving counts for each of the cards remaining
    #      in the deck, or None if the deck is empty or the game is over (e.g. when
    #      the user quits or goes bust).
    def startState(self):
        return (0, None, (self.multiplicity,) * len(self.cardValues))

    # Return set of actions possible from |state|.
    # You do not need to modify this function.
    # All logic for dealing with end states should be placed into the succAndProbReward function below.
    def actions(self, state):
        return ['Take', 'Peek', 'Quit']

    # Given a |state| and |action|, return a list of (newState, prob, reward) tuples
    # corresponding to the states reachable from |state| when taking |action|.
    # A few reminders:
    # * Indicate a terminal state (after quitting, busting, or running out of cards)
    #   by setting the deck to None.
    # * If |state| is an end state, you should return an empty list [].
    # * When the probability is 0 for a transition to a particular new state,
    #   don't include that state in the list returned by succAndProbReward.
    def succAndProbReward(self, state, action):
        # BEGIN_YOUR_CODE
        total, peek_idx, deck = state
        if deck is None:
            return []

        if action == 'Quit':
            # terminal with reward = total
            return [((total, None, None), 1.0, float(total))]

        counts = tuple(deck)
        remaining = sum(counts)

        def draw(i):
            # apply drawing card i
            v = self.cardValues[i]
            new_total = total + v
            new_counts = list(counts)
            new_counts[i] -= 1
            if new_total > self.threshold:          # bust
                return (new_total, None, None), 0.0
            if sum(new_counts) == 0:                 # deck empty (non-bust)
                return (new_total, None, None), float(new_total)
            return (new_total, None, tuple(new_counts)), 0.0

        if action == 'Peek':
            if peek_idx is not None or remaining == 0:
                return []
            out = []
            for i, c in enumerate(counts):
                if c:
                    p = c / float(remaining)
                    out.append(((total, i, counts), p, -float(self.peekCost)))
            return out

        if action == 'Take':
            if peek_idx is not None:
                s2, r = draw(peek_idx)               # deterministic draw after peek
                return [(s2, 1.0, r)]
            if remaining == 0:
                return []
            out = []
            for i, c in enumerate(counts):
                if c:
                    p = c / float(remaining)
                    s2, r = draw(i)
                    out.append((s2, p, r))
            return out

        return []
        # END_YOUR_CODE

    def discount(self):
        return 1

############################################################
# Problem 3b

def peekingMDP():
    """
    Return an instance of BlackjackMDP where peeking is the
    optimal action at least 10% of the time.
    """
    # BEGIN_YOUR_CODE
    cardValues = [2, 3, 13]
    multiplicity = 6
    threshold = 20
    peekCost = 1
    return BlackjackMDP(cardValues, multiplicity, threshold, peekCost)
    # END_YOUR_CODE
