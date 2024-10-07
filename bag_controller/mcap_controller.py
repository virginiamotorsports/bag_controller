"""
This python code uses the McapController class to record all messages
in all topics, & uses rosbags to store said data
"""

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
    """
    Initialize all variables & start the subscription to AmsReport
    """
    def __init__(self):
        super().__init__('mcap_controller')

        # Creating a subscription to topic "AmsReport", with a queue size of 10
        # Queue: will have a max message count of 10 and new messages will drop old ones
        self.subscription = self.create_subscription(AmsReport, 'ams_report', self.ams_callback, 10)
        self.subscription

        # State variables in the McapController
        self.prev_pos_air = False
        self.baging = False
        self.waiting_to_stop = False
        self.time_since_stop = self.get_clock().now()

        # Creating a timer for ending the bagging, runs every 1 second
        self.bagging_timer = self.create_timer(1, self.bagging_timer_callback)

    """
    Callback function for the subscription, will run whenever the messages are sent from rosbags
    But records in rosbags ALL messages sent in ALL topics 
    """
    def ams_callback(self, msg):
        pos_air_status = msg.pos_air_status

        # If pos_air_status is true, then keep running the code
        if pos_air_status == True and self.prev_pos_air == False:
            self.waiting_to_stop = False
            # print("restarting the timer for the bag")

        # If it is not bagging, then start the bagging process
        if pos_air_status == True and self.prev_pos_air == False and not self.baging:
            # self.rosbag_proc = subprocess.Popen(['ros2', 'bag', 'record', '-s', 'mcap', '-a'], stdout=subprocess.PIPE) # for testing
            # print("starting the bag")

            # Create a subprocess to start recording ALL messages in all topics, will keep running until SIGINT
            self.rosbag_proc = subprocess.Popen(['ros2', 'bag', 'record', '-s', 'mcap', '-a', '-o', '/bags'], stdout=subprocess.PIPE) # for the car
            self.baging = True

        # If pos_air_status is false & we are bagging, then start the timeout clock for 30 seconds.
        elif pos_air_status == False and self.prev_pos_air == True and self.baging:
            self.waiting_to_stop = True
        
        # print(self.get_clock().now() - self.time_since_stop - rclpy.time.Duration(seconds=30))
            
        self.prev_pos_air = msg.data

    """
    Function for the timer to see if we need to stop bagging (waiting_to_stop is true)
    After 30 seconds of waiting to stop, we can stop the recording and end the code
    Runs every 1 second
    """
    def bagging_timer_callback(self):
        # Check to see if we bagged in the last 30 seconds
        if  (self.get_clock().now() - self.time_since_stop).nanoseconds > rclpy.time.Duration(seconds=30).nanoseconds:
                # Interrupt the subprocess signal and stop the recording
                self.rosbag_proc.send_signal(subprocess.signal.SIGINT)
                self.baging = False
                self.waiting_to_stop = False
                # print("stopping bag")
        
        # If we are still running, and have bagged, then set timer to "reset"
        if not self.waiting_to_stop:
            self.time_since_stop = self.get_clock().now()
            # print("updating the time bag")

def main(args=None):
    # Initialize ROS library
    rclpy.init(args=args)
    # Creating the McapController
    sbr = McapController()

    # Start running the controller (will hang until the process ends, so shutdown will call whenever the
    # bagging_timer_callback sends the interrupt signal)
    rclpy.spin(sbr)
    rclpy.shutdown()


if __name__ == '__main__':
    main()