from itertools import combinations

class BattleStrategy:
    def __init__(self, game_state):
        self.game_state = game_state
        self.min_hp_loss = -1000
        self.is_first_turn = True
        self.monsters = self.game_state.monsters
        self.total_damage = 0

    def update_state(self, game_state):
        self.game_state = game_state

    def get_enemies_total_damage(self):
        self.total_damage = 0
        for monster in self.monsters:
            if monster.intent.name == "ATTACK" and not monster.is_gone:
                self.total_damage += monster.move_adjusted_damage

    def get_max_damage(self):
        # get all attack cards in hand
        attack_cards = [card for card in self.game_state.hand if card.card_type == "ATTACK"]
        # get all combinations of attack cards
        attack_combinations = []
        for i in range(1, len(attack_cards) + 1):
            attack_combinations.extend(combinations(attack_cards, i))
        # get max damage from all combinations and cost less than or equal to energy
        max_damage = 0
        energy_cost_for_max_damage = 0
        for attack_combination in attack_combinations:
            damage = 0
            energy_cost = 0
            for card in attack_combination:
                damage += card.damage
                energy_cost += card.cost
            if damage > max_damage and energy_cost <= self.game_state.energy:
                max_damage = damage
                energy_cost_for_max_damage = energy_cost
        return max_damage, energy_cost_for_max_damage




