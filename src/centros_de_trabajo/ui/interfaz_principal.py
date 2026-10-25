import sys
from PyQt6.QtWidgets import QApplication, QMainWindow, QPushButton, QGridLayout, QWidget
from PyQt6.QtCore import Qt, QTimer
from PyQt6.QtGui import QShortcut, QKeySequence

class InterfazVenta(QMainWindow):
    def __init__(self):
        super().__init__()
        self.setWindowTitle("POS Colectivo - Prototipo UI")
        self.showFullScreen()
        
        # Contenedor y Layout
        container = QWidget()
        layout = QGridLayout() # Organización 2x2
        self.botones = {}

        # Configuración de botones: (ID, Texto, Tecla)
        config_botones = [
            (1, "Iniciar Proceso", "F1"),
            (2, "Pausar Proceso", "F2"),
            (3, "Reanudar Proceso", "F3"),
            (4, "Finalizar Proceso", "F4"),
        ]

        for i, (bid, texto, tecla) in enumerate(config_botones):
            # Crear botón con texto y tecla asignada
            btn = QPushButton(f"{texto}\n[{tecla}]")
            btn.setStyleSheet(self.get_style("#3498db")) # Azul por defecto
            
            # 1. Al hacer click manual o via animateClick()
            btn.clicked.connect(lambda checked, b=bid: self.feedback_visual(b))
            
            # 2. Atajo de teclado (F1, F2, F3 o F4)
            shortcut = QShortcut(QKeySequence(tecla), self)
            shortcut.activated.connect(btn.animateClick) # animateClick visualiza el click y dispara el evento
            
            self.botones[bid] = btn
            layout.addWidget(btn, i // 2, i % 2)

        container.setLayout(layout)
        self.setCentralWidget(container)

        # Atajo de salida para desarrollador: Ctrl+Alt+S
        exit_sc = QShortcut(QKeySequence("Ctrl+Alt+S"), self)
        exit_sc.activated.connect(QApplication.quit)

    def get_style(self, color):
        """Genera el estilo CSS para los botones"""
        return f"""
            QPushButton {{
                font-size: 40px;
                font-weight: bold;
                background-color: {color};
                color: white;
                border-radius: 20px;
                margin: 15px;
                border: 4px solid #2980b9;
            }}
        """

    def feedback_visual(self, boton_id):
        """Cambia el color del botón brevemente para indicar activación"""
        btn = self.botones[boton_id]
        # Cambiar a Naranja para resaltar la activación
        btn.setStyleSheet(self.get_style("#f39c12")) 
        
        # Volver al color original tras 300ms
        QTimer.singleShot(300, lambda: btn.setStyleSheet(self.get_style("#3498db")))
        print(f"Boton {boton_id} activado")

if __name__ == "__main__":
    app = QApplication(sys.argv)
    ventana = InterfazVenta()
    ventana.show()
    sys.exit(app.exec())