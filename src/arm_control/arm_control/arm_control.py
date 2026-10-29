#!/usr/bin/env python3

import tensorflow_models_base.venv_hack

import sys
import os

import rclpy
from rclpy.node import Node
from rclpy.time import Time

from sensor_msgs.msg import Image
from geometry_msgs.msg import Twist

import tensorflow as tf
import numpy as np

import cv2
# cv_bridge2 is a local version of cv_bridge compiled with numpy 2
from cv_bridge2 import CvBridge, CvBridgeError
from std_msgs.msg import Float32

class ShoreFollowerDrive(Node):
    def __init__(self):
        super().__init__("classify")

        self.declare_parameter('~/model_dir', ".")
        self.declare_parameter('~/linear_vel', 1.0)
        self.declare_parameter('~/twist_factor', 1.0)
        self.declare_parameter('~/arm_velocity', 1.0)
        self.model_dir_ = self.get_parameter('~/model_dir').get_parameter_value().string_value
        self.arm_velocity = self.get_parameter('~/arm_velocity').get_parameter_value().double_value

        self.load_model()

        self.br = CvBridge()
        self.twist_pub_ = self.create_publisher(Twist,"~/twist",10)
        self.image_sub_ = self.create_subscription(Image,"~/image", self.image_callback, 1)
        self.tool_pub = self.create_publisher(Float32,'~/tool_command', 1)

    def load_model(self):
        # Loads the model
        self.model = tf.keras.models.load_model(self.model_dir_)

    def image_callback(self, data):
        # Image call back and resize to proper shape
        # Regularization is done directly inside the model so we don't have to do it.
        raw = self.br.imgmsg_to_cv2(data,"bgr8")
        processed_ = np.expand_dims(cv2.resize(raw, (0,0), fx = 32.0/data.height, fy=32.0/data.width, interpolation=cv2.INTER_AREA), axis=0)
        self.twist_pub_.publish(self.image_to_rot(processed_))
        tool = Float32()
        tool.data = -np.pi/2
        self.tool_pub.publish(tool)


    def image_to_rot(self, img):
        # Reads the image, feed it to the network, get the predictions and act on it.
        out = Twist()
        # Runs the network
        res = self.model(img, training=False)[0]
        # Makes sure that the shape of the network matches the required shape
        assert(res.shape[0] == 9)
        #TODO: Use the network output so the robot can drive around the lake
        # returns a geometry_msgs.Twist
        
        action = np.argmax(res)
        label_x = action % 3
        label_z = action // 3
        out.linear.x = self.arm_velocity * (label_x - 1)
        out.linear.z = self.arm_velocity * (label_z - 1)
        print(out)
        return out


def main(args=None):
    rclpy.init(args=args)

    drive = ShoreFollowerDrive()

    rclpy.spin(drive)

    drive.destroy_node()
    rclpy.shutdown()

if __name__ == '__main__':
    main()
