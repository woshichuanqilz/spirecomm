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
    def __init__(self, cur_pos, paths):
        self.paths = paths
        self.cur_pos = cur_pos
        self.map_conf = STS_Config['map']

    def calc_path_score(self, path, game_state):
        score = 0
        current_hp = game_state['current_hp']
        gold = game_state['gold']
        for node in path:
            if node['symbol'] == 'M':
                score += self.map_conf['room_type']['monster']['profit']
                current_hp += self.map_conf['room_type']['monster']['hp_consumption']
            elif node['symbol'] == 'R':
                score += self.map_conf['room_type']['campfire']['profit']
                current_hp += self.map_conf['room_type']['campfire']['hp_consumption']
            elif node['symbol'] == '?':
                score += self.map_conf['room_type']['question_mark']['profit']
                current_hp += self.map_conf['room_type']['question_mark']['hp_consumption']
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
                current_hp += self.map_conf['room_type']['shop']['hp_consumption']
            elif node['symbol'] == 'T':
                score += self.map_conf['room_type']['treasure']['profit']
                current_hp += self.map_conf['room_type']['treasure']['hp_consumption']
            elif node['symbol'] == 'E':
                if node['hasEmeraldKey']:
                    score += self.map_conf['room_type']['elite_with_fire']['profit']
                    current_hp += self.map_conf['room_type']['elite_with_fire']['hp_consumption']
                else:
                    score += self.map_conf['room_type']['elite']['profit']
                    current_hp += self.map_conf['room_type']['elite']['hp_consumption']
            elif node['symbol'] == 'B':
                pass
            else:
                # throw error
                print(node['symbol'])
                raise Exception('Unknown symbol')
        return {
            "score": score,
            "hp": current_hp,
            "path": path
        }

    def get_best_path(self, game_state):
        path_with_2e2r = []
        for path in self.paths:
            elite_count = 0
            campfire_count = 0
            for node in path:
                if node['symbol'] == 'E':
                    elite_count += 1
                if node['symbol'] == 'R':
                    campfire_count += 1
            if elite_count >= 2 and campfire_count >= 2:
                path_with_2e2r.append(path)
        path_with_score = []
        for p in path_with_2e2r:
            path_with_score.append(self.calc_path_score(p, game_state))
        # remove path with hp < 0
        path_with_score = [p for p in path_with_score if p['hp'] >= 0]
        # sort by score
        path_with_score.sort(key=lambda x: x['score'], reverse=True)
        return path_with_score[0]


class GetPaths:
    paths = []

    def getPath(self, start_node, cur_path, all_nodes):
        for pos in start_node['children']:
            print(pos['x'], pos['y'])
            node = getNodeByXY(pos['x'], pos['y'], all_nodes)
            if pos['y'] == 16:
                self.paths.append(cur_path + [node])
            else:
                return self.getPath(node, (cur_path + [node]).copy(), all_nodes)

    def getAllPaths(self):
        with open('../tmp.json', encoding='utf-8') as f:
            game_state = json.load(f)
        end_node = {
            "symbol": "B",
            "phrase": "INCOMPLETE",
            "children": [],
            "x": 3,
            "y": 16,
            "hasemeraldkey": False,
            "parents": []
        }
        sts_map = game_state['game_state']['map']
        sts_map.append(end_node)
        # get all node with y = 0
        start_nodes = [node for node in sts_map if node['y'] == 0]
        self.paths = find_paths(start_nodes, sts_map)

        return self.paths


if __name__ == '__main__':
    k = GetPaths()
    paths = k.getAllPaths()
    path_eval = PathEvaluator((0, 0), paths)
    bps = path_eval.get_best_path({'player': {
        'current_hp': 75
    }})
    print('done')
