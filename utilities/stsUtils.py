import json


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

    def get_best_path(self):
        result = []
        for path in self.paths:
            elite_count = 0
            campfire_count = 0
            for node in path:
                if node['symbol'] == 'E':
                    elite_count += 1
                if node['symbol'] == 'R':
                    campfire_count += 1
            if elite_count >= 2 and campfire_count >= 2:
                result.append(path)
        return result


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
            "hasEmeraldKey": False,
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
    pe = PathEvaluator((0, 0), paths)
    print(pe.get_best_path())
