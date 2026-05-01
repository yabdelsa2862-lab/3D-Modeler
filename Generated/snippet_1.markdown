# 3D‑Modeler

**3D‑Modeler** is a Python‑based system for generating, manipulating, and serving 3D models.  
It’s designed to help you create parametric and procedural models in formats like SCAD and STL, and includes tools for both scripted generation and interactive viewing.

---

## 🧩 Features
- Generate 3D models with Python scripts (`/privatemodels/*.py`)
- Export and view SCAD and STL files
- Serve models locally via an integrated server (`privateserver.py`)
- Preview models in an interactive window (`privatewindow.py`)
- One‑click launch with the included Windows batch file (`privaterun.bat`)

---

## ⚙️ Setup on Windows

1. Clone this repository  
   Open Command Prompt and run:  
   `git clone https://github.com/yabdelsa2862-lab/3D-Modeler`

2. Enter the project folder  
   `cd 3D-Modeler`

3. Install dependencies  
   `pip install -r privaterequirements.txt`

4. Run the server  
   `python privateserver.py`

5. (Optional) Launch the interactive viewer  
   `python privatewindow.py`

6. Or start everything automatically  
   Double-click the file `privaterun.bat`

---

## 💡 Example Usage

After setup, you can generate models using scripts in `/privatemodels`. For example:  
`python privatemodels/8582622a7d.py`  

This will create a corresponding `.scad` and `.stl` file ready for viewing or export.

---

## 🧠 About

Created by **Yousef Mohamed Nazmi**, the 3D‑Modeler toolkit combines Python and OpenSCAD workflows to streamline 3D object generation for creative and development projects.

---

## 🪟 Requirements
- Windows 10 or later  
- Python 3.10+  
- OpenSCAD (optional, for previewing `.scad` files)  

---

Enjoy exploring procedural modeling with **3D‑Modeler**!