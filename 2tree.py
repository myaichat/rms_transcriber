import wx
import wx.lib.agw.customtreectrl as CT
from pubsub import pub
from pprint import pprint as pp
import asyncio

# Assuming the previous CustomHtmlListBox and MultiLineHtmlTreeCtrl code is already provided here

import wx
import wx.lib.agw.customtreectrl as CT
from wx.lib.pubsub import pub
import asyncio
from pprint import pprint as pp
#from rms_transcriber import apc
from rms_transcriber.include.config import init_config
apc = init_config.apc


import wx
import wx.html
from pubsub import pub
from pprint import pprint as pp

class CustomHtmlListBox(wx.html.HtmlListBox):
    def __init__(self, tid, parent, text_item, tree_ctrl, tree_item, id=wx.ID_ANY, size=(200, 180)):
        super(CustomHtmlListBox, self).__init__(parent, id, size=size)
        self.text_item = text_item
        self.tid=tid
        self.tree_ctrl = tree_ctrl  # Reference to the tree control
        self.tree_item = tree_item  # Reference to the corresponding tree item
        self.formatted_item = None
        self.SetItemCount(0)  # Initial item count
        self.Bind(wx.EVT_LEFT_DCLICK, self.on_double_click)
        self.Bind(wx.EVT_LEFT_DOWN, self.on_single_click)
        #self.SetBackgroundColour(wx.Colour(255, 255, 255))
        #self.SetBackgroundColour(wx.Colour(211, 211, 211))
        
        # Remove the border by setting a simple style
        self.SetWindowStyleFlag(wx.BORDER_NONE)
        self.Bind(wx.EVT_SET_FOCUS, self.on_focus)
        self.Bind(wx.EVT_KILL_FOCUS, self.on_focus_lost)
        self.single_click_delayed = None
        self.add_history_item(text_item)
        self.Bind(wx.EVT_PAINT, self.on_paint) 
        self.Bind(wx.EVT_MOUSEWHEEL, self.on_mouse_wheel)
        self.Bind(wx.EVT_SCROLLWIN, self.on_scroll)
        self.Bind(wx.EVT_SCROLLWIN_THUMBRELEASE, self.on_scroll)
        self.Bind(wx.EVT_SCROLLWIN_LINEUP, self.on_scroll)
        self.Bind(wx.EVT_SCROLLWIN_LINEDOWN, self.on_scroll)
        pub.subscribe(self.on_resize, "panel_resize")
    def on_resize(self, event): 
        #print('on_resize')
        #self.adjust_size_to_fit_content(self.text_item)
        max_width = self.GetParent().GetSize().width - 75 
        x, y=self.GetSize()
        self.SetSize((max_width, y))       
    def on_mouse_wheel(self, event):
        # Do nothing to disable scroll
        #print('on_mouse_wheel')
        pass
    
    def on_scroll(self, event):
        # Prevent all scrolling
        print('on_scroll')
        pass

    def add_history_item(self, item):
        """Add a new history item with multiline text to the HtmlListBox."""
        #pp(item)

        #self.history_items.append(formatted_text)
        #self.SetItemCount(len(self.history_items))
        formatted_text=self.adjust_size_to_fit_content(item)
        self.formatted_item=formatted_text
        self.SetItemCount(1)
        self.Refresh()
        pp(self.GetParent())
        self.GetParent().EnsureVisible(self.tree_item)
        self.GetParent().ScrollPages(1)
        self.GetParent().GetParent().ScrollPages(1)

    def adjust_size_to_fit_content(self, text_item):
        """Calculate and adjust the size of the list box based on the content and LeftPanel width, with scroll check."""
        # Get the width of the LeftPanel (parent's parent in this case)
        max_width = self.GetParent().GetSize().width - 75  # Padding to prevent overflow

        # Use a device context to measure the text size
        dc = wx.ClientDC(self)
        dc.SetFont(self.GetFont())
        text = text_item

        # Measure each line of text and wrap if necessary
        lines = text.split("\n")
        wrapped_lines = []
        total_height = 0

        for line in lines:
            line_width, line_height = dc.GetTextExtent(line)
            if line_width > max_width:
                # Wrap the line manually if it exceeds max width
                wrapped_line = ""
                for word in line.split(" "):
                    test_line = f"{wrapped_line} {word}".strip()
                    test_width, _ = dc.GetTextExtent(test_line)
                    if test_width > max_width:
                        wrapped_lines.append(wrapped_line)
                        wrapped_line = word
                        total_height += line_height
                    else:
                        wrapped_line = test_line
                wrapped_lines.append(wrapped_line)
                total_height += line_height
            else:
                wrapped_lines.append(line)
                total_height += line_height

        # Set the total width and height with padding
        text_length = len(text)
        dynamic_padding = 20 + int(text_length / 25)  # Adjust base padding for longer text

        # Check the height-to-width ratio and adjust padding accordingly
        if total_height > max_width:
            # Increase padding further if the content height is greater than the available width
            dynamic_padding += int(total_height / 20)  # Increase padding based on height

        # Set the total width and height with dynamic padding
        adjusted_height = total_height + dynamic_padding

        # Check if the item would require scrolling by comparing the adjusted height to the current height
        current_height = self.GetSize().height
        if  0 and adjusted_height > current_height:
            # If the adjusted height is greater, increase the height a bit more to avoid scrolling
            adjusted_height += 20  # Additional height if scrolling is needed

        # Set the size of the list box, limiting the width to max_width
        self.SetSize((max_width, adjusted_height))

        # Refresh with wrapped content if necessary
        html_text = text.replace("\n", "<br>")
        formatted_text = f"""<span style="color: #2d2d2d; font-size: 14px; font-family: Arial, sans-serif;">{html_text}</span>"""        




        # Update the size of the HtmlListBox
        #self.SetSize((max_width, total_height))
        return formatted_text
    def on_paint(self, event):
        """Handle paint event to draw scroll indicators if needed."""
        # First call the default paint method
        event.Skip()
        if 0:
            # Check if content is overflowing
            if self.is_content_overflowing():
                dc = wx.PaintDC(self)
                width, height = self.GetSize()

                # Draw indicators at the top or bottom if content is hidden
                if self.has_hidden_top_content():
                    dc.DrawText("^ More above", 5, 5)  # Top indicator

                if self.has_hidden_bottom_content():
                    dc.DrawText("v More below", 5, height - 20)  # Bottom indicator


    def has_hidden_top_content(self):
        """Check if any content is hidden at the top (i.e., user scrolled down)."""
        # Placeholder: logic for detecting top hidden content
        return self.GetViewStart()[1] > 0  # `GetViewStart` gives the current scroll offset

    def has_hidden_bottom_content(self):
        """Check if any content is hidden at the bottom."""
        dc = wx.ClientDC(self)
        dc.SetFont(self.GetFont())

        # Calculate total content height
        total_content_height = 0
        for item in self.history_items:
            _, item_height = dc.GetTextExtent(item)
            total_content_height += item_height + 5  # Adding small padding between items

        # Check if scrolled to the bottom
        visible_height = self.GetSize().height
        current_scroll_position = self.GetScrollPos(wx.VERTICAL)
        return (total_content_height - current_scroll_position) > visible_height
    def on_focus(self, event):
        #self.SetBackgroundColour(wx.Colour(255, 255, 255))
        #self.SetBackgroundColour(wx.Colour(211, 211, 211))
        #self.Refresh()
        event.Skip()

    def on_focus_lost(self, event):
        self.SetBackgroundColour(wx.Colour(255, 255, 255))
        #self.Refresh()
        #event.Skip()

    def on_single_click(self, event):
        if self.single_click_delayed:
            self.single_click_delayed.Stop()        
        # Highlight the corresponding tree item on single click
        print("Single click in HtmlListBox")
        self.tree_ctrl.SelectItem(self.tree_item)
        #self.SetBackgroundColour(wx.Colour(211, 211, 211)) 
        #event.Skip()
        #self.SetBackgroundColour(wx.Colour(255, 255, 255))
        self.single_click_delayed = wx.CallLater(160, self.ProcessSingleClick, self.tree_item, event)        
    def ProcessSingleClick(self, item, event):
        if item:
            # self.SelectItem(item)
            print("Single click detected on item in tree")
        self.single_click_delayed = None
        self.SetBackgroundColour(wx.Colour(240, 240, 240)) 
    def on_double_click(self, event):
        if self.single_click_delayed:
            self.single_click_delayed.Stop()
            self.single_click_delayed = None        
        # Highlight the corresponding tree item on double click
        print("Double click in HtmlListBox")
        self.tree_ctrl.SelectItem(self.tree_item)
        self.SetBackgroundColour(wx.Colour(255, 255, 255))
        #item_index = self.tree_ctrl.GetIndexOfItem(self.tree_item)  # or define an index if needed
        #if item_index < len(self.history_items):
        pp( self.formatted_item)        
        #
        #event.Skip()
        print('is_scrollable:', self.is_scrollable())
        #print ('has_hidden_top_content:',self.has_hidden_top_content())
        print ('is_content_overflowing:',self.is_content_overflowing())

    def is_content_overflowing(self):
        """Check if the content height exceeds the visible height of the list box."""
        dc = wx.ClientDC(self)
        dc.SetFont(self.GetFont())
        
        total_content_height = 0
        for item in [self.formatted_item]:
            # Measure each line accurately, including wrapped lines
            text_lines = item.split("<br>")  # Assuming HTML <br> tags are used for new lines
            for line in text_lines:
                _, item_height = dc.GetTextExtent(line)
                total_content_height += item_height + 5  # Adding small padding between lines
                
        # Print the calculated content height and control height for debugging
        control_height = self.GetSize().height
        print(f"Total Content Height: {total_content_height}, Control Height: {control_height}")
        
        # Check if total content height is greater than the current control height
        is_overflowing = total_content_height > control_height
        print("is_content_overflowing:", is_overflowing)  # Debug statement
        return is_overflowing

    def is_scrollable(self):
        """Check if any part of the content is scrollable by comparing content and control height."""
        return self.is_content_overflowing()        

    def OnGetItem(self, index):
        if self.tid%2==1:
            self.SetBackgroundColour(wx.Colour(255, 255, 255))
        else:
            self.SetBackgroundColour(wx.Colour(240, 240, 240))
        return f"<div style='padding: 10px; background-color: #ffffff;'>{self.formatted_item}</div>"

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
        print('on_test_populate')
        #self.tree.DeleteAllItems()
        root = self.root
        
        # Add multiline items
        
        # Add parent and child items with unique HTML content for each HtmlListBox
        for i in range(5):
            parent1 = self.AppendMultilineItem(f'{i}:{i}', self.root, 'Tell me more about Apache Pyspark\nTell me more about Apache Pyspark\nTell me more about Apache Pyspark\nTell me more about Apache Pyspark\nTell me more about Apache Pyspark\nTell me more about Apache Pyspark')
   
       
        
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
            print('|'*80)
            pp(transcript)
            print('|'*80)
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
            if 0:
                # Adjust layout to reflect the changes
                new_html_item.adjust_size_to_fit_content(transcript)
                self.Layout()
                
                # Optionally expand/collapse to force a refresh if needed
                self.Collapse(tree_item)
                self.Expand(tree_item)

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
            self.ExpandAll()  # Expanding within the main thread       


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

    def UpdateMultilineItem(self, item_id, parent, text_item, data=None):
        assert item_id in self.html_items, f"Item ID {item_id} not found in html_items"
        
        # Access the HtmlListBox for the specific item
        html_item = self.html_items[item_id]
        
        # Add the new content and adjust the size accordingly
        html_item.add_history_item(text_item)
        
        # Adjust the size to fit new content
        html_item.adjust_size_to_fit_content(text_item)
        html_item.Update()  # Refresh the HtmlListBox
        if 1:
            
            # Invalidate the best size and trigger layout recalculation for the tree control
            self.InvalidateBestSize()
            self.Layout()
            
            # Optionally collapse and expand the specific item if necessary to force a refresh
            self.Collapse(html_item.tree_item)
            self.Expand(html_item.tree_item)
            
            # Expand all to ensure visibility for the updated item, if needed
            self.ExpandAll()              

    
    def AppendMultilineItem(self, item_id, parent, text_item, data=None):
        # Append an item with an empty string as the text

        # Create an instance of CustomHtmlListBox with specific items, passing tree control and item references
        if  item_id not in self.html_items:
            item = self.AppendItem(parent, "")
            if data is not None:
                self.SetItemData(item, data)
            self.tid += 1

            self.html_items[item_id]=html_list_box = CustomHtmlListBox(self.tid,self, text_item, self, item,  size=(400, 480))

            #html_list_box.Enable(False)
            self.SetItemWindow(item, html_list_box)
            html_list_box.SetMinSize((400, 480))
            html_list_box.SetMaxSize((400, 480))
            
            self.InvalidateBestSize()
            self.Layout()            
        
            # Add sample history items to the HtmlListBox
            #html_list_box.add_history_item("First line\nSecond line\nThird line")
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
            print("Single click detected on item in tree")
        self.single_click_delayed = None

    def OnDoubleClick(self, event):
        if self.single_click_delayed:
            self.single_click_delayed.Stop()
            self.single_click_delayed = None

        pos = event.GetPosition()
        item, flags = self.HitTest(pos)
        if item:
            self.SelectItem(item)
            print("Double-clicked on item in tree")
        event.Skip()

# Define the Main Application Frame
class MainFrame(wx.Frame):
    def __init__(self, *args, **kwargs):
        super(MainFrame, self).__init__(*args, **kwargs)

        # Set up the main panel and layout
        panel = wx.Panel(self)
        vbox = wx.BoxSizer(wx.VERTICAL)

        # Add the MultiLineHtmlTreeCtrl to the panel
        self.tree_ctrl = MultiLineHtmlTreeCtrl(panel)
        vbox.Add(self.tree_ctrl, 1, wx.EXPAND | wx.ALL, 5)

        panel.SetSizer(vbox)

        # Set the frame's properties
        self.SetTitle("HTML Tree Control Example")
        self.SetSize((800, 600))
        self.Centre()

        # Initialize the tree with some example data
        pub.sendMessage("test_populate")  # Triggers test population in the tree

# Define the Application Class
class MyApp(wx.App):
    def OnInit(self):
        # Create the main application window
        frame = MainFrame(None)
        frame.Show()
        return True

# Run the Application
if __name__ == "__main__":
    app = MyApp(False)
    app.MainLoop()
