import random

from pypokerengine.players import BasePokerPlayer


class RuleBasedAgent(BasePokerPlayer):
    """
    Rule-based agent placeholder.

    TODO: Replace random fallback with hand-strength rules, pot-odds
          analysis, and positional awareness in a future commit.
    """

    def declare_action(self, valid_actions, hole_card, round_state):
        # Placeholder: behaves like RandomAgent until rules are implemented
        return random.choice(valid_actions)["action"]

    def receive_game_start_message(self, game_info):
        pass

    def receive_round_start_message(self, round_count, hole_card, seats):
        pass

    def receive_street_start_message(self, street, round_state):
        pass

    def receive_game_update_message(self, action, round_state):
        pass

    def receive_round_result_message(self, winners, hand_info, round_state):
        pass


def setup_ai():
    return RuleBasedAgent()
