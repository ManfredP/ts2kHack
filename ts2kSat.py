#!/usr/bin/env python

import socket, sys, argparse

noError = True

def sendCommandToHamlib(sock_hamlib, command):
    b_cmd = bytearray()
    b_cmd.extend(map(ord, command + '\n'))
    sock_hamlib.send(b_cmd)
    waiting_for_answer = True
    return_value = ''
    while waiting_for_answer:
        return_value = sock_hamlib.recv(128).decode('utf-8')
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

def getUplinkFreq(sock_hamlib):
    retCode = sendCommandToHamlib(sock_hamlib, 'V VFOB')
    if retCode == "RPRT 0\n":
      freq = sendCommandToHamlib(sock_hamlib, 'f')
      return freq
    else:
      return retCode

def setFreq(sock_hamlib, freq, vfo):
  global noError
  retCode = sendCommandToHamlib(sock_hamlib, 'V ' + vfo)
  if retCode == "RPRT 0\n":
    retCode = sendCommandToHamlib(sock_hamlib, 'F ' + freq)
    if retCode != "RPRT 0\n":
      if noError:
        switchVfos(sock_hamlib)
        retCode = sendCommandToHamlib(sock_hamlib, 'F ' + freq)
        if retCode != "RPRT 0\n":
          noError = False
    else:
      noError = True
  return retCode

def switchToSatMode(sock_hamlib):
    sendCommandToHamlib(sock_hamlib, 'W SA1010000; 0')

def switchVfos(sock_hamlib):
  sendCommandToHamlib(sock_hamlib, 'W TS1; 0')

def main():
    ### Option Parsing ###
    parser = argparse.ArgumentParser()
    parser.add_argument("-c", dest="host_rigctld", type=str, required=True, help="specify which host to connect to")
    parser.add_argument("-p", dest="port_rigctld", type=int, required=True, help="specify which port to connect to")
    parser.add_argument("-l", dest="host_listen", type=str, required=True, help="specify which host to listen on")
    parser.add_argument("-P", dest="port_listen", type=int, required=True, help="specify which port to listen on")
    parser.add_argument("-d", dest="debug", default=False, action='store_true', help="print debug messages")

    args = parser.parse_args()

    # start tcp server
    sock_gpredict = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
    sock_gpredict.bind((args.host_listen, args.port_listen))
    sock_gpredict.listen(1)
    while True:
        conn, addr = sock_gpredict.accept()
        if args.debug:
          print('Connected by', addr)
        try:
          sock_hamlib = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
          sock_hamlib.connect((args.host_rigctld, args.port_rigctld))
        except socket.error as e:
          print('Problem connecting to rigctld: ', e)
        switchToSatMode(sock_hamlib)
        while 1:
            data = conn.recv(128)
            if args.debug:
              print('gpredict: ' + data.decode('utf-8').replace('\n', ''))
            if not data: break
            if data[0] in ['F', 'I']:
                # get downlink and uplink from gpredict
                cut = data.decode('utf-8').split(' ')
                if data[0] == 'F':  # F - gpredict ask for downlink
                    downlink = cut[len(cut)-1].replace('\n', '')
                    retCode = setFreq(sock_hamlib, downlink, 'VFOA')
                    conn.send(retCode.encode())
                if data[0] == 'I':  # I - gpredict ask for uplink
                    uplink = cut[len(cut)-1].replace('\n', '')
                    retCode = setFreq(sock_hamlib, uplink, 'VFOB')
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
        if args.debug:
          print('connect closed')
        conn.close()
        sock_hamlib.close()

main()
