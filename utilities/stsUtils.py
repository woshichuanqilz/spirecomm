import json


def getNodeByXY(x, y, all_nodes):
    for node in all_nodes:
        if node['x'] == x and node['y'] == y:
            return node


def getPath(start_node, cur_path, all_nodes):
    for pos in start_node['children']:
        print(pos['x'], pos['y'])
        node = getNodeByXY(pos['x'], pos['y'], all_nodes)
        if pos['y'] == 16:
            return cur_path + [node]
        else:
            return getPath(node, cur_path + [node], all_nodes)


def getAllPaths():
    with open('../tmp.json', encoding='utf-8') as f:
        game_state = json.load(f)
    sts_map = game_state['game_state']['map']
    # get all node with y = 0
    start_nodes = []
    paths = []
    for node in sts_map:
        if node['y'] == 0:
            paths += getPath(node, [node], sts_map)
    print(paths)


if __name__ == '__main__':
    getAllPaths()
