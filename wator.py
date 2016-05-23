#!/usr/bin/python3
#
#    This program is free software: you can redistribute it and/or modify
#    it under the terms of the GNU General Public License as published by
#    the Free Software Foundation, either version 3 of the License, or
#    (at your option) any later version.
#
#    This program is distributed in the hope that it will be useful,
#    but WITHOUT ANY WARRANTY; without even the implied warranty of
#    MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the
#    GNU General Public License for more details.
#
#    You should have received a copy of the GNU General Public License
#    along with this program.  If not, see <http://www.gnu.org/licenses/>.
#

import pygame
import random
import argparse
from pygame.locals import *

# Some constants
GREEN = (0, 255, 0)
BLUE = (0, 0, 255)
BLACK = (0, 0, 0)
WHITE = (255, 255, 255)

EMPTY = 0
FISH = 1
SHARK = 2

DIR_UP = 0
DIR_RIGHT = 1
DIR_DOWN = 2
DIR_LEFT = 3

# Init random and pygame
random.seed()
pygame.init()


# Small function to generate an empty map
def clearmap(maprect):
    worldmap = []
    for j in range(maprect[0]):
        worldmap.append([])
        for i in range(maprect[1]):
            worldmap[j].append(0)
    return worldmap


# -------------------------------------------
# Creature class
# -------------------------------------------
# The creature is a subclass of fish and sharks
# it includes definitions on how to move, draw and grow
class Creature(object):
    # init the creature
    def __init__(self, race, color, breedtime, width, height):
        self.x = 0
        self.y = 0
        self.race = race
        self.color = color
        self.breedtime = breedtime
        self.age = 0
        self.width = width
        self.height = height

    # set the position on the map
    def locate(self, worldmap, pos):
        self.x = pos[0]
        self.y = pos[1]

        if worldmap[self.x][self.y] != EMPTY:
            return False
        else:
            worldmap[self.x][self.y] = self.race
            return True

    # Draw a rectangle on the surface in the creature's color
    def draw(self, surface, zoom):
        pygame.draw.rect(surface, self.color,
                         (self.x * zoom, self.y * zoom, zoom, zoom))

    # returns the position after moving in direction
    def getpos(self, direction):
        if direction == DIR_UP:
            newy = self.y - 1
            newx = self.x
        elif direction == DIR_RIGHT:
            newx = self.x + 1
            newy = self.y
        elif direction == DIR_DOWN:
            newy = self.y + 1
            newx = self.x
        elif direction == DIR_LEFT:
            newx = self.x - 1
            newy = self.y

        # if the creature goes to top/bottom/left/right, move to other edge
        if newx == -1:
            newx = self.width - 1
        elif newx == self.width:
            newx = 0

        if newy == -1:
            newy = self.height - 1
        elif newy == self.height:
            newy = 0

        return (newx, newy)

    # moves the creature to the new position and returns (in case of the shark)
    # whether it has eaten a fish
    def swim(self, worldmap, direction):
        newpos = self.getpos(direction)

        oldfield = worldmap[newpos[0]][newpos[1]]

        # set the new position in the map
        worldmap[newpos[0]][newpos[1]] = self.race
        worldmap[self.x][self.y] = EMPTY
        self.x = newpos[0]
        self.y = newpos[1]

        return oldfield

    # returns the creature at the position of the field in direction
    def check(self, worldmap, direction):
        newpos = self.getpos(direction)

        return worldmap[newpos[0]][newpos[1]]

    # advance it in age and return true if it's old enough to breed
    def grow(self):
        self.age += 1
        if self.age == self.breedtime:
            self.age = 0
            return True
        else:
            return False


# ----------------------------------------------------------------------
# Fish class
# ----------------------------------------------------------------------
# The fish class is part of the world
# it defines the corpus' definitions for a fish
class Fish(Creature):
    # swim checks for empty fields
    def swim(self, worldmap):
        # get a list of all empty fields
        normdir = []
        for j in range(4):
            if super(Fish, self).check(worldmap, j) == EMPTY:
                normdir.append(j)

        # and choose a random direction
        if len(normdir) == 0:
            # the fish cannot move
            return False
        else:
            direction = random.choice(normdir)
        super(Fish, self).swim(worldmap, direction)

        return True

    # check if the fish was eaten by a shark
    def checkeaten(self, worldmap):
        # in this case there is 'SHARK' instead of 'FISH'
        # at the fish's position in the map
        return worldmap[self.x][self.y] == SHARK


# -----------------------------------------------------------------
# Shark class
# -----------------------------------------------------------------
# The shark class is part of the world
# it defines the corpus' definitions for a shark
class Shark(object):
    def __init__(self, width, height, color, energy, foodenergy, breedtime):
        self.corpus = Creature(SHARK, color, breedtime, width, height)
        self.energy = energy
        self.foodenergy = foodenergy

    def locate(self, worldmap, pos):
        return self.corpus.locate(worldmap, pos)

    def draw(self, surface, zoom):
        self.corpus.draw(surface, zoom)

    # swim to a fish or an empty field
    def swim(self, worldmap):
        # make a list of fields with fish
        fishdir = []
        # and another with empty ones
        normdir = []
        for j in range(4):
            if self.corpus.check(worldmap, j) == FISH:
                fishdir.append(j)
            elif self.corpus.check(worldmap, j) == EMPTY:
                normdir.append(j)

        # if there are fish around, get a random one
        if len(fishdir) != 0:
            direction = random.choice(fishdir)
        elif len(normdir) == 0:
            # there is no possible move
            return False
        else:
            # otherwise just swim to an empty field
            direction = random.choice(normdir)

        if self.corpus.swim(worldmap, direction) == FISH:
            # there was a fish, yummy
            self.energy += self.foodenergy

        return True

    # higher level growing: does the shark have enough energy left?
    def grow(self):
        canbreed = self.corpus.grow()
        self.energy -= 1
        if self.energy == 0:
            # RIP
            return -1
        return canbreed


# ------------------------------------------
# World class
# ------------------------------------------
# The world class includes all fish and sharks
# it defines the environment
class World(object):
    def __init__(self, worldrect, fishcolor, sharkcolor, backgroundcolor,
                 fishbreed, sharkbreed, sharkenergy, foodenergy, zoom):
        self.width = worldrect[0]
        self.height = worldrect[1]
        self.zoom = zoom

        self.fishcolor = fishcolor
        self.sharkcolor = sharkcolor
        self.backgroundcolor = backgroundcolor

        self.fishbreed = fishbreed
        self.sharkbreed = sharkbreed

        self.sharkenergy = sharkenergy
        self.foodenergy = foodenergy

        self.fish = []
        self.sharks = []

        # get a random number of fish and sharks
        numfish = random.randint(1, self.width * self.height / 2)
        numsharks = random.randint(1, self.width * self.height / 2)

        # create an empty map
        self.world = clearmap(worldrect)

        for j in range(numfish):
            # bear a fish
            newfish = Fish(race=FISH, color=self.fishcolor,
                           breedtime=self.fishbreed,
                           width=self.width, height=self.height)

            # and locate it on the map
            pos = (random.randint(0, self.width - 1),
                   random.randint(0, self.height - 1))
            if newfish.locate(self.world, pos) == True:
                self.fish.append(newfish)

        for j in range(numsharks):
            # bear a shark
            newshark = Shark(color=self.sharkcolor, energy=self.sharkenergy,
                             foodenergy=self.foodenergy,
                             breedtime=self.sharkbreed,
                             width=self.width, height=self.height)

            # locate it on the map
            pos = (random.randint(0, self.width - 1),
                   random.randint(0, self.height - 1))
            if newshark.locate(self.world, pos) == True:
                self.sharks.append(newshark)

    # drawing function
    def draw(self, surface):
        # draw the map to the screen
        for k in range(self.height):
            for j in range(self.width):
                mytype = self.world[j][k]

                if mytype == EMPTY:
                    color = self.backgroundcolor
                elif mytype == FISH:
                    color = self.fishcolor
                else:
                    color = self.sharkcolor

                pygame.draw.rect(surface, color,
                                 (j * self.zoom, k * self.zoom,
                                  self.zoom, self.zoom))

    # play another round
    def update(self):
        # holds all new fish and sharks
        allnewfish = []
        allnewsharks = []

        for fish in self.fish:
            if fish.checkeaten(self.world) == True:
                # a shark has eaten our fish
                self.fish.remove(fish)
                self.world[fish.x][fish.y] = EMPTY
            else:
                if fish.grow() == True:
                    # a new fish is born
                    newfish = Fish(race=FISH, color=self.fishcolor,
                                   breedtime=self.fishbreed, width=self.width,
                                   height=self.height)

                    pos = (fish.x, fish.y)
                    if fish.swim(self.world) == True:
                        # move the old fish

                        newfish.locate(self.world, pos)
                        allnewfish.append(newfish)
                else:
                    # fish is not old enough -> just swim away
                    fish.swim(self.world)

        # add new fish to the fishlist
        self.fish.extend(allnewfish)

        for shark in self.sharks:
            state = shark.grow()
            if state == -1:
                # the shark doesn't have enough energy
                self.sharks.remove(shark)
                self.world[shark.corpus.x][shark.corpus.y] = EMPTY
            elif state:
                # a new shark has to be born
                newshark = Shark(color=self.sharkcolor,
                                 energy=self.sharkenergy,
                                 foodenergy=self.foodenergy,
                                 breedtime=self.sharkbreed,
                                 width=self.width,
                                 height=self.height)

                pos = (shark.corpus.x, shark.corpus.y)
                if shark.swim(self.world) == True:
                    # swim away, old fish
                    newshark.locate(self.world, pos)
                    allnewsharks.append(newshark)
            else:
                # nothing happend, just move
                shark.swim(self.world)

        # add new sharks
        self.sharks.extend(allnewsharks)


def parse_arguments():
    # Parse arguments
    parser = argparse.ArgumentParser(description="Wa-Tor Implementation")
    parser.add_argument('-w', '--width', help="Width of the world",
                        default=100, type=int)
    parser.add_argument('-v', '--height', help="Height of the world",
                        default=50, type=int)
    parser.add_argument('-f', '--fishcolor', help="Color of the fish",
                        default='blue', type=str)
    parser.add_argument('-s', '--sharkcolor', help="Color of the shark",
                        default='green', type=str)
    parser.add_argument('-a', '--backgroundcolor', help="Background color",
                        default='black', type=str)
    parser.add_argument('-b', '--fishbreed',
                        help="Number of rounds that the fish need to breed",
                        default=4, type=int)
    parser.add_argument('-c', '--sharkbreed',
                        help="Number of rounds that the sharks need to breed",
                        default=5, type=int)
    parser.add_argument('-e', '--sharkenergy',
                        help="Number of energy points the sharks get at the " +
                        "beginning",
                        default=3, type=int)
    parser.add_argument('-g', '--foodenergy',
                        help="Number of energy points a shark earns when it " +
                        "eats a fish",
                        default=1, type=int)
    parser.add_argument('-z', '--zoom', help="Zoomimg factor", default=10,
                        type=int)
    args = parser.parse_args()
    return args


def game_loop(args):
    # Check arguments
    if args.zoom < 1 or args.zoom > 100:
        print("Error: --zoom invalid")
        exit(0)
    if args.width < 0 or args.width > 1000 \
            or args.height < 0 or args.height > 1000:
        print("Error: --world invalid")
        exit(0)
    if args.fishbreed < 1 or args.fishbreed > 1000:
        print("Errof: --fishbreed invalid")
        exit(0)
    if args.sharkbreed < 1 or args.sharkbreed > 1000:
        print("Error: --sharkbreed invalid")
        exit(0)
    if args.sharkenergy < 1 or args.sharkenergy > 1000:
        print("Error: --sharkenergy invalid")
        exit(0)
    if args.foodenergy < 0 or args.foodenergy > 1000:
        print("Error: --foodenergy invalid")
        exit(0)

    # init the world
    world = World((args.width, args.height),
                  fishcolor=Color(args.fishcolor),
                  sharkcolor=Color(args.sharkcolor),
                  backgroundcolor=Color(args.backgroundcolor),
                  fishbreed=args.fishbreed,
                  sharkbreed=args.sharkbreed,
                  sharkenergy=args.sharkenergy,
                  foodenergy=args.foodenergy,
                  zoom=args.zoom)

    # init the window
    windowsize = (args.width * args.zoom, args.height * args.zoom)
    display = pygame.display.set_mode(windowsize)
    pygame.display.set_caption("Wa-Tor")

    loop = True
    # main loop
    while loop:
        world.update()
        world.draw(display)
        pygame.display.update()

        for event in pygame.event.get():
            if event.type == QUIT:
                loop = False

if __name__ == '__main__':
    game_loop(parse_arguments())
