from tkinter import Tk, Label, Entry, Button, Checkbutton, IntVar, StringVar, filedialog, messagebox

class ConfigGUI:
    def __init__(self, master):
        self.master = master
        master.title("Générateur d'Horaires Configuration")

        self.salles_label = Label(master, text="Fichier des salles (.ini):")
        self.salles_label.grid(row=0, column=0)

        self.salles_entry = Entry(master, width=50)
        self.salles_entry.grid(row=0, column=1)

        self.browse_salles_button = Button(master, text="Parcourir", command=self.browse_salles)
        self.browse_salles_button.grid(row=0, column=2)

        self.out_label = Label(master, text="Fichier de sortie (.xml):")
        self.out_label.grid(row=1, column=0)

        self.out_entry = Entry(master, width=50)
        self.out_entry.grid(row=1, column=1)

        self.browse_out_button = Button(master, text="Parcourir", command=self.browse_out)
        self.browse_out_button.grid(row=1, column=2)

        self.api_label = Label(master, text="URL de l'API:")
        self.api_label.grid(row=2, column=0)

        self.api_entry = Entry(master, width=50)
        self.api_entry.grid(row=2, column=1)

        self.mock_label = Label(master, text="Fichier mock (JSON):")
        self.mock_label.grid(row=3, column=0)

        self.mock_entry = Entry(master, width=50)
        self.mock_entry.grid(row=3, column=1)

        self.browse_mock_button = Button(master, text="Parcourir", command=self.browse_mock)
        self.browse_mock_button.grid(row=3, column=2)

        self.include_empty_days_var = IntVar()
        self.include_empty_days_check = Checkbutton(master, text="Inclure les jours vides", variable=self.include_empty_days_var)
        self.include_empty_days_check.grid(row=4, columnspan=3)

        self.no_filter_location_var = IntVar()
        self.no_filter_location_check = Checkbutton(master, text="Ne pas filtrer par salle", variable=self.no_filter_location_var)
        self.no_filter_location_check.grid(row=5, columnspan=3)

        self.shift_hours_label = Label(master, text="Décalage d'heures:")
        self.shift_hours_label.grid(row=6, column=0)

        self.shift_hours_entry = Entry(master, width=5)
        self.shift_hours_entry.grid(row=6, column=1)

        self.generate_button = Button(master, text="Générer XML", command=self.generate_xml)
        self.generate_button.grid(row=7, columnspan=3)

    def browse_salles(self):
        filename = filedialog.askopenfilename(filetypes=[("INI files", "*.ini")])
        if filename:
            self.salles_entry.delete(0, 'end')
            self.salles_entry.insert(0, filename)

    def browse_out(self):
        filename = filedialog.asksaveasfilename(defaultextension=".xml", filetypes=[("XML files", "*.xml")])
        if filename:
            self.out_entry.delete(0, 'end')
            self.out_entry.insert(0, filename)

    def browse_mock(self):
        filename = filedialog.askopenfilename(filetypes=[("JSON files", "*.json")])
        if filename:
            self.mock_entry.delete(0, 'end')
            self.mock_entry.insert(0, filename)

    def generate_xml(self):
        salles = self.salles_entry.get()
        output = self.out_entry.get()
        api_url = self.api_entry.get()
        mock_file = self.mock_entry.get()
        include_empty_days = self.include_empty_days_var.get()
        no_filter_location = self.no_filter_location_var.get()
        shift_hours = self.shift_hours_entry.get()

        if not salles or not output:
            messagebox.showerror("Erreur", "Veuillez remplir tous les champs obligatoires.")
            return

        # Here you would call the main function from generateur_horaire_v2.py with the collected parameters
        # For example: main(salles, output, api_url, mock_file, include_empty_days, no_filter_location, shift_hours)

        messagebox.showinfo("Succès", "Fichier XML généré avec succès!")

if __name__ == "__main__":
    root = Tk()
    gui = ConfigGUI(root)
    root.mainloop()