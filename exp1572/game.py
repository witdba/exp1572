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
	lake = {"name": _("map.lake.name"), "found": False} # "Озеро Лагос Де Оро"
	camp = {"name": _("map.camp.name"), "found": False} # "Сожжённый лагерь европейских миссионеров"
	herd = {"name": _("map.herd.name"), "found": False} # "Мигрирующие стада животных"
	eclipse = {"name": _("map.eclipse.name"), "found": False} # "Предсказание солнечного затмения"
	princess = {"name": _("map.princess.name"), "found": False} # "Принцесса Канти"
	diego = {"name": _("map.diego.name"), "found": False} # "Диего Мендоса"
	wonders = [lake, camp, herd, eclipse, princess, diego]
	wonder = {"name": _("map.wonder.name"), "count": 0} # "Чудо природы"
	cartesianLocations = {}
	cubeLocations = {}
	empireLocations = []
	lakeLocations = []
	herdLocations = []
	trails = []

	def __init__(self):
		for i in range(0, 45):
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
		for i in range(1, 41, 3):
			self.locations[i].river = True
		self.locations[41].river = True
		self.locations[44].river = True

	def markCoordinates(self):
		for i in range(0, 45):
			self.cartesianLocations[(i // 3, i % 3)] = self.locations[i]
			self.locations[i].cartesianCoordinates = (i // 3, i % 3)
		for i in [21, 22, 23, 33, 34, 35, 39, 40, 41, 42, 43, 44]:
			del(self.cartesianLocations[(i // 3, i % 3)])
		for i in [21, 22, 23, 33, 34, 35, 39, 40, 41, 42, 43, 44]:
			self.cartesianLocations[(i // 3, i % 3 + 1)] = self.locations[i]
			self.locations[i].cartesianCoordinates = (i // 3, i % 3 + 1)
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
		d = sum(dice.roll())
		debug(f'points: {d}')
		if d < 4 and (loc.num // 3) <= (14 - 3):
			if not self.lake["found"]:
				debug('lake not found')
				self.lake["found"] = True
				res = self.lake
			else:
				debug('lake found already')
				self.wonder["count"] += 1
				res = self.wonder
		elif d == 4:
			if not self.camp["found"]:
				debug('camp not found')
				self.camp["found"] = True
				res = self.camp
			else:
				debug('camp found already')
				self.wonder["count"] += 1
				res = self.wonder
		elif d == 5:
			if not self.herd["found"]:
				debug('herd found')
				self.herd["found"] = True
				res = self.herd
			else:
				debug('herd found already')
				self.wonder["count"] += 1
				res = self.wonder
		elif d < 9:
			self.wonder["count"] += 1
			debug(f'wonder count incremented: {self.wonder["count"]}')
			res = self.wonder
		elif d == 10:
			if not self.princess["found"]:
				debug('princess not found')
				self.princess["found"] = True
				res = self.princess
			else:
				debug('princess already found')
				self.wonder["count"] += 1
				res = self.wonder
		else:
			if not self.diego["found"]:
				debug('diego not found')
				self.diego["found"] = True
				res = self.diego
			else:
				debug('diego found already')
				self.wonder["count"] += 1
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
			raise Exception(_("exception.locationAlreadyMapped").format(loc = loc)) # 'Участок {loc} уже нанесён на карту!'

	def foundEmpire(self, loc):
		if not loc in self.empireLocations:
			print(_("message.foundEmpire")) # 'Вы оказались в самом центре империи враждебных туземцев!'
		else:
			print(_("message.foundEmpireInsideEmpire")) # 'Империя враждебных туземцев расширила свои границы'
		self.empireLocations += self.nNeighbors(loc, 2)
		self.empireLocations = list(set(self.empireLocations))

		print(_("message.empireLocations")) # 'Территория империи:'
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
			self.expeditionType = sum(dice.roll(1))
		if self.expeditionType == 6:
			self.FEVERREQ = 2
		else:
			self.FEVERREQ = 3
		self.map = Map()
		if self.expeditionType == 1:
			self.markTrails()
		self.currentLocation = self.map.locations[0]

		self.con = 6
		self.ammo = 6
		self.food = 6
		self.morale = 6
		self.move = 6
		self.fever = False
		self.eclipse_count = 0

	def __str__(self):
		# '{type} экспедиция: {description}'
		res = _("expedition.str.expeditionTypeName").format(type = common.EXPEDITIONTYPES[self.expeditionType][0])
		if settings.VALUES["display.expeditionTypeDescription"] or self.day == 1:
			res += _("expedition.str.expeditionTypeDescription").format(description = common.EXPEDITIONTYPES[self.expeditionType][1])
		else:
			res += '.'
		res += "\n" + _("expedition.str.day").format(day = self.day,
			progressbar = utils.progressBar(42, self.day)) + "\n" # 'День {day} {progressbar}'
		# 'Текущий участок: {loc}'
		if self.currentLocation in self.map.lakeLocations:
			res += _("expedition.str.location").format(loc = self.map.lake["name"])
		else:
			res += _("expedition.str.location").format(loc = self.currentLocation)
		res += "\n"
		if self.fever:
			res += _("expedition.str.feverTrue") + "\n" # 'Лихорадка: [\u2623]'
		else:
			res += _("expedition.str.feverFalse") + "\n" # 'Лихорадка: [ ]'
		# 'Конкистадоры   : {progressbar}'
		res += _("expedition.str.con").format(progressbar = \
			utils.progressBar(6, self.con)) + "\n"
		# 'Снаряжение     : {progressbar}'
		res += _("expedition.str.ammo").format(progressbar = \
			utils.progressBar(6, self.ammo)) + "\n"
		# 'Еда            : {progressbar}'
		res += _("expedition.str.food").format(progressbar = \
			utils.progressBar(6, self.food)) + "\n"
		# 'Боевой дух     : {progressbar}'
		res += _("expedition.str.morale").format(progressbar = \
			utils.progressBar(6, self.morale)) + "\n"
		# 'Пункты движения: {progressbar}'
		res += _("expedition.str.move").format(progressbar = \
			utils.progressBar(6, self.move)) + "\n"
		res += '\n'
		res += _("expedition.str.neighbors") + "\n" # 'Соседние участки:'
		n = self.map.neighbors(self.map.locInLake(self.currentLocation))
		for k, l in n.items():
			if k != "0":
				res += f'{common.DIRS_EXTENSION[k][3].rjust(2)} {common.DIRS_EXTENSION[k][2]} {l}' + '\n'
		return(res)

	def markTrails(self):
		for k in self.map.locations:
			self.map.locations[k].trail = False
		debug('markTrail completed')

	def barMove(self, reqMP):
		return('[-' + ((self.move - 1) * '+' + max(0, (reqMP - self.move + 1)) * '-').ljust(5) + ']')

	def decCon(self):
		self.con -= 1
		if self.con < 1:
			raise Exception(_("message.endGame.noCon")) # Вы потеряли последнего конкистадора. Игра окончена :(
		print(_("message.decCon").format(con = self.con)) # "Потерян конкистадор. Осталось {con}"

	def incCon(self):
		if self.con < 6:
			self.con += 1
			print(_("message.incCon").format(con = self.con)) # "У Вас новый конкистадор. Теперь нас {con}"
		else:
			print(_("message.incConMax")) # "Достигнут максимальный размер отряда"

	def decAmmo(self):
		if self.ammo > 1:
			self.ammo -= 1
			print(_("message.decAmmo").format(ammo = self.ammo)) # 'Снаряжение и боеприпасы пропали. Кое-что осталось: {ammo}'
		else:
			raise Exception(_("message.decAmmoMin")) # 'Достигнут минимум по снаряжению'

	def incAmmo(self, amount = 1):
		if self.ammo + amount <= 6:
			self.ammo += amount
			print(_("message.incAmmo").format(ammo = self.ammo)) # 'Снаряжение и боеприпасы пополнены: {ammo}'
		else:
			self.ammo = 6
			print(_("message.incAmmoMax")) # 'Достигнут максимум по снаряжению'

	def decFood(self):
		if self.food > 1:
			self.food -= 1
			print(_("message.decFood").format(food = self.food)) # 'Запасы пищи уменьшились. Остаток: {food}'
		else:
			print(_("message.decFoodMin")) # 'Нехватка пищи'
			self.decCon()

	def incFood(self, amount = 1):
		if self.food + amount <= 6:
			self.food += amount
			print(_("message.incFood").format(food = self.food)) # 'Пополнены запасы пищи: {food}'
		else:
			self.food = 6
			print(_("message.incFoodMax")) # 'Достигнут максимум запасов пищи'

	def decmorale(self):
		if self.morale > 1:
			self.morale -= 1
			print(_("message.decmorale").format(morale = self.morale)) # 'Боевой дух упал: {morale}'
		else:
			print(_("message.decmoraleMin")) # 'Дезертирство'
			self.decCon()

	def incmorale(self, amount = 1):
		if self.morale + amount <= 6:
			self.morale += amount
			print(_("message.incmorale").format(morale = self.morale)) # 'Боевой дух повышен: {morale}'
		else:
			self.morale = 6
			print(_("message.incmoraleMax")) # 'Достигнут максимум боевого духа'

	def decMove(self, points = 1):
		if self.move - points >= 1:
			self.move -= points
			print(_("message.decMove").format(move = self.move)) # 'Пункты движения уменьшились: {move}'
		else:
			print(_("message.decMoveMin")) # 'Пунктов движения не может быть меньше 1'

	def incMove(self, amount = 1):
		if self.move + amount <= 6:
			self.move += amount
			print(_("message.incMove").format(move = self.move)) # 'Увеличены пункты движения: {move}'
		else:
			self.move = 6
			print(_("message.incMoveMax")) # 'Достигнут максимум пунктов движения'

	def feverSet(self):
		if self.expeditionType == 2:
			print(_("message.feverSetUnableExpType")) # 'Лихорадки удалось избежать!'
		else:
			if not self.fever:
				self.fever = True
				print(_("message.feverSet")) # 'Началась ЛИХОРАДКА!'
			else:
				print(_("message.feverSetAlready")) # 'Ещё один конкистадор приболел...'

	def feverUnset(self):
		self.fever = False
		print(_("message.deverUnset")) # 'Лихорадка закончилась!!!'

	def eclipseSet():
		self.eclipse_count = 2
		print(_("message.eclipseSet")) # 'В следующие два контакта с туземцами выбираете результат!'

	def foundSettlement(self, friendly = False):
		self.currentLocation.settlements += 1
		if friendly:
			self.currentLocation.friendlySettlements += 1
			print(_("message.foundFriendlySettlement")) # 'Обнаружено дружественное поселение!'
		else:
			print(_("message.foundSettlement")) # 'Обнаружено поселение!'
		if not (settings.VALUES["play.friendlyDisableMoveLoss"] and 
			self.currentLocation.friendlySettlements > 0):
			self.decMove()

	def foundTrail(self):
		menuItems = {}
		menuHeader = _("menuHeader.foundTrail") # 'Найдена ТРОПА!!!'
		inputPrompt = _("menuPrompt.foundTrail") # 'Выберите участок, в котором она заканчивается'
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
		print(_("message.foundBox")) # 'Найден ящик с припасами!'
		self.incFood()
		self.incAmmo()
		self.incmorale()

	def rediceForAmmo(self, originalDices, dicesToRedice):
		debug(f'rediceForAmmo enter: {originalDices}, {dicesToRedice}')
		if self.ammo == 1:
			raise Exception(_("exception.rediceNoAmmo")) # 'Переброс за снаряжение невозможен'
		self.decAmmo()
		debug('call dice.reRoll()')
		res = dice.reRoll(originalDices, dicesToRedice)
		debug(f'dice.reRoll() returns: {res}')
		if self.expeditionType == 3:
			res += [2]
			# 'Тип экспедиции "{type}" повысил результат: {res}'
			print(_("message.rediceExpType").format(type = common.EXPEDITIONTYPES[self.expeditionType][0]),
				res = res)
		return(res)

	def do02Walk(self, dicesWalk, jockers):
		debug(f'dicesWalk: {dicesWalk}, jockers: {jockers}')
		points = sum(dicesWalk) + jockers
		if self.currentLocation.land in [
		# 'Трясины', 'Холмы', 'Горы', 'Джунгли'
		_("lands.swamp"), _("lands.hills"), _("lands.mountains"), _("lands.jungle")
		]:
			points -= 1
			# '{land} снизили результат {dicesWalk}: {points}'
			print(_("message.doWalk.landDec").format(land = self.currentLocation.land,
				dicesWalk = dicesWalk, points = points))
		if self.currentLocation.land in [
		# 'Равнины', 'Озеро'
		_("lands.plains"), _("lands.lake")
		]:
			points += 1
			# {land} повысили результат {dicesWalk}: {points}
			print(_("message.doWalk.landInc").format(land = self.currentLocation.land,
				dicesWalk = dicesWalk, points = points))
		if points < 4:
			if self.expeditionType == 6 and self.food > 1:
				self.decFood()
			else:
				self.decCon()
		elif points < 6:
			self.incMove()
			self.feverSet()
		elif points < 9:
			self.incMove()
			self.decmorale()
		elif points == 9:
			self.incMove()
		elif points == 10:
			self.incMove(2)
		elif points == 11:
			self.incMove(3)
		else:
			self.incMove(4)

	def do03Map(self, loc, dicesMap, jockers):
		if self.currentLocation.river and 1 in dicesMap:
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
			if self.expeditionType == 6 and self.food > 1:
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
			if self.expeditionType == 5:
				self.foundSettlement(True)
			else:
				self.foundSettlement(False)
		elif points == 8:
			self.incmorale()
		elif points == 9:
			self.foundTrail()
		else:
			debug('call foundWonder()')
			wonder = self.map.foundWonder(self.currentLocation)
			debug(f'foundWonder returns {wonder}')
			debug(f'currentLocation: {self.currentLocation}')
			print(wonder["name"])
			debug(self.map.locations[44])
			debug('call do07Wonder()')
			self.do07Wonder(wonder)
			debug(self.map.locations[44])

	def do05Contact(self, dicesContact, jockers):
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
				if self.expeditionType == 5:
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
		if self.expeditionType == 2:
			points += 1
			# 'Тип экспедиции "{expType}" повысил результат: {points}'
			print(_("message.doHunting.incExpType").format(expType = common.EXPEDITIONTYPES[self.expeditionType][0],
				points = points))
		if points < 4:
			if self.expeditionType == 6 and self.food > 1:
				self.decFood()
			else:
				self.decCon()
		elif points == 4:
			self.decmorale()
		elif points == 5:
			self.decmorale()
			self.incFood()
		elif points < 9:
			self.incFood()
		elif points < 11:
			self.incFood(2)
		else:
			self.incFood(2)
			self.incmorale()

	def do07Wonder(self, wonder):
		debug('do07Wonder enter')
		if wonder == self.map.camp:
			debug('camp')
			self.incAmmo(5)
			self.foundTrail()
		elif wonder == self.map.herd:
			debug('herd')
			self.map.herdLocations = self.map.nNeighbors(self.currentLocation)
			debug('call manyFood()')
		elif wonder == self.map.wonder:
			debug('wonder')
			self.incmorale(5)
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
			shift = (14 - self.currentLocation.num // 3) // 2
			debug(f'shift: {shift}')
			l0 = self.map.locations[3 * (self.currentLocation.num // 3 + shift) + 1]
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
				l.land = common.LANDS[11]
				print(f'{l}')
		else:
			# 'Неизвестная достопримечательность: {wonder}'
			raise Exception(_("exception.doWonder.unknownWonder").format(wonder = wonder))

	def do08Food(self):
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
				self.incFood(5)
		else:
			self.decFood()

	def getMP(self, toLoc):
		movePoints = 5
		if self.currentLocation.river and toLoc.river \
		and self.currentLocation.num < toLoc.num:
			movePoints = 4
		if (self.currentLocation, toLoc) in self.map.trails:
			movePoints = 3
		if self.currentLocation == toLoc:
			movePoints = 0
		return(movePoints)

	def availableLocations(self):
		''' Вернуть список доступных для продвижения участков и требуемое количество пунктов движения
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
			menuItems[k] = [f'{common.DIRS_EXTENSION[k][3].rjust(2)} {self.barMove(avLocs[k][1])} {common.DIRS_EXTENSION[k][2]} ({avLocs[k][0]})',
			(avLocs[k][1] < self.move)]
			debug(k)
			debug(menuItems[k][0])
			debug(menuItems[k][1])
		m = getMenuChoice(menuItems, menuHeader, inputPrompt)
		if m != "0":
			debug(m)
			nextLocation = avLocs[m][0]
			reqMP = avLocs[m][1]
			if self.expeditionType == 4:
				if (((self.currentLocation, nextLocation) in self.map.trails)
								and self.currentLocation.land != nextLocation.land):
					# Обнаружить достопримечательность
					self.map.foundWonder(nextLocation)
			self.currentLocation = nextLocation
			# 'Ваш отряд переместился на участок {loc}'
			print(_("message.doMove.moveDone").format(loc = nextLocation))
			self.decMove(reqMP)
			movemorale = int(common.DIRS_EXTENSION[m][1])
			self.incmorale(movemorale)
			if self.currentLocation.num == 18:
				self.map.foundWonder(self.currentLocation)	

	def proposeReRoll(self, d1, forAmmo = False):
		debug(f'd1: {d1}')
		rdValid = []
		ok = False
		while not ok:
			if forAmmo:
				if self.ammo <= 1:
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
	'''
	def proposeJockerUse(self):
		jockers = 0
		if self.dicesPlan.count(1) > 1:
			while True:
				jockers = input('Сколько джокеров использовать: ')
				if jockers.isdigit() and int(jockers) <= self.dicesPlan.count(1):
					return jockers
		else:
			return(0)
	'''

	def dice01Plan(self):
		if self.fever:
			# 'ПЛАНИРОВАНИЕ (Лихорадочное)'
			print("\n" + _("header.dicePlanFever"))
		else:
			# 'ПЛАНИРОВАНИЕ'
			print("\n" + _("header.dicePlan"))
		p = dice.roll(5)
		if self.map.diego["found"]:
			p += [1]
			# 'Диего добавил джокер'
			print(_("message.dicePlan.diego"))
		self.dicesPlan = self.proposeReRoll(p)
		debug(f'dicesPlan: {self.dicesPlan}')
		if self.fever and self.currentLocation.land != _("lands.swamp"):
			if self.dicesPlan.count(1) >= self.FEVERREQ:
				self.feverUnset()
				for i in range(0, self.FEVERREQ):
					self.dicesPlan.remove(1)
			else:
				j = 0
				while 1 in self.dicesPlan:
					self.dicesPlan.remove(1)
					j += 1
				if j > 0:
					# 'Во время лихорадки нельзя использовать джокеры'
					print(_("message.dicePlan.feverNoJockers"))
		# 'Кубики планирования: {dices}'
		print(_("message.dicePlan").format(dices = self.dicesPlan))
		# Распределить джокеры
		j = self.dicesPlan.count(1)
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
			while 1 in self.dicesPlan:
				self.dicesPlan.remove(1)
			self.dicesPlan += jl
		if self.con < 6:
			for i in range(2, 7):
				if self.dicesPlan.count(i) >= 4:
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
		d = dice.roll()
		# 'ХОДЬБА'
		print("\n" + _("header.diceWalk"))
		if self.ammo > 1:
			self.dicesWalk = self.proposeReRoll(d, True)
		else:
			self.dicesWalk = d
			# 'Результат броска кубиков: {dices}'
			print(_("message.diceWalk").format(dices = self.dicesWalk))
		self.do02Walk(self.dicesWalk, self.dicesPlan.count(2) - 1)

	def dice03Map(self):
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
		# 'ИССЛЕДОВАНИЕ'
		print("\n" + _("header.diceExplore"))
		d = dice.roll()
		if self.ammo > 1:
			self.dicesExplore = self.proposeReRoll(d, True)
		else:
			self.dicesExplore = d
			# 'Результат броска кубиков: {dices}'
			print(_("message.diceExplore.dices").format(dices = self.dicesExplore))
		self.do04Explore(self.dicesExplore, self.dicesPlan.count(4) - 1)

	def dice05Contact(self):
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
			self.dicesContact = [int(m), int(m) + 1]
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
			if self.ammo > 1:
				self.dicesContact = self.proposeReRoll(d, True)
			else:
				self.dicesContact = d
		self.do05Contact(self.dicesContact, self.dicesPlan.count(5) - 1)

	def dice06Hunting(self):
		# 'ОХОТА'
		print("\n" + _("header.diceHunting"))
		d = dice.roll()
		if self.ammo > 1:
			self.dicesHunting = self.proposeReRoll(d, True)
		else:
			self.dicesHunting = d
		self.do06Hunting(self.dicesHunting, self.dicesPlan.count(6) - 1)

	def playDay(self):
		while True:
			tw = self.map.trailWith(self.currentLocation)
			print()
			print(self)
			c1 = self.currentLocation.cubeCoordinates
			c2 = self.map.locations[44].cubeCoordinates
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
			if self.expeditionType == 1 and self.move >= 3 \
			and not self.currentLocation.trail:
				self.foundTrail()
			if self.day > 42 or self.currentLocation.num == 44:
				break
		score = self.map.countMappedLocations()
		if self.currentLocation.num == 44:
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
