""" Minesweeper game code """
from tkinter import *
from random import randint
from datetime import datetime


class Minesweeper:
    """ Our game class """

    def __init__(self, tk):
      """ Initialize the game """
      self.tk = tk

      # Setup size & mines
      self.size = 10
      self.selected_mines = 10
      # self.selected_mines = min(self.size ** 2 - 9, 100)

      # Setup images
      self.images = {
        "tile": PhotoImage(file="images/unclicked_tile.png"),
        "mine": PhotoImage(file="images/unclicked_mine_tile.png"),
        "flag": PhotoImage(file="images/flag_tile.png"),
        "clicked_mine": PhotoImage(file="images/clicked_mine_tile.png"),
        "wrong_flag": PhotoImage(file="images/wrong_flag_tile.png"),
        "numbers": []
      }
      for i in range(0, 9):
        self.images["numbers"].append(
          PhotoImage(file="images/num{}_tile.png".format(str(i))))
      self._build_controls()
      self.start()

    def _build_controls(self):
      """Build labels/buttons based on current size, responsive layout."""
      self.frame = Frame(self.tk)
      self.frame.pack()
      self.repeat_timer = "after#0"
      self.time_label = Label(self.frame, text="Time:")
      self.time_label.grid(row=0, column=0, columnspan=self.size, sticky=W)

      self.mine_label = Label(self.frame, text="Mines left:")
      self.mine_label.grid(row=0, column=self.size - 4,
           columnspan=4, sticky=E)

      self.message_label = Label(self.frame, text="", font="none 14 bold")
      self.message_label.grid(row=self.size + 2, column=0, columnspan=self.size, sticky=W)

      # Responsive placement for main buttons
      btn_row = self.size + 3
      btn_width = max(8, self.size // 4)
      self.restart_button = Button(self.frame, text="Restart(R)", command=self.restart)
      self.restart_button.grid(row=btn_row, column=0, columnspan=btn_width, sticky=W)

      self.reload_button = Button(self.frame, text="Reload", command=self.reload)
      self.reload_button.grid(row=btn_row, column=btn_width, columnspan=btn_width, sticky=W)

      # Settings and Quit in a separate row
      control_row = btn_row + 1
      self.settings_button = Button(self.frame, text="Settings", command=self.open_settings)
      self.settings_button.grid(row=control_row, column=0, columnspan=btn_width, sticky=W)

      self.quit_button = Button(self.frame, text="Quit", command=self.tk.destroy)
      self.quit_button.grid(row=control_row, column=btn_width, columnspan=btn_width, sticky=W)

    def open_settings(self):
      """Open dialog to modify grid size and mine count."""
      win = Toplevel(self.tk)
      win.title("Settings")
      Label(win, text="Grid size (Max:35):").grid(row=0, column=0, sticky=W)
      size_entry = Entry(win)
      size_entry.insert(0, str(self.size))
      size_entry.grid(row=0, column=1)
      Label(win, text="Mines (Max:100):").grid(row=1, column=0, sticky=W)
      mines_entry = Entry(win)
      mines_entry.insert(0, str(self.selected_mines))
      mines_entry.grid(row=1, column=1)

      def apply_settings():
        try:
          new_size = int(size_entry.get())
          new_mines = int(mines_entry.get())
        except ValueError:
          return
        new_size = max(5, min(new_size, 35))
        new_mines = max(1, min(new_mines, new_size ** 2 - 9,100))
        win.destroy()
        self.stop = True
        try:
          self.tk.after_cancel(self.repeat_timer)
        except Exception:
          pass
        self.frame.destroy()
        self.size = new_size
        self.selected_mines = new_mines
        self._build_controls()
        self.start()

      Button(win, text="Apply", command=apply_settings).grid(row=2, column=0)
      Button(win, text="Cancel", command=win.destroy).grid(row=2, column=1)

    def start(self):
      """ Start the game """
      # Setting our variables
      self.is_armed = False
      self.clicks = 0
      self.flags = 0
      self.stop = False
      self.reloaded = False

      # Setup time
      self.time = 0
      self.time_label.config(text="Time: {}".format(self.time))

      # Setup mine counter
      self.mine_label.config(text="Mines left: {}"
                   .format(self.selected_mines - self.flags))

      # Bind restart key once
      self.tk.bind("r", lambda _: self.restart())

      # Create the grid
      frame = self.frame
      tile_img = self.images["tile"]
      grid = {}
      for x in range(self.size):
        grid_x = {}
        grid[x] = grid_x
        for y in range(self.size):
          btn = Button(frame, image=tile_img)
          btn.bind("<Button-1>",
               lambda _, xx=x, yy=y: self.left_click(xx, yy, active=True))
          btn.bind("<Button-3>",
               lambda _, xx=x, yy=y: self.right_click(xx, yy))
          btn.grid(row=x + 1, column=y)
          grid_x[y] = {
            "button": btn,
            "is_mine": False,
            "surrounding_mines": 0,
            "is_flagged": False,
            "is_clicked": False,
            "first": False,
            "x": x,
            "y": y
          }
      self.grid = grid

    def restart(self):
      """ Restart the game without rebuilding widgets """
      self.stop = True
      self.tk.after_cancel(self.repeat_timer)
      self.message_label.config(text="")
      try:
        self.game_over_window.destroy()
      except Exception:
        pass

      # Reset state
      self.is_armed = False
      self.clicks = 0
      self.flags = 0
      self.reloaded = False
      self.time = 0
      self.time_label.config(text="Time: {}".format(self.time))
      self.mine_label.config(text="Mines left: {}"
                   .format(self.selected_mines - self.flags))

      # Reset tiles in place
      for x in self.grid:
        for y in self.grid[x]:
          tile = self.grid[x][y]
          tile.update({
            "is_mine": False,
            "surrounding_mines": 0,
            "is_flagged": False,
            "is_clicked": False,
            "first": False
          })
          tile["button"].config(image=self.images["tile"])

      self.stop = False

    def create_mine(self):
        """ Create mines """
        for x in self.grid:
            for y in self.grid[x]:
                # Check the place where the lpayer first click to avoid mines
                if self.grid[x][y]["first"] is True:
                    continue

                # If the mine already exists, continue
                if self.grid[x][y]["is_mine"] is True:
                    continue

                # Distributes the mines with max efficiency
                if randint(0, (self.size ** 2 + 1) //
                           (self.selected_mines) + 1) == 0:
                    self.grid[x][y]["is_mine"] = True
                    # self.grid[x][y]["button"].config(
                    # image=self.images["mine"])
                    self.mines += 1

                # If the amount of mines is met, return
                if self.mines == self.selected_mines:
                    return

    def check_mines(self):
        """ Check surrounding mines """
        for x in self.grid:
            for y in self.grid[x]:

                # If it was mine continue
                if self.grid[x][y]["is_mine"] is True:
                    continue

                # Check surrounding mines
                for i in range(-1, 2):
                    for j in range(-1, 2):
                        # if out of boundries top and side
                        if x + i < 0 or y + j < 0:
                            continue

                        # if out of boundries bot and side
                        if x + i > self.size - 1 or y + j > self.size - 1:
                            continue

                        if self.grid[x + i][y + j]["is_mine"] is True:
                            self.grid[x][y]["surrounding_mines"] += 1
                # self.grid[x][y]["button"].config(
                    # image=self.images["numbers"]
                    # [self.grid[x][y]["surrounding_mines"]])

    def left_click(self, x, y, active=False):
        """ Left click """
        if self.stop:
            return
        if self.is_armed is False:
            # Create mines in the grid
            self.mines = 0
            for i in range(-1, 2):
                for j in range(-1, 2):
                    # if out of boundries top and side
                    if x + i < 0 or y + j < 0:
                        continue

                    # if out of boundries bot and side
                    if x + i > self.size - 1 or y + j > self.size - 1:
                        continue

                    self.grid[x + i][y + j]["first"] = True
            while True:
                # forever loop until the number is met
                self.create_mine()
                if self.mines == self.selected_mines:
                    break
            self.is_armed = True
            self.timer()

            # Check surrounding mines
            self.check_mines()

        if self.reloaded is True:
            self.reloaded = False
            self.timer()
        if self.grid[x][y]["is_flagged"] is True:
            return
        
        if self.grid[x][y]["is_clicked"] is True :
            if active is False:
                return
            # if the tile it already clicked, click the surrounding tiles if the amount of flags around it is equal to the number on the tile
            flags = 0
            for i in range(-1, 2):
                for j in range(-1, 2):
                    # if out of boundries top and side
                    if x + i < 0 or y + j < 0:
                        continue

                    # if out of boundries bot and side
                    if x + i > self.size - 1 or y + j > self.size - 1:
                        continue

                    if self.grid[x + i][y + j]["is_flagged"] is True:
                        flags += 1
            if flags == self.grid[x][y]["surrounding_mines"]:
                self.clear_surr_active(x, y)
            return

        elif self.grid[x][y]["is_mine"] is True:
            self.grid[x][y]["button"].config(
                image=self.images["clicked_mine"])
            self.grid[x][y]["is_clicked"] = True
            self.game_over(False)

        elif self.grid[x][y]["surrounding_mines"] == 0:
            self.grid[x][y]["button"].config(
                image=self.images["numbers"][0])
            self.grid[x][y]["is_clicked"] = True
            self.clicks += 1
            if self.clicks == (self.size ** 2 - self.mines):
                self.game_over(True)
            self.clear_surr(x, y)

        else:
            self.grid[x][y]["button"].config(
                image=self.images["numbers"]
                [self.grid[x][y]["surrounding_mines"]])
            self.grid[x][y]["is_clicked"] = True
            self.clicks += 1
            if self.clicks == (self.size ** 2 - self.mines):
                self.game_over(True)

    def clear_surr(self, x, y):
        """ Clear surrounding tiles """
        for i in range(-1, 2):
            for j in range(-1, 2):
                # if out of boundries top and side
                if x + i < 0 or y + j < 0:
                    continue

                # if out of boundries bot and side
                if x + i > self.size - 1 or y + j > self.size - 1:
                    continue

                # if self.grid[x + i][y + j]["surrounding_mines"] == 0:
                self.left_click(x + i, y + j)

    def right_click(self, x, y):
        """ Right click """
        if self.stop:
            return
        if self.grid[x][y]["is_clicked"] is True:
            return

        if self.grid[x][y]["is_flagged"] is False:
            self.grid[x][y]["button"].config(image=self.images["flag"])
            self.grid[x][y]["is_flagged"] = True
            self.flags += 1
            self.mine_label.config(text="Mines left: {}"
                                   .format(self.selected_mines - self.flags))

        else:
            self.grid[x][y]["button"].config(image=self.images["tile"])
            self.grid[x][y]["is_flagged"] = False
            self.flags -= 1
            self.mine_label.config(text="Mines left: {}"
                                   .format(self.selected_mines - self.flags))

    def game_over(self, result):
        """ Game over """
        self.stop = True
        self.tk.after_cancel(self.repeat_timer)
        self.time_label.config(text="Time: {}".format(self.time / 10))
        for x in self.grid:
            for y in self.grid[x]:

                # Show unflagged mines
                if self.grid[x][y]["is_mine"] is True\
                        and self.grid[x][y]["is_clicked"] is False:
                    if self.grid[x][y]["is_flagged"] is False:
                        self.grid[x][y]["button"].config(
                            image=self.images["mine"])

                # Show wrong flags
                if self.grid[x][y]["is_flagged"] is True:
                    if self.grid[x][y]["is_mine"] is False:
                        self.grid[x][y]["button"].config(
                            image=self.images["wrong_flag"])

        if result is True:
            title = "Game Over, You Win!"
            color = "green"
        else:
            title = "Game Over, You Lose!"
            color = "red"
        # Change the text in the message box label
        self.message_label.config(text=title, fg=color)

    def reload(self):
        """ Reload the same game """
        try:
            self.game_over_window.destroy()
        except Exception:
            pass
        self.clicks = 0
        for x in self.grid:
            for y in self.grid[x]:
                self.grid[x][y]["button"].config(
                                     image=self.images["tile"])
                self.grid[x][y]["is_flagged"] = False
                self.grid[x][y]["is_clicked"] = False
        self.reloaded = True
        self.stop = False
        self.tk.after_cancel(self.repeat_timer)
        self.time = 0
        self.time_label.config(text="Time: {}".format(self.time))
        self.flags = 0
        self.mine_label.config(text="Mines left: {}"
                               .format(self.selected_mines - self.flags))
        self.message_label.config(text="")

    def timer(self):
        """ Timer for the game """
        self.time += 1
        self.time_label.config(text="Time: {}".format(self.time / 10))
        self.repeat_timer = self.tk.after(100, self.timer)

    def clear_surr_active(self, x, y):
        """ Clear surrounding tiles if the amount of flags around it is equal to the number on the tile """
        for i in range(-1, 2):
            for j in range(-1, 2):
                # if out of boundries top and side
                if x + i < 0 or y + j < 0:
                    continue

                # if out of boundries bot and side
                if x + i > self.size - 1 or y + j > self.size - 1:
                    continue

                if self.grid[x + i][y + j]["is_flagged"] is False:
                    self.left_click(x + i, y + j)

if __name__ == "__main__":
    window = Tk()
    window.title("Minesweeper")
    game = Minesweeper(window)
    window.mainloop()
