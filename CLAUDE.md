# CLAUDE.md

This file provides guidance to Claude Code (claude.ai/code) when working with code in this repository.

## Project Overview

GameMacroAssistant is a desktop automation tool for PC games that allows users to record, edit, and replay mouse/keyboard operations. The tool uses visual recognition to match screen conditions before executing actions.

## Core Architecture

Based on the requirements document, this application should implement:

### Recording System
- Global input capture for mouse and keyboard operations
- Screen capture with native resolution support and GDI fallback
- ESC key termination for recording sessions
- Error handling for capture failures (logs `Err-CAP` codes)

### Visual Editor
- Block-based macro representation with drag-and-drop reordering
- Image editing for condition screenshots (double-click to edit, rectangular selection)
- Undo/redo support (Ctrl+Z)

### Execution Engine  
- Global hotkey triggering (e.g., Ctrl+Shift+F10)
- Image matching for conditional execution
- Timeout handling with notification system (logs `Err-TMO` codes)
- Progress indication in system tray

### File Management
- Encrypted `.gma.json` file format with password protection (8+ characters)
- Three-attempt password validation with error feedback

## Key Technical Requirements

- **Screen Capture**: Must handle fullscreen games with fallback to GDI when native capture fails
- **Visual Recognition**: Image matching between stored conditions and current screen state
- **Global Hooks**: System-wide input capture and hotkey registration
- **Encryption**: Secure storage of macro files with password protection
- **Error Logging**: Comprehensive logging with specific error codes (Err-CAP, Err-TMO)
- **UI Framework**: Visual editor supporting drag-and-drop, image editing, and block manipulation

## Development Notes

- The project currently contains only requirements documentation
- Implementation should focus on defensive automation (game assistance) rather than exploitative automation
- Error handling and user feedback are critical given the real-time nature of game automation
- Consider cross-platform compatibility for screen capture methods