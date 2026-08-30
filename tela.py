import sys
import time

from PySide6.QtCore import QThread, Qt, Signal
from PySide6.QtWidgets import (
    QApplication,
    QCheckBox,
    QDialog,
    QFrame,
    QHBoxLayout,
    QLabel,
    QMainWindow,
    QPushButton,
    QVBoxLayout,
    QWidget,
)

from janela_mapa import MapaWidget


# ==============================================================================
# 1. THREAD DE DADOS CAN (SIMULAÇÃO)
# ==============================================================================
class CANDataThread(QThread):
    data_updated = Signal(int, int)

    def __init__(self):
        super().__init__()
        self.is_running = True

    def run(self):
        rpm = 800
        speed = 0

        while self.is_running:
            rpm += 150
            speed += 3

            if rpm > 6000:
                rpm = 800
            if speed > 120:
                speed = 0

            self.data_updated.emit(rpm, speed)
            time.sleep(0.1)

    def stop(self):
        self.is_running = False
        self.wait()


# ==============================================================================
# 2. PAINÉIS E JANELAS SECUNDÁRIAS
# ==============================================================================
class ClickableFrame(QFrame):
    def __init__(self, click_callback, parent=None):
        super().__init__(parent)
        self.click_callback = click_callback

    def mousePressEvent(self, event):
        if event.button() == Qt.MouseButton.LeftButton:
            self.click_callback()
        super().mousePressEvent(event)


class SettingsDialog(QDialog):
    def __init__(self, car_parts_data, modo_escuro=False, parent=None):
        super().__init__(parent)
        self.car_parts_data = car_parts_data

        self.setWindowFlags(Qt.WindowType.FramelessWindowHint | Qt.WindowType.Dialog)
        self.setModal(True)
        self.setFixedSize(350, 250)

        bg_color = "#1e293b" if modo_escuro else "#f0f0f0"
        txt_color = "#ffffff" if modo_escuro else "#000000"
        border_color = "#45aafa"

        self.setStyleSheet(f"QDialog {{ background-color: {bg_color}; border: 2px solid {border_color}; }}")

        layout = QVBoxLayout(self)
        layout.setContentsMargins(20, 15, 20, 15)

        title = QLabel("SELECIONE AS PARTES VISÍVEIS:")
        title.setStyleSheet(f"font-family: Arial; font-size: 11pt; font-weight: bold; color: {txt_color}; border: none;")
        layout.addWidget(title, alignment=Qt.AlignmentFlag.AlignCenter)

        self.checkbox_items = []
        for part in self.car_parts_data:
            chk = QCheckBox(part["name"])
            chk.setChecked(part["enabled"])
            chk.setStyleSheet(f"font-family: Arial; font-size: 10pt; color: {txt_color}; border: none; padding-left: 20px;")
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
    def __init__(self, part_data, modo_escuro=False, parent=None):
        super().__init__(parent)
        self.part_data = part_data
        self.sensor_labels = {}

        self.setWindowFlags(Qt.WindowType.FramelessWindowHint | Qt.WindowType.Dialog)
        self.setModal(True)
        self.setFixedSize(450, 300)

        bg_color = "#1e293b" if modo_escuro else "#f0f0f0"
        frame_bg = "#0f172a" if modo_escuro else "#ffffff"
        txt_color = "#ffffff" if modo_escuro else "#000000"
        border_color = "#45aafa"
        frame_border = "#334155" if modo_escuro else "#cccccc"

        self.setStyleSheet(f"QDialog {{ background-color: {bg_color}; border: 2px solid {border_color}; }}")

        layout = QVBoxLayout(self)
        layout.setContentsMargins(20, 15, 20, 15)

        title = QLabel(f"SENSORES: {part_data['name']}")
        title.setStyleSheet(f"font-family: Arial; font-size: 12pt; font-weight: bold; color: {txt_color}; border: none;")
        layout.addWidget(title, alignment=Qt.AlignmentFlag.AlignCenter)

        sensor_frame = QFrame()
        sensor_frame.setStyleSheet(f"background-color: {frame_bg}; border: 1px solid {frame_border};")
        sensor_layout = QVBoxLayout(sensor_frame)
        sensor_layout.setContentsMargins(15, 10, 15, 10)

        for sensor_item in part_data['sensors']:
            sensor_name, value = sensor_item[0], sensor_item[1]
            item_label = QLabel(f"⚙️  {sensor_name}: {value}")
            item_label.setStyleSheet(f"font-family: Arial; font-size: 10pt; color: {txt_color}; border: none; background: transparent;")
            sensor_layout.addWidget(item_label)
            self.sensor_labels[sensor_name] = item_label

        sensor_layout.addStretch()
        layout.addWidget(sensor_frame)

        btn_close = QPushButton("FECHAR JANELA")
        btn_close.setCursor(Qt.CursorShape.PointingHandCursor)
        btn_close.setStyleSheet("font-family: Arial; font-size: 9pt; font-weight: bold; padding: 6px 12px;")
        btn_close.clicked.connect(self.accept)
        layout.addWidget(btn_close, alignment=Qt.AlignmentFlag.AlignCenter)

    def refresh_sensor_values(self):
        for sensor_item in self.part_data['sensors']:
            sensor_name, value = sensor_item[0], sensor_item[1]
            if sensor_name in self.sensor_labels:
                self.sensor_labels[sensor_name].setText(f"⚙️  {sensor_name}: {value}")


# ==============================================================================
# 3. APLICAÇÃO PRINCIPAL
# ==============================================================================
class CarMultimediaApp(QMainWindow):
    def __init__(self):
        super().__init__()
        self.setWindowTitle("Multimídia do Carro - Filtro de Partes")
        self.resize(800, 480)

        self.modo_escuro = False

        self.car_parts_data = [
            {
                "name": "MOTOR E SISTEMAS",
                "enabled": True,
                "sensors": [
                    ["RPM", "800 RPM"],
                    ["Velocidade", "0 km/h"],
                    ["Temp. Arrefecimento", "90°C (Normal)"],
                    ["Pressão do Óleo", "3.5 bar (Estável)"],
                    ["Voltagem Bateria", "13.8V (Carregando)"]
                ]
            },
            {
                "name": "FREIOS E SUSPENSÃO",
                "enabled": True,
                "sensors": [
                    ["Pastilhas Dianteiras", "75% Restante"],
                    ["Pastilhas Traseiras", "80% Restante"],
                    ["Alinhamento", "Normal"]
                ]
            },
            {
                "name": "CHASSI E PNEUS",
                "enabled": True,
                "sensors": [
                    ["Pressão Pneus", "32 PSI (Todos)"],
                    ["Controle Tração", "Ativo"]
                ]
            }
        ]

        self.current_part_index = 0
        self.active_pop_over = None

        central_widget = QWidget()
        self.setCentralWidget(central_widget)
        self.main_layout = QVBoxLayout(central_widget)
        self.main_layout.setContentsMargins(0, 0, 0, 0)
        self.main_layout.setSpacing(0)

        self.create_top_bar()
        self.create_map_area()
        self.create_bottom_area()

        self.aplicar_tema()
        self.update_car_display()

        # Thread de dados CAN
        self.can_thread = CANDataThread()
        self.can_thread.data_updated.connect(self.update_can_data)
        self.can_thread.start()

    def create_top_bar(self):
        self.top_bar = QWidget()
        self.top_bar.setFixedHeight(35)

        layout = QHBoxLayout(self.top_bar)
        layout.setContentsMargins(15, 0, 15, 0)

        # Botão para alternar tema
        self.btn_tema = QPushButton("🌙 Modo Escuro")
        self.btn_tema.setCursor(Qt.CursorShape.PointingHandCursor)
        self.btn_tema.clicked.connect(self.alternar_tema)
        layout.addWidget(self.btn_tema)

        layout.addStretch()

        self.status_label = QLabel("Bluetooth: ON   |   Wi-Fi: Conectado   |   Bateria: 85%")
        self.status_label.setStyleSheet("color: white; font-family: Arial; font-size: 10pt; font-weight: bold;")
        layout.addWidget(self.status_label)

        self.main_layout.addWidget(self.top_bar)

    def create_map_area(self):
        self.map_container = QWidget()

        layout = QVBoxLayout(self.map_container)
        layout.setContentsMargins(40, 10, 40, 10)

        self.mapa_widget = MapaWidget()
        layout.addWidget(self.mapa_widget)

        self.main_layout.addWidget(self.map_container, stretch=1)

    def create_bottom_area(self):
        self.bottom_container = QWidget()
        self.bottom_container.setFixedHeight(100)

        bottom_layout = QHBoxLayout(self.bottom_container)
        bottom_layout.setContentsMargins(40, 0, 40, 20)
        bottom_layout.setSpacing(10)

        # Painel Esquerdo
        left_panel = QWidget()
        left_layout = QHBoxLayout(left_panel)
        left_layout.setContentsMargins(0, 0, 0, 0)
        left_layout.setSpacing(5)

        self.prev_btn = QPushButton("◀")
        self.prev_btn.setFixedWidth(40)
        self.prev_btn.setFixedHeight(80)
        self.prev_btn.setCursor(Qt.CursorShape.PointingHandCursor)
        self.prev_btn.clicked.connect(self.prev_part)
        left_layout.addWidget(self.prev_btn)

        self.car_view_frame = ClickableFrame(self.open_sensor_pop_over)
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

        self.next_btn = QPushButton("▶")
        self.next_btn.setFixedWidth(40)
        self.next_btn.setFixedHeight(80)
        self.next_btn.setCursor(Qt.CursorShape.PointingHandCursor)
        self.next_btn.clicked.connect(self.next_part)
        left_layout.addWidget(self.next_btn)

        bottom_layout.addWidget(left_panel, stretch=1)

        # Painel Direito
        self.config_btn = QPushButton("⚙️ Filtrar\nPartes")
        self.config_btn.setFixedWidth(150)
        self.config_btn.setFixedHeight(80)
        self.config_btn.setCursor(Qt.CursorShape.PointingHandCursor)
        self.config_btn.clicked.connect(self.open_settings_window)

        bottom_layout.addWidget(self.config_btn)
        self.main_layout.addWidget(self.bottom_container)

    def alternar_tema(self):
        self.modo_escuro = not self.modo_escuro
        self.aplicar_tema()

    def aplicar_tema(self):
        if self.modo_escuro:
            bg_main = "#0f172a"
            bg_top = "#1e293b"
            bg_bottom = "#0f172a"
            btn_bg = "#1e293b"
            btn_fg = "#f8fafc"
            border_col = "#334155"
            car_frame_bg = "#1e293b"

            self.btn_tema.setText("☀️ Modo Claro")
            self.btn_tema.setStyleSheet(
                "background-color: #334155; color: #f8fafc; border: 1px solid #475569; "
                "padding: 4px 8px; border-radius: 5px; font-weight: bold;"
            )
        else:
            bg_main = "#ffffff"
            bg_top = "#666666"
            bg_bottom = "#ffffff"
            btn_bg = "#e0e0e0"
            btn_fg = "#333333"
            border_col = "#b0b0b0"
            car_frame_bg = "#777777"

            self.btn_tema.setText("🌙 Modo Escuro")
            self.btn_tema.setStyleSheet(
                "background-color: #e0e0e0; color: #333333; border: 1px solid #b0b0b0; "
                "padding: 4px 8px; border-radius: 5px; font-weight: bold;"
            )

        self.setStyleSheet(f"background-color: {bg_main};")
        self.top_bar.setStyleSheet(f"background-color: {bg_top};")
        self.map_container.setStyleSheet(f"background-color: {bg_main};")
        self.bottom_container.setStyleSheet(f"background-color: {bg_bottom};")

        self.prev_btn.setStyleSheet(f"font-size: 20pt; color: {btn_fg}; background-color: {bg_bottom}; border: none;")
        self.next_btn.setStyleSheet(f"font-size: 20pt; color: {btn_fg}; background-color: {bg_bottom}; border: none;")

        self.car_view_frame.setStyleSheet(f"background-color: {car_frame_bg}; border: 1px solid {border_col};")
        self.config_btn.setStyleSheet(f"font-family: Arial; font-size: 10pt; font-weight: bold; background-color: {btn_bg}; color: {btn_fg}; border: 1px solid {border_col};")

        self.mapa_widget.set_modo_escuro(self.modo_escuro)

    def update_can_data(self, rpm, speed):
        for part in self.car_parts_data:
            if part["name"] == "MOTOR E SISTEMAS":
                for sensor in part["sensors"]:
                    if sensor[0] == "RPM":
                        sensor[1] = f"{rpm} RPM"
                    elif sensor[0] == "Velocidade":
                        sensor[1] = f"{speed} km/h"

        if self.active_pop_over and self.active_pop_over.isVisible():
            self.active_pop_over.refresh_sensor_values()

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
        dialog = SettingsDialog(self.car_parts_data, modo_escuro=self.modo_escuro, parent=self)
        self._center_dialog(dialog)
        if dialog.exec():
            self.update_car_display()

    def open_sensor_pop_over(self):
        active_parts = self.get_active_parts()
        if not active_parts:
            return

        part_data = active_parts[self.current_part_index]
        self.active_pop_over = SensorPopOverDialog(part_data, modo_escuro=self.modo_escuro, parent=self)
        self._center_dialog(self.active_pop_over)
        self.active_pop_over.exec()
        self.active_pop_over = None

    def closeEvent(self, event):
        self.mapa_widget.timer.stop()
        self.can_thread.stop()
        event.accept()


if __name__ == "__main__":
    app = QApplication(sys.argv)
    window = CarMultimediaApp()
    window.show()
    sys.exit(app.exec())