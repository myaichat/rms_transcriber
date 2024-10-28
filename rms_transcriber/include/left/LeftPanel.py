
import wx
from pubsub import pub
from .MultiLineHtmlTreeCtrl import MultiLineHtmlTreeCtrl

class LeftPanel(wx.Panel):
    def __init__(self, parent):
        super().__init__(parent)
         # Create Notebook
        left_notebook = wx.Notebook(self)
        
        self.tree = MultiLineHtmlTreeCtrl(left_notebook)
        
        left_notebook.AddPage(self.tree, "HtmlTree")


        
        #left_notebook.SetSelection(3)

        self.button = wx.Button(self, label="Populate List")
        self.button.Bind(wx.EVT_BUTTON, self.on_button_click)
        sizer = wx.BoxSizer(wx.VERTICAL)
        sizer.Add(left_notebook, 1, wx.EXPAND)
        sizer.Add(self.button, 0, wx.ALL, 5)
        self.SetSizer(sizer)
        self.Bind(wx.EVT_SIZE, self.on_panel_resize)

    def on_panel_resize(self, event):
        #print('on_panel_resize')
        # Force the HtmlListBox to recalculate sizes on panel resize
        #self.html_list_box.Refresh()
        pub.sendMessage("panel_resize", event=None)
        event.Skip()        
       
    def on_button_click(self, event):
        pub.sendMessage("test_populate")