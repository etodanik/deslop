# tidepool

A command-line tool that downloads NOAA tide predictions for a station ID and prints the next high and low tides.

`tidepool` fetches predictions from the NOAA Tides & Currents API for the station ID you give it. It's handy for planning a fishing trip, a beach walk or a day on the water.

## Installation

With pip:

```bash
pip install tidepool
```

From source:

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

Open an issue or submit a pull request.
