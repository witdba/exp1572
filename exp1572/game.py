#!/usr/bin/env python

from os import path
import gettext
import babel
import json

from exp1572 import dice, utils, settings, version
# import utils
# import settings
# from menu import getMenuChoice
from exp1572.menu import getMenuChoice
from importlib import reload

# does it later - after translation
# import common

# does it later - and if needed
# import glob

APP_NAME = 'exp1572'

# Game constants
DICE_COUNT_PLAN = 5
DICE_COUNT_INC_CON = 4
WILD = 1
EMPIRE_RADIUS = 2
ECLIPSE_BONUS_COUNT = 2
LOCATIONS_NUM = 44
LOC_WONDER = 18
MAP_WIDTH = 3
DESTINATION = 44
LAST_DAY = 42
EXP_CART = 1
EXP_BOT = 2
EXP_MIL = 3
EXP_ARCH = 4
EXP_REL = 5
EXP_DOCTOR = 6
FEVER_WILDS = 3
FEVER_WILDS_DOCTOR = 2

EXP_MIL_BONUS = 2 # re-roll dice for ammo
EXP_CART_MP = 3

MIN = {"con": 1, "ammo": 1, "food": 1, "morale": 1, "move": 1}
MAX = {"con": 6, "ammo": 6, "food": 6, "morale": 6, "move": 6}
START = {"con": 6, "ammo": 6, "food": 6, "morale": 6, "move": 6, "fever": False}

MP_NORMAL = 5
MP_RIVER = 4
MP_TRAIL = 3
MP_STAY = 0

here = path.abspath(path.dirname(__file__))
LOCALES_DIR = path.join(here, 'locales', '')

# MSG_LEVEL = 'DEBUG'
MSG_LEVEL = 'INFO'
languages = {}


gettext.install(APP_NAME, LOCALES_DIR)
lang = gettext.translation(APP_NAME, LOCALES_DIR, languages=[settings.VALUES["display.locale"]])
lang.install()

# Only here - after translation installed
from exp1572 import common
# In order to get translated descriptions
reload(settings)

def loadTextResources():
	reload(common)
	reload(settings)

'''
TODO:
[] show legend
[] open file with map
[] document the code
[] upload code to the github
[] multiplayer mode
	[] Game object
	[] Player object
[] message() instead of print()
[] public score board
[+] main menu
[] complexity levels (settings presets)
[] game score board
[] game statistics (phase duration etc)
[] current score for game
[] [re-]dices + jockers count and consequences info (terrain and other influences)
[+] save/load (settings at least)
[] gameplay metrics
	[] time spent
		[] total
		[] for phase
		[] for turn
[] log (diary)
[.] Translations
	[+] English
	[] German
	[] Spanish
	[] Portugal
	[] French
[+] DONE 18th location findWonder (sight)
[+] DONE incFood for Ammo in herd locations
[+] DONE expedition type description
[+] DONE menu()
[+] DONE rjust для стрелок
[+] DONE trail to location & trail by Mapping Expedition handling
[-] REJECTED dice unicode characters (and other) REJECTion reason: (symbols are too small)
[+] DONE нельзя делать тропу в тот же участок foundTrail
'''

def useLocale(locale):
	languages[locale].install()
	loadTextResources()

def setOption(optionName, optionValue):
	settings.VALUES[optionName] = optionValue
	settings.save()

def debug(msg):
	if MSG_LEVEL == 'DEBUG':
		if type(msg) == list:
			print('DEBUG:')
			for m in msg:
				print(m)
		else:
			print(f'DEBUG: {msg}')

def cubeOffsetByDir(t1, direction):
	return utils.tupleAdd(t1, common.DIRS[direction][0])

def ring(t1, radius):
	res = []
	r = 1
	c = utils.tupleAdd(t1, utils.tupleMul(common.DIRS['N'][0], radius))
	while r <= radius:
		for i in range(0, 6):
			res += [c]
			c = utils.cubeRotateRight(c, t1)
		c = utils.tupleAdd(c, common.DIRS['SE'][0])
		r += 1
	return(res)

class Location:
	num = 0
	river = False
	land = None
	settlements = 0
	friendlySettlements = 0

	def __init__(self, num):
		self.num = num
		self.sights = []
		self.waterfall = False

	def __lt__(self, other):
		if isinstance(other, self.__class__):
			return(self.num < other.num)
		return(False)

	def __gt__(self, other):
		if isinstance(other, self.__class__):
			return(self.num > other.num)
		return(False)

	def addSight(self, sightType):
		self.sights += [sightType]

	def __str__(self):
		# Ландшафт не известен
		res = '#{num}: {land}'.format(num = str(self.num).ljust(2), 
			land = self.land if self.land else _("location.str.noterrain"))
		if self.river:
			res += _("location.str.river") # ' Река'
		if self.waterfall:
			res += _("location.str.waterfall") # ' с водопадом'
		#if self.friendlySettlements > 0:
		#	res += f'Дружественных поселений: {self.friendlySettlements} '
		if self.settlements > 0:
			s = self.friendlySettlements * u'\N{WINKING FACE}' + (self.settlements - self.friendlySettlements) * u'\N{ANGRY FACE}'
			res += _('location.str.settlements: [{s}]').format(s = s) # Поселений
		if self.sights:
			res += _('location.str.sights: {sights}').format(sights = self.sights) # Достопримечательности
		return(res)

class Map:
	locations = {}
	# "Озеро Лагос Де Оро"
	lake = {"name": _("map.lake.name"), "found": False, "dices": [2, 3]}
	# "Сожжённый лагерь европейских миссионеров"
	camp = {"name": _("map.camp.name"), "found": False, "dices": [4]}
	# "Мигрирующие стада животных"
	herd = {"name": _("map.herd.name"), "found": False, "dices": [5]}
	# "Предсказание солнечного затмения"
	eclipse = {"name": _("map.eclipse.name"), "found": False, "dices": [9]}
	# "Принцесса Канти"
	princess = {"name": _("map.princess.name"), "found": False, "dices": [10]}
	# "Диего Мендоса"
	diego = {"name": _("map.diego.name"), "found": False, "dices": [11, 12]}
	wonders = [lake, camp, herd, eclipse, princess, diego]
	wonder = {"name": _("map.wonder.name"), "count": 0} # "Чудо природы"
	cartesianLocations = {}
	cubeLocations = {}
	empireLocations = []
	lakeLocations = []
	herdLocations = []
	trails = []

	def __init__(self):
		for i in range(0, LOCATIONS_NUM + 1):
			self.locations[i] = Location(i)
		self.locations[0].land = _("lands.mountains") # "Горы"
		self.locations[1].land = _("lands.mountains") # "Горы"
		self.locations[7].land = _("lands.mountains") # "Горы"
		self.markRiver()
		self.markCoordinates()

	def countMappedLocations(self):
		res = 0
		for l in self.locations:
			if self.locations[l].land:
				res += 1
		return res

	def markRiver(self):
		for i in range(1, 41, MAP_WIDTH):
			self.locations[i].river = True
		self.locations[41].river = True
		self.locations[44].river = True

	def markCoordinates(self):
		for i in range(0, LOCATIONS_NUM + 1):
			self.cartesianLocations[(i // MAP_WIDTH, i % MAP_WIDTH)] = self.locations[i]
			self.locations[i].cartesianCoordinates = (i // MAP_WIDTH, i % MAP_WIDTH)
		for i in [21, 22, 23, 33, 34, 35, 39, 40, 41, 42, 43, 44]:
			del(self.cartesianLocations[(i // 3, i % 3)])
		for i in [21, 22, 23, 33, 34, 35, 39, 40, 41, 42, 43, 44]:
			self.cartesianLocations[(i // 3, i % 3 + 1)] = self.locations[i]
			self.locations[i].cartesianCoordinates = (i // MAP_WIDTH, i % MAP_WIDTH + 1)
		# Cube Coordinates
		mapCurve = ['0', 'NE', 'SE', 'NE', 'SE', 'NE', 'SE',
		'SE', 'NE', 'NE', 'SE', 'SE', 'NE', 'SE', 'SE']
		curLoc = (0, -1, 1)
		i = 1
		for direction in mapCurve:
			# debug(f'curLoc: {curLoc}, direction: {direction}, offset: {common.DIRS[direction][0]}')
			curLoc = utils.tupleAdd(curLoc, common.DIRS[direction][0])
			self.locations[i].cubeCoordinates = curLoc
			self.cubeLocations[curLoc] = self.locations[i]
			nLoc = utils.tupleAdd(curLoc, common.DIRS['N'][0])
			self.locations[i - 1].cubeCoordinates = nLoc
			self.cubeLocations[nLoc] = self.locations[i - 1]
			sLoc = utils.tupleAdd(curLoc, common.DIRS['S'][0])
			self.locations[i + 1].cubeCoordinates = sLoc
			self.cubeLocations[sLoc] = self.locations[i + 1]
			i += 3

	def neighbor(self, loc, direction):
		# debug(f'loc: {loc}, direction: {direction}')
		try:
			l = self.cubeLocations[cubeOffsetByDir(loc.cubeCoordinates, direction)]
		except KeyError:
			l = None
		return(l)

	def neighbors(self, loc):
		# loc included
		res = {}
		if type(loc) == list or type(loc) == set:
			dn = {}
			an = {}
			# Получить соседей для всех переданных участков
			for l in loc:
				dn[l] = self.neighbors(l)
			# Собрать всех соседей в один словарь с названиями направлений
			for l in loc:
				for k, n in dn[l].items():
					# Не брать переданные участки
					if not (n in loc):
						try:
							curK = an[n]
							an[n] = curK + k
						except KeyError:
							an[n] = k
				# an - словарь участков
			for n, k in an.items():
				if k in DIRS.keys():
					res[k] = n
				else:
					res[common.DIRS_ALIAS[k]] = n
			# res - словарь расширенных направлений
			# Добавить один из переданных участков
			res["0"] = loc[0]
		else:
			for k in common.DIRS.keys():
				l = self.neighbor(loc, k)
				if l:
					res[k] = l
		return(res)

	def nNeighbors(self, loc, level = 1):
		res = [loc]
		rings = []
		i = 1
		while i <= level:
			rings += ring(loc.cubeCoordinates, i)
			i += 1
		for c in rings:
			debug(c)
			try:
				l = self.cubeLocations[c]
				res += [l]
			except KeyError:
				pass
		return(res)

	def locInLake(self, loc):
		if loc in self.lakeLocations:
			l = self.lakeLocations
		else:
			l = loc
		return l		

	def neighborsToMap(self, loc):
		res = {}
		n = self.neighbors(self.locInLake(loc))
		for d, l in n.items():
			if l.land == None:
				res[d] = l
		return(res)

	def neighborsMapped(self, loc):
		res = {}
		n = self.neighbors(self.locInLake(loc))
		for d, l in n.items():
			if not l.land == None:
				res[d] = l
		return(res)

	def neighborsToTrail(self, loc):
		res = {}
		n = self.neighbors(self.locInLake(loc))
		for d, l in n.items():
			if not (l, loc) in self.trails:
				res[d] = l
		return(res)

	def foundWonder(self, loc):
		debug('foundWonder enter')
		# Define type of Interest
		d = sum(dice.roll())
		debug(f'points: {d}')
		if d in self.lake["dices"]:
			# Lagos de Oro
			# It should be placed in a half of the rest of river
			# so the distance from current location to the end point
			# must be divideable. This means that 14 (x for destination)
			# minus 1 (to preserve lake geography falls into the ocean)
			# minus current x minus 1 (to preserve current location suddenly
			# transforms to the lake) divided by 2 must be >= 1.
			# So: (destX - 1 - currX - 1) // 2 >= 1
			# Or: currX <= destX - 4
			currX = loc.num // MAP_WIDTH
			destX = LOCATIONS_NUM // MAP_WIDTH
			if not self.lake["found"]:
				if currX <= destX - 4:
					debug('lake not found yet')
					self.lake["found"] = True
					res = self.lake
				else:
					debug('lake do not fit on the river')
					self.wonder["count"] += 1
					res = self.wonder
			else:
				debug('lake found already')
				self.wonder["count"] += 1
				res = self.wonder
		elif d in self.camp["dices"]:
			if not self.camp["found"]:
				debug('camp not found')
				self.camp["found"] = True
				res = self.camp
			else:
				debug('camp found already')
				self.wonder["count"] += 1
				res = self.wonder
		elif d in self.herd["dices"]:
			if not self.herd["found"]:
				debug('herd found')
				self.herd["found"] = True
				res = self.herd
			else:
				debug('herd found already')
				self.wonder["count"] += 1
				res = self.wonder
		elif d in self.princess["dices"]:
			if not self.princess["found"]:
				debug('princess not found')
				self.princess["found"] = True
				res = self.princess
			else:
				debug('princess already found')
				self.wonder["count"] += 1
				res = self.wonder
		elif d in self.diego["dices"]:
			if not self.diego["found"]:
				debug('diego not found')
				self.diego["found"] = True
				res = self.diego
			else:
				debug('diego found already')
				self.wonder["count"] += 1
				res = self.wonder
		else:
			self.wonder["count"] += 1
			debug(f'wonder count incremented: {self.wonder["count"]}')
			res = self.wonder
		debug(f'addSight call for {self.locations[loc.num]} ({loc.num}) with "{res["name"]}" argument')
		self.locations[loc.num].addSight(res["name"])
		debug('foundWonder completed')
		return(res)

	def addTrail(self, fromLoc, toLoc):
		self.trails += [(fromLoc, toLoc)]
		self.trails += [(toLoc, fromLoc)]

	def trailWith(self, loc):
		res = []
		for f, t in self.trails:
			if f == loc:
				res += [t]
		return(res)

	def discoverLocation(self, loc, land):
		if loc.land == None:
			loc.land = land
		else:
			# 'Участок {loc} уже нанесён на карту!'
			raise Exception(_("exception.locationAlreadyMapped").format(loc = loc))

	def foundEmpire(self, loc):
		if not loc in self.empireLocations:
			# 'Вы оказались в самом центре империи враждебных туземцев!'
			print(_("message.foundEmpire"))
		else:
			# 'Империя враждебных туземцев расширила свои границы'
			print(_("message.foundEmpireInsideEmpire"))
		self.empireLocations += self.nNeighbors(loc, EMPIRE_RADIUS)
		self.empireLocations = list(set(self.empireLocations))
		# 'Территория империи:'
		print(_("message.empireLocations"))
		for l in self.empireLocations:
			print(l)

	def foundWaterfall(self, loc):
		''' Добавить водопад вниз по течению реки (на loc или на соседний относительно loc участок)
		'''
		if not loc.river:
			# 'Водопад возможен только на реке'
			raise Exception(_("exception.wrongLocationForWaterfall"))
		if settings.VALUES["play.waterfallInCurrentLocation"]:
			l = loc
			msg = _("message.foundWaterfallCurrentLocation")
		else:
			# Найти участок вниз по реке
			for l in self.neighbors(loc).values():
				if l.river and l.num > loc.num:
					break
			msg = _("message.foundWaterfallNextLocation")
		if not l.waterfall:
			if not l in self.lakeLocations:
				l.waterfall = True
				# 'На соседнем устастке {l} обнаружен водопад'
				print(msg.format(l = l))

	def distance(self, fromLoc, toLoc):
		return int(utils.cubeDistance(fromLoc.cubeCoordinates, toLoc.cubeCoordinates))

class Expedition:
	day = 1

	def __init__(self, expeditionType = None):
		if expeditionType:
			self.expeditionType = expeditionType
		else:
			# Random expedition type
			self.expeditionType = sum(dice.roll(1))
		self.FEVERREQ = FEVER_WILDS
		if self.expeditionType == EXP_DOCTOR:
			self.FEVERREQ = FEVER_WILDS_DOCTOR
		self.map = Map()
		if self.expeditionType == EXP_CART:
			self.markTrails()
		self.currentLocation = self.map.locations[0]

		self.con = START["con"]
		self.ammo = START["ammo"]
		self.food = START["food"]
		self.morale = START["morale"]
		self.move = START["move"]
		self.fever = START["fever"]
		self.eclipse_count = 0

	def __str__(self):
		# '{type} экспедиция: {description}'
		res = _("expedition.str.expeditionTypeName").format(type = \
			common.EXPEDITIONTYPES[self.expeditionType][0])
		# Description of expedition type
		if settings.VALUES["display.expeditionTypeDescription"] or self.day == 1:
			res += _("expedition.str.expeditionTypeDescription").format(\
				description = common.EXPEDITIONTYPES[self.expeditionType][1])
		else:
			res += '.'
		# 'День {day} {progressbar}'
		res += "\n" + _("expedition.str.day").format(day = self.day,
			progressbar = utils.progressBar(LAST_DAY, self.day)) + "\n"
		# 'Текущий участок: {loc}'
		if self.currentLocation in self.map.lakeLocations:
			res += _("expedition.str.location").format(loc = self.map.lake["name"])
		else:
			res += _("expedition.str.location").format(loc = self.currentLocation)
		res += "\n"
		if self.fever:
			res += _("expedition.str.feverTrue") + "\n"
		else:
			res += _("expedition.str.feverFalse") + "\n"
		# 'Конкистадоры   : {progressbar}'
		res += _("expedition.str.con").format(progressbar = \
			utils.progressBar(MAX["con"], self.con)) + "\n"
		# 'Снаряжение     : {progressbar}'
		res += _("expedition.str.ammo").format(progressbar = \
			utils.progressBar(MAX["ammo"], self.ammo)) + "\n"
		# 'Еда            : {progressbar}'
		res += _("expedition.str.food").format(progressbar = \
			utils.progressBar(MAX["food"], self.food)) + "\n"
		# 'Боевой дух     : {progressbar}'
		res += _("expedition.str.morale").format(progressbar = \
			utils.progressBar(MAX["morale"], self.morale)) + "\n"
		# 'Пункты движения: {progressbar}'
		res += _("expedition.str.move").format(progressbar = \
			utils.progressBar(MAX["move"], self.move)) + "\n"
		res += '\n'
		# 'Соседние участки:'
		res += _("expedition.str.neighbors") + "\n"
		n = self.map.neighbors(self.map.locInLake(self.currentLocation))
		for k, l in n.items():
			# All except current
			if k != "0":
				res += f'{common.DIRS_EXTENSION[k][3].rjust(2)} {common.DIRS_EXTENSION[k][2]} {l}' + '\n'
		return(res)

	def markTrails(self):
		# Initialize Location.trail for future use
		for k in self.map.locations:
			self.map.locations[k].trail = False
		debug('markTrail completed')

	def barMove(self, reqMP):
		# Display current and required movement points
		return('[-' + ((self.move - 1) * '+' + max(0, (reqMP - self.move + 1)) * '-').ljust(5) + ']')

	def decCon(self):
		# Decrement Conquistadors by 1
		self.con -= 1
		if self.con < MIN["con"]:
			# Вы потеряли последнего конкистадора. Игра окончена :(
			raise Exception(_("message.endGame.noCon"))
		# "Потерян конкистадор. Осталось {con}"
		print(_("message.decCon").format(con = self.con))

	def incCon(self):
		# Increase Conquistadors by 1
		if self.con < MAX["con"]:
			self.con += 1
			# "У Вас новый конкистадор. Теперь нас {con}"
			print(_("message.incCon").format(con = self.con))
		else:
			# "Достигнут максимальный размер отряда"
			print(_("message.incConMax"))

	def decAmmo(self):
		# Decrement muskets by 1
		if self.ammo > MIN["ammo"]:
			self.ammo -= 1
			# 'Снаряжение и боеприпасы пропали. Кое-что осталось: {ammo}'
			print(_("message.decAmmo").format(ammo = self.ammo))
		else:
			# 'Достигнут минимум по снаряжению'
			raise Exception(_("message.decAmmoMin"))

	def incAmmo(self, amount = 1):
		# Increment muskets by amount
		if self.ammo + amount <= MAX["ammo"]:
			self.ammo += amount
			print(_("message.incAmmo").format(ammo = self.ammo)) # 'Снаряжение и боеприпасы пополнены: {ammo}'
		else:
			self.ammo = MAX["ammo"]
			print(_("message.incAmmoMax")) # 'Достигнут максимум по снаряжению'

	def decFood(self):
		# Decrement food by 1
		if self.food > MIN["food"]:
			self.food -= 1
			# 'Запасы пищи уменьшились. Остаток: {food}'
			print(_("message.decFood").format(food = self.food))
		else:
			# 'Нехватка пищи'
			print(_("message.decFoodMin"))
			self.decCon()

	def incFood(self, amount = 1):
		# Increment food by amount
		if self.food + amount <= MAX["food"]:
			self.food += amount
			# 'Пополнены запасы пищи: {food}'
			print(_("message.incFood").format(food = self.food))
		else:
			self.food = MAX["food"]
			# 'Достигнут максимум запасов пищи'
			print(_("message.incFoodMax"))

	def decMorale(self):
		# Decrement morale by 1
		if self.morale > MIN["morale"]:
			self.morale -= 1
			# 'Боевой дух упал: {morale}'
			print(_("message.decMorale").format(morale = self.morale))
		else:
			# 'Дезертирство'
			print(_("message.decMoraleMin"))
			self.decCon()

	def incMorale(self, amount = 1):
		# Increase morale by amount
		if self.morale + amount <= MAX["morale"]:
			self.morale += amount
			# 'Боевой дух повышен: {morale}'
			print(_("message.incMorale").format(morale = self.morale))
		else:
			self.morale = 6
			# 'Достигнут максимум боевого духа'
			print(_("message.incMoraleMax"))

	def decMove(self, points = 1):
		# decrement movement points by amount
		if self.move - points >= MIN["move"]:
			self.move -= points
			# 'Пункты движения уменьшились: {move}'
			print(_("message.decMove").format(move = self.move))
		else:
			# 'Пунктов движения не может быть меньше 1'
			print(_("message.decMoveMin"))

	def incMove(self, amount = 1):
		if self.move + amount <= MAX["move"]:
			self.move += amount
			# 'Увеличены пункты движения: {move}'
			print(_("message.incMove").format(move = self.move))
		else:
			self.move = MAX["move"]
			# 'Достигнут максимум пунктов движения'
			print(_("message.incMoveMax"))

	def feverSet(self):
		# Set fever for the Expedition
		if self.expeditionType == EXP_BOT:
			# 'Лихорадки удалось избежать!'
			print(_("message.feverSetUnableExpType"))
		else:
			if not self.fever:
				self.fever = True
				# 'Началась ЛИХОРАДКА!'
				print(_("message.feverSet"))
			else:
				# 'Ещё один конкистадор приболел...'
				print(_("message.feverSetAlready"))

	def feverUnset(self):
		# Cure the fever
		self.fever = False
		# 'Лихорадка закончилась!!!'
		print(_("message.deverUnset"))

	def eclipseSet():
		# Set bonus count for eclipse prediction
		self.eclipse_count = ECLIPSE_BONUS_COUNT
		# 'В следующие два контакта с туземцами выбираете результат!'
		print(_("message.eclipseSet"))

	def foundSettlement(self, friendly = False):
		# Do the settlement consiquences
		self.currentLocation.settlements += 1
		if friendly:
			self.currentLocation.friendlySettlements += 1
			# 'Обнаружено дружественное поселение!'
			print(_("message.foundFriendlySettlement"))
		else:
			# 'Обнаружено поселение!'
			print(_("message.foundSettlement"))
		if not (settings.VALUES["play.friendlyDisableMoveLoss"] and 
			self.currentLocation.friendlySettlements > 0):
			self.decMove()

	def foundTrail(self):
		# Trail is found. Map their tail
		menuItems = {}
		# 'Найдена ТРОПА!!!'
		menuHeader = _("menuHeader.foundTrail")
		# 'Выберите участок, в котором она заканчивается'
		inputPrompt = _("menuPrompt.foundTrail")
		self.currentLocation.trail = True
		n = self.map.neighborsToTrail(self.currentLocation)
		i = 1
		for k in n:
			menuItems[k] = [f'{common.DIRS_EXTENSION[k][3].rjust(2)} {common.DIRS_EXTENSION[k][2]}', 
			not (self.currentLocation, n[k]) in self.map.trails \
			and self.currentLocation != n[k]]
		m = getMenuChoice(menuItems, menuHeader, inputPrompt)
		self.map.addTrail(self.currentLocation, n[m])

	def foundBox(self):
		# 'Найден ящик с припасами!'
		print(_("message.foundBox"))
		self.incFood()
		self.incAmmo()
		self.incMorale()

	def rediceForAmmo(self, originalDices, dicesToRedice):
		# Re-roll dices for a musket
		debug(f'rediceForAmmo enter: {originalDices}, {dicesToRedice}')
		if self.ammo == MIN["ammo"]:
			# 'Переброс за снаряжение невозможен'
			raise Exception(_("exception.rediceNoAmmo"))
		self.decAmmo()
		debug('call dice.reRoll()')
		res = dice.reRoll(originalDices, dicesToRedice)
		debug(f'dice.reRoll() returns: {res}')
		if self.expeditionType == EXP_MIL:
			res += [EXP_MIL_BONUS]
			# 'Тип экспедиции "{type}" повысил результат: {res}'
			print(_("message.rediceExpType").format(type = \
				common.EXPEDITIONTYPES[self.expeditionType][0]),
				res = res)
		return(res)

	def do02Walk(self, dicesWalk, jockers):
		# Phase 2 processing
		debug(f'dicesWalk: {dicesWalk}, jockers: {jockers}')
		points = sum(dicesWalk) + jockers
		# 'Трясины', 'Холмы', 'Горы', 'Джунгли'
		if self.currentLocation.land in [
		_("lands.swamp"), _("lands.hills"),
		_("lands.mountains"), _("lands.jungle")]:
			points -= 1
			# '{land} снизили результат {dicesWalk}: {points}'
			print(_("message.doWalk.landDec").format(land = self.currentLocation.land,
				dicesWalk = dicesWalk, points = points))
		# 'Равнины', 'Озеро'
		if self.currentLocation.land in [_("lands.plains"), _("lands.lake")]:
			points += 1
			# {land} повысили результат {dicesWalk}: {points}
			print(_("message.doWalk.landInc").format(land = self.currentLocation.land,
				dicesWalk = dicesWalk, points = points))
		# В принципе, набор вызываемых элементарных действий тоже может быть
		# настраиваемым по словарю
		if points < 4:
			if self.expeditionType == EXP_DOCTOR and self.food > MIN["food"]:
				self.decFood()
			else:
				self.decCon()
		elif points < 6:
			self.incMove()
			self.feverSet()
		elif points < 9:
			self.incMove()
			self.decMorale()
		elif points == 9:
			self.incMove()
		elif points == 10:
			self.incMove(2)
		elif points == 11:
			self.incMove(3)
		else:
			self.incMove(4)

	def do03Map(self, loc, dicesMap, jockers):
		# Phase 3 processing
		if self.currentLocation.river and (WILD in dicesMap):
			# Добавить водопад вниз по течению
			self.map.foundWaterfall(self.currentLocation)
		points = min(12, sum(dicesMap) + jockers)
		if 6 <= points <= 9:
			land = self.currentLocation.land
		else:
			land = common.LANDS[points]
		if loc.land == None:
			loc.land = land
		else:
			# 'Участок {loc} уже нанесён на карту!'
			raise Exception(_("exception.doMap.locationMapped").format(loc = loc))

	def do04Explore(self, dicesExplore, jockers):
		# Phase 4 processing
		points = sum(dicesExplore) + jockers
		debug(f'dicesExplore: {dicesExplore}, jockers: {jockers}')
		if self.currentLocation.land in ["lands.jungle"]:
			points -= 1
			# '{land} понизили результат {dices}: {points}'
			print(_("message.doExplore.landDec").format(land = self.currentLocation.land, 
				dices = dicesExplore, points = points))
		if self.currentLocation.friendlySettlements > 0:
			points += self.currentLocation.friendlySettlements
			 #'Дружественные поселения повысили результат: {points}'
			print(_("message.doExplore.incFriendly").format(points = points))
		if points < 3:
			# 'Потеря конкистадора ...'
			print(_("message.doExplore.decCon"))
			if self.expeditionType == EXP_DOCTOR and self.food > MIN["food"]:
				# '... заменена на потерю провизии!'
				print(_("message.doExplore.decConExpType"))
				self.decFood()
			else:
				self.decCon()
		elif points < 4:
			self.feverSet()
		elif points < 6:
			self.decMove()
		elif points < 8:
			if self.expeditionType == EXP_REL:
				self.foundSettlement(True)
			else:
				self.foundSettlement(False)
		elif points == 8:
			self.incMorale()
		elif points == 9:
			self.foundTrail()
		else:
			debug('call foundWonder()')
			wonder = self.map.foundWonder(self.currentLocation)
			debug(f'foundWonder returns {wonder}')
			debug(f'currentLocation: {self.currentLocation}')
			print(wonder["name"])
			debug('call do07Wonder()')
			self.do07Wonder(wonder)

	def do05Contact(self, dicesContact, jockers):
		# Phase 5 processing
		debug(f'do05Contact enter: dicesContact: {dicesContact}, jockers: {jockers}')
		if self.currentLocation in self.map.empireLocations \
		and len(dicesContact) > 1:
			# 'На территории империи бросать только 1 кубик!'
			raise Exception(_("exception.doContact1Dice"))
		if self.currentLocation.land == _("lands.lake"):
			# 'На озере контакта нет'
			print(_("message.doContact.noContact"))
		else:
			points = sum(dicesContact) + jockers
			if self.currentLocation.land in [_("lands.hills")]:
				points += 1
				# '{land} повысили результат {dices}: {points}'
				print(_("message.doContact.landInc").format(land = self.currentLocation.land,
					dices = dicesContact, points = points))
			if points < 5:
				self.map.foundEmpire(self.currentLocation)
			elif points == 5:
				self.feverSet()
			elif points < 9:
				if self.expeditionType == EXP_REL:
					self.foundSettlement(True)
				else:
					self.foundSettlement(False)
			elif points == 9:
				self.foundTrail()
			elif points == 10:
				self.incFood()
				self.foundSettlement(True)
			else:
				self.foundBox()
				self.foundSettlement(True)

	def do06Hunting(self, dicesHunting, jockers):
		# Phase 6 processing
		debug(f'dicesHunting: {dicesHunting}, jockers: {jockers}')
		points = sum(dicesHunting) + jockers
		# 'Горы', 'Лес'
		if self.currentLocation.land in [_("lands.mountains"), _("lands.forest")]:
			points += 1
			# '{land} повысили результат {dices}: {points}'
			print(_("message.doHunting.landInc").format(land = self.currentLocation.land,
				dices = dicesHunting, points = points))
		if self.currentLocation.friendlySettlements > 0:
			points += self.currentLocation.friendlySettlements
			# 'Дружественные поселения повысили результат: {points}'
			print(_("message.doHunting.friendlyInc").format(points = points))
		if self.expeditionType == EXP_BOT:
			points += 1
			# 'Тип экспедиции "{expType}" повысил результат: {points}'
			print(_("message.doHunting.incExpType").format(expType = 
				common.EXPEDITIONTYPES[self.expeditionType][0],
				points = points))
		if points < 4:
			if self.expeditionType == EXP_DOCTOR and self.food > MIN["food"]:
				self.decFood()
			else:
				self.decCon()
		elif points == 4:
			self.decMorale()
		elif points == 5:
			self.decMorale()
			self.incFood()
		elif points < 9:
			self.incFood()
		elif points < 11:
			self.incFood(2)
		else:
			self.incFood(2)
			self.incMorale()

	def do07Wonder(self, wonder):
		# Phase 7 processing
		debug('do07Wonder enter')
		if wonder == self.map.camp:
			debug('camp')
			self.incAmmo(MAX["ammo"] - 1)
			self.foundTrail()
		elif wonder == self.map.herd:
			debug('herd')
			self.map.herdLocations = self.map.nNeighbors(self.currentLocation)
			debug('call manyFood()')
		elif wonder == self.map.wonder:
			debug('wonder')
			self.incMorale(MAX["morale"] - 1)
		elif wonder == self.map.eclipse:
			debug('eclipse')
			self.eclipseSet()
		elif wonder == self.map.princess:
			# 'Принцесса Канти проявит себя при контакте с туземцами'
			print(_("message.doWonder.princess"))
		elif wonder == self.map.diego:
			debug('diego')
			self.incCon()
			self.incAmmo()
			# 'Диего Мендоса добавляет джокера на этапе планирования'
			print(_("message.doWonder.diego"))
		elif wonder == self.map.lake:
			debug('lake')
			# Find a location (on the river) between current and final locations
			shift = ((LOCATIONS_NUM // MAP_WIDTH) - 
				self.currentLocation.num // MAP_WIDTH) // 2
			debug(f'shift: {shift}')
			l0 = self.map.locations[MAP_WIDTH * (self.currentLocation.num // 
				MAP_WIDTH + shift) + 1]
			debug(f'l0: {l0.cubeCoordinates}')
			# Dice(1) to define two neighbor locations (amongst 6 possible options)
			c1 = common.DIRS[list(common.DIRS.keys())[1:][int(dice.roll(1)[0])-1]][0]
			debug(f'c1: {c1}')
			c2 = utils.tupleAdd(l0.cubeCoordinates, c1)
			debug(f'c2: {c2}')
			l1 = self.map.cubeLocations[c2]
			debug(f'l1: {l1}')
			l2 = self.map.cubeLocations[utils.cubeRotateRight(l1.cubeCoordinates, l0.cubeCoordinates)]
			# Register 3 locations as Lake Lagos de Oro
			self.map.lakeLocations = [l0, l1, l2]
			# Mark their lands as lake
			# 'Обнаружено Озеро Лагос де Оро! Оно занимает следующие участки:'
			print(_("message.doWonder.lake"))
			for l in self.map.lakeLocations:
				l.land = _("lands.lake")
				print(f'{l}')
		else:
			# 'Неизвестная достопримечательность: {wonder}'
			raise Exception(_("exception.doWonder.unknownWonder").format(wonder = wonder))

	def do08Food(self):
		# Phase 8 processing
		# 'ПРИЁМ ПИЩИ'
		print("\n" + _("header.doFood"))
		if self.currentLocation in self.map.herdLocations:
			menuHeader = _("menuHeader.doFood")
			inputPrompt = _("menuPrompt.doFood")
			menuItems = {}
			# Пока не понял - почему, но без str() показывает только
			# первые буквы
			menuItems['Y'] = str(_("doFood.menuIntemY"))
			menuItems['N'] = str(_("doFood.menuIntemN"))
			m = getMenuChoice(menuItems, menuHeader, inputPrompt)
			if m == 'Y':
				self.decAmmo()
				self.incFood(MAX["food"] - 1)
		else:
			self.decFood()

	def getMP(self, toLoc):
		movePoints = MP_NORMAL
		if self.currentLocation.river and toLoc.river \
		and self.currentLocation.num < toLoc.num:
			# May be replaced by locations comparison
			movePoints = MP_RIVER
		if (self.currentLocation, toLoc) in self.map.trails:
			movePoints = MP_TRAIL
		if self.currentLocation == toLoc:
			movePoints = MP_STAY
		return(movePoints)

	def availableLocations(self):
		''' Return list of available for move locations
		and move points required
		'''
		nm = self.map.neighborsMapped(self.currentLocation)
		# debug(nm)
		todel = []
		res = {}
		for k in nm.keys():
			l = nm[k]
			# Водопад
			if ((self.currentLocation.waterfall and l.river and self.currentLocation < l) \
			or (l.waterfall and self.currentLocation.river and self.currentLocation > l)):
				todel += [k]
		for i in todel:
			debug(i)
			del(nm[i])
		for k in nm.keys():
			res[k] = (nm[k], self.getMP(nm[k]))
		return(res)

	def do09move(self):
		# Phase 9 processing
		# 'ПРОДВИЖЕНИЕ ПО КАРТЕ'
		print("\n" + _("header.doMove"))
		debug(f'movePoints: {self.move}')
		avLocs = self.availableLocations()
		menuItems = {}
		# 'Нанесены на карту такие соседние участки:'
		menuHeader = _("menuHeader.doMove")
		# 'Выберите участок для продвижения'
		inputPrompt = _("menuPrompt.doMove")
		for k in avLocs.keys():
			debug(f'avLocs[k]: {avLocs[k]}')
			menuItems[k] = [f'{common.DIRS_EXTENSION[k][3].rjust(2)} \
{self.barMove(avLocs[k][1])} {common.DIRS_EXTENSION[k][2]} ({avLocs[k][0]})',
			(avLocs[k][1] < self.move)]
			debug(k)
			debug(menuItems[k][0])
			debug(menuItems[k][1])
		m = getMenuChoice(menuItems, menuHeader, inputPrompt)
		if m != "0":
			debug(m)
			nextLocation = avLocs[m][0]
			reqMP = avLocs[m][1]
			if self.expeditionType == EXP_ARCH:
				if (((self.currentLocation, nextLocation) in self.map.trails)
								and self.currentLocation.land != nextLocation.land):
					# Обнаружить достопримечательность
					self.map.foundWonder(nextLocation)
			self.currentLocation = nextLocation
			# 'Ваш отряд переместился на участок {loc}'
			print(_("message.doMove.moveDone").format(loc = nextLocation))
			self.decMove(reqMP)
			movemorale = int(common.DIRS_EXTENSION[m][1])
			self.incMorale(movemorale)
			if self.currentLocation.num == LOC_WONDER:
				self.map.foundWonder(self.currentLocation)	

	def proposeReRoll(self, d1, forAmmo = False):
		# Propose re-role dice if there is a musket
		debug(f'd1: {d1}')
		rdValid = []
		ok = False
		while not ok:
			if forAmmo:
				if self.ammo <= MIN["ammo"]:
					# 'Недостаточно снаряжения для переброски кубиков'
					raise Exception(_("exception.proposeReRoll.noAmmo"))
				else:
					# 'Перебросить кубики (за Снаряжение) {dices}: '
					rd = list(input(_("message.proposeReRollForAmmo").format(dices = d1)))
			else:
				# 'Перебросить кубики {dices}: '
				rd = list(input(_("message.proposeReRoll").format(dices = d1)))
			debug(f'rd: {rd}')
			rd = list(map(int, rd))
			debug(f'rd: {rd}')
			ok = True
			for i in range(0, 6):
				debug(f'i: {i}, rd{i + 1}: {rd.count(i + 1)}, d1{i + 1}: {d1.count(i + 1)}')
				ok = ok and (rd.count(i + 1) <= d1.count(i + 1))
				debug(ok)
		if rd:
			if forAmmo:
				debug(f'call rediceForAmmo with d1: {d1}, rd: {rd}')
				res = self.rediceForAmmo(d1, rd)
				debug(f'rediceForAmmo returns: {res}')
			else:
				debug(d1)
				debug(rd)
				res = dice.reRoll(d1, rd)
				debug(res)
			# 'Результат переброса кубиков: {dices}'
			print(_("message.reRollResult").format(dices = res))
		else:
			res = d1
		return(res)

	def dice01Plan(self):
		# Phase 1
		if self.fever:
			# 'ПЛАНИРОВАНИЕ (Лихорадочное)'
			print("\n" + _("header.dicePlanFever"))
		else:
			# 'ПЛАНИРОВАНИЕ'
			print("\n" + _("header.dicePlan"))
		p = dice.roll(DICE_COUNT_PLAN)
		if self.map.diego["found"]:
			p += [WILD]
			# 'Диего добавил джокер'
			print(_("message.dicePlan.diego"))
		self.dicesPlan = self.proposeReRoll(p)
		debug(f'dicesPlan: {self.dicesPlan}')
		if self.fever and self.currentLocation.land != _("lands.swamp"):
			if self.dicesPlan.count(WILD) >= self.FEVERREQ:
				self.feverUnset()
				for i in range(0, self.FEVERREQ):
					self.dicesPlan.remove(WILD)
			else:
				j = 0
				while WILD in self.dicesPlan:
					self.dicesPlan.remove(WILD)
					j += 1
				if j > 0:
					# 'Во время лихорадки нельзя использовать джокеры'
					print(_("message.dicePlan.feverNoJockers"))
		# 'Кубики планирования: {dices}'
		print(_("message.dicePlan").format(dices = self.dicesPlan))
		# Распределить джокеры
		j = self.dicesPlan.count(WILD)
		if j >= 1:
			# 'Распределите имеющиеся джокеры по этапам (2-6). Например, 223.'
			print(_("menuHeader.dicePlan.useJockers"))
			while True:
				# 'Напечатайте номера этапов по количеству джокеров ({j}): '
				s = input(_("menuPrompt.dicePlan.useJockers").format(j = j))
				if s.isdigit() and len(s) == j:
					jl = list(map(int, list(s)))
					if min(jl) >= 2 and max(jl) <= 6:
						break
			while WILD in self.dicesPlan:
				self.dicesPlan.remove(WILD)
			self.dicesPlan += jl
		if self.con < MAX["con"]:
			for i in range(2, 7):
				if self.dicesPlan.count(i) >= DICE_COUNT_INC_CON:
					self.incCon()
		if self.dicesPlan.count(2) >= 1:
			self.dice02Walk()
		if self.dicesPlan.count(3) >= 1:
			self.dice03Map()
		if self.dicesPlan.count(4) >= 1:
			self.dice04Explore()
		if self.dicesPlan.count(5) >= 1:
			if self.currentLocation.land == _("lands.lake"):
				# 'На озере контакт с туземцами не возможен'
				print(_("message.dicePlan.noContact"))
			else:
				self.dice05Contact()
		if self.dicesPlan.count(6) >= 1:
			self.dice06Hunting()

	def dice02Walk(self):
		# Phase 2
		d = dice.roll()
		# 'ХОДЬБА'
		print("\n" + _("header.diceWalk"))
		if self.ammo > MIN["ammo"]:
			self.dicesWalk = self.proposeReRoll(d, True)
		else:
			self.dicesWalk = d
			# 'Результат броска кубиков: {dices}'
			print(_("message.diceWalk").format(dices = self.dicesWalk))
		self.do02Walk(self.dicesWalk, self.dicesPlan.count(2) - 1)

	def dice03Map(self):
		# Phase 3
		# 'СОСТАВЛЕНИЕ КАРТЫ'
		print("\n" + _("header.diceMap"))
		menuItems = {}
		# 'Для картографирования доступны такие участки:'
		menuHeader = _("menuHeader.diceMap")
		# 'Выберите участок для нанесения на карту'
		inputPrompt = _("menuPrompt.diceMap")
		i = 1
		''' В настройки: показывать все соседние участки при составлении карты
			Тогда условие для menuItems: not dirLoc[k].land
			А dirLoc = self.map.neighbors()
			И menuHeader поменять
		'''
		dirLoc = self.map.neighborsToMap(self.currentLocation)
		debug(f'dirLoc: {dirLoc}')
		''' Если текущий участок принадлежит озеру Лагос де Оро,
			то соседних участков может быть 9. Это означает, что
			нужно использовать расширение словаря направлений.

			Для картографирования участки озера Лагос де Оро не
			предоставляются, так как их ландшафт устанавливается
			при открытии этой достопримечательности.

			Другое дело - передвижение по карте...
		'''
		for k in dirLoc.keys():
			menuItems[k] = [f'{common.DIRS_EXTENSION[k][3].rjust(2)} {common.DIRS_EXTENSION[k][2]}', True]
		if menuItems:
			m = getMenuChoice(menuItems, menuHeader, inputPrompt)
			self.dicesMap = dice.roll()
			# 'Кубики составления карты: {dices}'
			print(_("message.diceMap.dices").format(dices = self.dicesMap))
			self.do03Map(dirLoc[m], self.dicesMap, self.dicesPlan.count(3) - 1)
			# 'На карту нанесён ({direction}) новый участок: {loc}'
			print(_("message.diceMap.mapDone").format(direction = common.DIRS_EXTENSION[m][3], loc = dirLoc[m]))
		else:
			# 'Все соседние участки уже нанесены на карту'
			print(_("message.diceMap.noLocations"))

	def dice04Explore(self):
		# Phase 4
		# 'ИССЛЕДОВАНИЕ'
		print("\n" + _("header.diceExplore"))
		d = dice.roll()
		if self.ammo > MIN["ammo"]:
			self.dicesExplore = self.proposeReRoll(d, True)
		else:
			self.dicesExplore = d
			# 'Результат броска кубиков: {dices}'
			print(_("message.diceExplore.dices").format(dices = self.dicesExplore))
		self.do04Explore(self.dicesExplore, self.dicesPlan.count(4) - 1)

	def dice05Contact(self):
		# Phase 5
		# 'КОНТАКТ С ТУЗЕМЦАМИ'
		print("\n" + _("header.diceContact"))
		if self.eclipse_count > 0:
			menuItems = {}
			# 'Однажды Вы предсказали туземмцам солнечное затмение.'
			menuHeader = _("menuHeader.diceContact.eclipse")
			# 'Выберите желаемый результат контакта с туземцами'
			inputPrompt = _("menuPrompt.diceContact.eclipse")
			for k in common.CONTACT_RESULTS.keys():
				menuItems[k] = common.CONTACT_RESULTS[k]
			m = getMenuChoice(menuItems, menuHeader, inputPrompt)
			# Formula ...
			self.dicesContact = [int(m), int(m) + 1]
			# ... with exception
			if m == 5:
				self.dicesContact = [5, 5]
			self.do05Contact(self.dicesContact)
			self.eclipse_count -= 1
		else:
			if self.currentLocation in self.map.empireLocations:
				d = dice.roll(1)
			else:
				d = dice.roll()
			if self.map.princess["found"]:
				while 1 in d or 2 in d:
					d = dice.roll(len(d))
			if self.ammo > MIN["ammo"]:
				self.dicesContact = self.proposeReRoll(d, True)
			else:
				self.dicesContact = d
		self.do05Contact(self.dicesContact, self.dicesPlan.count(5) - 1)

	def dice06Hunting(self):
		# Phase 6
		# 'ОХОТА'
		print("\n" + _("header.diceHunting"))
		d = dice.roll()
		if self.ammo > MIN["ammo"]:
			self.dicesHunting = self.proposeReRoll(d, True)
		else:
			self.dicesHunting = d
		self.do06Hunting(self.dicesHunting, self.dicesPlan.count(6) - 1)

	def playDay(self):
		# Play all phases
		while True:
			tw = self.map.trailWith(self.currentLocation)
			print()
			print(self)
			c1 = self.currentLocation.cubeCoordinates
			c2 = self.map.locations[DESTINATION].cubeCoordinates
			# 'Расстояние до цели: {distance}'
			print(_("message.playDay.distance").format(distance = utils.cubeDistance(c1, c2)))
			if tw:
				# 'Имеются тропы на следующие участки:'
				print(_("message.playDay.trails"))
				for l in tw:
					print(l)
			self.dice01Plan()
			self.do08Food()
			while True:
				try:
					self.do09move()
					break
				except Exception as e:
					print(e)
					break

			self.day += 1
			# Cartography expedition found a trail if has > 2 MP 
			if self.expeditionType == EXP_CART and self.move >= EXP_CART_MP \
			and not self.currentLocation.trail:
				self.foundTrail()
			if self.day > LAST_DAY or self.currentLocation.num == DESTINATION:
				break
		score = self.map.countMappedLocations()
		if self.currentLocation.num == DESTINATION:
			print(_("message.gameover.win"))
			score += self.con
		else:
			print(_("message.gameover.defeat"))
		print(_("message.game.score {score}").format(score = score))

def mainMenu():
	''' 
	'''
	menuItemsPlay = {}
	menuItemsOptions = {}
	while True:
		# Составление пунктов меню помещается в цикле из-за необходимости
		# предоставлять правильный перевод при смене языка
		menuItems = {
			1: [_("menu.main.expType"), True],
			2: [_("menu.main.options"), True],
			0: [_("menu.main.quit"), True]
		}
		m = getMenuChoice(menuItems, _("menu.main.header"), _("menu.main.prompt"))
		if m == 1:
			menuItemsPlay['RANDOM'] = [_("menu.play.random"), True]
			for et in common.EXPEDITIONTYPES:
				menuItemsPlay[et] = [common.EXPEDITIONTYPES[et][0], True]
			menuItemsPlay['BACK'] = [_("menu.play.back"), True]
			while True:
				mp = getMenuChoice(menuItemsPlay, _("menu.play.header"), _("menu.play.prompt"))
				if mp == 'BACK':
					break
				else:
					et = None if mp == 'RANDOM' else mp
					e = Expedition(et)
					e.playDay()
		elif m == 2:
			while True:
				for s in settings.VALUES:
					menuItemsOptions[s] = [settings.DESCRIPTIONS[s] + ": " + str(settings.VALUES[s]), True]
				menuItemsOptions['BACK'] = [_("menu.options.back"), True]
				mo = getMenuChoice(menuItemsOptions, _("menu.options.header"), _("menu.options.prompt"))
				if mo == 'BACK':
					break
				elif mo == "display.locale":
					import glob
					menuItemsLocale = {}
					folders = [f.replace(LOCALES_DIR, '').replace('/', '') \
					for f in glob.glob(LOCALES_DIR + "**/", recursive = False)]
					folders.sort()
					for f in folders:
						lang = babel.Locale(f).display_name
						if not lang:
							lang = babel.Locale(f.split('_')[0], f.split('_')[1]).display_name
						menuItemsLocale[f] = [lang, True]
						languages[f] = gettext.translation(APP_NAME, LOCALES_DIR, languages = [f])
					menuItemsLocale['BACK'] = [_("menu.locales.back"), True]
					ml = getMenuChoice(menuItemsLocale, _("menu.locale.header"), _("menu.locale.prompt"))
					if ml == 'BACK':
						pass
					else:
						print(ml)
						setOption("display.locale", ml)
						useLocale(ml)
				elif mo in ("display.expeditionTypeDescription", "play.waterfallInCurrentLocation",
					"play.friendlyDisableMoveLoss"):
					setOption(mo, not settings.VALUES[mo])
		else:
			break

if __name__ == "__main__":
	m = exp1572.mainMenu()
