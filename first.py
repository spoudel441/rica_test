import logging
import time
import matplotlib.pyplot as plt
from matplotlib.animation import FuncAnimation
import collections
import numpy as np

try:
    from labjack.ljm import ljm
    # logging.info("Proper ljm imported")
    print("Proper ljm imported")
except Exception:
    # logging.critical('DAQ: Labjack library was not found.')
    print('DAQ: Labjack library was not found.')
    pass

class labjack_test():
    """To test if there is labjack connection and stream the data from accelerometer and temperature gauge"""
    
    def __init__(
        self,
        scan_rate: int = 1000,
        scans_per_read: int = 128,
        scan_list_names: list = ["AIN0", "AIN1"],
        *args,
        **kwargs,
    ):
        """Configure the LabJack Connection."""
        # Initialize base class
        # super().__init__(*args, **kwargs)
        
        # Labjack params
        # logging.info("DAQ: Creating Labjack connection...")
        print("DAQ: Creating Labjack connection...")
        self.scan_rate = scan_rate
        self.scans_per_read = scans_per_read
        self.scan_list_names = scan_list_names
        
        # Labjack Info
        (self.handle, self.info) = self._getHandle()
        if self.handle and self.info:
            print("got something")
        self.deviceType = self.info[0]
        
        # Configure Labjack
        self._configureDevice()
        logging.info("DAQ: LabJack Configured.")
        
        #Close the connection to the device
        self._close()
        
        
    def _getHandle(self):
        """Discover any connected LabJack T4 Devices.
        Attempt to open ethernet then default to usb connections.

        Returns:
            h: Device handle
            info: Device information
        """
        
        try:
            h = ljm.openS(
                "T4", "ETHERNET", "ANY"
            )  # T4 device, ETHERNET connection, ANY identifier
        except Exception:
            # logging.info("DAQ: Ethernet connection could not be established.")
            print("DAQ: Ethernet connection could not be established.")
            h = ljm.openS(
                "T4", "ANY", "ANY"
            )  # T4 device, ANY connection, ANY identifier
        info = ljm.getHandleInfo(h)
        # logging.info(
        #     "DAQ: Opened a LabJack with:\n"
        #     + f"\tDevice type: {info[0]}\n"
        #     + f"\tConnection type: {info[1]}\n"
        #     + f"\tSerial Number: {info[2]}\n"
        #     + f"\tIP Address: {ljm.numberToIP(info[3])}\n"
        #     + f"\tPort: {info[4]}\n"
        #     + f"\tMax bytes per MB: {info[5]}\n"
        # )
        print(
            "DAQ: Opened a LabJack with:\n"
            + f"\tDevice type: {info[0]}\n"
            + f"\tConnection type: {info[1]}\n"
            + f"\tSerial Number: {info[2]}\n"
            + f"\tIP Address: {ljm.numberToIP(info[3])}\n"
            + f"\tPort: {info[4]}\n"
            + f"\tMax bytes per MB: {info[5]}\n"
        )
        return (h, info)
    
    def _close(self):
        """Close LabJack T4 connection."""
        logging.info("DAQ: Cleaning up and exiting.")
        ljm.close(self.handle)
        
        
    def _configureDevice(self):
        """Configure LabJack T4.

        Configure labjack to:
            - Stream Data
            - Sample AIN0, AIN1
            - Set sampling rate
        """
        # Stream configuration
        self.numAddresses = len(self.scan_list_names)
        self.aScanList = ljm.namesToAddresses(self.numAddresses, self.scan_list_names)[
            0
        ]

        # LabJack T4
        a_names = [
            "AIN0_RANGE",
            "AIN1_RANGE",
            "STREAM_SETTLING_US",
            "STREAM_RESOLUTION_INDEX",
        ]
        a_values = [10.0, 10.0, 0.0, 0.0]
        num_frames = len(a_names)
        ljm.eWriteNAmes(self.handle, num_frames, a_names, a_values)
        
    def stream(self, poison_pill):
        """Begin streaming from LabJack T4.

        Start Streaming and recording data from DAQ
            -samples are cleared from DAQ in chunks of 128
            - samples are writeen to database every chunk
        """
        # Start Stream
        _ = ljm.eStreamStart(
            self.handle,
            self.scans_per_read,
            self.numAddresses,
            self.aScanList,
            self.scan_rate,
        )
        timestamp = int(int(time.time() * 1e3))
        # timestamp -= 8 * 3600

        # Continuous Read/Write
        # while not poison_pill.is_set():
        #     try:
        #         a_data = ljm.eStreamRead(self.handle)
        #         vib = a_data[0][::2]
        #         tmp = a_data[0][1::2]
        #         timestamp += 128
        #         # t0 = time.time()
        #         self._db_write(timestamp, vib, tmp)
        #     except Exception:
        #         logging.critical("DAQ: Connection lost to LabJack!")
        
        #Continuous viz
        vib_q = collections.deque(np.zeros(10))
        tmp_q = collections.deque(np.zeros(10))
        
        fig = plt.figure(figsize=(12,6), facecolor='#DEDEDE')
        ax = plt.subplot(121)
        ax1 = plt.subplot(122)
        ax.set_facecolor('#DEDEDE')
        ax1.set_facecolor('#DEDEDE')
        
        
    
        def plot_func(i):
            a_data = ljm.eStreamRead(self.handle)
            vib = a_data[0][::2]
            tmp = a_data[0][1::2]
            # timestamp += 128
            vib_q.popleft()
            vib_q.append(vib)
            tmp_q.popleft()
            tmp_q.append(tmp)
            
            # clear axis
            ax.cla()
            ax1.cla()
            
            # plot vib_q
            ax.plot(vib_q)
            ax.scatter(len(vib_q)-1, vib_q[-1])
            
            #plot tmp_q
            ax1.plot(tmp_q)
            ax1.scatter(len(tmp_q)-1, tmp_q[-1])
            
        # animate
        ani = FuncAnimation(fig, plot_func, interval=1000)
        
        plt.show()   
        self._close()
        
        
if __name__=="__main__":
    labjack_obj=labjack_test()
    
        
    
    