#!/usr/bin/env python

import socket
import sys

HOST_SERVER = '127.0.0.1'  # Standard loopback interface address (localhost)
PORT_SERVER = 4535  # Port to listen on (non-privileged ports are > 1023)
HOST_CLIENT = '127.0.0.1'
PORT_CLIENT = 4532  # Port to listen on (non-privileged ports are > 1023)

def sendCommandToHamlib(sock_hamlib, command):
    b_cmd = bytearray()
    b_cmd.extend(map(ord, command + '\n'))
    sock_hamlib.send(b_cmd)
    waiting_for_answer = True
    return_value = ''
    while waiting_for_answer:
        return_value = sock_hamlib.recv(100).decode('utf-8')
        if len(return_value) > 0:
            waiting_for_answer = False

    if 'RPRT -' in return_value:
        print('hamlib: ' + return_value.replace('\n', '') + ' for command ' + command)
    return return_value

def getDownlinkFreq(sock_hamlib):
    retCode = sendCommandToHamlib(sock_hamlib, 'V VFOA')
    if retCode == "RPRT 0\n":
      freq = sendCommandToHamlib(sock_hamlib, 'f')
      return freq
    else:
      return retCode

def setDownlinkFreq(sock_hamlib, freq):
    retCode = sendCommandToHamlib(sock_hamlib, 'V VFOA')
    if retCode == "RPRT 0\n":
      retCodeF = sendCommandToHamlib(sock_hamlib, 'F ' + freq)
      return retCodeF
    else:
      return retCode

def getUplinkFreq(sock_hamlib):
    retCode = sendCommandToHamlib(sock_hamlib, 'V VFOB')
    if retCode == "RPRT 0\n":
      freq = sendCommandToHamlib(sock_hamlib, 'f')
      return freq
    else:
      return retCode

def setUplinkFreq(sock_hamlib, freq):
    retCode = sendCommandToHamlib(sock_hamlib, 'V VFOB')
    if retCode == "RPRT 0\n":
      retCodeF = sendCommandToHamlib(sock_hamlib, 'F ' + freq)
      return retCodeF
    else:
      return retCode

def main():
    ###############################################
    # start sockets for gpredict und hamlib
    ###############################################

    # start tcp client
    try:
        sock_hamlib = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
        sock_hamlib.connect((HOST_CLIENT, PORT_CLIENT))
    except socket.error as e:
        print('Problem: ', e)

    # start tcp server
    sock_gpredict = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
    sock_gpredict.bind((HOST_SERVER, PORT_SERVER))
    sock_gpredict.listen(1)
    while True:
        conn, addr = sock_gpredict.accept()
        print('Connected by', addr)
        while 1:
            data = conn.recv(1000)
            print('gpredict: ' + data.decode('utf-8').replace('\n', ''))
            if not data: break
            if data[0] in ['F', 'I']:
                # get downlink and uplink from gpredict
                cut = data.decode('utf-8').split(' ')
                if data[0] == 'F':  # F - gpredict ask for downlink
                    downlink = cut[len(cut)-1].replace('\n', '')
                    retCode = setDownlinkFreq(sock_hamlib, downlink)
                    conn.send(retCode.encode())
                if data[0] == 'I':  # I - gpredict ask for uplink
                    uplink = cut[len(cut)-1].replace('\n', '')
                    retCode = setUplinkFreq(sock_hamlib, uplink)
                    conn.send(retCode.encode())
            elif data[0] in ['f', 'i']: # f, i
                if data[0] == 'f':  # f - gpredict ask for downlink
                    downlinkFreq = getDownlinkFreq(sock_hamlib)
                    conn.send(downlinkFreq.encode())
                if data[0] == 'i':  # i - gpredict ask for uplink
                    uplinkFreq = getUplinkFreq(sock_hamlib)
                    conn.send(uplinkFreq.encode())
            else:
                conn.send(b'RPRT 0\n')  # Return Data OK to gpredict
        print('connect closed')
        conn.close()

main()
