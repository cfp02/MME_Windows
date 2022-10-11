import math
import numpy as np
import re
import csv
import os
import matplotlib.pyplot as plt

### Global Variables
columns = {
    'force_mag' : [],       # polar, not used
    'force_angle' : [],     # polar, not used
    'force_x' : [],         ## calculated
    'force_y' : [],         ## calculated
    'cyl_x_pos' : [],       
    'cyl_y_pos' : [],
    'cyl_dist2robot' : [],  # polar, not used
    'cyl_angle2robot' : [], # polar, not used
    'cyl_x2robot' : [],     # calculated
    'cyl_y2robot' : [],     # calculated
    'cyl_dist2goal' : [],
    'robot_x_pos' : [],
    'robot_y_pos' : [],
    'robot_angle' : [],
    'robotdist2goal' : [],  # polar, not used
    'robotangle2goal' : [], # polar, not used
    'robotx2goal' : [],     # calculated
    'roboty2goal' : [],     # calculated
    'robot_lwheel' : [],
    'robot_rwheel' : [], 
    # 'next_force_x' : [],    # calculated and gotten from next row, this will always be sized one less than the others since it is started at the second row
    # 'next_force_y' : [],    # calculated and gotten from next row

    

    # Priors, each with a full vector, distance, inverse of distance, and unit vector (direction) variable
    'pRobot2Goal_vect' : [],
    'pRobot2Goal_dist' : [],
    'pRobot2Goal_inv' : [],
    'pRobot2Goal_dir' : [],
    'pCyl2Goal_vect' : [],
    'pCyl2Goal_dist' : [],
    'pCyl2Goal_inv' : [],
    'pCyl2Goal_dir' : [],
    'pRobot2Cyl_vect' : [],
    'pRobot2Cyl_dist' : [],
    'pRobot2Cyl_inv' : [],
    'pRobot2Cyl_dir' : [],
    
    'deltaForce' : [],

    'env_observations' : [],
    'agent_actions' : [],
    # proxVals is a 4x24 array of 24 proximity sensor values for each robot
    'proxVals' : [],

    ## Values calculated from the proximity sensors:
    'proxVals_avg' : [],    # Average of the 24 proximity sensor values for each robot
    'proxVals_max' : [],    # Maximum of the 24 proximity sensor values for each robot
    'proxVals_whichTouchCylinder' : [], # Which proximity sensors are touching the cylinder for each robot
    'proxVals_notTouchingCylinderAvg' : [], # Average of the 24 proximity sensor values for each robot that are not touching the cylinder
}

file_path_to_collective_transport_output_CSVs = ''
file_path_to_MME_input_CSVs = ''
file_path_to_MME_output_CSVs = ''
total_line_count = 0 # only incremented when actual data is read in, skipped when header is read and when buffer is skipped
tof_buffer = 10  # number of CSV lines to skip to account for the robots trying to find the cylinder
world_size = [20,10]

### Global Variables

def merge(list1, list2):
      
    merged_list = [[list1[i], list2[i]] for i in range(0, len(list1))]
    return merged_list

def p2c_on_list(magList, degList):
    xList = [0] * len(magList)
    yList = [0] * len(magList)
    for i in range(len(magList)):
        xList[i] = magList[i] * math.cos(degList[i])
        yList[i] = magList[i] * math.sin(degList[i])
    return xList,yList


def polar_to_cartesian(mag, deg):
    x_comp = mag * math.cos(deg)
    y_comp = mag* math.sin(deg)
    return x_comp, y_comp

def remove_zeros(row):
    retRow = 0
    
    return retRow


## Check row for filtering criteria (for proximity sensors)
# Returns false if the row should be filtered out
def checkRow(row, filter_type, range_min, range_max):

    ## Filters by x-value of cylinder
    if(filter_type == 'filter_x'):
        x_pos_for_row = float(row['cyl_x_pos'])
        #print(x_pos_for_row)
        # Returns true if in the range
        if(x_pos_for_row > range_min and x_pos_for_row < range_max):
            return True
        else:
            return False


## Takes the proxVals 2d array and returns the 4 average prox values for the robots
def avgProxForRobot(proxVals):
    avgProxVals = [0] * 4
    for i in range(4):
        avgProxVals[i] = sum(proxVals[i])/len(proxVals[i])
    return avgProxVals

## Takes the proxVals 2d array and returns the 4 max prox values for the robots
def maxProxForRobot(proxVals):
    maxProxVals = [0] * 4
    for i in range(4):
        maxProxVals[i] = max(proxVals[i])
    return maxProxVals

# Determines which proxmimity sensors are touching the cylinder for each robot 
# using previous and current proximity sensor values
def proxSensorsTouchingCylinder(proxVals):
    
    whichProxSensorsActivated = [[0] * 24 for i in range(4)]
    whichProxSensorsTouchingCylinder = [[0] * 8 for i in range(4)]
    for i in range(4):
        for j in range(24):
            if proxVals[i][j] > 0.9:
                whichProxSensorsActivated[i][j] = True
            else:
                whichProxSensorsActivated[i][j] = False
        # Find which prox sensors are touching the cylinder by checking for at least 3 activated sensors in a row
        for j in range(24):
            if whichProxSensorsActivated[i][(j-1)%24] and whichProxSensorsActivated[i][j] and whichProxSensorsActivated[i][(j+1)%24]:
                whichProxSensorsTouchingCylinder[i] = \
                [(i-3)%24, (i-2)%24, (i-1)%24, i, (i+1)%24, (i+2)%24, (i+3)%24, (i+4)%24]
    return(whichProxSensorsTouchingCylinder)
                    
def avgProxForRobot_notTouchingCylinder(proxVals, proxSensorsTouchingCylinder):
    avgProxVals = [0] * 4
    for i in range(4):
        for j in range(24):
            if j not in proxSensorsTouchingCylinder[i]:
                avgProxVals[i] += proxVals[i][j]
        avgProxVals[i] /= len(proxVals[i]) - len(proxSensorsTouchingCylinder[i])
    return avgProxVals
 


#############################################
## Takes a Collective Transport output CSV and reads in relevant columns and appends them to lists of the corresponding data.
# Also currently filters out rows that are not within the specified range of the x-value of the cylinder
## Can be called multiple times on all of the files in a folder
#############################################
def parse_NN_CSV(input_CSV_path, filter_type, range_min, range_max):

    with open(input_CSV_path, mode='r') as csv_file:
        global total_line_count
        line_count = 0
        csv_reader = csv.DictReader(csv_file)

        for row in csv_reader:

            # Skip the first 10 lines of the CSV to account for the robots trying to find the cylinder
            if line_count == 0:
                print(f'Column names are {", ".join(row)}')
                line_count += 1
            
            if line_count < tof_buffer:
                line_count += 1
                continue


            ##
            ## Read in all of the variables from the CSV
            ##

            agentActions = []

            envObsArray = [[float(d) for d in e] for e in [e.split(',') for e in (re.sub(r"[\n\t\s]*", "", (row['env_observations'][8:-18]))).split('],dtype=float32),array([')]]

            
            ##    
            ## Lists with 4 elements (one per robot)
            ##

            # CSV columns that already has 4 (or 1) variables in each cell
            force_mag = [float(e) for e in (row['force magnitude'][1:-1]).strip(" ").split(',')]
            force_angle = [float(e) for e in (row['force angle'][1:-1]).strip(" ").split(',')]
            cyl_x_pos = [float(row['cyl_x_pos'])] * 4
            cyl_y_pos = [float(row['cyl_y_pos'])] * 4
            robot_x_pos = [float(e) for e in (row['robots_x_pos'][1:-1]).strip(" ").split(',')]
            robot_y_pos = [float(e) for e in (row['robots_y_pos'][1:-1]).strip(" ").split(',')]
            robot_angle = [float(e) for e in (row['robot_angle'][1:-1]).strip(" ").split(',')]
            # cyl_angle2goal = [float(e) for e in (row['cyl_angle2goal'][1:-1]).strip(" ").split(',')]
            cyl_angle2goal = [float(row['cyl_angle2goal'])] * 4

            # Need to parse the env_observations column for each robot's vals as it is just one big array
            robotdist2goal = []
            robotangle2goal = []
            robot_lwheel = []
            robot_rwheel = []
            cyl_dist2robot = []
            cyl_angle2robot = []
            cyl_dist2goal = []
            for i in range(4): # 4 robots
                robotdist2goal.append(envObsArray[i][0])
                robotangle2goal.append(envObsArray[i][1])
                robot_lwheel.append(envObsArray[i][2])
                robot_rwheel.append(envObsArray[i][3])
                cyl_dist2robot.append(envObsArray[i][4])
                cyl_angle2robot.append(envObsArray[i][5])
                cyl_dist2goal.append(envObsArray[i][6])
            
            # Parse env_observations for proximity sensor values
            prox_sensors = []
            for i in range(4): #makes a 4x24 array
                prox_sensors.append(envObsArray[i][7:])
                

            # Calculate the non-given values (polar to cartesion conversions)
            force_x , force_y = p2c_on_list(force_mag, force_angle)
            cyl_x2robot, cyl_y2robot = p2c_on_list(cyl_dist2robot, cyl_angle2robot)
            robotx2goal ,roboty2goal = p2c_on_list(robotdist2goal, robotangle2goal)


            ###############################
            ###############################


            ## Perform filter checks before saving row data
            # if the x-value of the cylinder is not in the range -4 and 5, don't keep range
            
            if(checkRow(row, filter_type, range_min, range_max) == True):
                #print("Skipping row due to filter_x")
                continue


            ###############################
            ###############################



            ##
            ## Append temp lists to the general arrays of values for each variable
            ##
            columns['force_mag'].append(force_mag)
            columns['force_angle'].append(force_angle)
            columns['cyl_x_pos'].append(cyl_x_pos)
            columns['cyl_y_pos'].append(cyl_y_pos)
            columns['cyl_dist2robot'].append(cyl_dist2robot)
            columns['cyl_angle2robot'].append(cyl_angle2robot)
            columns['cyl_dist2goal'].append(cyl_dist2goal)
            columns['robot_x_pos'].append(robot_x_pos)
            columns['robot_y_pos'].append(robot_y_pos)
            columns['robotdist2goal'].append(robotdist2goal)
            columns['robotangle2goal'].append(robotangle2goal)
            columns['robot_lwheel'].append(robot_lwheel)
            columns['robot_rwheel'].append(robot_rwheel)
            columns['robot_angle'].append(robot_angle)
            # columns['env_observations'].append(envObsArray) #makes it huge and not necessary to keep as data
            columns['agent_actions'].append(agentActions)
            columns['proxVals'].append(prox_sensors)
            ## Append the other 6 calculated variables to be updated
            columns['force_x'].append(force_x)
            columns['force_y'].append(force_y)
            columns['cyl_x2robot'].append(cyl_x2robot)
            columns['cyl_y2robot'].append(cyl_y2robot)
            columns['robotx2goal'].append(robotx2goal)
            columns['roboty2goal'].append(roboty2goal)
            # if line_count != 1: # if on the first data line, there is no previous line to put data into
            #     columns['next_force_x'].append(force_x)
            #     columns['next_force_y'].append(force_y)

            global world_size
            world_size_array = np.array([world_size] * 4)

            cyl2goal_global_x, cyl2goal_global_y = p2c_on_list(cyl_dist2goal, cyl_angle2goal)

            cyl2goal_x = [cyl2goal_global_x[0] * math.cos(-robot_angle[robot]) - cyl2goal_global_y[0] * math.sin(-robot_angle[robot]) for robot in range(4)]
            cyl2goal_y = [cyl2goal_global_x[0] * math.sin(-robot_angle[robot]) + cyl2goal_global_y[0] * math.cos(-robot_angle[robot]) for robot in range(4)]

            robot2goal_vect = np.array(merge(robotx2goal, roboty2goal))
            cyl2goal_vect = np.array(merge(cyl2goal_x, cyl2goal_y))
            robot2cyl_vect = np.array(merge(cyl_x2robot, cyl_y2robot))
            
            ## All lists are of size [lengthOfCSV][numRobots][2]
            columns['pRobot2Goal_vect'].append((robot2goal_vect/world_size_array).tolist())
            columns['pRobot2Goal_dist'].append([[(math.sqrt(robot[0]**2 + robot[1]**2))/math.sqrt(world_size[0]**2 + world_size[1]**2) for _ in range(2)] for robot in robot2goal_vect])
            columns['pRobot2Goal_inv'].append([[1/robot[0]] * 2 for robot in columns['pRobot2Goal_dist'][-1]])
            columns['pRobot2Goal_dir'].append((robot2goal_vect/[[math.sqrt(robot[0]**2 + robot[1]**2) for _ in range (2)] for robot in robot2goal_vect]).tolist())
            columns['pCyl2Goal_vect'].append((cyl2goal_vect/world_size_array).tolist())
            columns['pCyl2Goal_dist'].append([[(math.sqrt(robot[0]**2 + robot[1]**2))/math.sqrt(world_size[0]**2 + world_size[1]**2) for _ in range(2)] for robot in cyl2goal_vect])
            columns['pCyl2Goal_inv'].append([[1/robot[0]] * 2 for robot in columns['pCyl2Goal_dist'][-1]])
            columns['pCyl2Goal_dir'].append((cyl2goal_vect/[[math.sqrt(robot[0]**2 + robot[1]**2) for _ in range(2)] for robot in cyl2goal_vect]).tolist())
            columns['pRobot2Cyl_vect'].append((robot2cyl_vect/world_size_array).tolist())
            columns['pRobot2Cyl_dist'].append([[math.sqrt(robot[0]**2 + robot[1]**2) for _ in range(2)] for robot in robot2cyl_vect])
            columns['pRobot2Cyl_inv'].append([[1/robot[0]] * 2 for robot in columns['pRobot2Cyl_dist'][-1]])
            columns['pRobot2Cyl_dir'].append((robot2cyl_vect/[[math.sqrt(robot[0]**2 + robot[1]**2) for _ in range (2)] for robot in robot2cyl_vect]).tolist())


            ##
            ## Do Calculations on the proximity sensor values
            ##

            # Agv Prox Sensor Data, stores a list of length 4
            columns['proxVals_avg'].append(avgProxForRobot(prox_sensors))

            
            proxTouchingCylinder = proxSensorsTouchingCylinder(prox_sensors)
            columns['proxVals_whichTouchCylinder'] = proxTouchingCylinder
            # # Determine which sensors touch the cylinder
            # columns['proxVals_notTouchingCylinderAvg'].append(proxSensorsTouchingCylinder())
            # columns['proxVals_whichTouchCylinder'].append(proxSensorsTouchingCylinder())
           
            # Average of prox sensors not touching the cylinder
            avgProxValsNotTouchingCylinder = avgProxForRobot_notTouchingCylinder(prox_sensors, proxTouchingCylinder)
            columns['proxVals_notTouchingCylinderAvg'].append(avgProxValsNotTouchingCylinder)
            # Average of sensor quadrants 

            # Determine direction of obstacle based on prox sensor data, filtering out ones touching the cylinder

            # Calculate max prox sensor value for each robot



            line_count += 1
            total_line_count += 1
            
        # print(columns)  
        print(f'Processed {line_count} lines from ' + input_CSV_path)


#############################################
# Takes in parsed data and converts it into a row for MME interpretation
# row : row number for reference in dictionary
# robot : which robot of the four
# xORy : either x or y data
# useProx : whether or not to use proximity sensor data
#############################################

def get_single_row(row, robot, xORy, useProx):
    var0, var1, var2, var3, var4, var5, var6, var7, var8, var9, var10, var11, output = 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0
    prox0, prox1, prox2, prox3, prox4, prox5, prox6, prox7, prox8, prox9, prox10, prox11, prox12, prox13, prox14, prox15, prox16, prox17, prox18, prox19, prox20, prox21, prox22, prox23 = 0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0
    proxAvg, proxNotTouchingAvg = 0, 0
    if useProx:
        # print("Row is this:\n" + str(row))
        # print("Proxavg is this: " + str(columns['proxVals_avg'][row][robot]))
        proxAvg = columns['proxVals_avg'][robot]
        proxNotTouchingAvg = columns['proxVals_notTouchingCylinderAvg'][robot]
        prox0, prox1, prox2, prox3, prox4, prox5, prox6, prox7, prox8, prox9, prox10, prox11, prox12, prox13, prox14, prox15, prox16, prox17, prox18, prox19, prox20, prox21, prox22, prox23 = columns['proxVals'][row][robot]
    dim = 0
    if xORy == 'x':
        dim = 0
    elif xORy == 'y':
        dim = 1
    var0 = columns['pRobot2Goal_vect'][row][robot][dim]
    var1 = columns['pRobot2Goal_dist'][row][robot][dim]
    var2 = columns['pRobot2Goal_inv'][row][robot][dim]
    var3 = columns['pRobot2Goal_dir'][row][robot][dim]
    var4 = columns['pCyl2Goal_vect'][row][robot][dim]
    var5 = columns['pCyl2Goal_dist'][row][robot][dim]
    var6 = columns['pCyl2Goal_inv'][row][robot][dim]
    var7 = columns['pCyl2Goal_dir'][row][robot][dim]
    var8 = columns['pRobot2Cyl_vect'][row][robot][dim]
    var9 = columns['pRobot2Cyl_dist'][row][robot][dim]
    var10 = columns['pRobot2Cyl_inv'][row][robot][dim]
    var11 = columns['pRobot2Cyl_dir'][row][robot][dim]
    if dim:
        output = columns['force_x'][row+1][robot] - columns['force_x'][row][robot]
        # output = columns['robot_lwheel'][row+1][robot] - columns['robot_lwheel'][row][robot]
    else:
        output = columns['force_y'][row+1][robot] - columns['force_y'][row][robot]
        # output = columns['robot_rwheel'][row+1][robot] - columns['robot_rwheel'][row][robot]
    if useProx:
        return [var0, var1, var2, var3, var4, var5, var6, var7, var8, var9, var10, var11, prox0, prox1, prox2, prox3, prox4, prox5, prox6, prox7, prox8, prox9, prox10, prox11, prox12, prox13, prox14, prox15, prox16, prox17, prox18, prox19, prox20, prox21, prox22, prox23, proxAvg, proxNotTouchingAvg, output]
    else:
        return [var0, var1, var2, var3, var4, var5, var6, var7, var8, var9, var10, var11, output]



#############################################
# Takes the row number, the robot number, and whether the x or y-value is being solved for and returns a row formatted for MME
# 
#############################################
def get_single_row_old(row, robot, xORy):
    if xORy == 'x':
        csv_row = [
            columns['robot_x_pos'][row][robot], 
            columns['cyl_x_pos'][row][robot], 
            columns['robot_lwheel'][row][robot], 
            columns['robot_rwheel'][row][robot], 
            columns['cyl_x2robot'][row][robot], 
            columns['robotx2goal'][row][robot], 
            # columns['robot_angle'],
            columns['force_x'][row][robot],   
            columns['force_x'][row+1][robot], # force from next row
        ]
    elif xORy == 'y':
        csv_row = [
            columns['robot_y_pos'][row][robot], 
            columns['cyl_y_pos'][row][robot], 
            columns['robot_lwheel'][row][robot], 
            columns['robot_rwheel'][row][robot], 
            columns['cyl_y2robot'][row][robot], 
            columns['roboty2goal'][row][robot],
            # columns['robot_angle'],
            columns['force_y'][row][robot],    
            columns['force_y'][row+1][robot]     # force from next row
        ]
    return csv_row


#############################################
# Takes the dictionary with the episode data and converts it into a CSV formatted for MME
# 
#############################################

def format_MME_CSV(output_file, line_count, xORy, useProx):
    useX = False
    useY = False
    if xORy == 'x':
        useX = True
    elif xORy == 'y':
        useY = True
    elif xORy == 'both':
        useX = True
        useY = True
    
    local_line_counter = 0

    with open(output_file, 'w') as f:
        writer = csv.writer(f)
        for row_num in range (0,line_count-1): # -1 for needing to use the next row's force
            # print(line_count)
            # print(i)

            for robot in range(len(columns['robot_x_pos'][0])): # run for the number of robots present (should be 4)
                # print(j)
                output_row = get_single_row(row_num, robot, xORy, useProx)
                writer.writerow(output_row)
                
                local_line_counter += 1
    print("Wrote " + str(local_line_counter) + " lines to " + output_file)


#############################################
#   Run the CSV parser on list of files passed
#
#############################################

def parse_all_CSVs_in_list(folder_path, filename_no_num, episode_list, filter_type, range_min, range_max):
    filename_list = []
    for file in episode_list:
        full_file_name = folder_path + filename_no_num + str(file) + '.csv'
        parse_NN_CSV(full_file_name, filter_type, range_min, range_max)

    print('Opened ' + str(len(episode_list)) + ' CSVs')


#############################################
#   Run the CSV parser on every file in the folder passed
#
#############################################

def parse_all_CSVs_in_folder(folder_path, filter_type, range_min, range_max):
    input_data_path = folder_path
    file_names = []
    for file in os.listdir(input_data_path):
        file_names.append(file)
        this_file_path = folder_path + file
        parse_NN_CSV(this_file_path, filter_type, range_min, range_max)

    print('Opened ' + str(len(file_names)) + ' CSVs')


#############################################
#   Creates simple box plots of the ranges of the data
#
#############################################

def create_box_plots(file_path):
    robot_y_pos= []
    cyl_y_pos = []
    robot_lwheel = []
    robot_rwheel = []
    cyl_y2robot = []
    robotygoal = []
    force_y = []
    with open(os.path.expanduser(file_path)) as f:
        reader = csv.reader(f)
        for col in reader:
            robot_y_pos.append(float(col[0]))
            cyl_y_pos.append(float(col[1]))
            robot_lwheel.append(float(col[2]))
            robot_rwheel.append(float(col[3]))
            cyl_y2robot.append(float(col[4]))
            robotygoal.append(float(col[5]))
            force_y.append(float(col[6]))
    # print(robot_y_pos)
    fig = plt.figure(figsize =(10, 7))
    ax = fig.add_subplot(111)
    ax.boxplot([robot_y_pos, cyl_y_pos,robot_lwheel,robot_rwheel,cyl_y2robot,robotygoal, force_y])
    ax.set_xlabel('robot_y_pos      cyl_y_pos     robot_lwheel       robot_rwheel     cyl_y2robot        robotygoal     force_y')
    
    plt.show()



def main():
    RL_input_folder_path = os.path.expanduser('/home/cparks/NEST/RL-CollectiveTransport/pytorch/python_code/Data/2022-09-26_Gate1/gateForFilter/Data')
    file_name = '/Data_Episode_'
    file_num_list = [
        2
    ]
    filter_type = 'filter_x'
    range_min = -4
    range_max = 5
    parse_all_CSVs_in_list(RL_input_folder_path, file_name, file_num_list, filter_type, range_min, range_max)
    #parse_NN_CSV(os.path.expanduser('~/NEST/CollectiveTransport_to_MME_parser/EpisodeDataCSVs/DDPG_2obs_int_ep300_Episode_419.csv')) # appends all of the data from the csv passed
    # parse_all_CSVs_in_folder(os.path.expanduser('~/NEST/CollectiveTransport_to_MME_parser/EpisodeDataCSVs/DDPG3_ep10-20-30-40-50-60-70/'))
    format_MME_CSV(output_file="DDPG_gate_FilterTest_x.csv", line_count=total_line_count, xORy='x', useProx=False)
    format_MME_CSV(output_file="DDPG_gate_FilterTest_y.csv", line_count=total_line_count, xORy='y', useProx=True)



if __name__ == '__main__':
    # create_box_plots('~/NEST/CollectiveTransport_to_MME_parser/MMEInputCSVs/DDPG_Data_y.csv')
    main()


