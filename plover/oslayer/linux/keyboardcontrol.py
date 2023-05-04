from plover import log
from plover.machine.keyboard_capture import Capture
from plover.output import Output

from .keyboardcontrol_libevdev import KeyboardCapture as  ev_kc, KeyboardEmulation as  ev_ke
from .keyboardcontrol_x11      import KeyboardCapture as x11_kc, KeyboardEmulation as x11_ke

class KeyboardCapture(Capture):

    _delegate: Capture

    def __init__(self):
        super().__init__()
        try:
            self._delegate = ev_kc()
        except Exception as e:
            log.warning('Keyboard capture falling back to X11 as libevdev backend failed: {}'.format(e))
            self._delegate = x11_kc()

    def start(self):
        self._delegate.start()

    def cancel(self):
        self._delegate.cancel()

    def suppress(self, suppressed_keys=()):
        self._delegate.suppress(suppressed_keys)


class KeyboardEmulation(Output):

    _delegate: Output

    def __init__(self):
        super().__init__()
        try:
            self._delegate = ev_ke()
        except Exception as e:
            log.warning('Keyboard emulation falling back to X11 as libevdev backend failed: {}'.format(e))
            self._delegate = x11_ke()

    def send_backspaces(self, count):
        self._delegate.send_backspaces(count)

    def send_string(self, string):
        self._delegate.send_string(string)

    def send_key_combination(self, combo):
        self._delegate.send_key_combination(combo)
