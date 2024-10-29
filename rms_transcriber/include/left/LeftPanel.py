
import wx
from wxasync import WxAsyncApp, AsyncBind
from pubsub import pub
from .MultiLineHtmlTreeCtrl import MultiLineHtmlTreeCtrl
from ..config import init_config
apc = init_config.apc
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

        self.auto_scroll_checkbox = wx.CheckBox(self, label="Auto Scroll")
        self.auto_scroll_checkbox.SetValue(True)  # Set default to checked
        apc.auto_scroll = True

        h_sizer = wx.BoxSizer(wx.HORIZONTAL)
        
        h_sizer.Add(self.button, 0, wx.ALL | wx.ALIGN_CENTER_VERTICAL, 5)
        #add filler
        h_sizer.AddStretchSpacer()
        h_sizer.Add(self.auto_scroll_checkbox, 0, wx.ALL | wx.ALIGN_CENTER_VERTICAL, 5)

        sizer = wx.BoxSizer(wx.VERTICAL)
        sizer.Add(left_notebook, 1, wx.EXPAND)
        sizer.Add(h_sizer, 0, wx.EXPAND| wx.ALL, 5)
        self.SetSizer(sizer)
        self.Bind(wx.EVT_SIZE, self.on_panel_resize)
        #AsyncBind(wx.EVT_LIST_ITEM_ACTIVATED, self.on_item_activated, self)

    def on_panel_resize(self, event):
        #print('on_panel_resize')
        # Force the HtmlListBox to recalculate sizes on panel resize
        #self.html_list_box.Refresh()
        pub.sendMessage("panel_resize", event=None)
        event.Skip()        
       
    def on_button_click(self, event):
        print('on_button_click')
        self.tree.on_test_populate()