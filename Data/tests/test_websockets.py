import asyncio

import pytest

from app.api.websockets import LiveUpdateManager


@pytest.mark.asyncio
async def test_live_update_manager_publishes_to_subscribers():
    manager = LiveUpdateManager()
    queue = await manager.subscribe("alerts")

    await manager.publish(
        "alerts",
        {"id": "alert-1", "severity": "high"},
    )

    assert await asyncio.wait_for(queue.get(), timeout=1) == {
        "id": "alert-1",
        "severity": "high",
    }

    await manager.unsubscribe("alerts", queue)
    assert "alerts" not in manager._channels
