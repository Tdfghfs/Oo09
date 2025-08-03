from flask import Flask, request, jsonify, render_template_string
from flask_cors import CORS
import subprocess
import os
import tempfile
import threading
import time
import uuid
import signal
import sys

app = Flask(__name__)
CORS(app)  # تمكين CORS للسماح بالطلبات من أي مصدر

# قاموس لتخزين العمليات النشطة
active_processes = {}

# مجلد لحفظ الملفات المرفوعة
UPLOAD_FOLDER = 'uploads'
if not os.path.exists(UPLOAD_FOLDER):
    os.makedirs(UPLOAD_FOLDER)

# HTML template للواجهة الأمامية
HTML_TEMPLATE = '''
<!DOCTYPE html>
<html lang="ar" dir="rtl">
<head>
    <meta charset="UTF-8">
    <meta name="viewport" content="width=device-width, initial-scale=1.0">
    <title>واجهة الترمنال الويب</title>
    <script src="https://cdn.jsdelivr.net/npm/xterm@5.3.0/lib/xterm.js"></script>
    <script src="https://cdn.jsdelivr.net/npm/xterm-addon-fit@0.8.0/lib/xterm-addon-fit.js"></script>
    <link rel="stylesheet" href="https://cdn.jsdelivr.net/npm/xterm@5.3.0/css/xterm.css" />
    <style>
        body {
            font-family: 'Segoe UI', Tahoma, Geneva, Verdana, sans-serif;
            margin: 0;
            padding: 20px;
            background-color: #1e1e1e;
            color: #ffffff;
        }
        .container {
            max-width: 1200px;
            margin: 0 auto;
        }
        .header {
            text-align: center;
            margin-bottom: 20px;
        }
        .controls {
            display: flex;
            gap: 10px;
            margin-bottom: 20px;
            flex-wrap: wrap;
        }
        .control-group {
            display: flex;
            gap: 10px;
            align-items: center;
        }
        button {
            background-color: #007acc;
            color: white;
            border: none;
            padding: 10px 15px;
            border-radius: 5px;
            cursor: pointer;
            font-size: 14px;
        }
        button:hover {
            background-color: #005a9e;
        }
        input[type="file"], input[type="text"] {
            padding: 8px;
            border: 1px solid #555;
            border-radius: 5px;
            background-color: #2d2d2d;
            color: white;
        }
        .terminal-container {
            background-color: #000;
            border-radius: 5px;
            padding: 10px;
            height: 500px;
            overflow: hidden;
        }
        .python-editor {
            margin-top: 20px;
        }
        textarea {
            width: 100%;
            height: 200px;
            background-color: #2d2d2d;
            color: white;
            border: 1px solid #555;
            border-radius: 5px;
            padding: 10px;
            font-family: 'Courier New', monospace;
            resize: vertical;
        }
        .status {
            margin-top: 10px;
            padding: 10px;
            border-radius: 5px;
            display: none;
        }
        .status.success {
            background-color: #4caf50;
            color: white;
        }
        .status.error {
            background-color: #f44336;
            color: white;
        }
    </style>
</head>
<body>
    <div class="container">
        <div class="header">
            <h1>واجهة الترمنال الويب</h1>
            <p>تشغيل أوامر الشل وأكواد بايثون مع رفع الملفات</p>
        </div>
        
        <div class="controls">
            <div class="control-group">
                <input type="file" id="fileInput" multiple>
                <button onclick="uploadFiles()">رفع الملفات</button>
            </div>
            <div class="control-group">
                <input type="text" id="commandInput" placeholder="أدخل أمر الشل هنا..." style="width: 300px;">
                <button onclick="executeCommand()">تنفيذ الأمر</button>
            </div>
            <div class="control-group">
                <button onclick="clearTerminal()">مسح الشاشة</button>
                <button onclick="listFiles()">عرض الملفات</button>
            </div>
        </div>
        
        <div class="terminal-container">
            <div id="terminal"></div>
        </div>
        
        <div class="python-editor">
            <h3>محرر أكواد بايثون</h3>
            <textarea id="pythonCode" placeholder="اكتب كود بايثون هنا...">print('مرحبا من بايثون!')
for i in range(5):
    print(f'السطر {i+1}')</textarea>
            <br>
            <button onclick="executePython()">تشغيل كود بايثون</button>
            <button onclick="installPackage()">تثبيت مكتبة</button>
        </div>
        
        <div id="status" class="status"></div>
    </div>

    <script>
        // إعداد الترمنال
        const terminal = new Terminal({
            theme: {
                background: '#000000',
                foreground: '#ffffff',
                cursor: '#ffffff'
            },
            fontSize: 14,
            fontFamily: 'Courier New, monospace'
        });
        
        const fitAddon = new FitAddon.FitAddon();
        terminal.loadAddon(fitAddon);
        terminal.open(document.getElementById('terminal'));
        fitAddon.fit();
        
        // رسالة ترحيب
        terminal.writeln('مرحبا بك في واجهة الترمنال الويب');
        terminal.writeln('يمكنك تشغيل أوامر الشل وأكواد بايثون ورفع الملفات');
        terminal.writeln('استخدم الأزرار أعلاه أو اكتب الأوامر مباشرة');
        terminal.writeln('');
        
        // تنفيذ أمر شل
        function executeCommand() {
            const command = document.getElementById('commandInput').value;
            if (!command.trim()) return;
            
            terminal.writeln(`$ ${command}`);
            
            fetch('/execute', {
                method: 'POST',
                headers: {
                    'Content-Type': 'application/json',
                },
                body: JSON.stringify({command: command})
            })
            .then(response => response.json())
            .then(data => {
                if (data.output) {
                    terminal.writeln(data.output);
                }
                if (data.error) {
                    terminal.writeln(`خطأ: ${data.error}`);
                }
                terminal.writeln('');
            })
            .catch(error => {
                terminal.writeln(`خطأ في الاتصال: ${error}`);
                terminal.writeln('');
            });
            
            document.getElementById('commandInput').value = '';
        }
        
        // تشغيل كود بايثون
        function executePython() {
            const code = document.getElementById('pythonCode').value;
            if (!code.trim()) return;
            
            terminal.writeln('>>> تشغيل كود بايثون...');
            
            fetch('/python', {
                method: 'POST',
                headers: {
                    'Content-Type': 'application/json',
                },
                body: JSON.stringify({code: code})
            })
            .then(response => response.json())
            .then(data => {
                if (data.output) {
                    terminal.writeln(data.output);
                }
                if (data.error) {
                    terminal.writeln(`خطأ: ${data.error}`);
                }
                terminal.writeln('');
            })
            .catch(error => {
                terminal.writeln(`خطأ في الاتصال: ${error}`);
                terminal.writeln('');
            });
        }
        
        // رفع الملفات
        function uploadFiles() {
            const fileInput = document.getElementById('fileInput');
            const files = fileInput.files;
            
            if (files.length === 0) {
                showStatus('يرجى اختيار ملف أو أكثر للرفع', 'error');
                return;
            }
            
            const formData = new FormData();
            for (let i = 0; i < files.length; i++) {
                formData.append('files', files[i]);
            }
            
            fetch('/upload', {
                method: 'POST',
                body: formData
            })
            .then(response => response.json())
            .then(data => {
                if (data.success) {
                    terminal.writeln(`تم رفع الملفات بنجاح: ${data.files.join(', ')}`);
                    terminal.writeln('');
                    showStatus('تم رفع الملفات بنجاح', 'success');
                } else {
                    terminal.writeln(`خطأ في رفع الملفات: ${data.error}`);
                    terminal.writeln('');
                    showStatus('خطأ في رفع الملفات', 'error');
                }
            })
            .catch(error => {
                terminal.writeln(`خطأ في الاتصال: ${error}`);
                terminal.writeln('');
                showStatus('خطأ في الاتصال', 'error');
            });
            
            fileInput.value = '';
        }
        
        // مسح الترمنال
        function clearTerminal() {
            terminal.clear();
        }
        
        // عرض الملفات
        function listFiles() {
            executeCommandDirect('ls -la uploads/');
        }
        
        // تثبيت مكتبة
        function installPackage() {
            const packageName = prompt('أدخل اسم المكتبة المراد تثبيتها:');
            if (packageName) {
                terminal.writeln(`>>> تثبيت مكتبة ${packageName}...`);
                executeCommandDirect(`pip install ${packageName}`);
            }
        }
        
        // تنفيذ أمر مباشر
        function executeCommandDirect(command) {
            fetch('/execute', {
                method: 'POST',
                headers: {
                    'Content-Type': 'application/json',
                },
                body: JSON.stringify({command: command})
            })
            .then(response => response.json())
            .then(data => {
                if (data.output) {
                    terminal.writeln(data.output);
                }
                if (data.error) {
                    terminal.writeln(`خطأ: ${data.error}`);
                }
                terminal.writeln('');
            });
        }
        
        // عرض رسالة الحالة
        function showStatus(message, type) {
            const status = document.getElementById('status');
            status.textContent = message;
            status.className = `status ${type}`;
            status.style.display = 'block';
            
            setTimeout(() => {
                status.style.display = 'none';
            }, 3000);
        }
        
        // تنفيذ الأمر عند الضغط على Enter
        document.getElementById('commandInput').addEventListener('keypress', function(e) {
            if (e.key === 'Enter') {
                executeCommand();
            }
        });
        
        // تغيير حجم الترمنال عند تغيير حجم النافذة
        window.addEventListener('resize', () => {
            fitAddon.fit();
        });
    </script>
</body>
</html>
'''

@app.route('/')
def index():
    """الصفحة الرئيسية"""
    return render_template_string(HTML_TEMPLATE)

@app.route('/execute', methods=['POST'])
def execute_command():
    """تنفيذ أوامر الشل"""
    try:
        data = request.get_json()
        command = data.get('command', '').strip()
        
        if not command:
            return jsonify({'error': 'لم يتم تقديم أمر للتنفيذ'})
        
        # منع بعض الأوامر الخطيرة
        dangerous_commands = ['rm -rf', 'format', 'del', 'shutdown', 'reboot', 'halt']
        if any(dangerous in command.lower() for dangerous in dangerous_commands):
            return jsonify({'error': 'هذا الأمر غير مسموح لأسباب أمنية'})
        
        # تنفيذ الأمر مع timeout
        result = subprocess.run(
            command,
            shell=True,
            capture_output=True,
            text=True,
            timeout=30,  # 30 ثانية كحد أقصى
            cwd=os.getcwd()
        )
        
        output = result.stdout
        if result.stderr:
            output += f"\nخطأ: {result.stderr}"
        
        return jsonify({
            'output': output,
            'return_code': result.returncode
        })
        
    except subprocess.TimeoutExpired:
        return jsonify({'error': 'انتهت مهلة تنفيذ الأمر (30 ثانية)'})
    except Exception as e:
        return jsonify({'error': f'خطأ في تنفيذ الأمر: {str(e)}'})

@app.route('/python', methods=['POST'])
def execute_python():
    """تنفيذ أكواد بايثون"""
    try:
        data = request.get_json()
        code = data.get('code', '').strip()
        
        if not code:
            return jsonify({'error': 'لم يتم تقديم كود للتنفيذ'})
        
        # إنشاء ملف مؤقت للكود
        with tempfile.NamedTemporaryFile(mode='w', suffix='.py', delete=False) as f:
            f.write(code)
            temp_file = f.name
        
        try:
            # تنفيذ الكود
            result = subprocess.run(
                [sys.executable, temp_file],
                capture_output=True,
                text=True,
                timeout=30,
                cwd=os.getcwd()
            )
            
            output = result.stdout
            if result.stderr:
                output += f"\nخطأ: {result.stderr}"
            
            return jsonify({
                'output': output,
                'return_code': result.returncode
            })
            
        finally:
            # حذف الملف المؤقت
            try:
                os.unlink(temp_file)
            except:
                pass
                
    except subprocess.TimeoutExpired:
        return jsonify({'error': 'انتهت مهلة تنفيذ الكود (30 ثانية)'})
    except Exception as e:
        return jsonify({'error': f'خطأ في تنفيذ الكود: {str(e)}'})

@app.route('/upload', methods=['POST'])
def upload_files():
    """رفع الملفات"""
    try:
        if 'files' not in request.files:
            return jsonify({'success': False, 'error': 'لم يتم اختيار ملفات'})
        
        files = request.files.getlist('files')
        uploaded_files = []
        
        for file in files:
            if file.filename == '':
                continue
                
            # حفظ الملف
            filename = file.filename
            file_path = os.path.join(UPLOAD_FOLDER, filename)
            file.save(file_path)
            uploaded_files.append(filename)
        
        if uploaded_files:
            return jsonify({
                'success': True,
                'files': uploaded_files,
                'message': f'تم رفع {len(uploaded_files)} ملف بنجاح'
            })
        else:
            return jsonify({'success': False, 'error': 'لم يتم رفع أي ملفات'})
            
    except Exception as e:
        return jsonify({'success': False, 'error': f'خطأ في رفع الملفات: {str(e)}'})

@app.route('/files')
def list_files():
    """عرض قائمة الملفات المرفوعة"""
    try:
        files = os.listdir(UPLOAD_FOLDER)
        return jsonify({'files': files})
    except Exception as e:
        return jsonify({'error': f'خطأ في عرض الملفات: {str(e)}'})

if __name__ == '__main__':
    # إنشاء مجلد الرفع إذا لم يكن موجوداً
    os.makedirs(UPLOAD_FOLDER, exist_ok=True)
    
    # تشغيل التطبيق
    app.run(host='0.0.0.0', port=5000, debug=True)

