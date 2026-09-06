
import pytest

from app.gfs.client import GFSClient

def test_build_url_contains_cycle_and_file():
    url = GFSClient.build_url(
        date="20260830",
        cycle=6,
        forecast_hour=0,
        file_name="gfs.t06z.pgrb2.0p25.anl",
    )

    assert "dir=%2Fgfs.20260830%2F06%2Fatmos" in url
    assert "file=gfs.t06z.pgrb2.0p25.anl" in url


def test_build_url_default_file():
    url = GFSClient.build_url(
        date="20260830",
        cycle=0,
        forecast_hour=0,
    )

    assert "file=gfs.t00z.pgrb2.0p25.f000" in url


def test_build_url_rejects_invalid_date():
    try:
        GFSClient.build_url(
            date="2026083",
            cycle=6,
            forecast_hour=0,
        )
    except ValueError:
        pass
    else:
        raise AssertionError("Expected ValueError")


def test_build_url_rejects_invalid_cycle():
    try:
        GFSClient.build_url(
            date="20260830",
            cycle=3,
            forecast_hour=0,
        )
    except ValueError:
        pass
    else:
        raise AssertionError("Expected ValueError")


def test_build_url_rejects_invalid_forecast_hour():
    try:
        GFSClient.build_url(
            date="20260830",
            cycle=6,
            forecast_hour=385,
        )
    except ValueError:
        pass
    else:
        raise AssertionError("Expected ValueError")

@pytest.mark.asyncio
async def test_download_grib2(tmp_path):
    class FakeResponse:
        def raise_for_status(self):
            pass

        async def __aenter__(self):
            return self

        async def __aexit__(self, exc_type, exc, tb):
            pass

        async def aiter_bytes(self, chunk_size=1024 * 1024):
            yield b"GRIB"
            yield b"TEST"

    class FakeClient:
        def stream(self, method, url):
            return FakeResponse()

    client = GFSClient()
    await client.close()

    client.client = FakeClient()

    output = tmp_path / "test.grib2"

    result = await client.download_grib2(
        url="https://example.com/test.grib2",
        output_path=output,
    )

    assert result == output
    assert output.exists()
    assert output.read_bytes() == b"GRIBTEST"
def test_build_url_supports_filter_parameters():
    url = GFSClient.build_url(
        date="20260830",
        cycle=6,
        forecast_hour=0,
        file_name="gfs.t06z.pgrb2.0p25.anl",
        variables=["TMP", "RH"],
        levels=["2_m_above_ground"],
        top_latitude=20.5,
        left_longitude=85.5,
        right_longitude=86.1,
        bottom_latitude=20.0,
    )

    assert "var_TMP=on" in url
    assert "var_RH=on" in url
    assert "lev_2_m_above_ground=on" in url

    assert "toplat=20.5" in url
    assert "leftlon=85.5" in url
    assert "rightlon=86.1" in url
    assert "bottomlat=20.0" in url