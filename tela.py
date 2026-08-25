import sys
from PySide6.QtWidgets import (
    QApplication, QMainWindow, QWidget, QVBoxLayout, QHBoxLayout,
    QLabel, QPushButton, QCheckBox, QDialog, QFrame
)
from PySide6.QtCore import Qt


class ClickableFrame(QFrame):
    """QFrame customizado para aceitar eventos de clique de mouse."""
    def __init__(self, click_callback, parent=None):
        super().__init__(parent)
        self.click_callback = click_callback

    def mousePressEvent(self, event):
        if event.button() == Qt.MouseButton.LeftButton:
            self.click_callback()
        super().mousePressEvent(event)


class SettingsDialog(QDialog):
    """Janela flutuante de configurações/filtros."""
    def __init__(self, car_parts_data, parent=None):
        super().__init__(parent)
        self.car_parts_data = car_parts_data

        self.setWindowFlags(Qt.WindowType.FramelessWindowHint | Qt.WindowType.Dialog)
        self.setModal(True)
        self.setFixedSize(350, 250)
        self.setStyleSheet("QDialog { background-color: #f0f0f0; border: 2px solid #45aafa; }")

        layout = QVBoxLayout(self)
        layout.setContentsMargins(20, 15, 20, 15)

        title = QLabel("SELECIONE AS PARTES VISÍVEIS:")
        title.setStyleSheet("font-family: Arial; font-size: 11pt; font-weight: bold; color: black; border: none;")
        layout.addWidget(title, alignment=Qt.AlignmentFlag.AlignCenter)

        self.checkbox_items = []
        for part in self.car_parts_data:
            chk = QCheckBox(part["name"])
            chk.setChecked(part["enabled"])
            chk.setStyleSheet("font-family: Arial; font-size: 10pt; color: black; border: none; padding-left: 20px;")
            layout.addWidget(chk)
            self.checkbox_items.append((part, chk))

        btn_close = QPushButton("APLICAR E FECHAR")
        btn_close.setCursor(Qt.CursorShape.PointingHandCursor)
        btn_close.setStyleSheet("font-family: Arial; font-size: 9pt; font-weight: bold; padding: 6px 12px;")
        btn_close.clicked.connect(self.apply_and_close)
        layout.addWidget(btn_close, alignment=Qt.AlignmentFlag.AlignCenter)

    def apply_and_close(self):
        for part, chk in self.checkbox_items:
            part["enabled"] = chk.isChecked()
        self.accept()


class SensorPopOverDialog(QDialog):
    """Janela flutuante para detalhes dos sensores."""
    def __init__(self, part_data, parent=None):
        super().__init__(parent)
        self.setWindowFlags(Qt.WindowType.FramelessWindowHint | Qt.WindowType.Dialog)
        self.setModal(True)
        self.setFixedSize(450, 300)
        self.setStyleSheet("QDialog { background-color: #f0f0f0; border: 2px solid #45aafa; }")

        layout = QVBoxLayout(self)
        layout.setContentsMargins(20, 15, 20, 15)

        title = QLabel(f"SENSORES: {part_data['name']}")
        title.setStyleSheet("font-family: Arial; font-size: 12pt; font-weight: bold; color: black; border: none;")
        layout.addWidget(title, alignment=Qt.AlignmentFlag.AlignCenter)

        sensor_frame = QFrame()
        sensor_frame.setStyleSheet("background-color: white; border: 1px solid #cccccc;")
        sensor_layout = QVBoxLayout(sensor_frame)
        sensor_layout.setContentsMargins(15, 10, 15, 10)

        for sensor_name, value in part_data['sensors']:
            item_label = QLabel(f"⚙️  {sensor_name}: {value}")
            item_label.setStyleSheet("font-family: Arial; font-size: 10pt; color: black; border: none; background: transparent;")
            sensor_layout.addWidget(item_label)

        sensor_layout.addStretch()
        layout.addWidget(sensor_frame)

        btn_close = QPushButton("FECHAR JANELA")
        btn_close.setCursor(Qt.CursorShape.PointingHandCursor)
        btn_close.setStyleSheet("font-family: Arial; font-size: 9pt; font-weight: bold; padding: 6px 12px;")
        btn_close.clicked.connect(self.accept)
        layout.addWidget(btn_close, alignment=Qt.AlignmentFlag.AlignCenter)


class CarMultimediaApp(QMainWindow):
    def __init__(self):
        super().__init__()
        self.setWindowTitle("Multimídia do Carro - Filtro de Partes")
        self.resize(800, 480)
        self.setStyleSheet("background-color: white;")

        self.car_parts_data = [
            {
                "name": "MOTOR E SISTEMAS",
                "enabled": True,
                "sensors": [
                    ("Temp. Arrefecimento", "90°C (Normal)"),
                    ("Pressão do Óleo", "3.5 bar (Estável)"),
                    ("Voltagem Bateria", "13.8V (Carregando)")
                ]
            },
            {
                "name": "FREIOS E SUSPENSÃO",
                "enabled": True,
                "sensors": [
                    ("Pastilhas Dianteiras", "75% Restante"),
                    ("Pastilhas Traseiras", "80% Restante"),
                    ("Alinhamento", "Normal")
                ]
            },
            {
                "name": "CHASSI E PNEUS",
                "enabled": True,
                "sensors": [
                    ("Pressão Pneus", "32 PSI (Todos)"),
                    ("Controle Tração", "Ativo")
                ]
            }
        ]

        self.current_part_index = 0

        # Widget central
        central_widget = QWidget()
        self.setCentralWidget(central_widget)
        self.main_layout = QVBoxLayout(central_widget)
        self.main_layout.setContentsMargins(0, 0, 0, 0)
        self.main_layout.setSpacing(0)

        self.create_top_bar()
        self.create_map_area()
        self.create_bottom_area()
        self.update_car_display()

    def create_top_bar(self):
        top_bar = QWidget()
        top_bar.setFixedHeight(30)
        top_bar.setStyleSheet("background-color: #666666;")

        layout = QHBoxLayout(top_bar)
        layout.setContentsMargins(20, 0, 20, 0)
        layout.addStretch()

        status_label = QLabel("Bluetooth: ON   |   Wi-Fi: Conectado   |   Bateria: 85%")
        status_label.setStyleSheet("color: white; font-family: Arial; font-size: 10pt; font-weight: bold;")
        layout.addWidget(status_label)

        self.main_layout.addWidget(top_bar)

    def create_map_area(self):
        container = QWidget()
        container.setStyleSheet("background-color: white;")
        
        layout = QVBoxLayout(container)
        layout.setContentsMargins(40, 10, 40, 10)

        map_frame = QFrame()
        map_frame.setStyleSheet("background-color: #45aafa; border: 2px solid #2d8bd6;")
        
        map_layout = QVBoxLayout(map_frame)
        map_label = QLabel("MAPA")
        map_label.setAlignment(Qt.AlignmentFlag.AlignCenter)
        map_label.setStyleSheet("color: white; font-family: Arial; font-size: 16pt; font-weight: bold; border: none;")
        map_layout.addWidget(map_label)

        layout.addWidget(map_frame)
        self.main_layout.addWidget(container, stretch=1)

    def create_bottom_area(self):
        bottom_container = QWidget()
        bottom_container.setFixedHeight(100)
        bottom_container.setStyleSheet("background-color: white;")

        bottom_layout = QHBoxLayout(bottom_container)
        bottom_layout.setContentsMargins(40, 0, 40, 20)
        bottom_layout.setSpacing(10)

        # Painel Esquerdo
        left_panel = QWidget()
        left_layout = QHBoxLayout(left_panel)
        left_layout.setContentsMargins(0, 0, 0, 0)
        left_layout.setSpacing(5)

        prev_btn = QPushButton("◀")
        prev_btn.setFixedWidth(40)
        prev_btn.setFixedHeight(80)
        prev_btn.setCursor(Qt.CursorShape.PointingHandCursor)
        prev_btn.setStyleSheet("font-size: 20pt; color: #555555; background-color: white; border: none;")
        prev_btn.clicked.connect(self.prev_part)
        left_layout.addWidget(prev_btn)

        self.car_view_frame = ClickableFrame(self.open_sensor_pop_over)
        self.car_view_frame.setStyleSheet("background-color: #777777; border: 1px solid #555555;")
        self.car_view_frame.setCursor(Qt.CursorShape.PointingHandCursor)

        frame_layout = QVBoxLayout(self.car_view_frame)
        frame_layout.setContentsMargins(5, 5, 5, 5)

        self.car_part_title_label = QLabel("")
        self.car_part_title_label.setAlignment(Qt.AlignmentFlag.AlignCenter)
        self.car_part_title_label.setStyleSheet("color: white; font-family: Arial; font-size: 11pt; font-weight: bold; border: none; background: transparent;")
        frame_layout.addWidget(self.car_part_title_label)

        self.instrucao_label = QLabel("(Clique para ver sensores)")
        self.instrucao_label.setAlignment(Qt.AlignmentFlag.AlignCenter)
        self.instrucao_label.setStyleSheet("color: #eeeeee; font-family: Arial; font-size: 8pt; border: none; background: transparent;")
        frame_layout.addWidget(self.instrucao_label)

        left_layout.addWidget(self.car_view_frame, stretch=1)

        next_btn = QPushButton("▶")
        next_btn.setFixedWidth(40)
        next_btn.setFixedHeight(80)
        next_btn.setCursor(Qt.CursorShape.PointingHandCursor)
        next_btn.setStyleSheet("font-size: 20pt; color: #555555; background-color: white; border: none;")
        next_btn.clicked.connect(self.next_part)
        left_layout.addWidget(next_btn)

        bottom_layout.addWidget(left_panel, stretch=1)

        # Painel Direito
        config_btn = QPushButton("⚙️ Filtrar\nPartes")
        config_btn.setFixedWidth(150)
        config_btn.setFixedHeight(80)
        config_btn.setCursor(Qt.CursorShape.PointingHandCursor)
        config_btn.setStyleSheet("font-family: Arial; font-size: 10pt; font-weight: bold; background-color: #e0e0e0; color: #333333; border: 1px solid #b0b0b0;")
        config_btn.clicked.connect(self.open_settings_window)

        bottom_layout.addWidget(config_btn)
        self.main_layout.addWidget(bottom_container)

    def get_active_parts(self):
        return [part for part in self.car_parts_data if part["enabled"]]

    def prev_part(self):
        active_parts = self.get_active_parts()
        if not active_parts:
            return

        self.current_part_index -= 1
        if self.current_part_index < 0:
            self.current_part_index = len(active_parts) - 1
        self.update_car_display()

    def next_part(self):
        active_parts = self.get_active_parts()
        if not active_parts:
            return

        self.current_part_index += 1
        if self.current_part_index >= len(active_parts):
            self.current_part_index = 0
        self.update_car_display()

    def update_car_display(self):
        active_parts = self.get_active_parts()

        if not active_parts:
            self.car_part_title_label.setText("⚠️ NENHUMA PARTE SELECIONADA")
            self.instrucao_label.setText("Use o botão 'Filtrar Partes' ao lado")
            return

        if self.current_part_index >= len(active_parts):
            self.current_part_index = 0

        part_name = active_parts[self.current_part_index]['name']
        self.car_part_title_label.setText(f"PARTE ATUAL:\n{part_name}")
        self.instrucao_label.setText("(Clique para ver sensores)")

    def _center_dialog(self, dialog):
        geo = self.geometry()
        x = geo.x() + (geo.width() - dialog.width()) // 2
        y = geo.y() + (geo.height() - dialog.height()) // 2
        dialog.move(x, y)

    def open_settings_window(self):
        dialog = SettingsDialog(self.car_parts_data, self)
        self._center_dialog(dialog)
        if dialog.exec():
            self.update_car_display()

    def open_sensor_pop_over(self):
        active_parts = self.get_active_parts()
        if not active_parts:
            return

        part_data = active_parts[self.current_part_index]
        dialog = SensorPopOverDialog(part_data, self)
        self._center_dialog(dialog)
        dialog.exec()


if __name__ == "__main__":
    app = QApplication(sys.argv)
    window = CarMultimediaApp()
    window.show()
    sys.exit(app.exec())