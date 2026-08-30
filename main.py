import sys
from PySide6.QtWidgets import QApplication
from PySide6.QtCore import QObject, Signal, Slot

from tela import CarMultimediaApp
from telemetry.telemetry import initialize_system


class SignalBridge(QObject):
    """
    Ponte de comunicação segura.
    Converte o callback bruto da thread (Python padrão) 
    em um Sinal do Qt (Thread-Safe) para atualizar a UI.
    """
    data_received = Signal(dict)

    def callback_from_thread(self, data: dict):
        self.data_received.emit(data)


@Slot(dict)
def update_ui_sensors(window: CarMultimediaApp, data: dict):
    """
    Injeta os dados reais recebidos da telemetria na estrutura de 
    dados mockada da interface gráfica, na seção de Motores (Índice 0).
    """
    motor_part = window.car_parts_data[0]
    
    # Substitui os dados estáticos pelos dados em tempo real
    motor_part["sensors"] = [
        ("RPM", f"{data.get('rpm', 0)} rev/min"),
        ("Velocidade", f"{data.get('speed', 0.0)} km/h"),
        ("Temp. Arrefecimento", f"{data.get('temp', 0.0)}°C")
    ]


if __name__ == "__main__":
    app = QApplication(sys.argv)
    
    # 1. Instancia a Interface e a Ponte
    window = CarMultimediaApp()
    bridge = SignalBridge()

    # 2. Inicializa o Hardware/Simulador CAN
    data_provider = initialize_system()

    # 3. Conecta a saída do CAN à nossa Ponte
    data_provider.insert_callback(bridge.callback_from_thread)

    # 4. Conecta a Ponte à Interface Gráfica
    # Usamos lambda para passar a referência da janela
    bridge.data_received.connect(lambda data: update_ui_sensors(window, data))

    # 5. Dá a partida na thread e garante o desligamento seguro
    data_provider.start()
    app.aboutToQuit.connect(data_provider.stop)

    window.show()
    sys.exit(app.exec())