"""Local Selenium controller. Credentials stay in the browser, never read by this app."""
import json
import os
import queue
import threading
import time
import webbrowser
from datetime import datetime, timezone
from http.server import BaseHTTPRequestHandler, ThreadingHTTPServer
from pathlib import Path
from urllib.parse import urlparse

ROOT = Path(__file__).resolve().parent
DATA = ROOT / 'data'
COMMANDS = queue.Queue()
STOP = threading.Event()
LOCK = threading.RLock()
STATE = dict(phase='opening', message='Đang mở Chrome…', ready=False, running=False, posts=0, comments=0, target=20, source='', results=[])
STATE['version'] = '2.4-startup-timeout'
ROWS = {}
HELPERS = (ROOT.parent / 'extension' / 'helpers.js').read_text(encoding='utf-8')
DOM = (ROOT / 'dom.js').read_text(encoding='utf-8')

def update(**values):
    with LOCK:
        STATE.update(values)

def payload():
    with LOCK:
        return dict(schema_version=1, source=STATE['source'], completeness='not_verified', posts=list(STATE['results']), rows=list(ROWS.values()))

def save():
    DATA.mkdir(exist_ok=True)
    temp = DATA / 'progress.tmp'
    temp.write_text(json.dumps(payload(), ensure_ascii=False, indent=2), encoding='utf-8')
    temp.replace(DATA / 'progress.json')

def restore():
    file = DATA / 'progress.json'
    if file.exists():
        data = json.loads(file.read_text(encoding='utf-8'))
        for row in data.get('rows', []):
            ROWS[(row['post_id'], row['comment_id'])] = row
        results = data.get('posts', [])
        update(source=data.get('source', ''), results=results, posts=len(results), comments=len(ROWS))

def navigate(driver, url):
    """A slow image/feed must not destroy an otherwise usable browser session."""
    from selenium.common.exceptions import TimeoutException
    try:
        driver.get(url)
    except TimeoutException:
        # Facebook may keep loading resources long after its page is usable.
        # Continue only if the browser still responds and reached the requested host.
        driver.execute_script('window.stop();')
        current = urlparse(driver.current_url)
        expected = urlparse(url)
        if current.hostname != expected.hostname:
            raise RuntimeError('Trang tải quá lâu và chưa tới Facebook. Kiểm tra mạng rồi mở lại công cụ.')
        driver.execute_script('return document.readyState;')
        update(message='Facebook tải chậm; đã giữ phiên Chrome. Chờ trang hiển thị rồi tiếp tục.')

def scope_url(url):
    parsed = urlparse(url)
    if parsed.scheme != 'https' or not (parsed.hostname == 'facebook.com' or (parsed.hostname or '').endswith('.facebook.com')):
        return False
    parts = parsed.path.strip('/').split('/')
    return bool(parts[0]) and not any(x in parts for x in ('posts', 'permalink', 'login', 'checkpoint', 'watch', 'reel', 'reels')) and (parts[0] != 'groups' or len(parts) >= 2)

def run_batch(driver):
    target = STATE['target']
    source = driver.current_url
    if not scope_url(source):
        update(message='Hãy vào trang nhóm hoặc fanpage trong Chrome của công cụ, rồi bấm Bắt đầu.', phase='ready', running=False)
        return
    with LOCK:
        previous_source = STATE['source']
        if previous_source != source:
            STATE['results'] = []
        STATE.update(source=source, running=True, phase='discovering', posts=0)
    feed_handle = driver.current_window_handle
    posts = {}
    stale = 0
    try:
        for _ in range(max(60, target * 3)):
            if STOP.is_set():
                break
            driver.execute_script(HELPERS)
            result = driver.execute_script(DOM, 'feed', '')
            if not result.get('posts') and not result.get('blocked'):
                # Facebook can populate the timestamp href only after pointer hover.
                from selenium.webdriver.common.action_chains import ActionChains
                for element in driver.execute_script(DOM, 'feed_hover', ''):
                    if STOP.is_set():
                        break
                    try:
                        ActionChains(driver).move_to_element(element).perform()
                        STOP.wait(0.3)
                    except Exception:
                        continue
                result = driver.execute_script(DOM, 'feed', '')
            if result.get('blocked'):
                raise RuntimeError('Facebook yêu cầu đăng nhập/xác minh hoặc đang hạn chế. Đã dừng.')
            before = len(posts)
            for post in result.get('posts', []):
                posts.setdefault(post['id'], post)
            diag = result.get('diagnostics', {})
            update(message=f'Tìm được {min(len(posts),target)}/{target} bài · đọc {diag.get("anchors",0)} link, {diag.get("articles",0)} khối bài, {diag.get("candidates",0)} permalink nhận diện. Bản 2.3.')
            if len(posts) >= target:
                break
            step = driver.execute_script(DOM, 'feed_scroll', '')
            stale = stale + 1 if len(posts) == before and not step.get('moved') else 0
            if stale >= 5:
                break
            if STOP.wait(2.5):
                break
        chosen = list(posts.values())[:target]
        if not chosen and not STOP.is_set():
            raise RuntimeError('Không nhận diện được link bài trong nhóm/trang. Chưa thu thập bài nào.')
        completed = {r['post_id'] for r in STATE['results'] if r.get('reason') == 'no_progress'}
        for index, post in enumerate(chosen, 1):
            if STOP.is_set():
                break
            if post['id'] in completed:
                update(posts=index, message=f'Bỏ qua bài {index}: đã xử lý lần trước.')
                continue
            reason = 'time_limit'
            update(phase='collecting', message=f'Bài {index}/{len(chosen)}: đang tải bình luận…')
            driver.switch_to.new_window('tab')
            try:
                navigate(driver, post['url'])
                if STOP.wait(3):
                    reason = 'user_stop'
                else:
                    started = time.monotonic()
                    stale = 0
                    missing = 0
                    while not STOP.is_set() and time.monotonic() - started < 180:
                        driver.execute_script(HELPERS)
                        result = driver.execute_script(DOM, 'read', post['id'])
                        if result.get('blocked'):
                            raise RuntimeError('Gặp đăng nhập/xác minh/hạn chế. Dừng toàn phiên, dữ liệu được giữ.')
                        if result.get('wrong_source'):
                            raise RuntimeError('Nguồn bài thay đổi. Dừng để tránh gán nhầm dữ liệu.')
                        if result.get('missing_scope'):
                            missing += 1
                            if missing >= 5:
                                reason = 'unrecognized_scope'
                                break
                            if STOP.wait(2.5):
                                break
                            continue
                        missing = 0
                        before = len(ROWS)
                        with LOCK:
                            for item in result.get('rows', []):
                                key = (post['id'], item['comment_id'])
                                if key in ROWS:
                                    if len(item['text_raw']) > len(ROWS[key]['text_raw']):
                                        ROWS[key]['text_raw'] = item['text_raw']
                                    continue
                                if len(ROWS) >= 10000:
                                    break
                                ROWS[key] = dict(item, post_id=post['id'], post_url=post['url'], label='', annotation_note='', collection_method='selenium_auto', collected_at=datetime.now(timezone.utc).isoformat(), comment_filter='unknown')
                            STATE['comments'] = len(ROWS)
                        save()
                        if len(ROWS) >= 10000:
                            reason = 'dataset_limit'
                            STOP.set()
                            break
                        if STOP.is_set():
                            break
                        step = driver.execute_script(DOM, 'advance', post['id'])
                        if step.get('blocked') or step.get('wrong_source'):
                            raise RuntimeError('Gặp hạn chế hoặc đổi bài khi tải. Đã dừng.')
                        if step.get('missing_scroll'):
                            reason = 'unrecognized_scroll'
                            break
                        stale = stale + 1 if len(ROWS) == before and not step.get('moved') and not step.get('clicked') else 0
                        if stale >= 5:
                            reason = 'no_progress'
                            break
                        update(message=f'Bài {index}/{len(chosen)} · {len(ROWS)} bình luận trong bộ dữ liệu. Đang tự cuộn/tải thêm…')
                        if STOP.wait(2.5):
                            break
                    if STOP.is_set() and reason != 'dataset_limit':
                        reason = 'user_stop'
            finally:
                driver.close()
                driver.switch_to.window(feed_handle)
            with LOCK:
                STATE['results'] = [r for r in STATE['results'] if r['post_id'] != post['id']]
                STATE['results'].append(dict(post_id=post['id'], url=post['url'], reason=reason, count=sum(r['post_id'] == post['id'] for r in ROWS.values()), completeness='not_verified'))
            update(posts=index)
            save()
            if STOP.wait(2):
                break
        update(phase='ready', message='Đã dừng theo yêu cầu.' if STOP.is_set() else f'Đã xử lý {STATE["posts"]}/{len(chosen)} bài. Không xác nhận đã lấy đủ bình luận.')
    except Exception as error:
        update(phase='error', message=str(error))
        save()
    finally:
        update(running=False)

def worker():
    driver = None
    try:
        from selenium import webdriver
        from selenium.webdriver.chrome.service import Service
        from selenium.webdriver.common.selenium_manager import SeleniumManager
        restore()
        options = webdriver.ChromeOptions()
        options.page_load_strategy = 'eager'
        options.add_argument('--start-maximized')
        options.add_argument('--user-data-dir=' + str(ROOT / 'chrome-profile'))
        # Resolve explicitly, ignoring obsolete chromedriver.exe on PATH.
        os.environ.pop('SE_CHROMEDRIVER', None)
        chrome = Path(os.environ.get('PROGRAMFILES', r'C:\Program Files')) / 'Google/Chrome/Application/chrome.exe'
        args = ['--browser', 'chrome', '--skip-driver-in-path', '--cache-path', str(ROOT / 'driver-cache')]
        if chrome.exists():
            options.binary_location = str(chrome)
            args.extend(['--browser-path', str(chrome)])
        update(message='Đang tìm/tải ChromeDriver phù hợp với Chrome. Cần Internet lần đầu…')
        resolved = SeleniumManager().binary_paths(args)
        if not options.binary_location and resolved.get('browser_path'):
            options.binary_location = resolved['browser_path']
        driver = webdriver.Chrome(service=Service(executable_path=resolved['driver_path']), options=options)
        driver.set_page_load_timeout(35)
        navigate(driver, 'https://www.facebook.com/')
        update(ready=True, phase='ready', message='Tự đăng nhập và vào nhóm/trang trong Chrome vừa mở. Sau đó bấm Bắt đầu.')
        while True:
            command = COMMANDS.get()
            if command == 'quit':
                break
            if command == 'start':
                run_batch(driver)
    except Exception as error:
        DATA.mkdir(exist_ok=True)
        (DATA / 'startup-error.txt').write_text(str(error), encoding='utf-8')
        summary = str(error).split('Stacktrace:')[0].strip()[:700]
        update(ready=False, running=False, phase='error', message=f'Không mở/điều khiển được Chrome: {summary}. Chi tiết trong selenium/data/startup-error.txt. Đóng công cụ rồi mở lại. Nếu lỗi timeout, kiểm tra kết nối mạng; tải driver chỉ cần Internet khi chưa có driver phù hợp.')
    finally:
        if driver:
            driver.quit()

class Handler(BaseHTTPRequestHandler):
    def log_message(self, *args):
        pass

    def send(self, content, kind, code=200, filename=None):
        self.send_response(code)
        self.send_header('Content-Type', kind)
        self.send_header('Cache-Control', 'no-store')
        if filename:
            self.send_header('Content-Disposition', f'attachment; filename="{filename}"')
        self.send_header('Content-Length', str(len(content)))
        self.end_headers()
        self.wfile.write(content)

    def do_GET(self):
        if self.path == '/':
            html = (ROOT / 'index.html').read_text(encoding='utf-8')
            html += '<script>' + (ROOT / 'count-control.js').read_text(encoding='utf-8') + '</script>'
            self.send(html.encode(), 'text/html;charset=utf-8')
        elif self.path == '/status':
            with LOCK:
                body = json.dumps(STATE, ensure_ascii=False).encode()
            self.send(body, 'application/json;charset=utf-8')
        elif self.path == '/download':
            self.send(json.dumps(payload(), ensure_ascii=False, indent=2).encode(), 'application/json;charset=utf-8', filename='ptit_selenium_comments.json')
        else:
            self.send(b'Not found', 'text/plain', 404)

    def do_POST(self):
        # Browser pages from another origin cannot start automation on this local service.
        if self.headers.get('Origin') != 'http://127.0.0.1:8767':
            self.send(b'Forbidden', 'text/plain', 403)
            return
        if self.path == '/start':
            try:
                length = int(self.headers.get('Content-Length', '0'))
                if not 0 < length <= 1024:
                    raise ValueError()
                body = json.loads(self.rfile.read(length))
                target = body.get('target')
                if type(target) is not int or not 1 <= target <= 500:
                    raise ValueError()
            except (ValueError, TypeError, AttributeError):
                self.send('Số bài phải là số nguyên từ 1 đến 500.'.encode(), 'text/plain;charset=utf-8', 400)
                return
            with LOCK:
                if not STATE['ready'] or STATE['running']:
                    self.send(b'Not ready', 'text/plain', 409)
                    return
                STATE['target'] = target
                STATE['running'] = True
                STATE['message'] = 'Đang bắt đầu…'
                STOP.clear()
            COMMANDS.put('start')
        elif self.path == '/stop':
            STOP.set()
        else:
            self.send(b'Not found', 'text/plain', 404)
            return
        self.send(b'{}', 'application/json')

if __name__ == '__main__':
    try:
        server = ThreadingHTTPServer(('127.0.0.1', 8767), Handler)
    except OSError:
        print('Cong 8767 dang bi chiem. Hay dong cua so MO_CONG_CU.cmd cu (Ctrl+C), roi mo lai. Dong tab web khong tat chuong trinh cu.')
        raise SystemExit(1)
    threading.Thread(target=worker, daemon=True).start()
    webbrowser.open('http://127.0.0.1:8767/')
    try:
        server.serve_forever()
    except KeyboardInterrupt:
        STOP.set()
        COMMANDS.put('quit')
    finally:
        server.server_close()
