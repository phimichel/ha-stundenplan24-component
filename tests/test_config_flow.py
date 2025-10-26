"""Test the Stundenplan24 config flow."""
import pytest
from unittest.mock import patch, AsyncMock, MagicMock
from homeassistant import config_entries, data_entry_flow
import aiohttp

from custom_components.stundenplan24.const import DOMAIN, CONF_FORM
from custom_components.stundenplan24.config_flow import CannotConnect, InvalidAuth


async def test_form_initial(hass):
    """Test we get the form."""
    result = await hass.config_entries.flow.async_init(
        DOMAIN, context={"source": config_entries.SOURCE_USER}
    )
    assert result["type"] == data_entry_flow.FlowResultType.FORM
    assert result["errors"] == {}


async def test_form_with_mobil_clients(hass, mock_hosting, mock_indiware_mobil_plan):
    """Test config flow with two-step form selection."""
    result = await hass.config_entries.flow.async_init(
        DOMAIN, context={"source": config_entries.SOURCE_USER}
    )
    assert result["type"] == data_entry_flow.FlowResultType.FORM
    assert result["errors"] == {}

    # Sample XML with forms
    sample_xml = """<?xml version="1.0" encoding="UTF-8"?>
<VpMobil>
    <Kopf>
        <planart>Klasse</planart>
        <zeitstempel>25.01.2025, 08:00</zeitstempel>
        <DatumPlan>Samstag, 25. Januar 2025</DatumPlan>
        <datei>PlanKl20250125.xml</datei>
        <woche>4</woche>
    </Kopf>
    <Klassen>
        <Kl>
            <Kurz>5a</Kurz>
            <KlStunden>
                <KlSt ZeitVon="08:00" ZeitBis="08:45">1</KlSt>
            </KlStunden>
            <Pl></Pl>
        </Kl>
        <Kl>
            <Kurz>5b</Kurz>
            <KlStunden>
                <KlSt ZeitVon="08:00" ZeitBis="08:45">1</KlSt>
            </KlStunden>
            <Pl></Pl>
        </Kl>
    </Klassen>
</VpMobil>"""

    # Mock client for both validation and form fetching
    with patch(
        "custom_components.stundenplan24.config_flow.IndiwareStundenplanerClient"
    ) as mock_client, patch(
        "custom_components.stundenplan24.config_flow.Hosting"
    ) as mock_hosting_cls:
        # Mock Hosting.deserialize
        mock_hosting_instance = MagicMock()
        mock_hosting_cls.deserialize.return_value = mock_hosting_instance

        # Create mock response object with content attribute
        mock_response = MagicMock()
        mock_response.content = sample_xml

        mock_mobil = AsyncMock()
        mock_mobil.fetch_dates = AsyncMock(return_value={"PlanKl20250125.xml": "2025-01-25"})
        mock_mobil.fetch_plan = AsyncMock(return_value=mock_response)

        client_instance = mock_client.return_value
        client_instance.form_plan_client = mock_mobil
        client_instance.indiware_mobil_clients = filter(lambda x: x is not None, [mock_mobil])
        client_instance.substitution_plan_clients = filter(lambda x: x is not None, [])
        client_instance.close = AsyncMock()

        # Step 1: Enter credentials
        result2 = await hass.config_entries.flow.async_configure(
            result["flow_id"],
            {
                "school_url": "https://test.stundenplan24.de",
                "username": "testuser",
                "password": "testpass",
            },
        )

        # Should now show form selection step
        assert result2["type"] == data_entry_flow.FlowResultType.FORM
        assert result2["step_id"] == "select_form"

        # Step 2: Select form
        result3 = await hass.config_entries.flow.async_configure(
            result2["flow_id"],
            {CONF_FORM: "5a"},
        )

        assert result3["type"] == data_entry_flow.FlowResultType.CREATE_ENTRY
        assert result3["title"] == "https://test.stundenplan24.de - 5a"
        assert result3["data"] == {
            "school_url": "https://test.stundenplan24.de",
            "username": "testuser",
            "password": "testpass",
            "form": "5a",
        }


async def test_form_with_substitution_clients(hass, mock_indiware_client_with_substitution, mock_hosting):
    """Test config flow with substitution clients only (no form selection needed)."""
    result = await hass.config_entries.flow.async_init(
        DOMAIN, context={"source": config_entries.SOURCE_USER}
    )

    result2 = await hass.config_entries.flow.async_configure(
        result["flow_id"],
        {
            "school_url": "https://test.stundenplan24.de",
            "username": "testuser",
            "password": "testpass",
        },
    )

    # When only substitution clients available, skip form selection
    assert result2["type"] == data_entry_flow.FlowResultType.CREATE_ENTRY
    assert result2["title"] == "https://test.stundenplan24.de"
    assert result2["data"] == {
        "school_url": "https://test.stundenplan24.de",
        "username": "testuser",
        "password": "testpass",
    }

    # Verify that the client was properly closed (may be called multiple times during setup)
    assert mock_indiware_client_with_substitution.return_value.close.called


async def test_form_no_clients_available(hass, mock_indiware_client_empty, mock_hosting):
    """Test we show error when no clients are available."""
    result = await hass.config_entries.flow.async_init(
        DOMAIN, context={"source": config_entries.SOURCE_USER}
    )

    result2 = await hass.config_entries.flow.async_configure(
        result["flow_id"],
        {
            "school_url": "https://test.stundenplan24.de",
            "username": "testuser",
            "password": "testpass",
        },
    )

    assert result2["type"] == data_entry_flow.FlowResultType.FORM
    assert result2["errors"] == {"base": "cannot_connect"}


async def test_form_invalid_auth(hass, mock_hosting):
    """Test we handle invalid auth."""
    result = await hass.config_entries.flow.async_init(
        DOMAIN, context={"source": config_entries.SOURCE_USER}
    )

    with patch(
        "custom_components.stundenplan24.config_flow.IndiwareStundenplanerClient"
    ) as mock_client:
        # Setup mock to raise ClientResponseError with 401
        mock_mobil = AsyncMock()
        mock_mobil.fetch_dates.side_effect = aiohttp.ClientResponseError(
            request_info=None,
            history=None,
            status=401,
        )

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

        result2 = await hass.config_entries.flow.async_configure(
            result["flow_id"],
            {
                "school_url": "https://test.stundenplan24.de",
                "username": "testuser",
                "password": "wrongpass",
            },
        )

    assert result2["type"] == data_entry_flow.FlowResultType.FORM
    assert result2["errors"] == {"base": "invalid_auth"}


async def test_form_cannot_connect(hass, mock_hosting):
    """Test we handle cannot connect error."""
    result = await hass.config_entries.flow.async_init(
        DOMAIN, context={"source": config_entries.SOURCE_USER}
    )

    with patch(
        "custom_components.stundenplan24.config_flow.IndiwareStundenplanerClient"
    ) as mock_client:
        # Setup mock to raise ClientError
        mock_mobil = AsyncMock()
        mock_mobil.fetch_dates.side_effect = aiohttp.ClientError("Connection timeout")

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

        result2 = await hass.config_entries.flow.async_configure(
            result["flow_id"],
            {
                "school_url": "https://test.stundenplan24.de",
                "username": "testuser",
                "password": "testpass",
            },
        )

    assert result2["type"] == data_entry_flow.FlowResultType.FORM
    assert result2["errors"] == {"base": "cannot_connect"}


async def test_form_unexpected_exception(hass, mock_hosting):
    """Test we handle unexpected exceptions."""
    result = await hass.config_entries.flow.async_init(
        DOMAIN, context={"source": config_entries.SOURCE_USER}
    )

    with patch(
        "custom_components.stundenplan24.config_flow.IndiwareStundenplanerClient"
    ) as mock_client:
        # Setup mock to raise unexpected exception
        mock_mobil = AsyncMock()
        mock_mobil.fetch_dates.side_effect = Exception("Unexpected error")

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

        result2 = await hass.config_entries.flow.async_configure(
            result["flow_id"],
            {
                "school_url": "https://test.stundenplan24.de",
                "username": "testuser",
                "password": "testpass",
            },
        )

    assert result2["type"] == data_entry_flow.FlowResultType.FORM
    assert result2["errors"] == {"base": "cannot_connect"}


# Options Flow Tests

async def test_options_flow_init(hass, mock_config_entry):
    """Test options flow shows subject selection."""
    mock_config_entry.add_to_hass(hass)

    # Mock XML response with subjects in Unterricht block
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
      <KlStunden />
      <Kurse />
      <Unterricht>
        <Ue>
          <UeNr UeFa="Ma" UeLe="Müller">1</UeNr>
        </Ue>
        <Ue>
          <UeNr UeFa="De" UeLe="Schmidt">2</UeNr>
        </Ue>
        <Ue>
          <UeNr UeFa="En" UeLe="Meyer">3</UeNr>
        </Ue>
        <Ue>
          <UeNr UeFa="Sp" UeLe="Weber">4</UeNr>
        </Ue>
      </Unterricht>
      <Pl />
      <Klausuren />
      <Aufsichten />
    </Kl>
  </Klassen>
  <ZusatzInfo />
</VpMobil>"""

    with patch(
        "custom_components.stundenplan24.config_flow.IndiwareStundenplanerClient"
    ) as mock_client:
        # Setup mock to return XML with subjects
        mock_form_client = AsyncMock()
        mock_form_client.fetch_plan = AsyncMock()
        mock_form_client.fetch_plan.return_value = MagicMock(content=xml_content)

        client_instance = mock_client.return_value
        client_instance.form_plan_client = mock_form_client
        client_instance.close = AsyncMock()

        result = await hass.config_entries.options.async_init(mock_config_entry.entry_id)

    assert result["type"] == data_entry_flow.FlowResultType.FORM
    assert result["step_id"] == "init"

    # Should show multi-select with all subjects
    schema_keys = list(result["data_schema"].schema.keys())
    assert len(schema_keys) == 1

    # Get the Optional wrapper and extract the actual selector
    subject_field = schema_keys[0]
    # When filter is not yet configured, all subjects should be pre-selected
    assert set(subject_field.description["suggested_value"]) == {"De", "En", "Ma", "Sp"}

    # The schema key itself contains the validator (multi_select)
    # We need to check the validator's options
    validator = result["data_schema"].schema[subject_field]

    # For cv.multi_select, the options are stored in the 'options' attribute
    assert hasattr(validator, 'options')
    assert set(validator.options.keys()) == {"De", "En", "Ma", "Sp"}


async def test_options_flow_preserves_existing_filter(hass, mock_config_entry):
    """Test that existing filter configuration is preserved when opening options."""
    # Set up entry with existing filter
    mock_config_entry.add_to_hass(hass)
    hass.config_entries.async_update_entry(
        mock_config_entry,
        options={"filter_subjects": ["Ma"]}  # Only Math pre-configured
    )

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
      <KlStunden />
      <Kurse />
      <Unterricht>
        <Ue>
          <UeNr UeFa="Ma" UeLe="Müller">1</UeNr>
        </Ue>
        <Ue>
          <UeNr UeFa="De" UeLe="Schmidt">2</UeNr>
        </Ue>
      </Unterricht>
      <Pl />
      <Klausuren />
      <Aufsichten />
    </Kl>
  </Klassen>
  <ZusatzInfo />
</VpMobil>"""

    with patch(
        "custom_components.stundenplan24.config_flow.IndiwareStundenplanerClient"
    ) as mock_client:
        mock_form_client = AsyncMock()
        mock_form_client.fetch_plan = AsyncMock()
        mock_form_client.fetch_plan.return_value = MagicMock(content=xml_content)

        client_instance = mock_client.return_value
        client_instance.form_plan_client = mock_form_client
        client_instance.close = AsyncMock()

        result = await hass.config_entries.options.async_init(mock_config_entry.entry_id)

    assert result["type"] == data_entry_flow.FlowResultType.FORM
    assert result["step_id"] == "init"

    # Should preserve existing filter (only "Ma")
    schema_keys = list(result["data_schema"].schema.keys())
    subject_field = schema_keys[0]
    assert subject_field.description["suggested_value"] == ["Ma"]


async def test_options_flow_save_filter(hass, mock_config_entry):
    """Test saving subject filter in options."""
    mock_config_entry.add_to_hass(hass)

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
      <KlStunden />
      <Kurse />
      <Unterricht>
        <Ue>
          <UeNr UeFa="Ma" UeLe="Müller">1</UeNr>
        </Ue>
        <Ue>
          <UeNr UeFa="De" UeLe="Schmidt">2</UeNr>
        </Ue>
      </Unterricht>
      <Pl />
      <Klausuren />
      <Aufsichten />
    </Kl>
  </Klassen>
  <ZusatzInfo />
</VpMobil>"""

    with patch(
        "custom_components.stundenplan24.config_flow.IndiwareStundenplanerClient"
    ) as mock_client:
        mock_form_client = AsyncMock()
        mock_form_client.fetch_plan = AsyncMock()
        mock_form_client.fetch_plan.return_value = MagicMock(content=xml_content)

        client_instance = mock_client.return_value
        client_instance.form_plan_client = mock_form_client
        client_instance.close = AsyncMock()

        result = await hass.config_entries.options.async_init(mock_config_entry.entry_id)

        # User selects only "Ma" and "De"
        result2 = await hass.config_entries.options.async_configure(
            result["flow_id"],
            user_input={"filter_subjects": ["Ma", "De"]}
        )

    assert result2["type"] == data_entry_flow.FlowResultType.CREATE_ENTRY
    assert result2["data"] == {"filter_subjects": ["Ma", "De"]}


async def test_options_flow_default_all_subjects(hass, mock_config_entry):
    """Test that by default all subjects are included (empty filter)."""
    mock_config_entry.add_to_hass(hass)

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
      <KlStunden />
      <Kurse />
      <Unterricht>
        <Ue>
          <UeNr UeFa="Ma" UeLe="Müller">1</UeNr>
        </Ue>
      </Unterricht>
      <Pl />
      <Klausuren />
      <Aufsichten />
    </Kl>
  </Klassen>
  <ZusatzInfo />
</VpMobil>"""

    with patch(
        "custom_components.stundenplan24.config_flow.IndiwareStundenplanerClient"
    ) as mock_client:
        mock_form_client = AsyncMock()
        mock_form_client.fetch_plan = AsyncMock()
        mock_form_client.fetch_plan.return_value = MagicMock(content=xml_content)

        client_instance = mock_client.return_value
        client_instance.form_plan_client = mock_form_client
        client_instance.close = AsyncMock()

        result = await hass.config_entries.options.async_init(mock_config_entry.entry_id)

        # User doesn't select anything (= all subjects)
        result2 = await hass.config_entries.options.async_configure(
            result["flow_id"],
            user_input={"filter_subjects": []}
        )

    assert result2["type"] == data_entry_flow.FlowResultType.CREATE_ENTRY
    assert result2["data"] == {"filter_subjects": []}


async def test_options_flow_no_form_client(hass, mock_config_entry):
    """Test options flow when no form client is available."""
    mock_config_entry.add_to_hass(hass)

    with patch(
        "custom_components.stundenplan24.config_flow.IndiwareStundenplanerClient"
    ) as mock_client:
        client_instance = mock_client.return_value
        client_instance.form_plan_client = None
        client_instance.close = AsyncMock()

        result = await hass.config_entries.options.async_init(mock_config_entry.entry_id)

    assert result["type"] == data_entry_flow.FlowResultType.FORM
    assert result["step_id"] == "init"

    # Should show empty options when no client available
    schema_keys = list(result["data_schema"].schema.keys())
    assert len(schema_keys) == 1

    subject_field = schema_keys[0]
    validator = result["data_schema"].schema[subject_field]
    assert len(validator.options) == 0


async def test_options_flow_connection_error(hass, mock_config_entry):
    """Test options flow handles connection errors gracefully."""
    mock_config_entry.add_to_hass(hass)

    with patch(
        "custom_components.stundenplan24.config_flow.IndiwareStundenplanerClient"
    ) as mock_client:
        mock_form_client = AsyncMock()
        mock_form_client.fetch_plan = AsyncMock()
        mock_form_client.fetch_plan.side_effect = Exception("Connection failed")

        client_instance = mock_client.return_value
        client_instance.form_plan_client = mock_form_client
        client_instance.close = AsyncMock()

        result = await hass.config_entries.options.async_init(mock_config_entry.entry_id)

    assert result["type"] == data_entry_flow.FlowResultType.FORM
    assert result["step_id"] == "init"

    # Should show empty options on error
    schema_keys = list(result["data_schema"].schema.keys())
    subject_field = schema_keys[0]
    validator = result["data_schema"].schema[subject_field]
    assert len(validator.options) == 0
