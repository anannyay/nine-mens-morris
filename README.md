# Nine Men's Morris

A Python implementation of the classic board game **Nine Men's Morris** with AI support.

## Features

- Play against another human or an AI opponent
- Three AI difficulty levels: Easy, Medium, Hard
- Interactive UI

## Installation

1. **Create and activate a virtual environment:**
   ```sh
   python -m venv env
   env\Scripts\activate
   ```

2. **Install dependencies:**
   ```sh
   pip install -r requirements.txt
   ```

## Usage

Run the game with:

```sh
python main.py
```

### Options

- `--ai` : Enable AI opponent
- `--ai-color {white,black}` : Choose AI color (default: black)
- `--difficulty {easy,medium,hard}` : Set AI difficulty (default: medium)

Example:

```sh
python main.py --ai --ai-color white --difficulty hard
``