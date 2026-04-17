import sys
import os
import urllib.request
import subprocess
import time
import tempfile
import signal

# ==============================================================================
# MANDATE: CONTROLLED POPUP BROWSER ONLY
# This script utilizes Playwright to render MetaClaw framework documentation.
# It allows us to synchronize the terminal setup sequence with HTML guides,
# ensuring we have real control over the synchronization between the terminal
# and the HTML pages being shown.
#
# CRITICAL: Do NOT use this script for opening the OpenClaw Agent Dashboard
# (e.g., 'make gui' or 'make gui-setup'). The agent dashboard must ALWAYS open
# in the user's native, personal web browser via the OS-native command.
# ==============================================================================

# Suppress Node deprecation warnings from the underlying Playwright installation
os.environ["NODE_NO_WARNINGS"] = "1"

from playwright.sync_api import sync_playwright

PORT = 18790
USER_DATA_DIR = os.path.join(tempfile.gettempdir(), 'metaclaw_browser_data')

def is_browser_running():
  try:
    urllib.request.urlopen(f"http://127.0.0.1:{PORT}/json/version", timeout=1)
    return True
  except:
    return False

def kill_browser_on_port(port):
  """Forcefully kills any zombie process holding the CDP debugging port hostage."""
  try:
    if sys.platform == 'win32':
      cmd = f'netstat -ano | findstr LISTENING | findstr :{port}'
      result = subprocess.run(cmd, shell=True, capture_output=True, text=True)
      for line in result.stdout.strip().split('\n'):
        if f':{port}' in line:
          pid = line.strip().split()[-1]
          subprocess.run(f'taskkill /F /PID {pid}', shell=True, stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL)
    else:
      cmd = f'lsof -t -i TCP:{port}'
      result = subprocess.run(cmd, shell=True, capture_output=True, text=True)
      for pid_str in result.stdout.strip().split('\n'):
        if pid_str.isdigit():
          os.kill(int(pid_str), signal.SIGKILL)
  except Exception as e:
    print(f"[Browser] Error during forceful cleanup: {e}")

def get_system_chrome():
  if sys.platform == 'win32':
    paths = [
      r"C:\Program Files\Google\Chrome\Application\chrome.exe",
      r"C:\Program Files (x86)\Google\Chrome\Application\chrome.exe",
      r"C:\Program Files\Microsoft\Edge\Application\msedge.exe",
      r"C:\Program Files\BraveSoftware\Brave-Browser\Application\brave.exe"
    ]
  elif sys.platform == 'darwin':
    paths = [
      "/Applications/Google Chrome.app/Contents/MacOS/Google Chrome",
      "/Applications/Brave Browser.app/Contents/MacOS/Brave Browser",
      "/Applications/Microsoft Edge.app/Contents/MacOS/Microsoft Edge",
      "/Applications/Chromium.app/Contents/MacOS/Chromium"
    ]
  else:
    paths = [
      "/usr/bin/google-chrome",
      "/usr/bin/google-chrome-stable",
      "/usr/bin/chromium-browser",
      "/usr/bin/chromium",
      "/usr/bin/brave-browser",
      "/usr/bin/microsoft-edge-stable"
    ]
  for p in paths:
    if os.path.exists(p):
      return p
  return None

def main():
  close_flag = '--close' in sys.argv
  urls = [arg for arg in sys.argv[1:] if not arg.startswith('--')]
  url = urls[0] if urls else None

  with sync_playwright() as p:
    if close_flag:
      if is_browser_running():
        try:
          browser = p.chromium.connect_over_cdp(f"http://127.0.0.1:{PORT}")
          context = browser.contexts[0]
          page = context.pages[0] if context.pages else context.new_page()
          client = context.new_cdp_session(page)
          client.send("Browser.close")
          print("[Browser] Teardown complete via CDP.")
        except Exception as e:
          print(f"[Browser] Error closing background instance via CDP: {e}")

      # Always enforce a hard port kill to catch headless zombies
      kill_browser_on_port(PORT)
      return

    if not url:
      return

    if not is_browser_running():
      # Clean up any dead port holders before spawning a fresh instance
      kill_browser_on_port(PORT)

      executable = get_system_chrome() or p.chromium.executable_path
      args = [
        executable,
        f'--remote-debugging-port={PORT}',
        f'--user-data-dir={USER_DATA_DIR}',
        '--no-first-run',
        '--no-default-browser-check',
        '--window-position=328,0',
        '--window-size=800,1000',
        url
      ]

      if sys.platform == 'win32':
        # 0x00000008 represents DETACHED_PROCESS to fully detach the child process on Windows
        subprocess.Popen(args, creationflags=subprocess.CREATE_NEW_PROCESS_GROUP | 0x00000008, stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL)
      else:
        # start_new_session=True creates a new process group on POSIX systems
        subprocess.Popen(args, start_new_session=True, stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL)

      for _ in range(20):
        if is_browser_running():
          break
        time.sleep(0.5)

      return

    try:
      browser = p.chromium.connect_over_cdp(f"http://127.0.0.1:{PORT}")
      context = browser.contexts[0]
      page = context.pages[0] if context.pages else context.new_page()

      # MANDATE: Do NOT call page.bring_to_front() here.
      # It steals OS-level keyboard focus from the user's terminal.
      # The browser is brought to front only once when initially spawned via subprocess.
      page.goto(url)

      if '#' in url:
        fragment = url.split('#', 1)[1]
        page.evaluate(f"document.getElementById('{fragment}')?.scrollIntoView()")

    except Exception as e:
      print(f"[Browser] Error interacting with daemon: {e}")

if __name__ == '__main__':
  main()
