import tempfile
import unittest
from pathlib import Path
from types import SimpleNamespace
from unittest.mock import Mock

from lili.portal_agent import Agent, PortalClient, TunnelController, tunnel_url


class PortalAgentTests(unittest.TestCase):
    def test_healthy_tunnel_is_never_replaced(self):
        scratch=Path("work/tests").resolve();scratch.mkdir(parents=True,exist_ok=True)
        with tempfile.TemporaryDirectory(dir=scratch) as folder:
            root=Path(folder);(root/"work/remote").mkdir(parents=True)
            (root/"work/remote/public-url.txt").write_text("https://good-test.trycloudflare.com")
            runner=Mock();controller=TunnelController(root,probe=lambda _:True,runner=runner,wait=Mock())
            self.assertTrue(controller.reconnect()["healthy"]);runner.assert_not_called()

    def test_transient_failure_is_checked_again_before_replacement(self):
        scratch=Path("work/tests").resolve();scratch.mkdir(parents=True,exist_ok=True)
        with tempfile.TemporaryDirectory(dir=scratch) as folder:
            root=Path(folder);(root/"work/remote").mkdir(parents=True)
            (root/"work/remote/public-url.txt").write_text("https://good-test.trycloudflare.com")
            runner=Mock();probe=Mock(side_effect=[False,True])
            self.assertTrue(TunnelController(root,probe=probe,runner=runner,wait=Mock()).reconnect()["healthy"])
            runner.assert_not_called()

    def test_agent_accepts_only_the_fixed_reconnection_action(self):
        client=Mock();controller=Mock();client.call.return_value={"job":{"id":"a"*48,"action":"execute","command":"unsafe"}}
        with self.assertRaises(ValueError):Agent(client,controller).once()
        controller.reconnect.assert_not_called()
        client.call.return_value={"job":{"id":"a"*48,"action":"reconnect"}}
        controller.reconnect.return_value={"url":"https://test-link.trycloudflare.com","healthy":True}
        Agent(client,controller).once()
        client.call.assert_called_with("report",{"url":"https://test-link.trycloudflare.com","healthy":True,"jobId":"a"*48})

    def test_device_key_cannot_be_sent_to_an_arbitrary_origin_or_action(self):
        for origin in ("http://127.0.0.1","https://evil.example","https://site.owner.chatgpt.site.evil.test","https://site.owner.chatgpt.site/path"):
            with self.subTest(origin=origin),self.assertRaises(ValueError):PortalClient(origin,"a"*64)
        opener=Mock();client=PortalClient("https://portal.owner.chatgpt.site","a"*64,opener=opener)
        with self.assertRaises(ValueError):client.call("unexpected")
        opener.open.assert_not_called()
        for url in ("http://localhost","https://evil.test","https://good.trycloudflare.com/evil"):
            self.assertIsNone(tunnel_url(url))
