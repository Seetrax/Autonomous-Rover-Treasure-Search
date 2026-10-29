import math

from geometry_msgs.msg import Twist

import rclpy
from rclpy.node import Node

from tf2_ros import TransformException
from tf2_ros.buffer import Buffer
from tf2_ros.transform_listener import TransformListener
from std_msgs.msg import Float32

class FrameListener(Node):

    def __init__(self):
        super().__init__('treasure_listener')

        # Declare and acquire `target_frame` parameter
        self.target_frame = self.declare_parameter(
          'target_frame', 'VSV/Tool').get_parameter_value().string_value

        self.tf_buffer = Buffer()
        self.tf_listener = TransformListener(self.tf_buffer, self)

        self.subscription = self.create_subscription(
            Float32,
            '/vrep/metalDetector',
            self.on_timer,
            10)
        # self.out_file = open("data/part1.txt", "a")

    def on_timer(self, msg):
        # Store frame names in variables
        self.get_logger().info(str(msg))
        from_frame_rel = self.target_frame
        t = self.tf_buffer.lookup_transform('world', 'VSV/Tool', rclpy.time.Time())
        self.get_logger().info(f"Translation: x={t.transform.translation.x}, y={t.transform.translation.y}, z={t.transform.translation.z}")
        min_dist = float('inf')
        for i in range(1,6):
            to_frame_rel = 'Treasure%d'%(i)
            
            try:
                t = self.tf_buffer.lookup_transform(
                    to_frame_rel,
                    from_frame_rel,
                    rclpy.time.Time())

                # Print the transformation to the console (similar to tf2_echo)
                # self.get_logger().info(f"Transformation from {to_frame_rel} to {from_frame_rel}:")
                # self.get_logger().info(f"Translation: x={t.transform.translation.x}, y={t.transform.translation.y}, z={t.transform.translation.z}")
                dist = math.sqrt (t.transform.translation.x ** 2 + t.transform.translation.y ** 2 + t.transform.translation.z ** 2)
                # self.get_logger().info(f"Translation: dist={dist}")
                if dist < min_dist:
                    min_dist = dist
                # self.get_logger().info(f"Rotation: x={t.transform.rotation.x}, y={t.transform.rotation.y}, z={t.transform.rotation.z}, w={t.transform.rotation.w}")
            except TransformException as ex:
                self.get_logger().info(
                    f'Could not transform {to_frame_rel} to {from_frame_rel}: {ex}')
                return
        self.get_logger().info(f"min dist: {min_dist}")
        # self.out_file.write("%f,%f\n"%(msg.data, min_dist))
def main():
    rclpy.init()
    node = FrameListener()
    try:
        rclpy.spin(node)
    except KeyboardInterrupt:
        pass

    rclpy.shutdown()