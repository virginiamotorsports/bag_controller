import rclpy
from rclpy.node import Node
from rclpy.serialization import serialize_message
import rclpy.time
from std_msgs.msg import String, Bool
import subprocess
import signal
from vm_msgs.msg import AmsReport

import rosbag2_py

class McapController(Node):
    def __init__(self):
        super().__init__('mcap_controller')

        self.subscription = self.create_subscription(AmsReport, 'ams_report', self.ams_callback, 10)
        self.subscription
        self.prev_pos_air = False
        self.baging = False
        self.waiting_to_stop = False
        self.time_since_stop = self.get_clock().now()
        self.bagging_timer = self.create_timer(1, self.bagging_timer_callback)

    def ams_callback(self, msg):
        pos_air_status = msg.pos_air_status
        if pos_air_status == True and self.prev_pos_air == False:
            self.waiting_to_stop = False
            # print("restarting the timer for the bag")

        if pos_air_status == True and self.prev_pos_air == False and not self.baging:
            # self.rosbag_proc = subprocess.Popen(['ros2', 'bag', 'record', '-s', 'mcap', '-a'], stdout=subprocess.PIPE) # for testing
            # print("starting the bag")

            self.rosbag_proc = subprocess.Popen(['ros2', 'bag', 'record', '-s', 'mcap', '-a', '-o', '/bags'], stdout=subprocess.PIPE) # for the car
            self.baging = True
        elif pos_air_status == False and self.prev_pos_air == True and self.baging:
            self.waiting_to_stop = True
        
        # print(self.get_clock().now() - self.time_since_stop - rclpy.time.Duration(seconds=30))
            
        self.prev_pos_air = msg.data
    def bagging_timer_callback(self):
        if  (self.get_clock().now() - self.time_since_stop).nanoseconds > rclpy.time.Duration(seconds=30).nanoseconds:
                self.rosbag_proc.send_signal(subprocess.signal.SIGINT)
                self.baging = False
                self.waiting_to_stop = False
                # print("stopping bag")
        if not self.waiting_to_stop:
            self.time_since_stop = self.get_clock().now()
            # print("updating the time bag")

def main(args=None):
    rclpy.init(args=args)
    sbr = McapController()
    rclpy.spin(sbr)
    rclpy.shutdown()


if __name__ == '__main__':
    main()