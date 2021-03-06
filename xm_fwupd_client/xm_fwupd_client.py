#!/usr/bin/env python


import socket
import multiprocessing
import xmodem
import time
#
#import verify_firmware

UPDATE_PORT_START = 11110
DEBUG_ON = True
MAX_PAYLOAD_SZ = 1500


# utils
def debug_print(msg):
    if DEBUG_ON:
        print(msg)


def Encrypt(data):
    """ Pass-through ATM """
    return data


def Decrypt(data):
    """ Pass-through ATM """
    return data


def RunUpdater(infile, url, port):
    # *************************** CLIENT ******************************
    class UpdaterClient:
        """ Firmware Updater client """
        firmware = None
        portnum = -1
        url = ""
        conn = None
        sock = socket.socket(socket.AF_INET, socket.SOCK_DGRAM, socket.IPPROTO_UDP)
        sock.setsockopt(socket.SOL_SOCKET, socket.SO_REUSEADDR, 1)
        default_size = sock.getsockopt(socket.SOL_SOCKET,socket.SO_RCVBUF)
        sfh = sock.makefile(mode='rb')
        #
        def __init__(self, url, portnum):
            self.url = url
            self.portnum = portnum
        #
        def Connect(self):
            """ Establish UDP comm """
            self.sock.setsockopt(socket.SOL_SOCKET,socket.SO_RCVBUF, MAX_PAYLOAD_SZ)
            print("Max payload was %s bytes - now set to %s!" % (self.default_size, MAX_PAYLOAD_SZ))
            #
            self.sock.setblocking(True)
            self.sock.settimeout(30)  # No point in timeout if non-blocking!
            debug_print("Started CLIENT using SERVER url=%s and port=%s" % (self.url, self.portnum))
            self.conn = (self.url, self.portnum)
        #
        def XMGet(self, size, timeout=10):
            """ TODO: emulate SRec-parser and Flash-procedure! """
            print("CLIENT: request for %s bytes to be received..." % size)
            self.sock.settimeout(timeout)
            data = None
            try:
                #tmp, addr = self.sock.recvfrom(size)
                #tmp = self.sock.recv(size)
                #tmp = self.sock.recv()
                tmp = self.sfh.read(size)
                #data = Decrypt(tmp)
                data = tmp
                debug_print("CLIENT: received %s bytes of data: %s" % (len(tmp), repr(data)))
            except socket.error as err:
                debug_print("Client on port=%s: Socket RECEIVE error! Msg=%s" % (self.portnum, err.strerror))
            return data
        #
        def XMput(self, data, timeout=10):
            """ Only used for handshake - not data ... """
            self.sock.settimeout(timeout)
            size = 0
            try:
                tmp = Encrypt(data)
                size = len(data)
                print("CLIENT: request for %s bytes to be sent..." % size)
                #self.sock.sendall(tmp)  # Or use 'sock.sendto()'
                self.sock.sendto(tmp, self.conn)
                print("CLIENT: bytes sent: %s" % repr(data))                
            except socket.error as err:
                debug_print("Client sending to SERVER-port=%s: socket SEND error!Msg=%s" % (self.portnum, err.strerror))
            return size
        #
        def XMRunUpdate(self, filename):
            self.Connect()
            stream = open(filename, 'wb')
            xm = xmodem.XMODEM(self.XMGet, self.XMput)
            size = xm.recv(stream, crc_mode=1, retry=16, timeout=60, delay=1, quiet=0)
            if size:
                debug_print("Received %s bytes of firmware via XModem" % size)
            else:
                debug_print("CLIENT ERROR: got no data from server!")
            stream.close()
            # Class instance will be disposed after use - might as well close socket here:
            self.sfh.close()
            self.sock.close()
            # Verify (but only if firmware BIN-fil has been received):
            # self.XMVerify(filename)
        #
        def XMVerify(self, filename):
            """ TODO: read and dump content of file ... """
            pass
    # ***********************************
    updater = UpdaterClient(url, port)
    updater.XMRunUpdate(infile)


# ******************* MAIN ***************************
# ====================================================
if __name__ == '__main__':
    url = "localhost"
    numclients = 1  # number of clients
    updater = None
    fwserver = None

    in_file = "IN_fw_1.dat"  # Actually .BIN-files

    RunUpdater(in_file, url, UPDATE_PORT_START)

"""
    # Add clients
    jobs = []
    for i in range(numclients):
        portnum = UPDATE_PORT_START + i
        in_file = "IN_fw_" + str(i) + ".dat"  # Actually .BIN-files
        # Start another client
        # updater = UpdaterClient(url, portnum)
        # kli = multiprocessing.Process(target=updater.XMRunUpdate, args=(in_file))
        kli = multiprocessing.Process(target=RunUpdater, args=(in_file, url, portnum))
        jobs.append(kli)
        # CLIENTs are forked as sub-processes of main too, will run separately from each other ...
        kli.start()
        #
    kli.join(timeout=60.0)
    # ------------------------------------------
    print("All clients terminated!")
"""




