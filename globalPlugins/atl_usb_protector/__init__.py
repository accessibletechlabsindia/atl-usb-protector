import globalPluginHandler
import scriptHandler
import ui
import gui
import gui.settingsDialogs
import tones
from . import config_manager
from . import usb_detector
from . import settings_gui

class GlobalPlugin(globalPluginHandler.GlobalPlugin):
	
	def __init__(self, *args, **kwargs):
		super(GlobalPlugin, self).__init__(*args, **kwargs)
		self.config = config_manager.init_config()
		self.detector = usb_detector.USBDetector()
		self.detector.start_monitoring()
		gui.settingsDialogs.NVDASettingsDialog.categoryClasses.append(settings_gui.USBProtectorSettingsPanel)

	def terminate(self):
		self.detector.stop_monitoring()
		gui.settingsDialogs.NVDASettingsDialog.categoryClasses.remove(settings_gui.USBProtectorSettingsPanel)
		super(GlobalPlugin, self).terminate()

	@scriptHandler.script(description="Adds the pending USB drive to the trusted list.", gesture="kb:alt+a")
	def script_addPendingUSB(self, gesture):
		tones.beep(700, 50)
		if usb_detector.USBDetector.pending_drive and usb_detector.USBDetector.timer:
			usb_detector.USBDetector.timer.cancel()
			conf = config_manager.get_config()
			display_name = usb_detector.USBDetector.pending_display_name
			if display_name not in conf["trusted_usbs"]:
				conf["trusted_usbs"].append(display_name)
				config_manager.save_config()
			usb_detector.USBDetector.pending_drive = None
			usb_detector.USBDetector.pending_serial = None
			usb_detector.USBDetector.pending_display_name = None
			ui.message("USB drive successfully added to the trusted list.")
		else:
			ui.message("No pending USB drive found to add.")