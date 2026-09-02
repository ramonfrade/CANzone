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

import random
import time
import threading

class SimProvider(CanProvider):
    def __init__(self):
        super().__init__()
        self.sim_running = False
        self.thread = None

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

    def _encode_obd2_frame(self, pid: int, value: float) -> tuple[str, list[int]]:
        """
        Converte o valor para a mensagem hexadecimal CAN e define os pinos do cabo OBD-II.
        """
        can_id = "07E8"  # ID padrão de resposta da ECU
        
        if pid == 0x0C:  # RPM -> (A*256 + B) / 4
            raw_val = int(value * 4)
            a = (raw_val >> 8) & 0xFF
            b = raw_val & 0xFF
            length = "04"
            payload = f"41 0C {a:02X} {b:02X} 00 00 00"
            
        elif pid == 0x0D:  # Velocidade (km/h) -> A
            a = int(value) & 0xFF
            length = "03"
            payload = f"41 0D {a:02X} 00 00 00 00 00"
            
        elif pid == 0x05:  # Temperatura (°C) -> A - 40
            a = int(value + 40) & 0xFF
            length = "03"
            payload = f"41 05 {a:02X} 00 00 00 00 00"
            
        else:
            return "", []

        # Formato de exibição Hexadecimal CAN: ID [DLN] DATA
        hex_frame = f"0x{can_id} [8] {length} {payload}"

        # Pinos acionados na comunicação CAN OBD-II:
        # Pin 4: Terra da Carcaça | Pin 5: Terra do Sinal
        # Pin 6: CAN High | Pin 14: CAN Low | Pin 16: Bateria (+12V)
        active_pins = [4, 5, 6, 14, 16]

        return hex_frame, active_pins

    def _sim_loop(self):
        speed_kmh = 0.0
        rpm = 800
        engine_temp = 90.0
        
        # PIDs OBD-II transmitidos sequencialmente no barramento
        pids = [0x0C, 0x0D, 0x05]
        pid_idx = 0

        while self.sim_running:
            speed_kmh += 0.5
            rpm += 70

            if rpm > 3000:
                rpm = 1800

            if speed_kmh > 120:
                speed_kmh = 0.0
                rpm = 800

            engine_temp += random.uniform(-0.1, 0.1)

            # Seleciona o PID da rodada para simular alternância de frames no barramento
            current_pid = pids[pid_idx % len(pids)]
            pid_idx += 1

            if current_pid == 0x0C:
                val = rpm
            elif current_pid == 0x0D:
                val = speed_kmh
            else:
                val = engine_temp

            raw_hex, active_pins = self._encode_obd2_frame(current_pid, val)

            current_data = {
                "speed": round(speed_kmh, 1),
                "rpm": int(rpm),
                "temp": round(engine_temp, 1),
                "raw_hex": raw_hex,          # Ex: "0x07E8 [8] 04 41 0C 1F 40 00 00 00"
                "active_pins": active_pins   # Ex: [4, 5, 6, 14, 16]
            }

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