import subprocess
import ui
import win32file
import win32api
import ctypes
import os
import winreg

def execute_action(drive, action):
	if "C" in drive.upper():
		return
	if win32file.GetDriveType(drive) != win32file.DRIVE_REMOVABLE:
		return
	drive_letter = drive.replace("\\", "")
	if action == "eject":
		try:
			ps_command = f"(New-Object -comObject Shell.Application).Namespace(17).ParseName('{drive_letter}').InvokeVerb('Eject')"
			subprocess.run(["powershell", "-WindowStyle", "Hidden", "-Command", ps_command], creationflags=subprocess.CREATE_NO_WINDOW)
			ui.message("Warning! An unauthorized USB drive was detected and has been safely ejected to protect your system.")
		except:
			ui.message("Error: Failed to eject the unauthorized USB drive.")
	elif action == "readonly":
		try:
			script_dp = f"select volume {drive_letter[0]}\nattributes disk set readonly\nattributes volume set readonly\nexit\n"
			dp_path = os.path.join(os.environ["TEMP"], "atl_lock.txt")
			with open(dp_path, "w") as f:
				f.write(script_dp)
			bat_script = f'@echo off\nreg add "HKLM\\SYSTEM\\CurrentControlSet\\Control\\StorageDevicePolicies" /v WriteProtect /t REG_DWORD /d 1 /f\ndiskpart /s "{dp_path}"\n'
			bat_path = os.path.join(os.environ["TEMP"], "atl_lock.bat")
			with open(bat_path, "w") as f:
				f.write(bat_script)
			ctypes.windll.shell32.ShellExecuteW(None, "runas", bat_path, None, None, 0)
			ui.message("Warning! An unauthorized USB drive was detected. Please grant Administrator permission in the UAC prompt to lock it in Read-Only mode.")
		except:
			ui.message("Error: Failed to lock the USB drive in Read-Only mode.")
	else:
		ui.message("Security Alert! An unknown USB drive has been connected to your system.")

def is_usb_locked():
	try:
		key = winreg.OpenKey(winreg.HKEY_LOCAL_MACHINE, r"SYSTEM\CurrentControlSet\Control\StorageDevicePolicies", 0, winreg.KEY_READ)
		value, _ = winreg.QueryValueEx(key, "WriteProtect")
		winreg.CloseKey(key)
		return value == 1
	except:
		return False

def unlock_usb_drives():
	try:
		drives = []
		drive_strings = win32api.GetLogicalDriveStrings()
		for d in drive_strings.split('\x00')[:-1]:
			if win32file.GetDriveType(d) == win32file.DRIVE_REMOVABLE:
				drives.append(d[0])
		script_dp = ""
		for d in drives:
			script_dp += f"select volume {d}\nattributes disk clear readonly\nattributes volume clear readonly\n"
		script_dp += "exit\n"
		dp_path = os.path.join(os.environ["TEMP"], "atl_unlock.txt")
		with open(dp_path, "w") as f:
			f.write(script_dp)
		bat_script = f'@echo off\nreg add "HKLM\\SYSTEM\\CurrentControlSet\\Control\\StorageDevicePolicies" /v WriteProtect /t REG_DWORD /d 0 /f\ndiskpart /s "{dp_path}"\n'
		bat_path = os.path.join(os.environ["TEMP"], "atl_unlock.bat")
		with open(bat_path, "w") as f:
			f.write(bat_script)
		ctypes.windll.shell32.ShellExecuteW(None, "runas", bat_path, None, None, 0)
		return True
	except:
		return False