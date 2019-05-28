def getMenuChoice(menuItems, menuHeader, inputPrompt):
	# menuItems{key: [menuText, isEnabled]}
	if not menuItems:
		raise Exception('There are no choices for the menu!')
	mc = {}
	i = 1
	res = None
	print("\n" + menuHeader)
	for k in menuItems.keys():
		if menuItems[k][1]:
			choiceKey = i
			mc[i] = k
			i += 1
		else:
			choiceKey = ' '
		print(f'{choiceKey} : {menuItems[k][0]}')
	if i > 1:
		while True:
			m = input(inputPrompt + ': ')
			if m.isdigit() and int(m) in mc.keys():
				m = int(m)
				break
		res = mc[m]
	return(res)
