import threading
import time
import win32api
import win32file
import ui
from . import action_engine
from . import config_manager

class USBDetector:
	paused = False
	pending_drive = None
	pending_serial = None
	pending_display_name = None
	timer = None

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
		if USBDetector.timer:
			USBDetector.timer.cancel()

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
				ui.message("Trusted USB drive connected.")
			else:
				if conf["action"] == "alert":
					action_engine.execute_action(drive, "alert")
				else:
					USBDetector.pending_drive = drive
					USBDetector.pending_serial = serial
					USBDetector.pending_display_name = display_name
					ui.message("Security Alert! Unknown USB detected. Press Alt+A within 10 seconds to add it to the trusted list, otherwise it will be blocked.")
					if USBDetector.timer:
						USBDetector.timer.cancel()
					USBDetector.timer = threading.Timer(10.0, self.execute_pending)
					USBDetector.timer.start()

	def execute_pending(self):
		if USBDetector.pending_drive:
			conf = config_manager.get_config()
			action_engine.execute_action(USBDetector.pending_drive, conf["action"])
			USBDetector.pending_drive = None
			USBDetector.pending_serial = None
			USBDetector.pending_display_name = None