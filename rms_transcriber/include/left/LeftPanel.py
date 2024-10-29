
import wx
from wxasync import WxAsyncApp, AsyncBind
from pubsub import pub
from .MultiLineHtmlTreeCtrl import MultiLineHtmlTreeCtrl
from .MultiLineTreeCtrl import MultiLineTreeCtrl
from ..config import init_config
apc = init_config.apc
class LeftPanel(wx.Panel):
    def __init__(self, parent):
        super().__init__(parent)
         # Create Notebook
        left_notebook = wx.Notebook(self)
        if 1: 
            self.tree = MultiLineHtmlTreeCtrl(left_notebook)
            
            left_notebook.AddPage(self.tree, "HtmlTree")
        if 1:
            self.tree_2 = MultiLineTreeCtrl(left_notebook)
            left_notebook.AddPage(self.tree_2, "Tree")        


        
        #left_notebook.SetSelection(3)

        self.button = wx.Button(self, label="Populate List")
        self.button.Bind(wx.EVT_BUTTON, self.on_button_click)
        if 0:
            self.auto_scroll_checkbox = wx.CheckBox(self, label="Auto Scroll")
            self.auto_scroll_checkbox.SetValue(True)  # Set default to checked
            self.auto_scroll_checkbox.Bind(wx.EVT_CHECKBOX, self.on_auto_scroll_checkbox)
        else:
            self.auto_scroll_button = wx.Button(self, label="Auto Scroll: ON")
            self.auto_scroll_button.SetBackgroundColour(wx.Colour(144, 238, 144))  # Green for ON state
            self.auto_scroll_button.Bind(wx.EVT_BUTTON, self.on_auto_scroll_button)
            self.auto_scroll_button.SetMinSize(wx.Size(-1, 40))
            self.auto_scroll_on = True  # Initial state            
        apc.auto_scroll = True

        h_sizer = wx.BoxSizer(wx.HORIZONTAL)
        
        h_sizer.Add(self.button, 0, wx.ALL | wx.ALIGN_CENTER_VERTICAL, 5)
        #add filler
        h_sizer.AddStretchSpacer()
        h_sizer.Add(self.auto_scroll_button, 0, wx.ALL | wx.ALIGN_CENTER_VERTICAL, 1)

        sizer = wx.BoxSizer(wx.VERTICAL)
        sizer.Add(left_notebook, 1, wx.EXPAND)
        sizer.Add(h_sizer, 0, wx.EXPAND| wx.ALL, 1)
        self.SetSizer(sizer)
        self.Bind(wx.EVT_SIZE, self.on_panel_resize)
    def on_auto_scroll_button(self, event):
        # Toggle auto-scroll state
        self.auto_scroll_on = not self.auto_scroll_on
        if self.auto_scroll_on:
            self.auto_scroll_button.SetLabel("Auto Scroll: ON")
            self.auto_scroll_button.SetBackgroundColour(wx.Colour(144, 238, 144))  # Green for ON
            apc.auto_scroll = True  # Set your app's auto-scroll state
        else:
            self.auto_scroll_button.SetLabel("Auto Scroll: OFF")
            self.auto_scroll_button.SetBackgroundColour(wx.Colour(255, 182, 193))  # Red for OFF
            apc.auto_scroll = False  # Set your app's auto-scroll state
        self.auto_scroll_button.Refresh()  # Ensure color update is visible

        #AsyncBind(wx.EVT_LIST_ITEM_ACTIVATED, self.on_item_activated, self)
    def on_auto_scroll_checkbox(self, event):
        """Toggle auto scroll based on checkbox state."""
        apc.auto_scroll = self.auto_scroll_checkbox.IsChecked()
        print(f"Auto Scroll is now {'enabled' if apc.auto_scroll else 'disabled'}")
    def on_panel_resize(self, event):
        #print('on_panel_resize')
        # Force the HtmlListBox to recalculate sizes on panel resize
        #self.html_list_box.Refresh()
        pub.sendMessage("panel_resize", event=None)
        event.Skip()        
       
    def on_button_click(self, event):
        print('on_button_click')
        self.tree.on_test_populate()
        self.tree_2.on_test_populate()