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

		with open(output_data_path, "a") as f2:
			writer = csv.writer(f2)
			# f2.write(eqn + "," + score + "," + accuracy + "," + complexity + "," + generation + "\n")
			writer.writerow([eqn, score, accuracy, complexity, generation])
			
		deltaT = time.time() - t
		run = i+1
		print("Run " + str(run) + ": " + str(deltaT))
	
def runMME_with_xy_outputs():
    pass

def edit_json_params(json_dict, complexity, maxRMSClamp):
    json_dict["targetComplexity"] = complexity
    json_dict["maxRMSClamp"] = maxRMSClamp
    
def runMME_different_config(path_to_input_json, path_to_output_json):
    complexity_list = [6,8,9,10,12,14]
    maxRMSclamp_list = [5,10,20,30,40,50]
    with open(path_to_input_json, 'r+') as f:
        config = json.load(f)

    for i in range(len(complexity_list)):
        for j in range(len(maxRMSclamp_list)):
            edit_json_params(config, complexity_list[i], maxRMSclamp_list[j])
            #print newline, then line to output csv about metaparameters changed
            #run mme maybe 5 times to get general idea

    with open(path_to_output_json, 'w', encoding='utf-8') as f:
        json.dump(config, f, ensure_ascii=False, indent=4)


def main():
    runMME_different_config('jsonBackup/config.json', 'config.json')

if __name__ == '__main__':

	# path_to_MME_input_data = '../../CollectiveTransport_to_MME_parser/MMEInputCSVs'
	# path_to_MME_output_data = '../../CollectiveTransport_to_MME_parser/MMEOutputCSVs'
	path_to_MME_input_data = os.path.expanduser('./MMEInputCSVs')
	path_to_MME_output_data = os.path.expanduser('./MMEOutputCSVs')

	for i in range(5):
		s0 = time.time()
		s = time.time()
		runAlg(path_to_MME_input_data + '/DDPG4_ep90_Data_y.csv', path_to_MME_output_data + '/MMEout_DDPG4_ep90_y.csv', 10)
		deltaSy = time.time() - s
		print("Total Y Time: " + str(deltaSy))

		s = time.time()
		runAlg(path_to_MME_input_data + '/DDPG4_ep90_Data_x.csv', path_to_MME_output_data + '/MMEout_DDPG4_ep90_x.csv', 10)
		deltaSx = time.time() - s
		print("Total X Time: " + str(deltaSx))

		deltaS = time.time() - s0
		# print("Total Y Time: " + str(deltaSy))
		print("Total Time: " + str(deltaS))

	
#fixed number of controlled organisms, using grown organisms for locomotion
# And, But, Therefore - need, approach, benefit, computation