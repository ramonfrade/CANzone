import sys
from PySide6.QtWidgets import QApplication

from tela import CarMultimediaApp, start_telemetry


if __name__ == "__main__":
    app = QApplication(sys.argv)

    # 1. Instancia a Interface (mapa integrado, sensores mockados)
    window = CarMultimediaApp()

    # 2. Inicializa o Hardware/Simulador CAN e conecta os dados
    #    aos sensores do Motor (thread-safe via SignalBridge em tela.py)
    data_provider = start_telemetry(window)

    # 3. Garante o desligamento seguro da thread ao fechar a aplicação
    app.aboutToQuit.connect(data_provider.stop)

    window.show()
    sys.exit(app.exec())