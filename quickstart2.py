import unittest
import uiautomator2 as u2

from time import sleep
from kea2 import precondition, prob, max_tries, KeaTestRunner, Options
from kea2.u2Driver import U2Driver


class Omni_Notes_Sample(unittest.TestCase):

    def setUp(self):
        self.d = u2.connect()

    @prob(0.7)  # The probability of executing the function when precondition is satisfied.
    @precondition(
        lambda self: self.d(text="Omni Notes Alpha").exists
        and self.d(text="Settings").exists
    )
    def test_goToPrivacy(self):
        """
        The ability to jump out of the UI tarpits

        precond:
            The drawer was opened
        action:
            go to settings -> privacy
        """
        print("trying to click Settings")
        self.d(text="Settings").click()
        sleep(0.5)
        print("trying to click Privacy")
        self.d(text="Privacy").click()

    @max_tries(1)
    @precondition(
        lambda self: self.d(resourceId="it.feio.android.omninotes.alpha:id/search_src_text").exists
    )
    def test_rotation(self):
        """
        The ability to make assertion to find functional bug

        precond:
            The search input box is opened
        action:
            rotate the device (set it to landscape, then back to natural)
        assertion:
            The search input box is still being opened
        """
        self.d.set_orientation("l")
        sleep(2)
        self.d.set_orientation("n")
        sleep(2)
        assert self.d(resourceId="it.feio.android.omninotes.alpha:id/search_src_text").exists()


PACKAGE_NAME = "it.feio.android.omninotes.alpha"
FILE_NAME = "omninotes.apk"

def check_installation():
    d = u2.connect()
    # automatically install omni-notes
    if PACKAGE_NAME not in d.app_list():
        d.app_install(FILE_NAME)
    d.stop_uiautomator()

if __name__ == "__main__":
    check_installation()
    KeaTestRunner.setOptions(
        Options(
            driverName="d",
            Driver=U2Driver,
            packageNames=[PACKAGE_NAME],
            # serial="emulator-5554",   # specify the serial
            maxStep=5000,
            # running_mins=10,  # specify the maximal running time in minutes, default value is 10m
            # throttle=200,   # specify the throttle in milliseconds, default value is 200ms
            # agent='native'  # 'native' for running the vanilla Fastbot, 'u2' for running Kea2
        )
    )
    unittest.main(testRunner=KeaTestRunner)
