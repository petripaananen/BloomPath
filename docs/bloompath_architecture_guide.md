# 🌸 BloomPath: Architecture & Workflow Guide

Welcome to **BloomPath**! This document explains how the system works in simple terms. Think of BloomPath as a "living bridge" that turns your boring project to-do lists into a beautiful, growing 3D garden.

Below is the breakdown of the diverse software roles shown in our workflow diagram. We will follow a single example: **"Build a stone bridge over the river"**.

![Workflow Diagram](./images/bloompath_workflow_diagram.png)

---

## 1. Project Lifecycle: From Seed to Structure
Your project board isn't just a list; it's the timeline of growth in the garden. Here is how each column interacts with the automated system:

| Column | Role in Garden (Unreal Engine 5) | What Happens? |
| :--- | :--- | :--- |
| **Backlog / To Do** | **The Seeds** | Issues here exist as dormant seeds or faint blueprints on the ground. They are potential energy waiting to be used. |
| **In Progress** | **The Growth** | **Action Trigger**: Moving here wakes up the **Python Middleware**. The **Architect (Marble AI)** begins generating the 3D model (the bridge). You might see scaffolding or growing vines in the garden. |
| **In Review** | **The Inspection** | **The Playtester (Genie 3)** runs its simulation. If the bridge is walkable, it glows with stability. If it's broken, it might look ghostly or unstable (Validation Pass). |
| **Done** | **The Bloom** | **Final State**: The bridge solidifies into permanent stone. It is now a functional part of the world that you can walk on. |

---

## 2. The Coordinator: Python Middleware
**Role: The "Gardener"**

This is the hidden brain of the operation. It connects your project management tool to the AI world.
- **What it does**: It watches the columns. When "FEATURE-101" moves to **In Progress**, it shouts, "Start building!"
- **Workflow**: "Okay, the user is working on a **stone bridge**. Creative Team, I need a visualization *now*."

## 3. The AI Creative Team (Synthesis & Validation)
This is a loop where three different AIs work together to build and check your reward.

### A. World Labs (Marble AI)
**Role: The "Architect"**
- **Job**: It takes the text "Stone Bridge" and imagines a 3D structure.
- **Example Action**: It creates the actual 3D geometry of a sturdy, arched stone bridge.

### B. Google Genie 3
**Role: The "Playtester"**
- **Job**: Before showing you the bridge, Genie 3 jumps *into* the 3D model and acts like a player.
- **Example Action**: It runs a simulation: "Can I walk from one side to the other without falling through the floor?"
- **Verdict**: If the bridge has a gap, Genie 3 reports a failure.

### C. Google Gemini 3
**Role: The "Inspector"**
- **Job**: Gemini 3 watches Genie 3 play and analyzes the visual style.
- **Example Action**: It looks at the bridge and tags it: *"Material: Stone", "Style: Ancient", "Function: Walkable"*. It writes a **Manifest** (a digital shipping label) so the garden knows exactly what is arriving.

## 4. The Destination: Unreal Engine 5
**Role: The "Garden"**

This is what you see on your screen. It is a high-quality 3D video game engine.
- **Experience**: You walk around and watch your work come to life.
- **Feedback**: The state of the garden tells you the health of the project. A garden full of ghosts means lots of work is "In Review" or failing tests. A garden of stone bridges means lots of work is "Done".
