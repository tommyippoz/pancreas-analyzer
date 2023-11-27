import configparser
import math
import os
import shutil
import tkinter
from tkinter import font
from csv import DictReader
from tkinter import *
from tkinter import ttk

from tkinter.filedialog import askdirectory
from tkinter.messagebox import showwarning
from tkinter.ttk import Combobox


# Global Variables

# Temporary Folder
TMP_FOLDER = "tmp"

# Output Folder
OUT_FOLDER = "output"

# CSV Data path
CSV_PATH = "./pancreas_data.csv"

# Patient Data
PATIENT_DATA = None


# Support Functions

def read_csv():
    if os.path.exists(CSV_PATH):
        with open(CSV_PATH, 'r') as f:
            dict_reader = DictReader(f, skipinitialspace=True)
            list_of_dict = []
            for item in list(dict_reader):
                if len(item['id'].strip()) > 0:
                    item['distance'] = 0.0
                    list_of_dict.append(item)
            return list_of_dict
    return None


def check_number(number):
    if number is not None and isinstance(number, str):
        number = number.strip()
        if str.isdigit(number) or len(number) == 0 or number == '.':
            return True
    return False


def clear_folder(folder):
    for filename in os.listdir(folder):
        file_path = os.path.join(folder, filename)
        try:
            if os.path.isfile(file_path) or os.path.islink(file_path):
                os.unlink(file_path)
            elif os.path.isdir(file_path):
                shutil.rmtree(file_path)
        except Exception as e:
            print('Failed to delete %s. Reason: %s' % (file_path, e))

def l2_norm(arr):
    l2 = 0.0
    for item in arr:
        l2 += item*item
    return math.sqrt(l2)

def compute_distance(to_compare, patient_triple, dist_metric):
    dist_value = 0.0
    if dist_metric is not None:
        if dist_metric == 'Euclidean':
            dist_value = math.dist(to_compare, patient_triple)
        if dist_metric == 'Canberra':
            for i in range(0, len(to_compare)):
                dist_value += abs(to_compare[i] - patient_triple[i]) / (abs(to_compare[i]) + abs(patient_triple[i]))
        if dist_metric == 'Cosine':
            for i in range(0, len(to_compare)):
                dist_value += to_compare[i]*patient_triple[i]
            dist_value = 1 - dist_value / (l2_norm(to_compare)*l2_norm(patient_triple))

    return dist_value


class PancreasGUI(tkinter.Frame):

    @classmethod
    def main(cls, patient_data):
        root = Tk()
        root.title('Pancreas Data Analyzer')
        root.iconbitmap('./resources/MACARON_nobackground.ico')
        root.configure(background='white')
        root.resizable(False, False)
        default_font = tkinter.font.nametofont("TkDefaultFont")
        default_font.configure(size=11)
        cls(root, patient_data)
        root.eval('tk::PlaceWindow . center')
        root.mainloop()

    def __init__(self, root, patient_data):
        super().__init__(root)
        self.patient_data = patient_data

        # Frame Init
        self.root = root
        in_names = ["GTV", "PTV", "EIV_5mm_t"]
        out_names = ["PTV V40G %", "PTV nonV40G cm3", "GTV V47G %", "GTV nonV47G cm3", "GTV V50G %", "PTV V35 %"]
        tab_in_names = ["id", "GTV", "PTV", "EIV_5mm_d", "EIV_5mm_s", "EIV_5mm_b", "EIV_5mm_t"]
        tab_out_names = ["PTV V40G %", "GTV V47G %", "GTV V50G %"]
        self.insert_f, self.v_texts = self.build_insert(Frame(root, bg="white",
                                                              highlightbackground="black",
                                                              highlightthickness=1), in_names)
        self.predict_f, self.predict_labels = self.build_predict(Frame(root, bg="white"), out_names)
        self.header_f, self.distance_dropdown = self.build_header(Frame(root, bg="white"))
        self.table_f, self.table_dict = self.build_table(Frame(root, bg="white"), tab_in_names, tab_out_names)
        self.footer = Frame(root, bg="white")

    def build_header(self, frame):
        frame.grid(padx=20, pady=10)

        head_lbl = Label(frame, text="Seeking for Similar Studies", font='Helvetica 12 bold', bg="white")
        head_lbl.grid(column=0, row=0, columnspan=5)

        folder_lbl = Label(frame, text="Reload Data", bg="white")
        folder_lbl.grid(column=0, row=1, padx=10, pady=5)

        folder_button = Button(frame, text="Reload Data", command=self.reload_data, bg="white")
        folder_button.grid(column=1, row=1, padx=10, pady=5)

        folder_lbl = Label(frame, text="Choose distance metric", bg="white")
        folder_lbl.grid(column=2, row=1, padx=10, pady=5)

        distance_dropdown = Combobox(frame, state="readonly", values=["Euclidean", "Canberra", "Cosine"])
        distance_dropdown.current(0)
        distance_dropdown.grid(column=3, row=1, padx=10, pady=5)

        p_button = Button(frame, text="Search!", command=self.neighbour_search, bg="white")
        p_button.grid(column=4, row=1, padx=10, pady=5)

        return frame, distance_dropdown

    def build_insert(self, frame, value_names):
        frame.grid(padx=20, pady=10)

        head_lbl = Label(frame, text="Type New Input Values", font='Helvetica 12 bold', bg="white")
        head_lbl.grid(column=0, row=0, columnspan=5)

        i_lbl = Label(frame, text='Input Variables', bg="white")
        i_lbl.grid(column=0, row=1, padx=10, pady=5)

        u_lbl = Label(frame, text='User Data', bg="white")
        u_lbl.grid(column=0, row=2, padx=10, pady=4)

        v_textfields = {}
        e_validation = frame.register(check_number)
        for value in value_names:
            v_lbl = Label(frame, text=value, bg="white")
            v_lbl.grid(column=1 + len(v_textfields.keys()), row=1, padx=10, pady=5)
            new_entry = Entry(frame, validate="key", validatecommand=(e_validation, '%S'))
            new_entry.grid(column=1 + len(v_textfields.keys()), row=2, padx=10, pady=5)
            v_textfields[value] = new_entry

        return frame, v_textfields

    def build_predict(self, frame, out_names):
        frame.grid(padx=20, pady=10)

        p_button = Button(frame, text="Predict Outputs!", command=self.predict_output, bg="white")
        p_button.grid(column=0, row=0, padx=10, pady=5, columnspan=len(out_names))

        p_labels = {}
        for value in out_names:
            v_lbl = Label(frame, text=value, bg="white")
            v_lbl.grid(column=len(p_labels.keys()), row=1, padx=5, pady=5)
            new_entry = Label(frame, text='-', bg='white')
            new_entry.grid(column=len(p_labels.keys()), row=2, padx=10, pady=5)
            p_labels[value] = new_entry

        return frame, p_labels

    def build_table(self, frame, value_names, out_names):
        frame.grid(padx=20, pady=10)

        head_index = 0
        for value in value_names:
            new_entry = Label(frame, text=value, bg='white')
            new_entry.grid(column=head_index, row=0, padx=5, pady=5)
            head_index += 1
        new_entry = Label(frame, text='Distance', bg='white', font=font.Font(weight="bold"))
        new_entry.grid(column=head_index, row=0, padx=5, pady=5)
        head_index += 1
        for value in out_names:
            new_entry = Label(frame, text=value, bg='white')
            new_entry.grid(column=head_index, row=0, padx=5, pady=5)
            head_index += 1

        l_table = {}
        for i in range(0, 5):
            l_table[i] = {}
            for value in value_names:
                new_entry = Label(frame, text='-', bg='white')
                new_entry.grid(column=len(l_table[i].keys()), row=1+i, padx=5, pady=5)
                l_table[i][value] = new_entry
            new_entry = Label(frame, text='-', bg='white', font=font.Font(weight="bold"))
            new_entry.grid(column=len(l_table[i].keys()), row=1 + i, padx=5, pady=5)
            l_table[i]['distance'] = new_entry
        for i in range(0, 5):
            for value in out_names:
                new_entry = Label(frame, text='-', bg='white')
                new_entry.grid(column=len(l_table[i].keys()), row=1+i, padx=5, pady=5)
                l_table[i][value] = new_entry

        return frame, l_table

    def neighbour_search(self):
        try:
            values = {}
            missing = False
            for value in self.v_texts.keys():
                v_str = self.v_texts[value].get()
                if len(v_str.strip()) > 0:
                    values[value] = float(v_str.strip())
                else:
                    missing = True
                    values[value] = 0.0

            if missing:
                showwarning("Input Error", 'Input values are missing or are malformed. Please check box above')
            else:
                # Creating Vars
                ptv = float(values['PTV'])
                gtv = float(values['GTV'])
                eic = float(values['EIV_5mm_t'])
                to_compare = [ptv, gtv, eic]
                dist_metric = self.distance_dropdown.get()

                for patient in self.patient_data:
                    patient_triple = [float(patient['PTV']), float(patient['GTV']), float(patient['EIV_5mm_t'])]
                    patient['distance'] = compute_distance(to_compare, patient_triple, dist_metric)

                # Sorting according to the distance
                self.patient_data = sorted(self.patient_data, key=lambda d: d['distance'])

                for i in self.table_dict.keys():
                    patient = self.patient_data[i]
                    for t_key in self.table_dict[i].keys():
                        if t_key == 'id':
                            self.table_dict[i][t_key].config(text=int(patient[t_key]))
                        else:
                            self.table_dict[i][t_key].config(text=format(float(patient[t_key]), ".2f"))

        except:
            showwarning("Input Error", 'Input values are missing or are malformed. Please check box above')

    def reload_data(self):
        self.patient_data = read_csv()

    def predict_output(self):
        try:
            values = {}
            missing = False
            for value in self.v_texts.keys():
                v_str = self.v_texts[value].get()
                if len(v_str.strip()) > 0:
                    values[value] = float(v_str.strip())
                else:
                    missing = True
                    values[value] = 0.0

            if missing:
                showwarning("Input Error", 'Input values are missing or are malformed. Please check box above')
            else:

                # Creating Vars
                ptv = values['PTV']
                gtv = values['GTV']
                eic = values['EIV_5mm_t']
                pg = gtv/ptv
                gp12 = math.pow(pg+0.5, 12)

                predicted_set = {}

                gtv_t = -0.09 * gtv + 0.065 * ptv + 0.25 * eic - 2.15 * pg + 0.43 * gp12 - 1.86

                predicted_set["GTV nonV47G cm3"] = gtv_t if gtv_t > 0 else 0.0

                ptv_t = -0.15 * gtv + 0.15 * ptv + 0.3 * eic - 3.92
                predicted_set["PTV nonV40G cm3"] = ptv_t if ptv_t > 0 else 0.0

                gtv_c = -0.42 * eic - 5.64 * pg + 104
                predicted_set["GTV V47G %"] = gtv_c if gtv_c < 100 else 100.0

                gtv50 = -0.69 * eic - 15.65 * pg + 106.7
                predicted_set["GTV V50G %"] = gtv50 if gtv50 < 100 else 100.0

                v40g = -1.05 * eic + 0.11 * predicted_set["PTV nonV40G cm3"] - 1.57 * predicted_set["GTV V47G %"] + 257.25
                predicted_set["PTV V40G %"] = v40g if v40g < 100 else 100.0

                v35g = 0.005 * eic + 0.44 * predicted_set["PTV V40G %"] + 56.4
                predicted_set["PTV V35 %"] = v35g if v35g < 100 else 100.0

                for out_key in self.predict_labels:
                    self.predict_labels[out_key].config(text=format(predicted_set[out_key], ".2f"))
        except:
            showwarning("Input Error", 'Input values are missing or are malformed')


if __name__ == "__main__":

    # Load configuration parameters
    config = None
    if os.path.exists('./pancreas-analyzer.cfg'):
        config = configparser.ConfigParser()
        config.read('./pancreas-analyzer.cfg')

    # Setting up variables
    if config is not None and isinstance(config, dict):
        if 'path' in config:
            if ('csv_file' in config['path']) and len(config['path']['csv_file'].strip()) > 0 \
                    and os.path.exists(config['path']['csv_file'].strip()):
                CSV_PATH = config['path']['csv_file'].strip()
            if ('tmp_folder' in config['path']) and len(config['path']['tmp_folder'].strip()) > 0:
                TMP_FOLDER = config['path']['tmp_folder'].strip()
            if ('out_folder' in config['path']) and len(config['path']['out_folder'].strip()) > 0:
                OUT_FOLDER = config['path']['out_folder'].strip()

    # Checking and clearing TMP_FOLDER
    if os.path.exists(TMP_FOLDER):
        clear_folder(TMP_FOLDER)
    else:
        os.makedirs(TMP_FOLDER)

    # Checking and clearing OUT_FOLDER
    if not os.path.exists(OUT_FOLDER):
        os.makedirs(OUT_FOLDER)

    patient_data = read_csv()
    if patient_data is None:
        print('error while reading historical patient data')

    # Starting UI
    PancreasGUI.main(patient_data)
