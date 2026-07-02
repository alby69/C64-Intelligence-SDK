import unittest
import json
import base64
from pyc64c.sdk import process_sdk_request

class TestSDKProtocol(unittest.TestCase):
    def test_successful_compilation(self):
        request = {
            "version": "1.0",
            "source_code": "x: byte = 10\ndef main():\n    print(\"hello\")",
            "options": {"target": "c64"}
        }
        response_json = process_sdk_request(json.dumps(request))
        response = json.loads(response_json)

        self.assertEqual(response["status"], "success")
        self.assertIn("prg_base64", response["artifacts"])
        self.assertIn("binary_size_bytes", response["metrics"])
        self.assertTrue(len(response["artifacts"]["prg_base64"]) > 0)

    def test_lexer_error(self):
        request = {
            "version": "1.0",
            "source_code": "x: byte = @", # @ is an unexpected character
            "options": {"target": "c64"}
        }
        response_json = process_sdk_request(json.dumps(request))
        response = json.loads(response_json)

        self.assertEqual(response["status"], "error")
        self.assertTrue(any("Carattere inatteso" in d["message"] for d in response["diagnostics"]))

    def test_parser_error(self):
        request = {
            "version": "1.0",
            "source_code": "def main(", # missing closing paren and colon
            "options": {"target": "c64"}
        }
        response_json = process_sdk_request(json.dumps(request))
        response = json.loads(response_json)

        self.assertEqual(response["status"], "error")
        self.assertTrue(len(response["diagnostics"]) > 0)

    def test_symbols_generation(self):
        request = {
            "version": "1.0",
            "source_code": "x: byte = 10\ndef main():\n    y: byte = 5\n    print(x + y)",
            "options": {"target": "c64", "generate_symbols": True}
        }
        response_json = process_sdk_request(json.dumps(request))
        response = json.loads(response_json)

        self.assertEqual(response["status"], "success")
        self.assertIn("symbols", response["artifacts"])
        symbols = response["artifacts"]["symbols"]
        self.assertIn(".main", symbols)
        self.assertIn("._x", symbols)
        self.assertIn("._main_y", symbols)

if __name__ == '__main__':
    unittest.main()
