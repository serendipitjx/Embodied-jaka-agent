# Embodied-JAKA-Agent

This project was developed for a robotics competition organised by Shanghai Jiao Tong University Shuzi Shanhai club and we won the Second Prize. It features an autonomous pakage delivery system that uses JAKA Lumi, it can be evoked by identifying user's orders by deploying Large Language Model (LLM).

## Core Functions

- **LLM-Based Control**: Uses DeepSeek-V3  to process voice commands and automatically trigger specific tool functions.
- **Automated Workflow**: Implements a complete loop: Voice Wake-up -> QR Code Task Retrieval -> Target Navigation -> Fixed-point Grasping -> Delivery.
- **Hardware Coordination**: Connects multiple modules including audio, camera, mobile base, and the robotic arm.

## Project Structure

- `demo/`: Contains the main entry in `main.py` and the task logic,the tools needed when the robot is moving in `mission.py`.
- `config/`: Stores API configurations and the LLM tool definitions (`tools.json`).
- `utils/`: Individual modules for the LLM Agent, arm control, navigation, QR scanning, and audio processing.

## Implementation Details

The project utilizes the baseline hardware SDK wrappers provided by the robotics club. My primary work focused on connecting these modules and implementing the logic required for the competition:

1. **Physical Coordinate Collection**: Performed manual teaching of the robot arm's grasping positions and calibrated the navigation markers on the map to match the physical competition field. This ensured that the movements and grasping were accurate in a real-world environment.
   
**Notion**:If you want to let the robot move to target place,you need to label the points in the map.You can get the map by controlling the robot manually. 

2. **Module Integration & Debugging**: Wrote code to link the separate modules (speech, vision, navigation, and arm control) and resolved logic conflicts when multiple hardware components were running simultaneously.
  
3. **Mission Logic Development**: Designed and implemented the full automation code that allowed the robot to autonomously identify tasks, navigate to pickup locations, and deliver items to target points.

## Notes

- This repository is for recording experiences and portfolio demonstration.
- Running the code requires a JAKA Lumi.
- Sensitive information (like API Keys) is hidden via `.gitignore`. You need to configure your own `.env` file based on the provided example.
