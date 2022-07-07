import csv
import subprocess
import random
import math
import time
import os
import json



def populate_default_data(data_path, num_lines):
	rows = ""

	for i in range(num_lines):
		x1 = random.random() * 10
		x2 = random.random() * 10
		y = nn(x1, x2)
		rows += str(x1) + "," +  str(x2) + "," +  str(y) + "\n"

	with open(data_path, "w") as f:
		f.write(rows)
	
def nn(var0, var1):
	return ((var0 * var1) + 10 * (var1 ** 2))

def runAlg(input_data_path, output_data_path, runs):
	for i in range(runs):
		t = time.time()
		p = subprocess.Popen([os.path.expanduser('test.exe'), input_data_path], text = True, stdout=subprocess.PIPE, encoding="utf")

		eqn = ""
		score = ""
		accuracy = ""
		complexity = ""
		generation = ""

		for line in iter(p.stdout.readline,''):
			print(line)
			if line.rstrip().__contains__("Final Best GenPop:"):
				eqn = str(line.rstrip()[19:])
				# eqn = eqn.replace(",", "'")
			elif line.rstrip().__contains__("Final Score:"):
				score = str(line.rstrip()[19:])
			elif line.rstrip().__contains__("Final Accuracy:"):
				accuracy = str(line.rstrip()[19:])
			elif line.rstrip().__contains__("Final Complexity:"):
				complexity = str(line.rstrip()[19:])
			elif line.rstrip().__contains__("starting generation "):
				generation = str(line.rstrip()[20:])

		with open(output_data_path, "a", newline = '') as f2:
			writer = csv.writer(f2)
			# f2.write(eqn + "," + score + "," + accuracy + "," + complexity + "," + generation + "\n")
			writer.writerow([eqn, score, accuracy, complexity, generation])
			
		deltaT = time.time() - t
		run = i+1
		print("Run " + str(run) + ": " + str(deltaT))
	
def runMME_with_xy_outputs(path_to_MME_input_data, path_to_MME_output_data, loop_num):
    # path_to_MME_input_data = '../../CollectiveTransport_to_MME_parser/MMEInputCSVs'
	# path_to_MME_output_data = '../../CollectiveTransport_to_MME_parser/MMEOutputCSVs'

	for _ in range(loop_num):
		s0 = time.time()
		s = time.time()
		runAlg(path_to_MME_input_data, path_to_MME_output_data, 1)
		deltaSy = time.time() - s
		print("Total Y Time: " + str(deltaSy))

		# s = time.time()
		# runAlg(path_to_MME_input_data + '/DQN_from_ep170_Episode_160_x.csv', path_to_MME_output_data + '/MMEout_DQN_from_ep170_Episode_160_x.csv', loop_num)
		# deltaSx = time.time() - s
		# print("Total X Time: " + str(deltaSx))

		deltaS = time.time() - s0
		# print("Total Y Time: " + str(deltaSy))
		print("Total Time: " + str(deltaS))


def edit_json_params(json_dict, param1_str, param1_list, param2_str, param2_list):
    json_dict[param1_str] = param1_list
    json_dict[param2_str] = param2_list
    
def runMME_different_config(path_to_MME_input_data, path_to_MME_output_data, path_to_input_json, path_to_output_json, param1_str, param1_list, param2_str, param2_list):
    with open(path_to_input_json, 'r+') as f:
        config = json.load(f)

    for i in range(len(param1_list)):
        for j in range(len(param2_list)):
            edit_json_params(config, param1_str, param1_list[i], param2_str, param2_list[j])  # Edits the json parameters
            with open(path_to_output_json, 'w', encoding='utf-8') as f:                         # Writes new parameters to file
                json.dump(config, f, ensure_ascii=False, indent=4)
            #print newline, then line to output csv about metaparameters changed
            with open(path_to_MME_output_data, "a", newline = '') as f2:
                writer = csv.writer(f2)
                writer.writerow('')
                writer.writerow([str(param1_str + '=' + str(param1_list[i]) + ', ' + param2_str + '=' + str(param2_list[j]))])
            runMME_with_xy_outputs(path_to_MME_input_data, path_to_MME_output_data, 3)          # Run mme with new parameters, loop 3 times for more data


def main():
    path_to_MME_input_data = os.path.expanduser('./MMEInputCSVs') + '/DDPG4_ep90_Data_y.csv'
    path_to_MME_output_data = os.path.expanduser('./MMEOutputCSVs') + '/MMEout_DDPG4_ep90_y.csv'
    complexity_list = [8,10]
    maxRMSclamp_list = [0.001, 0.01, 0.05, 0.5]
    runMME_different_config(path_to_MME_input_data, path_to_MME_output_data, 'jsonBackup/config.json', 'config.json', 'targetComplexity', complexity_list, 'maxRMSClamp', maxRMSclamp_list)


if __name__ == '__main__':
    path_to_MME_input_data = os.path.expanduser('./MMEInputCSVs') + '/DQN_from_ep120_Episode_100_y.csv'
    path_to_MME_output_data = os.path.expanduser('./MMEOutputCSVs') + '/MMEout_DQN_from_ep120_Episode_100_y.csv'
    runMME_with_xy_outputs(path_to_MME_input_data, path_to_MME_output_data, 5)
	
	
#fixed number of controlled organisms, using grown organisms for locomotion
# And, But, Therefore - need, approach, benefit, computation