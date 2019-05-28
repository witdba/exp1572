import random

def roll(num = 2, type = 6, order = True):
	result = []
	for i in range(1, num + 1):
		v = random.randint(1, type)
		result.append(v)
	if order:
		result.sort()
	return result

def reRoll(originalDices, dicesToRedice):
	n = len(dicesToRedice)
	while dicesToRedice:
		d = int(dicesToRedice.pop())
		for i in range(0, len(originalDices)):
			if originalDices[i] == d:
				originalDices.remove(d)
				break
	originalDices += roll(n)
	originalDices.sort()
	return(originalDices)
