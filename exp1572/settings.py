import json
import os
from shutil import copyfile

name = 'exp1572'
here = os.path.abspath(os.path.dirname(__file__))
settingsDstName = os.path.join(os.path.expanduser('~'), '.' + name)
settingsFileName = 'settings.json'

try:
	sfile = open(os.path.join(settingsDstName, settingsFileName))
except:
	try:
		os.mkdir(settingsDstName)
	except FileExistsError:
		pass
	copyfile(os.path.join(os.path.abspath(os.path.dirname(__file__)), 
		settingsFileName), os.path.join(settingsDstName, settingsFileName))
	sfile = open(os.path.join(settingsDstName, settingsFileName))

VALUES = json.load(sfile)

try:
	DESCRIPTIONS = {
		"play.friendlyDisableMoveLoss": _("settings.fdmd.description"),
		"play.waterfallInCurrentLocation": _("settings.wfcl.description"),
		"display.expeditionTypeDescription": _("settings.det.description"),
		"display.locale": _("settings.locale.description"),
	}
except NameError:
	pass
