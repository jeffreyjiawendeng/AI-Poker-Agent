import random

from pypokerengine.players import BasePokerPlayer


class CustomAgent(BasePokerPlayer):
    """
    Custom AI poker agent — replace this stub with your real implementation.

    Convention:
      - Name your class <YourName>Agent (e.g. MCTSAgent, CFRAgent).
      - Update arena/config/arena.yaml to point at your new class.
      - Add any ML/RL dependencies to envs/custom_agent/pyproject.toml.
    """

    def declare_action(self, valid_actions, hole_card, round_state):
        r = random.random()
        if r <= 0.5:
            return valid_actions[1]["action"]   # call
        elif r <= 0.9 and len(valid_actions) == 3:
            return valid_actions[2]["action"]   # raise
        else:
            return valid_actions[0]["action"]   # fold

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
    return CustomAgent()
