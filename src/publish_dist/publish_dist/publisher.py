import math

from geometry_msgs.msg import Twist

import rclpy
from rclpy.node import Node

from tf2_ros import TransformException
from tf2_ros.buffer import Buffer
from tf2_ros.transform_listener import TransformListener
from std_msgs.msg import Float32
import numpy as np
from sklearn.model_selection import train_test_split
from sklearn.neural_network import MLPRegressor
import pickle
from visualization_msgs.msg import Marker
from geometry_msgs.msg import Point
from builtin_interfaces.msg import Duration
from rclpy.time import Time, Duration



def read_file(filepath):
    x = []
    y = []
    with open(filepath) as f:
        for line in f:
            data = line.strip().split(',')
            x.append(float(data[0]))
            y.append(float(data[1]))
    return np.array(x, dtype=np.float32).reshape(-1,1), np.array(y, dtype=np.float32)

class DistPublisher(Node):

    def __init__(self):
        super().__init__('dist_publisher')
        X, Y = read_file("./data/part1.txt")
        X_train, X_test, Y_train, Y_test = train_test_split(X, Y, test_size=0.2, random_state=42)
        self.model = MLPRegressor(random_state=1, max_iter=2000, tol=0.1, hidden_layer_sizes=1000)
        self.model.fit(X_train, Y_train)
        train_score = self.model.score(X_train, Y_train)
        test_score = self.model.score(X_test, Y_test)
        self.subscription = self.create_subscription(
            Float32,
            '/vrep/metalDetector',
            self.on_timer,
            10)

        self.marker_pub = self.create_publisher(Marker, "/detected_cylinder", 10)
        self.tf_buffer = Buffer()
        self.tf_listener = TransformListener(self.tf_buffer, self)
        self.nx, self.ny = 100, 100
        self.occupancy_grid = dict()
        self.grid_precision = 0.5


    def publish_cylinder(self, x, y, radius, index):
        marker = Marker()
        marker.header.frame_id = "world"
        marker.header.stamp = self.get_clock().now().to_msg()

        marker.ns = "predicted_objects"
        marker.id = index
        marker.type = Marker.CYLINDER
        marker.action = Marker.ADD

        # Position (center of cylinder)
        marker.pose.position.x = x
        marker.pose.position.y = y
        marker.pose.position.z = 0. # cylinder sits on ground

        # Orientation (upright cylinder)
        marker.pose.orientation.x = 0.0
        marker.pose.orientation.y = 0.0
        marker.pose.orientation.z = 0.0
        marker.pose.orientation.w = 1.0

        # Cylinder dimensions
        marker.scale.x = radius * 2    # diameter
        marker.scale.y = radius * 2
        marker.scale.z = 10.

        # Color
        marker.color.r = 1.0
        marker.color.g = 0.2
        marker.color.b = 0.2
        marker.color.a = 0.8


        self.marker_pub.publish(marker)

    def circle_periphery_points(self, x_c, y_c, R, step_deg=2):
        """Return unique 0.5-precision points on the circle's periphery."""
        for deg in range(0, 360, step_deg):
            rad = math.radians(deg)
            x = x_c + R * math.cos(rad)
            y = y_c + R * math.sin(rad)

            # round to nearest 0.5
            x_r = round(x / self.grid_precision) * self.grid_precision
            y_r = round(y / self.grid_precision) * self.grid_precision

            key = (x_r, y_r)
            self.occupancy_grid[key] = self.occupancy_grid.get(key, 0) + 1

        return
    
    def non_max_suppression(self, suppression_radius):
        """
        Perform NMS on occupancy_grid where occupancy_grid maps (x, y) -> value.
        """
        points = [(x, y, v) for (x, y), v in self.occupancy_grid.items()]
        points.sort(key=lambda p: p[2], reverse=True)

        kept = []

        for x, y, val in points:
            keep = True

            # Compare with already kept maxima
            for kx, ky, kval in kept:
                if (x - kx)**2 + (y - ky)**2 <= suppression_radius**2:
                    keep = False
                    break

            if keep:
                kept.append((x, y, val))

        return kept


    def on_timer(self, msg):
        # self.get_logger().info(str(msg))
        if not self.tf_buffer.can_transform('world', 'VSV/Tool', rclpy.time.Time()):
            self.get_logger().warn("Cannot transform world → VSV/Tool yet")
            return
        t = self.tf_buffer.lookup_transform('world', 'VSV/Tool', rclpy.time.Time())
        if msg.data > 0.2:
            dist = self.model.predict([[msg.data]])
            self.get_logger().info(f"Predicted distance: {dist[0]}")
            self.get_logger().info(f"Translation: x={t.transform.translation.x}, y={t.transform.translation.y}, z={t.transform.translation.z}")

            x_r = t.transform.translation.x
            y_r = t.transform.translation.y
            self.circle_periphery_points(x_r, y_r, float(dist))
            
            local_maxima = self.non_max_suppression(suppression_radius=20.0)
            # Publish all detected maxima
            for i, (x, y, score) in enumerate(local_maxima):
                self.publish_cylinder(x, y, 1.0, i)

            
        

def main():
    rclpy.init()
    node = DistPublisher()
    try:
        rclpy.spin(node)
    except KeyboardInterrupt:
        pass

    rclpy.shutdown()