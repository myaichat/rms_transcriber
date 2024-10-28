
import wx
import asyncio
from pubsub import pub
from .left.LeftPanel import LeftPanel

class RMSFrame(wx.Frame):
    def __init__(self, title, size):
        super(RMSFrame, self).__init__(None, title=title, 
                                           size=size)
        panel= wx.Panel(self)
        self.left_panel = LeftPanel(panel)
        #self.tree = MultiLineHtmlTreeCtrl(panel, size=(380, 480))
        button = wx.Button(panel, label="Add Item")
        sizer = wx.BoxSizer(wx.VERTICAL)
        sizer.Add(self.left_panel, 1, wx.EXPAND | wx.ALL, 5)
        sizer.Add(button, 0, wx.EXPAND | wx.ALL, 5)
        panel.SetSizer(sizer)
        self.Bind(wx.EVT_BUTTON, self.OnAddItem, button)
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
        self.content_buffer = ""  # Buffer to store content before updating WebView

        # Start the long-running process in a background thread
        #await self._long_running_process()
        

     

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
    async def update_webview_periodically(self):
        while True:
            if self.content_buffer:
                pub.sendMessage("display_response", response=self.content_buffer)
                #wx.CallAfter(self.update_text, self.content_buffer)
                self.content_buffer = ""  # Clear buffer after update
            await asyncio.sleep(0.2)  # Update every 200ms
