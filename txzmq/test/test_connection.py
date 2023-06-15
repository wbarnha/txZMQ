"""
Tests for L{txzmq.connection}.
"""
from zmq import constants

from zope.interface import verify as ziv

from twisted.internet.interfaces import IFileDescriptor, IReadDescriptor
from twisted.trial import unittest

from txzmq.connection import ZmqConnection, ZmqEndpoint, ZmqEndpointType
from txzmq.factory import ZmqFactory
from txzmq.test import _wait


class ZmqTestSender(ZmqConnection):
    socketType = constants.PUSH


class ZmqTestReceiver(ZmqConnection):
    socketType = constants.PULL

    def messageReceived(self, message):
        if not hasattr(self, 'messages'):
            self.messages = []

        self.messages.append(message)


class ZmqConnectionTestCase(unittest.TestCase):
    """
    Test case for L{zmq.twisted.connection.Connection}.
    """

    def setUp(self):
        self.factory = ZmqFactory()

    def tearDown(self):
        self.factory.shutdown()

    def test_interfaces(self):
        ziv.verifyClass(IReadDescriptor, ZmqConnection)
        ziv.verifyClass(IFileDescriptor, ZmqConnection)

    def test_init(self):
        ZmqTestReceiver(
            self.factory, ZmqEndpoint(ZmqEndpointType.bind, "inproc://#1"))
        ZmqTestSender(
            self.factory, ZmqEndpoint(ZmqEndpointType.connect, "inproc://#1"))

    def test_addEndpoints(self):
        r = ZmqTestReceiver(
            self.factory, ZmqEndpoint(ZmqEndpointType.bind, "inproc://#1"))
        r.addEndpoints([ZmqEndpoint(ZmqEndpointType.bind, "inproc://#2"),
                        ZmqEndpoint(ZmqEndpointType.bind, "inproc://#3")])

        s = ZmqTestSender(
            self.factory, ZmqEndpoint(ZmqEndpointType.connect, "inproc://#3"))

        s.send(b'abcd')

        def check(ignore):
            result = getattr(r, 'messages', [])
            expected = [[b'abcd']]
            self.assertEqual(
                result, expected, "Message should have been received")

        return _wait(0.01).addCallback(check)

    def test_repr(self):
        expected = ("ZmqTestReceiver(ZmqFactory(), "
                    "[ZmqEndpoint(type='bind', address='inproc://#1')])")
        result = ZmqTestReceiver(
            self.factory, ZmqEndpoint(ZmqEndpointType.bind, "inproc://#1"))
        self.assertEqual(expected, repr(result))

    def test_send_recv(self):
        r = ZmqTestReceiver(
            self.factory, ZmqEndpoint(ZmqEndpointType.bind, "inproc://#1"))
        s = ZmqTestSender(
            self.factory, ZmqEndpoint(ZmqEndpointType.connect, "inproc://#1"))

        s.send(b'abcd')

        def check(ignore):
            result = getattr(r, 'messages', [])
            expected = [[b'abcd']]
            self.assertEqual(
                result, expected, "Message should have been received")

        return _wait(0.01).addCallback(check)

    def test_send_recv_tcp(self):
        r = ZmqTestReceiver(
            self.factory, ZmqEndpoint(ZmqEndpointType.bind,
                                      "tcp://127.0.0.1:5555"))
        s = ZmqTestSender(
            self.factory, ZmqEndpoint(ZmqEndpointType.connect,
                                      "tcp://127.0.0.1:5555"))

        for i in range(100):
            s.send(str(i).encode())

        def check(ignore):
            result = getattr(r, 'messages', [])
            expected = [[str(i).encode()] for i in range(100)]
            self.assertEqual(
                result, expected, "Messages should have been received")

        return _wait(0.01).addCallback(check)

    def test_send_recv_tcp_large(self):
        r = ZmqTestReceiver(
            self.factory, ZmqEndpoint(ZmqEndpointType.bind,
                                      "tcp://127.0.0.1:5555"))
        s = ZmqTestSender(
            self.factory, ZmqEndpoint(ZmqEndpointType.connect,
                                      "tcp://127.0.0.1:5555"))

        s.send([b'0' * 10000, b'1' * 10000])

        def check(ignore):
            result = getattr(r, 'messages', [])
            expected = [[b'0' * 10000, b'1' * 10000]]
            self.assertEqual(
                result, expected, "Messages should have been received")

        return _wait(0.01).addCallback(check)
