 
import wx
import wx.lib.agw.customtreectrl as CT
from wx.lib.pubsub import pub
import asyncio
from wxasync import WxAsyncApp, AsyncBind
from pprint import pprint as pp
#from rms_transcriber import apc
from ..config import init_config
apc = init_config.apc

from .CustomHtmlListBox import CustomHtmlListBox

class MultiLineHtmlTreeCtrl(CT.CustomTreeCtrl):
    def __init__(self, parent, id=wx.ID_ANY, pos=wx.DefaultPosition,
                 size=wx.DefaultSize):
        agwStyle = (CT.TR_HAS_VARIABLE_ROW_HEIGHT |
                    CT.TR_HAS_BUTTONS |
                    #CT.TR_NO_LINES |
                    CT.TR_FULL_ROW_HIGHLIGHT)
        super(MultiLineHtmlTreeCtrl, self).__init__(parent, id, pos, size, 
                                                agwStyle=agwStyle,
                                                style=wx.WANTS_CHARS)
        self.Bind(wx.EVT_LEFT_DOWN, self.OnSingleClick)
        self.Bind(wx.EVT_LEFT_DCLICK, self.OnDoubleClick)
        #AsyncBind(wx.EVT_LEFT_DCLICK, self.OnDoubleClick, self)
        self.single_click_delayed = None
        self.set_custom_expand_collapse_icons()
        
        self.root = self.AddRoot("Root")
        pub.subscribe(self.on_test_populate, "test_populate")
        #pub.subscribe(self.on_stream_closed, "stream_closed")
        
        #pub.subscribe(self.on_partial_stream, "partial_stream")

        self.tid=0
        self.html_items={}
        self.content_buffer = []
    def on_test_populate(self):
        #print('on_test_populate')
        #self.tree.DeleteAllItems()
        root = self.root
        
        # Add multiline items
        
        # Add parent and child items with unique HTML content for each HtmlListBox
        for i in range(5):
            test='Tell me more about Apache Pyspark'
            item_id=f'{i}:{i}'
            parent1 = self.AppendMultilineItem(item_id, self.root, test, pad_item=False)
            #parent1 = self.UpdateMultilineItem(item_id, self.root, test)
   
       
        
        # Expand all items
        self.ExpandAll()      
       
    async def consume_transcription_queue(self):
        # Continuously consume the queue and update WebView
        queue=apc.trans_queue
        while True:
            content = await queue.get()
            #print('\n\tconsume_queue: ',content)
            #pub.sendMessage("display_response", response=content)  # Send the content to the WebView
            #wx.CallAfter(self.update_text, content)  # Update UI safely in the main thread
            #queue.task_done()
            self.content_buffer.append(content  )

    async def update_tree_periodically(self):
        #queue=apc.trans_queue
        while True:
            if self.content_buffer:
                #print(self.content_buffer[0])
                #pub.sendMessage("display_response", response=self.content_buffer)
                #wx.CallAfter(self.update_text, self.content_buffer)
                #print('-----------------------update_tree_periodically:',len(self.content_buffer))
                for data in self.content_buffer:
                    if data[0].strip():
                        if data[1]=='stream_closed':
                            self.on_stream_closed(data)
                        else:
                            assert data[1]=='partial_stream', data[1]
                            self.on_partial_stream(data)
                self.content_buffer = [] # Clear buffer after update
            await asyncio.sleep(0.2)  # Update every 200ms

    def on_partial_stream(self, data):  
        transcript, corrected_time, tid, rid = data
        #print('on_partial_stream')
        #print(transcript, corrected_time, tid, rid)
        if transcript.strip():
            item_id=f'{tid}:{rid}'
            #self.html_items[tid]=transcript
            if item_id in self.html_items:
                
                wx.CallAfter( self.update_tree_with_transcript,item_id, f'{item_id}, {transcript}')
            else:
                
                wx.CallAfter(self.append_tree_with_transcript,item_id, f'{item_id}, {transcript}')       
            # Ensure UI updates happen in the main thread
            #wx.CallAfter(self.update_tree_with_transcript, transcript)

    def on_stream_closed(self, data):
        transcript, corrected_time, tid, rid = data
        if transcript.strip():  # Ensure there's content in the transcript
            #print('|'*80)
            #pp(transcript)
            #print('|'*80)
            item_id = f'{tid}:{rid}'
            wx.CallAfter(self.recreate_html_item,item_id, transcript)
    def recreate_html_item(self, item_id, transcript):
        # Check if the item exists
        if item_id in self.html_items:
            # Get the tree item and the existing HtmlListBox
            tree_item = self.html_items[item_id].tree_item
            old_html_item = self.html_items[item_id]
            
            # Remove the old control from the tree item
            self.DeleteItemWindow(tree_item)
            
            # Explicitly delete the old HtmlListBox to free up resources
            #old_html_item.Destroy()
            
            # Create a new HtmlListBox with the final transcription
            new_html_item = CustomHtmlListBox(self.tid, self, transcript, self, tree_item, size=(200, 80))
            self.html_items[item_id] = new_html_item  # Replace the old reference with the new one
            
            # Attach the new HtmlListBox to the tree item
            self.SetItemWindow(tree_item, new_html_item)
            if apc.auto_scroll:
                self.EnsureVisible(tree_item)
            return new_html_item

    def _on_stream_closed(self, data):
        transcript, corrected_time, tid, rid = data
        if transcript.strip():  
            item_id=f'{tid}:{rid}'
            #self.html_items[tid]=transcript
            if item_id in self.html_items:
                
                wx.CallAfter( self.update_tree_with_transcript,item_id, f'{item_id}, {transcript}')
            else:
                wx.CallAfter(self.append_tree_with_transcript,item_id, f'{item_id}, {transcript}')  

    def append_tree_with_transcript(self, item_id, transcript):
        #print('append_tree_with_transcript')
        if transcript.strip():
            parent1 = self.AppendMultilineItem(item_id, self.root, transcript)
            self.ExpandAll()  # Expanding within the main thread  

    def update_tree_with_transcript(self,item_id, transcript):
        #print('update_tree_with_transcript')
        if transcript.strip():
            parent1 = self.UpdateMultilineItem(item_id, self.root, transcript)
            #self.ExpandAll()  # Expanding within the main thread       


    def set_custom_expand_collapse_icons(self):
        # Create a larger "+" and "-" bitmap for expand/collapse
        expand_bmp = wx.Bitmap(20, 20)
        collapse_bmp = wx.Bitmap(20, 20)

        # Draw a "+" icon for expand
        dc = wx.MemoryDC(expand_bmp)
        dc.SetBackground(wx.Brush(wx.Colour(255, 255, 255)))
        dc.Clear()
        dc.SetPen(wx.Pen(wx.Colour(0, 0, 0), 3))
        dc.DrawLine(10, 5, 10, 15)
        dc.DrawLine(5, 10, 15, 10)
        dc.SelectObject(wx.NullBitmap)

        # Draw a "-" icon for collapse
        dc = wx.MemoryDC(collapse_bmp)
        dc.SetBackground(wx.Brush(wx.Colour(255, 255, 255)))
        dc.Clear()
        dc.SetPen(wx.Pen(wx.Colour(0, 0, 0), 3))
        dc.DrawLine(5, 10, 15, 10)
        dc.SelectObject(wx.NullBitmap)

        # Create an image list and add custom bitmaps
        image_list = wx.ImageList(20, 20)
        image_list.Add(expand_bmp)   # The first image is the expand icon
        image_list.Add(expand_bmp) # The second image is the collapse icon
        image_list.Add(collapse_bmp) # The second image is the collapse icon
        image_list.Add(collapse_bmp)
        # Assign the image list to the tree control
        self.SetButtonsImageList(image_list)
    def get_item_height(self,  item):
        """
        Retrieves the height of the specified tree item.
        
        Args:
            item: The tree item to measure.

        Returns:
            int: The height of the tree item in pixels.
        """
        rect = self.GetBoundingRect(item, textOnly=False)
        return rect.height
    def UpdateMultilineItem(self, item_id, parent, text_item, data=None):
        self.Freeze()
        assert item_id in self.html_items, f"Item ID {item_id} not found in html_items"
        
        # Access the HtmlListBox for the specific item
        html_item = self.html_items[item_id]
        
        # Add the new content and adjust the size accordingly
        html_item.add_history_item(text_item)
        
        # Adjust the size to fit new content
        html_item.adjust_size_to_fit_content(text_item)
        #html_item.text_item=text_item   
        #html_item.Update()  # Refresh the HtmlListBox
        try:
            html_item_height=html_item.GetSize().height
            tree_item_height=self.get_item_height(html_item.tree_item)
            if html_item_height*.9>tree_item_height :
                #print('html_item_height:',html_item_height, 'tree_item_height:', tree_item_height)
            
                
                padded_text=text_item+' \n'*html_item.padding_cnt
                new_html_item= self.recreate_html_item(item_id, padded_text)
                new_html_item.is_recreated=True
                new_html_item.SetItemCount(1) 
        except Exception as e:
            print(e)
             
        self.Thaw()
    
    def AppendMultilineItem(self, item_id, parent, text_item, data=None, pad_item=True):
        # Append an item with an empty string as the text

        # Create an instance of CustomHtmlListBox with specific items, passing tree control and item references
        if  item_id not in self.html_items:
            item = self.AppendItem(parent, "")
            if data is not None:
                self.SetItemData(item, data)
            self.tid += 1
            text=text_item
            if pad_item:
                padded_text=' \n'*5
                text=padded_text
            self.html_items[item_id]=html_list_box = CustomHtmlListBox(self.tid,self, text, self, item,  size=(400, 480))
            
            #html_list_box.Enable(False)
            self.SetItemWindow(item, html_list_box)
            html_list_box.SetMinSize((400, 480))
            html_list_box.SetMaxSize((400, 480))
            
            self.InvalidateBestSize()
            self.Layout()            
        
            # Add sample history items to the HtmlListBox
            #html_list_box.add_history_item("First line\nSecond line\nThird line")
            if pad_item:
                html_list_box.add_history_item(text_item)
            return item
    def _AppendMultilineItem(self, item_id, parent, text_item, data=None):
        # Append an item with an empty string as the text
        if item_id not in self.html_items:
            item = self.AppendItem(parent, "")
            if data is not None:
                self.SetItemData(item, data)
            self.tid += 1

            # Create the CustomHtmlListBox instance with the desired size
            html_list_box = CustomHtmlListBox(self.tid, self, text_item, self, item, size=(300, 280))
            self.html_items[item_id] = html_list_box

            # Create a sizer and set the item height within the sizer
            item_sizer = wx.BoxSizer(wx.VERTICAL)
            item_sizer.Add(html_list_box, flag=wx.EXPAND | wx.ALL, proportion=1, border=0)
            
            # Apply the sizer to the tree control to handle resizing
            item.SetSizer(item_sizer)
            item.SetMinSize((300, 280))  # Explicitly set the height

            # Set the item window and update the layout
            self.SetItemWindow(item, html_list_box)
            self.Layout()  # Force a layout update to apply the size changes

            return item

    def OnSingleClick(self, event):
        if self.single_click_delayed:
            self.single_click_delayed.Stop()

        pos = event.GetPosition()
        item, flags = self.HitTest(pos)
        if flags & CT.TREE_HITTEST_ONITEMBUTTON:
            event.Skip()
            return

        self.single_click_delayed = wx.CallLater(160, self.ProcessSingleClick, item, event)

    def ProcessSingleClick(self, item, event):
        if item:
            self.SelectItem(item)
            #print("Single click detected on item in tree")
        self.single_click_delayed = None

    def OnDoubleClick(self, event):
        if self.single_click_delayed:
            self.single_click_delayed.Stop()
            self.single_click_delayed = None

        pos = event.GetPosition()
        item, flags = self.HitTest(pos)
        if item:
            self.SelectItem(item)
            #print("Double-clicked on item in tree")

        event.Skip()
    async def on_ask_model(self, event):
        #print('on_item_activated')
        return
        # Get the selected row index and the data in the row
        index = event.GetIndex()
        id_value = self.list_ctrl.GetItemText(index, 0)
        transcription_value = self.list_ctrl.GetItemText(index, 1)
        await self.ask_model(transcription_value)         
