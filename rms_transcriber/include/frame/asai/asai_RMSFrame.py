
import wx
import asyncio
from pubsub import pub
from ...left.asai.LeftPanel import LeftPanel
from ...center.CenterPanel import CenterPanel
from ...right.RightPanel import RightPanel


class ProcessorPanel(wx.Panel):
    def __init__(self, parent):
        super().__init__(parent)
        
        splitter = wx.SplitterWindow(self, style=wx.SP_LIVE_UPDATE)
        self.center_panel = CenterPanel(splitter)
        #self.tree = MultiLineHtmlTreeCtrl(panel, size=(380, 480))

        self.right_panel = RightPanel(splitter)   

        # Split the main splitter window vertically between the left and right notebooks
        splitter.SplitVertically(self.center_panel, self.right_panel)
        splitter.SetSashGravity(0.5)  # Set initial split at 50% width for each side
        #splitter.SetMinimumPaneSize(400)  # Minimum pane width to prevent collapsing
        sizer = wx.BoxSizer(wx.VERTICAL)
        sizer.Add(splitter, 1, wx.EXPAND)

        self.SetSizer(sizer)
        
        self.Layout()

   

class RMSFrame(wx.Frame):
    def __init__(self, title, size):
        super(RMSFrame, self).__init__(None, title=title, 
                                           size=size)
        panel= wx.Panel(self)
        splitter = wx.SplitterWindow(panel, style=wx.SP_LIVE_UPDATE)
        self.left_panel = LeftPanel(splitter)
        #self.tree = MultiLineHtmlTreeCtrl(panel, size=(380, 480))
        if 0:
            button = wx.Button(panel, label="Add Item")
            sizer = wx.BoxSizer(wx.VERTICAL)
            sizer.Add(self.left_panel, 1, wx.EXPAND | wx.ALL, 5)
            sizer.Add(button, 0, wx.EXPAND | wx.ALL, 5)
            self.Bind(wx.EVT_BUTTON, self.OnAddItem, button)
        self.processor_panel = ProcessorPanel(splitter)   

        # Split the main splitter window vertically between the left and right notebooks
        splitter.SplitVertically(self.left_panel, self.processor_panel)
        splitter.SetSashGravity(0.5)  # Set initial split at 50% width for each side
        splitter.SetMinimumPaneSize(400)  # Minimum pane width to prevent collapsing
        sizer = wx.BoxSizer(wx.VERTICAL)
        sizer.Add(splitter, 1, wx.EXPAND)
        #sizer.Add(self.button, 0, wx.CENTER | wx.ALL, 5)
        #sizer.Add(self.abutton, 0, wx.CENTER | wx.ALL, 5)
        panel.SetSizer(sizer)
        self.content_buffer = ""
