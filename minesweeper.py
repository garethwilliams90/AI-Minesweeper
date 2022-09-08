from dataclasses import make_dataclass
import itertools
import random
import copy


class Minesweeper():
    """
    Minesweeper game representation
    """

    def __init__(self, height=8, width=8, mines=8):

        # Set initial width, height, and number of mines
        self.height = height
        self.width = width
        self.mines = set()

        # Initialize an empty field with no mines
        self.board = []
        for i in range(self.height):
            row = []
            for j in range(self.width):
                row.append(False)
            self.board.append(row)

        # Add mines randomly
        while len(self.mines) != mines:
            i = random.randrange(height)
            j = random.randrange(width)
            if not self.board[i][j]:
                self.mines.add((i, j))
                self.board[i][j] = True

        # At first, player has found no mines
        self.mines_found = set()

    def print(self):
        """
        Prints a text-based representation
        of where mines are located.
        """
        for i in range(self.height):
            print("--" * self.width + "-")
            for j in range(self.width):
                if self.board[i][j]:
                    print("|X", end="")
                else:
                    print("| ", end="")
            print("|")
        print("--" * self.width + "-")

    def is_mine(self, cell):
        i, j = cell
        return self.board[i][j]

    def nearby_mines(self, cell):
        """
        Returns the number of mines that are
        within one row and column of a given cell,
        not including the cell itself.
        """

        # Keep count of nearby mines
        count = 0

        # Loop over all cells within one row and column
        for i in range(cell[0] - 1, cell[0] + 2):
            for j in range(cell[1] - 1, cell[1] + 2):

                # Ignore the cell itself
                if (i, j) == cell:
                    continue

                # Update count if cell in bounds and is mine
                if 0 <= i < self.height and 0 <= j < self.width:
                    if self.board[i][j]:
                        count += 1

        return count

    def won(self):
        """
        Checks if all mines have been flagged.
        """
        return self.mines_found == self.mines


class Sentence():
    """
    Logical statement about a Minesweeper game
    A sentence consists of a set of board cells,
    and a count of the number of those cells which are mines.
    """

    def __init__(self, cells, count):
        self.cells = set(cells)
        self.count = count

    def __eq__(self, other):
        return self.cells == other.cells and self.count == other.count

    def __str__(self):
        return f"{self.cells} = {self.count}"

    def known_mines(self):
        """
        Returns the set of all cells in self.cells known to be mines.
        """
        # If cells number is the same as the count then definitely a mine there
        # We don't want count to be 0, since cannot have 0 cells around another cell
        if len(self.cells) == self.count and self.count != 0:
            return self.cells
        # Otherwise return the empty set
        else: return set()
                

    def known_safes(self):
        """
        Returns the set of all cells in self.cells known to be safe.
        """
        # We only really know if its safe when the count is == 0
        if self.count == 0:
            return self.cells
        return set()

    def mark_mine(self, cell):
        """
        Updates internal knowledge representation given the fact that
        a cell is known to be a mine.
        """
        # Check to see if cell is in the sentence
        if cell in self.cells:
            # Then update the sentence, to remove cell from sentence
            self.cells.remove(cell)
            self.count -=1
        # Otherwise do nothing

    def mark_safe(self, cell):
        """
        Updates internal knowledge representation given the fact that
        a cell is known to be safe.
        """
        # Check if cell in sentence
        if cell in self.cells:
            self.cells.remove(cell)
        # We don't need to update the count in this case since our knowledge of mines hasn't changed


class MinesweeperAI():
    """
    Minesweeper game player
    """

    def __init__(self, height=8, width=8):

        # Set initial height and width
        self.height = height
        self.width = width

        # Keep track of which cells have been clicked on
        self.moves_made = set()

        # Keep track of cells known to be safe or mines
        self.mines = set()
        self.safes = set()

        # List of sentences about the game known to be true
        self.knowledge = []
        
    # Update the knowledge base when we recieve new information
    def knowledge_update(self):
        while True:
            breaker = True
            
            # Check sentences in knowledge 
            for i in self.knowledge:
                for j in self.knowledge:
                    
                    # Check they're not 0 first 
                    if len(i.cells) != 0 and len(j.cells) != 0:
                        
                        # Gives the difference between the cells and counts to reduce subset of information
                        if i.cells < j.cells:
                            j.cells -= i.cells
                            j.count -= i.count
                            breaker = False
                    # If at least one is 0
                    else:
                        if i in self.knowledge and len(i.cells) == 0:
                            self.knowledge.remove(i)
                        if j in self.knowledge and len(j.cells) == 0:
                            self.knowledge.remove(j)                    
            if breaker:
                break


    def mark_mine(self, cell):
        """
        Marks a cell as a mine, and updates all knowledge
        to mark that cell as a mine as well.
        """
        self.mines.add(cell)
        for sentence in self.knowledge:
            sentence.mark_mine(cell)

    def mark_safe(self, cell):
        """
        Marks a cell as safe, and updates all knowledge
        to mark that cell as safe as well.
        """
        self.safes.add(cell)
        for sentence in self.knowledge:
            sentence.mark_safe(cell)

    def add_knowledge(self, cell, count):
        
        # Add the moves that have been made 
        self.moves_made.add(cell)
        
        # Then we want to mark that cell as a safe cell
        self.mark_safe(cell)

        # Define the cells that are nearby: ± one row or column 
        nearby_cells = set()
        for i in range(cell[0] - 1, cell[0] + 2):
            for j in range(cell[1] - 1, cell[1] + 2):
                
                # Check i falls within the actual board - height and width
                if 0 <= i < self.height and 0 <= j < self.width and (i, j) != cell:
                    # Then just add the cells to the nearby set
                    nearby_cells.add((i, j))  
                          
        # Define nearby cells that we don't yet know
        nearby_unknown = nearby_cells - self.moves_made - self.mines - self.safes
        nearby_unknown_count = count - len(nearby_cells & self.mines)
        
        if len(nearby_unknown) > 0: 
            self.knowledge.append(Sentence(nearby_unknown, nearby_unknown_count))    
            self.knowledge_update()      

        for sentence in self.knowledge:
            self.safes |= sentence.known_safes()
            self.mines |= sentence.known_mines()
        
    def make_safe_move(self):
        """
        Returns a safe cell to choose on the Minesweeper board.
        The move must be known to be safe, and not already a move
        that has been made.

        This function may use the knowledge in self.mines, self.safes
        and self.moves_made, but should not modify any of those values.
        """
        # Check if move hasn't been made already
        for move in self.safes:
            # Can't have already been made and must be a safe move
            if move not in self.moves_made and move in self.safes:
                return move   
        return None
                

    def make_random_move(self):
        """
        Returns a move to make on the Minesweeper board.
        Should choose randomly among cells that:
            1) have not already been chosen, and
            2) are not known to be mines
        """
        # Call this function is make_safe_move isn't possible
        # Lets first create an array of the moves from which we can randomly select
        potential_moves = []
        # Check cell hasn;t been picked yet and we know isn't a mine
        for i in range(self.height):
            for j in range(self.width):
                if (i,j) not in self.moves_made and (i,j) not in self.mines:
                    potential_moves.append((i,j))
        # If we have some moves stored in potential_moves, then we can choose a random one
        if len(potential_moves) != 0:
            return random.choice(potential_moves)
        else: return None
                    

    