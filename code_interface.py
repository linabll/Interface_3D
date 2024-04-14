#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Created on Sun Apr 14 11:12:19 2024

@author: lina
"""

import tkinter as tk
import pydicom
from tkinter import filedialog
from tkinter import messagebox
from PIL import Image, ImageTk
import matplotlib.pyplot as plt
from matplotlib.backends.backend_tkagg import FigureCanvasTkAgg
from matplotlib.colors import LinearSegmentedColormap
import os
import numpy as np
import vtk
from tkinter import ttk, simpledialog
from skimage import exposure, filters

# Variables globales
fenetre = None
message_label = None
text_widget = None
image_label = None
canvas = None
patient_info = None  # Variable pour stocker les informations du patient
dossier_ouvert = False # Variable globale pour suivre l'état du fichier ouvert
stacked_data = None
axes = None
coronal_label = None
transversal_label = None
sagittal_label = None
coronal_entry = None
transversal_entry = None
sagittal_entry = None
dossier=None
cmap = plt.cm.gray
# Variables globales pour les paramètres de fenêtre
fenetre_width = 1120
fenetre_height = 700

fenetre_width2 = 300
fenetre_height2 = 190


#Définition des couleurs
parula_colors = [(0.0, '#352a87'), (0.125, '#0363e1'), (0.25, '#1485d4'), (0.375, '#06a7c6'), 
               (0.5, '#38b99e'), (0.625, '#92bf73'), (0.75, '#d9ba56'), (0.875, '#fcce2e'), (1.0, '#f9fb0e')]
parula_cmap = LinearSegmentedColormap.from_list('parula', parula_colors)
civids_colors = [(0.0, 'midnightblue'), (0.25, 'mediumblue'), (0.5, 'cyan'), (0.75, 'yellow'), (1.0, 'white')]
civids_cmap = LinearSegmentedColormap.from_list('civids', civids_colors)
original_colors = [(0, 0, 0), (1, 1, 1)]
original_cmap = LinearSegmentedColormap.from_list('original', original_colors)
colors = {
    "ORIGINAL": original_cmap,
    "JET": plt.cm.jet,
    "BONE": plt.cm.bone,
    "CIVIDS": civids_cmap,
    "TURBO": plt.cm.turbo,
    "HOT": plt.cm.hot,
    "PARULA": parula_cmap,
    "TWILIGHT SHIFTED": plt.cm.twilight_shifted
}

def centrer_fenetre(fenetre, width, height):
    
    # Obtenir la taille de l'écran
    screen_width = fenetre.winfo_screenwidth()
    screen_height = fenetre.winfo_screenheight()
    
    # Calculer la position pour centrer la fenêtre
    x = (screen_width - fenetre_width) // 2
    y = (screen_height - fenetre_height) // 2
    
    # Définir la position de la fenêtre
    fenetre.geometry(f"{width}x{height}+{x}+{y}")


def configurer_message_bienvenue():
    global message_label, text_widget
    # Création d'un Label pour afficher le message de bienvenue
    message_label = tk.Label(fenetre, text="Bienvenue sur le logiciel de navigation 3D")
    message_label.pack()

      # Charger l'image de bienvenue
    try:
        image_welcome = Image.open("logo.png")
        image_welcome = image_welcome.resize((200, 200), Image.LANCZOS)
        photo_welcome = ImageTk.PhotoImage(image_welcome)
    except Exception as e:
        # Afficher une erreur si le chargement de l'image échoue
        messagebox.showerror("Erreur", f"Impossible de charger l'image : {e}")
        return
    # Mettre à jour le label avec le texte et l'image
    message_label.config(image=photo_welcome, compound="top")
    message_label.image = photo_welcome
    text_widget.pack_forget()
      
def afficher_images_3d(dossier, fenetre):
    global canvas, coronal_label, transversal_label, sagittal_label, coronal_entry, transversal_entry, sagittal_entry, stacked_data, axes, cmap
    
    # Liste pour stocker les données brutes de chaque image
    pixel_data_list = []

    # Parcourir tous les fichiers DICOM dans le dossier
    for filename in os.listdir(dossier):
        if filename.endswith(".dcm"):
            # Charger l'image DICOM
            ds = pydicom.dcmread(os.path.join(dossier, filename))
            # Extraire les données brutes de l'image
            pixel_data_list.append(ds.pixel_array)

    # Créer une matrice 3D en empilant les données brutes des images
    stacked_data = np.stack(pixel_data_list, axis=2)
 
    # Normaliser les valeurs des pixels dans la plage [0, 1]
    stacked_data = stacked_data.astype(np.float64) / np.max(stacked_data)

    # Appliquer l'égalisation d'histogramme à chaque image dans la pile
    for i in range(stacked_data.shape[2]):
        stacked_data[:, :, i] = exposure.equalize_hist(stacked_data[:, :, i])

    # Ajuster le contraste et la luminosité
    for i in range(stacked_data.shape[2]):
        stacked_data[:, :, i] = exposure.adjust_gamma(stacked_data[:, :, i], gamma=0.8)  # Réduire le gamma pour augmenter le contraste

    # Appliquer un filtre de netteté pour améliorer les détails
    for i in range(stacked_data.shape[2]):
        stacked_data[:, :, i] = filters.unsharp_mask(stacked_data[:, :, i], radius=1, amount=1)

    # Appliquer un seuil pour supprimer le bruit de fond
    threshold_value = 0.7
    stacked_data[stacked_data < threshold_value] = threshold_value

    # Afficher les coupes coronale, axiale et sagittale dans l'interface Tkinter
    fig, axes = plt.subplots(1, 3, figsize=(18, 10))
    fig.patch.set_facecolor('black')  # Changer la couleur du cadre de la figure en noir
    # Espacement entre les sous-graphiques
    plt.subplots_adjust(left=0.05, right=0.95, wspace=0.5)
    # Centrer la fenêtre principale
    centrer_fenetre(fenetre, fenetre_width, fenetre_height)

 # Définition de la fonction pour mettre à jour les coupes avec les nouvelles valeurs
    def update_slices(event=None):
        coronal_index = int(coronal_entry.get() or 127)  # Si vide, indice arbitraire pour avoir une image
        transversal_index = int(transversal_entry.get() or 127)
        sagittal_index = int(sagittal_entry.get() or 39)
        # Mettre à jour les coupes avec les nouvelles valeurs et la nouvelle couleur
        for i, ax in enumerate(axes):
            if i == 0:  # Coupe Sagittale
                slice_data = stacked_data[:, :, sagittal_index]
                ax.set_title("Coupe sagittale")
            elif i == 1:  # Coupe Transversale
                slice_data = stacked_data[transversal_index, :, :]
                ax.set_title("Coupe Transversale")
            else:  # Coupe Coronale
                slice_data = stacked_data[:, coronal_index, :]
                ax.set_title("Coupe Coronale")
            ax.imshow(slice_data, cmap=cmap)  # Appliquer la couleur définie par l'utilisateur
            ax.axis("off")
        # Mettre à jour la figure
        fig.canvas.draw()

    # Entrée pour l'indice sagittal
    sagittal_label = tk.Label(fenetre, text="Indice sagittal :")
    sagittal_label.pack()
    sagittal_entry = tk.Entry(fenetre)
    sagittal_entry.pack()
    sagittal_entry.pack(pady=10)
    sagittal_entry.bind("<KeyRelease>", lambda event: update_slices())

    # Entrée pour l'indice transversal
    transversal_label = tk.Label(fenetre, text="Indice transversal :")
    transversal_label.pack()
    transversal_entry = tk.Entry(fenetre)
    transversal_entry.pack()
    transversal_entry.pack(pady=10)
    transversal_entry.bind("<KeyRelease>", lambda event: update_slices())

    # Entrée pour l'indice coronal
    coronal_label = tk.Label(fenetre, text="Indice coronal :")
    coronal_label.pack()
    coronal_entry = tk.Entry(fenetre)
    coronal_entry.pack()
    coronal_entry.pack(pady=10)
    coronal_entry.bind("<KeyRelease>", lambda event: update_slices())

    # Appeler la fonction pour afficher les coupes initiales
    update_slices()

    # Convertir la figure matplotlib en widget Tkinter
    canvas = FigureCanvasTkAgg(fig, master=fenetre)
    canvas.draw()
    canvas.get_tk_widget().pack()

def ouvrir_dossier():
    global fenetre, dossier_ouvert, text_widget, patient_info
    dossier_ouvert = True
    # Cacher ou détruire le widget du message de bienvenue s'il existe
    if message_label:
        message_label.pack_forget()
    dossier = filedialog.askdirectory(title="Ouvrir un dossier")
    if dossier:
        try:
            afficher_images_3d(dossier, fenetre)
            label.config(text=f"Dossier DICOM ouvert : {dossier}")
            for filename in os.listdir(dossier):
                if filename.endswith(".dcm"):
                    fichier = os.path.join(dossier, filename)
                    ds = pydicom.dcmread(fichier)
                    patient_info = {
                        "Nom": getattr(ds, 'PatientName', ''),
                        "ID": getattr(ds, 'PatientID', ''),
                        "Date de Naissance": getattr(ds, 'PatientBirthDate', ''),
                        "Sexe": getattr(ds, 'PatientSex', ''),
                        "Age": getattr(ds, 'PatientAge', ''),
                        "Taille": getattr(ds, 'PatientSize', ''),  
                        "Poids": getattr(ds, 'PatientWeight', '')  
                    }
                    text_widget.delete("1.0", tk.END)
                    text_widget.insert(tk.END, patient_info)
                    label.config(text=f"Dossier DICOM ouvert : {dossier}")
                    break
        except Exception as e:
            label.config(text=f"Erreur lors de l'ouverture du dossier DICOM : {e}")

def fermer_dossier():
    global text_widget, image_label, message_label, dossier_ouvert, coronal_label, transversal_label, sagittal_label, coronal_entry, transversal_entry, sagittal_entry
    # Réinitialisation des variables globales
    dossier_ouvert = False
    # Cacher les widgets associés au dossier ouvert
    if text_widget:
        text_widget.pack_forget()
    if image_label:
        image_label.pack_forget()  
    # Cacher le widget Label de bienvenue s'il y avait un message précédent
    if message_label:
        message_label.pack_forget()  
        # Supprimer les images 3D
    if canvas:
        canvas.get_tk_widget().pack_forget()
        # Supprimer les boutons s'ils existent
    # Masquer les labels s'ils existent
    if coronal_label:
        coronal_label.pack_forget()
    if transversal_label:
        transversal_label.pack_forget()
    if sagittal_label:
        sagittal_label.pack_forget()
    # Masquer les entrées s'ils existent
    if coronal_entry:
        coronal_entry.pack_forget()
    if transversal_entry:
        transversal_entry.pack_forget()
    if sagittal_entry:
        sagittal_entry.pack_forget()
    # Afficher un message indiquant que le dossier est fermé
    label.config(text="Dossier DICOM fermé")

def enregistrer_sous():
    global text_widget, label

    # Demander à l'utilisateur de choisir l'emplacement où enregistrer le dossier DICOM
    dossier_parent = filedialog.askdirectory(title="Enregistrer dossier DICOM sous")
    if not dossier_parent:
        return

    try:
        # Obtenir le nom du nouveau dossier
        nom_dossier = simpledialog.askstring("Nouveau dossier", "Entrez le nom du nouveau dossier :")
        if not nom_dossier:
            return

        # Créer le chemin complet du nouveau dossier
        chemin_dossier = os.path.join(dossier_parent, nom_dossier)
        os.makedirs(chemin_dossier, exist_ok=True)  # Créer le dossier s'il n'existe pas

        # Éventuellement, vous pouvez copier ou déplacer vos fichiers DICOM dans le nouveau dossier ici

        label.config(text=f"Dossier DICOM enregistré dans : {chemin_dossier}")
    except Exception as e:
        # En cas d'erreur lors de l'enregistrement du dossier DICOM
        label.config(text=f"Erreur lors de l'enregistrement du dossier DICOM : {e}")

def afficher_informations_patient():
    global patient_info, dossier_ouvert
    # Vérifier si un fichier est ouvert
    if not dossier_ouvert:
        # Afficher un message d'erreur si aucun fichier n'est ouvert
        tk.messagebox.showerror("Erreur", "Aucun fichier DICOM ouvert.")
        return
    if patient_info:
        # Ouvrir une fenêtre pour afficher les informations du patient
        fenetre_info_patient = tk.Toplevel(fenetre)
        fenetre_info_patient.title("Informations Patient")

        # Créer un widget Text pour afficher les informations
        text_widget_info_patient = tk.Text(fenetre_info_patient, wrap="word", height=10, width=50)
        text_widget_info_patient.pack()

        for key, value in patient_info.items():
            text_widget_info_patient.insert(tk.END, f"{key} : {value}\n")
            
def changer_couleur_images(couleur):
    global stacked_data, axes, cmap
    if stacked_data is None:
        tk.messagebox.showerror("Erreur", "Aucun dossier DICOM ouvert.")
        return
    cmap = colors.get(couleur)
    for ax in axes:
        im = ax.get_images()[0]
        im.set_cmap(cmap)
    plt.draw()


def afficher_volume_3D(dicom_dir=None):
    global render_window    
    def on_select():
        selected_item = combo_box.get()
        # Vérifier si un élément a été sélectionné
        if not selected_item:
            # Afficher un message d'erreur à l'utilisateur
            tk.messagebox.showerror("Erreur", "Aucun élément sélectionné.")
            return
    
        selected_folder = dicom_folders[selected_item]
        threshold_max_str = entry_threshold_max.get()
        
        # Vérifier si une valeur pour threshold_max a été saisie
        if not threshold_max_str:
            # Afficher un message d'erreur à l'utilisateur
            tk.messagebox.showerror("Erreur", "Aucun seuil écrit.")
            return
        
        # Vérifier si la valeur saisie est un entier
        try:
            threshold_max = int(threshold_max_str)
        except ValueError:
            # Afficher un message d'erreur si la valeur n'est pas un entier
            tk.messagebox.showerror("Erreur", "Le seuil maximal doit être un entier.")
            return
        
        # Vérifier si la valeur saisie est positive
        if threshold_max < 0:
            # Afficher un message d'erreur si la valeur est négative
            tk.messagebox.showerror("Erreur", "Le seuil maximal doit être positif.")
            return
        
        threshold_min = 0
        afficher_volume_3D_selected(selected_folder, threshold_min, threshold_max)
        
    def afficher_volume_3D_selected(dicom_dir, threshold_min, threshold_max):
        # Votre code pour afficher le modèle 3D à partir du dossier DICOM spécifié
        volume = vtk.vtkImageData()
        reader = vtk.vtkDICOMImageReader()
        reader.SetDirectoryName(dicom_dir)
        reader.Update()
        volume.DeepCopy(reader.GetOutput())
        
        # Appliquer un seuillage pour segmenter le crâne
        threshold = vtk.vtkImageThreshold()
        threshold.SetInputData(volume)
        threshold.ThresholdBetween(threshold_min, threshold_max)
        threshold.ReplaceInOn()
        threshold.SetInValue(255)
        threshold.ReplaceOutOn()
        threshold.SetOutValue(0)
        threshold.Update()
        # Appliquer un seuil plus agressif pour augmenter le contraste
        threshold.SetInputData(volume)
        threshold.ThresholdBetween(1, 127)

        
        # Appliquer un filtre de lissage pour améliorer la surface 
        gaussian_filter = vtk.vtkImageGaussianSmooth()
        gaussian_filter.SetInputData(threshold.GetOutput())
        gaussian_filter.SetStandardDeviations(1.0, 1.0, 1.0)
        gaussian_filter.Update()
        
        # Utiliser l'algorithme Marching Cubes pour générer une surface en 3D 
        surface_extractor = vtk.vtkMarchingCubes()
        surface_extractor.SetInputData(gaussian_filter.GetOutput())
        surface_extractor.SetValue(0, 255)
        surface_extractor.Update()
     
        # Mapper pour la visualisation
        mapper = vtk.vtkPolyDataMapper()
        mapper.SetInputConnection(surface_extractor.GetOutputPort())
    
        # Acteur pour la visualisation
        actor = vtk.vtkActor()
        actor.SetMapper(mapper)
        actor_property = actor.GetProperty()
        actor_property.SetOpacity(opacity_slider.get())
        actor.GetProperty().SetColor(1.0, 0.0, 0.0)  # Changer la couleur du volume (ici bleu clair)

        # Créer un renderer, une fenêtre de rendu et un interactor
        renderer = vtk.vtkRenderer()
        renderer.SetBackground(1.0, 1.0, 1.0)
        renderer.AddActor(actor)
        render_window = vtk.vtkRenderWindow()
        render_window.SetWindowName("Affichage 3D")
        render_window.AddRenderer(renderer)
        
        # Configuration de la taille de la fenêtre VTK
        vtk_window_width = 800
        vtk_window_height = 600
    
        # Créer la fenêtre de rendu VTK
        render_window = vtk.vtkRenderWindow()
        render_window.SetWindowName("Affichage 3D")
        render_window.AddRenderer(renderer)
        render_window.SetSize(vtk_window_width, vtk_window_height)
    
        # Récupérer la taille de l'écran
        screen_width = root.winfo_screenwidth()
        screen_height = root.winfo_screenheight()
    
        # Calculer la position de la fenêtre VTK pour la placer au milieu de l'écran
        vtk_window_x = (screen_width - vtk_window_width) // 2
        vtk_window_y = (screen_height - vtk_window_height) // 2
    
        # Définir la position de la fenêtre de rendu VTK
        render_window.SetPosition(vtk_window_x, vtk_window_y)
    
        # Créer un interactor pour la fenêtre de rendu
        render_window_interactor = vtk.vtkRenderWindowInteractor()
        render_window_interactor.SetRenderWindow(render_window)


        def update_opacity(value):
            actor.GetProperty().SetOpacity(opacity_slider.get())
            render_window.Render()
            
        opacity_slider.config(command=update_opacity)
        
        # Ajouter l'acteur au renderer et démarrer l'interactor
        renderer.AddActor(actor)
        render_window.Render()

    # Définir les dossiers DICOM disponibles
    dicom_folder_brain = "DICOMData/DICOMData/Brain"
    dicom_folder_chest = "DICOMData/DICOMData/Chest"
    dicom_folder_legs = "DICOMData/DICOMData/Legs"
    dicom_folder_breast = "DICOMData/DICOMData/Breast"

    dicom_folders = {
        "Brain": dicom_folder_brain,
        "Chest": dicom_folder_chest,
        "Breast": dicom_folder_breast,
        "Legs": dicom_folder_legs
    }

    # Créer la fenêtre principale
    root = tk.Tk()
    root.title("Sélectionner un modèle 3D")
    centrer_fenetre(root, fenetre_width2, fenetre_height2) 

    # Créer l'option déroulante pour sélectionner le modèle 3D
    label = ttk.Label(root, text="Choisir un modèle 3D:")
    label.pack()

    combo_box = ttk.Combobox(root, values=list(dicom_folders.keys()))
    combo_box.pack()
    
    label_threshold_max = ttk.Label(root, text="Seuil maximal:")
    label_threshold_max.pack()
    entry_threshold_max = ttk.Entry(root)
    entry_threshold_max.pack()
    
    label_opacity = ttk.Label(root, text="Opacité maximale:")
    label_opacity.pack()
    opacity_slider = tk.Scale(root, from_=0, to=1, resolution=0.01, orient=tk.HORIZONTAL)
    opacity_slider.pack()

    # Bouton pour confirmer la sélection
    button = ttk.Button(root, text="Afficher", command=on_select)
    button.pack()

    root.mainloop()

def afficher_message_info():
    message = ("    Zoom : Translation avant.\n\n"
               "    Dézoom : Translation arrière.\n\n"
               "    Outils : bouton droit pour couper/copier/coller.\n\n"
               "    Propriétés : bouton gauche pour annuler/rétablir/modifier.")
    messagebox.showinfo("Informations souris 3D", message)

# Création de la fenêtre principale
fenetre = tk.Tk()
fenetre.title("Logiciel de Navigation 3D")
# Centrer la fenêtre principale
centrer_fenetre(fenetre, fenetre_width, fenetre_height) 

# Définition de l'icône personnalisée
#fenetre.iconbitmap("/Users/lina/Desktop/")


# Création de la barre de menu
barre_menu = tk.Menu(fenetre)

# Menu pour l'Onglet 1
menu_onglet1 = tk.Menu(barre_menu, tearoff=0)
menu_onglet1.add_command(label="Ouvrir", command=ouvrir_dossier)
menu_onglet1.add_command(label="Fermer", command=fermer_dossier)
menu_onglet1.add_command(label="Enregistrer sous", command=enregistrer_sous)
barre_menu.add_cascade(label="Fichier", menu=menu_onglet1)

# Menu pour l'Onglet 2
menu_onglet2 = tk.Menu(barre_menu, tearoff=0)
menu_onglet2.add_command(label="Informations du patient", command=afficher_informations_patient)
barre_menu.add_cascade(label="Informations", menu=menu_onglet2)

# Menu pour l'Onglet 3
menu_onglet3 = tk.Menu(barre_menu, tearoff=0)
menu_onglet3.add_command(label="ORIGINAL", command=lambda: changer_couleur_images("ORIGINAL"))
menu_onglet3.add_command(label="JET", command=lambda: changer_couleur_images("JET"))
menu_onglet3.add_command(label="BONE", command=lambda: changer_couleur_images("BONE"))
menu_onglet3.add_command(label="CIVIDS", command=lambda: changer_couleur_images("CIVIDS"))
menu_onglet3.add_command(label="TURBO", command=lambda: changer_couleur_images("TURBO"))
menu_onglet3.add_command(label="HOT", command=lambda: changer_couleur_images("HOT"))
menu_onglet3.add_command(label="PARULA", command=lambda: changer_couleur_images("PARULA"))
menu_onglet3.add_command(label="TWILIGHT SHIFTED", command=lambda: changer_couleur_images("TWILIGHT SHIFTED"))
menu_onglet3.add_command(label="Visualisation 3D", command=afficher_volume_3D)
barre_menu.add_cascade(label="Affichage", menu=menu_onglet3)

# Menu pour l'Onglet 4
menu_onglet4 = tk.Menu(barre_menu, tearoff=0)
menu_onglet4.add_command(label="Souris 3D", command=afficher_message_info)
barre_menu.add_cascade(label="Aide", menu=menu_onglet4)

# Configurer la fenêtre pour utiliser la barre de menu
fenetre.config(menu=barre_menu)

# Création d'un widget Text pour afficher le contenu du fichier
text_widget = tk.Text(fenetre, wrap="word", height=100, width=500)
text_widget.pack()

# Création d'un Label pour afficher les images
image_label = tk.Label(fenetre)
image_label.pack()

## Création d'un nouveau widget Label pour le texte
label = tk.Label(fenetre)
label.pack()

# Appeler la fonction pour configurer le message de bienvenue
configurer_message_bienvenue()

# Définition de l'icône personnalisée
fenetre.iconbitmap("logo.ico")

# Lancement de la boucle principale de l'interface graphique
fenetre.mainloop()
