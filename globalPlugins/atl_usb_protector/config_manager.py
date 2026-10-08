import config

def init_config():
	config.conf.spec["atl_usb_protector"] = {
		"enabled": "boolean(default=True)",
		"action": "string(default='eject')",
		"trusted_usbs": "string_list(default=list())"
	}
	if "atl_usb_protector" not in config.conf:
		config.conf["atl_usb_protector"] = {}
	
	conf = config.conf["atl_usb_protector"]
	if "enabled" not in conf:
		conf["enabled"] = True
	if "action" not in conf:
		conf["action"] = "eject"
	if "trusted_usbs" not in conf:
		conf["trusted_usbs"] = []
		
	return conf

def get_config():
	return config.conf["atl_usb_protector"]

def save_config():
	config.conf.save()