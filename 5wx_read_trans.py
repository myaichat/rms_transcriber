import wx
import socket
import json
import threading
import sys
import time

class TranscriptionFrame(wx.Frame):
    def __init__(self, *args, **kw):
        super(TranscriptionFrame, self).__init__(*args, **kw)
        
        # Create main panel
        panel = wx.Panel(self)
        
        # Create sizer for layout
        main_sizer = wx.BoxSizer(wx.VERTICAL)
        
        # Create text controls
        self.current_text = wx.TextCtrl(panel, style=wx.TE_READONLY)
        self.complete_text = wx.TextCtrl(panel, style=wx.TE_MULTILINE | wx.TE_READONLY | wx.HSCROLL)
        
        # Add labels and controls to sizer
        main_sizer.Add(wx.StaticText(panel, label="Current Transcription:"), 0, wx.ALL, 5)
        main_sizer.Add(self.current_text, 0, wx.EXPAND | wx.ALL, 5)
        main_sizer.Add(wx.StaticText(panel, label="Complete Transcriptions:"), 0, wx.ALL, 5)
        main_sizer.Add(self.complete_text, 1, wx.EXPAND | wx.ALL, 5)
        
        # Set panel sizer
        panel.SetSizer(main_sizer)
        
        # Create status bar
        self.CreateStatusBar()
        self.SetStatusText("Disconnected")
        
        # Set size
        self.SetSize((600, 400))
        
        # Center window
        self.Center()

    def update_current_text(self, text):
        """Update the current transcription text control"""
        wx.CallAfter(self.current_text.SetValue, text)
    
    def append_complete_text(self, text):
        """Append text to the complete transcriptions text control"""
        wx.CallAfter(self.complete_text.AppendText, f"{text}\n{'='*50}\n")
    
    def set_status(self, text):
        """Update the status bar text"""
        wx.CallAfter(self.SetStatusText, text)

class TranscriptionReader:
    def __init__(self, frame, host='127.0.0.1', port=5000):
        self.frame = frame
        self.host = host
        self.port = port
        self.client_socket = None
        self.running = True
        
    def connect(self):
        try:
            self.client_socket = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
            self.client_socket.connect((self.host, self.port))
            self.frame.set_status("Connected to transcription server")
            return True
        except ConnectionRefusedError:
            self.frame.set_status("Could not connect to server. Make sure the server is running.")
            return False
        except Exception as e:
            self.frame.set_status(f"Connection error: {e}")
            return False

    def read_transcriptions(self):
        if not self.client_socket:
            if not self.connect():
                return

        buffer = ""
        try:
            while self.running:
                data = self.client_socket.recv(4096).decode()
                if not data:
                    break

                buffer += data
                while '\n' in buffer:
                    line, buffer = buffer.split('\n', 1)
                    message = json.loads(line)
                    
                    if message['type'] == 'transcription':
                        text = message['text']
                        is_complete = message['complete']
                        
                        if is_complete:
                            self.frame.append_complete_text(text)
                        else:
                            self.frame.update_current_text(text)
                        
        except Exception as e:
            self.frame.set_status(f"Error reading transcriptions: {e}")
        finally:
            self.close()

    def close(self):
        self.running = False
        if self.client_socket:
            self.client_socket.close()
            self.frame.set_status("Connection closed")

def main():
    app = wx.App()
    frame = TranscriptionFrame(None, title='Transcription Reader')
    frame.Show()
    
    # Create and start reader thread
    reader = TranscriptionReader(frame)
    reader_thread = threading.Thread(target=reader.read_transcriptions)
    reader_thread.daemon = True
    reader_thread.start()
    
    # Start the main event loop
    app.MainLoop()
    
    # Cleanup when app closes
    reader.close()

if __name__ == "__main__":
    main()