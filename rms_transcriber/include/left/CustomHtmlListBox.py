
import wx
import wx.html
from pubsub import pub
from pprint import pprint as pp

class CustomHtmlListBox(wx.html.HtmlListBox):
    def __init__(self, tid, parent, text_item, tree_ctrl, tree_item, id=wx.ID_ANY, size=(200, 80)):
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