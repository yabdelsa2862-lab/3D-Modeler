# 3D‑Modeler 🛠️

**3D‑Modeler** is an AI-powered, Python-based toolkit designed for the rapid generation, manipulation, and serving of 3D models. By combining LLM-driven prompting with procedural geometry, it allows users to transform text or code logic into physical STL and SCAD files.

The system includes a lightweight local server and a dedicated Windows viewer for real-time inspection of generated geometry.

---

## 🌟 Key Features

* **AI-Driven Generation:** Utilize prompting to generate complex 3D structures via Python logic.
* **Procedural Workflows:** Full support for OpenSCAD (.scad) and Stereolithography (.stl) exports.
* **Real-time Preview:** * **Local HTTP Server:** Host your models locally for browser-based viewing.
    * **Desktop Viewer:** A native Windows window for high-performance geometry inspection.
* **Automation:** Batch scripts for seamless environment setup and execution.

---

## 🛠️ Installation (Windows)

1.  **Clone the Repository:**
    ```bash
    git clone https://github.com/yabdelsa2862-lab/3D-Modeler
    cd 3D-Modeler
    ```

2.  **Install Dependencies:**
    It is recommended to use a virtual environment.
    ```bash
    pip install -r requirements.txt
    ```

3.  **Verify Environment:**
    ```bash
    python --version
    pip list
    ```

---

## 🚀 Usage

| Action | Command |
| :--- | :--- |
| **Start Local Server** | `python server.py` |
| **Open 3D Viewer** | `python window.py` |
| **Generate Models** | `python generation.py` |
| **Full Automation** | `run.bat` |

---

## 📂 Folder Structure

* `models/` — Storage for Python scripts, SCAD source code, and final STL outputs.
* `generation.py` — The core logic handling AI prompting and 3D object creation.
* `server.py` — A micro-server utility to host 3D assets for remote or browser viewing.
* `window.py` — A PyQT/OpenGL-based desktop viewer for Windows.
* `run.bat` — One-click launcher to initialize the server and viewer simultaneously.
* `requirements.txt` — List of necessary Python libraries (e.g., SolidPython, NumPy).

---

## ⚖️ License

**Maintained by Yousef Mohamed Nazmi.** All rights reserved. Unauthorized distribution or commercial use is prohibited unless otherwise stated.
