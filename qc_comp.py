import argparse
import csv
import json
import os
import tkinter as tk
from tkinter import messagebox
from tkinter import ttk
from PIL import Image, ImageTk

# Constants for QC Observations and Retouch Reasons
QC_OBSERVATIONS_OPTIONS = [
    "Clipping", "Shadow", "Perspective", "Background", "LP missing",
    "LP alignment", "Background", "Haziness"
]
RETOUCH_REASONS_OPTIONS = QC_OBSERVATIONS_OPTIONS.copy()

CSV_HEADERS = [
    'WeekNum', 'Date', 'Namespace', 'Filename', 'QC Decision',
    'QC Observations', 'Retouch Quality', 'Retouch Observations', 'Next Action'
]

def get_image_files(root_directory, date, namespace, week_num):
    image_files = []
    try:
        week_dir = os.path.join(root_directory, week_num)
        date_dir = os.path.join(week_dir, date)
        ns_dir = os.path.join(date_dir, namespace)

        if not os.path.isdir(ns_dir):
            print(f"Namespace directory '{ns_dir}' does not exist.")
            return image_files

        for file in os.listdir(ns_dir):
            if file.lower().endswith('.jpeg'):
                file_path = os.path.join(ns_dir, file)
                if os.path.isfile(file_path):
                    image_files.append(file_path)

    except Exception as e:
        print(f"Error retrieving image files from directory '{ns_dir}': {e}")

    return sorted(image_files)

def load_existing_csv(output_dir, week_num, date, namespace):
    csv_path = os.path.join(output_dir, f"{week_num}-{date}-{namespace}.CSV")
    existing_data = {}
    if os.path.exists(csv_path):
        try:
            with open(csv_path, mode='r', newline='', encoding='utf-8') as file:
                reader = csv.DictReader(file)
                for row in reader:
                    key = row['Filename']
                    existing_data[key] = row
        except Exception as e:
            print(f"Error loading CSV file '{csv_path}': {e}")
    return existing_data

class ImageCheckerApp:
    def __init__(self, root, image_list, csv_data, week_num, date, namespace, output_dir):
        self.root = root
        self.root.title("Image QC Checker")
        self.root.state('zoomed')  # Maximize window

        self.image_list = image_list
        self.csv_data = csv_data
        self.week_num = week_num
        self.date = date
        self.namespace = namespace
        self.output_dir = output_dir

        self.total_images = len(self.image_list)
        self.current_image_index = 0

        self.results = {filename: row for filename, row in self.csv_data.items()}
        self.temp_json_file = os.path.join(output_dir, f"{week_num}-{date}-{namespace}.json")
        self.load_temp_data()

        # Initialize variables
        self.qc_decision = tk.StringVar()
        self.retouch_quality = tk.StringVar()
        self.next_action = tk.StringVar()

        self.qc_obs_vars = []  # Initialize the list
        self.retouch_obs_vars = []  # Initialize the list

        self.create_ui()

        if self.total_images > 0:
            self.load_image()
        else:
            tk.messagebox.showwarning("No Images", "No images found to process.")
            self.root.destroy()

    def create_ui(self):
        self.main_frame = tk.Frame(self.root)
        self.main_frame.pack(fill=tk.BOTH, expand=True)

        self.image_frame = tk.Frame(self.main_frame)
        self.image_frame.pack(fill=tk.BOTH, expand=True, padx=20, pady=10)

        self.image_label = tk.Label(self.image_frame)
        self.image_label.pack(expand=True)

        self.controls_frame = tk.Frame(self.main_frame)
        self.controls_frame.pack(fill=tk.X, padx=20, pady=10)

        self.left_controls = tk.Frame(self.controls_frame)
        self.left_controls.pack(side=tk.LEFT, fill=tk.BOTH, expand=True, padx=10)

        self.right_controls = tk.Frame(self.controls_frame)
        self.right_controls.pack(side=tk.RIGHT, fill=tk.BOTH, expand=True, padx=10)

        qc_right_rb = tk.Radiobutton(self.left_controls, text="Right", variable=self.qc_decision, value="Right")
        qc_right_rb.pack(side=tk.LEFT, padx=10)

        qc_wrong_rb = tk.Radiobutton(self.left_controls, text="Wrong", variable=self.qc_decision, value="Wrong")
        qc_wrong_rb.pack(side=tk.LEFT, padx=10)

        for obs in QC_OBSERVATIONS_OPTIONS:
            var = tk.BooleanVar()
            cb = tk.Checkbutton(self.left_controls, text=obs, variable=var)
            cb.pack(side=tk.LEFT, padx=5)  # Place checkboxes horizontally
            self.qc_obs_vars.append((obs, var))

        retouch_good_rb = tk.Radiobutton(self.right_controls, text="Good", variable=self.retouch_quality, value="Good")
        retouch_good_rb.pack(side=tk.LEFT, padx=10)

        retouch_bad_rb = tk.Radiobutton(self.right_controls, text="Bad", variable=self.retouch_quality, value="Bad")
        retouch_bad_rb.pack(side=tk.LEFT, padx=10)

        for obs in RETUCH_REASONS_OPTIONS:
            var = tk.BooleanVar()
            cb = tk.Checkbutton(self.right_controls, text=obs, variable=var)
            cb.pack(side=tk.LEFT, padx=5)  # Place checkboxes horizontally
            self.retouch_obs_vars.append((obs, var))

        next_ignore_rb = tk.Radiobutton(self.right_controls, text="Ignore", variable=self.next_action, value="Ignore")
        next_ignore_rb.pack(side=tk.LEFT, padx=10)

        next_retouch_rb = tk.Radiobutton(self.right_controls, text="Retouch", variable=self.next_action,
                                         value="Retouch")
        next_retouch_rb.pack(side=tk.LEFT, padx=10)

        next_retakes_rb = tk.Radiobutton(self.right_controls, text="Retake", variable=self.next_action, value="Retake")
        next_retakes_rb.pack(side=tk.LEFT, padx=10)

        # Progress Bar
        #self.progress_label = tk.Label(self.main_frame, text="Progress:")
        #self.progress_label.pack(anchor=tk.W)
#
        #self.progress_var = tk.DoubleVar()
        #self.progress_bar = ttk.Progressbar(self.main_frame, variable=self.progress_var, maximum=self.total_images)
        #self.progress_bar.pack(fill=tk.X, padx=20, pady=10)
#
        # 3. Bottom frame for the buttons (occupying the last part of the screen)
        self.bottom_frame = tk.Frame(self.main_frame)
        self.bottom_frame.pack(side=tk.BOTTOM, fill=tk.X, pady=20)

        self.prev_button = tk.Button(self.bottom_frame, text="Previous", command=self.show_previous_image)
        self.prev_button.pack(side=tk.LEFT, padx=10)

        self.save_button = tk.Button(self.bottom_frame, text="Save", command=self.save_data)
        self.save_button.pack(side=tk.LEFT, padx=10)

        self.next_button = tk.Button(self.bottom_frame, text="Next", command=self.show_next_image)
        self.next_button.pack(side=tk.LEFT, padx=10)

        # Bind keys for shortcuts
        self.root.bind("<q>", self.focus_qc_section)
        self.root.bind("<r>", self.focus_retouch_section)
        self.root.bind("<a>", self.select_right)
        self.root.bind("<d>", self.select_wrong)
        self.root.bind("<1>", self.select_option)
        self.root.bind("<2>", self.select_option)
        self.root.bind("<3>", self.select_option)
        self.root.bind("<4>", self.select_option)
        self.root.bind("<5>", self.select_option)
        self.root.bind("<6>", self.select_option)
        self.root.bind("<Left>", self.show_previous_image)
        self.root.bind("<Right>", self.show_next_image)

        self.root.bind("<Escape>", self.quit_application)

    # Placeholder functions for key bindings
    def focus_qc_section(self, event=None):
        self.left_controls.focus_set()  # Sets focus to the QC section (left_controls)
        print("Focusing on QC section...")

    def focus_retouch_section(self, event=None):
        self.right_controls.focus_set()
        print("Focusing on Retouch section...")

    def select_right(self, event=None):
        print("Selected Right")

    def select_wrong(self, event=None):
        print("Selected Wrong")

    def select_option(self, event=None):
        print("Option selected")

    def load_image(self):
        if self.total_images > 0:
            current_image_path = self.image_list[self.current_image_index]
            try:
                img = Image.open(current_image_path)
                img.thumbnail((1200, 800))  # Resize the image to fit the window
                img_tk = ImageTk.PhotoImage(img)
                self.image_label.config(image=img_tk)
                self.image_label.image = img_tk
                print(f"Image loaded: {current_image_path}")
            except Exception as e:
                print(f"Error loading image {current_image_path}: {e}")
        else:
            print("No images to display.")

    def update_progress_bar(self):
        self.progress_var.set(self.current_image_index + 1)

    def show_previous_image(self, event=None):
        if self.current_image_index > 0:
            self.current_image_index -= 1
            self.load_image()

    def show_next_image(self, event=None):
        if self.current_image_index < self.total_images - 1:
            self.current_image_index += 1
            self.load_image()

    def save_data(self):
        rows = []
        for filename in self.image_list:
            qc_decision = self.qc_decision.get()
            qc_observations = [obs for obs, var in self.qc_obs_vars if var.get()]
            retouch_quality = self.retouch_quality.get()
            retouch_observations = [obs for obs, var in self.retouch_obs_vars if var.get()]
            next_action = self.next_action.get()

            row = {
                'WeekNum': self.week_num,
                'Date': self.date,
                'Namespace': self.namespace,
                'Filename': filename,
                'QC Decision': qc_decision,
                'QC Observations': ", ".join(qc_observations),
                'Retouch Quality': retouch_quality,
                'Retouch Observations': ", ".join(retouch_observations),
                'Next Action': next_action
            }
            rows.append(row)

        # Save the data to CSV and JSON
        csv_file_path = os.path.join(self.output_dir, f"{self.week_num}-{self.date}-{self.namespace}.CSV")
        try:
            with open(csv_file_path, mode='w', newline='', encoding='utf-8') as file:
                writer = csv.DictWriter(file, fieldnames=CSV_HEADERS)
                writer.writeheader()
                writer.writerows(rows)
        except Exception as e:
            print(f"Error saving CSV file '{csv_file_path}': {e}")

        json_data = {
            "week_num": self.week_num,
            "date": self.date,
            "namespace": self.namespace,
            "images": rows
        }

        try:
            with open(self.temp_json_file, 'w') as json_file:
                json.dump(json_data, json_file, indent=4)
        except Exception as e:
            print(f"Error saving JSON file '{self.temp_json_file}': {e}")

        messagebox.showinfo("Success", "Data saved successfully!")

    def load_temp_data(self):
        if os.path.exists(self.temp_json_file):
            try:
                with open(self.temp_json_file, 'r') as json_file:
                    self.temp_data = json.load(json_file)
            except Exception as e:
                print(f"Error loading temp JSON file '{self.temp_json_file}': {e}")
        else:
            self.temp_data = {}

    def quit_application(self, event=None):
        self.root.quit()

def main():
    parser = argparse.ArgumentParser(description="QC Application")
    parser.add_argument("--root", help="Root directory containing the image files")
    parser.add_argument("--output", help="Directory to save the output CSV and JSON files")
    parser.add_argument("--week_num", help="Week number for the current QC session")
    parser.add_argument("--date", help="Date for the current QC session")
    parser.add_argument("--namespace", help="Namespace for the QC session")

    args = parser.parse_args()

    image_files = get_image_files(args.root, args.date, args.namespace, args.week_num)
    existing_data = load_existing_csv(args.output, args.week_num, args.date, args.namespace)

    if image_files:
        root = tk.Tk()
        app = ImageCheckerApp(root, image_files, existing_data, args.week_num, args.date, args.namespace, args.output)
        root.mainloop()
    else:
        print("No image files found.")

if __name__ == "__main__":
    main()
