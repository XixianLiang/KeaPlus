import unittest
from kea2.keaUtils import explore
import uiautomator2 as u2
import time

class MyTest(unittest.TestCase):
    def setUp(self):
        self.d = u2.connect()
        self.d.app_start("it.feio.android.omninotes.alpha")
    
    def test_add_note(self):
        self.d(resourceId="it.feio.android.omninotes.alpha:id/fab_expand_menu_button").click()
        time.sleep(1)
        self.d(resourceId="it.feio.android.omninotes.alpha:id/detail_title").set_text("Hello world")
        time.sleep(1)
        self.d(description="More options").click()
        time.sleep(1)
        self.d(text="Enable checklist").click()
        time.sleep(1)
        self.d(text="New item").set_text("first item")
        time.sleep(1)
        explore(max_step=50)
        self.d.press("back")
        time.sleep(1)
        assert (
            self.d(text="Hello world").exists
            and self.d(textContains="first item").exists
        )


if __name__ == "__main__":
    unittest.main()
