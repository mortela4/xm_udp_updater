#!/usr/bin/env python

import socket
import multiprocessing
import xmodem
import time

UPDATE_PORT_START = 11111
DEBUG_ON = True


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
    TEST_LINE = "Dette er en test - ABCDEFGHabcdefgh. No:"
    fh = open(fname, mode='w')
    for i in range(100):
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
        sock = socket.socket(socket.AF_INET, socket.SOCK_DGRAM, socket.IPPROTO_UDP)
        sock.setsockopt(socket.SOL_SOCKET, socket.SO_REUSEADDR, 1)
        #
        def __init__(self, url, portnum):
            self.url = url
            self.portnum = portnum
        #
        def Connect(self):
            """ Establish UDP comm """
            self.sock.setblocking(True)
            self.sock.settimeout(10)  # No point in timeout if non-blocking!
            debug_print("Started SERVER on url=%s and port=%s" % (self.url, self.portnum))
            conn = ("localhost", self.portnum)
            try:
                self.sock.bind(conn)
                self.sock.connect(conn)
                debug_print("Server on port=%s: connected!" % self.portnum)
            except socket.error:
                debug_print("Server on port=%s:: Socket connect ERROR!" % self.portnum)
        #
        def XMGet(self, size, timeout=10):
            """ Only used for handshake - not data ... """
            self.sock.settimeout(timeout)
            data = None
            try:
                #tmp = self.sock.recv(size)  # Or use 'sock.recvfrom()'
                tmp = self.sock.recvfrom(size)
                data = Decrypt(tmp)
                debug_print("SRV: received data: " + repr(data))
            except socket.error as err:
                debug_print("SRV on port=%s: Socket RECEIVE error! Msg=%s" % (self.portnum, err.strerror))
            return data
        #
        def XMput(self, data, timeout=10):
            """ TODO: emulate SRec-parser and read one Srec-frame at a time """
            self.sock.settimeout(timeout)
            size = 0
            try:
                tmp = Encrypt(data)
                self.sock.sendall(tmp)  # Or use 'sock.sendto()'
                size = len(data)
                debug_print("SRV: sent data: " + repr(data))
            except socket.error as err:
                debug_print("SRV on port=%s: socket SEND error! Msg=%s" % (self.portnum, err.strerror))
            return size
        #
        def XMServeUpdate(self, filename):
            self.Connect()
            stream = open(__file__, 'rb')
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
