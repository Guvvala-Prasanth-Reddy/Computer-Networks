from ast import arg
import os
import argparse
from statistics import mean, median
import subprocess
from matplotlib import pyplot as plt
import plotly.graph_objects as go
import glob
import jc
import pprint
import numpy as np
import shutil
import json
pp = pprint.PrettyPrinter(indent=4)



def save_as_json(args , final_json_op):
    """given a file path and a python dictionary save_as_json standardizes the dict to json and saves it as the filename specified in the path"""
    with open(args.OUTPUT+".json", "w") as outfile:
        json.dump(final_json_op, outfile , indent=4)
    


def plot_graph( args , final_distributions ,final_json_op ):
    """ plots a graph of hops  against the latencies """
    c = ['hsl('+str(h)+',50%'+',50%)' for h in np.linspace(0, 360, len(final_distributions[0]))]
    
    #print(len(final_distributions[0]) , len(final_distributions[1]))
    fig = go.Figure(data = [go.Box(y = final_distributions[0][i] if len(final_distributions[0][i]) != 0 else  [0] , name = final_distributions[1][i] , marker_color = c[i]  )  for i in range(len(final_distributions[0]))])
    for i in range(len(final_distributions[0])):
        fig.add_trace( go.Scatter(y= [final_json_op[i].get("avg")] , x=[final_distributions[1][i]], mode = "markers" , marker_color = "Black" ,showlegend=False) )
    fig.write_image(args.GRAPH+".pdf")
    return 0



"""Todo:
Add test_dir functionality 
"""
def create_a_host_list(lines,host_dict):
    """analyses the traceroute runs and returns the anticipated data structure of list of tuples of host and ip addresses mapped in tuple"""
    hop = 1
    for line in lines:
        contents = line.split(" ")
        temp_list = []
        #pp.#pprint(contents)
        for item in contents:
            if( ((item.count(".") > 1 and item != "ms") ) or "gateway" in item):
                temp_list.append(item)
        #pp.pprint(temp_list)
        i = 0
        while(i < len(temp_list)-1):
            if( host_dict.get(hop) == None):
                host_dict[hop] = [(temp_list[i],temp_list[i+1])]
                    
            else:
                host_dict[hop].append((temp_list[i],temp_list[i+1]))
            i+=2
        hop+=1
    for i in range(1,len(lines)+1):
        if( host_dict.get(i) == None):
            host_dict[i] = []
        else:
            host_dict[i] = list(set(host_dict[i]))
    return host_dict



def call_traceroute_and_save_results( args ):

    #Todo: add traceroute calling function
    destination_address = args.TARGET
    arguments_for_traceroute = "mkdir -p test_files;traceroute "
    arguments_for_traceroute += destination_address +" " 

    """
    Todo: for a regex commandline for traceroute to subsitute 
            RUN_DELAY(sleep command)  ,
            MAX_HOPS (-m argument directly )- Done  ,
            NUM_RUNS ( use a for loop in the command line) - Done

         Eg :   N=5; for i in `seq 1 $N` ; do traceroute google.com ;  sleep 25 ; done

         test_files - in progress - done with file creation

         understanding traceroute  - Done
         parsing the files - Done
         creating the graph - Done
         covering the edge cases - Done
         supporting path and name argument  

    """
    if( args.MAX_HOPS is not None):
        arguments_for_traceroute += " -m "+args.MAX_HOPS+" "        
    arguments_for_traceroute = f"for i in `seq 1 {args.NUM_RUNS if args.NUM_RUNS is not None else 1}` ; do "+ arguments_for_traceroute + " > test_files/tr_run-$i.txt ; " 
    if( args.RUN_DELAY is not None):
        arguments_for_traceroute = arguments_for_traceroute +" sleep " + args.RUN_DELAY +  " ; "
    arguments_for_traceroute = arguments_for_traceroute +" done"

    # print(arguments_for_traceroute)
    try:
        shutil.rmtree(os.getcwd()+"/test_files")
    except FileNotFoundError:
        b = 1
    traceroute = subprocess.run(arguments_for_traceroute , check = True , stdout=subprocess.PIPE , universal_newlines=True , shell = True)

    output_of_traceroute = traceroute.stdout
    return "test_files"
    # print(output_of_traceroute)


def perform_analysis( args ):
    """perform analysis analyses the files of a traceroute run and generates a json and graph by the end of its run"""
    final_json = {}
    hosts = {}
    if(  os.path.exists(args.TEST_DIR) == False):
        print("Folder doesnt exist")
        return 0


    file_names = glob.glob(f"{args.TEST_DIR}/*")
    
    file_names.sort()
    for file in file_names:
        with open(file) as f:
            lines = f.read()
            #print(lines)
        with open(file) as f:
            lines_list = f.readlines()
            lines_list = lines_list[1:]
            #print(lines_list)
        hosts = create_a_host_list(lines_list,hosts)
        data = jc.parse('traceroute' , lines)
        # print(data)
        for hop in data['hops']:
            #print(hop.get("hop"))
            if(final_json.get(hop.get("hop")) == None):
                final_json[hop.get("hop")] = {}
                final_json[hop.get("hop")]["hop"] = hop.get("hop")
                final_json[hop.get("hop")]["probes"] = []
                final_json[hop.get("hop")]["times"] = []
                for i in hop.get("probes"):
                    final_json[hop.get("hop")]["probes"].append(i.get('ip'))
                    final_json[hop.get("hop")]["times"].append(i.get('rtt'))
            else:
                for i in hop.get("probes"):
                    final_json[hop.get("hop")]["probes"].append(i.get('ip'))
                    final_json[hop.get("hop")]["times"].append(i.get('rtt'))
            # #pp.pprint(final_json)
            # #pp.pprint(hosts)

    final_json_op = []
    final_distributions = [[],[]]
    
    for key in final_json.keys():
        # #pp.pprint(final_json.get(key).get('times'))
        final_json.get(key)['times']= [0 if i is None else i for i in final_json.get(key).get('times') ]
        final_distributions[0].append( final_json.get(key).get('times'))
        final_distributions[1].append(f"hop {key}")
        temp_dict = {}
        temp_dict['hop'] = key
        temp_dict['hosts'] = tuple(set(final_json.get(key).get('probes')))
        # final_distributions.append({})
        if( len(final_json.get(key).get('times')) != 0):
            temp_dict['avg']= mean(final_json.get(key).get('times'))
            temp_dict['max'] = max(final_json.get(key).get('times'))
            temp_dict['med'] = median(final_json.get(key).get('times'))
            temp_dict['min'] = min(final_json.get(key).get('times'))
        else:
            temp_dict['avg'] = 0
            temp_dict['max'] = 0
            temp_dict['med'] = 0
            temp_dict['min'] = 0
        final_json_op.append(
            temp_dict
        )

    # #pp.pprint(final_json)
    
    # #pp.pprint(final_distributions)
    #pp.pprint(hosts)
    for i in hosts.keys():
        final_json_op[i-1]['hosts'] = hosts.get(i)
    save_as_json(args,final_json_op)
    plot_graph(args , final_distributions , final_json_op)
    pp.pprint(final_json_op)
    #pp.pprint(final_distributions)
    #pp.pprint(os.getcwd())

        
    return 0


def compare_file_count( args ):
    """Compare file count function for future use"""
    files_list = glob.glob(os.getcwd()+"/test_files/*.txt")
    print(files_list)
    if( len(files_list) == args.NUM_RUNS):
        return False
    return True
    



def main():
    """Main function captures the arguments and based on their values the conditional flow exectution runs"""
    help_message ="""
    """
    parser = argparse.ArgumentParser(description = help_message)

    #Required arguments addition 
    parser.add_argument("-o","--OUTPUT" , help = "Path and name of output JSON file containing the stats/n Eg:/home/student/nameofthefile"  , required = True)
    parser.add_argument("-g" , "--GRAPH" , help = "Path and name of output PDF file containing stats graph/n Eg: /home/student/nameofthefile", required = True)

    #Todo: add optional arguments
    parser.add_argument("-n" , "--NUM_RUNS", help = "Number of times traceroute will run" , required = False)
    parser.add_argument("-d" , "--RUN_DELAY" , help = "Number of seconds to wait between two consecutive runs" , required = False)
    parser.add_argument("-m" , "--MAX_HOPS" , help = "max hops of traceroute" , required = False )
    parser.add_argument("-t" , "--TARGET" , help = " A target domain name or IP address (required if --test is absent)" , required = False )
    parser.add_argument("-test","--TEST_DIR" , help = "Directory containing num_runs text files, each of which contains the output of a traceroute run", required = False)

 

    """
    Todo:Adding logic to call traceroute only iff --test is true or else use the files of the test_files folder to
            create metrics json and graph
    """
    args = parser.parse_args()

    #print(args)

    if( args.TEST_DIR is not None ):
        #check whether the test directory has the number of files that are equal to number of runs
        perform_analysis( args )

    else:
        args.__setattr__("TEST_DIR",call_traceroute_and_save_results( args ))
        perform_analysis( args )

    return 0


if __name__ == "__main__":
    main()
