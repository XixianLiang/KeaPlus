# Introduction 

Kea2 is an easy-to-use Python library for supporting, customizing and improving automated UI testing for mobile apps. The library is currently built on top of [Fastbot](https://github.com/bytedance/Fastbot_Android) and [uiautomator2](https://github.com/openatx/uiautomator2), and targeting [Android](https://en.wikipedia.org/wiki/Android_(operating_system)) apps.

### Kea2 has three important features:
- **Feature 1**(查找稳定性问题): coming with the full capability of [Fastbot](https://github.com/bytedance/Fastbot_Android) for stress testing and finding *stability problems* (i.e., *crashing bugs*); 
- **Feature 2**(自定义测试场景或事件序列[^1]): customizing testing scenarios when running Fastbot (e.g., testing specific app functionalities, executing specific event traces, entering specifc UI pages, reaching specific app states) with the full capability and flexibility powered by *python* language and [uiautomator2](https://github.com/openatx/uiautomator2);
- **Feature 3**(支持断言机制[^2]): supporting auto-assertions when running Fastbot, based on the idea of [property-based testing](https://en.wikipedia.org/wiki/Software_testing#Property_testing) inheritted from [Kea](https://github.com/ecnusse/Kea), for finding *logic bugs* (i.e., *non-crashing bugs*)

>We provide a detailed introduction to the application scenarios of features 2 and 3 using WeChat as an example. Please refer to [Scenario_Examples](docs/Scenario_Examples_zh.md).

These three features can be combined to customize and improve automated UI testing.

<div align="center">
    <div style="max-width:80%; max-height:80%">
    <img src="docs/intro.png" style="border-radius: 14px; width: 80%; height: 80%;"/> 
    </div>
</div>

> Kea2 is designed to be capable of fusing the (property-based) *scripts* (e.g., written in uiautomator2) with automated UI testing tools (e.g., Fastbot), thus combining the strengths of human knowledge on app's business logics (empowered by the scripts) and random fuzzing. Many useful features (e.g., mimicing exploratory testing) can be implemented based on such a capability.

**The ability of the three features in Kea2**
|  | **Feature 1** | **Feature 2** | **Feature 3** |
| --- | --- | --- | ---- |
| **Finding crashes** | :+1: | :+1: | :+1: |
| **Finding crashes in deep states** |  | :+1: | :+1: |
| **Finding non-crashing functional bugs** |  |  | :+1: |
 
Kea2, released as a Python library, currently works with:
- [unittest](https://docs.python.org/3/library/unittest.html) as the testing framework;
- [uiautomator2](https://github.com/openatx/uiautomator2) as the UI test driver; 
- [Fastbot](https://github.com/bytedance/Fastbot_Android) as the backend automated UI testing tool.

In the future, Kea2 will be extended to support
- [pytest](https://docs.pytest.org/en/stable/)
- [Appium](https://github.com/appium/appium), [Hypium]() (for HarmonyOS)
- other automated UI testing tools (not limited to Fastbot)

> Kea2 is inspired by many valuable insights, advices and lessons shared by experienced industrial practitioners from Bytedance (Zhao Zhang, Yuhui Su from the Fastbot team), OPay (Tiesong Liu), WeChat (Haochuan Lu, Yuetang Deng), Huawei, Xiaomi and etc. Kudos!

## Installation

Running requirements/environment:
- support Windows, MacOS and Linux
- python 3.8+
- Android SDK installed
- **VPN closed** (Features 2 and 3 required)

```bash
python3 -m pip install Kea2-python

kea2 -h
```


## Quick Test

Kea2 connects to and runs on Android devices. We recommend you to do a quick test to ensure that Kea2 is compatible with your devices.

1. Connect to an Android device and make sure you can see the connected device by running `adb devices`. 

2. Run `quicktest.py` to test a sample app `omninotes` (released as `omninotes.apk` in Kea2's repository). The script `quicktest.py` will automatically install and test this sample app for a short time.

```python
kea2 init
python3 quicktest.py
```

If you can see the app `omninotes` is successfully running and tested, Kea2 works. Otherwise, please help [file a bug report](https://github.com/ecnusse/Kea2/issues) with the error message to us. Thank you!

If you do not have an Android device at hand, you can use an Android emulator to run Kea2. The following commands can help create and start an Android emulator (Android version 12, API level 31) on a x86 machine (of course, you can create emulators by Android Studio):
```bash
sdkmanager "system-images;android-31;google_apis;x86_64"

avdmanager create avd --force --name Android12 --package 'system-images;android-31;google_apis;x86_64' --abi google_apis/x86_64 --sdcard 1024M --device 'Nexus 7'

emulator -avd Android12 -port 5554 &
```

> [quicktest.py](https://github.com/XixianLiang/KeaPlus/blob/main/quicktest.py) is a dead simple script which is ready-to-go with Fastbot. You can customize this script for testing your apps.

## Feature 1(查找稳定性问题): running Fastbot

Test your app with the full capability of [Fastbot](https://github.com/bytedance/Fastbot_Android) for stress testing and finding *stability problems* (i.e., *crashing bugs*); 


```bash
kea2 run -s "emulator-5554" -p it.feio.android.omninotes.alpha --agent native --running-minutes 10 --throttle 200
```

The usage is similar to the the original [Fastbot](https://github.com/bytedance/Fastbot_Android?tab=readme-ov-file#run-fastbot-with-shell-command)'s shell commands. 
See more options by `kea2 run -h`


## Feature 2(自定义测试场景或事件序列): customizing testing scenarios by scripts

When running any automated UI testing tools like Fastbot to test your apps, you may find that some specifc UI pages or functionalities are difficult to reach or cover. The reason is that Fastbot lacks knowledge of your apps. Fortunately, this is the strength of script testing. In Feature 2, Kea2 can support writing small scripts to guide Fastbot to explore wherever we want.

<div align="center">
    <div>
    <img src="docs/stage1.png" style="border-radius: 14px; width: 80%; height: 80%;"/> 
    </div>
</div>

<div align="center">
    <img src="docs/stage2.png" style="border-radius: 14px; width: 80%; height: 80%;"/> 
</div>

Kea2 can support you to test your app by customizing testing scenarios (e.g., testing specific app functionalities, executing specific event traces, entering specifc UI pages, reaching specific app states) with the full capability and flexibility powered by `python` language and [uiautomator2](https://github.com/openatx/uiautomator2);

In Kea2, a script is composed of two elements:
-  **Precondition:** When to execute the script.
- **Interaction scenario:** The interaction logic (specified in the script's test method) to reach where we want.

### Example

Assuming `Privacy` is a hard-to-reach UI page during automated UI testing. Kea2 can easily guide Fastbot to reach this page.

```python
    @prob(0.5)
    # precondition: when we are at the page `Home`
    @precondition(lambda self: 
        self.d(text="Home").exists
    )
    def test_goToPrivacy(self):
        """
        Guide Fastbot to the page `Privacy` by opening `Drawer`, 
        clicking the option `Setting` and clicking `Privacy`.
        """
        self.d(description="Drawer").click()
        self.d(text="Settings").click()
        self.d(text="Privacy").click()
```

- By the decorator `@precondition`, we specify the precondition --- when we are at the `Home` page. 
In this case, the `Home` page is the entry page of the `Privacy` page and the `Home` page can be easily reached by Fastbot. Thus, the script will be activated when we are at `Home` page by checking whether a unique widget `Home` exists. 
- In script's test method `test_goToPrivacy`, we specify the interaction logic (i.e., opening `Drawer`, clicking the option `Setting` and clicking `Privacy`) to guide Fastbot to reach the `Privacy` page.
- By the decorator `@prob`, we specify the probability (50% in this example) to do the guidance when we are at the `Home` page. As a result, Kea2 still allows Fastbot to explore other pages.

You can find the full example in script `quicktest.py` and run it by executing:

```python
python3 quicktest.py
```

In real use, you can use `kea2 run` to launch the customizing script.

```bash
# Launch Kea2 and load one single script quicktest.py.
kea2 run -s "emulator-5554" -p it.feio.android.omninotes.alpha --agent u2 --running-minutes 10 --throttle 200 --driver-name d unittest discover -p quicktest.py
```

## Feature 3(支持断言机制): Supporting auto-assertions by scripts.

Kea2 supports auto-assertions when running Fastbot for finding *logic bugs* (i.e., *non-crashing bugs*). To achieve this, you can add assertions in the scripts. When an assertion fails during automated UI testing, we find a likely functional bug. This idea is inspired by  [property-based testing](https://en.wikipedia.org/wiki/Software_testing#Property_testing) inheritted from [Kea](https://github.com/ecnusse/Kea).

<div align="center">
    <img src="docs/stage3.png" style="border-radius: 14px; width: 80%; height: 80%;"/> 
</div>

In Feature 3, a script is composed of three elements:

- **Precondition:** When to execute the script.
- **Interaction scenario:** The interaction logic (specified in the script's test method).
- **Assertion:** The expected app behaviour.

### Example

In a social media app, message sending is a common feature. On the message sending page, the `send` button should always appears when the input box is not empty (i.e., has some message).

<div align="center" >
    <div >
        <img src="docs/socialAppBug.png" style="border-radius: 14px; width:60%; height:70%;"/>
    </div>
    <p>The expected behavior (the upper figure) and the buggy behavior (the lower figure).
<p/>
</div>

For the preceding always-holding property, we can write the following script to validate the functional correctness: when there is an `input_box` widget on the message sending page, we can type any non-empty string text into the input box and assert `send_button` should always exists.


```python
    @precondition(
        lambda self: self.d(description="input_box").exists
    )
    def test_input_box(self):
        from hypothesis.strategies import text, ascii_letters
        random_str = text(alphabet=ascii_letters).example()
        self.d(description="input_box").set_text(random_str)
        assert self.d(description="send_button").exist

        # we can even do more assertions, e.g.,
        #       the input string should exist on the message sending page
        assert self.d(text=random_str).exist
```
>  We use [hypothesis](https://github.com/HypothesisWorks/hypothesis), a property-based testing library for Python, to generate random texts according to the given rules.

# Documentation

## Configuration File

After executing `Kea2 init`, some configuration files will be generated in the `configs` directory. 
These configuration files belong to `Fastbot`, and their specific introductions are provided in [Introduction to configuration files](https://github.com/bytedance/Fastbot_Android/blob/main/handbook-cn.md#%E4%B8%93%E5%AE%B6%E7%B3%BB%E7%BB%9F).

## Widget Block

We support blacklisting of widgets so that you can guide Fastbot to block certain widgets 
during the testing process. 
This feature is specifically divided into Global Block List (always effective) 
and Conditional Block List (only effective when one or several preconditions are met).
The list of blocked widgets is specifically written in `configs/widget.block.py`in the root directory, and its usage is as follows.

### Global Block List
You can write the following function in the script, and the return value of the function 
is the widgets you want to block, and the blocking will always take effect. 
The widgets here support specifying with `text`, `description`, or `xpath`.
```python
    def global_block_widgets(d: "Device"):
    """
    global block widgets.
    return the widgets you want to block globally
    only available in mode `u2 agent`
    """
    return [d(text="widgets to block"), d.xpath(".//node[@text='widget to block']"),
            d(description="widgets to block")]
```
### Conditional Block List
If you add the `@precondition` annotation before the function, you can specify that blocking 
only takes effect under certain specific conditions.
```python
    # conditional block list
@precondition(lambda d: d(text="In the home page").exists)
def block_sth(d: "Device"):
    # Important: function shold starts with "block"
    return [d(text="widgets to block"), d.xpath(".//node[@text='widget to block']"),
            d(description="widgets to block")]
```

## Write scripts

Kea2 uses [Unittest](https://docs.python.org/3/library/unittest.html) to manage scripts. All the Kea2's scripts can be found in unittest's rules (i.e., the test methods should start with `test_`, the test classes should extend `unittest.TestCase`).

Kea2 uses [Uiautomator2](https://github.com/openatx/uiautomator2) to manipulate android devices. Refer to [Uiautomator2's docs](https://github.com/openatx/uiautomator2?tab=readme-ov-file#quick-start) for more details.

Basically, you can write Kea2's scripts by following two steps:

1. Create a test class which extends `unittest.TestCase`.

```python
import unittest

class MyFirstTest(unittest.TestCase):
    ...
```

2. Write your own script by defining test methods

By default, only the test method starts with `test_` will be found by unittest. You can decorate the function with `@precondition`. The decorator `@precondition` takes a function which returns boolean as an arugment. When the function returns `True`, the precondition is satisified and the script will be activated, and Kea2 will run the script based on certain probability defined by the decorator `@prob`.

Note that if a test method is not decorated with `@precondition`.
This test method will never be activated during automated UI testing, and will be treated as a normal `unittset` test method.
Thus, you need to explicitly specify `@precondition(lambda self: True)` when the test method should be always executed. When a test method is not decorated with `@prob`, the default probability is 1 (always execute when precondition satisfied).

```python
import unittest
from kea2 import precondition

class MyFirstTest(unittest.TestCase):

    @prob(0.7)
    @precondition(lambda self: ...)
    def test_func1(self):
        ...
```

You can read [Kea - Write your fisrt property](https://kea-docs.readthedocs.io/en/latest/part-keaUserManuel/first_property.html) for more details.


## Launch Kea2

We offer two ways to launch Kea2.

### 1. Launch by shell commands

Kea2 is compatible with `unittest` framework. You can manage your test cases in unittest style. You can launch Kea2 with `kea run` with driver options and sub-command `unittest` (for unittest options).

The shell command:
```
kea2 run <Kea2 cmds> unittest <unittest cmds> 
```

Sample shell commands:

```bash
# Launch Kea2 and load one single script quicktest.py.
kea2 run -s "emulator-5554" -p it.feio.android.omninotes.alpha --agent u2 --running-minutes 10 --throttle 200 --driver-name d unittest discover -p quicktest.py

# Launch Kea2 and load multiple scripts from the directory mytests/omni_notes
kea2 run -s "emulator-5554" -p it.feio.android.omninotes.alpha --agent u2 --running-minutes 10 --throttle 200 --driver-name d unittest discover -s mytests/omni_notes
```

| arg | meaning |
| --- | --- |
| -s | The serial of your device, which can be found by `adb devices` |
| -p | The tested app's package name (e.g., com.example.app) | 
| -o | The ouput directory for logs and results |
| --agent |  {native, u2}. By default, `u2` is used and supports all the three important features of Kea2. If you hope to run the orignal Fastbot, please use `native`.|
| --running-minutes | The time (m) to run Kea2 | 
| --max-step | The maxium number of monkey events to send (only available in `--agent u2`) | 
| --throttle | The delay time (ms) between two monkey events |
| --driver-name | The name of driver used in the script. If `--driver-name d` is specified, you should use `d` to interact with a device, e..g, `self.d(..).click()`. |
| unittest | Specify to load which scripts. This  sub-command `unittest` is fully compatible with unittest. See `python3 -m unittest -h` for more options of unittest. This option is only available in `--agent u2`.


### 2. Launch by `unittest.main`

Like unittest, we can launch Kea2 through the method `unittest.main`.

Here is an example (named as `mytest.py`). You can see that the options are directly defined in the script.

```python
import unittest

from kea2 import KeaTestRunner, Options
from kea2.u2Driver import U2Driver

class MyTest(unittest.TestCase):
    ...
    # <your test methods here>

if __name__ == "__main__":
    KeaTestRunner.setOptions(
        Options(
            driverName="d",
            Driver=U2Driver,
            packageNames=[PACKAGE_NAME],
            # serial="emulator-5554",   # specify the serial
            maxStep=100,
            # running_mins=10,  # specify the maximal running time in minutes, default value is 10m
            # throttle=200,   # specify the throttle in milliseconds, default value is 200ms
            # agent='native'  # 'native' for running the vanilla Fastbot
        )
    )
    # Declare the KeaTestRunner
    unittest.main(testRunner=KeaTestRunner)
```

We can directly run the script `mytest.py` to launch Kea2, e.g.,
```python
python3 mytest.py
```

Here's all the available options in `Options`.

```python
# the driver_name in script (if self.d, then d.) 
driverName: str
# the driver (only U2Driver available now)
Driver: U2Driver
# list of package names. Specify the apps under test
packageNames: List[str]
# target device
serial: str = None
# test agent. "u2" is the default agent
agent: "u2" | "native" = "u2"
# max step in exploration (availble in stage 2~3)
maxStep: int # default "inf"
# time(mins) for exploration
running_mins: int = 10
# time(ms) to wait when exploring the app
throttle: int = 200
# the output_dir for saving logs and results
output_dir: str = "output"
```


## Examining the running statistics of scripts .

If you want to examine whether your scripts have been executed or how many times they have been executed during testing. Open the file `result.json` after the testing is finished.

Here's an example.

```json
{
    "test_goToPrivacy": {
        "precond_satisfied": 8,
        "executed": 2,
        "fail": 0,
        "error": 1
    },
    ...
}
```

**How to read `result.json`**

Field | Description | Meaning
--- | --- | --- |
precond_satisfied | During exploration, how many times has the test method's precondition been satisfied? | Does we reach the state during exploration? 
executed | During UI testing, how many times the test method has been executed? | Has the test method ever been executed?
fail | How many times did the test method fail the assertions during UI testing? | When failed, the test method found a likely functional bug. 
error | How many times does the test method abort during UI tsting due to some unexpected errors (e.g. some UI widgets used in the test method cannot be found) | When some error happens, the script needs to be updated/fixed because the script leads to some unexpected errors.

## Contributors/Maintainers

Kea2 has been actively developed and maintained by the people in [ecnusse](https://github.com/ecnusse).

### Open-source projects used by Kea2

- [Fastbot](https://github.com/bytedance/Fastbot_Android)
- [uiautomator2](https://github.com/openatx/uiautomator2)
- [hypothesis](https://github.com/HypothesisWorks/hypothesis)

[^1]: 不少UI自动化测试工具提供了“自定义事件序列”能力（如[Fastbot](https://github.com/bytedance/Fastbot_Android/blob/main/handbook-cn.md#%E8%87%AA%E5%AE%9A%E4%B9%89%E4%BA%8B%E4%BB%B6%E5%BA%8F%E5%88%97) 和[AppCrawler](https://github.com/seveniruby/AppCrawler)），但在实际使用中存在不少问题，如自定义能力有限、使用不灵活等。此前不少Fastbot用户抱怨过其“自定义事件序列”在使用中的问题，如[#209](https://github.com/bytedance/Fastbot_Android/issues/209), [#225](https://github.com/bytedance/Fastbot_Android/issues/225), [#286](https://github.com/bytedance/Fastbot_Android/issues/286)等。

[^2]: 在UI自动化测试过程中支持自动断言是一个很重要的能力，但几乎没有测试工具提供这样的能力。我们注意到[AppCrawler](https://ceshiren.com/t/topic/15801/5)的开发者曾经希望提供一种断言机制，得到了用户的热切响应，不少用户从21年就开始催更，但始终未能实现。
