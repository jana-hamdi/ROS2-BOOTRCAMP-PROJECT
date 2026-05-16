#!/usr/bin/env python3
"""
run_avoider.py
==============
Convenience script to build the workspace and run the obstacle_avoider node.

Run from the ros2_ws root:
    python3 src/obstacle_avoider/scripts/run_avoider.py

Or make it executable and run directly:
    chmod +x src/obstacle_avoider/scripts/run_avoider.py
    ./src/obstacle_avoider/scripts/run_avoider.py
"""

import subprocess
import sys
import os


# ---------------------------------------------------------------------------
# Helpers
# ---------------------------------------------------------------------------

def run(cmd: str, check: bool = True) -> int:
    """Print and execute a shell command."""
    print(f'\n>>> {cmd}\n')
    result = subprocess.run(cmd, shell=True)
    if check and result.returncode != 0:
        print(f'[ERROR] Command failed with exit code {result.returncode}')
        sys.exit(result.returncode)
    return result.returncode


def workspace_root() -> str:
    """Return the ros2_ws directory (two levels above this script)."""
    script_dir = os.path.dirname(os.path.abspath(__file__))
    return os.path.abspath(os.path.join(script_dir, '..', '..', '..'))


# ---------------------------------------------------------------------------
# Main
# ---------------------------------------------------------------------------

def main():
    ws = workspace_root()
    print(f'Workspace root: {ws}')
    os.chdir(ws)

    # 1. Source ROS2 Humble (requires interactive shell — done via bash -i below)
    print('\n[1/3] Building with colcon ...')
    run('bash -c "source /opt/ros/humble/setup.bash && colcon build --packages-select obstacle_avoider"')

    print('\n[2/3] Sourcing install/setup.bash ...')
    print('      (This step is informational; sourcing is baked into the next command.)')

    print('\n[3/3] Running obstacle_avoider node ...')
    run(
        'bash -c "'
        'source /opt/ros/humble/setup.bash && '
        'source install/setup.bash && '
        'ros2 run obstacle_avoider avoider'
        '"'
    )


if __name__ == '__main__':
    main()
