# rbwebhooks extension for Review Board.
#
# This extension allows remote services to be notified of events occuring
# within Review Board. An administrator may add "Target" URLs, at which
# the extension will fire HTTP POST requests when the specified hook
# event occurs.
import logging
import requests
import requests.exceptions

from reviewboard.extensions.base import Extension

from rbwebhooks.handlers import SignalHandlers
from rbwebhooks.models import WebHookTarget


class RBWebHooksExtension(Extension):
    """A Web Hooks Extension for Review Board"""

    is_configurable = True
    has_admin_site = True
    default_settings = {
        'attempts': 1,
    }

    def initialize(self):
        self.settings.load()
        self.signal_handlers = SignalHandlers(self)

    def notify(self, hook_id, request_payload):
        """
        Make web requests corresponding to a specific hook_id

        Called by signal handlers to send the web requests
        """
        targets = WebHookTarget.objects.filter(
            hook_id=hook_id,
            enabled=True,
        )

        for target in targets:
            self._send_web_request(
                target.url,
                request_payload,
                self.settings['attempts'])

    def _send_web_request(self, url, request_payload, attempts=1):
        """
        Send out a web request and retry on failure.

        Currently this is a blocking operation. devising a way to send
        these requests without blocking would be beneficial.
        """

        logging.debug("Web Hook URL: %s", url)
        logging.debug("Web Hook Payload: %s", request_payload)

        while attempts:
            try:
                r = requests.post(url, data=request_payload)
                logging.debug("Received response code: %s", r.status_code)
                r.raise_for_status()
                return r
            except requests.exceptions.RequestException:
                attempts -= 1

        logging.warning("Sending WebHook Request failed: %s " % url)
        return None
