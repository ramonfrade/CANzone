# CANzone — Contrato de Arquitetura

> Regras combinadas para os módulos se entenderem sem quebrar.
> Leia antes de mexer em qualquer arquivo e cobre nos PRs dos colegas.

## Donos dos módulos

| Módulo | Dono | Responsabilidade |
|---|---|---|
| `telemetry/telemetry.py` | Telemetria | Fonte de dados CAN (RPM, temperatura). `CanProvider` = interface, `SimProvider` = simulação atual, `RealProvider` = dispositivo real (futuro). |
| `janela_mapa.py` | Mapa (Lucas) | Navegação GPS. `MapaWidget` simula o carro na rota e emite a velocidade. |
| `tela.py` | Dashboard/UI | Interface gráfica: sensores, filtros, popovers. Consome os dados dos módulos acima. |
| `main.py` | Arquitetura | Lançador único. Usa `start_telemetry` do `tela.py`. |

## Formato dos dados

### Dados de telemetria (CAN / simulação)

Dict com as chaves **exatas** (mesmas unidades do simulador):

```python
{
    "rpm": 1500,          # inteiro, rev/min
    "speed": 45.0,        # float, km/h
    "temp": 88.2,         # float, °C
}
```

Qualquer provider (`SimProvider` ou futuro `RealProvider`) deve entregar o mesmo dict.

### Sensores da UI

Lista de `[nome, valor]` **mutável**, ou seja, `sensor[0]` é o nome e `sensor[1]` é o valor (sempre string de exibição). Nunca use tupla.

```python
["RPM", "1500 RPM"]
```

Atualização **por nome**, nunca substituindo a lista inteira nem mudando o índice de posição.

## Fonte da verdade de cada sensor

| Sensor | Fonte | Método |
|---|---|---|
| `Velocidade` | Mapa (`janela_mapa`) | `MapaWidget.velocidade_atualizada` → `set_velocidade` |
| `RPM` | Telemetria | `set_sensor_data` |
| `Temp. Arrefecimento` | Telemetria | `set_sensor_data` |

Cada sensor tem **um único escritor**. Se precisar mudar a fonte, revise o contrato primeiro.

## Regras de threading

- Threads de dados **nunca tocam diretamente na UI**.
- Comunicação thread → UI é feita **sempre** via `Signal` do Qt (`SignalBridge`).
- A telemetria usa callback (`insert_callback`); a ponte converte em `Signal`.
- Desligar providers com `stop()` no `aboutToQuit`, como no `start_telemetry`.

## Entrada da aplicação

`main.py` e `tela.py` rodam a mesma coisa (`start_telemetry(window)`).
Não duplicar lógica de arranque nos dois arquivos.

## Simulação × dispositivo real

- Hoje só o `SimProvider` é usado (simulação criada pelo grupo).
- O dispositivo real está com o professor; quando chegar:
  - `RealProvider` é **responsabilidade da telemetria**, não da arquitetura.
  - Ele deve implementar `start()`/`stop()` e emitir o **mesmo dict** acima.
  - A troca acontece em `initialize_system()` sem tocar na UI.

## Checklist para PRs

1. `python -m py_compile main.py tela.py janela_mapa.py telemetry/telemetry.py` não dá erro.
2. Somou com `main.py` e `tela.py` sem crash (abrir popover + filtro + mapa).
3. Não criou outra fonte de dados paralela ("mais um simulador").
4. Respeitou formato de sensor `[nome, valor]` mutável, atualizado por nome.
5. Non-tupla: nunca `sensor[1] = ...` sobre tupla.