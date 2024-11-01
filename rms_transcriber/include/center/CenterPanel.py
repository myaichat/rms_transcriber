
import re
import sys
import asyncio
import wx
import wx.html2
from urllib.parse import unquote
from pubsub import pub
from wxasync import WxAsyncApp, AsyncBind
import markdown2
from pygments import highlight
from pygments.lexers import PythonLexer
from pygments.formatters import HtmlFormatter
from ..config import init_config
apc = init_config.apc

class AppLog_Controller():
    def __init__(self):
        self.set_log()
        self.header='App Log'
        self.history=[]
        self.page_history=[]
        self.page_forward=[]
        
        #pub.subscribe(self.on_log, "applog")
        pub.subscribe(self.done_display, "done_display")
        pub.subscribe(self.display_response, "display_response")
        pub.subscribe(self.set_header, "set_header")
        pub.subscribe(self.on_page_back, "back")
        pub.subscribe(self.on_page_forward, "forward")  
    def on_page_back(self):
        if self.page_history:

            if 1:
                #print(333333, self.page_history)
                forward=self.page_history.pop()
                self.page_forward.append(forward)   
                self.update_back()
                self.update_forward() 
            self.load_from_file(self.page_history[-1])              
    def on_page_forward(self):
        print('on_page_forward')
        if self.page_forward:
            #print(333333, 'on_page_forward', self.page_forward)


           
            forward=self.page_forward.pop()
            self.page_history.append(forward)    
            self.load_from_file(forward)
            self.update_forward()
            self.update_back()
    def update_forward(self):
        if self.page_forward:
            self.enable_forward()
        else:
            self.disable_forward()
    def set_header(self, msg):
        self.history +=self.applog
        self.applog=[]  
                
        self.applog.append({'text':msg,'type':'header'})
        self.applog.append({'text':'','type':'info'})
        self.replace_header(msg)
  
    def done_display(self, response):
        #print(333333, 'done_display')
        #self.applog.append('<br><br>')
        tmp_file=self.save_html()
        self.page_history.append(tmp_file) 
        self.update_back()
        self.flip_colors()

    def update_back(self):
        if len(self.page_history)>1:
            self.enable_back()
        else:
            self.disable_back()
        #wx.CallAfter(self.refresh_log_with_history)
    def display_response(self, response):
        #e()
        if not self.applog:
            row={'text':response,'type':'info'}
            self.applog.append(row)
        else:
            row = self.applog[-1] 
            row["text"] +=response #.replace("\n", "<br>")
            self.applog[-1]=row
        #self.add_log_entry(response)
        
        self.replace_log_content(row["text"] )   
        #wx.CallAfter(self.refresh_log)
       
    def replace_log_content(self, content):
        # Step 1: Convert Markdown to HTML with fenced code blocks enabled
        html_content = markdown2.markdown(content, extras=["fenced-code-blocks"])

        # Step 2: Initialize Pygments formatter with inline CSS for syntax highlighting
        formatter = HtmlFormatter(nowrap=True, style="colorful")
        css_styles = formatter.get_style_defs('.highlight')

        # Custom block code styling (includes font-size and background)
        block_code_style = (
            "background-color: #f4f4f4; color: #008000; padding: 10px; "
            "border-radius: 5px; font-family: monospace;  line-height: 1.8; font-size: 10px;"
        )
        # Inline code styling (for single-line inline code snippets)
        inline_code_style = "background-color: #f4f4f4; color: #008000; font-family: monospace; font-size: 14px; padding: 2px 4px; border-radius: 3px;"

        custom_code_style = """
                code {
                    font-family: "Courier New", Courier, monospace;
                    font-size: 0.875em;
                    color: #2d2d2d;
                    background-color: #f6f6f6;
                    padding: 2px 4px;
                    border-radius: 3px;
                    white-space: nowrap;
                    overflow-wrap: break-word;
                }
                pre code {
                    font-family: "Courier New", Courier, monospace;
                    font-size: 0.875em;
                    color: #2d2d2d;
                    background-color: #f6f6f6;
                    padding: 2px 4px;
                    border-radius: 3px;
                    white-space: pre;
                    overflow-wrap: break-word;
                }
            """



        # Replace <pre><code>...</code></pre> blocks with highlighted HTML
        highlighted_html_content =  html_content.replace(
                    '<code>', f'<code style="{inline_code_style}">'
                ).replace(
                    '<pre><code>', f'<pre style="{block_code_style}"><code>'
                ).replace(
                    '</code></pre>', '</code></pre>'
                )


        # Step 4: Assemble final HTML with Pygments CSS for syntax colors
        final_content = f"""
        <style>
            {css_styles}
            {custom_code_style}
            /* Specific token coloring to make keywords and operators green */
            .highlight .k, .highlight .n, .highlight .o {{ color: #008000; }}
        </style>
        {highlighted_html_content}
        """

        # Escape backticks for JavaScript compatibility
        sanitized_content = final_content.replace("`", "\\`")
        
        # Inject the processed HTML content into the webview
        #self.web_view.RunScript(f"replaceLogContent(`{sanitized_content}`);")
        if self.auto_scroll_on:

            self.web_view.RunScript(f"""
                replaceLogContent(`{sanitized_content}`);
                setTimeout(() => {{
                    window.scrollTo(0, document.body.scrollHeight);
                }}, 100);
            """)
        else:
            self.web_view.RunScript(f"replaceLogContent(`{sanitized_content}`);")
    def replace_header(self, content):
        # Use JavaScript to replace content in the header row
        sanitized_content = content.replace("`", "\\`")+f' [{self.model_name}]'  # Escape backticks for JavaScript
        self.web_view.RunScript(f"replaceHeader(`{sanitized_content}`);")
    def append_log_content(self, content):
        # Use JavaScript to append content to the single row
        sanitized_content = content.replace("`", "\\`")  # Escape backticks for JavaScript
        self.web_view.RunScript(f"appendToLog(`{sanitized_content}`);")
   
    def _on_log(self, msg, type):
    
        if 1:

            if type == "error":
                msg = f'<span style="color:red">{msg}</span>'            
            self.applog.append(msg)

        wx.CallAfter(self.refresh_log)
    def set_log(self):
        self.applog = []

    def get_log(self):
        return self.applog

    def get_log_html(self):
        #header="<h1>App Log</h1>"
        import markdown2
        out=f'<table style="font-size: 16px;">'
        # Block code styling (for fenced code blocks)
        block_code_style = (
            "background-color: #f4f4f4; color: #008000; padding: 10px; "
            "border-radius: 5px; font-family: monospace;  line-height: 1.8; font-size: 10px;"
        )
        # Inline code styling (for single-line inline code snippets)
        inline_code_style = "background-color: #f4f4f4; color: #008000; font-family: monospace; padding: 2px 4px; border-radius: 3px;"


        for log in self.applog:
            text=log['text']
            rtype=log['type']
            #print(333333, rtype)
            if rtype=='header': 
                out += f'<tr><th style="text-align: left; font-size: 24px;">{text}</th></tr>'
            else:
                text = markdown2.markdown(text, extras=["fenced-code-blocks"])
            
                # Apply separate styling to block code and inline code
                text = text.replace(
                    '<code>', f'<code style="{inline_code_style}">'
                ).replace(
                    '<pre><code>', f'<pre style="{block_code_style}"><code>'
                ).replace(
                    '</code></pre>', '</code></pre>'
                )
                out += f'<tr><td>{text}</td></tr>'
        out += "</table>"
        #pp(out)
        return out
    def get_hist_log_html(self):
        #header="<h1>App Log</h1>"

        out=f'<table style="font-size: 16px;">'
        for log in self.history:
            text=log['text']
            rtype=log['type']
            #print(333333, rtype)
            if rtype=='header': 
                out += f'<tr><th style="text-align: left; font-size: 24px;">{text}</th></tr>'
            else:
                out += f'<tr><td>{text}</td></tr>'   
        out += "</table>"
        return out
    def refresh_log_with_history(self):
        html=self.get_log_html()
        hist=html=self.get_history_log_html()
        new_html = """
        <html>
        <body>
        <pre>
        %s
        </pre>
        <pre>
        %s
        </pre>        
        </body>
        </html>
        """   % (html,hist) 
        #print(444444, new_html)     
        self.web_view.SetPage(new_html, "")
    
    def refresh_log(self):
        html=self.get_log_html()
        new_html = """
        <html>
        <body>
        <pre>
        %s
        </pre>
        </body>
        </html>
        """   % html 
        #print(444444, new_html)     
        self.web_view.SetPage(new_html, "")

class CustomSchemeHandler_Log(wx.html2.WebViewHandler):
    def __init__(self, web_view_panel):
        wx.html2.WebViewHandler.__init__(self, "app")
        self.web_view_panel = web_view_panel

    def OnRequest(self, webview, request):
        print(f"Log: OnRequest called with URL: {request.GetURL()}")
        if request.GetResourceType() == wx.html2.WEBVIEW_RESOURCE_TYPE_MAIN_FRAME:
            if request.GetURL() == "app:test":
                wx.CallAfter(self.web_view_panel.on_test_button)
            elif request.GetURL() == "app:url_test":
                wx.CallAfter(self.web_view_panel.on_url_test)
        return None  
class ProcessorPanel(wx.Panel,AppLog_Controller):
    def __init__(self, parent):
        super().__init__(parent)
        AppLog_Controller.__init__(self)
        
        # Create the WebView control
        self.web_view = wx.html2.WebView.New(self)
        
        # Attach custom scheme handler
        self.attach_custom_scheme_handler()

        # Bind navigation and error events
        self.web_view.Bind(wx.html2.EVT_WEBVIEW_NAVIGATING, self.on_navigating)
        #self.web_view.Bind(wx.EVT_CONTEXT_MENU, self.on_right_click)
        #self.web_view.Bind(wx.html2.EVT_WEBVIEW_ERROR, self.on_webview_error)
        #self.web_view.Bind(wx.EVT_CONTEXT_MENU, self.show_popup_menu)
        self.create_navigation_panel()
        # Set initial HTML content
        self.set_initial_content()

        # Create sizer to organize the WebView
        sizer = wx.BoxSizer(wx.VERTICAL)
        sizer.Add(self.web_view, 1, wx.EXPAND, 0)
        sizer.Add(self.nav_panel, 0, wx.EXPAND | wx.ALL, 0)
        self.SetSizer(sizer)
        self.content_buffer = ""
        pub.subscribe(self.ask_model, "ask_model")
        self.Layout()
        self.listen_on=False
        self.scroll_to_bottom=False
    def ask_model(self, prompt):
        self.ask_model_text.SetValue(prompt)  
        asyncio.create_task(self.on_ask_model_button(None))
    async def consume_askmodel_queue(self, queue):
        # Continuously consume the queue and update WebView
        while True:
            content = await queue.get()
            #print('\n\tconsume_queue: ',content)
            #pub.sendMessage("display_response", response=content)  # Send the content to the WebView
            #wx.CallAfter(self.update_text, content)  # Update UI safely in the main thread
            queue.task_done()
            self.content_buffer += content        
    async def update_webview_periodically(self):
        while True:
            if self.content_buffer:
                #print('ProcessorPanel', self.content_buffer)
                pub.sendMessage("display_response", response=self.content_buffer)
                #wx.CallAfter(self.update_text, self.content_buffer)
                self.content_buffer = ""  # Clear buffer after update
            await asyncio.sleep(0.2)  # Update every 200ms        

    def enable_forward(self):
        self.forward_button.Enable(True)
        self.forward_button.SetForegroundColour(wx.Colour(0, 0, 255))  # Active blue
        font = self.forward_button.GetFont()
        font.SetUnderlined(True)
        self.forward_button.SetFont(font)          
    def disable_forward(self):
        self.forward_button.Enable(False)
        self.forward_button.Enable(False)  
        self.forward_button.SetForegroundColour(wx.Colour(150, 150, 150))  # Disabled gray
        font = self.forward_button.GetFont()
        font.SetUnderlined(False)
        self.forward_button.SetFont(font)         
    def enable_back(self):
        self.back_button.Enable(True)
        self.back_button.SetForegroundColour(wx.Colour(0, 0, 255))  # Active blue
        font = self.back_button.GetFont()
        font.SetUnderlined(True)
        self.back_button.SetFont(font)        
    def disable_back(self):
        self.back_button.Enable(False)  
        self.back_button.SetForegroundColour(wx.Colour(150, 150, 150))  # Disabled gray
        font = self.back_button.GetFont()
        font.SetUnderlined(False)
        self.back_button.SetFont(font)                       
    def create_navigation_panel(self):
        """Creates the navigation panel with Back and Forward buttons in opposite corners."""
        self.nav_panel = wx.Panel(self)
        nav_sizer = wx.BoxSizer(wx.HORIZONTAL)
        self.nav_panel.SetBackgroundColour(wx.Colour(255, 255, 255))
        # Back Button
        self.back_button = back_button=wx.StaticText(self.nav_panel, label="Back")
        l_sizer= wx.BoxSizer(wx.VERTICAL)
        if 1:  
            back_button.Bind(wx.EVT_LEFT_DOWN, self.on_back)
            #nav_sizer.Add(back_button, 0, wx.ALL, 5)
            font = back_button.GetFont()
            font.SetUnderlined(True)
            font.SetPointSize(12)  # Set to desired font size
            back_button.SetFont(font)           
            self.back_button.SetForegroundColour(wx.Colour(0, 0, 255))  # Blue for active state
            self.disable_back()
        if 1:
            self.listen_button = wx.Button(self.nav_panel, label="Listen:OFF")
            self.listen_button.SetMinSize((-1, 60)) 
            self.listen_button.SetBackgroundColour(wx.Colour(255, 228, 181))  # Light color for visibility
            
            self.listen_button.Bind(wx.EVT_BUTTON, self.on_listen)   

        if 1:
            self.auto_scroll_button = wx.Button(self.nav_panel, label="Auto Scroll\nOFF")
            self.auto_scroll_button.SetBackgroundColour(wx.Colour(144, 238, 144))  # Green for ON state
            self.auto_scroll_button.Bind(wx.EVT_BUTTON, self.on_auto_scroll_button)
            self.auto_scroll_button.SetMinSize(wx.Size(-1, -1))
            self.auto_scroll_on = False  # Initial state            
          

        l_sizer.Add(back_button, 0, wx.ALL , 5)         
        l_sizer.Add(self.listen_button, 0, wx.ALL, 5) 
        l_sizer.Add(self.auto_scroll_button, 0, wx.ALL, 5)  
        nav_sizer.Add(l_sizer, 0,  wx.ALL, 5)       
        if 1:

            # Add a spacer to push the "Forward" button to the far right
            #nav_sizer.AddStretchSpacer(1)
            self.ask_model_text = wx.TextCtrl(self.nav_panel, style=wx.TE_MULTILINE)
            self.ask_model_text.SetMinSize((200, 60))  # Set width and height as needed
            
            nav_sizer.Add(self.ask_model_text, 1, wx.EXPAND | wx.ALL, 5)   
            font = self.ask_model_text.GetFont()
            font.SetPointSize(11)  # Adjust the size as desired
            self.ask_model_text.SetFont(font)
            self.ask_model_text.Bind(wx.EVT_KEY_DOWN, self.on_key_down)
        m_sizer = wx.BoxSizer(wx.VERTICAL)
        if 1:
        
            self.ask_model_button = wx.Button(self.nav_panel, label="Ask Model")
            self.ask_model_button.SetBackgroundColour(wx.Colour(211, 211, 211))  # Green for ON state
            #self.ask_model_button.Bind(wx.EVT_BUTTON, self.on_ask_model_button)
            AsyncBind (wx.EVT_BUTTON, self.on_ask_model_button, self)
            self.ask_model_button.SetMinSize(wx.Size(-1, 80))
            m_sizer.Add(self.ask_model_button, 0, wx.ALL , 5)  # Add to the sizer
        if 1:
        
            self.clear_history_button = wx.Button(self.nav_panel, label="Clear\nHistory")
            self.clear_history_button.SetBackgroundColour(wx.Colour(211, 211, 211))  # Green for ON state
            #self.ask_model_button.Bind(wx.EVT_BUTTON, self.on_ask_model_button)
            self.clear_history_button.Bind(wx.EVT_BUTTON, self.on_clear_history_button)
            self.clear_history_button.SetMinSize(wx.Size(-1, -1))
            m_sizer.Add(self.clear_history_button, 0, wx.ALL , 5)  # Add to the sizer            
        nav_sizer.Add(m_sizer, 0, wx.ALL , 5)  
        if 0:
            self.model_names = ["gpt-3.5-turbo", "gpt-4o-mini", "gpt-4o", ]  # Populate with actual model names
            self.model_dropdown = wx.Choice(self.nav_panel, choices=self.model_names)
            self.model_dropdown.SetSelection(0)  # Set the default selection
            self.model_name = self.model_names[0]  # Set the default model name
            nav_sizer.Add(self.model_dropdown, 0, wx.ALL | wx.ALIGN_CENTER_VERTICAL, 5)  # Add to the sizer
            self.model_dropdown.Bind(wx.EVT_CHOICE, self.on_model_selection)
        if 1:
            # Model RadioBox (instead of dropdown)
            self.model_names = ["gpt-3.5-turbo", "gpt-4o-mini", "gpt-4o"]  # Populate with actual model names
            self.model_radio_box = wx.RadioBox(self.nav_panel, label="Select Model", choices=self.model_names,
                majorDimension=1, style=wx.RA_SPECIFY_COLS)
            self.model_radio_box.SetSelection(0)  # Set default selection
            self.model_name = self.model_names[0]  # Set default model name
            nav_sizer.Add(self.model_radio_box, 0, wx.ALL | wx.ALIGN_CENTER_VERTICAL, 5)
            self.model_radio_box.Bind(wx.EVT_RADIOBOX, self.on_model_selection)            

        if 1:     
            v_sizer = wx.BoxSizer(wx.VERTICAL)
            # Forward Button
            self.forward_button=forward_button = wx.StaticText(self.nav_panel, label="Forward")


            forward_button.Bind(wx.EVT_LEFT_DOWN, self.on_forward)
            v_sizer.Add(forward_button, 0, wx.ALL, 5)  # Removed wx.ALIGN_RIGHT
            font = forward_button.GetFont()
            font.SetPointSize(12)  # Set to desired font size
            forward_button.SetFont(font)  

            # Add padding to the top to remove the visible line
            #self.nav_panel.SetMinSize((-1, 25))  # Adjust height to fit the links with some padding
            self.color_square = wx.StaticText(self.nav_panel, label="  ", size=(20, 20))  # A blank label to act as a "square"
            self.color_square.SetBackgroundColour(wx.Colour(144, 238, 144))  # Start with green color
            self.is_processing = False  # Flag to track processing state
            v_sizer.Add(self.color_square, 0, wx.ALL , 5)
            nav_sizer.Add(v_sizer, 0, wx.ALL | wx.ALIGN_CENTER_VERTICAL, 5)
        self.nav_panel.SetSizer(nav_sizer)
        self.disable_forward()        
        # Optionally remove the border from WebView too
        self.web_view.SetWindowStyle(wx.NO_BORDER)   
        pub.subscribe(self.on_flip_colors, "ask_model")   
        #pub.subscribe(self.on_done_processing, "done_display")
        pub.subscribe(self.on_stream_closed, "stream_closed2")
    def on_auto_scroll_button(self, event):
        # Toggle auto-scroll state
        self.auto_scroll_on = not self.auto_scroll_on
        if self.auto_scroll_on:
            self.auto_scroll_button.SetLabel("Auto Scroll\nON")
            self.auto_scroll_button.SetBackgroundColour(wx.Colour(144, 238, 144))  # Green for ON
            #apc.auto_scroll = True  # Set your app's auto-scroll state
            #self.set_initial_content()
        else:
            self.auto_scroll_button.SetLabel("Auto Scroll\nOFF")
            self.auto_scroll_button.SetBackgroundColour(wx.Colour(255, 182, 193))  # Red for OFF
            #apc.auto_scroll = False  # Set your app's auto-scroll state

        self.auto_scroll_button.Refresh()  # Ensure color update is visible
        #self.set_initial_content()
    def on_clear_history_button(self, event):
        print('on_clear_history_button')
        apc.processor.clear_history()
    def on_listen(self, event):  
        print('on_listen')  
        self.listen_on = not self.listen_on
        self.listen_button.SetLabel(f"Listen:{'ON' if self.listen_on else 'OFF'}")
    def on_stream_closed    (self, data):
        transcript, corrected_time, tid, rid = data
        print('on_stream_closed')
        if self.listen_on:
            self.ask_model_text.SetValue(transcript)
            self.listen_on = not self.listen_on
            self.listen_button.SetLabel(f"Listen:{'ON' if self.listen_on else 'OFF'}")
    def on_key_down(self, event):
        # Check if Ctrl is pressed with Enter
        if event.ControlDown() and event.GetKeyCode() == wx.WXK_RETURN:
            self.on_ctrl_enter()  # Call your specific function for Ctrl+Enter
        else:
            event.Skip()  # Ensure other keys work as expected

    # Define the function to execute when Ctrl+Enter is pressed
    def on_ctrl_enter(self):
        # Replace with the desired action when Ctrl+Enter is pressed
        print("Ctrl+Enter was pressed")     
        asyncio.create_task(self.on_ask_model_button(None))
    async def on_ask_model_button(self, event):
        prompt = self.ask_model_text.GetValue()
        #pub.sendMessage("ask_model", prompt=prompt)
        self.flip_colors()
        self.display_response(f'<h3>{prompt} [{self.model_name}]</h3>')
        await apc.processor.run_stream_response(prompt,self.model_name) 
    def on_model_selection(self, event):
        """Handles the selection change in the model dropdown."""
        selected_model = self.model_dropdown.GetStringSelection()
        self.model_name = selected_model  # Update the selected model name
    def on_model_selection(self, event):
        # Get the selected model name based on the RadioBox selection
        selected_model_index = self.model_radio_box.GetSelection()
        selected_model_name = self.model_names[selected_model_index]

        # Set the processor's model name to the selected one
        self.model_name = selected_model_name
        
        # Optional: Print or log the selected model to verify
        print(f"Model selected: {selected_model_name}")
    def on_flip_colors(self, prompt):
        self.flip_colors()
    def on_done_processing(self, prompt):
        self.flip_colors()        
    def flip_colors(self):
        """Change the color of the square StaticText."""
        if self.is_processing:
            color = wx.Colour(144, 238, 144)
        else:
            color= wx.Colour(255, 182, 193)  # Red color
        self.is_processing = not self.is_processing
        
        self.color_square.SetBackgroundColour(color)
        self.color_square.Refresh()  # Ensure the new color is displayed
      
    def on_right_click(self, event):
        # Display the context menu only when there's selected text
        selected_text = self.get_selected_text()
        if selected_text:
            self.show_context_menu()

    def show_context_menu(self):
        # Create a custom context menu
        menu = wx.Menu()
        ask_model_item = menu.Append(wx.ID_ANY, "Ask Model")
        
        # Bind the menu item to an action
        #self.Bind(wx.EVT_MENU, self.on_ask_model, ask_model_item)
        AsyncBind(wx.EVT_MENU, self.on_ask_model, self)   
        self.ask_model_item_id = ask_model_item.GetId()
        
        # Show the context menu at the cursor position
        self.PopupMenu(menu)
        menu.Destroy()
    async def on_ask_model(self, event):
        # Use the selected text (stored when intercepted by on_navigating)
        if event.GetId() == self.ask_model_item_id:
            selected_text = getattr(self, 'selected_text', "No text selected").strip()
            
            if not selected_text:
                print(f"{self.__class__.__name__} : on_ask_model : No text selected")
                return
            # Check if Ctrl key is pressed
            if wx.GetKeyState(wx.WXK_CONTROL):
                # Show an editable dialog if Ctrl is pressed
                dialog = EditTextDialog(self, "Edit Selection", selected_text)
                if dialog.ShowModal() == wx.ID_OK:
                    edited_text = dialog.GetEditedText()
                    print(f"Edited text: {edited_text}")
                    pub.sendMessage("ask_model", prompt=edited_text)
                    # Here you can handle the edited text (e.g., pass it to the model)
                dialog.Destroy()
            else:
                # Default behavior when Ctrl is not pressed
                print(f"Selected text for model: {selected_text}")
                # Pass selected_text to your model for inference
                pub.sendMessage("ask_model", prompt=selected_text)
                await apc.processor.run_stream_response(selected_text,self.model_name)  

    def on_navigating(self, event):
        url = event.GetURL()
        if url.startswith("app://selection"):
            # Extract selected text from URL
            selected_text = url.split("text=")[-1]
            #pp(selected_text)
            self.selected_text = unquote(selected_text)  # Decode URL encoding
            #print(f"\n\n\n\tSelected text: {selected_text}")  # Handle the selected text as needed
            event.Veto()  # Prevent actual navigation for our custom scheme
            self.show_context_menu()
        elif url == "app://show_back_menu":
            event.Veto()  # Prevent navigation
            self.show_back_menu()   
    def show_back_menu(self):
        """Show a different context menu with 'Back' when no text is selected."""
        menu = wx.Menu()
        back_item = menu.Append(wx.ID_ANY, "Back")
        self.update_back()        
        # Bind the menu item to the on_back method
        self.Bind(wx.EVT_MENU, self.on_back, back_item)
        forward_item = menu.Append(wx.ID_ANY, "Forward")
        self.update_forward()
        
        # Bind the menu item to the on_back method
        self.Bind(wx.EVT_MENU, self.on_forward, forward_item)        
        # Show the context menu at the cursor position
        self.PopupMenu(menu)
        menu.Destroy()  
    def on_back(self, event):
       
        #print ("back")
        """Handle the 'Back' action to navigate back in the WebView."""
        pub.sendMessage("back") 
    def on_forward(self, event):
        #print ("forward")
        """Handle the 'Back' action to navigate back in the WebView."""
        pub.sendMessage("forward")                                    
    def attach_custom_scheme_handler(self):
        handler = CustomSchemeHandler_Log(self)
        self.web_view.RegisterHandler(handler)
        
    def save_html(self, html_source=None):
        import tempfile
        if not html_source:
            html_source= self.web_view.GetPageSource()
        with tempfile.NamedTemporaryFile(delete=False, suffix=".html") as tmp_file:
            tmp_file.write(html_source.encode('utf-8'))
            tmp_file_path = tmp_file.name
        return tmp_file_path
        # Load the HTML content from the temporary file to preserve navigation history
    def load_from_file(self, tmp_file_path):

        self.web_view.LoadURL(f"file://{tmp_file_path}")        
    def set_initial_content(self):
        initial_html = """
        <html>
        <head>
        <style>
            /* Apply styling to the table with a class */
            #log-table {
                font-family: Arial, sans-serif;   /* Basic, clean font */
                font-size: 16px;                  /* Regular font size */
                line-height: 1.5;                 /* Readable line spacing */
                color: #2d2d2d;                   /* Dark gray color */
                width: 100%;                      /* Full width */
                border-collapse: collapse;        /* Remove spacing between cells */
            }

            /* Styling for the header cell */
            #header-cell {
                font-weight: bold;
                font-size: 20px;
                padding: 10px;                    /* Add some padding */
                background-color: #f6f6f6;        /* Light background for header */
                border-bottom: 1px solid #ddd;    /* Border below header */
            }

            /* Styling for other table rows and cells */
            #log-cell {
                padding: 10px;
            }

            hr {
                border: 0;
                border-top: 1px solid #ddd;
                margin: 0;
            }
        #log-container {
            max-height: 500px;  
            overflow-y: auto;   
        }            
        </style>
        </head>
        <body>
        <table  id="log-container">
            <tr><td><hr></td></tr>
            <tr id="log-row">
                <td >  
                    <div id="log-cell"></div>
                </td>
            </tr>
        </table>
            <script>
                // Function to replace header content
                function replaceHeader(content) {
                    const headerCell = document.getElementById('header-cell');
                    headerCell.innerHTML = content;
                }
                
                // Function to replace log content
                function replaceLogContent(content) {
                    const logCell = document.getElementById('log-cell');
                    logCell.innerHTML = content;
                }
                // Listen for mouseup events to detect selection
                document.addEventListener('mouseup', function() {
                    var selectedText = window.getSelection().toString();
                    if (selectedText) {
                        // Send the selected text to Python via custom scheme
                        window.location.href = 'app://selection?text=' + encodeURIComponent(selectedText);
                    }
                });      
                // Detect right-click and check if text is selected
                document.addEventListener('contextmenu', function(event) {
                    var selectedText = window.getSelection().toString();
                    if (selectedText) {
                        // Send the selected text to Python via custom scheme
                        event.preventDefault();  // Prevent the default context menu
                        window.location.href = 'app://selection?text=' + encodeURIComponent(selectedText);
                    } else {
                        // Send a different URL to Python to indicate no selection
                        event.preventDefault();
                        window.location.href = 'app://show_back_menu';
                    }
                });                          
            </script>
        </body>
        </html>
        """


        self.web_view.SetPage(initial_html, "")
        tmp_file=self.save_html(initial_html)
        self.page_history.append(tmp_file)
        print(333333, self.page_history)
        #self.web_view.LoadURL(f"file://{tmp_file}")

 
    def add_log_entry(self, content):
        # Call the JavaScript function to add a log entry
        self.web_view.RunScript(f"addLogEntry(`{content}`);")

    def _set_initial_content(self):
        html=self.get_log_html()
        initial_html = """
        <html>
        <body>
        %s
        </body>
        </html>
        """   % html      
        self.web_view.SetPage(initial_html, "")



    def _on_navigating(self, event):
        url = event.GetURL()
        #print(f"Log Navigating to: {url[:50]}")
        if url.startswith("app:"):
            event.Veto()  # Prevent actual navigation for our custom scheme

    def on_webview_error(self, event):
        print(f"WebView error: {event.GetString()}")


import wx
from pubsub import pub


class CenterPanel(wx.Panel):
    def __init__(self, parent):
        super().__init__(parent)
         # Create Notebook
        center_notebook = wx.Notebook(self)
        
        self.processor_panel = ProcessorPanel(center_notebook)
        
        center_notebook.AddPage(self.processor_panel, "Processor")


        
        center_notebook.SetSelection(0)

        
        
        sizer = wx.BoxSizer(wx.VERTICAL)
        sizer.Add(center_notebook, 1, wx.EXPAND)
        
        self.SetSizer(sizer)
        #self.Bind(wx.EVT_SIZE, self.on_panel_resize)
        self.Layout()

    def on_panel_resize(self, event):
        #print('on_panel_resize')
        # Force the HtmlListBox to recalculate sizes on panel resize
        #self.html_list_box.Refresh()
        pub.sendMessage("panel_resize", event=None)
        event.Skip()        

