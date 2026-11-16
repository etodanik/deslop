# tidepool

🌊 A simple command-line tool that downloads NOAA tide predictions for a station and tells you when the next high and low tides are.

## Overview

`tidepool` fetches tide prediction data from the NOAA Tides & Currents API for any station ID you provide and prints the next high and low tides in a clean, easy-to-read format. Whether you're planning a fishing trip, a beach walk, or a day on the water, `tidepool` gets you the information you need in seconds.

## Installation

### Using pip

```bash
pip install tidepool
```

### From source

```bash
git clone https://github.com/your-username/tidepool.git
cd tidepool
pip install .
```

## Usage

Run `tidepool` with a NOAA station ID:

```bash
tidepool 9414290
```

Example output:

```
Station: 9414290 (San Francisco, CA)

Next high tide: Tue 06:42 AM  (5.8 ft)
Next low tide:  Tue 12:55 PM  (0.9 ft)
```

You can find station IDs on the [NOAA Tides & Currents website](https://tidesandcurrents.noaa.gov/).

## Contributing

Contributions are welcome! Feel free to open an issue or submit a pull request.
