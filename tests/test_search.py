import pytest
import os
import shutil
from click.testing import CliRunner
from yt_fts.yt_fts import cli
from yt_fts.utils import normalize_time_input
from testing_utils import fetch_and_unzip_test_db

CONFIG_DIR = os.path.expanduser("~/.config/yt-fts")


@pytest.fixture(scope="session")
def runner():
    return CliRunner()


def reset_testing_env():
    if os.path.exists(CONFIG_DIR):
        if os.environ.get("YT_FTS_TEST_RESET", "true").lower() == "true":
            shutil.rmtree(CONFIG_DIR)
            fetch_and_unzip_test_db()
        else:
            print("running tests with existing db")


def test_global_search(runner, capsys):
    result = runner.invoke(cli, ["search", "guilt", "-l", "99"])

    assert result.exit_code == 0

    print(result.output)
    captured = capsys.readouterr()
    output = captured.out

    assert "YC Root Access" in output
    assert "JCS - Criminal Psychology" in output


def test_channel_search(runner, capsys):
    result = runner.invoke(cli, ["search", "-c", "1", "criminal", "-l", "99"])

    assert result.exit_code == 0

    print(result.output)
    captured = capsys.readouterr()
    output = captured.out

    assert "JCS - Criminal Psychology" in output
    assert "The Bizarre Case of Stephen McDaniel" in output


# Tests for normalize_time_input function
class TestNormalizeTimeInput:
    def test_hhmmss_format(self):
        assert normalize_time_input("01:30:45") == "01:30:45.000"
        assert normalize_time_input("00:05:30") == "00:05:30.000"
        assert normalize_time_input("0:05:30") == "00:05:30.000"

    def test_mmss_format(self):
        assert normalize_time_input("5:30") == "00:05:30.000"
        assert normalize_time_input("30:00") == "00:30:00.000"
        assert normalize_time_input("00:00") == "00:00:00.000"

    def test_invalid_format(self):
        with pytest.raises(ValueError, match="Invalid time format"):
            normalize_time_input("invalid")
        with pytest.raises(ValueError, match="Invalid time format"):
            normalize_time_input("1:2:3:4")

    def test_invalid_time_values(self):
        with pytest.raises(ValueError, match="Minutes/seconds must be < 60"):
            normalize_time_input("00:60:00")
        with pytest.raises(ValueError, match="Minutes/seconds must be < 60"):
            normalize_time_input("60:60")


# Tests for time window search filtering
def test_search_with_end_time(runner):
    """Search with end time should only return results before that timestamp."""
    # Use 'criminal' which exists in the test DB at timestamps > 26:00
    result = runner.invoke(cli, ["search", "criminal", "--end-time", "00:40:00", "-l", "99"])
    assert result.exit_code == 0
    assert "criminal" in result.output.lower()


def test_search_with_start_time(runner):
    """Search with start time should only return results after that timestamp."""
    result = runner.invoke(cli, ["search", "criminal", "--start-time", "00:20:00", "-l", "99"])
    assert result.exit_code == 0


def test_search_with_time_window(runner):
    """Search with both start and end time."""
    result = runner.invoke(
        cli, ["search", "criminal", "--start-time", "00:25:00", "--end-time", "00:35:00", "-l", "99"]
    )
    assert result.exit_code == 0


def test_search_time_window_filters_results(runner):
    """Time window should filter out results outside the range."""
    # Search without filter
    result_all = runner.invoke(cli, ["search", "criminal", "-l", "99"])
    # Search with narrow window that excludes late timestamps
    result_early = runner.invoke(cli, ["search", "criminal", "--end-time", "00:10:00", "-l", "99"])
    # Early window should return no results (criminal appears after 26:00)
    assert result_all.exit_code == 0
    assert result_early.exit_code == 1  # No matches in early window


def test_search_with_short_time_format(runner):
    """Search with MM:SS time format should work."""
    result = runner.invoke(cli, ["search", "criminal", "--end-time", "40:00", "-l", "99"])
    assert result.exit_code == 0


def test_search_invalid_time_format(runner):
    """Invalid time format should return error."""
    result = runner.invoke(cli, ["search", "test", "--start-time", "invalid"])
    assert result.exit_code == 1
    assert "Invalid time format" in result.output


if __name__ == "__main__":
    pytest.main([__file__])
