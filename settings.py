import json

with open('settings.json') as sfile:
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
