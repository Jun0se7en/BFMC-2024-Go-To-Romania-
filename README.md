# 🏎️ BFMC 2024 - Go To Romania

Welcome to the official repository for our **Autonomous Vehicle Project** developed for the **Bosch Future Mobility Challenge (BFMC) 2024**.  
Our mission: build a smart, self-driving car that can navigate complex environments, avoid obstacles, and complete missions — all autonomously!

## 🚗 Project Overview

This project contains the full software stack that powers our autonomous vehicle, including:

- **Perception**: Using computer vision to detect lanes, traffic signs, and dynamic objects.
- **Control**: Implementing real-time path following, speed control, and motion planning algorithms.
- **Localization**: Fusing sensor data (camera, encoder, IMU) for accurate position estimation.
- **Traffic Handling**: Task sequencing and decision-making logic for competition scenarios.

## ✅ **Demo Videos**

- 🚘 Demo: [Watch here](https://youtu.be/real-world-demo)

## 📦 Folder Structure

```bash

├── BFMC_2024/ # Provide Multithreading Code for Jetson TX2
│   ├── src/           # Lane detection, object tracking, etc. threads
│   ├── export/      # Export tools for YOLOv5 models
│   ├── lib/         # Contains lib for YOLOv5 models
│   ├── models/      # Contains pretrained YOLOv5 models for traffic signs detection
│   └── tools/                # Helper functions, constants, visualization tools
├── RasberryPi/   # Provide Multithreading Code for RasberryPi

