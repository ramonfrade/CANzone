import os
from PIL import Image

pasta_script = os.path.dirname(os.path.abspath(__file__))
caminho_entrada = os.path.join(pasta_script, "mapa_exemplo.png")
caminho_saida = os.path.join(pasta_script, "mapa_grande.png")

imagem_original = Image.open(caminho_entrada)

imagem_redimensionada = imagem_original.resize(
    (2000, 2000), Image.Resampling.LANCZOS
)

imagem_redimensionada.save(caminho_saida)

print("Imagem redimensionada para 2000x2000 e salva como 'mapa_grande.png'!")