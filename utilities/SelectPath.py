# -*- coding: utf-8 -*-
import json
from utilities.sts_config import STS_Config
import random


def visualize_map(pos_list):
    with open('../map.md', encoding='utf-8') as the_file:
        map_v = the_file.read()
    map_v = [list(x[7:]) for x in map_v.split('\n') if x != '']
    line_cnt = len(map_v)
    for pos in pos_list[:15]:
        x = 3 * pos['x']
        y = line_cnt - 1 - 2 * pos['y']
        if x - 1 >= 0:
            map_v[y][x - 1] = '('
        if x + 1 >= len(map_v[y]):
            map_v[y].append('_')
        map_v[y][x + 1] = ')'
        # print(f'paint: {x}, {y}. {map_v[y][x]}')

    # join the list
    print('\n'.join([''.join(x) for x in map_v]))


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


def basicProcessPath(path, path_info):
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

    path_info.elite_count = elite_count
    path_info.campfire_count = campfire_count
    path_info.store_index = store_index
    path_info.store_before_first_elite = store_before_first_elite
    path_info.campfire_before_first_elite = campfire_before_first_elite


class ChoiceBonus:
    def __init__(self, choice_bonus_type, choice_bonus_score=0):
        self.choice_bonus_type = choice_bonus_type
        self.choice_bonus_score = choice_bonus_score


class PathInfo:
    def __init__(self, path, score, hp, elite_count, campfire_count, store_index, store_before_first_elite,
                 campfire_before_first_elite, monster_count_before_first_elite, choice_bonus):
        self.path = path
        self.score = score
        self.hp = hp
        self.elite_count = elite_count
        self.campfire_count = campfire_count
        self.store_index = store_index
        self.store_before_first_elite = store_before_first_elite
        self.campfire_before_first_elite = campfire_before_first_elite
        self.monster_count_before_first_elite = monster_count_before_first_elite
        self.choice_bonus = choice_bonus


class PathEvaluator:
    def __init__(self, game_state):
        self.best_path = None
        self.neow_event_choice = None
        self.game_state = game_state.game_state_json
        self.neows_choices = [x.lower() for x in self.game_state['choice_list']]
        self.count_dict = {}
        self.paths_info = []
        self.map_conf = STS_Config['map']
        self.getBestPath()

    def choice_bonus(self):
        for path_info in self.paths_info:
            # gold related
            tmp_bonus = ChoiceBonus('tbd')
            path_info.choice_bonus = []
            if 'gain 250 gold' in self.neows_choices[2]:
                tmp_bonus.choice_bonus_type = 'gain 250 gold'
                if path_info['store_before_first_elite']:
                    # tmp_score = 4
                    tmp_bonus.choice_bonus_score = 4
                    if 'obtain a curse' in self.neows_choices[2]:
                        # tmp_score += 2
                        tmp_bonus.choice_bonus_score += 2
                elif path_info.store_index >= 7:
                    tmp_bonus.choice_bonus_score = -5
            elif 'receive 100 gold' == self.neows_choices[1]:
                # tmp_bonus = {'choice_bonus_type': 'receive 100 gold'}
                tmp_bonus = ChoiceBonus('receive 100 gold')
                if path_info['store_before_first_elite']:
                    # tmp_bonus['choice_bonus_score'] = 4
                    tmp_bonus.choice_bonus_score = 4
                elif path_info['store_index'] >= 7:
                    # tmp_bonus['choice_bonus_score'] = -5
                    tmp_bonus.choice_bonus_score = -5
            if tmp_bonus.choice_bonus_type != 'tbd':
                path_info.choice_bonus.append(tmp_bonus)
            # neow's lament
            if path_info.monster_count_before_first_elite < 3:
                tmp_bonus.choice_bonus_score = 5
                tmp_bonus.choice_bonus_type = 'neow\'s lament'
                path_info.choice_bonus.append(tmp_bonus)
            if path_info.choice_bonus:
                path_info.choice_bonus = sorted(path_info.choice_bonus,
                                                key=lambda x: x.choice_bonus_score, reverse=True)
                path_info.score += path_info.choice_bonus[0].choice_bonus_score

    def calc_path_score(self, path, tmp_path_info):
        score = 0
        current_hp = self.game_state['current_hp']
        gold = self.game_state['gold']
        monster_room_count = 0
        keyword_map = self.map_conf['keyword_map']
        for node in path:
            kw = keyword_map[node['symbol']]
            if node['symbol'] == 'M':
                score += self.map_conf['room_type']['monster']['profit']
                if self.game_state['act'] == 1:
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
                # print(node['symbol'])
                raise Exception('Unknown symbol')
            # get max and min from list
            g_max = max(self.map_conf['room_type'][kw]['gold'])
            g_min = min(self.map_conf['room_type'][kw]['gold'])
            gold += random.randint(g_min, g_max)

        tmp_path_info.score = score
        tmp_path_info.hp = current_hp

    def getBestPath(self):
        end_node = STS_Config['map']['end_node']
        sts_map = self.game_state['map']
        sts_map.append(end_node)
        # get all node with y = 0
        start_nodes = [node for node in sts_map if node['y'] == 0]
        tmp_paths = find_paths(start_nodes, sts_map)

        for path in tmp_paths:
            # tmp_dict = {'path': path} to class
            tmp_path_info = PathInfo(path, 0, self.game_state['current_hp'], 0, 0,
                                     -1, False, False, 0, [])
            monster_count_before_first_elite = 0
            is_first_elite_appear = False
            for node in path:
                # 计算出现频率最多的点
                if 4 <= node['y'] <= 14:
                    key = str(node['x']) + '-' + str(node['y'])
                    if key in self.count_dict and node['y'] <= 6:
                        self.count_dict[key] += 1
                    else:
                        self.count_dict[key] = 1
                # 计算第一个精英怪出现前的怪物数量
                if node['symbol'] == 'E' and not is_first_elite_appear:
                    is_first_elite_appear = True
                    # tmp_path['monster_count_before_first_elite'] = monster_count_before_first_elite
                    tmp_path_info.monster_count_before_first_elite = monster_count_before_first_elite
                if node['symbol'] == 'M' and not is_first_elite_appear:
                    monster_count_before_first_elite += 1

            # dict extend
            basicProcessPath(path, tmp_path_info)
            if tmp_path_info.elite_count < 2 or tmp_path_info.campfire_count < 2:
                continue
            self.calc_path_score(path, tmp_path_info)
            # before first elite
            # if basic_info['store_before_first_elite'] or basic_info['campfire_before_first_elite']:
            if tmp_path_info.store_before_first_elite or tmp_path_info.campfire_before_first_elite:
                tmp_path_info.score += 3

            self.paths_info.append(tmp_path_info)
        # sort self.count_dict by value and get top 5 items
        self.count_dict = dict(sorted(self.count_dict.items(), key=lambda x: x[1], reverse=True)[:5])
        tmp_sum = 0
        for key in self.count_dict:
            tmp_sum += self.count_dict[key]
        avg = tmp_sum / len(self.count_dict)

        for path_info in self.paths_info:
            for node in path_info.path:
                key = str(node['x']) + '-' + str(node['y'])
                if key in self.count_dict:
                    path_info.score += self.count_dict.get(key, 0) / avg

        # self.paths_info sort by score
        self.choice_bonus()
        self.paths_info = sorted(self.paths_info, key=lambda x: x.score, reverse=True)
        if len(self.paths_info[0].choice_bonus):
            for i, choice in enumerate(self.game_state['choice_list']):
                if self.paths_info[0].choice_bonus[0].choice_bonus_type in choice:
                    self.neow_event_choice = (i, 'no_target')
                    break
        else:
            # merge two dict
            choice_scores = [(STS_Config['events']['neow_event']['1st_blessing'][self.neows_choices[0]]['score'],
                              STS_Config['events']['neow_event']['1st_blessing'][self.neows_choices[0]]['target']),
                             (STS_Config['events']['neow_event']['2nd_blessing'][self.neows_choices[1]]['score'],
                              STS_Config['events']['neow_event']['2nd_blessing'][self.neows_choices[1]]['target']),
                             ]
            t_3rd_blessing_adv = STS_Config['events']['neow_event']['3rd_blessing']['advantages'].copy()
            t_3rd_blessing_dis = STS_Config['events']['neow_event']['3rd_blessing']['disadvantages'].copy()
            score_for_3rd_blessing = 0
            t_3rd_blessing_adv.update(t_3rd_blessing_dis)
            t_3rd_target = ''
            for key in t_3rd_blessing_adv:
                if key in self.neows_choices[2]:
                    score_for_3rd_blessing += t_3rd_blessing_adv[key]['score']
                    if 'target' in t_3rd_blessing_adv[key]:
                        t_3rd_target = t_3rd_blessing_adv[key]['target']
            choice_scores.append((score_for_3rd_blessing, t_3rd_target))
            t_best = max(choice_scores, key=lambda x: x[0])
            self.neow_event_choice = (choice_scores.index(t_best), t_best[1].lower())
        self.best_path = self.paths_info[0]
        # choice = self.neows_choices[self.neow_event_choice]


if __name__ == '__main__':
    with open('../game_state.json', encoding='utf-8') as f:
        gs = json.load(f)
    path_eval = PathEvaluator(gs)
    # visualize_map(path_eval.paths_info[0]['path'])
    # print('done')
