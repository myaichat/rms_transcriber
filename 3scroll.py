import wx
import wx.html2

class LogPanel(wx.Panel):
    def __init__(self, parent):
        super().__init__(parent)
        
        # Create a ScrolledWindow to contain the WebView
        self.scroll_window = wx.ScrolledWindow(self, style=wx.VSCROLL)
        self.scroll_window.SetScrollRate(0, 20)  # Set vertical scrolling rate

        # Initialize the WebView within the ScrolledWindow
        self.web_view = wx.html2.WebView.New(self.scroll_window)
        
        # Set layout for scroll_window
        sizer = wx.BoxSizer(wx.VERTICAL)
        sizer.Add(self.web_view, 1, wx.EXPAND)  # Make the WebView expand to fill scroll_window
        self.scroll_window.SetSizer(sizer)

        # Set main layout for LogPanel
        main_sizer = wx.BoxSizer(wx.VERTICAL)
        main_sizer.Add(self.scroll_window, 1, wx.EXPAND)  # Make scroll_window expand to fill LogPanel
        self.SetSizer(main_sizer)

    def replace_log_content(self, content):
        # Process the HTML content
        final_content = f"<html><body>{content}</body></html>"
        
        # Load the content into the WebView
        self.web_view.SetPage(final_content, "")
        
        # Scroll to the bottom of the ScrolledWindow after content loads
        wx.CallAfter(self.scroll_to_bottom)
    
    def scroll_to_bottom(self):
        # Scroll to the bottom of the ScrolledWindow
        max_y = self.scroll_window.GetScrollRange(wx.VERTICAL)
        self.scroll_window.Scroll(0, max_y)

class MainFrame(wx.Frame):
    def __init__(self):
        super().__init__(None, title="Log Panel Example", size=(600, 400))
        panel = LogPanel(self)
        panel.replace_log_content("<h1>Log Content</h1><p>Here is some log content...</p>")
        self.Show()

app = wx.App(False)
frame = MainFrame()
app.MainLoop()
