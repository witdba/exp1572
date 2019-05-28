def tupleAdd(t1, t2):
	return tuple(map(lambda x, y: x + y, t1, t2))

def tupleMul(t1, scalar):
	return tuple(map(lambda x: x * scalar, t1))

def tupleSub(t1, t2):
	return tupleAdd(t1, tupleMul(t2, -1))

def cubeDistance(t1, t2):
	d = tupleSub(t2, t1)
	return (abs(d[0]) + abs(d[1]) + abs(d[2])) / 2

def cubeRotateRight(t1, t0 = (0, 0, 0)):
	v = tupleSub(t1, t0)
	return(tupleAdd(t0, (-v[2], -v[0], -v[1])))

def cubeRotateLeft(t1, t0 = (0, 0, 0)):
	v = tupleSub(t1, t0)
	return(tupleAdd(t0, (-v[1], -v[2], -v[0])))

def progressBar(size, progress, symbol = '*'):
	if size < progress:
		raise Exception('size < progress')
	return '[' + (progress * symbol).ljust(size) + ']'

