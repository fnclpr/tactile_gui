import rclpy
from rclpy.node import Node
from uclv_tactile_interfaces.msg import TactileStamped
import numpy as np

class DummyTactilePublisher(Node):
    def __init__(self):
        super().__init__('dummy_tactile_publisher')
        # Pubblica sul topic letto dalla GUI
        self.pub = self.create_publisher(TactileStamped, 'tactile_voltage/rect', 10)
        # Timer a 20 Hz (ogni 50ms)
        self.timer = self.create_timer(0.05, self.timer_callback)
        self.t = 0.0

    def timer_callback(self):
        msg = TactileStamped()
        msg.header.stamp = self.get_clock().now().to_msg()
        msg.header.frame_id = "fingertip0"
        msg.tactile.rows = 5
        msg.tactile.cols = 5
        msg.tactile.info = "voltages_simulated"

        # Genera una deformazione gaussiana (un punto di pressione che ruota al centro)
        x = np.linspace(-1, 1, 5)
        y = np.linspace(-1, 1, 5)
        xx, yy = np.meshgrid(x, y)
        
        # Centro di pressione mobile
        cx = 0.4 * np.sin(self.t)
        cy = 0.4 * np.cos(self.t)
        r = np.sqrt((xx - cx)**2 + (yy - cy)**2)
        
        # Modulazione di voltaggio (da 0.0V a 3.0V)
        grid = 3.0 * np.exp(-4 * r**2)
        
        # Assegna i 25 valori float
        msg.tactile.data = grid.flatten().astype(np.float32).tolist()

        self.pub.publish(msg)
        self.t += 0.1

def main():
    rclpy.init()
    node = DummyTactilePublisher()
    try:
        rclpy.spin(node)
    except KeyboardInterrupt:
        pass
    finally:
        node.destroy_node()
        rclpy.shutdown()

if __name__ == '__main__':
    main()