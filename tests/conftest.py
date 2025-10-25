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


@pytest.fixture
def mock_indiware_mobil_plan():
    """Mock IndiwareMobilPlan with forms."""
    plan = MagicMock()

    # Mock form 5a
    form_5a = MagicMock()
    form_5a.short_name = "5a"
    form_5a.lessons = []
    form_5a.periods = {}

    # Mock form 10b
    form_10b = MagicMock()
    form_10b.short_name = "10b"
    form_10b.lessons = []
    form_10b.periods = {}

    plan.forms = [form_5a, form_10b]

    return plan


@pytest.fixture
def mock_timetable_with_lessons():
    """Mock IndiwareMobilPlan with actual lessons for calendar tests."""
    from datetime import time, date

    plan_response = MagicMock()

    # Create proper XML content
    xml_content = """<?xml version="1.0" encoding="UTF-8"?>
<VpMobil>
  <Kopf>
    <planart>1</planart>
    <zeitstempel>25.01.2025, 08:00</zeitstempel>
    <DatumPlan>Samstag, 25. Januar 2025</DatumPlan>
    <datei>PlanKl20250125.xml</datei>
    <woche>4</woche>
    <tageprowoche>5</tageprowoche>
  </Kopf>
  <Klassen>
    <Kl>
      <Kurz>5a</Kurz>
      <KlStunden>
        <KlSt ZeitVon="08:00" ZeitBis="08:45">1</KlSt>
        <KlSt ZeitVon="08:50" ZeitBis="09:35">2</KlSt>
        <KlSt ZeitVon="09:55" ZeitBis="10:40">3</KlSt>
        <KlSt ZeitVon="10:45" ZeitBis="11:30">4</KlSt>
      </KlStunden>
      <Kurse />
      <Unterricht />
      <Pl>
        <Std>
          <St>1</St>
          <Beginn>08:00</Beginn>
          <Ende>08:45</Ende>
          <Fa FaAe="">Ma</Fa>
          <Le LeAe="">Müller</Le>
          <Ra RaAe="">101</Ra>
          <If></If>
        </Std>
        <Std>
          <St>2</St>
          <Beginn>08:50</Beginn>
          <Ende>09:35</Ende>
          <Fa FaAe="">De</Fa>
          <Le LeAe="">Schmidt</Le>
          <Ra RaAe="">102</Ra>
          <If></If>
        </Std>
        <Std>
          <St>3</St>
          <Beginn>09:55</Beginn>
          <Ende>10:40</Ende>
          <Fa FaAe="">En</Fa>
          <Le LeAe="">Meyer</Le>
          <Ra RaAe="">103</Ra>
          <If></If>
        </Std>
        <Std>
          <St>4</St>
          <Beginn>10:45</Beginn>
          <Ende>11:30</Ende>
          <Fa FaAe="">Sp</Fa>
          <Le LeAe="">Weber</Le>
          <Ra RaAe="">Turnhalle</Ra>
          <If></If>
        </Std>
      </Pl>
      <Klausuren />
      <Aufsichten />
    </Kl>
  </Klassen>
  <ZusatzInfo />
</VpMobil>"""

    plan_response.content = xml_content
    return plan_response
