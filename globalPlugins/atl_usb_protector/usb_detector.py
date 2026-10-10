import threading
import time
import win32api
import win32file
import ui
import wx
from . import action_engine
from . import config_manager

class USBDetector:
	paused = False
	pending_usbs = {}

	def __init__(self):
		self.monitoring = False
		self.thread = None
		self.known_drives = self.get_current_drives()

	def get_current_drives(self):
		drives = []
		try:
			drive_strings = win32api.GetLogicalDriveStrings()
			drive_list = drive_strings.split('\x00')[:-1]
			for drive in drive_list:
				if win32file.GetDriveType(drive) == win32file.DRIVE_REMOVABLE:
					drives.append(drive)
		except:
			pass
		return drives

	def get_drive_info(self, drive):
		try:
			info = win32api.GetVolumeInformation(drive)
			serial = str(info[1])
			vol_name = info[0] if info[0].strip() else "Removable Drive"
			space_info = win32file.GetDiskFreeSpaceEx(drive)
			size_gb = round(space_info[1] / (1024**3))
			display_name = f"{vol_name} ({size_gb} GB) - Serial: {serial}"
			return serial, display_name
		except:
			return None, None

	def start_monitoring(self):
		self.monitoring = True
		self.thread = threading.Thread(target=self.monitor_loop)
		self.thread.daemon = True
		self.thread.start()

	def stop_monitoring(self):
		self.monitoring = False
		for drive, info in list(USBDetector.pending_usbs.items()):
			info['timer'].cancel()
		USBDetector.pending_usbs.clear()

	def monitor_loop(self):
		while self.monitoring:
			time.sleep(1)
			current_drives = self.get_current_drives()
			new_drives = [d for d in current_drives if d not in self.known_drives]
			for drive in new_drives:
				if not USBDetector.paused:
					self.handle_new_drive(drive)
			self.known_drives = current_drives

	def handle_new_drive(self, drive):
		conf = config_manager.get_config()
		if not conf["enabled"]:
			return
		serial, display_name = self.get_drive_info(drive)
		if serial:
			is_trusted = False
			for trusted in conf["trusted_usbs"]:
				if serial in trusted:
					is_trusted = True
					break
			if is_trusted:
				wx.CallAfter(ui.message, "Trusted USB drive connected.")
			else:
				if conf["action"] == "alert":
					action_engine.execute_action(drive, "alert")
				else:
					wx.CallAfter(ui.message, "Security Alert! Unknown USB detected. Press Alt+A within 10 seconds to add it to the trusted list, otherwise it will be blocked.")
					if drive in USBDetector.pending_usbs:
						USBDetector.pending_usbs[drive]['timer'].cancel()
					
					timer = threading.Timer(10.0, self.execute_pending, args=[drive])
					USBDetector.pending_usbs[drive] = {
						'serial': serial,
						'display_name': display_name,
						'timer': timer
					}
					timer.start()

	def execute_pending(self, drive):
		if drive in USBDetector.pending_usbs:
			current_drives = self.get_current_drives()
			if drive in current_drives:
				conf = config_manager.get_config()
				action_engine.execute_action(drive, conf["action"])
			else:
				wx.CallAfter(ui.message, "USB drive was removed before any action was taken. System is safe.")
			
			if drive in USBDetector.pending_usbs:
				del USBDetector.pending_usbs[drive]