import math
import os
import sys
from PySide6.QtCore import QPoint, QTimer, Qt
from PySide6.QtGui import QColor, QFont, QPainter, QPen, QPixmap, QPolygon
from PySide6.QtWidgets import (
    QApplication,
    QHBoxLayout,
    QLabel,
    QPushButton,
    QVBoxLayout,
    QWidget,
)


class MapaWidget(QWidget):

    def __init__(self):
        super().__init__()

        pasta_script = os.path.dirname(os.path.abspath(__file__))
        caminho_imagem = os.path.join(pasta_script, "mapa_grande.png")
        self.pixmap_mapa_completo = QPixmap(caminho_imagem)

        self.rota = [
            (1245, 1641),
            (1156, 1641),
            (1156, 1439),
            (938, 1445),
            (938, 1105),
            (690, 1083),
            (690, 1032),
            (700, 1011),
            (697, 982),
            (751, 894),
            (754,522),
            (1067,525),
            (1067,357),
            (1438,358),
            (1428,1660),
            (1380,1660),
        ]
        self.indice_ponto_atual = 1

        self.carro_x = float(self.rota[0][0])
        self.carro_y = float(self.rota[0][1])

        self.angulo_atual = 0.0
        self.velocidade_kmh = 0.0
        self.velocidade = 0.0
        self.em_pausa = False

        # Parâmetros de navegação
        self.VELOCIDADE_MAX_KMH = 45.0
        self.VELOCIDADE_MIN_CURVA_KMH = 12.0
        self.VELOCIDADE_MEDIA_ROTA_KMH = 35.0

        layout_principal = QVBoxLayout()

        self.rotulo_mapa = QLabel()
        self.rotulo_mapa.setAlignment(Qt.AlignCenter)
        layout_principal.addWidget(self.rotulo_mapa)

        layout_botoes = QHBoxLayout()
        self.btn_simulacao = QPushButton("Iniciar / Pausar Navegação")
        layout_botoes.addWidget(self.btn_simulacao)

        layout_principal.addLayout(layout_botoes)
        self.setLayout(layout_principal)

        self.timer = QTimer()
        self.timer.setInterval(40)
        self.timer.timeout.connect(self.mover_carro)

        self.btn_simulacao.clicked.connect(self.alternar_simulacao)

        self.calcular_angulo_inicial()
        self.atualizar_mapa()

    def calcular_angulo_inicial(self):
        alvo_x, alvo_y = self.rota[self.indice_ponto_atual]
        dx = alvo_x - self.carro_x
        dy = alvo_y - self.carro_y
        if dx != 0 or dy != 0:
            self.angulo_atual = math.degrees(math.atan2(dy, dx))

    def calcular_distancia_restante(self):
        if self.indice_ponto_atual >= len(self.rota):
            return 0.0

        alvo_x, alvo_y = self.rota[self.indice_ponto_atual]
        dist_trecho_atual = (
            (alvo_x - self.carro_x) ** 2 + (alvo_y - self.carro_y) ** 2
        ) ** 0.5

        dist_restante_pixels = dist_trecho_atual
        for i in range(self.indice_ponto_atual, len(self.rota) - 1):
            p1 = self.rota[i]
            p2 = self.rota[i + 1]
            dist_restante_pixels += (
                (p2[0] - p1[0]) ** 2 + (p2[1] - p1[1]) ** 2
            ) ** 0.5

        return dist_restante_pixels * 1.5

    def obter_proxima_manobra(self):
        if self.indice_ponto_atual >= len(self.rota) - 1:
            return "Em 0 m", "Chegando ao destino", "🏁"

        p0 = self.rota[self.indice_ponto_atual - 1]
        p1 = self.rota[self.indice_ponto_atual]
        p2 = self.rota[self.indice_ponto_atual + 1]

        v1 = (p1[0] - p0[0], p1[1] - p0[1])
        v2 = (p2[0] - p1[0], p2[1] - p1[1])

        cp = v1[0] * v2[1] - v1[1] * v2[0]

        dist_px = math.hypot(p1[0] - self.carro_x, p1[1] - self.carro_y)
        dist_m = int(dist_px * 1.5)

        dist_texto = (
            f"Em {dist_m} m" if dist_m >= 15 else "Nas proximidades da curva"
        )

        if cp > 5000:
            instrucao = "Vire à direita"
            seta = "↱"
        elif cp < -5000:
            instrucao = "Vire à esquerda"
            seta = "↰"
        else:
            instrucao = "Siga em frente"
            seta = "↑"

        return dist_texto, instrucao, seta

    def atualizar_mapa(self):
        resultado = QPixmap(800, 480)
        resultado.fill(Qt.black)

        painter = QPainter(resultado)
        painter.setRenderHint(QPainter.Antialiasing)
        painter.setRenderHint(QPainter.SmoothPixmapTransform)

        carro_tela_x = 400
        carro_tela_y = 390

        # --- 1. RENDERIZAÇÃO DO MAPA E ROTAS ---
        painter.translate(carro_tela_x, carro_tela_y)
        painter.rotate(-(self.angulo_atual + 90))
        painter.translate(-self.carro_x, -self.carro_y)

        painter.drawPixmap(0, 0, self.pixmap_mapa_completo)

        pen_linha = QPen(QColor("darkgreen"), 6, Qt.SolidLine)
        painter.setPen(pen_linha)

        if self.indice_ponto_atual < len(self.rota):
            alvo_x, alvo_y = self.rota[self.indice_ponto_atual]
            painter.drawLine(
                int(self.carro_x), int(self.carro_y), alvo_x, alvo_y
            )

        for i in range(self.indice_ponto_atual, len(self.rota) - 1):
            painter.drawLine(
                self.rota[i][0],
                self.rota[i][1],
                self.rota[i + 1][0],
                self.rota[i + 1][1],
            )

        # --- 2. SETA INDICADORA DO CARRO ---
        painter.resetTransform()

        painter.setPen(Qt.NoPen)
        painter.setBrush(QColor("lightgreen"))

        seta_carro = QPolygon(
            [
                QPoint(carro_tela_x, carro_tela_y - 22),
                QPoint(carro_tela_x - 15, carro_tela_y + 14),
                QPoint(carro_tela_x + 15, carro_tela_y + 14),
            ]
        )
        painter.drawPolygon(seta_carro)

        # --- 3. ELEMENTOS FLUTUANTES DA INTERFACE (HUD) ---

        # 3.1 VELOCÍMETRO (Canto inferior esquerdo)
        painter.setBrush(QColor(15, 23, 42, 210))
        painter.setPen(QPen(QColor("lightgreen"), 2))
        painter.drawRoundedRect(20, 370, 95, 80, 12, 12)

        painter.setPen(QColor("white"))
        painter.setFont(QFont("Segoe UI", 22, QFont.Bold))
        painter.drawText(
            20,
            375,
            95,
            40,
            Qt.AlignCenter,
            str(int(round(self.velocidade_kmh))),
        )

        painter.setPen(QColor("lightgray"))
        painter.setFont(QFont("Segoe UI", 9, QFont.Bold))
        painter.drawText(20, 415, 95, 20, Qt.AlignCenter, "KM/H")

        # 3.2 PLACA DE LIMITE DE VELOCIDADE (Tamanho Reduzido)
        centro_x, centro_y = 138, 410
        raio = 20  # Reduzido para ficar em proporção mais harmoniosa

        painter.setBrush(QColor("white"))
        painter.setPen(QPen(QColor(220, 38, 38), 3))
        painter.drawEllipse(QPoint(centro_x, centro_y), raio, raio)

        painter.setPen(QColor("black"))
        painter.setFont(QFont("Segoe UI", 11, QFont.Bold))
        painter.drawText(
            centro_x - raio,
            centro_y - raio,
            raio * 2,
            raio * 2,
            Qt.AlignCenter,
            "50",
        )

        # 3.3 PAINEL DE ETA (Canto inferior direito)
        painter.setBrush(QColor(15, 23, 42, 210))
        painter.setPen(QPen(QColor(0, 150, 255), 2))
        painter.drawRoundedRect(520, 370, 260, 80, 12, 12)

        dist_m = self.calcular_distancia_restante()
        texto_dist = (
            f"{dist_m/1000:.1f} km" if dist_m >= 1000 else f"{int(dist_m)} m"
        )
        tempo_min = max(
            1, math.ceil((dist_m / 1000) / self.VELOCIDADE_MEDIA_ROTA_KMH * 60)
        )

        painter.setPen(QColor("white"))
        painter.setFont(QFont("Segoe UI", 12, QFont.Bold))
        painter.drawText(
            535, 380, 230, 25, Qt.AlignLeft, f"Distância: {texto_dist}"
        )

        painter.setPen(QColor("lightgreen"))
        painter.setFont(QFont("Segoe UI", 11))
        painter.drawText(
            535, 408, 230, 25, Qt.AlignLeft, f"Chegada em: {tempo_min} min"
        )

        # 3.4 CARTÃO DE PRÓXIMA MANOBRA (Canto superior direito)
        painter.setBrush(QColor(15, 23, 42, 210))
        painter.setPen(QPen(QColor(255, 165, 0), 2))
        painter.drawRoundedRect(520, 20, 260, 80, 12, 12)

        dist_texto, instrucao, seta = self.obter_proxima_manobra()

        painter.setPen(QColor(255, 165, 0))
        painter.setFont(QFont("Segoe UI", 28, QFont.Bold))
        painter.drawText(530, 25, 50, 70, Qt.AlignCenter, seta)

        painter.setPen(QColor("white"))
        painter.setFont(QFont("Segoe UI", 11, QFont.Bold))
        painter.drawText(585, 30, 185, 25, Qt.AlignLeft, instrucao)

        painter.setPen(QColor("lightgray"))
        painter.setFont(QFont("Segoe UI", 10))
        painter.drawText(585, 58, 185, 25, Qt.AlignLeft, dist_texto)

        painter.end()

        self.rotulo_mapa.setPixmap(resultado)

    def mover_carro(self):
        if self.em_pausa:
            self.atualizar_mapa()
            return

        alvo_x, alvo_y = self.rota[self.indice_ponto_atual]

        dx = alvo_x - self.carro_x
        dy = alvo_y - self.carro_y
        distancia = (dx**2 + dy**2) ** 0.5

        e_ultimo_segmento = self.indice_ponto_atual == len(self.rota) - 1
        vel_minima = (
            0.0 if e_ultimo_segmento else self.VELOCIDADE_MIN_CURVA_KMH
        )

        fator_alvo = min(1.0, distancia / 200.0)
        velocidade_alvo_kmh = vel_minima + (
            self.VELOCIDADE_MAX_KMH - vel_minima
        ) * (fator_alvo**0.8)

        if self.indice_ponto_atual == 1:
            origem_x, origem_y = self.rota[0]
            dist_origem = (
                (self.carro_x - origem_x) ** 2 + (self.carro_y - origem_y) ** 2
            ) ** 0.5
            fator_origem = min(1.0, dist_origem / 150.0)
            velocidade_alvo_kmh *= fator_origem

        if self.velocidade_kmh < velocidade_alvo_kmh:
            self.velocidade_kmh = min(
                velocidade_alvo_kmh, self.velocidade_kmh + 0.6
            )
        elif self.velocidade_kmh > velocidade_alvo_kmh:
            self.velocidade_kmh = max(
                velocidade_alvo_kmh, self.velocidade_kmh - 0.9
            )

        self.velocidade = max(
            0.05, (self.velocidade_kmh / self.VELOCIDADE_MAX_KMH) * 1.8
        )

        if dx != 0 or dy != 0:
            angulo_alvo = math.degrees(math.atan2(dy, dx))
            diferenca = (angulo_alvo - self.angulo_atual + 180) % 360 - 180
            self.angulo_atual += diferenca * 0.10

        if distancia < max(1.0, self.velocidade):
            self.carro_x = float(alvo_x)
            self.carro_y = float(alvo_y)

            if e_ultimo_segmento:
                self.velocidade_kmh = 0.0
                self.velocidade = 0.0
                self.em_pausa = True
                QTimer.singleShot(2000, self.reiniciar_rota)
            else:
                self.indice_ponto_atual += 1
        else:
            self.carro_x += (dx / distancia) * self.velocidade
            self.carro_y += (dy / distancia) * self.velocidade

        self.atualizar_mapa()

    def reiniciar_rota(self):
        self.indice_ponto_atual = 1
        self.carro_x = float(self.rota[0][0])
        self.carro_y = float(self.rota[0][1])
        self.velocidade_kmh = 0.0
        self.calcular_angulo_inicial()
        self.em_pausa = False

    def alternar_simulacao(self):
        if self.timer.isActive():
            self.timer.stop()
        else:
            self.timer.start()


if __name__ == "__main__":
    app = QApplication(sys.argv)

    janela = MapaWidget()
    janela.setWindowTitle("Multimídia - Módulo de Mapa")
    janela.resize(800, 480)
    janela.show()

    sys.exit(app.exec())