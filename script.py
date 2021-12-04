# img_viewer.py

# Import the libraries
import PySimpleGUI as sg
import cv2
from PIL import Image,ImageTk
import io
import numpy as np
import os.path
import retinalSeg

# Initialization
imgURL = np.array([])
Acc1 = -10
Sn1 = -10
Sp1 = -10
Auc1 = -10
PrevAcc = -20

# Window layout in 2 columns
file_list_column = [
    [
        sg.Text("Train Dataset"),
        sg.In(size=(25, 1), enable_events=True, key="-FOLDER-"),
        sg.FolderBrowse(),
    ],
    [
        sg.Listbox(
            values=[], enable_events=True, size=(40, 20), key="-FILE LIST-"
        )
    ],

]
file_list_column1 = [
    [
        sg.Text("Test Dataset"),
        sg.In(size=(25, 1), enable_events=True, key="-FOLDER1-"),
        sg.FolderBrowse(),
    ],
    [
        sg.Listbox(
            values=[], enable_events=True, size=(40, 20), key="-FILE LIST1-"
        )
    ],

]


# Display the name of the file that was chosen
image_viewer_column = [
    [sg.Text("Input Image:",justification='center',size=(40,1))],
    # [sg.Text(size=(40, 1), key="-TOUT-")],
    
    [sg.Text(size=(40, 1), key="-ACC1-")],
    [sg.Text(size=(40, 1), key="-SN1-")],
    [sg.Text(size=(40, 1), key="-SP1-")],
    [sg.Text(size=(40, 1), key="-ROC1-")],
    [sg.Image(key="-IMAGE-")],
]
image_viewer_column1 = [
    [sg.Text("Output Image",justification='center',size=(40,1))],
    # [sg.Text(size=(40, 1), key="-TOUT1-")],
    [sg.Text(size=(40, 1), key="-ACC-")],
    [sg.Text(size=(40, 1), key="-SN-")],
    [sg.Text(size=(40, 1), key="-SP-")],
    [sg.Text(size=(40, 1), key="-ROC-")],
    [sg.Image(key="-IMAGE1-")],
]


# ----- Full layout -----

layout = [
    [
        sg.Column(file_list_column),
        sg.VSeperator(),
        sg.Column(image_viewer_column),
        sg.HorizontalSeparator(),
        # sg.Column(file_list_column1),
        sg.VSeperator(),
        sg.Column(image_viewer_column1),
    ]
]


window = sg.Window("DIP Project: Retinal Blood Vessel Segmentation", layout)


# Run the Event Loop

while True:
    event, values = window.read()
    if event == "Exit" or event == sg.WIN_CLOSED:
        break

    # Make a list of files in the folder

    if event == "-FOLDER-":
        folder = values["-FOLDER-"]
        print(folder)
        try:
            # Get list of files in folder
            file_list = os.listdir(folder)
        except:
            file_list = []

        fnames = [
            f
            for f in file_list
            if os.path.isfile(os.path.join(folder, f))
            and f.lower().endswith((".png", ".ppm",".tif","jpeg","jpg"))
        ]
        window["-FILE LIST-"].update(fnames)

    elif event == "-FILE LIST-":  # A file was chosen from the listbox
        try:
            filename = os.path.join(
                values["-FOLDER-"], values["-FILE LIST-"][0]
            )
            # window["-TOUT-"].update(filename)
            size = (300, 300)
            im = Image.open(filename)
            im = im.resize(size, resample=Image.BICUBIC)
            image = ImageTk.PhotoImage(image=im)
            # update image in sg.Image
            window['-IMAGE-'].update(data=image)
            imgURL,Acc1,Sn1,Sp1,Auc1 = retinalSeg.Segment(filename)
            # window["-IMAGE-"].update(filename=filename)
        except:
            pass

    if PrevAcc == -20 or Acc1 !=PrevAcc or Acc1==-1:  # A file was chosen from the listbox
        print("Trigger")
        try:
            print("Trigger1")
            print(np.unique(imgURL))
            # filename = os.path.join(
            #     values["-FOLDER1-"], values["-FILE LIST1-"][0]
            # )
            # filename = imgURL
            # window["-TOUT1-"].update(filename)
            if PrevAcc!=-20:
                window["-ACC-"].update("Accuracy(Acc): "+str(Acc1))
                window["-SN-"].update("Sensitivity(Sn): "+str(Sn1))
                window["-SP-"].update("Specificity:(Sp) "+str(Sp1))
                window["-ROC-"].update("Area Under Curve(AUC): "+str(Auc1))
            size = (300, 300)
            im = imgURL
            print("Image",imgURL)
            im = cv2.resize(im, size, interpolation = cv2.INTER_AREA)
            image = ImageTk.PhotoImage(image=Image.fromarray(im))
            window["-IMAGE1-"].update(data=image)
        except:
            pass
    # imgURL = np.array([])
    PrevAcc = Acc1
window.close()
