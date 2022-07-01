class MatplotlibManager:
    def __init__(self, state, name):
        self._state = state
        self._name = name
        self._pixel_ratio = 1
        self._dpi = 192
        self._w_inch = 1
        self._h_inch = 1
        self._state[self._name] = {}

    def size(self):
        if self._state[self._name] is not None:
            pixel_ratio = self._state[self._name].get("pixelRatio")
            dpi = self._state[self._name].get("dpi")
            rect = self._state[self._name].get("size")
            w_inch = (rect.get("width") - 30) / (dpi)
            h_inch = (rect.get("height") - 0) / (dpi)
            if w_inch > 0 and h_inch > 0:
                self._pixel_ratio = pixel_ratio
                self._dpi = dpi
                self._w_inch = w_inch
                self._h_inch = h_inch
        return {
            "figsize": (self._w_inch, self._h_inch),
            "dpi": self._dpi,
        }
