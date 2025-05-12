import unittest
import uiautomator2 as u2

from kea2 import KeaTestRunner, Options
from kea2.u2Driver import U2Driver

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
            maxStep=10,
            # running_mins=10,  # specify the maximal running time in minutes, default value is 10m
            # throttle=200,   # specify the throttle in milliseconds, default value is 200ms
            # agent='native'  # 'native' for running the vanilla Fastbot, 'u2' for running Kea2
        )
    )
    unittest.main(testRunner=KeaTestRunner)
