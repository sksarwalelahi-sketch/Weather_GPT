import xarray as xr

from app.era5.normalizer import ERA5Normalizer


def main():
    instant = xr.open_dataset(
        "data/era5_test/data_stream-oper_stepType-instant.nc",
        engine="netcdf4",
    )

    accum = xr.open_dataset(
        "data/era5_test/data_stream-oper_stepType-accum.nc",
        engine="netcdf4",
    )

    # Combine the instant and accumulated variables.
    dataset = xr.merge([instant, accum])

    result = ERA5Normalizer.normalize_point(
        dataset,
        latitude=20.2961,
        longitude=85.8245,
    )

    print("REAL ERA5 NORMALIZED RESULT:")
    print(result)

    instant.close()
    accum.close()


if __name__ == "__main__":
    main()