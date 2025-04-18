# 🏎️ BFMC 2024 - Go To Romania

Welcome to the official repository for our **Autonomous Vehicle Project** developed for the **Battle of the Future Mobility Challenge (BFMC) 2024**.  
Our mission: build a smart, self-driving car that can navigate complex environments, avoid obstacles, and complete missions — all autonomously!

## 🚗 Project Overview

This project contains the full software stack that powers our autonomous vehicle, including:

- **Perception**: Using computer vision to detect lanes, traffic signs, and dynamic objects.
- **Control**: Implementing real-time path following, speed control, and motion planning algorithms.
- **Localization**: Fusing sensor data (camera, encoder, IMU) for accurate position estimation.
- **Communication**: ROS-based messaging infrastructure for efficient node-to-node data transfer.
- **Mission Handling**: Task sequencing and decision-making logic for competition scenarios.

## 📦 Folder Structure

```bash
├── src/
│   ├── perception/           # Lane detection, object tracking, etc.
│   ├── control/              # PID controllers, trajectory tracking
│   ├── localization/         # Sensor fusion, pose estimation
│   ├── mission_manager/      # High-level logic & finite state machine
│   └── utils/                # Helper functions, constants, visualization tools
├── launch/                   # ROS launch files
├── config/                   # Camera calibration, vehicle parameters
├── scripts/                  # Debugging, logging, and calibration tools
└── docs/                     # Technical documentation and figures
