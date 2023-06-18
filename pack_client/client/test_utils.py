import unittest
import json

from utils import get_msg, send_msg, msg_to_client


class TestSocket:
    def __init__(self, test_dict):
        self.test_dict = test_dict
        self.encoded_message = None
        self.receved_message = None

    def send(self, message_to_send):
        json_test_message = json.dumps(self.test_dict)
        self.encoded_message = json_test_message.encode('utf-8')
        self.receved_message = message_to_send

    def recv(self, max_len):
        json_test_message = json.dumps(self.test_dict)
        return json_test_message.encode('utf-8')


class TestUtils(unittest.TestCase):
    test_msg = {
        "action": "authenticate",
        "time": 555,
        "user": {
            "account_name": "admin",
            "password": "adminpass"
        }
    }
    test_msg_2 = {
        "action": "authenticate",
        "time": 555,
        "user": {
            "account_name": "notadmin",
            "password": "adminpass"
        }
    }

    def test_get_msg(self):
        test_socket = TestSocket(self.test_msg)
        try:
            if self.assertEqual(get_msg(test_socket),
                                self.test_msg):
                print('OK')
        except AssertionError:
            print('BAD')

    def test_send_msg(self):
        test_socket = TestSocket(self.test_msg)
        send_msg(test_socket, self.test_msg)
        try:
            if self.assertEqual(test_socket.encoded_message,
                                test_socket.receved_message):
                print('OK')
        except AssertionError:
            print('BAD')

    def test_msg_to_client(self):
        self.assertIsInstance(msg_to_client(), dict)


if __name__ == '__main__':
    unittest.main()
