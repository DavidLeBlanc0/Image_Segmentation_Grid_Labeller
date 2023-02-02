from tkinter import *
import tkinter.font as font
from tkinter import filedialog

import numpy as np
from PIL import Image, ImageTk
import os
import sys
import pickle

from PMEL_Datum import PMEL_Datum

# TODO: Move these to a shared config file
NES_XRES = 240
NES_YRES = 256
SCALE_FACTOR = 3
GRID_SIZE = 15
GRID_X_INTERVAL = np.floor(NES_XRES/GRID_SIZE)
GRID_Y_INTERVAL = np.floor(NES_YRES/GRID_SIZE)

class PMEL:
	"""
	---------------------------------------------------------------------------
	PlatformerMan Eyes Labeller (PMEL)
	Creates a tkinter application that is capable of labelling screenshots of
	platformers as a small pseudo-gridworld.
	---------------------------------------------------------------------------
	"""
	def __init__(self, debugMode = False):

		# Class constants
		self.LABEL_NONE, \
		self.LABEL_GROUND, \
		self.LABEL_PLAYER, \
		self.LABEL_ENEMY, \
		self.LABEL_HAZARD \
			= range(0,5)

		self.FILTER_NONE, \
		self.FILTER_LABELLED, \
		self.FILTER_UNLABELLED \
			= range(0, 3)

		# Hotkeys
		self.LABEL_GROUND_HOTKEY = "1"
		self.LABEL_PLAYER_HOTKEY = "2"
		self.LABEL_ENEMY_HOTKEY = "3"
		self.LABEL_HAZARD_HOTKEY = "4"
		self.HOTKEY_NEXT 	= "<d>"
		self.HOTKEY_PREV 	= "<a>"
		self.HOTKEY_DELETE 	= "<BackSpace>"
		self.HOTKEY_CLEAR   = "<q>"

		# File structure
		self.imageDirectory = "bingus"
		self.imagePathList = []
		self.filteredIndices = [] # Indices of imagePathList that meet filter
		self.imageIndex = 0
		self.dataDirectoryName = "PMEL_Data"
		self.deleteDirectoryName = "PMEL_Deleted"

		self.selectedLabel = None
		self.filterRadio = []
		self.labelRadio = []
		self.controlButtons = []
		self.currentImage = "./nesTest2.png"
		self.currentGrid  = np.zeros(shape = (GRID_SIZE, GRID_SIZE),dtype=int)
		self.rootImgName = ""
		self.root = None # Defined in main_window()
		self.screenshotCanvas = None # Defined in create_image_frame()
		self.labelColours = ["","green", "blue", "red", "yellow"]

		self.placingLabels = True
		self.placingLabels = False

		self.debugMode = debugMode

		self.main_window()

#------------------------------------------------------------------------------
#FUNCTIONALITY
#------------------------------------------------------------------------------

	def set_directories(self, imgDir = None):
		if imgDir != None:
			self.imageDirectory = imgDir

		self.imagePathList = []
		for filePath in os.listdir(self.imageDirectory):
			wholePath = os.path.join(self.imageDirectory, filePath)
			if os.path.isfile(wholePath):
				self.imagePathList.append(wholePath)

		dirPath = os.path.join(self.imageDirectory, self.dataDirectoryName)
		delDirPath = os.path.join(self.imageDirectory, 
			self.deleteDirectoryName)

		if not os.path.exists(dirPath):
			os.mkdir(dirPath)
		if not os.path.exists(delDirPath):
			os.mkdir(delDirPath)


		self.load_data()

	def filter_images(self, event = None):

		#TODO: make this less abominably slow
		self.set_directories() # This is abominably slow. 
		self.filteredIndices = []
		

		for idx in range(len(self.imagePathList)):
			if self.filterVal == self.FILTER_LABELLED:
				if os.path_exists(self.get_data_path_for(idx)):
					self.filteredIndices.append(idx)
			elif self.filterVal == self.FILTER_UNLABELLED:
				if not os.path_exists(self.get_data_path_for(idx)):
					self.filteredIndices.append(idx)
			else: # No Filter
					self.filteredIndices.append(idx)

		self.imagePathList = [self.imagePathList[i] for i in self.filteredIndices]

	
	def get_current_data_path(self):
		dir = os.path.join(self.imageDirectory, self.dataDirectoryName)

		return self.get_data_path_for(self.imageIndex)

	def get_data_path_for(self, idx):
		dataDir = os.path.join(self.imageDirectory, self.dataDirectoryName)

		return os.path.join(dataDir,
			os.path.splitext(os.path.basename(self.imagePathList[idx]))[0]) + ".pkl"

	def delete_current(self, event = None):
		imgPath = self.imagePathList[self.imageIndex]
		dataPath = self.get_current_data_path()
		if os.path.isfile(imgPath):
			#os.remove(imgPath)
			binPath = os.path.join(self.imageDirectory, 
				self.deleteDirectoryName,
				os.path.basename(imgPath))
			os.rename(imgPath, binPath)
		if os.path.isfile(dataPath):
			os.remove(dataPath)
		self.imagePathList.pop(self.imageIndex)
		self.update_canvas_image()

	def go_previous(self, save = True, event = None):
		if save:
			self.save_data()

		self.imageIndex = max(0, self.imageIndex - 1)
		self.load_data()

	def go_next(self, save = True, event = None):
		if save:
			self.save_data()

		self.imageIndex = min(len(self.imagePathList) - 1, self.imageIndex + 1)
		self.load_data()
	
	def load_data(self, event = None):
		# Update current image, load grid if exists
		self.update_canvas_image()

		dataPath = self.get_current_data_path()
		if os.path.isfile(dataPath):
			with open(dataPath, "rb") as f:
				datum = pickle.load(f)
			self.currentGrid = datum.grid.T
			print("loaded from", dataPath)
		else:
			self.clear_labels()

		self.update_canvas_grid()
	
	def save_data(self, event = None):
		unprocessedImage = Image.open(self.imagePathList[self.imageIndex])
		unprocessedImage = np.asarray(unprocessedImage)
		
		datum = PMEL_Datum(unprocessedImage, self.currentGrid)


		with open(self.get_current_data_path(), "wb") as f:
			pickle.dump(datum, f)

	def change_label(self, event = None):
		pressedKey = event.char
		if pressedKey == self.LABEL_GROUND_HOTKEY:
			self.selectedLabel.set(self.LABEL_GROUND)
		
		if pressedKey == self.LABEL_ENEMY_HOTKEY:
			self.selectedLabel.set(self.LABEL_ENEMY)

		if pressedKey == self.LABEL_PLAYER_HOTKEY:
			self.selectedLabel.set(self.LABEL_PLAYER)

		if pressedKey == self.LABEL_HAZARD_HOTKEY:
			self.selectedLabel.set(self.LABEL_HAZARD)

	def clear_labels(self, event = None):
		self.currentGrid = np.zeros(shape = (GRID_SIZE, GRID_SIZE),dtype=int)
		self.update_canvas_grid()

	def save_quit(self, event = None):
		self.save_data()
		self.root.destroy()

	def update_canvas_grid(self, event = None):
		self.screenshotCanvas.delete("labels")
		for xCell in range(self.currentGrid.shape[0]):
			for yCell in range(self.currentGrid.shape[1]):
				x1 = np.floor(xCell*\
						np.floor((NES_XRES*SCALE_FACTOR)/GRID_SIZE))
				y1 = np.floor(yCell*\
						np.floor((NES_YRES*SCALE_FACTOR)/GRID_SIZE))
				x2 = np.floor((xCell + 1)*\
						np.floor((NES_XRES*SCALE_FACTOR)/GRID_SIZE))
				y2 = np.floor((yCell + 1)*\
						np.floor((NES_YRES*SCALE_FACTOR)/GRID_SIZE))

				newFill = self.labelColours[self.currentGrid[xCell,yCell]]

				self.screenshotCanvas.create_rectangle(x1, y1, x2, y2, 
					fill = newFill, tag = "labels", outline = "", 
					stipple = "gray75")
		
		self.screenshotCanvas.delete("grid_line")
		imgWidth	= NES_XRES*SCALE_FACTOR
		imgHeight	= NES_YRES*SCALE_FACTOR
		# vertical
		for i in range(0, imgWidth, round(imgWidth/GRID_SIZE)):
			self.screenshotCanvas.create_line([(i, 0), (i, imgHeight)], 
				tag='grid_line')
		# horizontal
		for i in range(0, imgHeight, round(imgHeight/GRID_SIZE)):
			self.screenshotCanvas.create_line([(0, i),(imgWidth, i)], 
				tag='grid_line')

	def update_canvas_image(self):
		self.screenshotCanvas.delete("img")
		nesImg = Image.open(self.imagePathList[self.imageIndex])
		# Resample using Resampling.NEAREST or Dither.NONE to avoid anti-aliasing
		nesImg = nesImg.resize((NES_XRES*SCALE_FACTOR, NES_YRES*SCALE_FACTOR), 
			resample=Image.Resampling.NEAREST)
		self.currentImage = ImageTk.PhotoImage(nesImg)
		self.screenshotCanvas.create_image(0, 0, anchor = NW, image = self.currentImage, tag = "img")
				
	
#------------------------------------------------------------------------------
#LAYOUT
#------------------------------------------------------------------------------

	def create_button_frame(self, container):
		#TODO: bring in for loops, check if need to save to self
		frame = Frame(container)
		frame.columnconfigure(0, weight=1)

		self.controlButtons.extend((
			Button(frame, text="Save and Next\n"+self.HOTKEY_NEXT,
				command=self.go_next).grid(column=1, row=0),
			Button(frame, text="Save and Prev\n"+self.HOTKEY_PREV,
				command=self.go_previous).grid(column=0, row=0),
			Button(frame, text="Delete\n"+self.HOTKEY_DELETE,
				command=self.delete_current).grid(column=0, row=1),
			Button(frame, text="Clear Labels\n"+self.HOTKEY_CLEAR,
				command=self.clear_labels).grid(column=1, row=1)
		))

		self.controlButtons[0]

		self.filterVal = IntVar(container, self.FILTER_NONE)
		self.selectedLabel = IntVar(container, self.LABEL_GROUND)
		
		self.filterRadio.extend((
			Radiobutton(frame, text = "Labelled", 
				variable=self.filterVal, value = self.FILTER_LABELLED).grid(column=0, row=2),
			Radiobutton(frame, text = "Unlabelled", 
				variable=self.filterVal, value = self.FILTER_UNLABELLED).grid(column=0, row=3),
			Radiobutton(frame, text = "No Filter", 
				variable=self.filterVal, value = self.FILTER_NONE).grid(column=0, row=4),
		))

		self.labelRadio.extend((
			Radiobutton(frame, 
					text = "Ground Label (" + self.LABEL_GROUND_HOTKEY + ")", 
					variable=self.selectedLabel, 
					value = self.LABEL_GROUND
				).grid(column=1, row=2),

			Radiobutton(frame, 
					text = "Player Label (" + self.LABEL_PLAYER_HOTKEY + ")", 
					variable=self.selectedLabel, 
					value = self.LABEL_PLAYER
				).grid(column=1, row=3),

			Radiobutton(frame, 
					text = "Enemy Label (" + self.LABEL_ENEMY_HOTKEY + ")", 
					variable=self.selectedLabel, 
					value = self.LABEL_ENEMY
				).grid(column=1, row=4),
			
			Radiobutton(frame, 
					text = "Hazard Label (" + self.LABEL_HAZARD_HOTKEY + ")", 
					variable=self.selectedLabel, 
					value = self.LABEL_HAZARD
				).grid(column=1, row=5),
						
		))

		#TODO: add buttons / hotkeys for label selection

		for widget in frame.winfo_children():
			widget.grid(padx=0, pady=3, sticky=W)

		return frame

	def create_image_frame(self, container, photo):
		#frame = Frame(container)
		#frame.columnconfigure(0, weight=1)
		imgWidth	= NES_XRES*SCALE_FACTOR
		imgHeight	= NES_YRES*SCALE_FACTOR


		self.screenshotCanvas = Canvas(container, 
			width = imgWidth,
			height = imgHeight
			)

		self.screenshotCanvas.create_image(0, 0, anchor = NW, image = photo, tag = "img")

		# Move these to a <Configure> event?

		# vertical
		for i in range(0, imgWidth, round(imgWidth/GRID_SIZE)):
			self.screenshotCanvas.create_line([(i, 0), (i, imgHeight)], 
				tag='grid_line')
		# horizontal
		for i in range(0, imgHeight, round(imgHeight/GRID_SIZE)):
			self.screenshotCanvas.create_line([(0, i),(imgWidth, i)], 
				tag='grid_line')

		# Finds the x and y coords of mouse on image according to scale
		# TODO: Change so that this happens while mouse is held down w/ flags
		def place_flag(event):
			self.placingLabels = True
			place_action(event.x, event.y)

		def place_unflag(event):
			self.placingLabels = False

		def place_motion(event):
			place_action(event.x, event.y)

		def delete_m2_pressed(event):
			self.removingLabels = True
			delete_action(event.x, event.y)

		def delete_m2_released(event):
			self.removingLabels = False

		def delete_motion(event):
			delete_action(event.x, event.y)

		def place_action(ex, ey):
			x = round(self.screenshotCanvas.canvasx(ex)/SCALE_FACTOR)
			y = round(self.screenshotCanvas.canvasy(ey)/SCALE_FACTOR)

			gridX = int(np.floor(x/GRID_X_INTERVAL))
			gridY = int(np.floor(y/GRID_Y_INTERVAL))

			if gridX < GRID_SIZE and gridY < GRID_SIZE \
			and gridX >= 0 and gridY >=0:
				self.currentGrid[gridX,gridY] = self.selectedLabel.get()
				self.update_canvas_grid()

			#print(self.currentGrid)

		def delete_action(ex, ey):
			if self.removingLabels:
				x = round(self.screenshotCanvas.canvasx(ex)/SCALE_FACTOR)
				y = round(self.screenshotCanvas.canvasy(ey)/SCALE_FACTOR)

				gridX = int(np.floor(x/GRID_X_INTERVAL))
				gridY = int(np.floor(y/GRID_Y_INTERVAL))

				if gridX < GRID_SIZE and gridY < GRID_SIZE \
				and gridX >= 0 and gridY >=0:
					self.currentGrid[gridX,gridY] = 0
					self.update_canvas_grid()

		# MOUSE CONTROL
		self.screenshotCanvas.bind("<Button-1>", place_flag)
		self.root.bind("<ButtonRelease-1>", place_unflag)
		self.screenshotCanvas.bind("<B1-Motion>", place_motion)

		self.screenshotCanvas.bind("<Button-3>",delete_m2_pressed)
		self.root.bind("<ButtonRelease-3>",delete_m2_released)
		self.screenshotCanvas.bind("<B3-Motion>",delete_motion)

		return self.screenshotCanvas

	def toolbar(self, container):

		menuBar = Menu(container)
		container.config(menu=menuBar)

		#TODO: use to set some global for image or json directory, need plan
		def set_image_dir_menu():
			selectedDir = filedialog.askdirectory()
			self.set_directories(imgDir = selectedDir)

		fileMenu = Menu(menuBar)
		fileMenu.add_command(label="Set Image Directory", 
			command = set_image_dir_menu)
		fileMenu.add_command(label="Save and Quit",
			command = self.save_quit)
		
		menuBar.add_cascade(label="File", menu=fileMenu)

	def main_window(self):
		# Window Params
		self.root = Tk()
		self.root.title("PMEL")
		self.root.geometry("1200x800")
		self.root.resizable(0,0)
		self.root.configure(bg='black')

		buttonFrame = self.create_button_frame(self.root)
		buttonFrame.grid(column=1,row=0)

		nesImg = Image.open(self.currentImage)
		# Resample using Resampling.NEAREST or Dither.NONE to avoid anti-aliasing
		nesImg = nesImg.resize((NES_XRES*SCALE_FACTOR, NES_YRES*SCALE_FACTOR), 
			resample=Image.Resampling.NEAREST)
		photo = ImageTk.PhotoImage(nesImg)

		imageFrame = self.create_image_frame(self.root, photo)
		imageFrame.grid(column=2, row = 0)

		self.toolbar(self.root)

		# HOTKEYS
		self.root.bind("<Key>", self.change_label)
		self.root.bind(self.HOTKEY_CLEAR, self.clear_labels)
		self.root.bind(self.HOTKEY_DELETE, self.delete_current)
		self.root.bind(self.HOTKEY_NEXT, self.go_next)
		self.root.bind(self.HOTKEY_PREV, self.go_previous)

		self.root.mainloop()

if __name__ == "__main__":
	pmel = PMEL(debugMode = True)
