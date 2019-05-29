import json
import os
from shutil import copyfile

name = 'exp1572'
settingsFileName = 'settings.json'
dfltDirName = os.path.abspath(os.path.dirname(__file__))
dfltFileName = os.path.join(dfltDirName, settingsFileName)
userDirName = os.path.join(os.path.expanduser('~'), '.' + name)
userFileName = os.path.join(dfltDirName, settingsFileName)
VALUES = {}
DESCRIPTIONS = {}
merged = False

def save():
	with open(userFileName, 'w') as sfile:
		json.dump(VALUES, sfile)

def checkMerge():
	''' Check user settings for compliance with current (renewed)
		system settings and set values for missing keys to default values
	'''
	with open(dfltFileName) as dFile:
		dDict = json.load(dFile)
	for k in (dDict.keys() - VALUES.keys()):
		VALUES[k] = dDict[k]
		merged = True
	if merged:
		save()

def load():
	# Load user settings
	try:
		sfile = open(userFileName)
	except:
		# Probably: first run, no file. So, create it
		try:
			os.mkdir(userDirName)
		except FileExistsError:
			pass
		copyfile(dfltFileName, userFileName)
		sfile = open(userFileName)
	try:
		VALUES = json.load(sfile)
		sfile.close()
		checkMerge()
	except json.decoder.JSONDecodeError:
		# It's unable to load data from user file
		# Then replace it with default property file
		copyfile(dfltFileName, userFileName)
		raise Exception(_("exception.settings.jsonLoad"))

	try:
		for k in VALUES.keys():
			DESCRIPTIONS[k] = _(f"settings.{k}.desc")
		'''
		DESCRIPTIONS = {
			"play.friendlyDisableMoveLoss": _("settings.fdmd.description"),
			"play.waterfallInCurrentLocation": _("settings.wfcl.description"),
			"display.expeditionTypeDescription": _("settings.det.description"),
			"display.locale": _("settings.locale.description"),
		}
		'''
	except NameError:
		pass

load()
if merged:
	load()
