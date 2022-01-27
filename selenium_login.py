from selenium import webdriver
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.common.desired_capabilities import DesiredCapabilities
from selenium.common.exceptions import TimeoutException, WebDriverException
import os
import subprocess
import sys

from math import inf as infinity

try:
    assert __file__
except (NameError, AssertionError):
    print("Please import selenium_login, don't run it directly!")
    sys.exit()


def loadBrowser():

    chrome_binary = os.path.join(os.path.split(__file__)[0], r"chrome/bin/chrome.exe")
    chrome_updater = os.path.join(os.path.split(__file__)[0], "chrome/chrlauncher 2.5.4 (64-bit).exe")
    chromedriver_binary = os.path.join(os.path.split(__file__)[0], "chrome/bin/chromedriver.exe")

    sys.path.append(os.path.split(__file__)[0])

    if not os.path.exists(chrome_binary):
        assert os.path.exists(chrome_updater)
        subprocess.run([chrome_updater])

    capabilities = {
        'browserName': 'chrome',
        # 'logPrefs': "PERFORMANCE",
        'loggingPrefs': {"performance": "ALL"},
        'goog:loggingPrefs': {"performance": "ALL"},
        'goog:chromeOptions': {'perfLoggingPrefs': {'enableNetwork': True}},
        "chromeOptions": {
            "binary": chrome_binary
        }
    }

    browser = webdriver.Chrome(
        desired_capabilities=capabilities,
        executable_path=chromedriver_binary
    )
    browser.set_window_size(850, 930)
    return browser


def login(start, until, giveinstance=False):
    try:
        browser = loadBrowser()

        browser.get(start)
        try:
            # Login
            WebDriverWait(browser, timeout=infinity).until(until)
            print("Done.")
        except TimeoutException:
            print("Time out! Go faster next time. ")
            browser.quit()
            raise

        sessiondata = {
            "cookies": {c['name']: c['value'] for c in browser.get_cookies()},
            "localStorage": browser.execute_script("return window.localStorage"),
            "sessionStorage": browser.execute_script("return window.sessionStorage"),
            "location": browser.execute_script("return window.location.href")
        }
    except WebDriverException:
        import pyperclip
        print(f"Fallback: Please copy cookies.txt from site {start} and press enter.")
        input()
        cookiestxt = pyperclip.paste()

        browser = False

        cookies = {}
        for line in cookiestxt.split("\n"):
            if line.startswith("#"):
                continue
            domain, __, subdir, __, __, name, value = line.split("\t")
            cookies[name] = value

        sessiondata = {
            "cookies": cookies,
            "localStorage": "UNIMPLEMENTED",
            "sessionStorage": "UNIMPLEMENTED",
            "location": "UNIMPLEMENTED"
        }
    if giveinstance:
        return browser
    else:
        if browser:
            browser.quit()
        return sessiondata