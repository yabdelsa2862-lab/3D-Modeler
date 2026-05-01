# 3D‑Modeler

**3D‑Modeler** is a Python‑based toolkit for generating, manipulating, and serving 3D models.  
It supports SCAD and STL workflows and can run a lightweight local server or windowed viewer for inspecting generated geometry.

---

## Features
- Procedural 3D model generation with Python
- Exports to SCAD and STL formats
- Lightweight local preview server
- Windows launcher and viewer support

---

## Installation on Windows

1. Clone this repository:
   git clone https://github.com/yabdelsa2862-lab/3D-Modeler
   cd 3D-Modeler

2. Install required dependencies:
   pip install -r privaterequirements.txt

3. (Optional) Verify the environment:
   python --version
   pip list

---

## Usage

Start the local server:
   python privateserver.py

Open the 3D viewer window:
   python privatewindow.py

Generate models manually:
   python privategeneration.py

Or run everything automatically:
   privaterun.bat

---

## Folder Structure
- `privatemodels/` — contains Python, SCAD, and STL model definitions and outputs  
- `privategeneration.py` — handles 3D object generation  
- `privateserver.py` — hosts a local HTTP server for viewing models  
- `privatewindow.py` — provides a desktop viewer on Windows  
- `privaterun.bat` — simple launcher combining the above  
- `privaterequirements.txt` — dependency list

---

## License
This project is maintained by Yousef Mohamed Nazmi.  
All rights reserved unless otherwise stated.
