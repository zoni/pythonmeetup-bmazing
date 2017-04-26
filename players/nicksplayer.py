import logging
from random import choice
from game.moves import UP, DOWN, LEFT, RIGHT
from game.mazefield_attributes import Path, Finish, Wall
from players.player import Player


class NicksPlayer(Player):
    name = "Nick"
    last = None

    def __init__(self):
        self.log = logging.getLogger("player")
        self.moves = []
        self.x = 0
        self.y = 0
        self.marks = {}

    def turn(self, surroundings):
        move = self.determine_move(surroundings)
        self.moves.append(move)
        self.update_position(move)
        return move

    def _to_coords(self, move):
        """
        Return the coordinates of the spot the given move would put us on.
        """
        if move is None:
            return self.x, self.y

        if move == UP:
            return self.x, self.y + 1
        elif move == DOWN:
            return self.x, self.y - 1
        elif move == LEFT:
            return self.x - 1, self.y
        elif move == RIGHT:
            return self.x + 1, self.y
        raise Exception("Unexpected move")

    def update_position(self, move):
        """
        Update our position on the grid after making a move.
        """
        if move is None:
            self.log.debug("Still at (%s, %s)", self.x, self.y)
            return
        self.x, self.y = self._to_coords(move)
        self.log.debug("Now at (%s, %s)", self.x, self.y)
        self.place_mark(self.x, self.y)

    def place_mark(self, x, y):
        """
        Remember this location for later reference.
        """
        key = "%s:%s" % (x, y)
        if key in self.marks:
            self.marks[key] += 1
        else:
            self.marks[key] = 1

    def determine_move(self, surroundings):
        """
        Return the optimal next move to make.
        """
        if Finish in surroundings:
            return self.finish_position(surroundings)
        if len(self.moves) < 1:
            return choice(self.valid_directions(surroundings))

        if self.at_junction(surroundings):
            if self.marks["%s:%s" % (self.x, self.y)] == 1:
                self.log.debug("We're at a new junction, picking a passage at random")
                directions = [d for d in self.valid_directions(surroundings) if d != self.reverse(self.previous_move)]
                return choice(directions)
            elif self.marks["%s:%s" % self._to_coords(self.reverse(self.previous_move))] == 1:
                self.log.debug("Reached previously visited junction via new passage, backtracking")
                return self.start_backtracking()
            else:
                self.log.debug("We're back at a previously visited junction, picking least visited passage at random")
                return self.pick_least_visited_passage_at_junction(surroundings)
        elif self.at_dead_end(surroundings):
            self.log.debug("Dead end - start backtracking")
            return self.start_backtracking()
        else:
            return self.follow_path(surroundings)

        raise Exception("No move taken")

    def pick_least_visited_passage_at_junction(self, surroundings):
        """
        Turn into the passage which has been entered the least amount of times.
        """
        lowest_number = -1
        targets = {}
        for direction in self.valid_directions(surroundings):
            visits = self.marks.get("%s:%s" % self._to_coords(direction), 0)
            targets[visits] = targets.get(visits, []) + [direction]
        return choice(targets[sorted(targets.keys())[0]])

    def follow_path(self, surroundings):
        """
        Return the next move necessary to follow the current path
        up to a junction.
        """
        if self.at_junction(surroundings):
            raise Exception("Shouldn't be called on a junction")
        for direction in self.valid_directions(surroundings):
            if direction == self.reverse(self.previous_move):
                continue
            return direction

    @staticmethod
    def valid_directions(surroundings):
        """
        Return valid directions to go into based on the current position.
        """
        directions = []
        if surroundings.left == Path:
            directions.append(LEFT)
        if surroundings.right == Path:
            directions.append(RIGHT)
        if surroundings.up == Path:
            directions.append(UP)
        if surroundings.down == Path:
            directions.append(DOWN)
        return directions

    @staticmethod
    def at_junction(surroundings):
        """
        Return true if we are currently at a junction point.
        """
        return len([x for x in surroundings if x == Path]) > 2

    def at_dead_end(self, surroundings):
        """
        Return true if we've hit a dead end.
        """
        if self.at_junction(surroundings):
            return False
        if self.follow_path(surroundings) is None:
            return True
        return False

    @staticmethod
    def finish_position(surroundings):
        """
        Return the direction of the finish position (if it is in sight).
        """
        if surroundings.left == Finish:
            return LEFT
        if surroundings.right == Finish:
            return RIGHT
        if surroundings.up == Finish:
            return UP
        if surroundings.down == Finish:
            return DOWN

    @staticmethod
    def reverse(direction):
        """
        Return the reverse of the given direction.
        """
        if direction == UP:
            return DOWN
        elif direction == DOWN:
            return UP
        elif direction == LEFT:
            return RIGHT
        elif direction == RIGHT:
            return LEFT

    def start_backtracking(self):
        """
        Start moving back in the opposite direction.
        """
        return self.reverse(self.previous_move)

    @property
    def previous_move(self):
        """
        Return the direction of the last move taken.
        """
        if len(self.moves) > 0:
            return self.moves[-1]
