import json
from os import path

here = path.abspath(path.dirname(__file__))
with open(path.join(here, 'settings.json')) as sfile:
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
