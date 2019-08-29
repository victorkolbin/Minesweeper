import pygame, random
from sys import exit
pygame.init()
pygame.display.set_caption("Minesweeper")
clock = pygame.time.Clock()


class Tile():
    def __init__(self):
        self.reset()

    def reset(self):
        self.number = 0  # -1 to 9: -1 means whitespace (no surrounding mines), 0 means the tile isn't being used, 1-8 means that amount of mines are nearby, 9 means mine
        self.isClicked = False         # tile is open or not
        self.isFlagged = False         # tile is flagged or not
        self.amtSurroundingFlags = 0   # used to keep track of how many of the surrounding tiles have been marked with a flag
        self.wasDoubleClicked = False  # indicates if tile has been processed by doubleClick() or not
        self.whitespaceClicked = False # indicates if tile has been processed by whitespaceClick() or not



''' Only one Gameboard object will be used per gaming session
    Instantiation, board resets, & difficulty changes will all be handled by newGame()'''
class Gameboard():
    def __init__(self):
        # load in all images. This noticably slows down execution, but this is the best time to do it
        self.originalRedMine = pygame.image.load("./images/mine_red.png")
        self.originalLightBlueMine = pygame.image.load("./images/mine_light_blue.png")
        self.originalDarkBlueMine = pygame.image.load("./images/mine_dark_blue.png")
        self.originalLightGreenFlag = pygame.image.load("./images/flag_light_green.png")
        self.originalDarkGreenFlag = pygame.image.load("./images/flag_dark_green.png")
        self.originalLightYellowFlag = pygame.image.load("./images/flag_light_yellow.png")
        self.originalDarkYellowFlag = pygame.image.load("./images/flag_dark_yellow.png")

        # this list is used if the user has power double-click enabled... it is a class variable because multiple Gameboard methods use it
        self.doubleClickQueue = []
        # these values are used to keep track of what the user has done in the Custom menu
        self.powerDoubleclickEnabled = False
        self.autoTileOpeningEnabled = False
        self.customDifficultyInputted = False

        '''Create a 50 x 99 board of Tile objects: this is the max allowed size for the board.
           A new board will not be created at the start of every new game, but rather all Tile objects in it will be reset'''
        self.board = [[Tile() for x in range(99)] for y in range(50)]



    def firstClick(self, row, col):  # this chooses mine locations based on the first click location, and then updates the numbers of all Tiles objects on our board
        # there must not be any mines in any of the surrounding tiles of the first clicked tile, so we must change our population for the random sampling
        excemptLocations = []
        for i in range(3):
            for j in range(3):
                excemptLocations.append((row - 1 + i) * self.numCols + (col - 1 + j))

        # obtain the random sampling for mine locations: random.sample arguments are population list to choose from, then how many samples you want
        self.mineLocations = random.sample([x for x in range(self.numCols * self.numRows) if x not in excemptLocations], self.numMines)

        # change the random sampling (numbers ranging from 0 to the amount of tiles on the gameboard) into a list of coordinates
        for i in range(len(self.mineLocations)):
            self.mineLocations[i] = (self.mineLocations[i] // self.numCols, self.mineLocations[i] % self.numCols)


        # THIS PRINTS THE MINES TO THE SCREEN, YOU CAN UNCOMMENT IF YOU WANT TO
        '''for x, y in self.mineLocations:
            pygame.draw.rect(self.screen, (10,10,10), (self.TILESIZE * y + int(self.TILESIZE/4), self.TILESIZE * x + int(self.TILESIZE/4), int(self.TILESIZE/2), int(self.TILESIZE/2)))
        pygame.display.flip()'''                                                                                                                                                                                                                                                                                                              

    
        # increment Tile.number for each tile surrounding each mine... there are 8 surrounding tiles
        for x, y in self.mineLocations:
            for i in range(3):
                for j in range(3):
                    try:
                        if (x - 1 + i) < self.numRows and (y - 1 + j) < self.numCols:
                            self.board[self.onlyNonnegative(x - 1 + i)][self.onlyNonnegative(y - 1 + j)].number += 1
                    except IndexError: # in case we try to go outside of the board, simply ignore (pass) this attempt
                        pass
                    
        # set Tile.number to 9 for each mine
        for x, y in self.mineLocations:
            self.board[x][y].number = 9

        # set Tile.number to -1 for remaining tiles on the board (whitespace)
        for x in range(self.numRows):   
            for y in range(self.numCols):
                if self.board[x][y].number == 0:
                    self.board[x][y].number = -1

        self.whitespaceClick(row, col) # this function will open the first click, which is guaranteed to be whitespace
                   

        
    def mouseClick(self, row, col, button): # this function handles all clicks: different things happen depending on the type of click and selected tile
        if row == 50: # this happens when the user sets the rows to the max size of 50 in the custom menu
            return
        
        tile = self.board[row][col]
        
        if button == 1 and tile.isClicked == False and tile.isFlagged == False: # single left-click
            if tile.number == -1:        # clicked on whitespace
                self.whitespaceClick(row, col)
            elif 1 <= tile.number <= 8:  # clicked on number
                self.openTiles([(row,col)])
            elif tile.number == 9:       # clicked on mine
                self.gameOver(row, col, 0)
                
        elif button == 2 and tile.isFlagged == False: # double left-click (single-click takes care of whitespace and mines, all we have to look at are numbered tiles)
            if 1 <= tile.number <= 8 and self.powerDoubleclickEnabled == False:
                self.doubleClick(row, col)
            elif 1 <= tile.number <= 8 and self.powerDoubleclickEnabled == True:
                self.powerDoubleClick(row, col)
                
        elif button == 3 and tile.isClicked == False: # right-click
            if tile.isFlagged == False:  # flag not marked, mark it
                tile.isFlagged = True
                self.screen.blit(self.darkYellowFlag if (row + col) % 2 else self.lightYellowFlag, (col * self.TILESIZE, row * self.TILESIZE))
                self.numMinesRemaining -= 1
                
            elif tile.isFlagged == True: # flag already marked, undo it by switching back to blue tile
                tile.isFlagged = False
                pygame.draw.rect(self.screen, (100, 108, 248) if (col + row) % 2 else (104, 113, 255), (self.TILESIZE * col, self.TILESIZE * row, self.TILESIZE, self.TILESIZE))
                self.numMinesRemaining += 1

            # flagging or unflagging a tile should change the state of surrounding tiles, specifically their .amtSurroundingFlags and .wasDoubleClicked attributes
            self.flaggedTileUpdate(row, col, True if tile.isFlagged else False)
                



    def whitespaceClick(self, row, col): # this function handles a single or double-click on whitespace
        whitespaceQueue = [(row, col)]
        tileCoordinates = [(row, col)]

        # algorithm: open whitespace, look at all 8 surrounding tiles. Add any whitespace you find to the whitespaceQueue and repeat
        while whitespaceQueue:
            row, col = whitespaceQueue[0][0], whitespaceQueue[0][1]
            self.board[row][col].whitespaceClicked = True
                
            for i in range(3):
                for j in range(3):
                    try:
                        tile = self.board[self.onlyNonnegative(row - 1 + i)][self.onlyNonnegative(col - 1 + j)]

                        if tile.number == -1 and tile.whitespaceClicked == False and tile.isFlagged == False:       # found more whitespace: add its location to the whitespace queue
                            tile.whitespaceClicked = True
                            whitespaceQueue.append((row - 1 + i, col - 1 + j))
                            tileCoordinates.append((row - 1 + i, col - 1 + j))
    
                        elif 1 <= tile.number <= 8 and tile.isClicked == False and tile.isFlagged == False: # found a number: add its location to tileCoordinates list to open
                            tileCoordinates.append((row - 1 + i, col - 1 + j))

                    except IndexError:
                        pass

            whitespaceQueue.pop(0) # pop the whitespace tile we just looked at
    
        self.openTiles(tileCoordinates)
            


    def doubleClick(self, row, col): # this function handles a double-click on a numbered tile... different from single-click on number because this one expands
        tileCoordinates = [(row, col)]
        self.board[row][col].wasDoubleClicked = True

        # if the amount of surrounding flags is not equal to the tile number, then it is not satisfied. simply return
        if self.board[row][col].amtSurroundingFlags != self.board[row][col].number:
            return
    
        # now since the tile is satisfied, open up 8 surrounding tiles, and look for any whitespace or mines as well
        for i in range(3):
            for j in range(3):    
                try:
                    tile = self.board[self.onlyNonnegative(row - 1 + i)][self.onlyNonnegative(col - 1 + j)]

                    if tile.number == -1 and tile.isClicked == False:  # whitespace
                        self.whitespaceClick(row - 1 + i, col - 1 + j)
                                
                    elif 1 <= tile.number <= 8 and (i, j) != (1, 1):   # number
                        if tile.isClicked == False:
                            tileCoordinates.append((row - 1 + i, col - 1 + j))

                        # if the user has power double-click enabled and this numbered tile hasn't been on the doubleClickQueue, we're going to append it to doubleClickQueue
                        if self.powerDoubleclickEnabled == True and tile.wasDoubleClicked == False:
                            tile.wasDoubleClicked = True
                            self.doubleClickQueue.append((row - 1 + i, col - 1 + j))

                    elif tile.number == 9 and tile.isFlagged == False: # mine
                            self.gameOver(row - 1 + i, col - 1 + j, 0)
                            return
                            
                except IndexError:
                    pass
        
        self.openTiles(tileCoordinates)

        

    def powerDoubleClick(self, row, col): # this function handles a power double-click on a numbered tile
        self.doubleClickQueue = []

        # power double-clicking isn't only activated by the double-clicked tile, but can also be triggered by any of the 8 surrounding tiles... check for satisfied UNOPENED tiles
        for i in range(3):
            for j in range(3):        
                try:
                    tile = self.board[self.onlyNonnegative(row - 1 + i)][self.onlyNonnegative(col - 1 + j)]
                    if tile.amtSurroundingFlags == tile.number and (row - 1 + i) < self.numRows and (col - 1 + j) < self.numCols and tile.isClicked:
                        self.doubleClickQueue.append((row - 1 + i, col - 1 + j))
                        tile.wasDoubleClicked = True
                except IndexError:
                    pass

        ''' algorithm: take the satisfied numbered tile that was power double-clicked, treat it as a generic double-click, ...
            and add any other satisfied, nearby tiles to the queue. Repeat.'''
        while self.doubleClickQueue:
            # first check if the game has ended from one of the previous iterations
            if self.started == False:
                return
            
            row, col = self.doubleClickQueue[0][0], self.doubleClickQueue[0][1]
            self.doubleClick(row, col)   # send the numbered tile to doubleClick()
            self.doubleClickQueue.pop(0) # pop the numbered tile we just looked at



    def flaggedTileUpdate(self, row, col, flagPlaced):
        ''' This function is only called when a tile is (un)flagged. It goes to all surrounding tiles to update their .amtSurroundingFlags and .wasDoubleClicked attributes.
            The reason for resetting .wasDoubleClicked to False is because powerDoubleClick() uses this attribute to identify which tiles to look at when opening them'''
        for i in range(3):
            for j in range(3):
                # first check if the game has ended from one of the previous iterations
                if self.started == False:
                    return
                
                try:
                    tile = self.board[self.onlyNonnegative(row - 1 + i)][self.onlyNonnegative(col - 1 + j)]
                    if 1 <= tile.number <= 8:
                        tile.amtSurroundingFlags += 1 if flagPlaced else -1 # increment .amtSurroundingFlags if a flag was placed, else decrement
                        tile.wasDoubleClicked = False # set to False, even if .wasDoubleClicked isn't being used (aka power double-click not enabled). It doesn't matter

                    # if some surrounding tile is satisfied and the user has Automatic tile opening enabled, double-click it (or power double-click if the user has that enabled)
                    if self.autoTileOpeningEnabled == True and tile.amtSurroundingFlags == tile.number and (row - 1 + i) < self.numRows and (col - 1 + j) < self.numCols:
                        if self.powerDoubleclickEnabled == True:
                            self.powerDoubleClick(row - 1 + i, col - 1 + j)
                        elif self.powerDoubleclickEnabled == False and tile.isClicked == True:
                            self.powerDoubleClick(row - 1 + i, col - 1 + j)
                        
                except IndexError:
                    pass



    def openTiles(self, tileCoordinates): # this functions renders the text of the numbers and displays it on the appropriate tile
        font = pygame.font.SysFont('Lucida Grande', int(self.TILESIZE / 1.1))
        
        # determine the appropriate color for the text depending on the tile number
        for row,col in tileCoordinates:
            tile = self.board[row][col]

            if tile.isClicked == True:
                continue
            
            tile.isClicked = True
            self.numTilesRemaining -= 1
            
            if tile.number == 1 or tile.number == -1:
                color = (95, 104, 234)
            elif tile.number == 2:
                color = (61, 166, 66)
            elif tile.number == 3:
                color = (217, 72, 66)
            elif tile.number == 4:
                color = (67, 72, 170)
            elif tile.number == 5:
                color = (138, 0, 198)
            elif tile.number == 6:
                color = (104, 73, 0)
            elif tile.number == 7:
                color = (50, 50, 50)
            elif tile.number == 8:
                color = (0, 0, 0)

            # display the number
            txt = font.render('' if tile.number == -1 else str(tile.number), True, color)
            txtRect = txt.get_rect()
            txtRect.center = (int(self.TILESIZE * (col + .5)), int(self.TILESIZE * (row + .5)))
            pygame.draw.rect(self.screen, (245, 245, 245) if (col + row) % 2 else (251, 250, 251), (self.TILESIZE * col, self.TILESIZE * row, self.TILESIZE, self.TILESIZE))
            self.screen.blit(txt, txtRect)

        pygame.display.flip()



    def gameOver(self, row, col, gameState): # game ends either by clicking a mine or winning the game
        self.started = False

        # display all blue mines, green flags, and yellow flags in the appropriate locations
        for i in range(self.numRows):
            for j in range(self.numCols):
                tile = self.board[i][j]
                if tile.number == 9 and tile.isClicked == False and tile.isFlagged == False and (i, j) != (row, col):   # unclicked, unflagged mine: blue
                    self.screen.blit(self.darkBlueMine if (i + j) % 2 else self.lightBlueMine, (j * self.TILESIZE, i * self.TILESIZE))
                if tile.number == 9 and (tile.isFlagged == True or self.numTilesRemaining == 0):                        # correctly flagged mine: green
                        self.screen.blit(self.darkGreenFlag if (i + j) % 2 else self.lightGreenFlag, (j * self.TILESIZE, i * self.TILESIZE))
                if (tile.number == -1 or 1 <= tile.number <= 8) and tile.isFlagged == True:                             # incorrectly flagged mine: yellow
                        self.screen.blit(self.darkYellowFlag if (i + j) % 2 else self.lightYellowFlag, (j * self.TILESIZE, i * self.TILESIZE))

        # if the game ended by a mine click, display a red mine where it exploded
        if gameState == 0:
            self.screen.blit(self.redMine, (col * self.TILESIZE, row * self.TILESIZE))

        
        # set size and location of "Click for a new game" box
        boxWidth = 185
        boxHeight = 35
        boxLeft = (self.screenWidth - boxWidth) / 2
        boxTop = self.screenHeight * .66

        # display "Click for a new game" box
        newGameBox = pygame.Surface((boxWidth, boxHeight))  # newGameBox is a new Surface object
        newGameBox.set_alpha(200)                           # make it a little transparent
        newGameBox.fill((30,30,30))
        self.screen.blit(newGameBox, (boxLeft, boxTop))     # blit newGameBox surface onto the main surface

        # display "Click for a new game" text
        font = pygame.font.SysFont('Lucida Grande', 15)
        newGameText = font.render("Click for a new game", True, (255, 255, 255))
        self.screen.blit(newGameText, (boxLeft + 16, boxTop + 8))
        pygame.display.flip()

        # while we wait for the to select the "Click for a new game" box, we can reset all Tile objects' properties on our board
        self.resetTiles(self.numRows, self.numCols)

        # wait for the user to either quit out of the window, click the "Click for a new game" box, or click the "Change difficulty" box
        while True:
            for event in pygame.event.get():
                if event.type == pygame.QUIT or (event.type == pygame.KEYDOWN and event.key == pygame.K_ESCAPE):
                    pygame.quit()
                    exit()

                if event.type == pygame.MOUSEBUTTONUP:
                    x,y = pygame.mouse.get_pos()
                    pygame.mouse.get_pressed()
                    if event.button == 1:
                        if boxLeft < x < boxLeft + boxWidth and boxTop < y < boxTop + boxHeight:    # user clicks "Create a new game" box
                            self.newGame(self.numRows, self.numCols, self.numMines, self.TILESIZE)  # reset the gameboard with the same dimensions and numMines
                            return

                        # user clicks "Change difficulty" box
                        elif (int(Game.screenWidth / 2) - 56) < x < (int(Game.screenWidth / 2) + 61) and (Game.screenHeight - 21) < y < (Game.screenHeight - 4):
                            menu.difficultyMenu()
                            self.resetTiles(menu.numRows, menu.numCols)
                            Game.newGame(menu.numRows, menu.numCols, menu.numMines, menu.tilesize)
                            return



    def newGame(self, numRows, numCols, numMines, tilesize): # this function resets the Gameboard class properties, and displays the new gameboard
        # most of Gameboard's member variables are initialized here
        self.started = False
        self.numRows = numRows
        self.numCols = numCols
        self.numMines = numMines
        self.TILESIZE = tilesize
        
        self.screenWidth = numCols * self.TILESIZE
        self.screenHeight = numRows * self.TILESIZE + 25 # 25 extra pixels for the bottom bar
        self.numMinesRemaining = numMines
        self.numTilesRemaining = (numCols * numRows) - numMines
        self.mineLocations = []
        self.displayedTimer = 0
        self.screen = pygame.display.set_mode((self.screenWidth, self.screenHeight))
        self.screen.set_alpha(None)

        # resize all loaded images
        self.redMine = pygame.transform.scale(self.originalRedMine, (self.TILESIZE, self.TILESIZE))
        self.lightBlueMine = pygame.transform.scale(self.originalLightBlueMine, (self.TILESIZE, self.TILESIZE))
        self.darkBlueMine = pygame.transform.scale(self.originalDarkBlueMine, (self.TILESIZE, self.TILESIZE))
        self.lightGreenFlag = pygame.transform.scale(self.originalLightGreenFlag, (self.TILESIZE, self.TILESIZE))
        self.darkGreenFlag = pygame.transform.scale(self.originalDarkGreenFlag, (self.TILESIZE, self.TILESIZE))
        self.lightYellowFlag = pygame.transform.scale(self.originalLightYellowFlag, (self.TILESIZE, self.TILESIZE))
        self.darkYellowFlag = pygame.transform.scale(self.originalDarkYellowFlag, (self.TILESIZE, self.TILESIZE))
        
        # create the blue checkerboard pattern
        colorSwitch = True
        for i in range(self.numRows):
            for j in range(self.numCols):
                pygame.draw.rect(self.screen, (104, 113, 255) if colorSwitch else (100, 108, 248), (self.TILESIZE * j, self.TILESIZE * i, self.TILESIZE, self.TILESIZE))
                colorSwitch = not colorSwitch
            colorSwitch = colorSwitch if self.numCols % 2 else not colorSwitch

        # draw the bottom bar and the "Change difficulty box"
        pygame.draw.rect(self.screen, (200,200,210), (0, self.screenHeight - 25, self.screenWidth, 25))
        font = pygame.font.SysFont('Lucida Grande', 13)
        difficultyText = font.render("Change difficulty", True, (20, 20, 20), (200, 200, 210))
        difficultyRect = difficultyText.get_rect()
        difficultyRect.center = (int(self.screenWidth / 2) + 3, int(self.screenHeight - 13))            
        self.screen.blit(difficultyText, difficultyRect)
        difficultyRect.width, difficultyRect.height, difficultyRect.left = 117, 17, difficultyRect.left - 5
        pygame.draw.rect(self.screen, (110, 110,170), difficultyRect, 1)
        pygame.display.flip()


        
    def resetTiles(self, numRows, numCols):
        # we want to reset the tiles on the current gameboard, and one extra row and column, unless numRows and/or numCols hit their max: 50 and 99
        numRows = numRows + 1 if numRows != 50 else numRows
        numCols = numCols + 1 if numCols != 99 else numCols
        
        for row in range(numRows):
            for col in range(numCols):
                self.board[row][col].reset()



    def onlyNonnegative(self, num): # this is used throughout the Gameboard class to obtain integers >= 0, for the purpose of indexing into board[][]
        if num < 0:
            return 1000 # returning 1000 as an index value will throw IndexError. it will be caught
        else:
            return num




#######    DIFFICULTY MENU    ########        
''' My Menu class doesn't work as desired since pygame doesn't allow to un-blit() a screen.
    Instead, clicking on Custom or Help blits a new screen on top of the current one as many times as the user clicks them,
    and we only leave the difficulty menu once the user clicks Beginner, Intermediate, or Expert, or types in custom game parameters.
    I also had to create my own text boxes and that made customMenu() very confusing. Overall, it's a spaghetti class but it works'''
class Menu():
    def difficultyMenu(self):
        # initialize all of Menu's member variables
        self.screen = pygame.display.set_mode((300, 350))
        self.screen.fill((199, 204, 216))
        self.rowsBoxSelected = False
        self.colsBoxSelected = False
        self.minesBoxSelected = False
        self.tilesizeBoxSelected = False
        self.cancelBoxSelected = False
        self.okBoxSelected = False
        self.numRows = 0
        self.numCols = 0
        self.numMines = 0
        self.tilesize = 28
        

        # display the Beginner, Intermediate, Expert, Custom, and Help boxes
        pygame.draw.rect(self.screen, (82, 108, 235), (50, 40, 200, 42))
        pygame.draw.rect(self.screen, (52, 78, 165), (50, 99, 200, 42))
        pygame.draw.rect(self.screen, (22, 48, 115), (50, 158, 200, 42))
        pygame.draw.rect(self.screen, (52, 78, 165), (100, 225, 100, 34), 2)
        pygame.draw.rect(self.screen, (52, 78, 165), (110, 275, 80, 30), 2)

        # set font and font colors
        font = pygame.font.SysFont('Lucida Grande', 20)
        difficultyColor = (245, 245, 250)
        otherBoxColor = (34,34,34)

        # render the texts
        txtBeginner = font.render('Beginner', True, difficultyColor)
        txtIntermediate = font.render('Intermediate', True, difficultyColor)
        txtExpert = font.render('Expert', True, difficultyColor)
        txtCustom = font.render('Custom', True, otherBoxColor)
        txtHelp = font.render('Help', True, otherBoxColor)

        # obtain text rectangles
        txtRectBeginner = txtBeginner.get_rect()
        txtRectIntermediate = txtIntermediate.get_rect()
        txtRectExpert = txtExpert.get_rect()
        txtRectCustom = txtCustom.get_rect()
        txtRectHelp = txtHelp.get_rect()

        # set text rectangles' centers
        txtRectBeginner.center = (150, 61)
        txtRectIntermediate.center = (150, 120)
        txtRectExpert.center = (150, 179)
        txtRectCustom.center = (150, 242)
        txtRectHelp.center = (150, 290)

        # blit the text to the screen
        self.screen.blit(txtBeginner, txtRectBeginner)
        self.screen.blit(txtIntermediate, txtRectIntermediate)
        self.screen.blit(txtExpert, txtRectExpert)
        self.screen.blit(txtCustom, txtRectCustom)
        self.screen.blit(txtHelp, txtRectHelp)

        pygame.display.flip()


        # the user may go back and forth from the Help and Custom menus, but this loop will end when they select/input a difficulty or close the window
        while True:
            for event in pygame.event.get():
                if event.type == pygame.QUIT or (event.type == pygame.KEYDOWN and event.key == pygame.K_ESCAPE):
                    pygame.quit()
                    exit()

                if event.type == pygame.MOUSEBUTTONUP:
                    x,y = pygame.mouse.get_pos()
                    pygame.mouse.get_pressed()
                    if event.button == 1:
                        if 50 < x < 250 and 40 < y < 82:      # Beginner
                            self.numRows, self.numCols, self.numMines, self.tilesize = 10, 10, 15, 28
                            Game.customDifficultyInputted, Game.powerDoubleclickEnabled, Game.autoTileOpeningEnabled = False, False, False
                        elif 50 < x < 250 and 99 < y < 141:   # Intermediate
                            self.numRows, self.numCols, self.numMines, self.tilesize = 15, 27, 80, 28
                            Game.customDifficultyInputted, Game.powerDoubleclickEnabled, Game.autoTileOpeningEnabled = False, False, False
                        elif 50 < x < 250 and 158 < y < 200:  # Expert
                            self.numRows, self.numCols, self.numMines, self.tilesize = 24, 30, 155, 28
                            Game.customDifficultyInputted, Game.powerDoubleclickEnabled, Game.autoTileOpeningEnabled = False, False, False
                        elif 100 < x < 200 and 225 < y < 259: # Custom menu
                            self.customMenu()
                        elif 110 < x < 190 and 275 < y < 305: # Help menu
                            self.helpMenu()
                        else:  # any other click will be ignored
                            continue

                        return # if one of the buttons was pressed, we're all set with this temporary difficulty menu... return

            clock.tick(30)



    def helpMenu(self):
        # create and display transparent gray Help box
        newGameBox = pygame.Surface((230, 330))
        newGameBox.set_alpha(230)
        newGameBox.fill((30,30,30))
        self.screen.blit(newGameBox, (35, 10))

        # render all Help box text
        font = pygame.font.SysFont('Lucida Grande', 15)
        XButton = font.render('[X]', True, (255, 0, 0))
        line1 = font.render('Left-click to open a tile', True, (255, 255, 255))
        line2 = font.render('Right-click to place a flag', True, (255, 255, 255))
        line3 = font.render('Double-click\'s special ability:', True, (255, 255, 255))
        line4 = font.render('- Opens all surrounding tiles', True, (255, 255, 255))
        line5 = font.render('- BUT there must be the', True, (255, 255, 255))
        line6 = font.render('   correct amount of flags', True, (255, 255, 255))
        line7 = font.render('   surrounding the tile', True, (255, 255, 255))
        line8 = font.render('- Works for both opened', True, (255, 255, 255))
        line9 = font.render('   and unopened tiles', True, (255, 255, 255))

        # blit all text to the screen
        self.screen.blit(XButton, (40, 13, 19, 19))
        self.screen.blit(line1, (45, 45))
        self.screen.blit(line2, (45, 95))
        self.screen.blit(line3, (45, 145))
        self.screen.blit(line4, (45, 165))
        self.screen.blit(line5, (45, 185))
        self.screen.blit(line6, (45, 205))
        self.screen.blit(line7, (45, 225))
        self.screen.blit(line8, (45, 245))
        self.screen.blit(line9, (45, 265))

        pygame.display.flip()


        # wait for the user to click [X], click outside of the Help window, or close the Minesweeper window    
        while True:
            for event in pygame.event.get():
                if event.type == pygame.QUIT:
                    pygame.quit()
                    exit()

                elif event.type == pygame.KEYDOWN and event.key == pygame.K_ESCAPE:
                    self.difficultyMenu()
                    return

                elif event.type == pygame.MOUSEBUTTONUP:
                    x,y = pygame.mouse.get_pos()
                    pygame.mouse.get_pressed()
                    if event.button == 1:
                        if (40 < x < 59 and 13 < y < 32) or (x < 35 or x > 265 or y < 10 or y > 340):
                            self.difficultyMenu()
                            return
                        
            clock.tick(30)



    def customMenu(self):
        # set up the new screen and all the fonts we'll be using
        self.screen.fill((199, 204, 216))
        messageSurface = pygame.Surface((120, 20))
        messageSurface.fill((199, 204, 216))
        self.screen.blit(messageSurface, (157, 302))
        smallFont = pygame.font.SysFont('Lucida Grande', 9)
        mediumFont = pygame.font.SysFont('Lucida Grande', 12)
        largeFont = pygame.font.SysFont('Lucida Grande', 15)

        # display the keyboard input boxes, Cancel & OK boxes, and the 2 checkboxes (black outline w/ a white/gray inner box)
        pygame.draw.rect(self.screen, (0, 0, 0), (140, 45, 50, 25), 1)      # row
        pygame.draw.rect(self.screen, (0, 0, 0), (140, 80, 50, 25), 1)      # col
        pygame.draw.rect(self.screen, (0, 0, 0), (140, 115, 50, 25), 1)     # mines
        pygame.draw.rect(self.screen, (0, 0, 0), (140, 150, 30, 25), 1)     # tilesize
        pygame.draw.rect(self.screen, (0, 0, 0), (175, 200, 15, 15), 1)     # power double-click
        pygame.draw.rect(self.screen, (0, 0, 0), (175, 224, 15, 15), 1)     # auto tile opening
        pygame.draw.rect(self.screen, (0, 0, 0), (45, 285, 95, 30), 1)      # cancel
        pygame.draw.rect(self.screen, (0, 0, 0), (160, 285, 95, 30), 1)     # OK
        
        pygame.draw.rect(self.screen, (255, 255, 255), (141, 46, 48, 23))   # row
        pygame.draw.rect(self.screen, (255, 255, 255), (141, 81, 48, 23))   # col
        pygame.draw.rect(self.screen, (255, 255, 255), (141, 116, 48, 23))  # mines
        pygame.draw.rect(self.screen, (255, 255, 255), (141, 151, 28, 23))  # tilesize
        pygame.draw.rect(self.screen, (255, 255, 255), (176, 201, 13, 13))  # power double-clicking
        pygame.draw.rect(self.screen, (255, 255, 255), (176, 225, 13, 13))  # auto tile opening
        pygame.draw.rect(self.screen, (200, 200, 200), (46, 286, 93, 28))   # cancel
        pygame.draw.rect(self.screen, (200, 200, 200), (161, 286, 93, 28))  # OK

        # insert blue boxes in the checkboxes if they were previously selected
        if Game.powerDoubleclickEnabled:
            pygame.draw.rect(self.screen, (0, 17, 255), (178, 203, 9, 9))
        if Game.autoTileOpeningEnabled:
            pygame.draw.rect(self.screen, (0, 17, 255), (178, 227, 9, 9))

        # render all the text labelling the boxes
        warning = smallFont.render('Making the board too small or too large', True, (229, 0, 0))
        warning2 = smallFont.render('may cause issues, be wary.', True, (229, 0, 0))
        rowBox = largeFont.render('Rows:', True, (0, 0, 0))
        rowRange = smallFont.render('10 to 50', True, (52, 52, 77))
        colBox = largeFont.render('Columns:', True, (0, 0, 0))
        colRange = smallFont.render('10 to 99', True, (52, 52, 77))
        mineBox = largeFont.render('Mines:', True, (0, 0, 0))
        mineRange = smallFont.render('1 to rows * cols - 10', True, (52, 52, 77))
        tilesizeBox = largeFont.render('Tile size:', True, (0, 0, 0))
        tilesizeRange = smallFont.render('15 to 50', True, (52, 52, 77))
        pixels = smallFont.render('pixels', True, (0, 0, 0))
        powerDoubleClick = mediumFont.render('Power double-click', True, (0, 0, 0))
        autoTileOpening = mediumFont.render('Automatic tile opening', True, (0, 0, 0))
        cancelBox = largeFont.render('Cancel', True, (0, 0, 0))
        okBox = largeFont.render('OK', True, (0, 0, 0))
        dimError = smallFont.render('dimensions not accepted', True, (229, 0, 0), (199, 204, 216))
        tilesizeError = smallFont.render('tile size not accepted', True, (229, 0, 0), (199, 204, 216))

        # get the rects of a few of the texts
        warningRect = warning.get_rect()
        warning2Rect = warning2.get_rect()
        cancelBoxRect = cancelBox.get_rect()
        okBoxRect = okBox.get_rect()

        # set the locations of these rects
        warningRect.center = (150, 9)
        warning2Rect.center = (150, 20)
        cancelBoxRect.center = (92, 300)
        okBoxRect.center = (207, 300)

        # blit all the static text to the screen
        self.screen.blit(warning, warningRect)
        self.screen.blit(warning2, warning2Rect)
        self.screen.blit(rowBox, (35, 43))
        self.screen.blit(rowRange, (35, 59))
        self.screen.blit(colBox, (35, 78))
        self.screen.blit(colRange, (35, 94))
        self.screen.blit(mineBox, (35, 113))
        self.screen.blit(mineRange, (35, 129))
        self.screen.blit(tilesizeBox, (34, 147))
        self.screen.blit(tilesizeRange, (34, 164))
        self.screen.blit(pixels, (175, 160))
        self.screen.blit(powerDoubleClick, (35, 200))
        self.screen.blit(autoTileOpening, (35, 224))
        self.screen.blit(cancelBox, cancelBoxRect)
        self.screen.blit(okBox, okBoxRect)
        
        #####   initialize all needed strings, texts, and text rectangles for the following loop   #####
        # if the Custom menu is entered before selecting a difficulty, Game.numRows, Game.numCols, etc haven't been initialized. In this case, set default values for strings
        try:
            rowsStr = str(Game.numRows) if Game.customDifficultyInputted else ''
            colsStr = str(Game.numCols) if Game.customDifficultyInputted else ''
            minesStr = str(Game.numMines) if Game.customDifficultyInputted else ''
            tilesizeStr = str(Game.TILESIZE)
        except AttributeError:
            rowsStr, colsStr, minesStr, tilesizeStr = '', '', '', '28'

        rowsText = largeFont.render(rowsStr, True, (0, 0, 0), (255, 255, 255))
        colsText = largeFont.render(colsStr, True, (0, 0, 0), (255, 255, 255))
        minesText = largeFont.render(minesStr, True, (0, 0, 0), (255, 255, 255))
        tilesizeText = largeFont.render(tilesizeStr, True, (0, 0, 0), (255, 255, 255))
        
        rowsRect = (169, 48, 18, 19)
        colsRect = (169, 83, 18, 19)
        tilesizeRect = (149, 153, 18, 19)
        # the number displayed in the Mines box can be 1-4 digits long, while the others have to be 2, so it gets special treatment
        minesRect = minesText.get_rect()
        minesRect.right, minesRect.top = 187, 118

        ''' Check if the user is typing custom game parameters, clicking Cancel or OK, or closing the Minesweeper window.
            This loop is kinda spaghettied but that's cause I had to make keyboard input boxes on my own, pygame doesn't have this'''
        while True:
            for event in pygame.event.get():
                if event.type == pygame.QUIT:
                    pygame.quit()
                    exit()

                if event.type == pygame.KEYDOWN and event.key == pygame.K_ESCAPE:
                    self.difficultyMenu()
                    return

                elif event.type == pygame.MOUSEBUTTONUP:
                    x,y = pygame.mouse.get_pos()
                    pygame.mouse.get_pressed()
                    if event.button == 1:
                        # if one of the 6 boxes is selected, set its Selected variable equal to True, and all other boxes' Selected variable to False
                        if 140 < x < 190 and 45 < y < 70:     # Rows box
                            self.rowsBoxSelected, self.colsBoxSelected, self.minesBoxSelected, self.tilesizeBoxSelected,    \
                            self.cancelBoxSelected, self.okBoxSelected = True, False, False, False, False, False
                        elif 140 < x < 190 and 80 < y < 105:  # Columns box
                            self.rowsBoxSelected, self.colsBoxSelected, self.minesBoxSelected, self.tilesizeBoxSelected,    \
                            self.cancelBoxSelected, self.okBoxSelected = False, True, False, False, False, False
                        elif 140 < x < 190 and 115 < y < 140: # Mines box
                            self.rowsBoxSelected, self.colsBoxSelected, self.minesBoxSelected, self.tilesizeBoxSelected,    \
                            self.cancelBoxSelected, self.okBoxSelected = False, False, True, False, False, False
                        elif 140 < x < 170 and 150 < y < 175: # Tile size box
                            self.rowsBoxSelected, self.colsBoxSelected, self.minesBoxSelected, self.tilesizeBoxSelected,    \
                            self.cancelBoxSelected, self.okBoxSelected = False, False, False, True, False, False
                        elif 45 < x < 140 and 285 < y < 315:  # Cancel box
                            self.rowsBoxSelected, self.colsBoxSelected, self.minesBoxSelected, self.tilesizeBoxSelected,    \
                            self.cancelBoxSelected, self.okBoxSelected = False, False, False, False, True, False
                        elif 160 < x < 255 and 285 < y < 315: # OK box
                            self.rowsBoxSelected, self.colsBoxSelected, self.minesBoxSelected, self.tilesizeBoxSelected,    \
                            self.cancelBoxSelected, self.okBoxSelected = False, False, False, False, False, True
                        elif 175 < x < 190 and 200 < y < 215: # Power double-click checkbox
                            self.rowsBoxSelected, self.colsBoxSelected, self.minesBoxSelected, self.tilesizeBoxSelected,    \
                            self.cancelBoxSelected, self.okBoxSelected = False, False, False, False, False, False
                            Game.powerDoubleclickEnabled = False if Game.powerDoubleclickEnabled else True
                            pygame.draw.rect(self.screen, (0, 17, 255) if Game.powerDoubleclickEnabled else (255, 255, 255), (178, 203, 9, 9))
                        elif 175 < x < 190 and 224 < y < 239: # Automatic tile opening checkbox
                            self.rowsBoxSelected, self.colsBoxSelected, self.minesBoxSelected, self.tilesizeBoxSelected,    \
                            self.cancelBoxSelected, self.okBoxSelected = False, False, False, False, False, False
                            Game.autoTileOpeningEnabled = False if Game.autoTileOpeningEnabled else True
                            pygame.draw.rect(self.screen, (0, 17, 255) if Game.autoTileOpeningEnabled else (255, 255, 255), (178, 227, 9, 9))
                        

            # if one of the 4 keyboard input boxes has been selected, process what the user is typing
            if self.rowsBoxSelected:
                rowsStr = self.keyboardInput(rowsStr.lstrip(), 2)
                rowsText = largeFont.render(rowsStr, True, (0, 0, 0), (255, 255, 255))
                rowsRect = rowsText.get_rect()
                rowsRect.right, rowsRect.top = 187, 48

            elif self.colsBoxSelected:
                colsStr = self.keyboardInput(colsStr.lstrip(), 2)
                colsText = largeFont.render(colsStr, True, (0, 0, 0), (255, 255, 255))
                colsRect = colsText.get_rect()
                colsRect.right, colsRect.top = 187, 83

            elif self.minesBoxSelected:
                minesStr = self.keyboardInput(minesStr.lstrip(), 4)
                minesText = largeFont.render(minesStr, True, (0, 0, 0), (255, 255, 255))
                minesRect = minesText.get_rect()
                minesRect.right, minesRect.top = 187, 118

            elif self.tilesizeBoxSelected:
                tilesizeStr = self.keyboardInput(tilesizeStr.lstrip(), 2)
                tilesizeText = largeFont.render(tilesizeStr, True, (0, 0, 0), (255, 255, 255))
                tilesizeRect = tilesizeText.get_rect()
                tilesizeRect.right, tilesizeRect.top = 167, 153

            # if the Cancel box has been selected, go back to the difficulty screen
            elif self.cancelBoxSelected:
                self.difficultyMenu()
                return

            # if the OK box has been selected, check that all keyboard input is within the correct range. If not, display a warning message
            elif self.okBoxSelected:
                if int(rowsStr if rowsStr else '0') < 10 or int(rowsStr if rowsStr else '0') > 50 or int(colsStr if colsStr else '0') < 10       \
                or int(colsStr if colsStr else '0') > 99 or int(minesStr if minesStr else '0') < 1                                              \
                or int(minesStr if minesStr else '0') > int(rowsStr if rowsStr else '0') * int(colsStr if colsStr else '0') - 10:
                    self.screen.blit(messageSurface, (157, 317))
                    self.screen.blit(dimError, (160, 318))
                elif int(tilesizeStr if tilesizeStr else '0') < 15 or int(tilesizeStr if tilesizeStr else '0') > 50:
                    self.screen.blit(messageSurface, (157, 317))
                    self.screen.blit(tilesizeError, (160, 318))
                else:
                    self.numRows, self.numCols, self.numMines, self.tilesize = int(rowsStr), int(colsStr), int(minesStr), int(tilesizeStr)
                    Game.customDifficultyInputted = True
                    return

            # keep updating the keyboard input display
            self.screen.blit(rowsText, rowsRect)
            self.screen.blit(colsText, colsRect)
            self.screen.blit(minesText, minesRect)
            self.screen.blit(tilesizeText, tilesizeRect)
                            
            pygame.display.flip()
            clock.tick(30)



    def keyboardInput(self, string, maximumDigits): # this function determines if what's being typed is ok (then returns it), and detects if the user clicks on a different box
        pygame.event.clear()
        
        while True:
            event = pygame.event.wait()
            if event.type == pygame.QUIT:
                pygame.quit()
                exit()

            elif event.type == pygame.KEYUP:
                if event.key == pygame.K_ESCAPE:
                    self.rowsBoxSelected, self.colsBoxSelected, self.minesBoxSelected, self.tilesizeBoxSelected,    \
                    self.cancelBoxSelected, self.okBoxSelected = False, False, False, False, False, False
                    return string
                # the rows, columns, numMines, and tilesize input boxes allow a maximum of 2, 2, 4, & 2 displayed digits, respectively
                elif pygame.K_1 <= event.key <= pygame.K_9: # a number 1-9 has been typed
                    return string + str(event.key - 48) if len(string) < maximumDigits else string
                elif event.key == pygame.K_0 and string:    # 0 has been typed... only allowed if it's not the first typed number
                    return string + '0' if len(string) < maximumDigits else string
                elif event.key == pygame.K_BACKSPACE:
                    return '  ' + string[:-1]
                
            # check if another box has been clicked on
            if event.type == pygame.MOUSEBUTTONUP:
                    x,y = pygame.mouse.get_pos()
                    pygame.mouse.get_pressed()
                    if event.button == 1:
                        # if one of the 6 boxes is selected, set its Selected variable equal to True, and all other boxes' Selected variable to False
                        if 140 < x < 190 and 45 < y < 70:       # Rows box
                            self.rowsBoxSelected, self.colsBoxSelected, self.minesBoxSelected, self.tilesizeBoxSelected,    \
                            self.cancelBoxSelected, self.okBoxSelected = True, False, False, False, False, False
                        elif 140 < x < 190 and 80 < y < 105:    # Columns box
                            self.rowsBoxSelected, self.colsBoxSelected, self.minesBoxSelected, self.tilesizeBoxSelected,    \
                            self.cancelBoxSelected, self.okBoxSelected = False, True, False, False, False, False
                        elif 140 < x < 190 and 115 < y < 140:   # Mines box
                            self.rowsBoxSelected, self.colsBoxSelected, self.minesBoxSelected, self.tilesizeBoxSelected,    \
                            self.cancelBoxSelected, self.okBoxSelected = False, False, True, False, False, False
                        elif 140 < x < 170 and 150 < y < 175:   # Tile size box
                            self.rowsBoxSelected, self.colsBoxSelected, self.minesBoxSelected, self.tilesizeBoxSelected,    \
                            self.cancelBoxSelected, self.okBoxSelected = False, False, False, True, False, False
                        elif 45 < x < 140 and 285 < y < 315:    # Cancel box
                            self.rowsBoxSelected, self.colsBoxSelected, self.minesBoxSelected, self.tilesizeBoxSelected,    \
                            self.cancelBoxSelected, self.okBoxSelected = False, False, False, False, True, False
                        elif 160 < x < 255 and 285 < y < 315:   # OK box
                            self.rowsBoxSelected, self.colsBoxSelected, self.minesBoxSelected, self.tilesizeBoxSelected,    \
                            self.cancelBoxSelected, self.okBoxSelected = False, False, False, False, False, True
                        elif 175 < x < 190 and 200 < y < 215:   # Power double-click checkbox
                            self.rowsBoxSelected, self.colsBoxSelected, self.minesBoxSelected, self.tilesizeBoxSelected,    \
                            self.cancelBoxSelected, self.okBoxSelected = False, False, False, False, False, False
                            Game.powerDoubleclickEnabled = False if Game.powerDoubleclickEnabled else True
                            pygame.draw.rect(self.screen, (0, 17, 255) if Game.powerDoubleclickEnabled else (255, 255, 255), (178, 203, 9, 9))
                        elif 175 < x < 190 and 224 < y < 239:   # Automatic tile opening checkbox
                            self.rowsBoxSelected, self.colsBoxSelected, self.minesBoxSelected, self.tilesizeBoxSelected,    \
                            self.cancelBoxSelected, self.okBoxSelected = False, False, False, False, False, False
                            Game.autoTileOpeningEnabled = False if Game.autoTileOpeningEnabled else True
                            pygame.draw.rect(self.screen, (0, 17, 255) if Game.autoTileOpeningEnabled else (255, 255, 255), (178, 227, 9, 9))

                        return string



#######    MAIN LOOP    #######
running = True
timer = 0
Game = Gameboard()
menu = Menu()
# load up the start menu and obtain the difficulty the user wants
menu.difficultyMenu()
# create and display the gameboard
Game.newGame(menu.numRows, menu.numCols, menu.numMines, menu.tilesize)

pygame.event.set_allowed([pygame.QUIT, pygame.KEYDOWN, pygame.MOUSEBUTTONUP])
bottomBarFont = pygame.font.SysFont('Lucida Grande', 18)

# THE OPTIONS FOR THE USER ARE: closing out of the window or pressing Esc, (single/double left-clicking)/right-clicking a tile, or clicking on "Change difficulty"
while running:
    for event in pygame.event.get():
        if event.type == pygame.QUIT or (event.type == pygame.KEYDOWN and event.key == pygame.K_ESCAPE):   # user closes window or presses Esc
            running = False

        elif event.type == pygame.MOUSEBUTTONUP:
            x,y = pygame.mouse.get_pos()
            row, col = y // Game.TILESIZE, x // Game.TILESIZE
            pygame.mouse.get_pressed()
            if event.button == 1:
                # check if user clicked on "Change difficulty" box. We will still have access to (x, y) from the main loop
                if int(Game.screenWidth / 2) - 56 < x < int(Game.screenWidth / 2) + 61 and Game.screenHeight - 21 < y < Game.screenHeight - 4:
                    menu.difficultyMenu()
                    Game.resetTiles(Game.numRows, Game.numCols)
                    Game.newGame(menu.numRows, menu.numCols, menu.numMines, menu.tilesize)
                    continue
                
                elif Game.started == False and 0 < y < Game.screenHeight - 25: # game hasn't been started and user clicks on a tile
                    Game.firstClick(row, col)    # first click is important... determines the positions of the mines
                    Game.started = True
                    Game.displayedTimer = 1
                    continue

                Game.mouseClick(row, col, 1)     # single left-click (ALWAYS EXECUTES, DOUBLE CLICK WILL BE SENT AFTER THE INITIAL SINGLE CLICK)
                
                if timer == 0:
                    timer = 1
                elif timer <= 250:
                    Game.mouseClick(row, col, 2) # double left-click (second click happens within 250 milliseconds of first)
                    timer = 0
                    
            elif event.button == 3 and 0 < y < Game.screenHeight - 25: #right-click
                Game.mouseClick(row, col, 3)

    if Game.numTilesRemaining == 0: # if game is won, set numMinesRemaining to 0 to be displayd
        Game.numMinesRemaining = 0

    # correct timer to appropriate time. if it passed 250 ms, it's beyond a double click... reset to 0
    if timer != 0:
        timer += ms
        if timer > 250:
            timer = 0

    if Game.displayedTimer != 0:
        Game.displayedTimer += ms
        
    # displayed timer will have 2 decimal places before 10 seconds, 1 decimal place before 100 seconds, 0 decimals afterwards
    if Game.displayedTimer < 10000:
        gameTime = round(Game.displayedTimer / 1000, 2)
    elif Game.displayedTimer < 100000:
        gameTime = round(Game.displayedTimer / 1000, 1)
    else:
        gameTime = Game.displayedTimer // 1000


    # render the timer and minesRemaining text
    timerText = bottomBarFont.render(str(gameTime) + "   ", True, (34, 34, 34), (200, 200, 210))
    numMinesRemainingText = bottomBarFont.render("   " + str(Game.numMinesRemaining), True, (34, 34, 34), (200, 200, 210))
    # set minesRemaining text to correct location
    numMinesRemainingRect = numMinesRemainingText.get_rect()
    numMinesRemainingRect.right, numMinesRemainingRect.top = Game.screenWidth - 9, Game.screenHeight - 23
    # display both texts onto the bottom bar
    Game.screen.blit(timerText, (7, Game.screenHeight - 23))
    Game.screen.blit(numMinesRemainingText, numMinesRemainingRect)
    

    pygame.display.flip()
    ms = clock.tick(60) # milliseconds since last tick

    if Game.numTilesRemaining == 0: # if game is won, call gameOver() with a gameState of 1
        Game.gameOver(0, 0, 1)

pygame.quit()
exit()
