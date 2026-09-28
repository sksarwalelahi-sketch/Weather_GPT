# WeatherGPT Project Requirements

## Objective

Develop WeatherGPT as an AI-powered, multilingual conversational weather
intelligence platform integrating meteorological datasets, forecasting models,
and disaster-warning systems.

## Core requirements

- Real-time weather information retrieval
- Natural-language weather and forecast queries
- Location-based forecasting
- Extreme-weather alerts and early-warning dissemination
- Alert sources: NDMA SACHET, NOAA weather alerts, and Open-Meteo Flood API
- Scalable real-time data ingestion
- Contextual, accurate, and multilingual answers

## NWP requirement

Use:

- NOAA GFS
- ECMWF Open Data

During the initial implementation, access both models through Open-Meteo's
model APIs:

- `gfs_seamless`
- `ecmwf_ifs025`

Direct GRIB parsing is optional and must not be required for normal startup,
development, or evaluation. The optional direct GFS ingestion path can be used
later for advanced regional comparison and offline processing.

## Alert and warning source requirements

- **NDMA SACHET** is the preferred official Indian disaster-warning feed,
  activated through the All India RSS feed:
  `https://sachet.ndma.gov.in/cap_public_website/rss/rss_india.xml`.
- **NOAA/NWS active alerts** provide official weather warnings where NOAA
  coverage applies.
- **Open-Meteo Flood API** provides model-derived river-discharge outlooks.
  These must be displayed as non-official outlooks, never as government
  warnings.

## Expected outcomes

- Faster dissemination of weather information
- Better public access to forecasts
- Improved disaster preparedness and response

## Use cases

- Crop-weather advisories for farmers
- Aviation weather briefings
- Flood and cyclone warning dissemination
- Smart-city weather monitoring
- Climate analytics for researchers

## Evaluation parameters

- Accuracy and relevance
- Response latency
- Scalability and innovation
- Integration with real-time meteorological systems
