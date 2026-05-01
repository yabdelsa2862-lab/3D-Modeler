"""
OpenGL 3D viewport widget for Forge 3D.
Uses fixed-function OpenGL via PyOpenGL — no shaders needed.
"""
import numpy as np
from PySide6.QtOpenGLWidgets import QOpenGLWidget
from PySide6.QtCore import Qt, QPoint, QTimer
from PySide6.QtGui import QSurfaceFormat, QFont, QPainter, QColor, QPen

try:
    from OpenGL.GL import *
    from OpenGL.GLU import *
    HAS_GL = True
except ImportError:
    HAS_GL = False


def _setup_format():
    fmt = QSurfaceFormat()
    fmt.setSamples(4)
    fmt.setDepthBufferSize(24)
    fmt.setSwapInterval(1)
    QSurfaceFormat.setDefaultFormat(fmt)


_setup_format()


class Viewport3D(QOpenGLWidget):
    def __init__(self, parent=None):
        super().__init__(parent)

        # ── Camera ──────────────────────────────────────────
        self.azimuth   = -40.0
        self.elevation =  22.0
        self.distance  = 300.0
        self.target    = np.array([0.0, 0.0, 0.0])

        # ── Mesh data ────────────────────────────────────────
        self.vertices = None
        self.normals  = None
        self.faces    = None
        self.has_model = False
        self._display_list = None

        # ── Render options ───────────────────────────────────
        self.show_grid      = True
        self.wireframe      = False
        self.model_color    = (0.18, 0.48, 1.0)   # Apple blue

        # ── Mouse tracking ───────────────────────────────────
        self._last_pos  = None
        self._mouse_btn = None

        self.setMinimumSize(300, 200)
        self.setFocusPolicy(Qt.StrongFocus)

    # ── OpenGL lifecycle ─────────────────────────────────────────────────────

    def initializeGL(self):
        if not HAS_GL:
            return

        glEnable(GL_DEPTH_TEST)
        glEnable(GL_MULTISAMPLE)
        glEnable(GL_LIGHTING)
        glEnable(GL_LIGHT0)   # key light  (warm, top-right-front)
        glEnable(GL_LIGHT1)   # fill light (cool, left-back)
        glEnable(GL_LIGHT2)   # rim  light (subtle, bottom-front)
        glEnable(GL_COLOR_MATERIAL)
        glEnable(GL_NORMALIZE)
        glShadeModel(GL_SMOOTH)
        glColorMaterial(GL_FRONT_AND_BACK, GL_AMBIENT_AND_DIFFUSE)

        # Background
        glClearColor(0.031, 0.031, 0.055, 1.0)

        # Key light — warm white, directional
        glLightfv(GL_LIGHT0, GL_POSITION, [ 1.2,  2.0,  1.5, 0.0])
        glLightfv(GL_LIGHT0, GL_DIFFUSE,  [ 1.0,  0.97, 0.93, 1.0])
        glLightfv(GL_LIGHT0, GL_SPECULAR, [ 0.6,  0.6,  0.6, 1.0])
        glLightfv(GL_LIGHT0, GL_AMBIENT,  [ 0.0,  0.0,  0.0, 1.0])

        # Fill light — cool blue
        glLightfv(GL_LIGHT1, GL_POSITION, [-1.5,  0.5, -1.2, 0.0])
        glLightfv(GL_LIGHT1, GL_DIFFUSE,  [ 0.25, 0.35, 0.55, 1.0])
        glLightfv(GL_LIGHT1, GL_SPECULAR, [ 0.0,  0.0,  0.0, 1.0])
        glLightfv(GL_LIGHT1, GL_AMBIENT,  [ 0.0,  0.0,  0.0, 1.0])

        # Rim light — subtle, from below-front
        glLightfv(GL_LIGHT2, GL_POSITION, [ 0.0, -1.0,  1.8, 0.0])
        glLightfv(GL_LIGHT2, GL_DIFFUSE,  [ 0.12, 0.18, 0.28, 1.0])
        glLightfv(GL_LIGHT2, GL_SPECULAR, [ 0.0,  0.0,  0.0, 1.0])
        glLightfv(GL_LIGHT2, GL_AMBIENT,  [ 0.0,  0.0,  0.0, 1.0])

        # Global ambient — very dark
        glLightModelfv(GL_LIGHT_MODEL_AMBIENT, [0.08, 0.08, 0.12, 1.0])

        # Material specular
        glMaterialfv(GL_FRONT_AND_BACK, GL_SPECULAR,  [0.35, 0.35, 0.35, 1.0])
        glMaterialf (GL_FRONT_AND_BACK, GL_SHININESS, 48.0)

    def resizeGL(self, w, h):
        if not HAS_GL or h == 0:
            return
        glViewport(0, 0, w, h)
        glMatrixMode(GL_PROJECTION)
        glLoadIdentity()
        gluPerspective(42.0, w / h, 0.5, 10000.0)
        glMatrixMode(GL_MODELVIEW)

    def paintGL(self):
        if not HAS_GL:
            return
        glClear(GL_COLOR_BUFFER_BIT | GL_DEPTH_BUFFER_BIT)
        glLoadIdentity()

        # Camera position from spherical coords
        az  = np.radians(self.azimuth)
        el  = np.radians(self.elevation)
        eye = self.target + self.distance * np.array([
            np.cos(el) * np.sin(az),
            np.sin(el),
            np.cos(el) * np.cos(az),
        ])
        gluLookAt(eye[0], eye[1], eye[2],
                  self.target[0], self.target[1], self.target[2],
                  0.0, 1.0, 0.0)

        if self.show_grid:
            self._draw_grid()

        if self.has_model:
            self._draw_model()

    def _draw_grid(self):
        glDisable(GL_LIGHTING)
        glLineWidth(1.0)

        SIZE, STEP = 250, 25

        # Minor grid
        glColor3f(0.07, 0.07, 0.13)
        glBegin(GL_LINES)
        for i in range(-SIZE, SIZE + STEP, STEP):
            glVertex3f(i, 0, -SIZE); glVertex3f(i, 0,  SIZE)
            glVertex3f(-SIZE, 0, i); glVertex3f( SIZE, 0, i)
        glEnd()

        # Axes
        glLineWidth(1.5)
        glColor3f(0.18, 0.18, 0.30)
        glBegin(GL_LINES)
        glVertex3f(-SIZE, 0, 0); glVertex3f(SIZE, 0, 0)
        glVertex3f(0, 0, -SIZE); glVertex3f(0, 0, SIZE)
        glEnd()
        glLineWidth(1.0)

        glEnable(GL_LIGHTING)

    def _draw_model(self):
        if self._display_list is not None:
            glColor3f(*self.model_color)
            if self.wireframe:
                glDisable(GL_LIGHTING)
                glColor3f(0.4, 0.65, 1.0)
                glPolygonMode(GL_FRONT_AND_BACK, GL_LINE)
            glCallList(self._display_list)
            if self.wireframe:
                glPolygonMode(GL_FRONT_AND_BACK, GL_FILL)
                glEnable(GL_LIGHTING)

    def _build_display_list(self):
        """Compile geometry into an OpenGL display list for fast redraw."""
        if self._display_list is not None:
            glDeleteLists(self._display_list, 1)

        self._display_list = glGenLists(1)
        glNewList(self._display_list, GL_COMPILE)
        glBegin(GL_TRIANGLES)
        for face in self.faces:
            for vi in face:
                glNormal3fv(self.normals[vi].tolist())
                glVertex3fv(self.vertices[vi].tolist())
        glEnd()
        glEndList()

    # ── Mesh loading ─────────────────────────────────────────────────────────

    def load_stl(self, stl_path):
        """Load an STL file and display it."""
        import trimesh
        import warnings
        self.makeCurrent()   # ensure correct GL context

        # Suppress the scipy-missing fallback noise — trimesh handles it fine
        with warnings.catch_warnings():
            warnings.simplefilter("ignore")
            m = trimesh.load(str(stl_path), force="mesh")
        try:
            m.merge_vertices()
            m.remove_degenerate_faces()
        except Exception:
            pass

        verts = m.vertices.copy().astype(np.float32)

        # Convert trimesh z-up → OpenGL y-up: (x,y,z)→(x,z,y)
        verts_gl = verts[:, [0, 2, 1]]

        # Centre and normalise to ~100 units
        lo, hi   = verts_gl.min(0), verts_gl.max(0)
        span     = hi - lo
        max_span = max(span.max(), 1e-6)
        scale    = 100.0 / max_span
        center   = (lo + hi) * 0.5
        center[1] = lo[1]          # sit on y=0
        verts_gl  = (verts_gl - center) * scale

        self.vertices = verts_gl
        # Normals use same axis swap
        n = m.vertex_normals.astype(np.float32)
        self.normals = n[:, [0, 2, 1]]
        self.faces   = m.faces

        # Update camera
        bb_size = (verts_gl.max(0) - verts_gl.min(0))
        self.distance = max(bb_size) * 2.6
        self.target   = np.array([0.0, verts_gl[:,1].max() * 0.5, 0.0])

        self.has_model = True
        self._build_display_list()
        self.update()

    # ── Controls ─────────────────────────────────────────────────────────────

    def reset_view(self):
        self.azimuth   = -40.0
        self.elevation =  22.0
        if self.has_model and self.vertices is not None:
            bb = self.vertices.max(0) - self.vertices.min(0)
            self.distance = max(bb) * 2.6
            self.target   = np.array([0.0, self.vertices[:,1].max()*0.5, 0.0])
        self.update()

    def toggle_wireframe(self):
        self.wireframe = not self.wireframe
        self.update()
        return self.wireframe

    def toggle_grid(self):
        self.show_grid = not self.show_grid
        self.update()
        return self.show_grid

    # ── Mouse ────────────────────────────────────────────────────────────────

    def mousePressEvent(self, e):
        self._last_pos  = e.position().toPoint()
        self._mouse_btn = e.button()

    def mouseMoveEvent(self, e):
        if self._last_pos is None:
            return
        dx = e.position().x() - self._last_pos.x()
        dy = e.position().y() - self._last_pos.y()

        if self._mouse_btn == Qt.LeftButton:
            self.azimuth   += dx * 0.45
            self.elevation  = float(np.clip(self.elevation - dy * 0.45, -89, 89))

        elif self._mouse_btn == Qt.RightButton:
            az  = np.radians(self.azimuth)
            spd = self.distance * 0.0025
            self.target[0] -= np.cos(az) * dx * spd
            self.target[2] += np.sin(az) * dx * spd
            self.target[1] += dy * spd

        self._last_pos = e.position().toPoint()
        self.update()

    def mouseReleaseEvent(self, e):
        self._last_pos  = None
        self._mouse_btn = None

    def wheelEvent(self, e):
        factor = 0.87 if e.angleDelta().y() > 0 else 1.15
        self.distance = float(np.clip(self.distance * factor, 5.0, 8000.0))
        self.update()
