#!/usr/bin/env python

import socket
import multiprocessing
import xmodem
import time
import queue


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


def GenerateFirmwareFile(fname):
    NUM_LINES = 1
    TEST_LINE = "Dette er en test - ABCDEFGHabcdefgh. No:"
    fh = open(fname, mode='w')
    for i in range(NUM_LINES):
        line = TEST_LINE + str(i) + "\n"
        fh.write(line)
    fh.close()


def RunFWserver(outfile, srv_url, port):
    # *************************** SERVER ******************************
    class UpdaterServer:
        """ Firmware Update server """
        firmware = None
        portnum = -1
        url = ""
        conn = None
        addr = None
        sock = socket.socket(socket.AF_INET, socket.SOCK_DGRAM, socket.IPPROTO_UDP)
        sock.setsockopt(socket.SOL_SOCKET, socket.SO_REUSEADDR, 1)  
        default_size = sock.getsockopt(socket.SOL_SOCKET,socket.SO_RCVBUF)
        #
        def __init__(self, url, portnum):
            self.url = url
            self.portnum = portnum
        #
        def Connect(self):
            """ Establish UDP comm """
            self.sock.setsockopt(socket.SOL_SOCKET,socket.SO_RCVBUF, MAX_PAYLOAD_SZ)
            print("Max payload was %s bytes - now set to %s!" % (self.default_size, MAX_PAYLOAD_SZ))
            self.sock.setblocking(True)
            self.sock.settimeout(10)  # No point in timeout if non-blocking!
            debug_print("Starting SERVER on url=%s and port=%s" % (self.url, self.portnum))
            self.conn = ("localhost", self.portnum)
            try:
                self.sock.bind(self.conn)
                debug_print("Server on port=%s: running!" % self.portnum)
            except socket.error as err:
                debug_print("Server on port=%s:: Socket connect ERROR!" % (self.portnum, err.strerror))
        #
        def XMGet(self, size, timeout=10):
            """ Only used for handshake - not data ... """
            self.sock.settimeout(timeout)
            data = None
            print("SRV: request for %s bytes to be received..." % size)
            try:
                #tmp, addr = self.sock.recvfrom(MAX_PAYLOAD_SZ)
                tmp, addr = self.sock.recvfrom(size)
                if self.addr == None:
                    print("SRV: client connected to from address=%s!" % repr(addr))
                    self.addr = addr
                #data = Decrypt(tmp)
                data = tmp
                debug_print("SRV: received %s bytes of data: %s" % (len(tmp), repr(data)))
            except socket.error as err:
                debug_print("SRV on port=%s: Socket RECEIVE error! Msg=%s" % (self.portnum, err.strerror))
            return data[:size]
        #
        def XMput(self, data, timeout=10):
            """ TODO: emulate SRec-parser and read one Srec-frame at a time """
            self.sock.settimeout(timeout)
            size = 0
            try:
                #tmp = Encrypt(data)
                tmp = data
                print("SRV: request for %s bytes to be sent..." % len(data))
                #self.sock.sendall(tmp)  # Or use 'sock.sendto()'
                if self.addr:
                    self.sock.sendto(tmp, self.addr)
                    debug_print("SRV: sent data: " + repr(data))
                    size = len(data)
                else:
                    debug_print("SERVER ERROR: no client address set yet! Dummy-send ...")
            except socket.error as err:
                debug_print("SRV on port=%s: socket SEND error! Msg=%s" % (self.portnum, err.strerror))
            return size
        #
        def XMServeUpdate(self, filename):
            self.Connect()
            stream = open(filename, 'rb')
            xm = xmodem.XMODEM(self.XMGet, self.XMput)
            # TODO: possibly infer a callback? (for debug-purpose f.ex.)
            status = xm.send(stream)
            stream.close()
            if status:
                print("Sent firmware via XModem")
            else:
                print("Failed to send firmware via XModem!")
            # Class instance will be disposed after use - might as well close socket here:
            self.sock.close()
            # **************************************
    # ------------------------------------------------
    fwserver = UpdaterServer(srv_url, port)
    fwserver.XMServeUpdate(outfile)


# ******************* MAIN ***************************
# ====================================================
if __name__ == '__main__':
    url = "localhost"
    num_servers = 1  # = number of clients
    fwserver = None

    out_file = "OUT_fw_1.dat"  # Actually .BIN-files
    GenerateFirmwareFile(out_file)
    RunFWserver(out_file, url, UPDATE_PORT_START)

"""
    # Add servers and clients
    jobs = []
    for i in range(num_servers):
        portnum = UPDATE_PORT_START + i
        # Start server first
        # ==================
        out_file = "OUT_fw_" + str(i) + ".dat"  # Actually .BIN-files
        GenerateFirmwareFile(out_file)
        #
        # fwserver = UpdaterServer(url, portnum)
        # srv = multiprocessing.Process(target=fwserver.XMServeUpdate, args=(out_file))
        srv_proc = multiprocessing.Process(target=RunFWserver, args=(out_file, url, portnum))
        jobs.append(srv_proc)
        # SERVERs are forked as sub-processes of main, will run separately from each other ...
        srv_proc.start()
        #
    srv_proc.join(timeout=60.0)
    # t.join(timeout=60.0)
    # ------------------------------------------
    print("All servers and clients terminated!")
"""
