import re
import os
import threading
import time
import typing


PATTERN_EXCEPTION = re.compile(r"\[Fastbot\].+Internal\serror\n([\s\S]*)")
PATTERN_STATISTIC = re.compile(r".+Monkey\sis\sover!\n([\s\S]+)")
PATTERN_COVERAGE = re.compile(r"(.+Activity\sof\sCoverage.+)")


def thread_excepthook(args):
    print(args.exc_value)
    os._exit(1)


class LogWatcher:

    def watcher(self, poll_interval=1):
        self.buffer = ""
        self.buffer_lines = list()
        self.last_pos = 0
        self.keywords = {
            "Internal error",
            "Monkey is over!",
            "Activity of Coverage",
        }

        with open(self.log_path, "r", encoding="utf-8") as fp:
            while True:
                self.read_log(fp)
                time.sleep(poll_interval)
        
    def read_log(self, fp: typing.IO):
        capture = False
        fp.seek(self.last_pos)
        for line in fp:
            if not capture and any(kw in line for kw in self.keywords):
                time.sleep(0.01)
                capture = True
            if capture:
                self.buffer_lines.append(line)
        capture = False

        self.last_pos = fp.tell()

        if self.buffer_lines:
            self.parse_log("".join(self.buffer_lines))
            self.buffer_lines.clear()

        # time.sleep(poll_interval)
        # fp.seek(self.last_pos)
        # new_data = fp.read()
        # self.last_pos = fp.tell()

        # if new_data:
        #     self.buffer += new_data
        # self.parse_log()

    def parse_log(self, buffer):
        exception_match = PATTERN_EXCEPTION.search(buffer)
        if exception_match:
            exception_body = exception_match.group(1).strip()
            if exception_body:
                raise RuntimeError(
                    "[Error] Execption while running fastbot:\n" + 
                    exception_body + 
                    "\nSee fastbot.log for details."
                )
        coverage_match = PATTERN_COVERAGE.search(buffer)
        if coverage_match:
            coverage_body = coverage_match.group(1).strip()
            if coverage_body:
                print(
                    "[INFO] Cov info:\n" + 
                    coverage_body
                )
        statistic_match = PATTERN_STATISTIC.search(buffer)
        if statistic_match:
            statistic_body = statistic_match.group(1).strip()
            if statistic_body:
                print(
                    "[INFO] Fastbot exit:\n" + 
                    statistic_body
                )

    def __init__(self):
        self.log_path = "fastbot.log"
        # self.watcher()

        threading.excepthook = thread_excepthook
        t = threading.Thread(target=self.watcher, daemon=True)
        t.start()
    
    def close(self):
        time.sleep(0.2) 
        with open("fastbot.log", "r") as fp:
            self.read_log(fp)


if __name__ == "__main__":
    LogWatcher()