#!/usr/bin/env python

import rospy
import math
from custom_classes import *  # imports all classes
import actionlib
from move_base_msgs.msg import MoveBaseAction, MoveBaseActionGoal, MoveBaseActionFeedback, MoveBaseActionResult, MoveBaseGoal, MoveBaseFeedback
from actionlib_msgs.msg import GoalID, GoalStatusArray
from geometry_msgs.msg import PoseWithCovarianceStamped, PoseStamped
from squaternion import euler2quat


PENDING = 0
ACTIVE = 1
DONE = 2
WARN = 3
ERROR = 4

#global variables
robot = position()
person = position()
tracking = True


#Callback functions

def feedback_callback(feedback):
    pass
   #print feedback 
    #robot.x = feedback.base_position.pose.position.x
    #robot.y = feedback.base_position.pose.position.y


def amcl_pose_callback(msg):
    #rospy.loginfo("amcl_pose recieved")
    global robot
    robot.x = msg.pose.pose.position.x
    robot.y = msg.pose.pose.position.y


def person_pose_callback(msg):
    #rospy.loginfo("person_pose received")
    global person
    person.x = msg.pose.position.x
    person.y = msg.pose.position.y


if __name__ == "__main__":

    rospy.init_node("target_calculation")

    #initialize action client
    action_server_name = "/robot/move_base"
    client = actionlib.SimpleActionClient(action_server_name, MoveBaseAction)

    rospy.loginfo("Waiting for action server" + action_server_name)
    client.wait_for_server()
    rospy.loginfo("Action server found..." + action_server_name)

    #initialize /amcl_pose subscriber
    # confirmar que el topic esta bien
    sub_amcl = rospy.Subscriber("/robot/amcl_pose", PoseWithCovarianceStamped, amcl_pose_callback)

    #initialize /person_pose subscriber
    sub_person = rospy.Subscriber("/person_pose", PoseStamped, person_pose_callback)

    while True:
        if tracking:    

            goal = []
            goal.append(calculate_goal_position(robot, person))  # index 0

            q = euler2quat(0, 0, goal[0].theta)  # theta en rad

            gp = MoveBaseGoal()
            gp.target_pose.header.stamp = rospy.Time.now()
            gp.target_pose.header.frame_id = "robot_map"
            gp.target_pose.pose.position.x = goal[0].x
            gp.target_pose.pose.position.y = goal[0].y
            gp.target_pose.pose.position.z = goal[0].z
            gp.target_pose.pose.orientation.x = q.x
            gp.target_pose.pose.orientation.y = q.y
            gp.target_pose.pose.orientation.z = q.z
            gp.target_pose.pose.orientation.w = q.w

            print ("GOAL: x = " + str(goal[0].x) + "  y = " + str(goal[0].y))
            print ("ROBOT: x = " + str(robot.x) + "  y = " + str(robot.y))

            client.send_goal(gp, feedback_cb=feedback_callback)
            state = client.get_state()
            rate = rospy.Rate(1)  #actualiza el goal cada 1s 

            while state < DONE and tracking:

                rate.sleep()

                goal.append(calculate_goal_position(robot, person))

                if goal[0].x != goal[1].x or goal[0].y != goal[1].y or goal[0].theta != goal[1].theta:
                    # borramos el goal anterior por lo que goal[0] es el nuevo goal

                    goal.pop(0)
                    q = euler2quat(0, 0, goal[0].theta)

                    gp.target_pose.header.stamp = rospy.Time.now()
                    gp.target_pose.header.frame_id = "robot_map"
                    gp.target_pose.pose.position.x = goal[0].x
                    gp.target_pose.pose.position.y = goal[0].y
                    gp.target_pose.pose.position.z = goal[0].z
                    gp.target_pose.pose.orientation.x = q.x
                    gp.target_pose.pose.orientation.y = q.y
                    gp.target_pose.pose.orientation.z = q.z
                    gp.target_pose.pose.orientation.w = q.w


                    client.send_goal(gp, feedback_cb=feedback_callback)

                state = client.get_state()

            if state == DONE:
                rospy.loginfo(
                    "La persona esta parada y el robot en su radio minimo de seguimiento")

            elif state == WARN:
                rospy.loginfo("There is a warning in the server side")

            elif state == ERROR:
                rospy.loginfo("Something went wrong in the server side")

            
    rospy.spin()
    