# Obstacle Avoider — ROS2 Humble

A lightweight, reactive obstacle-avoidance package for ROS2 Humble. The robot reads its laser scanner, figures out what's in front of it, and smoothly steers away from anything too close. No maps, no path planning — just pure sensor-to-motor reaction, which makes it a great starting point for understanding how ROS2 nodes communicate.

Tested with **TurtleBot3 Burger/Waffle** in **Gazebo** simulation on Ubuntu 22.04.

---

## How It Works

The node divides the 360° laser scan into three sectors and reads the closest obstacle in each:

```
         FRONT  (0° ± 30°)
              ↑
    LEFT ←   🤖   → RIGHT
  (90° ± 20°)     (270° ± 20°)
```

Every time a new scan arrives, the decision logic is:

1. **Front blocked?** (distance < `front_threshold`)
   - Compare left vs right distance
   - Turn toward the more open side
2. **Front clear?**
   - Drive straight ahead at `forward_speed`

NaN and Inf values from the sensor are silently ignored — the node always uses only valid, finite readings.

---

## Prerequisites

| Requirement | Version / Notes |
|---|---|
| Ubuntu | 22.04 LTS |
| ROS2 | Humble Hawksbill |
| Gazebo | Classic 11 (ships with `ros-humble-gazebo-ros-pkgs`) |
| TurtleBot3 | `ros-humble-turtlebot3` + `ros-humble-turtlebot3-simulations` |
| Python | 3.10+ (comes with Ubuntu 22.04) |

### Install TurtleBot3 packages (if not already installed)

```bash
sudo apt install ros-humble-turtlebot3 ros-humble-turtlebot3-simulations
echo "export TURTLEBOT3_MODEL=burger" >> ~/.bashrc
source ~/.bashrc
```

---


## Build

```bash
cd ~/ros2_ws
source /opt/ros/humble/setup.bash
colcon build --packages-select obstacle_avoider
source install/setup.bash
```

> **Tip:** Add `source ~/ros2_ws/install/setup.bash` to your `~/.bashrc` so you never forget to source after building.

---

## Run

You need two terminals.

### Terminal 1 — Gazebo simulation

```bash
source /opt/ros/humble/setup.bash
export TURTLEBOT3_MODEL=burger
ros2 launch turtlebot3_gazebo turtlebot3_world.launch.py
```

Wait for Gazebo to fully load before continuing.

### Terminal 2 — Obstacle avoider node

```bash
source /opt/ros/humble/setup.bash
source ~/ros2_ws/install/setup.bash
ros2 run obstacle_avoider avoider
```

Or use the launch file (supports parameter overrides):

```bash
ros2 launch obstacle_avoider avoider.launch.py
ros2 launch obstacle_avoider avoider.launch.py front_threshold:=0.4 forward_speed:=0.22
```

---

## Parameters

| Parameter | Type | Default | Description |
|---|---|---|---|
| `front_threshold` | float | `0.55` | Distance in **metres** below which the front sector is considered blocked |
| `forward_speed` | float | `0.18` | Linear velocity (m/s) when the path ahead is clear |
| `turn_speed` | float | `0.60` | Angular velocity (rad/s) when turning to avoid an obstacle |

### Override at runtime (without restarting)

```bash
ros2 param set /obstacle_avoider front_threshold 0.40
ros2 param set /obstacle_avoider forward_speed 0.25
ros2 param list /obstacle_avoider
```

---

## Log Output

While running you will see lines like:

```
[CLEAR  ] front=1.23m  left=0.87m  right=2.14m  → Moving forward
[BLOCKED] front=0.42m  left=1.10m  right=0.30m  → Turning LEFT
```

`CLEAR` = moving forward. `BLOCKED` = obstacle detected, turning toward the more open side.

---


## Troubleshooting

**`ros2 run obstacle_avoider avoider` — package not found**
→ Did you run `source install/setup.bash` after building? This is the most common mistake.

**Robot doesn't move / no `/cmd_vel` output**
→ Check that `/scan` is being published: `ros2 topic echo /scan`. If nothing appears, Gazebo may not have finished loading — wait a few seconds and try again.

**Robot spins forever and never goes forward**
→ The `front_threshold` might be too high. Try lowering it: `ros2 param set /obstacle_avoider front_threshold 0.30`

**All laser readings are `inf`**
→ The robot is in open space with nothing in range. This is normal — the node will drive forward. If it happens when surrounded by walls, your LIDAR range settings in the simulation may not match expectations.

**`ModuleNotFoundError: No module named 'obstacle_avoider'`**
→ Rebuild and re-source:
```bash
cd ~/ros2_ws
colcon build --packages-select obstacle_avoider
source install/setup.bash
```

**Gazebo crashes or is very slow**
→ Make sure hardware acceleration is enabled. For VMs, enable 3D acceleration in your hypervisor settings.

---

## License

MIT — do whatever you want with it, just don't blame me if the robot knocks something over.
