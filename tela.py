import os
import sys
import json
import time

from PySide6.QtCore import QObject, QRectF, Qt, Signal, Slot, QTimer
from PySide6.QtGui import QBrush, QColor, QPainter, QPen, QPixmap
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

# --- TELEMETRIA (CAN real ou simulador) ---
from telemetry.telemetry import initialize_system


PIN_CENTERS = {
    1: (70.0, 53.0),
    2: (124.0, 53.0),
    3: (177.0, 53.0),
    4: (231.0, 53.0),
    5: (284.0, 53.0),
    6: (337.5, 53.0),
    7: (391.0, 53.0),
    8: (444.0, 53.0),
    9: (70.0, 131.5),
    10: (124.0, 131.5),
    11: (177.0, 131.5),
    12: (231.0, 131.5),
    13: (284.0, 131.5),
    14: (337.5, 131.5),
    15: (391.0, 131.5),
    16: (444.0, 131.5),
}


class OBD2Widget(QWidget):
    """
    Widget que renderiza o ícone do conector OBD-II e anima (pisca)
    os pinos ativos fornecidos pela telemetria CAN.
    """
    def __init__(self, parent=None):
        super().__init__(parent)
        self.setFixedSize(210, 80)

        icon_path = os.path.join(os.path.dirname(os.path.abspath(__file__)), "icons", "obd2.png")
        self.pixmap = QPixmap(icon_path)

        self.active_pins = []
        self.blink_state = True

        # Timer para animação de piscar dos pinos ativos
        self.timer = QTimer(self)
        self.timer.setInterval(220)
        self.timer.timeout.connect(self._toggle_blink)
        self.timer.start()

    def _toggle_blink(self):
        self.blink_state = not self.blink_state
        self.update()

    def set_active_pins(self, pins: list[int]):
        self.active_pins = list(pins) if pins else []
        self.update()

    def paintEvent(self, event):
        painter = QPainter(self)
        painter.setRenderHint(QPainter.RenderHint.Antialiasing)
        painter.setRenderHint(QPainter.RenderHint.SmoothPixmapTransform)

        if self.pixmap.isNull():
            return

        w = self.width()
        h = self.height()

        orig_w = 514.0
        orig_h = 192.0

        scale = min(w / orig_w, h / orig_h)
        target_w = orig_w * scale
        target_h = orig_h * scale
        offset_x = (w - target_w) / 2.0
        offset_y = (h - target_h) / 2.0

        target_rect = QRectF(offset_x, offset_y, target_w, target_h)
        painter.drawPixmap(target_rect.toRect(), self.pixmap)

        if self.active_pins:
            for pin in self.active_pins:
                if pin not in PIN_CENTERS:
                    continue
                orig_cx, orig_cy = PIN_CENTERS[pin]
                cx = offset_x + orig_cx * scale
                cy = offset_y + orig_cy * scale
                pin_w = 32.0 * scale
                pin_h = 50.0 * scale
                pin_rect = QRectF(cx - pin_w / 2.0, cy - pin_h / 2.0, pin_w, pin_h)

                if self.blink_state:
                    glow_color = QColor(0, 240, 255, 230)
                    border_color = QColor(255, 255, 255, 255)
                    painter.setBrush(QBrush(glow_color))
                    painter.setPen(QPen(border_color, 1.5))
                    painter.drawRoundedRect(pin_rect, 2.0, 2.0)
                else:
                    dim_color = QColor(0, 180, 216, 70)
                    painter.setBrush(QBrush(dim_color))
                    painter.setPen(QPen(QColor(0, 180, 216, 110), 1.0))
                    painter.drawRoundedRect(pin_rect, 2.0, 2.0)


class SignalBridge(QObject):
    """
    Ponte de comunicação segura.
    Converte o callback bruto da thread (Python padrão)
    em um Sinal do Qt (Thread-Safe) para atualizar a UI.
    """
    data_received = Signal(dict)

    def callback_from_thread(self, data: dict):
        self.data_received.emit(data)


def start_telemetry(window):
    """
    Inicia o provider (CAN real ou simulador) e conecta os dados
    recebidos ao dashboard de forma thread-safe (via SignalBridge).
    Retorna o provider para que a entrada garanta o desligamento limpo.
    """
    bridge = SignalBridge()
    data_provider = initialize_system()
    data_provider.insert_callback(bridge.callback_from_thread)
    bridge.data_received.connect(window.set_sensor_data)
    data_provider.start()
    return data_provider


# ==============================================================================
# PAINÉIS E JANELAS SECUNDÁRIAS
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
    def __init__(self, part_data, initial_telemetry=None, modo_escuro=False, parent=None):
        super().__init__(parent)
        self.part_data = part_data
        self.sensor_labels = {}

        self.setWindowFlags(Qt.WindowType.FramelessWindowHint | Qt.WindowType.Dialog)
        self.setModal(True)
        self.setFixedSize(540, 420)

        bg_color = "#1e293b" if modo_escuro else "#f8fafc"
        frame_bg = "#0f172a" if modo_escuro else "#ffffff"
        txt_color = "#f8fafc" if modo_escuro else "#0f172a"
        subtxt_color = "#94a3b8" if modo_escuro else "#64748b"
        border_color = "#38bdf8" if modo_escuro else "#0284c7"
        frame_border = "#334155" if modo_escuro else "#cbd5e1"
        obd_bg = "#0b1120" if modo_escuro else "#f1f5f9"
        hex_bg = "#030712"
        hex_text_color = "#38bdf8"

        self.setStyleSheet(f"QDialog {{ background-color: {bg_color}; border: 2px solid {border_color}; border-radius: 8px; }}")

        layout = QVBoxLayout(self)
        layout.setContentsMargins(18, 14, 18, 14)
        layout.setSpacing(10)

        title = QLabel(f"SENSORES: {part_data['name']}")
        title.setStyleSheet(f"font-family: Arial; font-size: 11pt; font-weight: bold; color: {txt_color}; border: none; background: transparent;")
        layout.addWidget(title, alignment=Qt.AlignmentFlag.AlignCenter)

        # 1. Painel de Sensores da Parte
        sensor_frame = QFrame()
        sensor_frame.setStyleSheet(f"background-color: {frame_bg}; border: 1px solid {frame_border}; border-radius: 6px;")
        sensor_layout = QVBoxLayout(sensor_frame)
        sensor_layout.setContentsMargins(14, 8, 14, 8)
        sensor_layout.setSpacing(4)

        for sensor_item in part_data['sensors']:
            sensor_name, value = sensor_item[0], sensor_item[1]
            item_label = QLabel(f"⚙️  {sensor_name}: {value}")
            item_label.setStyleSheet(f"font-family: Arial; font-size: 9pt; color: {txt_color}; border: none; background: transparent;")
            sensor_layout.addWidget(item_label)
            self.sensor_labels[sensor_name] = item_label

        sensor_layout.addStretch()
        layout.addWidget(sensor_frame, stretch=1)

        # 2. Painel OBD-II & Telemetria CAN
        obd_frame = QFrame()
        obd_frame.setStyleSheet(f"background-color: {obd_bg}; border: 1px solid {frame_border}; border-radius: 6px;")
        obd_main_layout = QVBoxLayout(obd_frame)
        obd_main_layout.setContentsMargins(12, 8, 12, 8)
        obd_main_layout.setSpacing(6)

        obd_header = QLabel("🔌 INTERFACE OBD-II & TELEMETRIA CAN")
        obd_header.setStyleSheet(f"font-family: Arial; font-size: 8.5pt; font-weight: bold; color: {txt_color}; border: none; background: transparent;")
        obd_main_layout.addWidget(obd_header)

        obd_content_layout = QHBoxLayout()
        obd_content_layout.setContentsMargins(0, 0, 0, 0)
        obd_content_layout.setSpacing(10)

        # Coluna da esquerda: Conector OBD-II com pinos animados
        obd_col = QVBoxLayout()
        obd_col.setContentsMargins(0, 0, 0, 0)
        obd_col.setSpacing(3)

        self.obd2_widget = OBD2Widget()
        obd_col.addWidget(self.obd2_widget, alignment=Qt.AlignmentFlag.AlignCenter)

        self.pins_info_label = QLabel("Pinos Ativos: --")
        self.pins_info_label.setStyleSheet(f"font-family: Arial; font-size: 7.5pt; font-weight: bold; color: {subtxt_color}; border: none; background: transparent;")
        self.pins_info_label.setAlignment(Qt.AlignmentFlag.AlignCenter)
        obd_col.addWidget(self.pins_info_label)

        obd_content_layout.addLayout(obd_col)

        # Coluna da direita: Valor de raw_hex e status CAN
        hex_panel = QFrame()
        hex_panel.setStyleSheet(f"background-color: {hex_bg}; border: 1px solid {frame_border}; border-radius: 4px;")
        hex_layout = QVBoxLayout(hex_panel)
        hex_layout.setContentsMargins(8, 6, 8, 6)
        hex_layout.setSpacing(3)

        hex_title = QLabel("CAN RAW HEX:")
        hex_title.setStyleSheet("font-family: Arial; font-size: 7.5pt; font-weight: bold; color: #94a3b8; border: none; background: transparent;")
        hex_layout.addWidget(hex_title)

        self.raw_hex_label = QLabel("Aguardando frame...")
        self.raw_hex_label.setStyleSheet(f"font-family: 'Consolas', 'Courier New', monospace; font-size: 8.5pt; font-weight: bold; color: {hex_text_color}; border: none; background: transparent;")
        self.raw_hex_label.setWordWrap(True)
        hex_layout.addWidget(self.raw_hex_label)

        self.bus_status_label = QLabel("● Barramento CAN: Ativo")
        self.bus_status_label.setStyleSheet("font-family: Arial; font-size: 7.5pt; color: #4ade80; border: none; background: transparent;")
        hex_layout.addWidget(self.bus_status_label)

        obd_content_layout.addWidget(hex_panel, stretch=1)
        obd_main_layout.addLayout(obd_content_layout)

        layout.addWidget(obd_frame)

        # 3. Botão Fechar
        btn_close = QPushButton("FECHAR JANELA")
        btn_close.setCursor(Qt.CursorShape.PointingHandCursor)
        btn_close.setStyleSheet("font-family: Arial; font-size: 9pt; font-weight: bold; padding: 5px 14px;")
        btn_close.clicked.connect(self.accept)
        layout.addWidget(btn_close, alignment=Qt.AlignmentFlag.AlignCenter)

        if initial_telemetry:
            self.update_telemetry(initial_telemetry)

    def refresh_sensor_values(self):
        for sensor_item in self.part_data['sensors']:
            sensor_name, value = sensor_item[0], sensor_item[1]
            if sensor_name in self.sensor_labels:
                self.sensor_labels[sensor_name].setText(f"⚙️  {sensor_name}: {value}")


    def update_telemetry(self, data: dict):
        self.refresh_sensor_values()
        raw_hex = data.get("raw_hex", "")
        if raw_hex:
            self.raw_hex_label.setText(raw_hex)

        active_pins = data.get("active_pins", [])
        self.obd2_widget.set_active_pins(active_pins)
        if active_pins:
            pins_str = ", ".join(str(p) for p in sorted(active_pins))
            self.pins_info_label.setText(f"Pinos Ativos: {pins_str}")
        else:
            self.pins_info_label.setText("Pinos Ativos: Nenhum")


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
        self.latest_telemetry_data = {}

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

        # Instanciação do Widget do Mapa importado de janela_mapa.py
        # A velocidade simulada do mapa alimenta o sensor "Velocidade" do dashboard
        self.mapa_widget = MapaWidget()
        self.mapa_widget.velocidade_atualizada.connect(self.set_velocidade)
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

    def save_telemetry(self, nome_arquivo, dicionario:dict):
        """
        Recebe um dicionário e o salva em um arquivo no formato JSON.
        """
        try:
            # Garante que o nome do arquivo termine com .json
            if not nome_arquivo.endswith('.json'):
                nome_arquivo += '.json'
                
            with open(nome_arquivo, 'w', encoding='utf-8') as arquivo:
                # indent=4 deixa o visual organizado; ensure_ascii=False preserva acentos
                json.dump(dicionario, arquivo, indent=4, ensure_ascii=False)
                
        except Exception as e:
            print(f"Ocorreu um erro ao salvar o arquivo: {e}")

    @Slot(dict)
    def set_sensor_data(self, data: dict):
        """
        Atualiza RPM e Temperatura a partir da telemetria (CAN real ou
        simulador). A Velocidade vem do mapa via set_velocidade —
        então cada sensor tem um único escritor, sem conflito.
        """
        self.latest_telemetry_data = data
        for part in self.car_parts_data:
            if part["name"] == "MOTOR E SISTEMAS":
                for sensor in part["sensors"]:
                    if sensor[0] == "RPM":
                        sensor[1] = f"{data.get('rpm', 0)} RPM"
                    elif sensor[0] == "Temp. Arrefecimento":
                        sensor[1] = f"{data.get('temp', 0.0)}°C"

        if self.active_pop_over and self.active_pop_over.isVisible():
            self.active_pop_over.update_telemetry(data)

        self.save_telemetry(
        "telemetry",
        {
            "speed": int(self.car_parts_data[0]["sensors"][1][1].split(' ')[0]),
            "rpm": int(self.car_parts_data[0]["sensors"][0][1].split(' ')[0]),
            "temp": float(self.car_parts_data[0]["sensors"][2][1].split('°')[0]),
            "lat" : f"{self.mapa_widget.carro_y:.2f}",
            "long": f"{self.mapa_widget.carro_x:.2f}",
            "fuel": 30,
            "tires": 32,
            "timestamp": time.strftime("%H:%M:%S")
        })

    @Slot(float)
    def set_velocidade(self, velocidade_kmh):
        """
        Atualiza o sensor de Velocidade a partir da simulação do mapa (GPS).
        """
        for part in self.car_parts_data:
            if part["name"] == "MOTOR E SISTEMAS":
                for sensor in part["sensors"]:
                    if sensor[0] == "Velocidade":
                        sensor[1] = f"{velocidade_kmh:.0f} km/h"

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
        self.active_pop_over = SensorPopOverDialog(
            part_data,
            initial_telemetry=self.latest_telemetry_data,
            modo_escuro=self.modo_escuro,
            parent=self
        )
        self._center_dialog(self.active_pop_over)
        self.active_pop_over.exec()
        self.active_pop_over = None

    def closeEvent(self, event):
        self.mapa_widget.timer.stop()
        event.accept()


if __name__ == "__main__":
    app = QApplication(sys.argv)
    window = CarMultimediaApp()
    data_provider = start_telemetry(window)
    app.aboutToQuit.connect(data_provider.stop)

    window.show()
    sys.exit(app.exec())