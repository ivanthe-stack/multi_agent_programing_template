# CLAUDE.md

This file provides guidance to Claude Code (claude.ai/code) when working with code in this repository.

## Project Overview

This is a multi-agent programming template repository focused on developing a multi-agent system with task management capabilities. The system is designed to be decentralized, where agents can communicate and coordinate tasks through documented protocols.

## Architecture

### Core Components

- **Communication System**: Agents communicate through structured markdown files with predefined message formats
- **Task Management**: Tasks are logged in `comunication.md` using a specific format with agent identifiers, timestamps, descriptions, and status tracking
- **Template System**: Uses template files (`comunication-template.md`, `GEMINI_template.md`) that can be edited to customize the system
- **Demo Interface**: Simple HTML/CSS/JS landing page in the `demo/` directory for demonstration purposes

### Agent Communication Protocol

Agents must follow these rules:
- Always include agent identifier in messages
- Log tasks in `comunication.md` using the specified format:
  ```
  <details>
  <summary>task</summary>
  
  **Agent:** Agent x
  **Timestamp:** YYYY-MM-DD
  **Description:** task description
  **Status:** In Progress|Done
  
  </details>
  ```
- Never delete or replace other agents' tasks
- Break tasks into small, manageable pieces
- Continue working until goal is finished and tested

### File Structure

- `comunication.md` - Active task log and communication records
- `comunication-template.md` - Template for communication structure
- `GEMINI.md` / `GEMINI_template.md` - Agent-specific documentation templates
- `start_prompt_*.md` - Initialization prompts for different agent types
- `demo/` - Web interface demonstration (HTML/CSS/JS)

## Development Guidelines

### Task Management
- Each agent should log tasks before implementation begins
- Tasks should be concise and focused on architecture/code updates
- Always update task status from "In Progress" to "Done" when completed
- Include file references in task descriptions

### Agent Coordination
- The system is fully decentralized - any agent can initiate tasks
- Agents process messages and forward information as needed
- Goal is specified in `<goal>` tags within `comunication.md`

### Current Goal
The active goal is to develop the multi-agent system and add a database for task management, specifically editing template files like `comunication-template.md` and `GEMINI_template.md`.

## No Build System
This repository contains no package.json, requirements.txt, or other dependency management files. Development is primarily template-based with static HTML/CSS/JS for demonstrations.