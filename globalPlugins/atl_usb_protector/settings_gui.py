import wx
import gui
from gui.settingsDialogs import SettingsPanel
from . import config_manager
from . import usb_detector
from . import action_engine
import win32api
import win32file
import webbrowser
import ui

class USBProtectorSettingsPanel(SettingsPanel):
	title = "ATL USB Protector"

	def makeSettings(self, settingsSizer):
		usb_detector.USBDetector.paused = True
		self.sHelper = gui.guiHelper.BoxSizerHelper(self, sizer=settingsSizer)
		conf = config_manager.get_config()
		
		self.enabledCheckbox = self.sHelper.addItem(wx.CheckBox(self, label="Enable USB Protection"))
		self.enabledCheckbox.SetValue(conf["enabled"])
		self.enabledCheckbox.Bind(wx.EVT_CHECKBOX, self.onEnableChange)
		
		self.dynamicSizer = wx.BoxSizer(wx.VERTICAL)
		self.dynamicHelper = gui.guiHelper.BoxSizerHelper(self, sizer=self.dynamicSizer)
		
		actions = ["eject", "readonly", "alert"]
		self.actionChoice = self.dynamicHelper.addLabeledControl("Action for unauthorized USB:", wx.Choice, choices=actions)
		try:
			self.actionChoice.SetSelection(actions.index(conf["action"]))
		except ValueError:
			self.actionChoice.SetSelection(0)
			
		self.trustedList = self.dynamicHelper.addLabeledControl("Trusted USB Drives:", wx.ListBox, choices=conf["trusted_usbs"])
		
		self.addBtn = self.dynamicHelper.addItem(wx.Button(self, label="Add Current USB to Trusted"))
		self.addBtn.Bind(wx.EVT_BUTTON, self.onAddUSB)
		
		self.removeBtn = self.dynamicHelper.addItem(wx.Button(self, label="Remove Selected USB"))
		self.removeBtn.Bind(wx.EVT_BUTTON, self.onRemoveUSB)
		
		if action_engine.is_usb_locked():
			self.unlockBtn = self.dynamicHelper.addItem(wx.Button(self, label="Unlock All USB Drives (Remove Read-Only)"))
			self.unlockBtn.Bind(wx.EVT_BUTTON, self.onUnlockUSB)
		
		self.sHelper.addItem(self.dynamicSizer)
		
		btn_donate = self.sHelper.addItem(wx.Button(self, label="Donate to Accessible Tech Labs India"))
		btn_visit = self.sHelper.addItem(wx.Button(self, label="Visit Official Website"))
		btn_contact = self.sHelper.addItem(wx.Button(self, label="Contact Accessible Tech Labs India"))
		
		btn_donate.Bind(wx.EVT_BUTTON, lambda e: webbrowser.open("https://accessibletechlabsindia.github.io/support.html"))
		btn_visit.Bind(wx.EVT_BUTTON, lambda e: webbrowser.open("https://accessibletechlabsindia.github.io/"))
		btn_contact.Bind(wx.EVT_BUTTON, lambda e: webbrowser.open("https://accessibletechlabsindia.github.io/contact.html"))
		
		self.updateDynamicVisibility()

	def onEnableChange(self, event):
		self.updateDynamicVisibility()

	def updateDynamicVisibility(self):
		is_enabled = self.enabledCheckbox.GetValue()
		self.sHelper.sizer.Show(self.dynamicSizer, is_enabled)
		self.Layout()

	def onAddUSB(self, event):
		drives = win32api.GetLogicalDriveStrings().split('\x00')[:-1]
		added = False
		for drive in drives:
			if win32file.GetDriveType(drive) == win32file.DRIVE_REMOVABLE:
				try:
					info = win32api.GetVolumeInformation(drive)
					serial = str(info[1])
					vol_name = info[0] if info[0].strip() else "Removable Drive"
					space_info = win32file.GetDiskFreeSpaceEx(drive)
					size_gb = round(space_info[1] / (1024**3))
					display_name = f"{vol_name} ({size_gb} GB) - Serial: {serial}"
					items = self.trustedList.GetStrings()
					if display_name not in items:
						self.trustedList.Append(display_name)
						added = True
				except:
					pass
		if added:
			wx.CallAfter(ui.message, "USB drive successfully added to the trusted list.")
		else:
			wx.CallAfter(ui.message, "No new removable USB drive found. Please insert a USB drive first.")

	def onRemoveUSB(self, event):
		sel = self.trustedList.GetSelection()
		if sel != wx.NOT_FOUND:
			self.trustedList.Delete(sel)
			wx.CallAfter(ui.message, "Selected USB drive has been removed from the trusted list.")
		else:
			wx.CallAfter(ui.message, "No USB drive selected. Please select a drive from the list to remove.")

	def onUnlockUSB(self, event):
		msg = "Warning! Unlocking USB drives will allow data to be written to them. This might expose your system to viruses if the USB is infected. Are you sure you want to proceed?"
		dlg = wx.MessageDialog(self, msg, "Confirm Unlock", wx.YES_NO | wx.ICON_WARNING)
		result = dlg.ShowModal()
		dlg.Destroy()
		if result == wx.ID_YES:
			if action_engine.unlock_usb_drives():
				wx.CallAfter(ui.message, "Please grant Administrator permission in the UAC prompt to unlock USB drives.")
				self.unlockBtn.Hide()
				self.Layout()
			else:
				wx.CallAfter(ui.message, "Error: Failed to initiate unlock process.")

	def onSave(self):
		conf = config_manager.get_config()
		conf["enabled"] = self.enabledCheckbox.GetValue()
		actions = ["eject", "readonly", "alert"]
		conf["action"] = actions[self.actionChoice.GetSelection()]
		conf["trusted_usbs"] = self.trustedList.GetStrings()
		config_manager.save_config()
		usb_detector.USBDetector.paused = False

	def onDiscard(self):
		usb_detector.USBDetector.paused = False

def show_settings_dialog():
	try:
		if hasattr(gui.mainFrame, '_popupSettingsDialog'):
			gui.mainFrame._popupSettingsDialog(USBProtectorSettingsPanel)
		else:
			d = gui.settingsDialogs.NVDASettingsDialog(gui.mainFrame, panels=[USBProtectorSettingsPanel])
			d.ShowModal()
			d.Destroy()
	except Exception as e:
		wx.CallAfter(ui.message, f"Settings Error: {str(e)}")