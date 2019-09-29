#FLM: Glyph: Nodes
# ----------------------------------------
# (C) Vassil Kateliev, 2018 (http://www.kateliev.com)
# (C) Karandash Type Foundry (http://www.karandash.eu)
#-----------------------------------------

# No warranties. By using this you agree
# that you use it at your own risk!

# - Init
global pLayers
global pMode
pLayers = None
pMode = 0
app_name, app_version = 'TypeRig | Nodes', '0.70'

# - Dependencies -----------------
import fontlab as fl6
import fontgate as fgt
from PythonQt import QtCore
from typerig import QtGui
from typerig.glyph import eGlyph
from typerig.node import eNode
from typerig.contour import eContour
from typerig.proxy import pFont, pFontMetrics, pContour
from typerig.gui import getProcessGlyphs
from typerig.brain import Coord, Line

# - Sub widgets ------------------------
class basicOps(QtGui.QGridLayout):
	# - Basic Node operations
	def __init__(self):
		super(basicOps, self).__init__()
		
		# - Basic operations
		self.btn_insert = QtGui.QPushButton('&Insert')
		self.btn_remove = QtGui.QPushButton('&Remove')
		self.btn_mitre = QtGui.QPushButton('&Mitre')
		self.btn_knot = QtGui.QPushButton('&Overlap')
		self.btn_trapA = QtGui.QPushButton('&Trap')
		self.btn_rebuild = QtGui.QPushButton('Rebuil&d')
						
		self.btn_insert.setMinimumWidth(80)
		self.btn_remove.setMinimumWidth(80)
		self.btn_mitre.setMinimumWidth(80)
		self.btn_knot.setMinimumWidth(80)
		self.btn_trapA.setMinimumWidth(80)
		self.btn_rebuild.setMinimumWidth(80)

		self.btn_insert.setToolTip('Insert Node after Selection\nat given time T.')
		self.btn_remove.setToolTip('Remove Selected Nodes!\nFor proper curve node deletion\nalso select the associated handles!')
		self.btn_mitre.setToolTip('Mitre corner using size X.')
		self.btn_knot.setToolTip('Overlap corner using radius -X.')
		self.btn_trapA.setToolTip('Insert Angular (generic) Ink Trap at node selected')
		self.btn_rebuild.setToolTip('Rebuild corner from nodes selected.')
		
		self.btn_insert.clicked.connect(self.insertNode)
		self.btn_remove.clicked.connect(self.removeNode)
		self.btn_mitre.clicked.connect(lambda: self.cornerMitre(False))
		self.btn_knot.clicked.connect(lambda: self.cornerMitre(True))
		self.btn_trapA.clicked.connect(lambda: self.cornerTrap())
		self.btn_rebuild.clicked.connect(lambda: self.cornerRebuild())

		# - Edit fields
		self.edt_time = QtGui.QLineEdit('0.5')
		self.edt_radius = QtGui.QLineEdit('5')
		self.edt_trap = QtGui.QLineEdit('5, 30, 2')
		
		self.edt_time.setToolTip('Insertion Time.')
		self.edt_radius.setToolTip('Mitre size/Overlap or Round Radius.')
		self.edt_trap.setToolTip('Ink trap: Incision into glyphs flesh, Side depth, Trap size')

		# -- Build: Basic Ops
		self.addWidget(self.btn_insert, 	0, 0)
		self.addWidget(QtGui.QLabel('T:'), 	0, 1)
		self.addWidget(self.edt_time, 		0, 2)
		self.addWidget(self.btn_remove, 	0, 3)

		self.addWidget(self.btn_mitre,		1, 0)
		self.addWidget(QtGui.QLabel('X:'), 	1, 1)
		self.addWidget(self.edt_radius,		1, 2)
		self.addWidget(self.btn_knot,		1, 3)

		self.addWidget(self.btn_trapA,		2, 0)
		self.addWidget(QtGui.QLabel('P:'),	2, 1)
		self.addWidget(self.edt_trap,		2, 2)
		self.addWidget(self.btn_rebuild,		2, 3)


	def insertNode(self):
		glyph = eGlyph()
		selection = glyph.selectedAtContours(True)
		wLayers = glyph._prepareLayers(pLayers)

		for layer in wLayers:
			nodeMap = glyph._mapOn(layer)
			
			for cID, nID in reversed(selection):
				glyph.insertNodeAt(cID, nodeMap[cID][nID] + float(self.edt_time.text), layer)

		glyph.updateObject(glyph.fl, 'Insert Node @ %s.' %'; '.join(wLayers))
		glyph.update()

	def removeNode(self):
		glyph = eGlyph()
		wLayers = glyph._prepareLayers(pLayers)

		'''
		selection = glyph.selectedAtContours()
		for layer in wLayers:
			for cID, nID in reversed(selection):
				glyph.removeNodeAt(cID, nID, layer)
				glyph.contours(layer)[cID].updateIndices()

				#glyph.contours()[cID].clearNodes()
		'''
		
		# Kind of working
		for layer in wLayers:
			selection = glyph.selectedAtContours(False, layer)

			for contour, node in reversed(selection):
				prevNode, nextNode = node.prevNode(), node.nextNode()
				
				if not prevNode.isOn:
					contour.removeOne(prevNode)
			
				if not nextNode.isOn:
					contour.removeOne(nextNode)

				contour.removeOne(node)	
				contour.updateIndices()
		
		'''
		# - Not Working Again!
		from typerig.utils import groupConsecutives		
		selection = glyph.selectedAtContours()
		tempDict = {}

		for cID, nID in selection:
			tempDict.setdefault(cID, []).append(nID)

		for layer in wLayers:
			for cID, nIDlist in tempDict.iteritems():
				nidList = groupConsecutives(nIDlist)

				for pair in reversed(nidList):
					
					nodeA = eNode(glyph.contours(layer)[cID].nodes()[pair[-1] if len(pair) > 1 else pair[0]]).getNextOn()
					nodeB = eNode(glyph.contours(layer)[cID].nodes()[pair[0]]).getPrevOn()

					glyph.contours(layer)[cID].removeNodesBetween(nodeB, nodeA)
									
		'''
		glyph.update()
		glyph.updateObject(glyph.fl, 'Delete Node @ %s.' %'; '.join(wLayers))

	def cornerMitre(self, doKnot=False):
		from typerig.node import eNode
		glyph = eGlyph()
		wLayers = glyph._prepareLayers(pLayers)
		
		for layer in wLayers:
			selection = glyph.selectedNodes(layer, filterOn=True, extend=eNode, deep=True)
			
			for node in reversed(selection):
				if not doKnot:
					node.cornerMitre(float(self.edt_radius.text))
				else:
					node.cornerMitre(-float(self.edt_radius.text), True)


		action = 'Mitre Corner' if not doKnot else 'Overlap Corner'
		glyph.update()
		glyph.updateObject(glyph.fl, '%s @ %s.' %(action, '; '.join(wLayers)))

	def cornerTrap(self):
		from typerig.node import eNode
		glyph = eGlyph()
		wLayers = glyph._prepareLayers(pLayers)
		parameters = tuple([float(value.strip()) for value in self.edt_trap.text.split(',')])
		
		for layer in wLayers:
			selection = glyph.selectedNodes(layer, filterOn=True, extend=eNode, deep=True)
			
			for node in reversed(selection):
				node.cornerTrapInc(*parameters)

		glyph.update()
		glyph.updateObject(glyph.fl, '%s @ %s.' %('Trap Corner', '; '.join(wLayers)))

	def cornerRebuild(self):
		from typerig.node import eNode
		glyph = eGlyph()
		wLayers = glyph._prepareLayers(pLayers)
		
		for layer in wLayers:
			selection = glyph.selectedNodes(layer, filterOn=True, extend=eNode, deep=True)
			
			if len(selection) > 1:
				node_first = selection[0]
				node_last = selection[-1]
				
				line_in = node_first.getPrevLine() if node_first.getPrevOn(False) not in selection else node_first.getNextLine()
				line_out = node_last.getNextLine() if node_last.getNextOn(False) not in selection else node_last.getPrevLine()

				crossing = line_in & line_out

				node_first.smartReloc(*crossing)
				node_first.parent.removeNodesBetween(node_first.fl, node_last.getNextOn())

		glyph.update()
		glyph.updateObject(glyph.fl, 'Rebuild corner: %s nodes reduced; At layers: %s' %(len(selection), '; '.join(wLayers)))


class alignNodes(QtGui.QGridLayout):
	# - Basic Node operations
	def __init__(self):
		super(alignNodes, self).__init__()
		
		# - Init
		self.copyLine = {}

		# - Buttons
		self.btn_left = QtGui.QPushButton('Left')
		self.btn_right = QtGui.QPushButton('Right')
		self.btn_top = QtGui.QPushButton('Top')
		self.btn_bottom = QtGui.QPushButton('Bottom')
		self.btn_bboxCenterX = QtGui.QPushButton('Outline Center X')
		self.btn_bboxCenterY = QtGui.QPushButton('Outline Center Y')
		self.btn_peerCenterX = QtGui.QPushButton('Neighbors Center X')
		self.btn_peerCenterY = QtGui.QPushButton('Neighbors Center Y')
		self.btn_toAscender = QtGui.QPushButton('Asc.')
		self.btn_toCapsHeight = QtGui.QPushButton('Caps')
		self.btn_toDescender = QtGui.QPushButton('Desc.')
		self.btn_toXHeight = QtGui.QPushButton('X Hgt.')
		self.btn_toBaseline = QtGui.QPushButton('Base')
		self.btn_toYpos = QtGui.QPushButton('Y Pos')
		self.btn_toMpos = QtGui.QPushButton('Measure')
		self.btn_solveY = QtGui.QPushButton('Lineup Min/Max Y')
		self.btn_solveX = QtGui.QPushButton('Lineup Min/Max X')
		self.btn_copy = QtGui.QPushButton('Copy Slope')
		self.btn_italic = QtGui.QPushButton('Italic')
		self.btn_pasteMinY = QtGui.QPushButton('Min Y')
		self.btn_pasteMaxY = QtGui.QPushButton('Max Y')
		self.btn_pasteFMinY = QtGui.QPushButton('Flip Min')
		self.btn_pasteFMaxY = QtGui.QPushButton('Flip Max')

		self.btn_copy.setCheckable(True)
		self.btn_copy.setChecked(False)

		self.btn_italic.setCheckable(True)
		self.btn_italic.setChecked(False)

		self.btn_solveY.setToolTip('Channel Process selected nodes according to Y values')
		self.btn_solveX.setToolTip('Channel Process selected nodes according to X values')
		self.btn_copy.setToolTip('Copy slope between lowest and highest of selected nodes.')
		self.btn_italic.setToolTip('Use Italic Angle as slope.')
		self.btn_pasteMinY.setToolTip('Apply slope to selected nodes.\nReference at MIN Y value.')
		self.btn_pasteMaxY.setToolTip('Apply slope to selected nodes.\nReference at MAX Y value.')
		self.btn_pasteFMinY.setToolTip('Apply X flipped slope to selected nodes.\nReference at MIN Y value.')
		self.btn_pasteFMaxY.setToolTip('Apply X flipped slope to selected nodes.\nReference at MAX Y value.')
		self.btn_toAscender.setToolTip('Send selected nodes to Ascender height.')
		self.btn_toCapsHeight.setToolTip('Send selected nodes to Caps Height.')
		self.btn_toDescender.setToolTip('Send selected nodes to Descender height.')
		self.btn_toXHeight.setToolTip('Send selected nodes to X Height.')
		self.btn_toBaseline.setToolTip('Send selected nodes to Baseline.')
		self.btn_toYpos.setToolTip('Send selected nodes to Y coordinate.')
		self.btn_toMpos.setToolTip('Send selected nodes to Measurment Line.\nSHIFT + Click switch intercept.')

		self.btn_alignLayer_V = QtGui.QPushButton('Vertical')
		self.btn_alignLayer_H = QtGui.QPushButton('Horizontal')
		

		# - Combo boxes
		self.cmb_select_V = QtGui.QComboBox()
		self.cmb_select_H = QtGui.QComboBox()
		self.cmb_select_V.addItems(['BBox width', 'Adv. width'])
		self.cmb_select_H.addItems(['BBox height', 'X-Height', 'Caps Height', 'Ascender', 'Descender', 'Adv. height'])

		# - Spin Boxes
		self.edt_toYpos = QtGui.QSpinBox()
		self.edt_toYpos.setToolTip('Destination Y Coordinate')
		self.edt_toYpos.setMaximum(1500)
		self.edt_toYpos.setMinimum(-1500)

		self.spb_prc_V =  QtGui.QSpinBox()
		self.spb_prc_V.setMaximum(100)
		self.spb_prc_V.setSuffix('%')
		self.spb_prc_V.setMinimumWidth(40)

		self.spb_prc_H =  QtGui.QSpinBox()
		self.spb_prc_H.setMaximum(100)
		self.spb_prc_H.setSuffix('%')
		self.spb_prc_H.setMinimumWidth(40)

		self.spb_unit_V =  QtGui.QSpinBox()
		self.spb_unit_V.setMaximum(100)
		self.spb_unit_V.setMinimum(-100)
		self.spb_unit_V.setSuffix(' U')
		self.spb_unit_V.setMinimumWidth(40)

		self.spb_unit_H =  QtGui.QSpinBox()
		self.spb_unit_H.setMaximum(100)
		self.spb_unit_H.setMinimum(-100)
		self.spb_unit_H.setSuffix(' U')
		self.spb_unit_H.setMinimumWidth(40)

		# - Properties
		self.btn_left.setMinimumWidth(40)
		self.btn_right.setMinimumWidth(40)
		self.btn_top.setMinimumWidth(40)
		self.btn_bottom.setMinimumWidth(40)
		self.btn_pasteFMinY.setMinimumWidth(40)
		self.btn_pasteFMaxY.setMinimumWidth(40)
		self.btn_pasteMinY.setMinimumWidth(40)
		self.btn_pasteMaxY.setMinimumWidth(40)
		self.btn_toAscender.setMinimumWidth(40)
		self.btn_toCapsHeight.setMinimumWidth(40)
		self.btn_toDescender.setMinimumWidth(40)
		self.btn_toXHeight.setMinimumWidth(40)
		self.btn_toYpos.setMinimumWidth(40)
		self.edt_toYpos.setMinimumWidth(20)
				
		self.btn_copy.clicked.connect(self.copySlope)
		self.btn_left.clicked.connect(lambda: self.alignNodes('L'))
		self.btn_right.clicked.connect(lambda: self.alignNodes('R'))
		self.btn_top.clicked.connect(lambda: self.alignNodes('T'))
		self.btn_bottom.clicked.connect(lambda: self.alignNodes('B'))
		self.btn_solveY.clicked.connect(lambda: self.alignNodes('Y'))
		self.btn_solveX.clicked.connect(lambda: self.alignNodes('X'))
		self.btn_pasteMinY.clicked.connect(lambda: self.pasteSlope('MinY'))
		self.btn_pasteMaxY.clicked.connect(lambda: self.pasteSlope('MaxY'))
		self.btn_pasteFMinY.clicked.connect(lambda: self.pasteSlope('FLMinY'))
		self.btn_pasteFMaxY.clicked.connect(lambda: self.pasteSlope('FLMaxY'))
		self.btn_bboxCenterX.clicked.connect(lambda: self.alignNodes('BBoxCenterX'))
		self.btn_bboxCenterY.clicked.connect(lambda: self.alignNodes('BBoxCenterY'))
		self.btn_peerCenterX.clicked.connect(lambda: self.alignNodes('peerCenterX'))
		self.btn_peerCenterY.clicked.connect(lambda: self.alignNodes('peerCenterY'))
		self.btn_toAscender.clicked.connect(lambda: self.alignNodes('FontMetrics_0'))
		self.btn_toCapsHeight.clicked.connect(lambda: self.alignNodes('FontMetrics_1'))
		self.btn_toDescender.clicked.connect(lambda: self.alignNodes('FontMetrics_2'))
		self.btn_toXHeight.clicked.connect(lambda: self.alignNodes('FontMetrics_3'))
		self.btn_toBaseline.clicked.connect(lambda: self.alignNodes('FontMetrics_4'))
		self.btn_toYpos.clicked.connect(lambda: self.alignNodes('FontMetrics_5'))
		self.btn_toMpos.clicked.connect(lambda: self.alignNodes('FontMetrics_6'))
		self.btn_alignLayer_V.clicked.connect(lambda: self.alignNodes('Layer_V'))
		self.btn_alignLayer_H.clicked.connect(lambda: self.alignNodes('Layer_H'))

		# - Check box
		self.chk_slope = QtGui.QPushButton('Intercept')
		self.chk_slope.setCheckable(True)
		self.chk_slope.setToolTip('Find intersections of selected font metric\nwith slopes on which selected nodes resign.')
				
		# - Build Layout
		self.addWidget(self.btn_left, 			0,0)
		self.addWidget(self.btn_right, 			0,1)
		self.addWidget(self.btn_top, 			0,2)
		self.addWidget(self.btn_bottom,	 		0,3)
		self.addWidget(self.btn_bboxCenterX,	1,0,1,2)
		self.addWidget(self.btn_bboxCenterY,	1,2,1,2)
		self.addWidget(self.btn_peerCenterX,	2,0,1,2)
		self.addWidget(self.btn_peerCenterY,	2,2,1,2)
		self.addWidget(QtGui.QLabel('Align to Font & Glyph metrics'), 3,0,1,2)
		self.addWidget(self.btn_toAscender,		4,0,1,1)
		self.addWidget(self.btn_toCapsHeight,	4,1,1,1)
		self.addWidget(self.btn_toDescender,	4,2,1,1)
		self.addWidget(self.btn_toXHeight,		4,3,1,1)
		self.addWidget(self.btn_toBaseline,		5,0,1,1)
		self.addWidget(self.edt_toYpos,			5,1,1,1)
		self.addWidget(self.btn_toYpos,			5,2,1,1)
		self.addWidget(self.btn_toMpos, 		5,3,1,1)
		self.addWidget(self.chk_slope, 			6,0,1,4)

		#self.addWidget(QtGui.QLabel('Align to Glyph Layer'), 	6, 0, 1, 4)
		self.addWidget(self.cmb_select_V, 						7, 0)
		self.addWidget(self.spb_prc_V, 							7, 1)
		self.addWidget(self.spb_unit_V, 						7, 2)
		self.addWidget(self.btn_alignLayer_V, 					7, 3)
		self.addWidget(self.cmb_select_H, 						8, 0)
		self.addWidget(self.spb_prc_H, 							8, 1)
		self.addWidget(self.spb_unit_H, 						8, 2)
		self.addWidget(self.btn_alignLayer_H, 					8, 3)
		self.addWidget(QtGui.QLabel('Channel processing and slopes'), 9,0,1,4)
		self.addWidget(self.btn_solveY, 		10,0,1,2)
		self.addWidget(self.btn_solveX, 		10,2,1,2)
		self.addWidget(self.btn_copy,			11,0,1,3)
		self.addWidget(self.btn_italic,			11,3,1,1)
		self.addWidget(self.btn_pasteMinY,		12,0,1,1)
		self.addWidget(self.btn_pasteMaxY,		12,1,1,1)
		self.addWidget(self.btn_pasteFMinY,		12,2,1,1)
		self.addWidget(self.btn_pasteFMaxY,		12,3,1,1)

	def copySlope(self):
		from typerig.brain import Line

		if self.btn_copy.isChecked():
			self.btn_copy.setText('Reset Slope')
			self.btn_italic.setChecked(False)

			glyph = eGlyph()
			wLayers = glyph._prepareLayers(pLayers)
			
			for layer in wLayers:
				selection = glyph.selectedNodes(layer)
				self.copyLine[layer] = Line(selection[0], selection[-1])
				#print self.copyLine[layer].getAngle(), self.copyLine[layer].getSlope()
		else:
			self.btn_copy.setText('Copy Slope')
			self.btn_italic.setChecked(False)

	def pasteSlope(self, mode):
		from typerig.brain import Line
		
		if self.btn_copy.isChecked() or self.btn_italic.isChecked():
			glyph = eGlyph()
			wLayers = glyph._prepareLayers(pLayers)
			italicAngle = glyph.package.italicAngle_value
			control = (True, False)
			
			for layer in wLayers:
				selection = [eNode(node) for node in glyph.selectedNodes(layer)]
				srcLine = self.copyLine[layer] if not self.btn_italic.isChecked() else None

				if mode == 'MinY':
					dstLine = Line(min(selection, key=lambda item: item.y).fl, max(selection, key=lambda item: item.y).fl)
					
					if not self.btn_italic.isChecked():
						dstLine.slope = srcLine.getSlope()
					else:
						dstLine.setAngle(-1*italicAngle)

				elif mode == 'MaxY':
					dstLine = Line(max(selection, key=lambda item: item.y).fl, min(selection, key=lambda item: item.y).fl)
					
					if not self.btn_italic.isChecked():
						dstLine.slope = srcLine.getSlope()
					else:
						dstLine.setAngle(-1*italicAngle)

				elif mode == 'FLMinY':
					dstLine = Line(min(selection, key=lambda item: item.y).fl, max(selection, key=lambda item: item.y).fl)
					
					if not self.btn_italic.isChecked():
						dstLine.slope = -1.*srcLine.getSlope()
					else:
						dstLine.setAngle(italicAngle)

				elif mode == 'FLMaxY':
					dstLine = Line(max(selection, key=lambda item: item.y).fl, min(selection, key=lambda item: item.y).fl)
					
					if not self.btn_italic.isChecked():
						dstLine.slope = -1.*srcLine.getSlope()
					else:
						dstLine.setAngle(italicAngle)
				
				for node in selection:
					node.alignTo(dstLine, control)

			glyph.updateObject(glyph.fl, 'Paste Slope @ %s.' %'; '.join(wLayers))
			glyph.update()


	def alignNodes(self, mode):
		process_glyphs = getProcessGlyphs(pMode)
		modifiers = QtGui.QApplication.keyboardModifiers()

		for glyph in process_glyphs:
			wLayers = glyph._prepareLayers(pLayers)
			
			for layer in wLayers:
				selection = glyph.selectedNodes(layer, extend=eNode, deep=True)

				if mode == 'L':
					target = min(selection, key=lambda item: item.x)
					control = (True, False)

				elif mode == 'R':
					target = max(selection, key=lambda item: item.x)
					control = (True, False)
				
				elif mode == 'T':
					target = max(selection, key=lambda item: item.y)
					control = (False, True)
				
				elif mode == 'B':
					target = min(selection, key=lambda item: item.y)
					control = (False, True)
				
				elif mode == 'Y':
					target = Line(min(selection, key=lambda item: item.y).fl, max(selection, key=lambda item: item.y).fl)
					control = (True, False)

				elif mode == 'X':
					target = Line(min(selection, key=lambda item: item.x).fl, max(selection, key=lambda item: item.x).fl)
					control = (False, True)

				elif mode == 'BBoxCenterX':
					newX = glyph.layer(layer).boundingBox.x() + glyph.layer(layer).boundingBox.width()/2
					newY = 0.
					target = fl6.flNode(newX, newY)
					control = (True, False)

				elif mode == 'BBoxCenterY':
					newX = 0.
					newY = glyph.layer(layer).boundingBox.y() + glyph.layer(layer).boundingBox.height()/2
					target = fl6.flNode(newX, newY)
					control = (False, True)

				elif 'FontMetrics' in mode:
					layerMetrics = glyph.fontMetricsInfo(layer)
					italicAngle = glyph.package.italicAngle_value
					
					newX = 0.
					toMaxY = True

					if '0' in mode:
						newY = layerMetrics.ascender
						toMaxY = True if modifiers == QtCore.Qt.ShiftModifier else False 
					elif '1' in mode:
						newY = layerMetrics.capsHeight
						toMaxY = True if modifiers == QtCore.Qt.ShiftModifier else False 
					elif '2' in mode:
						newY = layerMetrics.descender
						toMaxY = False if modifiers == QtCore.Qt.ShiftModifier else True 
					elif '3' in mode:
						newY = layerMetrics.xHeight
						toMaxY = True if modifiers == QtCore.Qt.ShiftModifier else False 
					elif '4' in mode:
						newY = 0
						toMaxY = False if modifiers == QtCore.Qt.ShiftModifier else True 
					elif '5' in mode:
						newY = self.edt_toYpos.value
						toMaxY = False if modifiers == QtCore.Qt.ShiftModifier else True 
					elif '6' in mode:
						newY = glyph.mLine()
						toMaxY = newY >= 0 
						if modifiers == QtCore.Qt.ShiftModifier: toMaxY = not toMaxY

				elif mode == 'Layer_V':
					if 'BBox' in self.cmb_select_V.currentText:
						width = glyph.layer(layer).boundingBox.width()
						origin = glyph.layer(layer).boundingBox.x()
				
					elif 'Adv' in self.cmb_select_V.currentText:
						width = glyph.getAdvance(layer)
						origin = 0.

					target = fl6.flNode(float(width)*self.spb_prc_V.value/100 + origin + self.spb_unit_V.value, 0)
					control = (True, False)

				elif mode == 'Layer_H':
					metrics = pFontMetrics(glyph.package)

					if 'BBox' in self.cmb_select_H.currentText:
						height = glyph.layer(layer).boundingBox.height()
						origin = glyph.layer(layer).boundingBox.y()
					
					elif 'Adv' in self.cmb_select_H.currentText:
						height = glyph.layer(layer).advanceHeight
						origin = 0.

					elif 'X-H' in self.cmb_select_H.currentText:
						height = metrics.getXHeight(layer)
						origin = 0.

					elif 'Caps' in self.cmb_select_H.currentText:
						height = metrics.getCapsHeight(layer)
						origin = 0.

					elif 'Ascender' in self.cmb_select_H.currentText:
						height = metrics.getAscender(layer)
						origin = 0.			

					elif 'Descender' in self.cmb_select_H.currentText:
						height = metrics.getDescender(layer)
						origin = 0.		

					target = fl6.flNode(0, float(height)*self.spb_prc_H.value/100 + origin + self.spb_unit_H.value)
					control = (False, True)

				for node in selection:
					if 'FontMetrics' in mode:
						if italicAngle != 0 and not self.chk_slope.isChecked():
							tempTarget = Coord(node.fl)
							tempTarget.setAngle(italicAngle)

							target = fl6.flNode(tempTarget.getWidth(newY), newY)
							control = (True, True)
						
						elif self.chk_slope.isChecked():
							pairUp = node.getMaxY().position
							pairDown = node.getMinY().position
							pairPos = pairUp if toMaxY else pairDown
							newLine = Line(node.fl.position, pairPos)
							newX = newLine.solveX(newY)

							target = fl6.flNode(newX, newY)
							control = (True, True)

						else:
							target = fl6.flNode(newX, newY)
							control = (False, True)

					if mode == 'peerCenterX':
						newX = node.x + (node.getPrevOn().x + node.getNextOn().x - 2*node.x)/2.
						newY = node.y
						target = fl6.flNode(newX, newY)
						control = (True, False)

					elif mode == 'peerCenterY':
						newX = node.x
						newY = node.y + (node.getPrevOn().y + node.getNextOn().y - 2*node.y)/2.
						target = fl6.flNode(newX, newY)
						control = (False, True)

					# - Execute Align ----------
					node.alignTo(target, control)

			glyph.updateObject(glyph.fl, 'Align Nodes @ %s.' %'; '.join(wLayers))
			glyph.update()


class breakContour(QtGui.QGridLayout):
	# - Split/Break contour 
	def __init__(self):
		super(breakContour, self).__init__()
			 
		# -- Split button
		self.btn_splitContour = QtGui.QPushButton('&Break')
		self.btn_splitContourClose = QtGui.QPushButton('&Break && Close')
		
		self.btn_splitContour.clicked.connect(self.splitContour)
		self.btn_splitContourClose.clicked.connect(self.splitContourClose)
		
		self.btn_splitContour.setMinimumWidth(80)
		self.btn_splitContourClose.setMinimumWidth(80)

		self.btn_splitContour.setToolTip('Break contour at selected Node(s).')
		self.btn_splitContourClose.setToolTip('Break contour and close open contours!\nUseful for cutting stems and etc.')

		# -- Extrapolate value
		self.edt_expand = QtGui.QLineEdit('0.0')
		#self.edt_expand.setMinimumWidth(30)

		self.edt_expand.setToolTip('Extrapolate endings.')
								
		# -- Build: Split/Break contour
		self.addWidget(self.btn_splitContour, 0, 0)
		self.addWidget(QtGui.QLabel('E:'), 0, 1)
		self.addWidget(self.edt_expand, 0, 2)
		self.addWidget(self.btn_splitContourClose, 0, 3)
				
	def splitContour(self):
		glyph = eGlyph()
		glyph.splitContour(layers=pLayers, expand=float(self.edt_expand.text), close=False)
		glyph.updateObject(glyph.fl, 'Break Contour @ %s.' %'; '.join(glyph._prepareLayers(pLayers)))
		glyph.update()

	def splitContourClose(self):
		glyph = eGlyph()
		glyph.splitContour(layers=pLayers, expand=float(self.edt_expand.text), close=True)
		glyph.updateObject(glyph.fl, 'Break Contour & Close @ %s.' %'; '.join(glyph._prepareLayers(pLayers)))
		glyph.update()        

class basicContour(QtGui.QGridLayout):
	# - Split/Break contour 
	def __init__(self):
		super(basicContour, self).__init__()
		self.btn_BL = QtGui.QPushButton('B L')
		self.btn_TL = QtGui.QPushButton('T L')
		self.btn_BR = QtGui.QPushButton('B R')
		self.btn_TR = QtGui.QPushButton('T R')
		self.btn_close= QtGui.QPushButton('C&lose')
		self.btn_CW = QtGui.QPushButton('CW')
		self.btn_CCW = QtGui.QPushButton('CCW')

		self.btn_BL.setMinimumWidth(40)
		self.btn_TL.setMinimumWidth(40)
		self.btn_BR.setMinimumWidth(40)
		self.btn_TR.setMinimumWidth(40)
		self.btn_CW.setMinimumWidth(40)
		self.btn_CCW.setMinimumWidth(40)

		self.btn_close.setToolTip('Close selected contour')
		self.btn_BL.setToolTip('Set start point:\nBottom Left Node') 
		self.btn_TL.setToolTip('Set start point:\nTop Left Node') 
		self.btn_BR.setToolTip('Set start point:\nBottom Right Node') 
		self.btn_TR.setToolTip('Set start point:\nTop Right Node') 
		self.btn_CW.setToolTip('Set direction:\nClockwise (TT)') 
		self.btn_CCW.setToolTip('Set direction::\nCounterclockwise (PS)') 
		
		self.btn_BL.clicked.connect(lambda : self.setStart((0,0)))
		self.btn_TL.clicked.connect(lambda : self.setStart((0,1)))
		self.btn_BR.clicked.connect(lambda : self.setStart((1,0)))
		self.btn_TR.clicked.connect(lambda : self.setStart((1,1)))
		self.btn_CW.clicked.connect(lambda : self.setDirection(False))
		self.btn_CCW.clicked.connect(lambda : self.setDirection(True))
		self.btn_close.clicked.connect(self.closeContour)

		self.addWidget(self.btn_BL, 0, 0, 1, 1)
		self.addWidget(self.btn_TL, 0, 1, 1, 1)
		self.addWidget(self.btn_BR, 0, 2, 1, 1)
		self.addWidget(self.btn_TR, 0, 3, 1, 1)
		self.addWidget(self.btn_close, 1, 0, 1, 2)
		self.addWidget(self.btn_CW, 1, 2, 1, 1)
		self.addWidget(self.btn_CCW, 1, 3, 1, 1)

	def closeContour(self):
		glyph = eGlyph()
		wLayers = glyph._prepareLayers(pLayers)
		selection = glyph.selectedAtContours()

		for layerName in wLayers:
			contours = glyph.contours(layerName)

			for cID, nID in reversed(selection):
				if not contours[cID].closed: contours[cID].closed = True

		glyph.updateObject(glyph.fl, 'Close Contour @ %s.' %'; '.join(wLayers))
		glyph.update()

	def setStart(self, control=(0,0)):
		process_glyphs = getProcessGlyphs(pMode)

		for glyph in process_glyphs:
			wLayers = glyph._prepareLayers(pLayers)

			if control == (0,0):
				criteria = lambda node : (node.x, node.y)
			elif control == (0,1):
				criteria = lambda node : (-node.y, node.x)
			elif control == (1,0):
				criteria = lambda node : (-node.x, node.y)
			elif control == (1,1):
				criteria = lambda node : (-node.y, -node.x)
			
			for layerName in wLayers:
				contours = glyph.contours(layerName)

				for contour in contours:
					onNodes = [node for node in contour.nodes() if node.isOn]
					newFirstNode = sorted(onNodes, key=criteria)[0]
					contour.setStartPoint(newFirstNode.index)

			glyph.update()
			glyph.updateObject(glyph.fl, 'Glyph: %s;\tAction: Set Start Points @ %s.' %(glyph.name, '; '.join(wLayers)))

	def setDirection(self, ccw=True):
		process_glyphs = getProcessGlyphs(pMode)

		for glyph in process_glyphs:
			selection = glyph.selectedAtContours()

			wLayers = glyph._prepareLayers(pLayers)

			for layerName in wLayers:
				all_contours = glyph.contours(layerName)

				if len(selection):
					process_contours = [pContour(all_contours[item[0]]) for item in selection]
				else:
					process_contours = [pContour(contour) for contour in all_contours]

				for contour in process_contours:
					if ccw:
						contour.setCCW()
					else:
						contour.setCW()

			glyph.update()
			glyph.updateObject(glyph.fl, 'Glyph: %s;\tAction: Set contour direction @ %s.' %(glyph.name, '; '.join(wLayers)))

class alignContours(QtGui.QGridLayout):
	# - Align Contours
	def __init__(self):
		super(alignContours, self).__init__()
		from collections import OrderedDict
		
		# - Init
		self.align_x = OrderedDict([('Left','L'), ('Right','R'), ('Center','C'), ('Keep','K')])
		self.align_y = OrderedDict([('Top','T'), ('Bottom','B'), ('Center','E'), ('Keep','X')])
		self.align_mode = OrderedDict([('Layer','CL'), ('Contour to Contour','CC'), ('Contour to Contour (REV)','RC')])
		
		# !!! To be implemented
		#self.align_mode = OrderedDict([('Layer','CL'), ('Contour to Contour','CC'), ('Contour to Contour (REV)','RC'), ('Contour to Node','CN'),('Node to Node','NN')])

		# - Widgets
		self.cmb_align_x = QtGui.QComboBox()
		self.cmb_align_y = QtGui.QComboBox()
		self.cmb_align_mode = QtGui.QComboBox()
		self.cmb_align_x.addItems(self.align_x.keys())
		self.cmb_align_y.addItems(self.align_y.keys())
		self.cmb_align_mode.addItems(self.align_mode.keys())

		self.cmb_align_x.setToolTip('Horizontal Alignment')
		self.cmb_align_y.setToolTip('Vertical Alignment')
		self.cmb_align_mode.setToolTip('Alignment Mode')

		self.btn_align = QtGui.QPushButton('Align')
		self.btn_align.clicked.connect(self.alignContours)

		self.addWidget(self.cmb_align_mode, 	0, 0, 1, 2)
		self.addWidget(self.cmb_align_x, 		0, 2, 1, 1)
		self.addWidget(self.cmb_align_y, 		0, 3, 1, 1)
		self.addWidget(self.btn_align, 			1, 0, 1, 4)

	def alignContours(self):
		# - Helpers
		def getContourBonds(work_contours):
			tmp_bounds = [contour.bounds() for contour in work_contours]
			cont_min_X, cont_min_Y, cont_max_X, cont_max_Y = map(set, zip(*tmp_bounds))
			return (min(cont_min_X), min(cont_min_Y), max(cont_max_X), max(cont_max_Y))

		def getAlignDict(bounds_tuple):
			align_dict = {	'L': bounds_tuple[0], 
							'R': bounds_tuple[2],
							'C': bounds_tuple[2]/2,
							'B': bounds_tuple[1], 
							'T': bounds_tuple[3], 
							'E': bounds_tuple[3]/2
						}

			return align_dict

		# - Init
		user_mode =  self.align_mode[self.cmb_align_mode.currentText]
		user_x = self.align_x[self.cmb_align_x.currentText]
		user_y = self.align_y[self.cmb_align_y.currentText]
		keep_x, keep_y = True, True	

		if user_x == 'K': keep_x = False; user_x = 'L'
		if user_y == 'X': keep_y = False; user_y = 'B'		
		
		process_glyphs = getProcessGlyphs(pMode)

		# - Process
		for glyph in process_glyphs:
			selection = glyph.selectedAtContours()
			wLayers = glyph._prepareLayers(pLayers)

			for layerName in wLayers:
				glyph_contours = glyph.contours(layerName, extend=eContour)
				work_contours = [glyph_contours[index] for index in list(set([item[0] for item in selection]))]
				
				if user_mode == 'CL': # Align all contours in given Layer
					layer_bounds = glyph.getBounds(layerName)
					cont_bounds = (layer_bounds.x(), layer_bounds.y(), layer_bounds.x() + layer_bounds.width(), layer_bounds.y() + layer_bounds.height())
					align_type = getAlignDict(cont_bounds)
					target = Coord(align_type[user_x], align_type[user_y])

					for contour in glyph_contours:
						contour.alignTo(target, user_x + user_y, (keep_x, keep_y))					

				elif user_mode =='CC': # Align contours to contours
					if 1 < len(work_contours) < 3:
						c1, c2 = work_contours
						c1.alignTo(c2, user_x + user_y, (keep_x, keep_y))

					elif len(work_contours) > 2:
						cont_bounds = getContourBonds(work_contours)
						align_type = getAlignDict(cont_bounds)
						target = Coord(align_type[user_x], align_type[user_y])

						for contour in work_contours:
							contour.alignTo(target, user_x + user_y, (keep_x, keep_y))
					
				elif user_mode == 'RC': # Align contours to contours in reverse order
					if 1 < len(work_contours) < 3:
						c1, c2 = work_contours
						c2.alignTo(c1, user_x + user_y, (keep_x, keep_y))

					elif len(work_contours) > 2:
						cont_bounds = getContourBonds(work_contours)
						align_type = getAlignDict(cont_bounds)
						target = Coord(align_type[user_x], align_type[user_y])

						for contour in reversed(work_contours):
							contour.alignTo(target, user_x + user_y, (keep_x, keep_y))	

				# !!! To be implemented
				elif user_mode == 'CN': # Align contour to node
					pass

				elif user_mode == 'NN': # Align a node on contour to node on another
					pass

			glyph.update()
			glyph.updateObject(glyph.fl, 'Glyph: %s;\tAction: Align Contours @ %s.' %(glyph.name, '; '.join(wLayers)))


class convertHobby(QtGui.QHBoxLayout):
	# - Split/Break contour 
	def __init__(self):
		super(convertHobby, self).__init__()

		# -- Convert button
		self.btn_convertNode = QtGui.QPushButton('C&onvert')
		self.btn_convertNode.setToolTip('Convert/Un-convert selected curve node to Hobby Knot')
		self.btn_convertNode.clicked.connect(self.convertHobby)

		#self.btn_convertNode.setFixedWidth(80)

		# -- Close contour checkbox
		#self.chk_Safe = QtGui.QCheckBox('Safe')

		# -- Tension value (not implemented yet)
		#self.edt_tension = QtGui.QLineEdit('0.0')
		#self.edt_tension.setDisabled(True)    
				
		# -- Build
		self.addWidget(self.btn_convertNode)
		#self.addWidget(QtGui.QLabel('T:'), 1, 1)
		#self.addWidget(self.edt_tension, 1, 2)
		#self.addWidget(self.chk_Safe, 1, 3)

	def convertHobby(self):
		glyph = eGlyph()
		wLayers = glyph._prepareLayers(pLayers)
		selection = glyph.selected()

		for layerName in wLayers:
			pNodes = [glyph.nodes(layerName)[nID] for nID in selection]
			
			for node in pNodes:
				if not node.hobby:
					node.hobby = True
				else:
					node.hobby = False
				node.update()

		glyph.updateObject(glyph.fl, 'Convert to Hobby @ %s.' %'; '.join(wLayers))
		glyph.update()
		
		#fl6.Update(fl6.CurrentGlyph())

class advMovement(QtGui.QVBoxLayout):
	def __init__(self, aux):
		super(advMovement, self).__init__()

		# - Init
		self.aux = aux
		self.methodList = ['Move', 'Simple Move', 'Interpolated Move', 'Slanted Grid Move', 'Slope walker']
		
		# - Methods
		self.cmb_methodSelector = QtGui.QComboBox()
		self.cmb_methodSelector.addItems(self.methodList)
		self.cmb_methodSelector.setToolTip('Select movement method')
		self.chk_percent = QtGui.QCheckBox('% of BBox')
		self.chk_percent.setToolTip('Interpret new positional coordinates as if they were scaled by percent given in (X,Y)\nEquivalent to affine scaling of selected nodes in respect to the Layers BoundingBox')
		
		# - Arrow buttons
		self.btn_up = QtGui.QPushButton('Up')
		self.btn_down = QtGui.QPushButton('Down')
		self.btn_left = QtGui.QPushButton('Left')
		self.btn_right = QtGui.QPushButton('Right')
		
		self.btn_up.setMinimumWidth(80)
		self.btn_down.setMinimumWidth(80)
		self.btn_left.setMinimumWidth(80)
		self.btn_right.setMinimumWidth(80)

		self.btn_up.clicked.connect(self.onUp)
		self.btn_down.clicked.connect(self.onDown)
		self.btn_left.clicked.connect(self.onLeft)
		self.btn_right.clicked.connect(self.onRight)
		self.chk_percent.clicked.connect(self.toggleInput)
		
		self.edt_offX = QtGui.QLineEdit('1.0')
		self.edt_offY = QtGui.QLineEdit('1.0')
		self.edt_offX.setToolTip('X offset')
		self.edt_offY.setToolTip('Y offset')

		# - Layout
		self.lay_btn = QtGui.QGridLayout()

		self.lay_btn.addWidget(self.cmb_methodSelector, 0, 0, 1, 5)
		self.lay_btn.addWidget(self.chk_percent, 		0, 5, 1, 1)
		self.lay_btn.addWidget(QtGui.QLabel('X:'), 		1, 0, 1, 1)
		self.lay_btn.addWidget(self.edt_offX, 			1, 1, 1, 1)
		self.lay_btn.addWidget(self.btn_up, 			1, 2, 1, 2)
		self.lay_btn.addWidget(QtGui.QLabel('Y:'), 		1, 4, 1, 1)
		self.lay_btn.addWidget(self.edt_offY, 			1, 5, 1, 1)
		self.lay_btn.addWidget(self.btn_left, 			2, 0, 1, 2)
		self.lay_btn.addWidget(self.btn_down, 			2, 2, 1, 2)
		self.lay_btn.addWidget(self.btn_right, 			2, 4, 1, 2)

		self.addLayout(self.lay_btn)

		
	def toggleInput(self):
		if self.chk_percent.isChecked():
			self.edt_offX.setText(str(float(self.edt_offX.text)/100)) 
			self.edt_offY.setText(str(float(self.edt_offY.text)/100))
		else:
			self.edt_offX.setText(str(float(self.edt_offX.text)*100)) 
			self.edt_offY.setText(str(float(self.edt_offY.text)*100))

	def moveNodes(self, offset_x, offset_y, method, inPercent):
		# - Init
		font = pFont()
		glyph = eGlyph()
		italic_angle = font.getItalicAngle()

		process_glyphs = getProcessGlyphs(pMode)

		for glyph in process_glyphs:
			wLayers = glyph._prepareLayers(pLayers)

			for layer in wLayers:
				selectedNodes = glyph.selectedNodes(layer=layer, extend=eNode)
				
				
				# -- Scaling move - coordinates as percent of position
				def scaleOffset(node, off_x, off_y):
					return (-node.x + width*(float(node.x)/width + offset_x), -node.y + height*(float(node.y)/height + offset_y))

				width = glyph.layer(layer).boundingBox.width() # glyph.layer().advanceWidth
				height = glyph.layer(layer).boundingBox.height() # glyph.layer().advanceHeight

				# - Process
				if method == self.methodList[0]:
					for node in selectedNodes:
						if node.isOn:
							if inPercent:						
								node.smartShift(*scaleOffset(node, offset_x, offset_y))
							else:
								node.smartShift(offset_x, offset_y)

				elif method == self.methodList[1]:
					for node in selectedNodes:
						if inPercent:						
							node.shift(*scaleOffset(node, offset_x, offset_y))
						else:
							node.shift(offset_x, offset_y)

				elif method == self.methodList[2]:
					for node in selectedNodes:
						if inPercent:						
							node.interpShift(*scaleOffset(node, offset_x, offset_y))
						else:
							node.interpShift(offset_x, offset_y)

				elif method == self.methodList[3]:
					if italic_angle != 0:
						for node in selectedNodes:
							if inPercent:						
								node.slantShift(*scaleOffset(node, offset_x, offset_y))
							else:
								node.slantShift(offset_x, offset_y, italic_angle)
					else:
						for node in selectedNodes:
							if inPercent:						
								node.smartShift(*scaleOffset(node, offset_x, offset_y))
							else:
								node.smartShift(offset_x, offset_y)

				elif method == self.methodList[4]:			
					current_layer = glyph.activeLayer().name

					if len(self.aux.copyLine) and current_layer in self.aux.copyLine:
						for node in selectedNodes:
							node.slantShift(offset_x, offset_y, -90 + self.aux.copyLine[current_layer].getAngle())				
					else:
						print 'ERROR:\tNo slope information for layer found!\nNOTE:\tPlease <<Copy Slope>> first using TypeRig Node align toolbox.'

			# - Finish it
			glyph.update()
			glyph.updateObject(glyph.fl, 'Node: %s @ %s.' %(method, '; '.join(wLayers)))

	def onUp(self):
		self.moveNodes(.0, float(self.edt_offY.text), method=str(self.cmb_methodSelector.currentText), inPercent=self.chk_percent.isChecked())

	def onDown(self):
		self.moveNodes(.0, -float(self.edt_offY.text), method=str(self.cmb_methodSelector.currentText), inPercent=self.chk_percent.isChecked())
			
	def onLeft(self):
		self.moveNodes(-float(self.edt_offX.text), .0, method=str(self.cmb_methodSelector.currentText), inPercent=self.chk_percent.isChecked())
			
	def onRight(self):
		self.moveNodes(float(self.edt_offX.text), .0, method=str(self.cmb_methodSelector.currentText), inPercent=self.chk_percent.isChecked())

# - Tabs -------------------------------
class tool_tab(QtGui.QWidget):
	def __init__(self):
		super(tool_tab, self).__init__()

		# - Init
		layoutV = QtGui.QVBoxLayout()
		self.KeyboardOverride = False
		
		# - Build		
		layoutV.addWidget(QtGui.QLabel('Basic Operations'))
		layoutV.addLayout(basicOps())

		layoutV.addWidget(QtGui.QLabel('Align nodes'))
		self.alignNodes = alignNodes()
		layoutV.addLayout(self.alignNodes)

		#layoutV.addWidget(QtGui.QLabel('Break/Knot Contour'))
		#layoutV.addLayout(breakContour())

		layoutV.addWidget(QtGui.QLabel('Basic Contour Operations'))
		layoutV.addLayout(basicContour())

		layoutV.addWidget(QtGui.QLabel('Align Contours'))
		layoutV.addLayout(alignContours())

		#layoutV.addWidget(QtGui.QLabel('Convert to Hobby'))
		#layoutV.addLayout(convertHobby())    

		layoutV.addWidget(QtGui.QLabel('Movement'))
		self.advMovement = advMovement(self.alignNodes)
		layoutV.addLayout(self.advMovement)  

		# - Capture Kyaboard
		self.btn_capture = QtGui.QPushButton('Capture Keyboard')
		self.btn_capture.setCheckable(True)
		self.btn_capture.setToolTip('Click here to capture keyboard arrows input.\nNote:\n+10 SHIFT\n+100 CTRL\n Exit ESC')
		self.btn_capture.clicked.connect(self.captureKeyaboard)

		layoutV.addWidget(self.btn_capture)

		# - Build ---------------------------
		layoutV.addStretch()
		self.setLayout(layoutV)


	def keyPressEvent(self, eventQKeyEvent):

		#self.setFocus()
		key = eventQKeyEvent.key()
		modifier = int(eventQKeyEvent.modifiers())
		addon = .0
		
		if key == QtCore.Qt.Key_Escape:
			#self.close()
			self.releaseKeyboard()
			self.KeyboardOverride = False
			self.btn_capture.setChecked(False)
			self.btn_capture.setText('Capture Keyboard')
			
		# - Keyboard listener
		# -- Modifier addon
		if modifier == QtCore.Qt.ShiftModifier:
			addon = 10.0 if not self.advMovement.chk_percent.isChecked() else 0.1
		elif modifier == QtCore.Qt.ControlModifier:
			addon = 100.0 if not self.advMovement.chk_percent.isChecked() else 1.0
		else:
			addon = .0
		
		# -- Standard movement keys	
		if key == QtCore.Qt.Key_Up:
			shiftXY = (.0, float(self.advMovement.edt_offY.text) + addon)
		
		elif key == QtCore.Qt.Key_Down:
			shiftXY = (.0, -float(self.advMovement.edt_offY.text) - addon)
		
		elif key == QtCore.Qt.Key_Left:
			shiftXY = (-float(self.advMovement.edt_offX.text) - addon, .0)
		
		elif key == QtCore.Qt.Key_Right:
			shiftXY = (float(self.advMovement.edt_offX.text) + addon, .0)
		
		else:
			shiftXY = (.0,.0)
		
		# - Move
		self.advMovement.moveNodes(*shiftXY, method=str(self.advMovement.cmb_methodSelector.currentText),  inPercent=self.advMovement.chk_percent.isChecked())

	def captureKeyaboard(self):
		if not self.KeyboardOverride:
			self.KeyboardOverride = True
			self.btn_capture.setChecked(True)
			self.btn_capture.setText('Keyboard Capture Active. [ESC] Exit')
			self.grabKeyboard()
		else:
			self.KeyboardOverride = False
			self.btn_capture.setChecked(False)
			self.btn_capture.setText('Capture Keyboard')
			self.releaseKeyboard()
	

# - Test ----------------------
if __name__ == '__main__':
	test = tool_tab()
	test.setWindowTitle('%s %s' %(app_name, app_version))
	test.setGeometry(300, 300, 200, 400)
	test.setWindowFlags(QtCore.Qt.WindowStaysOnTopHint) # Always on top!!
	
	test.show()