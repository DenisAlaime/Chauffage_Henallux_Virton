from tkinter import Tk, Label, Entry, Button, Checkbutton, IntVar, filedialog
import subprocess
import os
import sys
import json

CONFIG_FILE = "last_paths.json"

class HorairesApp:
    def __init__(self, master):
        self.master = master
        master.title("Générateur d'Horaires")

        self.salles_label = Label(master, text="Fichier .ini des salles:")
        self.salles_label.pack()

        self.salles_entry = Entry(master)
        self.salles_entry.pack()

        self.browse_button = Button(master, text="Parcourir", command=self.browse_salles)
        self.browse_button.pack()

        self.out_label = Label(master, text="Fichier XML de sortie:")
        self.out_label.pack()

        self.out_entry = Entry(master)
        self.out_entry.pack()

        self.out_browse_button = Button(master, text="Parcourir", command=self.browse_output)
        self.out_browse_button.pack()

        self.api_label = Label(master, text="URL de l'API:")
        self.api_label.pack()

        self.api_entry = Entry(master)
        self.api_entry.pack()
        self.api_entry.insert(0, "https://simple-planning.henallux.be/api/getHoraireSalle")

        self.shift_hours_label = Label(master, text="Décalage d'heures:")
        self.shift_hours_label.pack()

        self.shift_hours_entry = Entry(master)
        self.shift_hours_entry.pack()
        self.shift_hours_entry.insert(0, "-2")

        self.include_empty_days_var = IntVar()
        self.include_empty_days_check = Checkbutton(master, text="Inclure les jours vides", variable=self.include_empty_days_var)
        self.include_empty_days_check.pack()

        self.no_filter_location_var = IntVar()
        self.no_filter_location_check = Checkbutton(master, text="Ne pas filtrer par salle exacte", variable=self.no_filter_location_var)
        self.no_filter_location_check.pack()

        self.submit_button = Button(master, text="Générer XML", command=self.generate_xml)
        self.submit_button.pack()

        self.reload_button = Button(master, text="Charger les derniers chemins", command=self.load_last_paths)
        self.reload_button.pack()

        self.load_last_paths()

    def browse_salles(self):
        filename = filedialog.askopenfilename(filetypes=[("INI files", "*.ini")])
        if filename:
            self.salles_entry.delete(0, 'end')
            self.salles_entry.insert(0, filename)
            self.save_last_paths()

    def browse_output(self):
        filename = filedialog.asksaveasfilename(defaultextension=".xml", filetypes=[("XML files", "*.xml")])
        if filename:
            self.out_entry.delete(0, 'end')
            self.out_entry.insert(0, filename)
            self.save_last_paths()

    def generate_xml(self):
        salles = self.salles_entry.get()
        output = self.out_entry.get()
        api_url = self.api_entry.get()
        shift_hours = self.shift_hours_entry.get()
        include_empty_days = self.include_empty_days_var.get()
        no_filter_location = self.no_filter_location_var.get()

        self.save_last_paths()

        # Résoudre le chemin absolu vers le script à partir du fichier courant
        script_path = os.path.abspath(os.path.join(os.path.dirname(__file__), "..", "..", "generateur_horaire_v2.py"))
        if not os.path.exists(script_path):
            print(f"Script introuvable: {script_path}")
            return

        # Utiliser le même interpréteur Python (sys.executable) et le chemin absolu
        command = [
            sys.executable, script_path,
            "--salles", salles,
            "--out", output,
            "--api", api_url,
            "--shift-hours", shift_hours
        ]

        if include_empty_days:
            command.append("--include-empty-days")
        if no_filter_location:
            command.append("--no-filter-location")

        result = subprocess.run(command)

        # si la génération a réussi, tenter l'upload via FTP (config.ini à la racine du package)
        try:
            if result.returncode == 0 and os.path.exists(output):
                config_path = os.path.abspath(os.path.join(os.path.dirname(__file__), "..", "config.ini"))
                # utils.py se trouve dans le même dossier src
                from utils import upload_xml_via_ftp
                ok, msg = upload_xml_via_ftp(output, config_path)
                if not ok:
                    print("Upload FTP échoué :", msg)
                else:
                    print("Upload FTP :", msg)
        except Exception as e:
            print("Erreur lors de l'upload FTP :", e)

    def save_last_paths(self):
        data = {
            "salles": self.salles_entry.get(),
            "output": self.out_entry.get()
        }
        try:
            with open(CONFIG_FILE, "w", encoding="utf-8") as f:
                json.dump(data, f)
        except Exception as e:
            print("Erreur lors de la sauvegarde des chemins :", e)

    def load_last_paths(self):
        if os.path.exists(CONFIG_FILE):
            try:
                with open(CONFIG_FILE, "r", encoding="utf-8") as f:
                    data = json.load(f)
                self.salles_entry.delete(0, 'end')
                self.salles_entry.insert(0, data.get("salles", ""))
                self.out_entry.delete(0, 'end')
                self.out_entry.insert(0, data.get("output", ""))
            except Exception as e:
                print("Erreur lors du chargement des chemins :", e)

if __name__ == "__main__":
    root = Tk()
    app = HorairesApp(root)
    root.mainloop()