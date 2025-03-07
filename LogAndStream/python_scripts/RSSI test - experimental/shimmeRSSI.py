# performs a simple device inquiry, followed by a remote name request of each
# discovered device

import binascii
import os
import struct
import sys
import time
import matplotlib
matplotlib.use('TkAgg')

import bluetooth._bluetooth as bluez
import matplotlib.animation as animation
import matplotlib.pyplot as plt



def printpacket(pkt):
    for c in pkt: # Itera sobre cada byte en pkt
        sys.stdout.write("%02x " % struct.unpack("B", c)[0]) # Convierte a hexadecimal
    print() # Salto de línea


def read_inquiry_mode(sock):
    """returns the current mode, or -1 on failure"""
    try:
        # save current filter
        old_filter = sock.getsockopt(bluez.SOL_HCI, bluez.HCI_FILTER, 14)
        print("Socket filter retrieved successfully.")
    except Exception as e:
        print("Error retrieveng socket filter:", e)
        return -1

    try:
        # Setup socket filter to receive only events related to the
        # read_inquiry_mode command
        flt = bluez.hci_filter_new()
        opcode = bluez.cmd_opcode_pack(bluez.OGF_HOST_CTL, bluez.OCF_READ_INQUIRY_MODE)
        bluez.hci_filter_set_ptype(flt, bluez.HCI_EVENT_PKT)
        bluez.hci_filter_set_event(flt, bluez.EVT_CMD_COMPLETE)
        bluez.hci_filter_set_opcode(flt, opcode)
        print("Socket filter set up successfully.")
    except Exception as e:
        print("Error setting up socket filter:", e)
        return -1
        
    try:
        sock.setsockopt(bluez.SOL_HCI, bluez.HCI_FILTER, flt)
        print("Socket filter applied successfully.")
    except Exception as e:
        print("Error aplying filter:", e)
        return -1
        
    try:
        # first read the current inquiry mode.
        bluez.hci_send_cmd(sock, bluez.OGF_HOST_CTL, bluez.OCF_READ_INQUIRY_MODE)
        print("Command sent successfully.")
    except Exception as e:
        print("Error sending command:", e)
        return -1
        
    try:
        pkt = sock.recv(255)
        status, mode = struct.unpack("xxxxxxBB", pkt)
        print("Packet received successfully.")
    except Exception as e:
        print("Error receiving packet:", e)
        return -1
    
    print("Status: ", status)
    if status != 0: 
        mode = -1

    try:
        # restore old filter
        print("Old filter length:", len(old_filter) if old_filter else "None")
        print("Old filter raw data:", old_filter)
        if old_filter and old_filter != b'\x00' * 14:
            sock.setsockopt(bluez.SOL_HCI, bluez.HCI_FILTER, old_filter)
            print("Socket filter restored successfully.")
        else:
            print("Warning: Old filter is empty or invalid, skipping restore.")
    except Exception as e:
        print("Error restoring old filter")
        return -1
        
    return mode


def write_inquiry_mode(sock, mode):
    """returns 0 on success, -1 on failure"""
    try:
        # save current filter
        old_filter = sock.getsockopt(bluez.SOL_HCI, bluez.HCI_FILTER, 14)
        print("Old filter retrieved successfully.")
    except Exception as e:
        print("Error reading old filter:", e)
        return -1

    try:
        # Setup socket filter to receive only events related to the
        # write_inquiry_command mode
        flt = bluez.hci_filter_new()
        opcode = bluez.cmd_opcode_pack(bluez.OGF_HOST_CTL, bluez.OCF_WRITE_INQUIRY_MODE)
        bluez.hci_filter_set_ptype(flt, bluez.HCI_EVENT_PKT)
        bluez.hci_filter_set_event(flt, bluez.EVT_CMD_COMPLETE)
        bluez.hci_filter_set_opcode(flt, opcode)
        sock.setsockopt(bluez.SOL_HCI, bluez.HCI_FILTER, flt)
        print("Filter set up successfully.")
    except Exception as e:
        print("Error setting up filter:", e)
        return -1

    try:
        # send the command!
        bluez.hci_send_cmd(sock, bluez.OGF_HOST_CTL, bluez.OCF_WRITE_INQUIRY_MODE, struct.pack("B", mode))
        print("Command sent successfully.")
    except Exception as e:
        print("Error sending command:", e)
        return -1

    try:
        pkt = sock.recv(255)
        print("Packet received successfully: ", binascii.hexlify(pkt))
    except Exception as e:
        print("Error receiving packet:", e)
        return -1

    try:
        status = struct.unpack("xxxxxxB", pkt)[0]
        print("Status: ", status)
    except Exception as e:
        print("Error unpacking packet:", e)
        return -1

    try:
        # restore old filter
        if old_filter and old_filter != b'\x00' * 14:
            sock.setsockopt(bluez.SOL_HCI, bluez.HCI_FILTER, old_filter)
            print("Socket filter restored successfully.")
        else:
            print("Warning: Old filter is empty or invalid, skipping restore.")
    except Exception as e:
        print("Error restoring old filter:", e)
        return -1
        
    if status != 0:
        print("Error setting inquiry mode. Status returned: %d" % status) 
        return -1
    
    print("Inquiry mode changed successfully.")
    return 0


def device_inquiry_with_with_rssi(sock):
    try:
        # save current filter
        old_filter = sock.getsockopt(bluez.SOL_HCI, bluez.HCI_FILTER, 14)
        print("Old filter retrieved successfully.")
    except Exception as e:
        print("Error reading old filter:", e)
        sys.exit(1)

    try:
        # perform a device inquiry on bluetooth device #0
        # The inquiry should last 8 * 1.28 = 10.24 seconds
        # before the inquiry is performed, bluez should flush its cache of
        # previously discovered devices
        flt = bluez.hci_filter_new()
        
        # bluez.hci_filter_all_events(flt)
        
        bluez.hci_filter_set_event(flt, bluez.EVT_CONN_COMPLETE)
        bluez.hci_filter_set_event(flt, bluez.EVT_CONN_REQUEST)
        bluez.hci_filter_set_event(flt, bluez.EVT_DISCONN_COMPLETE)
        bluez.hci_filter_set_event(flt, bluez.EVT_INQUIRY_RESULT_WITH_RSSI)
        bluez.hci_filter_set_event(flt, bluez.EVT_INQUIRY_RESULT)
        bluez.hci_filter_set_event(flt, bluez.EVT_INQUIRY_COMPLETE)

  
        sock.setsockopt(bluez.SOL_HCI, bluez.HCI_FILTER, flt)
        print("Filter set up successfully.")
    except Exception as e:
        print("Error setting up filter:", e)
        sys.exit(1)
    
    duration = 4
    max_responses = 255
    cmd_pkt = struct.pack("BBBBB", 0x33, 0x8b, 0x9e, duration, max_responses)
    
    try:
        bluez.hci_send_cmd(sock, bluez.OGF_LINK_CTL, bluez.OCF_INQUIRY, cmd_pkt)
        print("Command sent successfully.")
    except Exception as e:
        print("Error sending command:", e)
        sys.exit(1)

    results = []

    done = False
    addr = "NA"
    while not done:
        pkt = sock.recv(255)
        ptype, event, plen = struct.unpack("BBB", pkt[:3])
        if event == bluez.EVT_INQUIRY_RESULT_WITH_RSSI:
            pkt = pkt[3:]
            nrsp = struct.unpack("B", pkt[0])[0]
            for i in range(nrsp):
                addr = bluez.ba2str(pkt[1 + 6 * i:1 + 6 * i + 6])
                rssi = struct.unpack("b", pkt[1 + 13 * nrsp + i])[0]
                results.append((addr, rssi))
        # done = True
        elif event == bluez.EVT_INQUIRY_COMPLETE:
            done = True
        elif event == bluez.EVT_CMD_STATUS:
            status, ncmd, opcode = struct.unpack("BBH", pkt[3:7])
            if status != 0:
                # print("uh oh...")
                # printpacket(pkt[3:7])
                done = True
        elif event == bluez.EVT_INQUIRY_RESULT:
            pkt = pkt[3:]
            nrsp = struct.unpack("B", pkt[0])[0]
            for i in range(nrsp):
                addr = bluez.ba2str(pkt[1 + 6 * i:1 + 6 * i + 6])
                results.append((addr, -1))
        # print("[%s] (no RRSI)" % addr)
    # else:
    # print("unrecognized packet type 0x%02x" % ptype)
    # print("event ", event)

    # restore old filter
    sock.setsockopt(bluez.SOL_HCI, bluez.HCI_FILTER, old_filter)

    return results


dev_id = 0 # Identificador del dispositivo Bluetooth (probablemente el adaptador Bluetooth local)
mac = [] # Lista vacía para almacenar identificadores cortos de direcciones MAC
macIDs = ['D8:47:8F:04:BC:A6']
numDev = len(macIDs)

print("Number of devices: ", numDev)

timeStamp = [[] for _ in range(numDev)] # Marcas de tiempo para cada dispositivo detectado
rssi = [[] for _ in range(numDev)] # Intensidad de la señal recibida de cada dispositivo
data = [[] for _ in range(numDev)] # Datos adicionales que podrían capturarse del Bluetooth

for MAC in macIDs:
    mac.append(MAC.replace(":", "")[-4:])

try:
    sock = bluez.hci_open_dev(dev_id)
except Exception as e:
    print(e)
    sys.exit(1)

try:
    mode = read_inquiry_mode(sock)
    print("Inquiry mode is %d" % mode)
except Exception as e:
    print("Error reading inquiry mode.")
    print("Are you sure this a bluetooth 1.2 device?")
    print(e)
    sys.exit(1)
print("Current inquiry mode is %d" % mode)

if mode != 1:
    print("Writing inquiry mode...")
    try:
        result = write_inquiry_mode(sock, 1)
    except Exception as e:
        print("Error writing inquiry mode.  Are you sure you're root?")
        print(e)
        sys.exit(1)
    if result != 0:
        print("Error while setting inquiry mode")
    print("Result: %d" % result)


def handle_close(evt):
    print("Testing done!")

    if not os.path.exists("./data"):
        try:
            os.makedirs("./data")
            os.chmod("./data", 0o777)
        except OSError:
            if not os.path.isdir("./data"):
                raise

    for i in range(0, numDev):
        print("".join(['data/RSSI_', mac[i], '_', time.strftime("%d-%m-%Y_%H.%M"), '.txt']))
        f = open("".join(['data/RSSI_', mac[i], '_', time.strftime("%d-%m-%Y_%H.%M"), '.txt']), 'w')
        for d in data[i]:
            f.write(", ".join(map(str, d)) + "\n")

        f.close()

    print("File saved")


fig = plt.figure()
fig.canvas.mpl_connect('close_event', handle_close)

ax = []

for i in range(0, numDev):
    ax.append(fig.add_subplot(numDev, 1, i + 1))
    ax[-1].set_title(mac[i])
    ax[-1].set_ylabel('RSSI in dBm')


def animate(i):
    results = device_inquiry_with_with_rssi(sock)

    for i in range(0, len(results)):
        for j in range(0, numDev):
            if (macIDs[j] == results[i][0]):
                rssi[j].append(results[i][1])
                timeStamp[j].append(time.strftime("%H:%M:%S"))
                data[j].append([timeStamp[j][-1], rssi[j][-1]])

    for k in range(0, numDev):
        if (len(rssi[k]) > 1):
            print(data[k][-1])
            ax[k].clear()
            ax[k].set_title(mac[k])
            ax[k].set_ylabel('RSSI in dBm')
            ax[k].plot(range(len(rssi[k])), rssi[k])


try:
    ani = animation.FuncAnimation(fig, animate, interval=500, save_count=10)
    anim_global = ani  # Evita que Python lo elimine
    plt.show()
except KeyboardInterrupt:
    print("Interrupted!")
    fig.close()

except:
    pass
