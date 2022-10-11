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

def runAlg(input_data_path, output_data_path, runs, which_robot, remove_low_threshold):
	m_input_data_path = '' # modified data path based on whether one robot or all are being sampled; if all are then no change is made, if one robot is then a new csv is made with just that data
	z_input_data_path = ''
	temp_data_path = os.path.expanduser('./MMEInputCSVs/') + 'temp_MME_Input.csv'
	z_temp_data_path = os.path.expanduser('./MMEInputCSVs/') + 'zero_removal_temp_MME_Input.csv'
	if which_robot == 'all':
		m_input_data_path = input_data_path
	elif which_robot in [0,1,2,3]:
		with open(temp_data_path, "w", newline = '') as ftemp:
			writer = csv.writer(ftemp)
			with open(input_data_path, "r") as fdata:
				reader = csv.reader(fdata)
				line_num = 0
				for row in reader:
					if line_num % 4 == which_robot:
						writer.writerow(row)
					line_num += 1
				fdata.close()
				print("Wrote " + str(line_num/4) + " to temp CSV")
			ftemp.close()
		m_input_data_path = temp_data_path
		
	if remove_low_threshold == False:
		z_input_data_path = m_input_data_path
	else:
		with open(z_temp_data_path, "w", newline = '') as ztemp:
			writer = csv.writer(ztemp)
			with open(m_input_data_path, "r") as fdata:
				reader = csv.reader(fdata)
				line_num = 0
				#if the last column is low, don't add it to the z_temp csv
				for row in reader:
					if float(row[-1]) > remove_low_threshold:
						writer.writerow(row)
						line_num += 1
				print("Wrote " + str(line_num) + " to temp CSV after low value removal")
		z_input_data_path = z_temp_data_path
				
				
			
	# open temp data path, go through the last column to see if it is less than 

	for i in range(runs):
		t = time.time()
		p = subprocess.Popen([os.path.expanduser('test.exe'), z_input_data_path], text = True, stdout=subprocess.PIPE, encoding="utf")

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
	
def runMME_with_xy_outputs(path_to_MME_input_data, path_to_MME_output_data, loop_num, which_robot, low_value_threshold):
	# path_to_MME_input_data = '../../CollectiveTransport_to_MME_parser/MMEInputCSVs'
	# path_to_MME_output_data = '../../CollectiveTransport_to_MME_parser/MMEOutputCSVs'

	for _ in range(loop_num):
		s0 = time.time()
		s = time.time()
		runAlg(path_to_MME_input_data, path_to_MME_output_data, 1, which_robot, low_value_threshold)
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

####
## Runs MME on an input CSV
#	change_params_bool : boolean for changing the config.json parameters
#	num_loops : number of time to run MME for each configuration combination
#	param_str : string for the item name from the config.json to edit
# 	param_list: list of values to run for the modified item in the config file

def runMME_different_config(change_params_bool, which_robot, low_value_threshold, path_to_MME_input_data, path_to_MME_output_data, num_loops, path_to_input_json, path_to_output_json, param1_str, param1_list, param2_str, param2_list):
	if change_params_bool:
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
				runMME_with_xy_outputs(path_to_MME_input_data, path_to_MME_output_data, num_loops, which_robot, low_value_threshold)          # Run mme with new parameters, loop n times for more data
	else:
		runMME_with_xy_outputs(path_to_MME_input_data, path_to_MME_output_data, num_loops, which_robot, low_value_threshold)

def main():
	mmeFilesArray = ['/2022-10-10_GateFilterTest1/DDPG_gate_FilterTest_x.csv', 
					'/2022-10-10_GateFilterTest1/DDPG_gate_FilterTest_y.csv'
					]
	for i in range(len(mmeFilesArray)):
		path_to_MME_input_data = os.path.expanduser('./MMEInputCSVs') + mmeFilesArray[i]
		print(path_to_MME_input_data)
		path_to_MME_output_data = os.path.expanduser('./MMEOutputCSVs') + mmeFilesArray[i]
		print(path_to_MME_output_data)
		complexity_list = [14,18]
		maxRMSclamp_list = [1,3]
		runMME_different_config(change_params_bool=True, which_robot = 'all', low_value_threshold= False, path_to_MME_input_data=path_to_MME_input_data, path_to_MME_output_data=path_to_MME_output_data, num_loops=3, path_to_input_json='./jsonBackup/config.json', path_to_output_json='config.json', param1_str='complexity', param1_list=complexity_list, param2_str='maxRMSclamp', param2_list=maxRMSclamp_list)
	# runMME_different_config(False, 'all', False, path_to_MME_input_data, path_to_MME_output_data, 3, 'jsonBackup/config.json', 'config.json', 'targetComplexity', complexity_list, 'maxRMSClamp', maxRMSclamp_list)
	# maybe run with even lower rms clamps and discard beginning data points (if 10 was too few)

if __name__ == '__main__':
	main()
