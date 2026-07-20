from __future__ import annotations

from octw.common.config import OCTWSettings


class TestConfig:
    def test_defaults(self):
        s = OCTWSettings()
        assert s.tenant_base_dir == "/var/lib/octw/tenants"
        assert s.default_pids_limit == 512
        assert s.idle_pause_seconds == 1800
        assert s.idle_stop_seconds == 28800
        assert s.openclaw_image == "ghcr.io/openclaw/openclaw"
        assert s.openclaw_digest == "sha256:6a31d44b2944e7adcd2b582bf6fb463111264ebca97a0201795b799135bd102c"

    def test_env_prefix(self):
        import os
        os.environ["OCTW_LOG_LEVEL"] = "DEBUG"
        s = OCTWSettings()
        assert s.log_level == "DEBUG"
        del os.environ["OCTW_LOG_LEVEL"]
