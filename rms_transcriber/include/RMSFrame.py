
import wx
import asyncio
from pubsub import pub
from .left.LeftPanel import LeftPanel
from .center.CenterPanel import CenterPanel

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
        self.center_panel = CenterPanel(splitter)   

        # Split the main splitter window vertically between the left and right notebooks
        splitter.SplitVertically(self.left_panel, self.center_panel)
        splitter.SetSashGravity(0.5)  # Set initial split at 50% width for each side
        splitter.SetMinimumPaneSize(400)  # Minimum pane width to prevent collapsing
        sizer = wx.BoxSizer(wx.VERTICAL)
        sizer.Add(splitter, 1, wx.EXPAND)
        #sizer.Add(self.button, 0, wx.CENTER | wx.ALL, 5)
        #sizer.Add(self.abutton, 0, wx.CENTER | wx.ALL, 5)
        panel.SetSizer(sizer)
        #self.content_buffer = ""
        
        if 0:
            
            root = self.tree.AddRoot("Root")
            
            # Add parent and child items with unique HTML content for each HtmlListBox
            parent1 = self.tree.AppendMultilineItem(root,
                                                    ["<b>Parent Info 1</b>", "<i>Additional Info</i>"])
            child1 = self.tree.AppendMultilineItem(parent1,
                                                ["<b>Child Info 1</b>", "<i>Extra Info</i>"])
            child2 = self.tree.AppendMultilineItem(parent1,
                                                ["<b>Child Info 2</b>", "<i>Extra Details</i>"])
            self.tree.ExpandAll()
            
            self.Layout()
            self.Bind(wx.EVT_SIZE, self.OnSize)


     

    def OnSize(self, event):
        self.Layout()
        event.Skip()
    def OnAddItem(self, event):
        pub.sendMessage("ADD_ITEM")
    async def consume_queue(self):
        # Continuously consume the queue and update WebView
        while True:
            content = await self.queue.get()
            #print('\n\tconsume_queue: ',content)
            #pub.sendMessage("display_response", response=content)  # Send the content to the WebView
            #wx.CallAfter(self.update_text, content)  # Update UI safely in the main thread
            self.queue.task_done()
            self.content_buffer += content  
    async def _update_webview_periodically(self):
        while True:
            if self.content_buffer:
                pub.sendMessage("display_response", response=self.content_buffer)
                #wx.CallAfter(self.update_text, self.content_buffer)
                self.content_buffer = ""  # Clear buffer after update
            await asyncio.sleep(0.2)  # Update every 200ms
