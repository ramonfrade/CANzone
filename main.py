import sys
from PySide6.QtWidgets import (QApplication, QMainWindow, QStackedWidget, 
                               QWidget, QVBoxLayout, QLabel, QPushButton)
import time
from PySide6.QtCore import QThread, Signal

class CANDataThread(QThread):
    data_updated = Signal(int, int)

    def __init__(self):
        super().__init__()
        self.is_running = True

    def run(self):
        rpm = 800
        speed = 0

        while self.is_running:
            # -- Simulação de dados --
            rpm += 150
            speed += 3
            
            # Reseta os valores para dar um efeito de loop na simulação
            if rpm > 6000:
                rpm = 800
            if speed > 120:
                speed = 0

            self.data_updated.emit(rpm, speed)

            time.sleep(0.1)

    def stop(self):
        self.is_running = False
        self.wait()

# -- Telas --
class ScreenHome(QWidget):
    def __init__(self):
        super().__init__()
        layout = QVBoxLayout()
        layout.addWidget(QLabel("Tela Inicial (Home)"))
        
        self.btn_go_dashboard = QPushButton("Ir para o Dashboard")
        layout.addWidget(self.btn_go_dashboard)
        
        self.setLayout(layout)

class ScreenDashboard(QWidget):
    def __init__(self):
        super().__init__()
        layout = QVBoxLayout()
        layout.addWidget(QLabel("Dashboard (Dados CAN Simulados)"))
        
        self.lbl_rpm = QLabel("RPM: 0")
        self.lbl_speed = QLabel("Velocidade: 0 km/h")
        
        font = self.lbl_rpm.font()
        font.setPointSize(24)
        self.lbl_rpm.setFont(font)
        self.lbl_speed.setFont(font)

        layout.addWidget(self.lbl_rpm)
        layout.addWidget(self.lbl_speed)
        
        self.btn_go_home = QPushButton("Voltar para Home")
        layout.addWidget(self.btn_go_home)
        
        self.setLayout(layout)

    def update_dashboard_data(self, rpm, speed):
        self.lbl_rpm.setText(f"RPM: {rpm}")
        self.lbl_speed.setText(f"Velocidade: {speed} km/h")

# -- Janela Principal --
class MainWindow(QMainWindow):
    def __init__(self):
        super().__init__()
        self.setWindowTitle("CANzone - MVP")
        self.resize(800, 480) 

        self.stacked_widget = QStackedWidget()
        self.setCentralWidget(self.stacked_widget)

        self.screen_home = ScreenHome()
        self.screen_dashboard = ScreenDashboard()

        self.stacked_widget.addWidget(self.screen_home)
        self.stacked_widget.addWidget(self.screen_dashboard)

        self.screen_home.btn_go_dashboard.clicked.connect(self.go_to_dashboard)
        self.screen_dashboard.btn_go_home.clicked.connect(self.go_to_home)

        self.can_thread = CANDataThread()
        
        self.can_thread.data_updated.connect(self.screen_dashboard.update_dashboard_data)
        
        self.can_thread.start()

    def go_to_dashboard(self):
        self.stacked_widget.setCurrentIndex(1)

    def go_to_home(self):
        self.stacked_widget.setCurrentIndex(0)

    def closeEvent(self, event):
        print("Encerrando a aplicação e parando as threads...")
        self.can_thread.stop()
        event.accept()

if __name__ == "__main__":
    app = QApplication(sys.argv)
    window = MainWindow()
    window.show()
    sys.exit(app.exec())