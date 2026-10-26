import sys
import threading
import signal
import numpy as np

from PyQt6.QtWidgets import (QApplication, QMainWindow, QWidget, 
                             QVBoxLayout, QHBoxLayout, QPushButton, QLabel, QComboBox)
from PyQt6.QtCore import pyqtSignal, QObject, QTimer
import pyqtgraph as pg

import rclpy
from rclpy.node import Node
from rclpy.action import ActionClient

from uclv_tactile_interfaces.msg import TactileStamped
from uclv_tactile_interfaces.action import ComputeBias


class RosSignalBridge(QObject):
    """Bridge per trasferire in modo thread-safe i dati da ROS 2 al Main Thread Qt."""
    raw_data_signal = pyqtSignal(np.ndarray)
    rect_data_signal = pyqtSignal(np.ndarray)
    status_signal = pyqtSignal(str)


class TactileGuiNode(Node):
    """Nodo ROS 2 con doppia sottoscrizione permanente ai topic Raw e Debiased."""
    def __init__(self, bridge: RosSignalBridge):
        super().__init__('tactile_heatmap_gui')
        self.bridge = bridge

        self.declare_parameter('raw_topic', 'tactile_voltage/raw')
        self.declare_parameter('debiased_topic', 'tactile_voltage/rect')
        self.declare_parameter('action_name', 'compute_bias_action')
        self.declare_parameter('rows', 5)
        self.declare_parameter('cols', 5)

        self.raw_topic = self.get_parameter('raw_topic').value
        self.debiased_topic = self.get_parameter('debiased_topic').value
        self.action_name = self.get_parameter('action_name').value
        self.rows = self.get_parameter('rows').value
        self.cols = self.get_parameter('cols').value

        # Sottoscrizione permanente a entatrambi i topic (Opzione B)
        self.sub_raw = self.create_subscription(
            TactileStamped, self.raw_topic, self.raw_callback, 10)
        self.sub_rect = self.create_subscription(
            TactileStamped, self.debiased_topic, self.rect_callback, 10)

        self._action_client = ActionClient(self, ComputeBias, self.action_name)
        self.get_logger().info(f"GUI attiva. Iscritta a: {self.raw_topic} e {self.debiased_topic}")

    def raw_callback(self, msg: TactileStamped):
        if len(msg.tactile.data) == (self.rows * self.cols):
            mat = np.array(msg.tactile.data, dtype=np.float32).reshape((self.rows, self.cols))
            self.bridge.raw_data_signal.emit(mat)

    def rect_callback(self, msg: TactileStamped):
        if len(msg.tactile.data) == (self.rows * self.cols):
            mat = np.array(msg.tactile.data, dtype=np.float32).reshape((self.rows, self.cols))
            self.bridge.rect_data_signal.emit(mat)

    def send_bias_goal(self, num_samples=100):
        if not self._action_client.wait_for_server(timeout_sec=2.0):
            self.bridge.status_signal.emit("Errore: Action Server Bias non raggiungibile!")
            return

        goal_msg = ComputeBias.Goal()
        goal_msg.num_samples = num_samples

        self.bridge.status_signal.emit("Ricalibrazione tara/bias in corso...")
        future = self._action_client.send_goal_async(goal_msg)
        future.add_done_callback(self.goal_response_callback)

    def goal_response_callback(self, future):
        goal_handle = future.result()
        if not goal_handle.accepted:
            self.bridge.status_signal.emit("Richiesta di tara rifiutata.")
            return

        result_future = goal_handle.get_result_async()
        result_future.add_done_callback(self.get_result_callback)

    def get_result_callback(self, future):
        result = future.result().result
        if result.success:
            self.bridge.status_signal.emit("Tara/Bias completata con successo!")
        else:
            self.bridge.status_signal.emit("Errore durante il calcolo del Bias.")


class TactileHeatmapWindow(QMainWindow):
    """Finestra principale della GUI PyQt6."""
    def __init__(self, ros_node: TactileGuiNode, bridge: RosSignalBridge):
        super().__init__()
        self.ros_node = ros_node
        self.bridge = bridge

        self.setWindowTitle("Tactile Sensor Visualizer (5x5)")
        self.resize(700, 650)

        main_widget = QWidget()
        layout = QVBoxLayout()
        main_widget.setLayout(layout)
        self.setCentralWidget(main_widget)

        # Header di stato
        self.label_status = QLabel("Stato: Pronto - In attesa dati...")
        self.label_status.setStyleSheet("font-weight: bold; font-size: 14px; color: #333;")
        layout.addWidget(self.label_status)

        # Visualizzatore Mappa 2D
        self.graph_layout = pg.GraphicsLayoutWidget()
        layout.addWidget(self.graph_layout)

        self.plot_view = self.graph_layout.addPlot()
        self.plot_view.setAspectLocked(True)
        self.plot_view.invertY(True)  # Origine (0,0) in alto a sinistra

        self.img_item = pg.ImageItem()
        self.plot_view.addItem(self.img_item)

        # Mappa colori 'viridis'
        cmap = pg.colormap.getFromMatplotlib('viridis')
        self.img_item.setLookupTable(cmap.getLookupTable())

        # Livelli visivi di default (Debiased)
        self.current_mode = "DEBIASED"
        self.min_level = -0.2
        self.max_level = 2.0

        self.color_bar = pg.ColorBarItem(values=(self.min_level, self.max_level), cmap=cmap)
        self.color_bar.setImageItem(self.img_item, insert_in=self.plot_view)

        # Barra dei comandi
        ctrl_layout = QHBoxLayout()

        self.combo_mode = QComboBox()
        self.combo_mode.addItems(["Debiased (Rectified)", "Raw Voltage"])
        self.combo_mode.currentIndexChanged.connect(self.on_mode_changed)
        ctrl_layout.addWidget(self.combo_mode)

        self.btn_bias = QPushButton("Azzera Bias / Esegui Tara")
        self.btn_bias.setStyleSheet("padding: 8px; font-weight: bold; background-color: #2196F3; color: white;")
        self.btn_bias.clicked.connect(self.on_click_bias)
        ctrl_layout.addWidget(self.btn_bias)

        layout.addLayout(ctrl_layout)

        # Connessione Segnali -> Slot
        self.bridge.raw_data_signal.connect(self.on_raw_data)
        self.bridge.rect_data_signal.connect(self.on_rect_data)
        self.bridge.status_signal.connect(self.update_status)

    def on_mode_changed(self, index: int):
        if index == 0:
            self.current_mode = "DEBIASED"
            self.min_level, self.max_level = -0.2, 2.0
        else:
            self.current_mode = "RAW"
            self.min_level, self.max_level = 0.0, 3.3
        
        self.color_bar.setLevels((self.min_level, self.max_level))

    def on_raw_data(self, data: np.ndarray):
        if self.current_mode == "RAW":
            # Si applica la trasposta .T per allineare l'orientamento NumPy a PyQtGraph
            self.img_item.setImage(data.T, autoLevels=False, levels=(self.min_level, self.max_level))

    def on_rect_data(self, data: np.ndarray):
        if self.current_mode == "DEBIASED":
            self.img_item.setImage(data.T, autoLevels=False, levels=(self.min_level, self.max_level))

    def update_status(self, text: str):
        self.label_status.setText(f"Stato: {text}")

    def on_click_bias(self):
        self.ros_node.send_bias_goal(num_samples=100)


def main(args=None):
    rclpy.init(args=args)

    bridge = RosSignalBridge()
    ros_node = TactileGuiNode(bridge)

    spin_thread = threading.Thread(target=rclpy.spin, args=(ros_node,), daemon=True)
    spin_thread.start()

    app = QApplication(sys.argv)
    window = TactileHeatmapWindow(ros_node, bridge)
    window.show()

    # Timer per consentire la gestione dei segnali Python (SIGINT / CTRL+C)
    timer = QTimer()
    timer.timeout.connect(lambda: None)
    timer.start(100)

    signal.signal(signal.SIGINT, lambda sig, frame: app.quit())

    exit_code = app.exec()
    ros_node.destroy_node()
    rclpy.shutdown()
    spin_thread.join(timeout=1.0)
    sys.exit(exit_code)


if __name__ == '__main__':
    main()