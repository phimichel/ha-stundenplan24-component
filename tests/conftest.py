"""Common fixtures for Stundenplan24 tests."""
import pytest
from unittest.mock import MagicMock, AsyncMock, patch
from pytest_homeassistant_custom_component.common import MockConfigEntry

from custom_components.stundenplan24.const import (
    DOMAIN,
    CONF_SCHOOL_URL,
    CONF_USERNAME,
    CONF_PASSWORD,
)


pytest_plugins = "pytest_homeassistant_custom_component"


@pytest.fixture(autouse=True)
def auto_enable_custom_integrations(enable_custom_integrations):
    """Enable custom integrations for all tests."""
    yield


@pytest.fixture
def mock_config_entry():
    """Return a mock config entry."""
    return MockConfigEntry(
        domain=DOMAIN,
        data={
            CONF_SCHOOL_URL: "https://test-schule.stundenplan24.de",
            CONF_USERNAME: "test_user",
            CONF_PASSWORD: "test_password",
        },
        unique_id="test_school",
    )


@pytest.fixture
def mock_indiware_client_with_mobil():
    """Mock IndiwareStundenplanerClient with mobil clients."""
    with patch(
        "custom_components.stundenplan24.config_flow.IndiwareStundenplanerClient"
    ) as mock_client:
        # Mock mobil client
        mock_mobil = MagicMock()
        mock_mobil.fetch_dates = AsyncMock(return_value={
            "PlanKl20250125.xml": "datetime object",
        })

        # Return filter object (wie in echter API)
        client_instance = mock_client.return_value
        client_instance.indiware_mobil_clients = filter(
            lambda x: x is not None,
            [mock_mobil]
        )
        client_instance.substitution_plan_clients = filter(
            lambda x: x is not None,
            []
        )
        client_instance.close = AsyncMock()

        yield mock_client


@pytest.fixture
def mock_indiware_client_with_substitution():
    """Mock IndiwareStundenplanerClient with substitution clients."""
    with patch(
        "custom_components.stundenplan24.config_flow.IndiwareStundenplanerClient"
    ) as mock_client:
        # Mock substitution client
        mock_subst = MagicMock()
        mock_subst.get_metadata = AsyncMock(return_value={"test": "data"})

        # Return filter object
        client_instance = mock_client.return_value
        client_instance.indiware_mobil_clients = filter(
            lambda x: x is not None,
            []
        )
        client_instance.substitution_plan_clients = filter(
            lambda x: x is not None,
            [mock_subst]
        )
        client_instance.close = AsyncMock()

        yield mock_client


@pytest.fixture
def mock_indiware_client_empty():
    """Mock IndiwareStundenplanerClient with no clients."""
    with patch(
        "custom_components.stundenplan24.config_flow.IndiwareStundenplanerClient"
    ) as mock_client:
        client_instance = mock_client.return_value
        client_instance.indiware_mobil_clients = filter(
            lambda x: x is not None,
            []
        )
        client_instance.substitution_plan_clients = filter(
            lambda x: x is not None,
            []
        )
        client_instance.close = AsyncMock()

        yield mock_client


@pytest.fixture
def mock_hosting():
    """Mock Hosting.deserialize."""
    with patch(
        "custom_components.stundenplan24.config_flow.Hosting"
    ) as mock_hosting_class:
        mock_hosting_instance = MagicMock()
        mock_hosting_class.deserialize.return_value = mock_hosting_instance
        yield mock_hosting_class
