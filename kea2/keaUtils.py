import json
from pathlib import Path
import subprocess
import threading
from typing import IO, Callable, Any, Dict, List, Literal, NewType, Optional, Union
from unittest import TextTestRunner, registerResult, TestSuite, TestCase, TextTestResult
import random
import warnings
from xml.etree import ElementTree
from dataclasses import dataclass, asdict
import requests
from .absDriver import AbstractDriver
from functools import wraps
from time import sleep
from .adbUtils import push_file
from .logWatcher import LogWatcher
import types
PRECONDITIONS_MARKER = "preconds"
PROP_MARKER = "prop"


# Class Typing
PropName = NewType("PropName", str)
PropertyStore = NewType("PropertyStore", Dict[PropName, TestCase])

def precondition(precond: Callable[[Any], bool]) -> Callable:
    """the decorator @precondition

    The precondition specifies when the property could be executed.
    A property could have multiple preconditions, each of which is specified by @precondition.
    """
    def accept(f):
        @wraps(f)
        def precondition_wrapper(*args, **kwargs):
            return f(*args, **kwargs)

        preconds = getattr(f, PRECONDITIONS_MARKER, tuple())

        setattr(precondition_wrapper, PRECONDITIONS_MARKER, preconds + (precond,))

        return precondition_wrapper

    return accept

def prob(p: float):
    """the decorator @prob

    The prob specify the propbability of execution when a property is satisfied.
    """
    p = float(p)
    if not 0 < p <= 1.0:
        raise ValueError("The propbability should between 0 and 1")
    def accept(f):
        @wraps(f)
        def precondition_wrapper(*args, **kwargs):
            return f(*args, **kwargs)

        setattr(precondition_wrapper, PROP_MARKER, p)

        return precondition_wrapper

    return accept


@dataclass
class Options:
    """
    Kea and Fastbot configurations
    """
    # the driver_name in script (if self.d, then d.) 
    driverName: str
    # the driver (only U2Driver available now)
    Driver: AbstractDriver
    # list of package names. Specify the apps under test
    packageNames: List[str]
    # target device
    serial: str = None
    # test agent. "native" for stage 1 and "u2" for stage 1~3
    agent: Literal["u2", "native"] = "u2"
    # max step in exploration (availble in stage 2~3)
    maxStep: Union[str, float] = float("inf")
    # time(mins) for exploration
    running_mins: int = 10
    # time(ms) to wait when exploring the app
    throttle: int = 200


@dataclass
class PropStatistic:
    precond_satisfied: int = 0
    executed: int = 0
    fail: int = 0
    error: int = 0

class PBTTestResult(dict):
    def __getitem__(self, key) -> PropStatistic:
        return super().__getitem__(key)


def getFullPropName(testCase: TestCase):
    return ".".join([
        testCase.__module__,
        testCase.__class__.__name__,
        testCase._testMethodName
    ])

class JsonResult(TextTestResult):
    res: PBTTestResult

    @classmethod
    def setProperties(cls, allProperties: Dict):
        cls.res = dict()
        for testCase in allProperties.values():
            cls.res[getFullPropName(testCase)] = PropStatistic()

    def flushResult(self, outfile):
        json_res = dict()
        for propName, propStatitic in self.res.items():
            json_res[propName] = asdict(propStatitic)
        with open(outfile, "w") as fp:
            json.dump(json_res, fp, indent=4)

    def addExcuted(self, test: TestCase):
        self.res[getFullPropName(test)].executed += 1

    def addPrecondSatisfied(self, test: TestCase):
        self.res[getFullPropName(test)].precond_satisfied += 1

    def addFailure(self, test, err):
        super().addFailure(test, err)
        self.res[getFullPropName(test)].fail += 1

    def addError(self, test, err):
        super().addError(test, err)
        self.res[getFullPropName(test)].error += 1


def activateFastbot(options: Options, port=None) -> threading.Thread:
    """
    activate fastbot.
    :params: options: the running setting for fastbot
    :params: port: the listening port for script driver
    :return: the fastbot daemon thread
    """
    cur_dir = Path(__file__).parent
    push_file(
        Path.joinpath(cur_dir, "assets/monkeyq.jar"),
        "/sdcard/monkeyq.jar",
        device=options.serial
    )
    push_file(
        Path.joinpath(cur_dir, "assets/fastbot-thirdpart.jar"),
        "/sdcard/fastbot-thirdpart.jar",
        device=options.serial,
    )
    push_file(
        Path.joinpath(cur_dir, "assets/framework.jar"), 
        "/sdcard/framework.jar",
        device=options.serial
    )
    push_file(
        Path.joinpath(cur_dir, "assets/fastbot_libs/arm64-v8a"),
        "/data/local/tmp",
        device=options.serial
    )
    push_file(
        Path.joinpath(cur_dir, "assets/fastbot_libs/armeabi-v7a"),
        "/data/local/tmp",
        device=options.serial
    )
    push_file(
        Path.joinpath(cur_dir, "assets/fastbot_libs/x86"),
        "/data/local/tmp",
        device=options.serial
    )
    push_file(
        Path.joinpath(cur_dir, "assets/fastbot_libs/x86_64"),
        "/data/local/tmp",
        device=options.serial
    )

    t = startFastbotService(options)
    print("[INFO] Running Fastbot...")

    return t

def check_alive(port):
    """
    check if the script driver and proxy server are alive.
    """
    for _ in range(10):
        sleep(2)
        try:
            requests.get(f"http://localhost:{port}/ping")
            return
        except requests.ConnectionError:
            print("[INFO] waiting for connection.")
            pass
    raise RuntimeError("Failed to connect fastbot")

def startFastbotService(options: Options) -> threading.Thread:
    shell_command = [
        "CLASSPATH=/sdcard/monkeyq.jar:/sdcard/framework.jar:/sdcard/fastbot-thirdpart.jar",
        "exec", "app_process",
        "/system/bin", "com.android.commands.monkey.Monkey",
        "-p", *options.packageNames,
        "--agent-u2" if options.agent == "u2" else "--agent", 
        "reuseq",
        "--running-minutes", f"{options.running_mins}",
        "--throttle", f"{options.throttle}",
        "-v", "-v", "-v"
    ]

    full_cmd = ["adb"] + (["-s", options.serial] if options.serial else []) + ["shell"] + shell_command

    with open("fastbot.log", "w"):
        pass

    # log file
    outfile = open("fastbot.log", "w")

    print("[INFO] Options info: {}".format(asdict(options)))
    print("[INFO] Launching fastbot with shell command:\n{}".format(" ".join(full_cmd)))
    print("[INFO] Fastbot log will be saved to {}".format(outfile.name))

    # process handler
    proc = subprocess.Popen(full_cmd, stdout=outfile, stderr=outfile)
    t = threading.Thread(target=close_on_exit, args=(proc, outfile), daemon=True)
    t.start()

    return t

def close_on_exit(proc: subprocess.Popen, f: IO):
    proc.wait()
    f.close()
    

class KeaTestRunner(TextTestRunner):

    resultclass: JsonResult
    allProperties: PropertyStore
    options: Options = None

    @classmethod
    def setOptions(cls, options: Options):
        if not isinstance(options.packageNames, list) and len(options.packageNames) > 0:
            raise ValueError("packageNames should be given in a list.")
        if options.Driver is not None and options.agent == "native":
            print("[Warning] Can not use any Driver when runing native mode.")
            options.Driver = None
        cls.options = options

    def run(self, test):

        self.allProperties = dict()
        self.collectAllProperties(test)

        if len(self.allProperties) == 0:
            print("[Warning] No property has been found.")

        JsonResult.setProperties(self.allProperties)
        self.resultclass = JsonResult

        result: JsonResult = self._makeResult()
        registerResult(result)
        result.failfast = self.failfast
        result.buffer = self.buffer
        result.tb_locals = self.tb_locals

        with warnings.catch_warnings():
            if self.warnings:
                # if self.warnings is set, use it to filter all the warnings
                warnings.simplefilter(self.warnings)
                # if the filter is 'default' or 'always', special-case the
                # warnings from the deprecated unittest methods to show them
                # no more than once per module, because they can be fairly
                # noisy.  The -Wd and -Wa flags can be used to bypass this
                # only when self.warnings is None.
                if self.warnings in ["default", "always"]:
                    warnings.filterwarnings(
                        "module",
                        category=DeprecationWarning,
                        message=r"Please use assert\w+ instead.",
                    )

            t = activateFastbot(options=self.options)
            log_watcher = LogWatcher()
            if self.options.agent == "native":
                t.join()
            else:
                # setUp for the u2 driver
                self.scriptDriver = self.options.Driver.getScriptDriver()
                check_alive(port=self.scriptDriver.lport)
                
                end_by_remote = False
                step = 0
                while step < self.options.maxStep:
                    step += 1
                    print("[INFO] Sending monkeyEvent {}".format(
                        f"({step} / {self.options.maxStep})" if self.options.maxStep != float("inf")
                        else f"({step})"
                        )
                    )

                    try:
                        propsSatisfiedPrecond = self.getValidProperties()
                    except requests.ConnectionError:
                        print(
                            "[INFO] Exploration times up (--running-minutes)."
                        )
                        end_by_remote = True
                        break

                    print(f"{len(propsSatisfiedPrecond)} precond satisfied.")

                    # Go to the next round if no precond satisfied
                    if len(propsSatisfiedPrecond) == 0:
                        continue

                    # get the random probability p
                    p = random.random()
                    propsNameFilteredByP = []
                    # filter the properties according to the given p
                    for propName, test in propsSatisfiedPrecond.items():
                        result.addPrecondSatisfied(test)
                        if getattr(test, "p", 1) >= p:
                            propsNameFilteredByP.append(propName)

                    if len(propsNameFilteredByP) == 0:
                        print("Not executed any property due to probability.")
                        continue

                    execPropName = random.choice(propsNameFilteredByP)
                    test = propsSatisfiedPrecond[execPropName]
                    # Dependency Injection. driver when doing scripts
                    self.scriptDriver = self.options.Driver.getScriptDriver()
                    setattr(test, self.options.driverName, self.scriptDriver)
                    print("execute property %s." % execPropName)

                    result.addExcuted(test)
                    try:
                        test(result)
                    finally:
                        result.printErrors()

                    result.flushResult(outfile="result.json")

                if not end_by_remote:
                    self.stopMonkey()
                result.flushResult(outfile="result.json")

            print(f"Finish sending monkey events.")
            log_watcher.close()
            self.tearDown()

        # Source code from unittest Runner
        # process the result
        expectedFails = unexpectedSuccesses = skipped = 0
        try:
            results = map(
                len,
                (result.expectedFailures, result.unexpectedSuccesses, result.skipped),
            )
        except AttributeError:
            pass
        else:
            expectedFails, unexpectedSuccesses, skipped = results

        infos = []
        if not result.wasSuccessful():
            self.stream.write("FAILED")
            failed, errored = len(result.failures), len(result.errors)
            if failed:
                infos.append("failures=%d" % failed)
            if errored:
                infos.append("errors=%d" % errored)
        else:
            self.stream.write("OK")
        if skipped:
            infos.append("skipped=%d" % skipped)
        if expectedFails:
            infos.append("expected failures=%d" % expectedFails)
        if unexpectedSuccesses:
            infos.append("unexpected successes=%d" % unexpectedSuccesses)
        if infos:
            self.stream.writeln(" (%s)" % (", ".join(infos),))
        else:
            self.stream.write("\n")
        self.stream.flush()
        return result

    def stepMonkey(self) -> str:
        """
        send a step monkey request to the server and get the xml string.
        """
        r = requests.get(f"http://localhost:{self.scriptDriver.lport}/stepMonkey")

        res = json.loads(r.content)
        xml_raw = res["result"]
        return xml_raw

    def stopMonkey(self) -> str:
        """
        send a stop monkey request to the server and get the xml string.
        """
        r = requests.get(f"http://localhost:{self.scriptDriver.lport}/stopMonkey")

        res = r.content.decode(encoding="utf-8")
        print(f"[Server INFO] {res}")

    def getValidProperties(self) -> PropertyStore:

        xml_raw = self.stepMonkey()
        staticCheckerDriver = self.options.Driver.getStaticChecker(hierarchy=xml_raw)

        validProps: PropertyStore = dict()
        for propName, test in self.allProperties.items():
            valid = True
            prop = getattr(test, propName)
            # check if all preconds passed
            for precond in prop.preconds:
                # Dependency injection. Static driver checker for precond
                setattr(test, self.options.driverName, staticCheckerDriver)
                # excecute the precond
                if not precond(test):
                    valid = False
                    break
            # if all the precond passed. make it the candidate prop.
            if valid:
                validProps[propName] = test
        return validProps

    def collectAllProperties(self, test: TestSuite):
        """collect all the properties to prepare for PBT
        """

        def remove_setUp(testCase: TestCase):
            """remove the setup function in PBT
            """
            def setUp(self): ...
            testCase.setUp = types.MethodType(setUp, testCase)

        def remove_tearDown(testCase: TestCase):
            """remove the tearDown function in PBT
            """
            def tearDown(self): ...
            testCase = types.MethodType(tearDown, testCase)
        
        def iter_tests(suite):
            for test in suite:
                if isinstance(test, TestSuite):
                    yield from iter_tests(test)
                else:
                    yield test

        # Traverse the TestCase to get all properties
        for t in iter_tests(test):
            testMethodName = t._testMethodName
            # get the test method name and check if it's a property
            testMethod = getattr(t, testMethodName)
            if hasattr(testMethod, PRECONDITIONS_MARKER):
                # remove the hook func in its TestCase
                remove_setUp(t)
                remove_tearDown(t)
                # save it into allProperties for PBT
                self.allProperties[testMethodName] = t

    def tearDown(self):
        # TODO Add tearDown method (remove local port, etc.)
        pass
        