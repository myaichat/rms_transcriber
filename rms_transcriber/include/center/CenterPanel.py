


import wx
from pubsub import pub
from .ProcessorPanel import ProcessorPanel

class CenterPanel(wx.Panel):
    def __init__(self, parent):
        super().__init__(parent)
         # Create Notebook
        center_notebook = wx.Notebook(self)
        
        self.processor_panel = ProcessorPanel(center_notebook,prefix="Center")
        
        center_notebook.AddPage(self.processor_panel, "Processor")


        
        center_notebook.SetSelection(0)

        
        
        sizer = wx.BoxSizer(wx.VERTICAL)
        sizer.Add(center_notebook, 1, wx.EXPAND)
        
        self.SetSizer(sizer)
        #self.Bind(wx.EVT_SIZE, self.on_panel_resize)
        self.Layout()

    async def consume_askmodel_queue(self, queue):
        # Continuously consume the queue and update WebView
        while True:
            content = await queue.get()
            #print('\n\tconsume_queue: ',content)
            #pub.sendMessage("display_response", response=content)  # Send the content to the WebView
            #wx.CallAfter(self.update_text, content)  # Update UI safely in the main thread
            queue.task_done()
            self.processor_panel.content_buffer += content         

