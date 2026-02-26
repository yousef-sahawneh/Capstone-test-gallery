from openni import openni2

class OpenNIDevice:
    def __init__(self):
        self.dev = None

    def __enter__(self):
        openni2.initialize()
        self.dev = openni2.Device.open_any()
        return self

    def __exit__(self, exc_type, exc, tb):
        try:
            if self.dev is not None:
                self.dev.close()
                self.dev = None
        finally:
            openni2.unload()
        return False
