import tkinter as tk
# Import the AppWindow class from our package
from context_selector.app_window import AppWindow

if __name__ == "__main__":
    # Create the main Tkinter root window
    root = tk.Tk()

    # Create an instance of our application window class,
    # passing the root window to it.
    app = AppWindow(master=root)

    # Start the Tkinter event loop. This makes the window visible
    # and responsive to user interactions.
    root.mainloop()