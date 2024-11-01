
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
    def __init__(self, prefix):
        self.set_log()
        self.prefix=prefix
        self.header='App Log'
        self.history=[]
        self.page_history=[]
        self.page_forward=[]
        #pub.subscribe(self.on_log, "applog")
        pub.subscribe(self.done_display, f"{self.prefix}:"+"done_display")
        pub.subscribe(self.display_response,f"{self.prefix}:"+ "display_response")
        pub.subscribe(self.set_header, f"{self.prefix}:"+"set_header")
        pub.subscribe(self.on_page_back, f"{self.prefix}:"+"back")
        pub.subscribe(self.on_page_forward, f"{self.prefix}:"+"forward")  
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
        self.web_view.RunScript(f"replaceLogContent(`{sanitized_content}`);")
    def replace_header(self, content):
        # Use JavaScript to replace content in the header row
        sanitized_content = content.replace("`", "\\`")+f' [{apc.processor_model_name[self.parent_name]}]'  # Escape backticks for JavaScript
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

