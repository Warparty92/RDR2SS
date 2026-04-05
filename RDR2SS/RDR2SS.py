from pathlib import Path
import sys
import tkinter as tk
from tkinter import filedialog, ttk
import customtkinter
import shutil
import os
import subprocess
import filecmp
import linecache
import stat
import time

global selected_save
global save_path
global current_selection
global saves_dir
global launch_game
global game_exe_path
global combo
global target_directory

# Function to get the save path, using the APPDATA environment variable on Windows
def get_save_path():
    # Use the APPDATA environment variable on Windows
    app_data = os.getenv('APPDATA') 
    save_dir = os.path.join(app_data, "RDR2SS", "Saves")
    print(f"Using save directory: {save_dir}")
    # Create the folder if it doesn't exist
    if not os.path.exists(save_dir):
        os.makedirs(save_dir)
    return save_dir

# Use this path for your GUI to read/write files
current_save_path_temp = get_save_path()
current_save_path = Path(current_save_path_temp)

#temporary test
parent_dir = current_save_path.parent
os.chdir(parent_dir)
saves_dir = Path(parent_dir / "Saves")

#load game exe path and game save directory from text files
game_exe_path = linecache.getline(str(parent_dir / "game_exe_data.txt"), 1).strip('\n')
game_save_dir = linecache.getline(str(parent_dir / "game_save_data.txt"), 1).strip('\n')
print(f"loaded game_exe_path: {game_exe_path}")
print(f"loaded game_save_dir: {game_save_dir}")

# Create the main window object
root = tk.Tk()
menubar = tk.Menu(root)

style = ttk.Style(root)
root.style = style
style.theme_use('alt')

#get exe dirrectory
if getattr(sys, 'frozen', False):
    # Running as compiled executable
    script_dir = os.path.dirname(sys.executable)
else:
    # Running as normal python script
    script_dir = os.path.dirname(os.path.abspath(__file__))

def resource_path(relative_path):
    """ Get absolute path to resource, works for dev and for PyInstaller """
    try:
        # PyInstaller creates a temp folder and stores path in _MEIPASS
        base_path = sys._MEIPASS
    except Exception:
        base_path = os.path.abspath(".")

    return os.path.join(base_path, relative_path)

# Set window title and size
root.title("RDR2 Save Selector")
root.geometry("400x100")
root.resizable(False, False)
icon_path = resource_path("RDR2SS.ico")
root.iconbitmap(icon_path)

def load_save():
    save_folder = filedialog.askdirectory(title="Select RDR2 Save")
    save_name = os.path.basename(save_folder)
    if save_folder:
        print(f"Loading save folder: {save_folder}")
        shutil.copytree(save_folder, f"{saves_dir}\\{save_name}", dirs_exist_ok=True)
        refresh_saves()

def locate_game_save_dir():
    game_save_dir = filedialog.askdirectory(title="Select RDR2 Game Save Directory")
    if game_save_dir:
        print(f"Selected game save directory: {game_save_dir}")
        Path(saves_dir.parent / "game_save_data.txt").write_text(game_save_dir)
        print(f"loaded game_save_dir: {game_save_dir}")

#locate and save the path to the game executable
def load_game_exe():
    game_exe_path = filedialog.askopenfilename(title="Select RDR2 Game Executable", filetypes=[("Executable Files", "*.exe")])
    if game_exe_path:
        print(f"Selected game executable: {game_exe_path}")
        Path(saves_dir.parent / "game_exe_data.txt").write_text(game_exe_path)
        print(f"loaded game_exe_path: {game_exe_path}")

#settings menu parameters
settings_menu = tk.Menu(menubar, tearoff=0)
settings_menu.add_command(label="Settings", command=lambda: print("Settings menu clicked"))

#File menu parameters
file_menu = tk.Menu(menubar, tearoff=0)
file_menu.add_command(label="Load Save", command=load_save)
file_menu.add_separator()
file_menu.add_command(label="Select Game Exe", command=load_game_exe)
file_menu.add_command(label="Select Game Save Directory", command=locate_game_save_dir)
file_menu.add_separator()
file_menu.add_command(label="Exit", command=root.quit)

# Add the file menu to the menubar
menubar.add_cascade(label="File", menu=file_menu)
root.config(menu=menubar)

#create the string variable to hold the loaded save files
if not saves_dir.exists():
    saves_dir.mkdir()
    saves_list = [f.name for f in saves_dir.iterdir() if f.is_dir()]
else:
    saves_list = [f.name for f in saves_dir.iterdir() if f.is_dir()]

#function to refresh the combo box with the loaded save files
def refresh_saves():
    global saves_list
    saves_list = [f.name for f in saves_dir.iterdir() if f.is_dir()]
    combo['values'] = saves_list

#create a combo box to display the loaded save file
combo = ttk.Combobox(root, values=saves_list)
combo.place(x=50, y=25) 

#Launch game with the selected save file
def launch_game():
    selected_save = combo.get()
    print(selected_save)
    print({combo.get()})
    if selected_save:
        global save_path
        save_path = Path(f"{saves_dir}/{selected_save}")
        if save_path.exists():
            compare_saves(game_save_dir, saves_dir, Path(f"{game_save_dir}/{selected_save}"))
            print(f"Launching game with save: {selected_save}")
            subprocess.run(game_exe_path)
            compare_saves(game_save_dir, saves_dir, save_path)
        else:
            print("Selected game file does not exist.")
    else:
        print("No save file selected.")


#compare the save files in the game save directory and the program save directory
#If they are the same, compare the modification dates and copy the newer one to the older one
def compare_saves(reference_directory, target_directorys, save_path):
    
    os.makedirs(Path(reference_directory), exist_ok=True)
    
    # 1. Get the single filename from the reference folder
    ref_files = os.listdir(reference_directory)
    target_directory = os.path.join(target_directorys, combo.get())
    print(f"{target_directory}, {combo.get()}")

    if not ref_files:
        print("The reference folder is empty!")
        clean_and_sync_saves(target_directory, save_path)
        print(f"Copied previous save from {save_path} to {target_directory}.")
    else:
        ref_name = ref_files[0]
        print(f"Reference file identified as: {ref_name}")

        # 2. Get all names in the target directory
        target_files = os.listdir(target_directory)

        # 3. Check for the match
        if ref_name in target_files:
            print(f"SUCCESS: '{ref_name}' was found in the target directory.")
            mtime_ref = os.path.getmtime(os.path.join(reference_directory, ref_name))
            mtime_target = os.path.getmtime(os.path.join(target_directory, ref_name))
            if mtime_ref > mtime_target:
                clean_and_sync_saves(reference_directory,target_directory)
                print(f"'{ref_name}' in the target directory was older. Copied from reference.")
                return
            elif mtime_target > mtime_ref:
                clean_and_sync_saves(target_directory, reference_directory)
                print(f"'{ref_name}' in the reference directory was older. Copied from target.")
                return
        else:
            print(f"FAILED: No file named '{ref_name}' exists in the target directory.")
            temp = Path(reference_directory) / combo.get()
            clean_and_sync_saves(target_directory, temp)
            print(f"Copied '{combo.get()}' from target to reference directory.")
            return


    #Walks through src_root, creates folders in dst_root named after 
    #the parent folders, and copies the files into them.
def force_delete_readonly(func, path, _):
    """Force deletes read-only files during rmtree."""
    os.chmod(path, stat.S_IWRITE)
    func(path)

def clean_and_sync_saves(src_root, dst_root):
    # 1. COMPLETELY WIPE the destination folder first
    os.makedirs(src_root, exist_ok=True)
    os.makedirs(dst_root, exist_ok=True)
    print(f"Preparing to wipe and sync from '{src_root}' to '{dst_root}'...")

    print(f"Wiping: {game_save_dir}")
    try:
        # onerror handles read-only files automatically
        shutil.rmtree(game_save_dir, onerror=force_delete_readonly)
        # Short pause to let Windows "release" the folder
        time.sleep(0.5) 
    except Exception as e:
        print(f"Warning: Could not fully wipe folder. Error: {e}")
    # 2. Recreate the base destination
    os.makedirs(Path(game_save_dir), exist_ok=True)
    print(f"recreated base destination: {dst_root}")

    for item in os.listdir(src_root): # 3. Walk through the source folder and copy everything to the destination
        src_item = os.path.join(src_root, item)
        dst_item = os.path.join(dst_root, item)
        os.makedirs(os.path.dirname(dst_item), exist_ok=True)  # Ensure parent directories exist
        print(f"Processing item: {src_item} -> {dst_item}")

        if os.path.isdir(src_item):
            print(f"Copying directory: {src_item} to {dst_item}")
            shutil.copytree(src_item, dst_item)
        else:
            print(f"Copying file: {src_item} to {dst_item}")
            shutil.copy2(src_item, dst_item.replace("\\", "/"))  # Ensure consistent path separators

#Launch button
launch = ttk.Button(
    root, 
    text="Launch Game", 
    command=launch_game
)
launch.place(x=200, y=25)

# Keep the window open
root.mainloop()