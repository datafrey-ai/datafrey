from datafrey_api import DatabaseStatus, Provider


class TestProvider:
    def test_values(self):
        assert Provider.snowflake == "snowflake"
        assert len(Provider) == 1

    def test_value_access(self):
        assert Provider.snowflake.value == "snowflake"

    def test_from_value(self):
        assert Provider("snowflake") is Provider.snowflake


class TestDatabaseStatus:
    def test_values(self):
        assert DatabaseStatus.loading == "loading"
        assert DatabaseStatus.connected == "connected"
        assert DatabaseStatus.disconnected == "disconnected"
        assert DatabaseStatus.error == "error"
        assert len(DatabaseStatus) == 4
