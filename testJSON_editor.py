import json


def edit_json_params(json_dict, param1_str, param1_list, param2_str, param2_list):
    json_dict[param1_str] = param1_list
    json_dict[param2_str] = param2_list
    
def change_json_file(path_to_input_json, path_to_output_json, param1_str, param1_list, param2_str, param2_list):
    with open(path_to_input_json, 'r+') as f:
        config = json.load(f)

    for i in range(len(param1_list)):
        for j in range(len(param2_list)):
            edit_json_params(config, param1_str, param1_list[i], param2_str, param2_list[i])
            #print newline, then line to output csv about metaparameters changed
            #run mme maybe 5 times to get general idea

    with open(path_to_output_json, 'w', encoding='utf-8') as f:
        json.dump(config, f, ensure_ascii=False, indent=4)

def main():
    complexity_list = [6,8,9,10,12,80]
    maxRMSclamp_list = [5,10,20,30,40,50]
    change_json_file('jsonBackup/config.json', 'outputJSON.json', 'targetComplexity', complexity_list, 'maxRMSClamp', maxRMSclamp_list)

if __name__ == '__main__':
    main()