# import the library
import can, math
from abc import ABC, abstractmethod
import time
import threading
import random
from PySide6.QtCore import QTimer

class CanProvider:
    '''classe abstrata de interface CAN, SimProvider -> CanProvider ou RealProvider -> CanProvider'''

    def __init__(self):
        self._callbacks_list = []

    def insert_callback(self, callback: callable):
        if callback not in self._callbacks_list:
            self._callbacks_list.append(callback)

    def notify_callbacks(self, data: dict):
        for callback in self._callbacks_list:
            callback(data)

    @abstractmethod
    def start():
        ...

    @abstractmethod
    def stop():
        ...

class RealProvider(CanProvider):
    ...

class SimProvider(CanProvider):
    def __init__(self):
        super().__init__()

        self.sim_running = False
        self.thread = None

        self.angulo_atual = 0.0
        self.velocidade_kmh = 0.0
        self.velocidade = 0.0
        self.em_pausa = False

        # Parâmetros de navegação
        self.VELOCIDADE_MAX_KMH = 45.0
        self.VELOCIDADE_MIN_CURVA_KMH = 12.0
        self.VELOCIDADE_MEDIA_ROTA_KMH = 35.0

        self.calcular_angulo_inicial()
        self.timer.start()

    def start(self):
        self.sim_running = True
        self.thread = threading.Thread(target=self._sim_loop, daemon=True)
        self.thread.start()
        print('Simulação iniciada...')

    def stop(self):
        self.sim_running = False
        if self.thread:
            self.thread.join()
            print('Simulação terminada.')

    def _sim_loop(self):
        speed_kmh = 0
        rpm = 10
        engine_temp = 20
        while self.sim_running:
            
            speed_kmh += 0.5
            rpm += 70
            
            if rpm > 3000:
                rpm = 1800
            
           
            if speed_kmh > 120:
                speed_kmh = 0.0
                rpm = 800

            
            engine_temp += random.uniform(-0.1, 0.1)

            # Empacota os dados gerados
            current_data = {
                "speed": round(speed_kmh, 1),
                "rpm": int(rpm),
                "temp": round(engine_temp, 1)
            }

            # Envia os dados para a interface
            self.notify_callbacks(current_data)

            time.sleep(0.1)

def initialize_system() -> CanProvider:

    try:
        bus = can.interface.Bus(channel='vcan0', interface='socketcan')
        print("Hardware CAN detectado. Iniciando modo Real.")
        car_system = RealProvider(bus)

    except (can.CanError, FileNotFoundError, OSError) as e:
        print("Hardware CAN não encontrado, Iniciando simulação...")
        car_system = SimProvider()

    return car_system

def show_engine_data(data: dict):
    print(data)

if __name__ == '__main__':
    data_provider = initialize_system()
    data_provider.insert_callback(show_engine_data)
    data_provider.start()

    time.sleep(5)
    data_provider.stop()