
# TwinYields Python library

## Configuration

Configuration is read from file: `~./twinyields/config.toml`. See template: `config/config.toml` 

## Usage

### Update data in MongoDB

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


