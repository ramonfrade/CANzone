import tkinter as tk
from tkinter import ttk

class CarMultimediaApp:
    def __init__(self, root):
        self.root = root
        self.root.title("Multimídia do Carro - Filtro de Partes")
        self.root.geometry("800x480")
        self.root.configure(bg="white")

        # Lista de partes do carro. 
        # Adicionamos "enabled" (tk.BooleanVar) para controlar as checkboxes!
        self.car_parts_data = [
            {
                "name": "MOTOR E SISTEMAS",
                "enabled": tk.BooleanVar(value=True),
                "sensors": [
                    ("Temp. Arrefecimento", "90°C (Normal)"),
                    ("Pressão do Óleo", "3.5 bar (Estável)"),
                    ("Voltagem Bateria", "13.8V (Carregando)")
                ]
            },
            {
                "name": "FREIOS E SUSPENSÃO",
                "enabled": tk.BooleanVar(value=True),
                "sensors": [
                    ("Pastilhas Dianteiras", "75% Restante"),
                    ("Pastilhas Traseiras", "80% Restante"),
                    ("Alinhamento", "Normal")
                ]
            },
             {
                "name": "CHASSI E PNEUS",
                "enabled": tk.BooleanVar(value=True),
                "sensors": [
                    ("Pressão Pneus", "32 PSI (Todos)"),
                    ("Controle Tração", "Ativo")
                ]
            }
        ]
        
        self.current_part_index = 0
        self.pop_over_window = None
        self.settings_window = None

        self.create_top_bar()
        self.create_map_area()
        self.create_bottom_area()
        self.update_car_display() # Força a primeira atualização da tela

    def create_top_bar(self):
        top_frame = tk.Frame(self.root, bg="#666666", height=30)
        top_frame.pack(side="top", fill="x")
        top_frame.pack_propagate(False)

        status_label = tk.Label(top_frame, text="Bluetooth: ON   |   Wi-Fi: Conectado   |   Bateria: 85%", bg="#666666", fg="white", font=("Arial", 10, "bold"))
        status_label.pack(side="right", padx=20, pady=5)

    def create_map_area(self):
        map_container = tk.Frame(self.root, bg="white")
        map_container.pack(side="top", fill="both", expand=True, padx=40, pady=(10,10))

        self.map_frame = tk.Frame(map_container, bg="#45aafa", highlightbackground="#2d8bd6", highlightthickness=2)
        self.map_frame.pack(fill="both", expand=True)

        tk.Label(self.map_frame, text="MAPA", bg="#45aafa", fg="white", font=("Arial", 16, "bold")).pack(expand=True)

    def create_bottom_area(self):
        bottom_container = tk.Frame(self.root, bg="white", height=100)
        bottom_container.pack(side="bottom", fill="x", padx=40, pady=(0, 20))
        bottom_container.pack_propagate(False)

        # --- PAINEL DIREITO: Botão de Configuração ---
        right_panel = tk.Frame(bottom_container, bg="white", width=150)
        right_panel.pack(side="right", fill="y", padx=(10, 0))
        right_panel.pack_propagate(False)

        config_btn = tk.Button(
            right_panel, text="⚙️ Filtrar\nPartes", font=("Arial", 10, "bold"), 
            bg="#e0e0e0", fg="#333333", relief="raised", cursor="hand2", 
            command=self.open_settings_window
        )
        config_btn.pack(side="right", fill="both", expand=True)

        # --- PAINEL ESQUERDO: Setas e Caixa Cinza ---
        left_panel = tk.Frame(bottom_container, bg="white")
        left_panel.pack(side="left", fill="both", expand=True)

        tk.Button(left_panel, text="◀", font=("Arial", 20), bg="white", fg="#555555", relief="flat", command=self.prev_part, cursor="hand2").pack(side="left", padx=(0, 10))

        self.car_view_frame = tk.Frame(left_panel, bg="#777777", relief="raised", bd=1, cursor="hand2")
        self.car_view_frame.pack(side="left", fill="both", expand=True)
        self.car_view_frame.bind("<Button-1>", lambda e: self.open_sensor_pop_over())

        self.car_part_title_label = tk.Label(self.car_view_frame, text="", bg="#777777", fg="white", font=("Arial", 11, "bold"))
        self.car_part_title_label.pack(side="top", pady=10)
        self.car_part_title_label.bind("<Button-1>", lambda e: self.open_sensor_pop_over())

        self.instrucao_label = tk.Label(self.car_view_frame, text="(Clique para ver sensores)", bg="#777777", fg="#eeeeee", font=("Arial", 8))
        self.instrucao_label.pack(side="bottom", pady=5)
        self.instrucao_label.bind("<Button-1>", lambda e: self.open_sensor_pop_over())

        tk.Button(left_panel, text="▶", font=("Arial", 20), bg="white", fg="#555555", relief="flat", command=self.next_part, cursor="hand2").pack(side="right", padx=(10, 0))

    def get_active_parts(self):
        """Retorna apenas as partes que estão marcadas no filtro."""
        return [part for part in self.car_parts_data if part["enabled"].get()]

    def prev_part(self):
        active_parts = self.get_active_parts()
        if not active_parts: return # Se nada estiver selecionado, não faz nada
        
        self.current_part_index -= 1
        if self.current_part_index < 0:
            self.current_part_index = len(active_parts) - 1
        self.update_car_display()

    def next_part(self):
        active_parts = self.get_active_parts()
        if not active_parts: return
        
        self.current_part_index += 1
        if self.current_part_index >= len(active_parts):
            self.current_part_index = 0
        self.update_car_display()

    def update_car_display(self):
        """Atualiza a caixa cinza baseada apenas nas partes ativas."""
        active_parts = self.get_active_parts()
        
        if not active_parts:
            self.car_part_title_label.config(text="⚠️ NENHUMA PARTE SELECIONADA")
            self.instrucao_label.config(text="Use o botão 'Filtrar Partes' ao lado")
            return
            
        # Garante que o índice atual não quebre se o usuário desmarcar várias opções de uma vez
        if self.current_part_index >= len(active_parts):
            self.current_part_index = 0

        part_name = active_parts[self.current_part_index]['name']
        self.car_part_title_label.config(text=f"PARTE ATUAL:\n{part_name}")
        self.instrucao_label.config(text="(Clique para ver sensores)")

    # --- JANELAS POP-OVER ---

    def open_settings_window(self):
        """Abre a janela flutuante de seleção (Filtros) centralizada."""
        if self.settings_window is not None:
            return

        self.settings_window = tk.Toplevel(self.root)
        
        # --- LÓGICA DE CENTRALIZAÇÃO ---
        width, height = 350, 250
        # Garante que as dimensões da janela principal estejam atualizadas
        self.root.update_idletasks() 
        x = self.root.winfo_x() + (self.root.winfo_width() // 2) - (width // 2)
        y = self.root.winfo_y() + (self.root.winfo_height() // 2) - (height // 2)
        
        self.settings_window.geometry(f"{width}x{height}+{x}+{y}")
        # -------------------------------
        
        self.settings_window.configure(bg="#f0f0f0", highlightthickness=2, highlightbackground="#45aafa")
        self.settings_window.overrideredirect(True)
        self.settings_window.update_idletasks()
        self.settings_window.grab_set()

        tk.Label(self.settings_window, text="SELECIONE AS PARTES VISÍVEIS:", bg="#f0f0f0", font=("Arial", 11, "bold")).pack(pady=15)

        for part in self.car_parts_data:
            chk = tk.Checkbutton(
                self.settings_window, text=part["name"], variable=part["enabled"],
                bg="#f0f0f0", font=("Arial", 10), activebackground="#f0f0f0"
            )
            chk.pack(anchor="w", padx=40, pady=2)

        ttk.Button(self.settings_window, text="APLICAR E FECHAR", command=self.close_settings_window).pack(side="bottom", pady=20)

    def close_settings_window(self):
        if self.settings_window:
            self.update_car_display() # Atualiza a barra cinza de acordo com os filtros
            self.settings_window.destroy()
            self.settings_window = None

    def open_sensor_pop_over(self):
        """Abre a janela flutuante dos sensores da parte atual centralizada."""
        if self.pop_over_window is not None:
            return

        active_parts = self.get_active_parts()
        if not active_parts: 
            return 

        part_data = active_parts[self.current_part_index]
        
        self.pop_over_window = tk.Toplevel(self.root)
        
        # --- LÓGICA DE CENTRALIZAÇÃO ---
        width, height = 450, 300
        self.root.update_idletasks()
        x = self.root.winfo_x() + (self.root.winfo_width() // 2) - (width // 2)
        y = self.root.winfo_y() + (self.root.winfo_height() // 2) - (height // 2)
        
        self.pop_over_window.geometry(f"{width}x{height}+{x}+{y}")
        # -------------------------------
        
        self.pop_over_window.configure(bg="#f0f0f0", highlightthickness=2, highlightbackground="#45aafa")
        self.pop_over_window.overrideredirect(True)
        self.pop_over_window.update_idletasks()
        self.pop_over_window.grab_set()

        tk.Label(self.pop_over_window, text=f"SENSORES: {part_data['name']}", bg="#f0f0f0", fg="black", font=("Arial", 12, "bold")).pack(side="top", pady=(15, 10))

        sensor_list_frame = tk.Frame(self.pop_over_window, bg="white", highlightbackground="#cccccc", highlightthickness=1)
        sensor_list_frame.pack(fill="both", expand=True, padx=20, pady=10)

        for sensor_name, value in part_data['sensors']:
            item_frame = tk.Frame(sensor_list_frame, bg="white")
            item_frame.pack(fill="x", anchor="w", pady=5, padx=10)
            
            tk.Label(item_frame, text="⚙️", bg="white", font=("Arial", 10)).pack(side="left", padx=(0, 10))
            tk.Label(item_frame, text=f"{sensor_name}: {value}", bg="white", font=("Arial", 10)).pack(side="left")

        ttk.Button(self.pop_over_window, text="FECHAR JANELA", command=self.close_sensor_pop_over).pack(side="bottom", pady=10)

    def close_sensor_pop_over(self):
        if self.pop_over_window:
            self.pop_over_window.destroy()
            self.pop_over_window = None

if __name__ == "__main__":
    root = tk.Tk()
    app = CarMultimediaApp(root)
    root.mainloop()