#!/usr/bin/env python

# Copyright (c) Twisted Matrix Laboratories.
# See LICENSE for details.

import socket
import multiprocessing
import xmodem
import time

UPDATE_PORT_START = 8000
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


def RunFWserver(outfile, url, port):
    # *************************** SERVER ******************************
    class UpdaterServer:
        """ Firmware Update server """
        firmware = None
        portnum = -1
        url = ""
        sock = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
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
                # self.sock.connect(conn)
                self.sock.bind(conn)
                debug_print("Server on port=%s: connected!" % self.portnum)
            except socket.error:
                debug_print("Server on port=%s:: Socket connect ERROR!" % self.portnum)

        #
        def XMGet(self, size, timeout=10):
            """ Only used for handshake - not data ... """
            self.sock.settimeout(timeout)
            data = None
            try:
                tmp = self.sock.recv(size)  # Or use 'sock.recvfrom()'
                data = Decrypt(tmp)
            except socket.error:
                debug_print("Client on port=%s: Socket RECEIVE error!" % self.portnum)
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
            except socket.error:
                debug_print("Client on port=%s: socket SEND error!" % self.portnum)
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

    fwserver = UpdaterServer(url, port)
    fwserver.XMServeUpdate(outfile)


def RunUpdater(infile, url, port):
    # *************************** CLIENT ******************************
    class UpdaterClient:
        """ Firmware Updater client """
        firmware = None
        portnum = -1
        url = ""
        sock = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
        sock.setsockopt(socket.SOL_SOCKET, socket.SO_REUSEADDR, 1)

        #
        def __init__(self, url, portnum):
            self.url = url
            self.portnum = portnum

        #
        def Connect(self):
            """ Establish UDP comm """
            self.sock.setblocking(True)
            self.sock.settimeout(30)  # No point in timeout if non-blocking!
            debug_print("Started CLIENT using url=%s and port=%s" % (self.url, self.portnum))
            conn = ("localhost", self.portnum)
            try:
                self.sock.connect(conn)
                debug_print("Client on port=%s: connected!" % self.portnum)
            except socket.error:
                debug_print("Client on port=%s:: Socket connect ERROR!" % self.portnum)

        #
        def XMGet(self, size, timeout=10):
            """ TODO: emulate SRec-parser and Flash-procedure! """
            self.sock.settimeout(timeout)
            data = None
            try:
                tmp = self.sock.recv(size)  # Or - use 'socket.recvfrom()'
                data = Decrypt(tmp)
            except socket.error:
                debug_print("Client on port=%s: Socket RECEIVE error!" % self.portnum)
            return data

        #
        def XMput(self, data, timeout=10):
            """ Only used for handshake - not data ... """
            self.sock.settimeout(timeout)
            size = 0
            try:
                tmp = Encrypt(data)
                self.sock.sendall(tmp)  # Or use 'sock.sendto()'
                size = len(data)
            except socket.error:
                debug_print("Client on port=%s: socket SEND error!" % self.portnum)
            return size

        #
        def XMRunUpdate(self, filename):
            self.Connect()
            stream = open(__file__, 'wb')
            xm = xmodem.XMODEM(self.XMGet, self.XMput)
            size = xm.recv(stream, crc_mode=1, retry=16, timeout=60, delay=1, quiet=0)
            if size:
                debug_print("Received %s bytes of firmware via XModem" % size)
            else:
                debug_print("CLIENT ERROR: got no data from server!")
            stream.close()
            # Class instance will be disposed after use - might as well close socket here:
            self.sock.close()
            # Verify:
            self.XMVerify(self, filename)

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

    # Ex: RunFWserver("test.out", "localhost", 8001)

    # Add servers and clients
    jobs = []
    for i in range(numclients):
        portnum = UPDATE_PORT_START + i
        # Start server first
        # ==================
        out_file = "OUT_fw_" + str(i) + ".dat"  # Actually .BIN-files
        GenerateFirmwareFile(out_file)
        in_file = "IN_fw_" + str(i) + ".dat"  # Actually .BIN-files
        #
        # fwserver = UpdaterServer(url, portnum)
        # srv = multiprocessing.Process(target=fwserver.XMServeUpdate, args=(out_file))
        srv = multiprocessing.Process(target=RunFWserver, args=(out_file, url, portnum))
        jobs.append(srv)
        # SERVERs are forked as sub-processes of main, will run separately from each other ...
        srv.start()
        # sleep 3sec
        time.sleep(3)
        # Then start client
        # updater = UpdaterClient(url, portnum)
        # kli = multiprocessing.Process(target=updater.XMRunUpdate, args=(in_file))
        kli = multiprocessing.Process(target=RunUpdater, args=(in_file, url, portnum))
        jobs.append(kli)
        # CLIENTs are forked as sub-processes of main too, will run separately from each other ...
        kli.start()
        # t = multiprocessing.Process(target=RunUpdate, args=(out_file, in_file, url, port))
        # jobs.append(t)
        # CLIENTs are forked as sub-processes of main too, will run separately from each other ...
        # t.start()

    srv.join(timeout=60.0)
    kli.join(timeout=60.0)
    # t.join(timeout=60.0)
    # ------------------------------------------
    print("All servers and clients terminated!")





