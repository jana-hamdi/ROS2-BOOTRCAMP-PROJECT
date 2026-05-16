#!/usr/bin/env python3
"""
Obstacle Avoider Node
=====================
Subscribes to /scan (LaserScan) and publishes to /cmd_vel (Twist).

Decision logic:
  - Read front (0° ± 30°), left (90° ± 20°), right (-90° ± 20°) distances
  - If front distance < front_threshold → turn toward the more open side
  - Otherwise → move forward

Compatible with ROS2 Humble + TurtleBot3 (burger / waffle).
"""

import math
import rclpy
from rclpy.node import Node
from sensor_msgs.msg import LaserScan
from geometry_msgs.msg import Twist


# ---------------------------------------------------------------------------
# Utility helpers
# ---------------------------------------------------------------------------

def safe_min(values: list) -> float:
    """
    Return the minimum of a list of floats, ignoring NaN, Inf, and zero.
    Returns float('inf') when no valid readings exist (all blocked or bad).
    """
    valid = [v for v in values if not math.isnan(v) and not math.isinf(v) and v > 0.0]
    return min(valid) if valid else float('inf')


def get_sector_ranges(ranges: list, center_deg: float, half_width_deg: float) -> list:
    """
    Extract all range readings within [center_deg ± half_width_deg].

    Args:
        ranges        : full list of floats from LaserScan.ranges
        center_deg    : centre angle of the sector (degrees, 0 = forward)
        half_width_deg: half-width of the sector (degrees)

    Returns:
        List of float readings belonging to the requested sector.

    Notes:
        - Assumes scan covers exactly 360° with uniform angular resolution.
        - Negative angles (e.g. -90°) are normalised to [0, 360°).
        - Wrap-around at 0°/360° is handled correctly.
    """
    n = len(ranges)
    if n == 0:
        return []

    # Normalise angles to [0, 360)
    center_deg = center_deg % 360
    start_deg  = (center_deg - half_width_deg) % 360
    end_deg    = (center_deg + half_width_deg) % 360

    result = []
    for i in range(n):
        angle = (i / n) * 360.0
        if start_deg <= end_deg:
            # No wrap-around
            if start_deg <= angle <= end_deg:
                result.append(ranges[i])
        else:
            # Sector wraps around 0° (e.g. 350° → 10°)
            if angle >= start_deg or angle <= end_deg:
                result.append(ranges[i])

    return result


# ---------------------------------------------------------------------------
# Main node class
# ---------------------------------------------------------------------------

class ObstacleAvoider(Node):
    """
    ROS2 node that reads LaserScan data and steers the robot away from
    obstacles using a simple reactive control strategy.

    Parameters (configurable at launch or via ros2 param set):
        front_threshold (float) : distance in metres below which the front
                                  is considered blocked. Default: 0.55 m
        forward_speed   (float) : linear velocity when path is clear (m/s).
                                  Default: 0.18 m/s
        turn_speed      (float) : angular velocity when turning (rad/s).
                                  Default: 0.60 rad/s
    """

    def __init__(self):
        super().__init__('obstacle_avoider')

        # ------------------------------------------------------------------
        # Declare ROS2 parameters (overridable from CLI / YAML / launch file)
        # ------------------------------------------------------------------
        self.declare_parameter('front_threshold', 0.55)
        self.declare_parameter('forward_speed',   0.18)
        self.declare_parameter('turn_speed',      0.60)

        self.front_threshold = self.get_parameter('front_threshold').value
        self.forward_speed   = self.get_parameter('forward_speed').value
        self.turn_speed      = self.get_parameter('turn_speed').value

        # ------------------------------------------------------------------
        # Publisher: velocity commands → /cmd_vel
        # ------------------------------------------------------------------
        self.cmd_pub = self.create_publisher(Twist, '/cmd_vel', 10)

        # ------------------------------------------------------------------
        # Subscriber: laser scan ← /scan
        # ------------------------------------------------------------------
        self.scan_sub = self.create_subscription(
            LaserScan,
            '/scan',
            self.scan_callback,
            10
        )

        self.get_logger().info(
            f'[ObstacleAvoider] Node started.\n'
            f'  front_threshold : {self.front_threshold} m\n'
            f'  forward_speed   : {self.forward_speed} m/s\n'
            f'  turn_speed      : {self.turn_speed} rad/s'
        )

    # ------------------------------------------------------------------
    # LaserScan callback — called every time a new scan arrives
    # ------------------------------------------------------------------
    def scan_callback(self, msg: LaserScan):
        """
        Core decision loop, executed on every incoming /scan message.

        1. Extract minimum distances for front, left, and right sectors.
        2. If front is blocked → compute the more open side and turn there.
        3. Otherwise → drive straight ahead.
        """
        ranges = list(msg.ranges)

        # Guard: empty or malformed scan
        if not ranges:
            self.get_logger().warn('[ObstacleAvoider] Received empty scan — skipping.')
            return

        # ------------------------------------------------------------------
        # Sector extraction
        #   Front : 0°  ± 30°  (cone directly ahead)
        #   Left  : 90° ± 20°  (left side)
        #   Right : 270°± 20°  (right side, i.e. -90° normalised)
        # ------------------------------------------------------------------
        front_readings = get_sector_ranges(ranges, center_deg=0.0,   half_width_deg=30.0)
        left_readings  = get_sector_ranges(ranges, center_deg=90.0,  half_width_deg=20.0)
        right_readings = get_sector_ranges(ranges, center_deg=270.0, half_width_deg=20.0)

        front_dist = safe_min(front_readings)
        left_dist  = safe_min(left_readings)
        right_dist = safe_min(right_readings)

        # ------------------------------------------------------------------
        # Build the Twist command
        # ------------------------------------------------------------------
        cmd = Twist()

        if front_dist < self.front_threshold:
            # ---- OBSTACLE AHEAD — choose the more open side ----
            cmd.linear.x = 0.0   # stop forward motion while turning

            if left_dist >= right_dist:
                # Left is more open → turn left (positive angular z)
                cmd.angular.z = self.turn_speed
                direction = 'LEFT '
            else:
                # Right is more open → turn right (negative angular z)
                cmd.angular.z = -self.turn_speed
                direction = 'RIGHT'

            self.get_logger().info(
                f'[BLOCKED] front={front_dist:.2f}m  '
                f'left={left_dist:.2f}m  right={right_dist:.2f}m  '
                f'→ Turning {direction}'
            )
        else:
            # ---- PATH CLEAR — move forward ----
            cmd.linear.x  = self.forward_speed
            cmd.angular.z = 0.0

            self.get_logger().info(
                f'[CLEAR  ] front={front_dist:.2f}m  '
                f'left={left_dist:.2f}m  right={right_dist:.2f}m  '
                f'→ Moving forward'
            )

        # Publish the command
        self.cmd_pub.publish(cmd)


# ---------------------------------------------------------------------------
# Entry point
# ---------------------------------------------------------------------------

def main(args=None):
    rclpy.init(args=args)
    node = ObstacleAvoider()
    try:
        rclpy.spin(node)
    except KeyboardInterrupt:
        node.get_logger().info('[ObstacleAvoider] Shutting down (KeyboardInterrupt).')
    finally:
        # Send a stop command before exiting so the robot doesn't keep moving
        stop_cmd = Twist()
        node.cmd_pub.publish(stop_cmd)
        node.destroy_node()
        rclpy.shutdown()


if __name__ == '__main__':
    main()
