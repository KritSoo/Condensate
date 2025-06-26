# Condensate - Conductivity Data Logger

A Python application for logging and visualizing conductivity meter data. Supports multiple conductivity meter models including HACH Sension7, Oakton CON150, and Milwaukee MW301.

## Features

- Real-time conductivity data display and logging
- Historical data visualization with charts
- Multiple device support through adapter system
- Configuration settings with persistent storage
- CSV data export and backup options
- Mock data generation for testing without physical devices

## Installation

1. Clone or download this repository
2. Install dependencies:

```
pip install -r requirements.txt
```

## Usage

Run the application:

```
python main.py
```

## Configuration

The application stores settings in:
- Windows: `%APPDATA%\Condensate\settings.ini`
- macOS: `~/Library/Application Support/Condensate/settings.ini`
- Linux: `~/.config/condensate/settings.ini`

Data logs are stored in a `logs` subdirectory of the application directory by default, but can be configured in the settings.

## Troubleshooting File Access Issues

If you encounter file access or permission issues:

1. Open the Settings menu in the application
2. In the "การบันทึกข้อมูล" (Logging) tab:
   - Click "ตรวจสอบสิทธิ์" (Check permissions) to see detailed information
   - Use "ทดสอบการบันทึกไฟล์" (Test file writing) to verify write access
   - Change the log directory to a location with proper write permissions

If issues persist, the application will attempt to use fallback locations:
- User's home directory
- System temporary directory

## Supported Devices

- HACH Sension7 Conductivity Meter
- Oakton CON150 Conductivity Meter
- Milwaukee MW301 Conductivity Meter

## License

This software is released under the MIT License.
