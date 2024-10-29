import wx
import wx.lib.agw.customtreectrl as CT
from pubsub import pub
import asyncio
from wxasync import AsyncBind
from pprint import pprint as pp
from ..config import init_config
apc = init_config.apc

class MultiLineTreeCtrl(CT.CustomTreeCtrl):
    def __init__(self, parent, id=wx.ID_ANY, pos=wx.DefaultPosition,
                 size=wx.DefaultSize):
        # Create the base style with required flags
        agwStyle = (CT.TR_HAS_VARIABLE_ROW_HEIGHT |  # Required for multiline
                   CT.TR_HAS_BUTTONS |               # Show expand/collapse buttons
                   # CT.TR_NO_LINES |                  # No connection lines
                   CT.TR_FULL_ROW_HIGHLIGHT)         # Highlight full row on selection
        
        # Initialize with explicit agwStyle
        super(MultiLineTreeCtrl, self).__init__(parent, id, pos, size, 
                                               agwStyle=agwStyle,
                                               style=wx.WANTS_CHARS)
        
        # Bind single-click and double-click events to the tree control
        self.Bind(wx.EVT_LEFT_DOWN, self.OnSingleClick)
        #self.Bind(wx.EVT_LEFT_DCLICK, self.OnDoubleClick)
        AsyncBind(wx.EVT_LEFT_DCLICK, self.OnDoubleClick, self)
        self.root = self.AddRoot("Root")
        # Initialize a variable for the delayed single-click call
        self.single_click_delayed = None
        self.html_items={}
        self.content_buffer = []
        self.large_font = wx.Font(12, wx.FONTFAMILY_DEFAULT, wx.FONTSTYLE_NORMAL, wx.FONTWEIGHT_NORMAL)
        self.SetFont(self.large_font)
    def on_test_populate(self):
        print('on_test_populate')
        #self.tree.DeleteAllItems()
        root = self.root
        
        # Add multiline items
        
        # Add parent and child items with unique HTML content for each HtmlListBox
        for i in range(5):
            test='Tell me more about Apache Pyspark'
            item_id=f'{i}:{i}'
            parent1 = self.AppendMultilineItem(item_id, self.root, test)
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
            queue.task_done()
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
    def on_stream_closed(self, data):
        transcript, corrected_time, tid, rid = data
        if transcript.strip():  # Ensure there's content in the transcript
            print('|'*80)
            pp(transcript)
            print('|'*80)
            item_id = f'{tid}:{rid}'
            wx.CallAfter(self.UpdateMultilineItem,item_id, f'{item_id}, {transcript}')
    def on_partial_stream(self, data):  
        transcript, corrected_time, tid, rid = data
        #print('on_partial_stream')
        #print(transcript, corrected_time, tid, rid)
        print('on_partial_stream')
        if transcript.strip():
            item_id=f'{tid}:{rid}'
            #self.html_items[tid]=transcript
            if item_id in self.html_items:
                
                wx.CallAfter( self.UpdateMultilineItem,item_id, f'{item_id}, {transcript}')
            else:
                
                wx.CallAfter(self.AppendMultilineItem,item_id, self.root, f'{item_id}, {transcript}')       
            # Ensure UI updates happen in the main thread
            #wx.CallAfter(self.update_tree_with_transcript, transcript)

    def AppendMultilineItem(self, item_id, parent, text, data=None):
        # Append item without checkbox
        item = self.AppendItem(parent, text)
        item.is_colored=False
        item.is_bolded=False
        self.html_items[item_id]=item
        base_font = wx.Font(11, wx.FONTFAMILY_DEFAULT, wx.FONTSTYLE_NORMAL, wx.FONTWEIGHT_NORMAL)
        bold_words = ["Apache", "Pyspark", "Oracle", "PL/SQL", "Hints", "Airflow", 'models', 'model']
        if bold_words:
            for word in bold_words:
                if word in text:
                    bold_font = wx.Font(base_font.GetPointSize(), base_font.GetFamily(),
                                        base_font.GetStyle(), wx.FONTWEIGHT_BOLD)
                    self.SetItemText(item, text.replace(word, f"**{word}**"))  # Placeholder formatting
                    self.SetItemFont(item, bold_font)
                    item.is_bolded=True
        color_words = {"models": wx.Colour(0, 0, 255), "model": wx.Colour(255, 0, 0)}
        if color_words:
            for word, color in color_words.items():
                if word in text:
                    self.SetItemTextColour(item, color)  # Set specific color for the word
                    item.is_colored=True
        self.SetItemFont(item, base_font)
        self.ExpandAll()


        if 0:
            # Create a button and attach it to the tree item as a window
            button = wx.Button(self, label="Button")
            self.SetItemWindow(item, button)
            
            # Bind single-click button event and embed the item text directly
            button.Bind(wx.EVT_BUTTON, lambda event: self.OnButtonClicked(event, text))
        
        if data is not None:
            self.SetItemData(item, data)
            
        return item
    def UpdateMultilineItem(self, item_id, new_text, new_data=None, max_line_length=50):
        # Check if item exists with the given item_id
        if item_id in self.html_items:
            item = self.html_items[item_id]
            
            # Split text into multiple lines if it exceeds the max_line_length
            if len(new_text) > max_line_length:
                lines = [new_text[i:i+max_line_length] for i in range(0, len(new_text), max_line_length)]
                multiline_text = "\n".join(lines)
            else:
                multiline_text = new_text
            
            # Update the text of the item with multiline text
            self.SetItemText(item, multiline_text)
            
            # Update the data if new_data is provided
            if new_data is not None:
                self.SetItemData(item, new_data)
            base_font = wx.Font(11, wx.FONTFAMILY_DEFAULT, wx.FONTSTYLE_NORMAL, wx.FONTWEIGHT_NORMAL)
            bold_words = ["Apache", "Pyspark", "Oracle", "PL/SQL", "Hints", "Airflow", 'models', 'model']
            if bold_words:
                for word in bold_words:
                    if word in multiline_text:
                        bold_font = wx.Font(base_font.GetPointSize(), base_font.GetFamily(),
                                            base_font.GetStyle(), wx.FONTWEIGHT_BOLD)
                        self.SetItemText(item, multiline_text.replace(word, f"**{word}**"))  # Placeholder formatting
                        self.SetItemFont(item, bold_font)
            color_words = {"models": wx.Colour(0, 0, 255), "model": wx.Colour(255, 0, 0)}
            if color_words:
                for word, color in color_words.items():
                    if word in multiline_text:
                        self.SetItemTextColour(item, color)  # Set specific color for the word

            return item  # Return the updated item if needed
        else:
            print(f"Item with ID {item_id} not found.")
            return None   
    def OnButtonClicked(self, event, item_text):
        # Display the message with the embedded item text
        wx.MessageBox(f"Button clicked on item '{item_text}'")

    def OnSingleClick(self, event):
        # Cancel any pending single-click
        if self.single_click_delayed:
            self.single_click_delayed.Stop()

        # Get the item and the flags at the position of the click
        pos = event.GetPosition()
        item, flags = self.HitTest(pos)
        print (f"OnSingleClick: item: {item}, flags: {flags}")
        # Check if the click was on the expand/collapse button, if so, skip single-click action
        if flags & CT.TREE_HITTEST_ONITEMBUTTON:
            event.Skip()  # Allow the tree to handle the expand/collapse
            return

        # Set a delayed call for single-click, allowing for a double-click check
        self.single_click_delayed = wx.CallLater(160, self.ProcessSingleClick, item, event)

    def ProcessSingleClick(self, item, event):
        # Get the item at the position of the single click
        pos = event.GetPosition()
        item1, flags = self.HitTest(pos)
        print (f"ProcessSingleClick: item: {item}, flags: {flags}")
        if item:
            # Ensure the item is highlighted (selected)
            self.SelectItem(item)

            # Retrieve the button (or any window) associated with the item
            window = self.GetItemWindow(item)
            
            # Check if the window is a button or simply log the item text
            item_text = self.GetItemText(item)
            if isinstance(window, wx.Button):
                #wx.MessageBox(f"Single click detected on button of item '{item_text}'")
                print (f"Single click detected on BUTTON of item '{item_text}'")
            else:
                #wx.MessageBox(f"Single click detected on item '{item_text}' without button")
                print (f"Single click detected on item '{item_text}' without button")
        
        # Clear the delayed call reference
        self.single_click_delayed = None

    async def OnDoubleClick(self, event):
        # Cancel the single-click action if double-click detected
        print("OnDoubleClick")
        if self.single_click_delayed:
            self.single_click_delayed.Stop()
            self.single_click_delayed = None
        
        # Get the item at the position of the double-click
        pos = event.GetPosition()
        item, flags = self.HitTest(pos)
        print (f"OnDoubleClick: item: {item}, flags: {flags}")
        if item:
            # Ensure the item is highlighted (selected)
            self.SelectItem(item)
            
            # Check if the item is expanded, and re-expand it if needed
            if self.IsExpanded(item):
                self.Expand(item)
            if 0:
                # Retrieve the button (or any window) associated with the item
                window = self.GetItemWindow(item)
                
                # Check if the window is a button
                if isinstance(window, wx.Button):
                    item_text = self.GetItemText(item)
                    #wx.MessageBox(f"Button double-clicked on item '{item_text}'")
                    print (f"Button double-clicked on item '{item_text}'")  
                else:
                    item_text = self.GetItemText(item)
                    print (f"Double-clicked on item '{item_text}' without button")
            if 1:
            # Get the selected row index and the data in the row
                item_text = self.GetItemText(item)
                await self.ask_model(item_text)
        # Skip the event to allow other handlers to process it
        event.Skip()
    async  def ask_model(self, prompt):
        #assert prompt.strip()
        print(8888, 'ask_model', prompt)
        #print(8888, 'self.formatted_item', self.formatted_item)
        pub.sendMessage("set_header", msg=prompt)
        
        if apc.mock:
            await self.mock_stream_response(prompt) 
        else:
            await apc.processor.run_stream_response(prompt)  
    async def mock_stream_response(self, prompt):
        """Mock streaming response for testing."""
        print(9999, 'mock_stream_response', prompt)
        responses = [
            f'{prompt}<br>',
            "This is the second response.<br>",
            "This is the third response.<br>",
            "This is the fourth response.<br>",
            "This is the fifth response.<br>",
        ]

        for response in responses:
            #pub.sendMessage("display_response", response=response)
            await apc.processor.queue.put(response)
            await asyncio.sleep(0.1)   
        pub.sendMessage("done_display", response=())

class TranscriptionTreePanel(wx.Panel):
    def __init__(self, parent):
        super().__init__(parent)
        self.tree = MultiLineTreeCtrl(self)
        # Add root and example items
        self.root = self.tree.AddRoot("Root")
        if 0:
            # Add multiline items
            parent1 = self.tree.AppendMultilineItem(root, "Parent Item 1\nWith multiple lines\nof text")
            child1 = self.tree.AppendMultilineItem(parent1, "This is a child item\nwith two lines")
            child2 = self.tree.AppendMultilineItem(parent1, "Another child Another child Another child Another child Another child Another child Another child Another child Another child\nwith even more\nlines of text\nto display")
            child3 = self.tree.AppendMultilineItem(child2, "Another child\nwith even more\nlines of text\nto display")
            parent2 = self.tree.AppendMultilineItem(root, "Parent Item 2\nAlso multiline")
            
            # Expand all items
            self.tree.ExpandAll()
        
        # Layout the frame
        
        sizer = wx.BoxSizer(wx.VERTICAL)
        sizer.Add(self.tree, 1, wx.EXPAND)
        self.SetSizer(sizer)
        self.Layout()
        pub.subscribe(self.on_test_populate, "test_populate") 
        pub.subscribe(self.on_stream_closed, "stream_closed")  
        #pub.subscribe(self.on_ask_model_event, "ask_model")
      
    def  _on_stream_closed(self, data):
        transcript, corrected_time, tid=    data
        #print (7777, tid, transcript, corrected_time, tid)
        if transcript.strip():
            parent = self.tree.AppendMultilineItem(self.root, f"{transcript}")
            self.tree.ExpandAll()
            self.tree.Refresh()

    def _on_test_populate(self):
        print('on_test_populate')
        #self.tree.DeleteAllItems()
        root = self.root
        
        # Add multiline items
        parent1 = self.tree.AppendMultilineItem(root, "Tell me more about Oracle")
        child1 = self.tree.AppendMultilineItem(parent1, "Tell me more about Oracle PL/SQL")
        child2 = self.tree.AppendMultilineItem(parent1, "Tell me more about Oracle Hints")
        child3 = self.tree.AppendMultilineItem(child2, "Tell me more about Apache Pyspark")
        parent2 = self.tree.AppendMultilineItem(root, "Tell me more about Apache Airflow")
        
        # Expand all items
        self.tree.ExpandAll()