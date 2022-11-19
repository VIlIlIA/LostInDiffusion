# Lost In Diffusion
Interactive artwork examining the relationship between human being and/or intelligence machine.

## Requirements
 - python 3.10
 - poetry package manager (https://python-poetry.org/)
 - CUDA Toolkit ^11.7
 - Powerful enough Nvidia GPU

## Installation and Running

### Setup
1. Run `poetry install`
2. Run `poetry run poe touch`
3. Run `poetry run poe accelerate` (optional)
4. Add your hugging face token to the .env file (same directory as main.py) as TOKEN

### Running
1. Run `uvicorn main:app --reload --host [your host]`