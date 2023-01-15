import argparse
from dataclasses import dataclass
import socket
import base64
import urllib.request
from threading import Lock
import _thread
from socket import timeout
import requests
from scapy.all import *
PORT = 53
Lock = 0
mutex = threading.Lock()
def extract_the_domain_name(data):
    parts = []
    part = ''
    mode = 'n'
    length_of_part = 0
    accumulated_length = 0

    for byte in data:
        if mode == 'r':
            part += chr(byte)
            accumulated_length += 1
            if ( accumulated_length == length_of_part):
                parts.append(part)
                part = ''
                accumulated_length = 0
                mode = 'n'
            if byte == 0:
                break
        else:
            length_of_part = byte
            mode = 'r'
        # print(mode , part , parts)
    print(parts)
    return ".".join(parts)
def check_for_domain_name(domain_name , file_name):
    file = open(file_name , 'r')
    hosts = file.readlines()
    if domain_name in hosts:
        return True
    else:
        return False
def parse_flags(part):
    part1 = bytes(part[:1])
    part2 = bytes(part[1:2])

    rflags = ''

    QR = '1'

    OPCODE = ''
    for bit in range(1,5):
        OPCODE += str(ord(part1)&(1<<bit))

    AA = '1'

    TC = '0'

    RD = '0'

    # Byte 2

    RA = '0'

    Z = '000'

    RCODE = '0000'
    print(int(QR+OPCODE+AA+TC+RD, 2).to_bytes(1, byteorder='big')+int(RA+Z+RCODE, 2).to_bytes(1, byteorder='big') , "2 bytes")

    return int(QR+OPCODE+AA+TC+RD, 2).to_bytes(1, byteorder='big')+int(RA+Z+RCODE, 2).to_bytes(1, byteorder='big')

#dns forwarder is server for dig  as well as client for dns_resolvers 
def dns_udp_implementation(dns_server_ip , source_ip_address , sock  , stream , denied_host_names , logger):
    parsed_dns_request = IP(dst = dns_server_ip)/UDP(dport=PORT)/DNS(stream)
    txid = parsed_dns_request[DNS].id
    host_name = parsed_dns_request[DNSQR].qname
    host_name= host_name.decode()[:-1].encode()
    query_type = parsed_dns_request[DNSQR].qtype
    query_type_dictionary = {1:'A' , 15:'MX' , 2 : 'NS' , 5 : 'CNAME'}
    query_type = query_type_dictionary.get(query_type)
    for i in range(len(denied_host_names)):
        denied_host_names[i] = denied_host_names[i].strip()
    print(host_name.decode())
    if( host_name.decode() in denied_host_names):
        sock.sendto(bytes(DNS(id =txid,qd =  DNSQR(qname = host_name , qtype = query_type ),rcode = 3)) ,source_ip_address)
        if( logger != None):
            mutex.acquire(1)
            logger.write(host_name.decode()+' '+query_type+' '+'DENY \n')
            mutex.release()
    else:
        forwarder_udp_socket = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
        forwarder_udp_socket.connect((dns_server_ip, PORT))
        forwarder_udp_socket.send(stream)
        stream = forwarder_udp_socket.recv(2048)
        sock.sendto(stream,source_ip_address)
        if( logger != None):
            mutex.acquire(1)
            logger.write(host_name.decode()+' '+query_type+' '+'ALLOW \n')
            mutex.release()
    return





    
        
def doh_dns_implementation(doh_server , source_ip_address , sock  , stream , denied_host_names , logger):
    parsed_dns_request = IP(dst = doh_server)/UDP(dport=PORT)/DNS(stream)
    txid = parsed_dns_request[DNS].id
    host_name = parsed_dns_request[DNSQR].qname
    host_name= host_name.decode()[:-1].encode()
    query_type = parsed_dns_request[DNSQR].qtype
    print(query_type)
    query_type_dictionary = {28 : "AAAA" , 1:'A' , 15:'MX' , 2 : 'NS' , 5 : 'CNAME'}
    query_type = query_type_dictionary.get(query_type)
    for i in range(len(denied_host_names)):
        denied_host_names[i] = denied_host_names[i].strip()
    if( host_name.decode() in denied_host_names):
        sock.sendto(bytes(DNS(id =txid,qd =  DNSQR(qname = host_name , qtype = query_type ),rcode = 3)) ,source_ip_address)
        if( logger != None):
            mutex.acquire(1)
            logger.write(host_name.decode()+' '+query_type+' '+'DENY \n')
            mutex.release()
    else:
       # print()
        #message = dns.message.make_query(host_name.decode(),query_type_dictionary.get(parsed_dns_request[DNSQR].qtype))
       # print(message)
        #dns_req = base64.urlsafe_b64encode(message.to_wire()).decode("UTF8").rstrip("=")
       # print(dns.message.from_wire(stream))
        # k = base64.urlsafe_b64encode(stream.decode("UTF8").rstrip("="))
       # print(f"https://{doh_server}/dns-query?dns={str(base64.urlsafe_b64encode(stream))[2:-1]}")
        refined = str(base64.urlsafe_b64encode(stream))[2:-1].strip("=")
        response = requests.get(f"https://{doh_server}/dns-query?dns={refined}")
        # print(r)
        # print(r.content)
        r  = response.content
        # r = k+r[2:]
       # r = dns.message.from_wire(r)
        print(r)
        # response = urllib.request.urlopen(https_request , timeout = 100)
        # response = response.read()
        sock.sendto(response.content, source_ip_address)
        if( logger != None):
            mutex.acquire(1)
            logger.write(host_name.decode()+' '+query_type+' '+'ALLOW \n')
            mutex.release()

    return
def create_and_run_the_socket_for_dns(IP):
    IP = "172.17.149.15"
    sock = socket.socket(socket.AF_INET , socket.SOCK_DGRAM )
    sock.bind((IP , PORT))
    return sock
   
        
def forward_dns_response():
    return 0

def parse_arguments():
    help_message =""" """
    parser = argparse.ArgumentParser(description = help_message)
    


    #optional arguments
    # parser.add_argument("-d" , "--NUM_RUNS", help = "Number of times traceroute will run" , required = False)
    parser.add_argument("-d" , "--DST_IP", help = "Destination DNS server IP" , required = False)
    parser.add_argument("-f" , "--DENY_LIST_FILE", help = "File containing domains to block" , required = False)
    parser.add_argument("-l" , "--LOG_FILE", help = "Append-only log file" , required = False)
    parser.add_argument("--doh" , help = "Use default upstream DoH server" , required = False)
    parser.add_argument("--doh_server" , help = "Use this upstream DoH server" , required = False)
    args = parser.parse_args()

    return args

def main():
    arguments = parse_arguments()
    deny_list = []
    logger = None
    if arguments.DENY_LIST_FILE:
        deny_list = open(arguments.DENY_LIST_FILE , 'r').readlines()
        print(deny_list)
        print("theres a deny list file")
    if arguments.LOG_FILE is not None:
        logger = open(arguments.LOG_FILE , 'a')
    print(arguments.doh)
    if arguments.doh_server is not None:
        ip_address_of_doh_server = arguments.doh_server
        sock = create_and_run_the_socket_for_dns("")
        while(True):
            stream,source_ip_address = sock.recvfrom(2048)
            _thread.start_new_thread(doh_dns_implementation , (ip_address_of_doh_server,source_ip_address,sock,stream,deny_list , logger))
    elif( arguments.doh is not None):
        default_doh_server = '8.8.8.8'
        sock = create_and_run_the_socket_for_dns("")
        while(True):
            stream,source_ip_address = sock.recvfrom(2048)
            _thread.start_new_thread(doh_dns_implementation, (default_doh_server , source_ip_address,sock,stream,deny_list , logger))
    elif ( arguments.DST_IP is not None):
        sock = create_and_run_the_socket_for_dns("")
        ip_address_of_dns_server = arguments.DST_IP
        while(True):
            stream,source_ip_address = sock.recvfrom(2048)
            _thread.start_new_thread(dns_udp_implementation , (ip_address_of_dns_server , source_ip_address , sock , stream , deny_list , logger))
    else:
        ip_address_of_dns_server = '8.8.8.8'
        sock = create_and_run_the_socket_for_dns("")
        while(True):
            stream,source_ip_address = sock.recvfrom(2048)
            _thread.start_new_thread(dns_udp_implementation , (ip_address_of_dns_server , source_ip_address , sock , stream , deny_list , logger))
            print("served address " , source_ip_address)  



    




    # print(arguments)
    # sock = create_and_run_the_socket_for_dns("127.0.0.1")
    # while True:
    #     data,addr = sock.recvfrom(2048)
    #     print(data)
    #     domain_name = extract_the_domain_name(data[12:])
    #     nx_flag = check_for_domain_name(domain_name , arguments.DENY_LIST_FILE)
    #     if( nx_flag):
    #         return_nx_domain_response( addr , domain_name , data)






if __name__ == "__main__":
    main()
