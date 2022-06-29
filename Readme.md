
# TwinYields Python library

## Install

```
git clone https://github.com/TwinYields/twinyields-python.git
cd twinyields-python
pip install -r requirements.txt --no-deps .
```

## Configuration

Configuration is read from file: `~./twinyields/config.toml`. See template: `config/config.toml` 

## Usage

### Command line

```bash
usage: twinyields [-h] [-i] [-s] [-e] [-r]

Control TwinYields digital twin

optional arguments:
  -h, --help            show this help message and exit
  -i, --init            Initialize the digital twin
  -s, --update-sensors  Fetch updated sensor data
  -e, --update-eo       Fetch updated satellite data
  -r, --run             Run the simulation model
```


### Python

#### Sentinel2 

```python
from twinyields.database import EOUpdater
eoup = EOUpdater()
eoup.update_field("RVIII")
```

#### SoilScouts

```python
from twinyields.database import SoilScoutUpdater
scu = SoilScoutUpdater()
scu.update()
```

#### Farmiaisti

Requires installing private `farmiaisti` package.

```python
from twinyields.database import FarmiaistiUpdater
fu = FarmiaistiUpdater()
fu.update()
```


