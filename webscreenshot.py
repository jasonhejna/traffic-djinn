## For QT5
#from PyQt5.QtCore import *
#from PyQt5.QtGui import *
#from PyQt5.QtWidgets import *
#from PyQt5.QtWebKitWidgets import *
#from PyQt5.QtWebKit import *
## For QT4
from PyQt4.QtCore import *
from PyQt4.QtGui import *
from PyQt4.QtWebKit import *
from PyQt4.QtNetwork import *

import urllib, time

class WebScreenShot(QWebView):
    def __init__(self, enable_js=True):
        self.app = QApplication([])
        QWebView.__init__(self)
        if enable_js:
            self.settings().setAttribute(QWebSettings.JavascriptEnabled, True)
        self._loaded = False
        self.loadFinished.connect(self._loadFinished)
        self.cookie_jar = QNetworkCookieJar()
        self.nam = QNetworkAccessManager()
        self.nam.setCookieJar(self.cookie_jar)
        self.page().setNetworkAccessManager(self.nam)

    def wait_load(self, delay):
        # process app events until page loaded
        final_time = time.time()+delay
        while time.time() < final_time:
            if self.app.hasPendingEvents():
                self.app.processEvents()
        self._loaded = False

    def _loadFinished(self, result):
        self._loaded = True

    def capture(self, url, wait=5):
        self.load(QUrl(url))
        self.wait_load(delay=wait)
        # set to webpage size
        frame = self.page().mainFrame()
        self.page().setViewportSize(frame.contentsSize())
        # render image
        image = QImage(self.page().viewportSize(), QImage.Format_ARGB32)
        painter = QPainter(image)
        frame.render(painter)
        painter.end()
        return image

    def get_cookies(self):
        cookies = self.cookie_jar.allCookies()
        return [urllib.parse.unquote(bytearray(c.value()).decode()) for c in cookies]

if __name__ == "__main__":
    import sys
    S = WebScreenShot()
    image = S.capture(sys.argv[1])
    image.save(sys.argv[2])
