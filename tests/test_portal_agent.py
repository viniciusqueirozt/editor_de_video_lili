import tempfile
import unittest
from pathlib import Path
from types import SimpleNamespace
from unittest.mock import Mock
from concurrent.futures import Future
from urllib.error import HTTPError

from lili.portal_agent import Agent, PortalClient, TunnelController, tunnel_url


class PortalAgentTests(unittest.TestCase):
    def test_client_identifies_itself_and_sends_report_as_json(self):
        response=Mock();response.read.return_value=b'{"ok":true}'
        response.__enter__=Mock(return_value=response);response.__exit__=Mock(return_value=False)
        opener=Mock();opener.open.return_value=response
        client=PortalClient("https://portal.owner.chatgpt.site","a"*64,opener=opener)
        self.assertEqual(client.call("report",{"healthy":False,"url":None}),{"ok":True})
        request=opener.open.call_args.args[0]
        self.assertEqual(request.get_header("User-agent"),"Lili-Portal-Connector/1.0")
        self.assertEqual(request.get_header("Accept"),"application/json")
        self.assertEqual(request.get_method(),"POST")
        self.assertEqual(request.full_url,"https://portal.owner.chatgpt.site/api/device/report")

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

    def test_heartbeat_continues_while_probe_and_reconnect_are_pending(self):
        client=Mock();client.call.return_value={"job":None}
        controller=Mock();executor=Mock();probe=Future();reconnect=Future()
        executor.submit.side_effect=[probe,reconnect]
        clock=[0];agent=Agent(client,controller,clock=lambda:clock[0])
        agent.step(executor)
        job={"id":"b"*48,"action":"reconnect"}
        client.call.return_value={"job":job};agent.step(executor)
        client.call.return_value={"job":None};agent.step(executor)
        self.assertEqual(executor.submit.call_count,1)
        probe.set_result({"url":"https://still-live.trycloudflare.com","healthy":True})
        agent.step(executor)
        self.assertEqual(executor.submit.call_args.args,(controller.reconnect,))
        reports=[call for call in client.call.call_args_list if call.args[0]=="report"]
        self.assertEqual(reports,[],"A stale probe cannot finish a claimed reconnection")
        for _ in range(4):clock[0]+=3;agent.step(executor)
        self.assertEqual(executor.submit.call_count,2,"Only one local task runs at a time")
        reconnect.set_result({"url":"https://still-live.trycloudflare.com","healthy":True})
        agent.step(executor)
        client.call.assert_called_with("report",{"url":"https://still-live.trycloudflare.com","healthy":True,"jobId":"b"*48})
        self.assertGreaterEqual(sum(call.args[0]=="poll" for call in client.call.call_args_list),8)

    def test_completed_report_retries_network_failure_without_repeating_reconnect(self):
        client=Mock();job={"id":"c"*48,"action":"reconnect"}
        client.call.return_value={"job":job};executor=Mock();task=Future();executor.submit.return_value=task
        agent=Agent(client,Mock(),clock=lambda:0);agent.step(executor)
        task.set_result({"url":"https://kept-link.trycloudflare.com","healthy":True})
        def call(action,data=None):
            if action=="report":raise OSError("simulated offline")
            return {"job":None}
        client.call.side_effect=call
        with self.assertRaises(OSError):agent.step(executor)
        self.assertIs(agent.future,task);executor.submit.assert_called_once()
        client.call.side_effect=lambda action,data=None:{"job":None} if action=="poll" else {"ok":True}
        agent.step(executor);self.assertIsNone(agent.future);executor.submit.assert_called_once()

    def test_expired_job_report_is_discarded_and_heartbeat_recovers(self):
        client=Mock();client.call.return_value={"job":{"id":"d"*48,"action":"reconnect"}}
        executor=Mock();task=Future();executor.submit.return_value=task
        agent=Agent(client,Mock(),clock=lambda:0);agent.step(executor);task.set_exception(RuntimeError("synthetic failure"))
        def call(action,data=None):
            if action=="report":raise HTTPError("https://portal.owner.chatgpt.site",409,"Expired",{},None)
            return {"job":None}
        client.call.side_effect=call;agent.step(executor)
        self.assertIsNone(agent.future);self.assertIsNone(agent.job_id)

    def test_polling_worker_rejects_unknown_actions_before_scheduling(self):
        client=Mock();client.call.return_value={"job":{"id":"e"*48,"action":"execute"}}
        executor=Mock()
        with self.assertRaises(ValueError):Agent(client,Mock()).step(executor)
        executor.submit.assert_not_called()
