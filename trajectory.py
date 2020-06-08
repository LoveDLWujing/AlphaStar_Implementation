#!/usr/bin/env python
from pysc2.lib import features, point, actions, units
from pysc2.env.environment import TimeStep, StepType
from pysc2.env import sc2_env, available_actions_printer
from pysc2 import run_configs
from s2clientprotocol import sc2api_pb2 as sc_pb

import importlib
import random
import sys
import glob

from absl import app, flags
FLAGS = flags.FLAGS
FLAGS(sys.argv)

function_dict = {}
for _FUNCTION in actions._FUNCTIONS:
    #print(_FUNCTION)
    function_dict[_FUNCTION.ability_id] = _FUNCTION.name

race_list = ['Terran', 'Zerg', 'Protoss']

# from trajectory import get_random_trajectory
# get_random_trajectory(source='/media/kimbring2/Steam1/StarCraftII/Replays/4.8.2.71663-20190123_035823-1/', home_race=1, away_race=1, replay_filter=3500)
# import sys, importlib
# importlib.reload(sys.modules['trajectory'])
def get_random_trajectory(source, home_race, away_race, replay_filter, filter_repeated_camera_moves=True):
	run_config = run_configs.get()
	sc2_proc = run_config.start()
	controller = sc2_proc.controller

	#root_path = '/media/kimbring2/Steam1/StarCraftII/Replays/4.8.2.71663-20190123_035823-1/'
	root_path = source
	file_list = glob.glob(root_path + '*.*')
	#print ("file_list: {}".format(file_list))

	for i in range(50):
		#print("i: " + str(i))

		replay_file_path = random.choice(file_list)
		#print ("replay_file_path: {}".format(replay_file_path))
		#replay_file_path_0 = root_path + '/0a0f62052fe4311368910ad38c662bf979e292b86ad02b49b41a87013e58c432.SC2Replay'
		#replay_file_path_1 = root_path + '/0a1b09abc9e98f4e0c3921ae0a427c27e97c2bbdcf34f50df18dc41cea3f3249.SC2Replay'
		#replay_file_path_2 = root_path + '/0a01d32e9a98e1596b88bc2cdec7752249b22aca774e3305dae2e93efef34be3.SC2Replay'
		#replay_file_path_0 = human_data

		try: 
			replay_data = run_config.replay_data(replay_file_path)
			ping = controller.ping()
			info = controller.replay_info(replay_data)
			#print("ping: " + str(ping))
			print("replay_info: " + str(info))

			player0_race = info.player_info[0].player_info.race_actual
			player0_mmr = info.player_info[0].player_mmr
			player0_apm = info.player_info[0].player_apm
			player0_result = info.player_info[0].player_result.result
			#print("player0_race: " + str(player0_race))
			#print("player0_mmr: " + str(player0_mmr))
			#print("player0_apm: " + str(player0_apm))
			#print("player0_result: " + str(player0_result))

			home_race = race_list.index(home_race) + 1
			if (home_race == player0_race):
				print("player0_race pass ")
			else:
				continue

			player1_race = info.player_info[0].player_info.race_actual
			player1_mmr = info.player_info[0].player_mmr
			player1_apm = info.player_info[0].player_apm
			player1_result = info.player_info[0].player_result.result
			#print("player1_race: " + str(player1_race))
			#print("player1_mmr: " + str(player1_mmr))
			#print("player1_apm: " + str(player1_apm))
			#print("player1_result: " + str(player1_result))
			#if (away_race == player1_race):
			#	print("player1_race pass ")
			#else:
			#	continue

			if (player0_mmr >= replay_filter):
				print("player0_mmr pass ")
			else:
				continue

			screen_size_px = (128, 128)
			minimap_size_px = (64, 64)
			player_id = 1
			discount = 1.
			step_mul = 1

			screen_size_px = point.Point(*screen_size_px)
			minimap_size_px = point.Point(*minimap_size_px)
			interface = sc_pb.InterfaceOptions(raw=False, score=True,
				feature_layer=sc_pb.SpatialCameraSetup(width=24))
			screen_size_px.assign_to(interface.feature_layer.resolution)
			minimap_size_px.assign_to(interface.feature_layer.minimap_resolution)

			map_data = None
			if info.local_map_path:
				map_data = run_config.map_data(info.local_map_path)

			_episode_length = info.game_duration_loops
			_episode_steps = 0

			controller.start_replay(sc_pb.RequestStartReplay(replay_data=replay_data, 
				map_data=map_data, options=interface,
				observed_player_id=player_id))

			_state = StepType.FIRST

			if (info.HasField("error") or
			                    info.base_build != ping.base_build or  # different game version
			                    info.game_duration_loops < 1000 or
			                    len(info.player_info) != 2):
				# Probably corrupt, or just not interesting.
				print("error")
				continue

			feature_screen_size = 128
			feature_minimap_size = 64
			rgb_screen_size = None
			rgb_minimap_size = None
			action_space = None
			use_feature_units = True
			agent_interface_format = sc2_env.parse_agent_interface_format(
				feature_screen=feature_screen_size,
				feature_minimap=feature_minimap_size,
				rgb_screen=rgb_screen_size,
				rgb_minimap=rgb_minimap_size,
				action_space=action_space,
				use_feature_units=use_feature_units)

			_features = features.features_from_game_info(controller.game_info())

			build_info = []
			replay_step = 0
			while True:
				replay_step += 1
				print("replay_step: " + str(replay_step))

				controller.step(step_mul)
				obs = controller.observe()

				if (len(obs.actions) != 0):
					action = (obs.actions)[0]
					action_spatial = action.action_feature_layer
					unit_command = action_spatial.unit_command
					ability_id = unit_command.ability_id
					function_name = function_dict[ability_id]
					if (function_name != 'build_queue'):
						function_name_parse = function_name.split('_')

						function_name_first = function_name_parse[0]
						#print("function_name_first: " + str(function_name_first))
						if (function_name_first == 'Build' or function_name_first == 'Train'):
							unit_name = function_name_parse[1]
							#print("function_name_parse[1]: " + str(function_name_parse[1]))
							build_info.append(unit_name)

				if obs.player_result: # Episide over.
					_state = StepType.LAST
					discount = 0

				else:
					discount = discount

					_episode_steps += step_mul

				agent_obs = _features.transform_obs(obs)
				step = TimeStep(step_type=_state, reward=0,
			                    discount=discount, observation=agent_obs)

				score_cumulative = agent_obs['score_cumulative']
				score_cumulative_dict = {}
				score_cumulative_dict['score'] = score_cumulative.score
				score_cumulative_dict['idle_production_time'] = score_cumulative.idle_production_time
				score_cumulative_dict['idle_worker_time'] = score_cumulative.idle_worker_time
				score_cumulative_dict['total_value_units'] = score_cumulative.total_value_units
				score_cumulative_dict['total_value_structures'] = score_cumulative.total_value_structures
				score_cumulative_dict['killed_value_units'] = score_cumulative.killed_value_units
				score_cumulative_dict['killed_value_structures'] = score_cumulative.killed_value_structures
				score_cumulative_dict['collected_minerals'] = score_cumulative.collected_minerals
				score_cumulative_dict['collected_vespene'] = score_cumulative.collected_vespene
				score_cumulative_dict['collection_rate_minerals'] = score_cumulative.collection_rate_minerals
				score_cumulative_dict['collection_rate_vespene'] = score_cumulative.collection_rate_vespene
				score_cumulative_dict['spent_minerals'] = score_cumulative.spent_minerals
				score_cumulative_dict['spent_vespene'] = score_cumulative.spent_vespene

				if obs.player_result:
					break

				_state = StepType.MID


			return build_info, score_cumulative_dict
		except:
			continue

