# wx_client.py
import wx
import json
import socket
import threading
import subprocess
import os
import time
import sys
import signal

class TranscriptionFrame(wx.Frame):
    def __init__(self):
        super().__init__(parent=None, title='Speech Recognition', size=(600, 400))
        self.server_process = None
        self.initialize_ui()
        self.connect_to_server()

    def initialize_ui(self):
        panel = wx.Panel(self)
        vbox = wx.BoxSizer(wx.VERTICAL)

        # Transcription text area
        self.text_ctrl = wx.TextCtrl(
            panel, 
            style=wx.TE_MULTILINE | wx.TE_READONLY | wx.HSCROLL
        )
        vbox.Add(self.text_ctrl, 1, wx.EXPAND | wx.ALL, 5)

        # Buttons
        hbox = wx.BoxSizer(wx.HORIZONTAL)
        
        self.start_button = wx.Button(panel, label='Start Server')
        self.start_button.Bind(wx.EVT_BUTTON, self.on_start_server)
        hbox.Add(self.start_button, 0, wx.RIGHT, 5)

        self.stop_button = wx.Button(panel, label='Stop Server')
        self.stop_button.Bind(wx.EVT_BUTTON, self.on_stop_server)
        self.stop_button.Disable()
        hbox.Add(self.stop_button, 0, wx.RIGHT, 5)

        self.clear_button = wx.Button(panel, label='Clear')
        self.clear_button.Bind(wx.EVT_BUTTON, self.on_clear)
        hbox.Add(self.clear_button, 0)

        vbox.Add(hbox, 0, wx.ALL, 5)
        panel.SetSizer(vbox)

        # Status bar
        self.CreateStatusBar()
        self.SetStatusText("Disconnected")

        # Bind close event
        self.Bind(wx.EVT_CLOSE, self.on_close)

    def connect_to_server(self):
        self.client_socket = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
        self.receiver_thread = None

    def start_receiver_thread(self):
        if self.receiver_thread is None or not self.receiver_thread.is_alive():
            self.receiver_thread = threading.Thread(target=self.receive_data)
            self.receiver_thread.daemon = True
            self.receiver_thread.start()

    def on_start_server(self, event):
        try:
            # Check if server is already running
            pid_file = os.path.join(os.path.dirname(__file__), "speech_server.pid")
            if os.path.exists(pid_file):
                wx.MessageBox("Server appears to be already running", 
                            "Warning", 
                            wx.OK | wx.ICON_WARNING)
                return

            # Start server script in new process
            server_script = os.path.join(os.path.dirname(__file__), 'speech_server.py')
            startupinfo = None
            if os.name == 'nt':
                startupinfo = subprocess.STARTUPINFO()
                startupinfo.dwFlags |= subprocess.STARTF_USESHOWWINDOW
                startupinfo.wShowWindow = subprocess.SW_HIDE

            self.server_process = subprocess.Popen(
                [sys.executable, server_script],
                startupinfo=startupinfo,
                creationflags=subprocess.CREATE_NEW_PROCESS_GROUP if os.name == 'nt' else 0
            )
            
            # Wait for server to start
            max_attempts = 10
            attempts = 0
            while attempts < max_attempts:
                try:
                    self.client_socket = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
                    self.client_socket.connect(('127.0.0.1', 5000))
                    break
                except socket.error:
                    attempts += 1
                    time.sleep(1)
                    if attempts == max_attempts:
                        raise Exception("Failed to connect to server")

            self.SetStatusText("Connected to server")
            self.start_button.Disable()
            self.stop_button.Enable()
            
            # Start receiving data
            self.start_receiver_thread()
            
        except Exception as e:
            wx.MessageBox(f"Error connecting to server: {str(e)}", 
                         "Error", 
                         wx.OK | wx.ICON_ERROR)
            self.cleanup_server()

    def on_stop_server(self, event):
        self.cleanup_server()
        self.start_button.Enable()
        self.stop_button.Disable()
        self.SetStatusText("Server stopped")

    def cleanup_server(self):
        # Close socket
        try:
            if hasattr(self, 'client_socket'):
                self.client_socket.close()
        except:
            pass

        # Stop server process
        try:
            if self.server_process:
                if os.name == 'nt':
                    os.kill(self.server_process.pid, signal.CTRL_BREAK_EVENT)
                else:
                    self.server_process.terminate()
                self.server_process.wait(timeout=5)
        except:
            pass

        # Remove PID file
        try:
            pid_file = os.path.join(os.path.dirname(__file__), "speech_server.pid")
            if os.path.exists(pid_file):
                os.remove(pid_file)
        except:
            pass

    def receive_data(self):
        buffer = ""
        while True:
            try:
                data = self.client_socket.recv(4096).decode()
                if not data:
                    break
                
                buffer += data
                while '\n' in buffer:
                    line, buffer = buffer.split('\n', 1)
                    message = json.loads(line)
                    
                    if message['type'] == 'transcription':
                        wx.CallAfter(self.update_transcription, 
                                   message['text'], 
                                   message['complete'])
                        
            except Exception as e:
                wx.CallAfter(self.handle_disconnect)
                break

    def update_transcription(self, text, complete):
        if complete:
            current_text = self.text_ctrl.GetValue()
            self.text_ctrl.SetValue(f"{current_text}\n{text}")
        else:
            lines = self.text_ctrl.GetValue().split('\n')
            if lines[-1].strip() == '':
                lines = lines[:-1]
            lines[-1] = text
            self.text_ctrl.SetValue('\n'.join(lines))
        
        self.text_ctrl.ShowPosition(self.text_ctrl.GetLastPosition())

    def handle_disconnect(self):
        self.SetStatusText("Disconnected from server")
        self.start_button.Enable()
        self.stop_button.Disable()
        self.cleanup_server()
        self.connect_to_server()

    def on_clear(self, event):
        self.text_ctrl.Clear()

    def on_close(self, event):
        self.cleanup_server()
        event.Skip()

if __name__ == '__main__':
    app = wx.App()
    frame = TranscriptionFrame()
    frame.Show()
    app.MainLoop()