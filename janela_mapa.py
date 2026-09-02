import math
import os
from PySide6.QtCore import QPoint, QTimer, Qt, Signal
from PySide6.QtGui import QColor, QFont, QPainter, QPen, QPixmap, QPolygon
from PySide6.QtWidgets import QLabel, QVBoxLayout, QWidget


class MapaWidget(QWidget):
    velocidade_atualizada = Signal(float)

    def __init__(self, parent=None):
        super().__init__(parent)

        self.modo_escuro = True

        # Carregamento do Mapa com Fallback caso a imagem não exista
        pasta_script = os.path.dirname(os.path.abspath(__file__))
        caminho_imagem = os.path.join(pasta_script, "mapa.png")

        self.imagem_existe = os.path.exists(caminho_imagem)
        if self.imagem_existe:
            self.pixmap_mapa_completo = QPixmap(caminho_imagem)
        else:
            self.pixmap_mapa_completo = QPixmap(1024, 1024)
            self.pixmap_mapa_completo.fill(QColor("#1e293b"))

        # Carregamento dos Ícones Especiais (icons / icones)
        self.icones = {}
        pasta_icones = os.path.join(pasta_script, "icons")
        if not os.path.exists(pasta_icones):
            pasta_icones = os.path.join(pasta_script, "icones")

        if os.path.exists(pasta_icones):
            for nome_arquivo in os.listdir(pasta_icones):
                if nome_arquivo.lower().endswith(".png"):
                    chave = os.path.splitext(nome_arquivo)[0].lower()
                    caminho_icone = os.path.join(pasta_icones, nome_arquivo)
                    pix = QPixmap(caminho_icone)
                    if not pix.isNull():
                        self.icones[chave] = pix.scaled(
                            100, 100,
                            Qt.AspectRatioMode.KeepAspectRatio,
                            Qt.TransformationMode.SmoothTransformation,
                        )

        # Pontos de Interesse no mapa (coordenadas x, y no espaço do mapa)
        self.pontos_interesse = [
            {"tipo": "hospital", "x": 1350, "y": 1190, "nome": "Santa Casa de Misericórdia de Campos", "cor": "#ef4444"},
            {"tipo": "hospital", "x": 995, "y": 690, "nome": "Hospital Escola Álvaro Alvim", "cor": "#ef4444"},
            {"tipo": "hospital", "x": 1630, "y": 220, "nome": "Hospital geral Bené", "cor": "#ef4444"},
            {"tipo": "restaurant", "x": 645, "y": 1870, "nome": "Aquariu's Steakhouse", "cor": "#f59e0b"},
            {"tipo": "restaurant", "x": 550, "y": 300, "nome": "Pizza Buzz - Pelinca", "cor": "#f59e0b"},
            {"tipo": "shop", "x": 970, "y": 860, "nome": "Drogaria Tamoios Campos dos Goytacazes", "cor": "#a63af3"},
            {"tipo": "shop", "x": 1310, "y": 1015, "nome": "Shopping Pelinca Square Center", "cor": "#a63af3"},
            {"tipo": "shop", "x": 1360, "y": 1580, "nome": "Shopping Avenida 28", "cor": "#a63af3"},
            {"tipo": "shop", "x": 1815, "y": 490, "nome": "Shopping Avenida 28", "cor": "#a63af3"},
            {"tipo": "hotel", "x": 1370, "y": 1710, "nome": "Comfort Hotel", "cor": "#38bdf8"},
            {"tipo": "hotel", "x": 1740, "y": 1800, "nome": "Aptos. Via Park Flat", "cor": "#38bdf8"},
            {"tipo": "school", "x": 808, "y": 1450, "nome": "IFF Campos Centro", "cor": "#10b981"},
        ]

        # Nomes das Ruas no mapa (coordenadas x, y no espaço do mapa)
        self.nomes_ruas = [
            {"nome": "RJ-216", "x": 1025, "y": 1650},
            {"nome": "Rua Dr. Siqueira", "x": 1320, "y": 1440},
            {"nome": "Av. Dom Bosco", "x": 130, "y": 1006},
            {"nome": "R. Visconde de Inhaúma", "x": 450, "y": 800},
            {"nome": "R. Marquês de Herval", "x": 450, "y": 560},
            {"nome": "Av. Pelinca", "x": 1550, "y": 1250},
            {"nome": "R. Alvarenga Filho", "x": 1580, "y": 1110},
            {"nome": "R. Câmara Júnior", "x": 1440, "y": 740},
        ]

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
                            (754, 522),
                            (1067, 525),
                            (1067, 357),
                            (1438, 358),
                            (1428, 1660),
                            (1380, 1660),
                        ]
                
        self.indice_ponto_atual = 1

        self.angulo_atual = 0.0
        self.velocidade_kmh = 0.0
        self.velocidade = 0.0
        self.em_pausa = False

        # Parâmetros de navegação
        self.VELOCIDADE_MAX_KMH = 45.0
        self.VELOCIDADE_MIN_CURVA_KMH = 12.0
        self.VELOCIDADE_MEDIA_ROTA_KMH = 35.0

        self.carro_x = float(self.rota[0][0])
        self.carro_y = float(self.rota[0][1])

        layout_principal = QVBoxLayout(self)
        layout_principal.setContentsMargins(0, 0, 0, 0)

        self.rotulo_mapa = QLabel()
        self.rotulo_mapa.setAlignment(Qt.AlignmentFlag.AlignCenter)
        layout_principal.addWidget(self.rotulo_mapa)

        self.timer = QTimer(self)
        self.timer.setInterval(40)
        self.timer.timeout.connect(self.mover_carro)
        self.calcular_angulo_inicial()
        self.timer.start()

    def set_modo_escuro(self, ativo: bool):
        self.modo_escuro = ativo
        if not self.imagem_existe:
            cor_fundo = QColor("#0f172a") if self.modo_escuro else QColor("#e2e8f0")
            self.pixmap_mapa_completo.fill(cor_fundo)
        self.atualizar_mapa()

    def adicionar_ponto_interesse(self, tipo: str, x: float, y: float, nome: str = "", cor: str = "#ffffff"):
        poi = {"tipo": tipo, "x": x, "y": y}
        if nome:
            poi["nome"] = nome
        if cor:
            poi["cor"] = cor
        self.pontos_interesse.append(poi)
        self.atualizar_mapa()

    def adicionar_rua(self, nome: str, x: float, y: float, angulo: float = 0.0):
        self.nomes_ruas.append({"nome": nome, "x": x, "y": y, "angulo": angulo})
        self.atualizar_mapa()

    def adicionar_nome_rua(self, nome: str, x: float, y: float, angulo: float = 0.0):
        self.adicionar_rua(nome, x, y, angulo)


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

    def resizeEvent(self, event):
        super().resizeEvent(event)
        self.atualizar_mapa()

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
        w = self.rotulo_mapa.width()
        h = self.rotulo_mapa.height()

        if w < 10 or h < 10:
            return

        resultado = QPixmap(w, h)
        cor_fundo_canvas = QColor("#090d16") if self.modo_escuro else Qt.GlobalColor.black
        resultado.fill(cor_fundo_canvas)

        painter = QPainter(resultado)
        painter.setRenderHint(QPainter.RenderHint.Antialiasing)
        painter.setRenderHint(QPainter.RenderHint.SmoothPixmapTransform)

        carro_tela_x = w // 2
        carro_tela_y = int(h * 0.8)

        # 1. RENDERIZAÇÃO DO MAPA E ROTAS
        painter.translate(carro_tela_x, carro_tela_y)
        painter.rotate(-(self.angulo_atual + 90))
        painter.translate(-self.carro_x, -self.carro_y)

        painter.drawPixmap(0, 0, self.pixmap_mapa_completo)

        cor_linha = QColor("#4ade80") if self.modo_escuro else QColor("darkgreen")
        pen_linha = QPen(cor_linha, 6, Qt.PenStyle.SolidLine)
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

        # 1.1 RENDERIZAÇÃO DOS ÍCONES E NOMES DE PONTOS DE INTERESSE
        for poi in self.pontos_interesse:
            tipo = poi.get("tipo", "").lower()
            nome = poi.get("nome", "")
            cor_val = poi.get("cor", "#ffffff")
            cor_poi = QColor(cor_val) if QColor(cor_val).isValid() else QColor("#ffffff")

            pix = self.icones.get(tipo)

            painter.save()
            painter.translate(poi["x"], poi["y"])
            # Compensa a rotação do mapa para que o ícone e o nome acompanhem a orientação vertical da tela
            painter.rotate(self.angulo_atual + 90)

            if pix and not pix.isNull():
                w_pix = pix.width()
                h_pix = pix.height()
                painter.drawPixmap(-w_pix // 2, -h_pix // 2, pix)
                offset_y = h_pix // 2 + 4
            else:
                raio = 14
                painter.setBrush(cor_poi)
                painter.setPen(QPen(QColor(255, 255, 255, 220), 2))
                painter.drawEllipse(QPoint(0, 0), raio, raio)
                offset_y = raio + 6

            if nome:
                fonte_poi = QFont("Segoe UI", 9, QFont.Weight.Bold)
                painter.setFont(fonte_poi)
                fm = painter.fontMetrics()
                largura_texto = fm.horizontalAdvance(nome)
                altura_texto = fm.height()

                pad_x = 6
                pad_y = 2
                ret_x = -largura_texto // 2 - pad_x
                ret_y = offset_y
                ret_w = largura_texto + (pad_x * 2)
                ret_h = altura_texto + (pad_y * 2)

                # Caixa de fundo translúcida para contraste e legibilidade
                painter.setBrush(QColor(15, 23, 42, 215))
                painter.setPen(QPen(cor_poi, 1.5))
                painter.drawRoundedRect(ret_x, ret_y, ret_w, ret_h, 4, 4)

                # Texto com a cor customizada
                painter.setPen(cor_poi)
                painter.drawText(
                    ret_x,
                    ret_y,
                    ret_w,
                    ret_h,
                    Qt.AlignmentFlag.AlignCenter,
                    nome,
                )

            painter.restore()

        # 1.2 RENDERIZAÇÃO DOS NOMES DAS RUAS
        fonte_rua = QFont("Segoe UI", 9, QFont.Weight.DemiBold)
        for rua in self.nomes_ruas:
            nome = rua.get("nome", "")
            if not nome:
                continue
            x = rua.get("x", 0.0)
            y = rua.get("y", 0.0)
            angulo_extra = rua.get("angulo", 0.0)

            painter.save()
            painter.translate(x, y)
            # Acompanha a rotação para manter a legibilidade
            painter.rotate(self.angulo_atual + 90 + angulo_extra)

            painter.setFont(fonte_rua)
            painter.setPen(QColor(255, 255, 255))  # Cor branca pura, sem contorno

            fm = painter.fontMetrics()
            largura_texto = fm.horizontalAdvance(nome)
            altura_texto = fm.height()

            painter.drawText(
                -largura_texto // 2,
                altura_texto // 4,
                nome,
            )
            painter.restore()

        # 2. SETA INDICADORA DO CARRO
        painter.resetTransform()
        painter.setPen(Qt.PenStyle.NoPen)
        cor_carro = QColor("#22c55e") if self.modo_escuro else QColor("lightgreen")
        painter.setBrush(cor_carro)

        seta_carro = QPolygon(
            [
                QPoint(carro_tela_x, carro_tela_y - 20),
                QPoint(carro_tela_x - 12, carro_tela_y + 12),
                QPoint(carro_tela_x + 12, carro_tela_y + 12),
            ]
        )
        painter.drawPolygon(seta_carro)

        # 3. PAINEL HUD DINÂMICO
        hud_bg = QColor(15, 23, 42, 230) if self.modo_escuro else QColor(15, 23, 42, 210)

        # 3.1 VELOCÍMETRO
        painter.setBrush(hud_bg)
        painter.setPen(QPen(cor_carro, 2))
        painter.drawRoundedRect(15, h - 85, 90, 70, 10, 10)

        painter.setPen(QColor("white"))
        painter.setFont(QFont("Segoe UI", 18, QFont.Weight.Bold))
        painter.drawText(
            15, h - 85, 90, 35, Qt.AlignmentFlag.AlignCenter, str(int(round(self.velocidade_kmh)))
        )

        painter.setPen(QColor("lightgray"))
        painter.setFont(QFont("Segoe UI", 8, QFont.Weight.Bold))
        painter.drawText(15, h - 45, 90, 20, Qt.AlignmentFlag.AlignCenter, "KM/H")

        # 3.2 PLACA DE LIMITE DE VELOCIDADE
        centro_x, centro_y = 150, h - 50
        raio = 18

        painter.setBrush(QColor("white"))
        painter.setPen(QPen(QColor(220, 38, 38), 3))
        painter.drawEllipse(QPoint(centro_x, centro_y), raio, raio)

        painter.setPen(QColor("black"))
        painter.setFont(QFont("Segoe UI", 10, QFont.Weight.Bold))
        painter.drawText(
            centro_x - raio, centro_y - raio, raio * 2, raio * 2, Qt.AlignmentFlag.AlignCenter, "50"
        )

        # 3.3 PAINEL DE ETA
        eta_w, eta_h = min(220, int(w * 0.35)), 70
        painter.setBrush(hud_bg)
        painter.setPen(QPen(QColor(0, 150, 255), 2))
        painter.drawRoundedRect(w - eta_w - 15, h - 85, eta_w, eta_h, 10, 10)

        dist_m = self.calcular_distancia_restante()
        texto_dist = f"{dist_m/1000:.1f} km" if dist_m >= 1000 else f"{int(dist_m)} m"
        tempo_min = max(1, math.ceil((dist_m / 1000) / self.VELOCIDADE_MEDIA_ROTA_KMH * 60))

        painter.setPen(QColor("white"))
        painter.setFont(QFont("Segoe UI", 10, QFont.Weight.Bold))
        painter.drawText(w - eta_w, h - 78, eta_w - 10, 22, Qt.AlignmentFlag.AlignLeft, f"Dist.: {texto_dist}")

        painter.setPen(QColor("#4ade80") if self.modo_escuro else QColor("lightgreen"))
        painter.setFont(QFont("Segoe UI", 9))
        painter.drawText(w - eta_w, h - 53, eta_w - 10, 22, Qt.AlignmentFlag.AlignLeft, f"ETA: {tempo_min} min")

        # 3.4 CARTÃO DE PRÓXIMA MANOBRA
        man_w, man_h = min(240, int(w * 0.38)), 70
        painter.setBrush(hud_bg)
        painter.setPen(QPen(QColor(255, 165, 0), 2))
        painter.drawRoundedRect(w - man_w - 15, 12, man_w, man_h, 10, 10)

        dist_texto, instrucao, seta = self.obter_proxima_manobra()

        painter.setPen(QColor(255, 165, 0))
        painter.setFont(QFont("Segoe UI", 24, QFont.Weight.Bold))
        painter.drawText(w - man_w - 5, 12, 45, man_h, Qt.AlignmentFlag.AlignCenter, seta)

        painter.setPen(QColor("white"))
        painter.setFont(QFont("Segoe UI", 10, QFont.Weight.Bold))
        painter.drawText(w - man_w + 40, 20, man_w - 50, 20, Qt.AlignmentFlag.AlignLeft, instrucao)

        painter.setPen(QColor("lightgray"))
        painter.setFont(QFont("Segoe UI", 9))
        painter.drawText(w - man_w + 40, 43, man_w - 50, 20, Qt.AlignmentFlag.AlignLeft, dist_texto)

        painter.end()
        self.rotulo_mapa.setPixmap(resultado)

    def mover_carro(self):
        if self.em_pausa:
            self.velocidade_atualizada.emit(self.velocidade_kmh)
            self.atualizar_mapa()
            return

        alvo_x, alvo_y = self.rota[self.indice_ponto_atual]

        dx = alvo_x - self.carro_x
        dy = alvo_y - self.carro_y
        distancia = (dx**2 + dy**2) ** 0.5

        e_ultimo_segmento = self.indice_ponto_atual == len(self.rota) - 1
        vel_minima = 0.0 if e_ultimo_segmento else self.VELOCIDADE_MIN_CURVA_KMH

        fator_alvo = min(1.0, distancia / 200.0)
        velocidade_alvo_kmh = vel_minima + (self.VELOCIDADE_MAX_KMH - vel_minima) * (fator_alvo**0.8)

        if self.indice_ponto_atual == 1:
            origem_x, origem_y = self.rota[0]
            dist_origem = ((self.carro_x - origem_x) ** 2 + (self.carro_y - origem_y) ** 2) ** 0.5
            fator_origem = min(1.0, dist_origem / 150.0)
            velocidade_alvo_kmh *= fator_origem

        if self.velocidade_kmh < velocidade_alvo_kmh:
            self.velocidade_kmh = min(velocidade_alvo_kmh, self.velocidade_kmh + 0.6)
        elif self.velocidade_kmh > velocidade_alvo_kmh:
            self.velocidade_kmh = max(velocidade_alvo_kmh, self.velocidade_kmh - 0.9)

        self.velocidade = max(0.05, (self.velocidade_kmh / self.VELOCIDADE_MAX_KMH) * 1.8)

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

        self.velocidade_atualizada.emit(self.velocidade_kmh)
        self.atualizar_mapa()

    def reiniciar_rota(self):
        self.indice_ponto_atual = 1
        self.carro_x = float(self.rota[0][0])
        self.carro_y = float(self.rota[0][1])
        self.velocidade_kmh = 0.0
        self.calcular_angulo_inicial()
        self.em_pausa = False