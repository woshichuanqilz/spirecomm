import json
from sts_config import STS_Config


def getNodeByXY(x, y, all_nodes):
    for node in all_nodes:
        if node['x'] == x and node['y'] == y:
            return node


def find_paths(start_nodes, all_nodes):
    paths = []
    current_path = []

    def dfs(node):
        current_path.append(node)
        if node['y'] == 16:
            paths.append(list(current_path))
        else:
            for child in node['children']:
                dfs(getNodeByXY(child['x'], child['y'], all_nodes))

        current_path.pop()

    for start_node in start_nodes:
        dfs(start_node)

    return paths


class PathEvaluator:
    def __init__(self, game_state):
        self.game_state = game_state
        self.count_dict = {}
        self.paths_info = []
        self.map_conf = STS_Config['map']
        self.choice_list = game_state['game_state']['choice_list']
        self.getAllPaths()

    def choice_bonus(self):
        for path in self.paths_info:
            if 'receive 100 gold' == self.choice_list[1] or 'gain 250 gold' in self.choice_list[2]:
                pass

    def get_best_path(self):
        for path in self.paths_info:
            self.calc_path_score(path)
        print('hello')

    def calc_path_score(self, path):
        score = 0
        current_hp = self.game_state['game_state']['current_hp']
        gold = self.game_state['game_state']['gold']
        monster_room_count = 0
        keyword_map = self.map_conf['keyword_map']
        for node in path:
            kw = keyword_map[node['symbol']]
            if node['symbol'] == 'M':
                score += self.map_conf['room_type']['monster']['profit']
                if self.game_state['game_state']['act'] == 1:
                    if monster_room_count <= 3:
                        current_hp += self.map_conf['room_type'][kw]['hp_consumption']
                    else:
                        current_hp += self.map_conf['room_type'][kw]['hp_consumption_act1_first3']
                monster_room_count += 1
            elif node['symbol'] == '$':  # shop
                if gold < 75:
                    profit = 0
                elif 75 <= gold < 120:
                    profit = 2
                elif 120 <= gold < 180:
                    profit = 4
                elif 180 <= gold < 230:
                    profit = 5
                else:
                    profit = 7
                score += profit
                current_hp += self.map_conf['room_type'][kw]['hp_consumption']
            elif node['symbol'] == 'E':
                if node['hasEmeraldKey']:
                    score += self.map_conf['room_type']['elite_with_fire']['profit']
                    current_hp += self.map_conf['room_type']['elite_with_fire']['hp_consumption']
                else:
                    score += self.map_conf['room_type'][kw]['profit']
                    current_hp += self.map_conf['room_type'][kw]['hp_consumption']
            elif node['symbol'] in ['R', '?', 'T']:
                score += self.map_conf['room_type'][kw]['profit']
                current_hp += self.map_conf['room_type'][kw]['hp_consumption']
            elif node['symbol'] == 'B':
                pass
            else:
                # throw error
                print(node['symbol'])
                raise Exception('Unknown symbol')
        return {
            "score": score,
            "hp": current_hp
        }

    def getAllPaths(self):
        end_node = STS_Config['map']['end_node']
        sts_map = self.game_state['game_state']['map']
        sts_map.append(end_node)
        # get all node with y = 0
        start_nodes = [node for node in sts_map if node['y'] == 0]
        tmp_paths = find_paths(start_nodes, sts_map)
        for path in tmp_paths:
            tmp_dict = {'path': path}
            monster_count_before_first_elite = 0
            is_first_elite_appear = False
            for node in path:
                key = str(node['x']) + '-' + str(node['y'])
                if key in self.count_dict and node['y'] <= 6:
                    self.count_dict[key] += 1
                else:
                    self.count_dict[key] = 1
                if node['symbol'] == 'E' and not is_first_elite_appear:
                    is_first_elite_appear = True
                    tmp_dict['monster_count_before_first_elite'] = monster_count_before_first_elite
                if node['symbol'] == 'M' and not is_first_elite_appear:
                    monster_count_before_first_elite += 1

            # dict extend
            basic_info = self.basicProcessPath(path)
            if basic_info['elite_count'] < 2 or basic_info['campfire_count'] < 2:
                continue
            score_tmp_dict = self.calc_path_score(path)
            print(score_tmp_dict)
            self.paths_info.append({
                **tmp_dict,
                **score_tmp_dict,
                **basic_info
            })

        return self.paths_info

    def basicProcessPath(self, path):
        # count elite and campfire
        elite_count = 0
        campfire_count = 0
        for node in path:
            if node['symbol'] == 'E':
                elite_count += 1
            if node['symbol'] == 'R':
                campfire_count += 1
        # index of first store
        store_index = -1
        for i, node in enumerate(path):
            if node['symbol'] == '$':
                store_index = i
                break
        # if store before the first elite
        store_before_first_elite = False
        if store_index != -1:
            for i, node in enumerate(path):
                if node['symbol'] == 'E':
                    if i < store_index:
                        store_before_first_elite = True
                        break
        # if campfire before the first elite
        campfire_before_first_elite = False
        if store_index != -1:
            for i, node in enumerate(path):
                if node['symbol'] == 'E':
                    if i < store_index:
                        campfire_before_first_elite = True
                        break

        return {
            "elite_count": elite_count,
            "campfire_count": campfire_count,
            "store_index": store_index,
            "store_before_first_elite": store_before_first_elite,
            "campfire_before_first_elite": campfire_before_first_elite
        }


if __name__ == '__main__':
    # k = PathEvaluator()
    # paths = k.getAllPaths()
    with open('../game_state.json', encoding='utf-8') as f:
        gs = json.load(f)
    path_eval = PathEvaluator(gs)
    print('done')
