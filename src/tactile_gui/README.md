```markdown
# tactile_gui

Un'applicazione GUI ad alte prestazioni sviluppata in **ROS 2 Jazzy** (Python, PyQt6, PyQtGraph) per la visualizzazione in tempo reale dei dati di matrice di sensori tattili 5x5 sotto forma di heatmap termica.

Il pacchetto fa parte dell'architettura di percezione tattile ed è progettato per interfacciarsi con i nodi di acquisizione hardware USB-seriali e con i nodi C++ di elaborazione dei voltaggi/forze tramite messaggi ed azioni definiti nel pacchetto `uclv_tactile_interfaces`.

---

## 🚀 Caratteristiche Principali

* **Rendering Grafico ad Alta Frequenza:** Utilizzo di `PyQtGraph` (sopra `PyQt6`) per il rendering a 60+ FPS a basso consumo di CPU.
* **Architettura Multi-Thread Thread-Safe:** Il loop di ROS 2 (`rclpy.spin`) viene eseguito in un thread secondario dedicato e comunica con la GUI tramite **Segnali e Slot di PyQt**, garantendo che l'interfaccia utente non si blocchi mai.
* **Mappatura Cromatico-Termica Dinamica:** Integrazione delle colormap di Matplotlib (`hot`, `viridis`, ecc.) con barra della scala dei voltaggi/forze interattiva (`ColorBarItem`).
* **Integrazione Action Client:** Pulsante integrato per richiedere la ricalibrazione del bias/tara direttamente all'Action Server C++ `ComputeBias`.
* **Gestione Segnali di Chiusura:** Supporto nativo all'interruzione tramite `CTRL+C` (SIGINT) da terminale per un teardown pulito dei nodi e dei thread.

---

## 📂 Struttura del Pacchetto

```text
tactile_gui/
├── launch/
│   └── tactile_gui.launch.py       # Launch file Python per avvio parametrizzato
├── resource/
│   └── tactile_gui
├── tactile_gui/
│   ├── __init__.py
│   └── heatmap_gui.py              # Nodo principale ROS 2 + Codice GUI PyQt6
├── package.xml                     # Dipendenze di sistema e ROS 2
├── setup.cfg
├── setup.py                        # Entry point dell'eseguibile ros2 run
└── README.md

```

---

## 🛠️ Requisiti e Dipendenze

Il pacchetto è ottimizzato per **Ubuntu 24.04 LTS** con **ROS 2 Jazzy Jalisco** (ambiente Docker o nativo).

### Dipendenze ROS 2:

* `rclpy`
* `uclv_tactile_interfaces` (pacchetto custom contenente `TactileStamped.msg` e `ComputeBias.action`)

### Dipendenze Python di Sistema:

```bash
sudo apt-get update && sudo apt-get install -y \
    python3-pyqt6 \
    python3-pyqtgraph \
    python3-matplotlib

```

---

## 🔄 Interfacce ROS 2

### Topic Sottoscritti (Subscribers)

| Topic | Tipo Messaggio | Descrizione |
| --- | --- | --- |
| `tactile_voltage/rect` | `uclv_tactile_interfaces/msg/TactileStamped` | Riceve la matrice di voltaggi/forze 5x5 flattenizzata (25 elementi). |

### Action Client

| Nome Action | Tipo Action | Descrizione |
| --- | --- | --- |
| `tactile_voltage/action_compute_bias` | `uclv_tactile_interfaces/action/ComputeBias` | Invia la richiesta di campionamento e azzeramento del bias al nodo hardware. |

### Parametri Configurabili

| Parametro | Tipo | Valore Default | Descrizione |
| --- | --- | --- | --- |
| `topic_name` | `string` | `tactile_voltage/rect` | Topic su cui ascoltare i dati del sensore. |
| `action_name` | `string` | `tactile_voltage/action_compute_bias` | Nome dell'action server per il ricalcolo del bias. |
| `rows` | `int` | `5` | Numero di righe della matrice tattile. |
| `cols` | `int` | `5` | Numero di colonne della matrice tattile. |

---

## 📦 Compilazione ed Installazione

Dalla radice del tuo workspace ROS 2 (`~/ros2_ws`):

```bash
# 1. Posizionati nel workspace
cd ~/ros2_ws

# 2. Compila il pacchetto
colcon build --symlink-install --packages-select tactile_gui

# 3. Effettua il source dell'ambiente
source install/local_setup.bash

```

---

## 💻 Guida all'Uso

### 1. Esecuzione della GUI

Dopo aver compilato e caricato l'ambiente:

```bash
ros2 run tactile_gui heatmap_gui

```

In alternativa, è possibile avviarla tramite Launch File:

```bash
ros2 launch tactile_gui tactile_gui.launch.py

```

### 2. Personalizzazione dei Parametri da CLI

Puoi sovrascrivere i parametri predefiniti da riga di comando (es. ascoltare su un altro topic):

```bash
ros2 run tactile_gui heatmap_gui --ros-args -p topic_name:=/my_tactile_sensor/data -p rows:=5 -p cols:=5

```

---

## 🧪 Testing e Simulazione (Senza Hardware Reale)

In assenza del sensore fisico, è possibile testare l'intera pipeline di rendering usando uno script publisher simulato o tramite comandi da terminale.

### Opzione A: Simulatore Dinamico (Consigliato)

Crea uno script `dummy_publisher.py` nella radice del workspace per pubblicare un'onda di pressione che ruota al centro del pad 5x5 a 20 Hz:

```bash
python3 dummy_publisher.py

```

### Opzione B: Pubblicazione Singola da CLI

Per inviare una singola matrice tattile di prova da terminale:

```bash
ros2 topic pub --once /tactile_voltage/rect uclv_tactile_interfaces/msg/TactileStamped "
header:
  stamp:
    sec: 0
    nanosec: 0
  frame_id: 'fingertip0'
tactile:
  rows: 5
  cols: 5
  info: 'test'
  data: [
    0.0, 0.1, 0.2, 0.1, 0.0,
    0.1, 1.5, 2.8, 1.5, 0.1,
    0.2, 2.8, 3.3, 2.8, 0.2,
    0.1, 1.5, 2.8, 1.5, 0.1,
    0.0, 0.1, 0.2, 0.1, 0.0
  ]"

```

---

## 🔍 Comandi utili per Debug e Verifiche

Mentre la GUI è aperta, puoi eseguire i seguenti comandi da un secondo terminale per verificare lo stato delle connessioni:

* **Verifica della presenza del nodo GUI:**
```bash
ros2 node list
# Output atteso: /tactile_heatmap_gui

```


* **Ispezione delle sottoscrizioni e della frequenza dei dati:**
```bash
ros2 node info /tactile_heatmap_gui
ros2 topic hz /tactile_voltage/rect

```


* **Stato dell'Action Server per la calibrazione:**
```bash
ros2 action info /tactile_voltage/action_compute_bias

```



---

## ⚠️ Troubleshooting

* **Errore `FileNotFoundError` o Colormap Mancante:**
Assicurati di aver installato `python3-matplotlib`. La GUI utilizza `pg.colormap.getFromMatplotlib('hot')` per garantire la massima compatibilità cross-platform senza dipendere dai file fisici `.csv` di PyQtGraph.
* **Warning `QStandardPaths: XDG_RUNTIME_DIR not set`:**
È un avviso standard di Qt quando viene eseguito all'interno di container Docker. Non influenza il funzionamento dell'interfaccia e può essere ignorato.

```

```