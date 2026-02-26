# Automated BACnet Commissioning & Testing Framework

![Python](https://img.shields.io/badge/Python-3.13+-blue.svg)
![Protocol](https://img.shields.io/badge/Protocol-BACnet%2FIP-green.svg)
![Library](https://img.shields.io/badge/Library-BAC0-orange.svg)

## 📌 Project Overview
This repository contains an asynchronous Python-based automation framework designed for testing and commissioning Building Management System (BMS) and Data Center HVAC edge devices. 

By leveraging the `BAC0` library and `asyncio`, this script replaces traditional manual point-to-point testing (via UI/mouse clicks) with programmatic, scalable protocol validation. It demonstrates how to interact with industrial controllers at the network layer, specifically focusing on hardware override mechanisms and state injection.

## 🚀 Key Features & Validation Methodology
Coming from a strict system-level validation background, this tool treats physical MEP (Mechanical, Electrical, and Plumbing) hardware as the "Device Under Test" (DUT):
- **Asynchronous Polling:** Utilizes Python's `asyncio` event loop to handle non-blocking network requests, a critical architecture for polling thousands of IO points in a large-scale Data Center.
- **Automated Data Retrieval (ReadProperty):** Programmatically reads real-time sensor data (e.g., `Analog Input` for indoor temperature).
- **Hardware Decoupling / Force Override:** Implements the BACnet `Out_of_Service` property to safely decouple control logic from physical sensors—equivalent to injecting a "Force" command in hardware simulation.
- **Test Vector Injection (WriteProperty):** Automates the injection of edge-case setpoints (e.g., `Analog Value` Setpoint) to trigger and verify the controller's internal HVAC response loops.

## 🛠️ Technology Stack
- **Language:** Python 3.13
- **BMS Protocol Engine:** [BAC0](https://bac0.readthedocs.io/en/latest/) (built on `bacpypes3`)
- **Simulation Environment:** [Yabe (Yet Another BACnet Explorer)](https://sourceforge.net/projects/yetanotherbacnetexplorer/) & BACnet Room Simulator for local DUT emulation.

## ⚙️ Prerequisites & Setup
1. Clone the repository:
   ```bash
   git clone <your-github-repo-url>
   cd <your-repo-folder>
