import argparse
from socket import *
from scapy.layers.inet import *
import threading
import logger
import datetime
icmp_resp_data = []
tcp_resp_data = []
port = 5000
REACHED_DESTINATION_FLAG = 0

dict_of_sequences= {}
ip_data = []
def capture_ip_packets():
    try:
        p = socket.socket(socket.AF_INET , socket.SOCK_RAW  , socket.IPPROTO_IP)
        data,address = p.recvfrom(1024)
        ip_data.append((data , address))
        print(IP(data).display())
        p.settimeout(2)
        while(True):
            data,address = p.recvfrom(1024)
            ip_data.append((data , address))
            print(IP(data).display())
    except :
        err =1
        # print(2)



#function to recieve the ICMP ttl exceeded responses
def recieve_ICMP_response(ttl ):
    try:
        r = socket.socket(socket.AF_INET , socket.SOCK_RAW  , socket.IPPROTO_ICMP)
        r.setsockopt(socket.IPPROTO_IP , socket.IP_TTL , ttl) 
        r.settimeout(0.0275)
        while(REACHED_DESTINATION_FLAG != 1):
            data , address = r.recvfrom(1024)
            ip = IP(data)
            icmp = ip[ICMP]
            # print(icmp.fields)
            # print(icmp.show())
            if( icmp.type == 11 and icmp.code == 0):
                tcp = ip["TCP in ICMP"]
                ip_in_icmp = ip["IP in ICMP"]
                dict_of_sequences.get(tcp.seq)["end_time"] = datetime.datetime.now() 
                dict_of_sequences.get(tcp.seq)["dst"] = address[0]
                # print(icmp.show())
                # print(tcp.show())
                # icmp_resp_data.append([ttl,data,address])
        r.close()
        return data
    except:
        err = 1

#function to caputre the synack packets from the destination ip
def recieve_TCP_response(ttl, port , dest_ip):
    try:
        k = socket.socket(socket.AF_INET , socket.SOCK_RAW , socket.IPPROTO_TCP )
        k.setsockopt(socket.IPPROTO_IP ,socket.IP_TTL , ttl)
        k.bind(('',port))
        data , address = k.recvfrom(1024)
        while(address[0] != dest_ip):
            data , address = k.recvfrom(1024)
            # print(address)
            logger.info(address)
        global REACHED_DESTINATION_FLAG
        REACHED_DESTINATION_FLAG = 1
        ip = IP(data)
        tcp = ip[TCP]
        # print(ip.show())
        if( tcp.flags == "SA"):
            dict_of_sequences.get(tcp.ack)["end_time"] = datetime.datetime.now()
            dict_of_sequences.get(tcp.ack)["dst"] = address[0]
            dict_of_sequences.get(tcp.ack)["ack"] = True
            tcp_resp_data.append([ttl,data,address])
        k.close()
    except:
        # print(1)
        err =1

#function that intelligently sends tcp packets with seq number set
def send_syn_packet(dest_ip , dest_port , ttl , port , seq):
    s = socket.socket(socket.AF_INET, socket.SOCK_RAW, socket.IPPROTO_RAW)
    syn_packet = IP( dst=dest_ip, ttl=ttl) / TCP(dport=dest_port, sport=port, flags='S' , seq = seq)
    s.setsockopt(socket.IPPROTO_IP , socket.IP_TTL , ttl)
    s.sendto(bytes(syn_packet) , (dest_ip , dest_port) )
    dict_of_sequences[seq]["start_time"] = datetime.datetime.now()
    p = threading.Thread(target = recieve_ICMP_response , args = (ttl,))
    k = threading.Thread(target = recieve_TCP_response , args = (ttl, port , dest_ip))

    p.start() , k.start()
    capture_ip_packets()
#function that makes and fires all the tcp packets at once    
def call_traceroute(target , target_ip , max_hops , destination_port):
    p = []
    port = 5000
    seq = 0
    for i in range(1, max_hops+1):
        for j in range(3):
            p.append(threading.Thread(target = send_syn_packet , args = (target_ip , destination_port , i , port , seq)))
            dict_of_sequences[seq] = {}
            seq+=1
            port += 50
    for i in range(len(p)):
        p[i].start()
    

    return 1
#main function to take input and parse the traceroute
if __name__ == '__main__':
    parser = argparse.ArgumentParser( )
    parser.add_argument("-m" , "--MAX_HOPS" ,default = 30, type = int ,help = 'Max hops to probe (default = 30)' , required=False)
    parser.add_argument("-p" , "--DST_PORT" ,default = 80, type = int , help = "TCP destination port (default = 80)")
    parser.add_argument("-t" , "--TARGET"   , help = "Target domain or IP" , required = True)
    arguments = parser.parse_args()

    target_ip = socket.gethostbyname(arguments.TARGET)
    max_hops = arguments.MAX_HOPS
    destination_port = arguments.DST_PORT
    target = arguments.TARGET
    # print(target , max_hops , destination_port , target_ip)
    p = call_traceroute(target , target_ip , max_hops , destination_port)
    # print(len(icmp_resp_data) , len(tcp_resp_data))
    # for i in icmp_resp_data:
    #     # print(IP(i)[ICMP].display())
    #     try:
    #         print(f"hop {i[0]} IP destination {IP(i[1]).src } IP src {IP(i[1]).dst} FLAGS  ICMP code{IP(i[1])[ICMP].code} ICMP type {IP(i[1])[ICMP].type} ")
    #     except:
    #         print("Nothing much happened")

    # for i in tcp_resp_data:
    #     # print(IP(i)[ICMP].display())
    #     try:
    #         print("hop " ,i[0],f"IP destination {IP(i[1]).src } IP src {IP(i[1]).dst}", IP(i[1])[TCP].flags,"Tcp flags")
    #     except:
    #         print("Nothing much happened")
            
    # # print(icmp_resp_data)
    # print("TCP DATA")
    # # print(tcp_resp_data)
    # print(len(tcp_resp_data)+len(icmp_resp_data))
    print('traceroute to {} ({}), {} hops max, TCP SYN to port {}'.format(target, target_ip,max_hops, destination_port))
    k = dict_of_sequences.keys()
    end = " "
    flag = 0
    # for item in dict_of_sequences:
        # print(dict_of_sequences[item])
    for i in range(len(k)//3):
        print('{:<2}'.format(i+1) , end = " ")
        hop_dict = {}
        for j in range(3):
            try:
                host = socket.gethostbyaddr(dict_of_sequences[i*3+j].get("dst"))[0]
            except:
                host = dict_of_sequences[i*3+j].get("dst")
            if( "dst" in dict_of_sequences[i*3+j]):
                key = host+" "+ f"({dict_of_sequences[i*3+j].get('dst')})"
                if( hop_dict.get(key) == None):
                    hop_dict[key] = []
                
                # print( host  ,  f"({dict_of_sequences[i*3+j].get('dst')})" , end = " ")
                if( "start_time" in dict_of_sequences[i*3+j] and "end_time" in dict_of_sequences[i*3+j]):
                    hop_dict[key].append(
                    str(((max(dict_of_sequences[i*3+j].get("end_time") ,
                    dict_of_sequences[i*3+j].get("start_time")) - min(dict_of_sequences[i*3+j].get("end_time") , 
                    dict_of_sequences[i*3+j].get("start_time"))).microseconds)/1000)+" ms")
                else:
                    if( hop_dict.get("*") == None):
                        hop_dict["*"] = []
                    hop_dict["*"].append("*")
                if( "ack"  in dict_of_sequences[i*3+j] ):
                    flag = 1
            else:
                if( hop_dict.get("*") == None):
                    hop_dict["*"] = []
                hop_dict["*"].append("*")
        # print(hop_dict)
        for key in  hop_dict.keys():
            if( key != "*"):
                print( key ,end = "  ")
            for item in hop_dict[key]:
                print(item , end = " ")
        if(flag ):
            break   
        print()

            
        
    


