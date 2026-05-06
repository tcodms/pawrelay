import sys
import types
from unittest.mock import Mock

from ai.errors import notify_admin


def test_notify_admin_uses_email_sender(monkeypatch):
    app_module = types.ModuleType("app")
    app_module.__path__ = []
    services_module = types.ModuleType("app.services")
    services_module.__path__ = []
    email_service_module = types.ModuleType("app.services.email_service")
    email_service_module.send_admin_alert_email_sync = Mock(return_value=True)

    monkeypatch.setitem(sys.modules, "app", app_module)
    monkeypatch.setitem(sys.modules, "app.services", services_module)
    monkeypatch.setitem(sys.modules, "app.services.email_service", email_service_module)

    notify_admin("matching failed")

    email_service_module.send_admin_alert_email_sync.assert_called_once_with(
        "matching failed"
    )
