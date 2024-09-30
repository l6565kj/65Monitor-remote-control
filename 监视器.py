import cv2
import numpy as np
import pyautogui
from flask import Flask, Response, render_template, jsonify, request
import time

app = Flask(__name__)

def draw_mouse_pointer(frame):
    # 获取当前鼠标位置
    x, y = pyautogui.position()
    
    # 设置鼠标指针的颜色和大小
    pointer_color = (0, 255, 0)  # 绿色
    pointer_radius = 5

    # 绘制鼠标指针（圆形）
    cv2.circle(frame, (x, y), pointer_radius, pointer_color, -1)

def generate_frames():
    # 获取屏幕尺寸
    screen_width, screen_height = pyautogui.size()
    
    # 计算新的宽高比例
    target_short_edge = 1100
    if screen_width < screen_height:
        # 短边为宽
        new_width = target_short_edge
        new_height = int((screen_height / screen_width) * target_short_edge)
    else:
        # 短边为高
        new_height = target_short_edge
        new_width = int((screen_width / screen_height) * target_short_edge)

    while True:
        # 捕获屏幕
        screenshot = pyautogui.screenshot()
        frame = np.array(screenshot)
        frame = cv2.cvtColor(frame, cv2.COLOR_RGB2BGR)

        # 绘制鼠标指针
        draw_mouse_pointer(frame)

        # 调整帧大小
        frame = cv2.resize(frame, (new_width, new_height))

        # 使用 H.264 编码（需要在系统上安装 ffmpeg）
        encode_param = [int(cv2.IMWRITE_JPEG_QUALITY), 70]  # 降低质量以加快编码
        result, encoded_image = cv2.imencode('.jpg', frame, encode_param)

        if result:
            # 减少延迟
            time.sleep(0.02)  # 大约50 FPS
            yield (b'--frame\r\n'
                   b'Content-Type: image/jpeg\r\n\r\n' + 
                   encoded_image.tobytes() + b'\r\n')

@app.route('/')
def index():
    return render_template('index.html')

@app.route('/6565TECH')
def video_feed():
    return Response(generate_frames(),
                    mimetype='multipart/x-mixed-replace; boundary=frame')

@app.route('/Signal')
def signal_status():
    return "Connected"

@app.route('/resolution')
def get_resolution():
    # 获取当前屏幕分辨率
    screen_width, screen_height = pyautogui.size()
    return jsonify({'width': screen_width, 'height': screen_height})

@app.route('/<path:filename>')
def render_html(filename):
    try:
        return render_template(f"{filename}")
    except Exception as e:
        return jsonify({'error': str(e)}), 404

# 错误处理
@app.errorhandler(404)
def not_found_error(error):
    return redirect(url_for('error_page', message="404 Not Found: The page you are looking for does not exist."))

@app.errorhandler(500)
def internal_error(error):
    return redirect(url_for('error_page', message="500 Internal Server Error: An unexpected error occurred."))

@app.route('/error')
def error_page():
    message = request.args.get('message', 'An unexpected error occurred.')
    return render_template('error.html', message=message)

# 新增接口：移动鼠标到指定坐标
@app.route('/move_mouse', methods=['POST'])
def move_mouse():
    data = request.json
    x = data.get('x')
    y = data.get('y')

    if x is None or y is None:
        return jsonify({'error': 'Missing x or y parameter'}), 400

    try:
        pyautogui.moveTo(x, y)
        return jsonify({'status': 'Mouse moved', 'x': x, 'y': y}), 200
    except Exception as e:
        return jsonify({'error': str(e)}), 500

# 新增接口：按下指定键或鼠标按键
@app.route('/press_key_or_mouse', methods=['POST'])
def press_key_or_mouse():
    data = request.json
    key = data.get('key')
    button = data.get('button')

    if key:
        try:
            pyautogui.press(key)
            return jsonify({'status': 'Key pressed', 'key': key}), 200
        except Exception as e:
            return jsonify({'error': str(e)}), 500
    elif button:
        try:
            pyautogui.click(button=button)
            return jsonify({'status': 'Mouse button clicked', 'button': button}), 200
        except Exception as e:
            return jsonify({'error': str(e)}), 500
    else:
        return jsonify({'error': 'Missing key or button parameter'}), 400

if __name__ == '__main__':
    app.run(host='0.0.0.0', port=9383, threaded=True)
