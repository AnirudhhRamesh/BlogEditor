import argparse
import cmd
from blog_editor import BlogEditor
import curses
import time
from errors import GuestNotFoundError
import itertools
import sys
import os
import logging
from schemas.file import Metadata, Blog

def main(stdscr):
    """
    CLI for the blog editor to easily generate blogs
    """
    # Clear screen and hide cursor
    curses.curs_set(0)
    stdscr.clear()
    
    # Get terminal dimensions
    height, width = stdscr.getmaxyx()
    current_file = None
    current_file_name = "No file set!"
    
    # Initialize input variables
    input_buffer = ""
    input_y = height - 2  # Position at bottom of screen
    
    # Add preview scroll position
    preview_scroll = 0
    visible_preview_lines = height - 4
    
    welcome_text = "Welcome to Blog Generator CLI!"
    commands = ["list", "get", "set_model", "generate_all", "quit"]

    content_text = "Here are the available commands: \n - " + "\n - ".join(commands) + "\n \nTo start, use 'get <file>'\n"
    preview_lines = ["Preview screen"]

    # Initialize blog editor
    blog_editor = BlogEditor()

    def refresh_screen():
        nonlocal stdscr, height, width, welcome_text, current_file_name, content_text, preview_lines, visible_preview_lines, input_buffer, preview_scroll, input_y
        stdscr.clear()
        try:
            # Redraw header
            stdscr.addstr(0, 0, welcome_text[:width-1])
            header_text = "Currently editing file: "
            stdscr.addstr(1, 0, header_text)
            stdscr.addstr(1, len(header_text), current_file_name[:width-len(header_text)-1], curses.A_REVERSE)
            
            # Redraw content with up-to-date info
            if current_file_name != "No file set!":
                current_file = blog_editor.get(current_file_name)
                content_text = f"{current_file.__str__()}"

            content_y_pos = 3
            for paragraph in content_text.split('\n'):
                # Skip empty paragraphs but still add the spacing
                if not paragraph.strip():
                    content_y_pos += 1
                    continue

                was_wrapped = False
                line = paragraph
                while line and content_y_pos < height - 2:
                    if len(line) > width - 1:
                        wrap_point = line[:width-1].rfind(' ')
                        if wrap_point == -1:  # No space found, force wrap at width
                            wrap_point = width - 1
                        
                        stdscr.addstr(content_y_pos, 0, line[:wrap_point])
                        line = line[wrap_point:].lstrip()
                        was_wrapped = True
                    else:
                        stdscr.addstr(content_y_pos, 0, line)
                        line = ''
                    content_y_pos += 1
                
                # Add extra line break after wrapped paragraphs
                if was_wrapped and content_y_pos < height - 2:
                    content_y_pos += 1
            
            # Divider
            if content_y_pos < height - 2:
                stdscr.addstr(content_y_pos, 0, "-" * (width - 1))
                content_y_pos += 1

            # Redraw preview with text wrapping and paragraph spacing
            preview_y_pos = content_y_pos + 1
            preview_text = preview_lines[0].split('\n')
            
            wrapped_preview_lines = []
            for paragraph in preview_text:
                if not paragraph.strip():
                    wrapped_preview_lines.append('')
                    continue

                line = paragraph
                paragraph_lines = []
                while line:
                    if len(line) > width - 1:
                        wrap_point = line[:width-1].rfind(' ')
                        if wrap_point == -1:
                            wrap_point = width - 1
                        paragraph_lines.append(line[:wrap_point])
                        line = line[wrap_point:].lstrip()
                    else:
                        paragraph_lines.append(line)
                        line = ''
                
                # Add the paragraph lines
                wrapped_preview_lines.extend(paragraph_lines)
                # Add extra line break if the paragraph was wrapped
                if len(paragraph_lines) > 1:
                    wrapped_preview_lines.append('')

            for i in range(visible_preview_lines):
                line_idx = i + preview_scroll
                if line_idx < len(wrapped_preview_lines):
                    if preview_y_pos + i < height - 2:
                        stdscr.addstr(preview_y_pos + i, 0, wrapped_preview_lines[line_idx])
            
            # Redraw input line
            stdscr.addstr(input_y, 0, "> " + input_buffer[:width-3])  # Leave room for "> "
        except curses.error:
            pass
        stdscr.refresh()

    def llm_stream(text):
        nonlocal preview_lines
        preview_lines[0] += text
        refresh_screen()

    def cli_callback(text):
        nonlocal preview_lines
        preview_lines[0] = f"Generating...\nCurrent status: {text}\n\n"
        refresh_screen()# Generate content

    while True:
        refresh_screen()
        
        # Get user input
        key = stdscr.getch()
        # if key == ord('q'):
        #     break
        if key == curses.KEY_UP:
            if preview_scroll > 0:
                preview_scroll -= 1
        elif key == curses.KEY_DOWN:
            if preview_scroll < len(preview_lines[0].split('\n')) - visible_preview_lines:
                preview_scroll += 1
        elif key == curses.KEY_BACKSPACE or key == 127:
            input_buffer = input_buffer[:-1]
        elif key == ord('\n'):
            # Parse and handle commands
            cmd_parts = input_buffer.strip().split()
            if not cmd_parts:
                pass  # Empty line
            else:
                cmd = cmd_parts[0]
                param = cmd_parts[1] if len(cmd_parts) > 1 else None
                extra = cmd_parts[2:] if len(cmd_parts) > 2 else None

                # List files
                if cmd == 'list':
                    files = blog_editor.list_files()
                    content_text = "Files: \n - " + "\n - ".join(files)

                # Choose the working file
                elif cmd == 'get':
                    if param:
                        try:
                            file_name = " ".join(cmd_parts[1:])
                            current_file_name = file_name
                            current_file = blog_editor.get(file_name)
                            content_text = f"{current_file.__str__()}"

                            preview_lines[0] = f"File {file_name} loaded!"
                        except GuestNotFoundError:
                            content_text = f"File '{file_name}' not found! \n \n Here are the list of available files: \n - " + "\n - ".join(blog_editor.list_files())
                
                # Help
                elif cmd == 'help':
                    content_text = "Here are the available commands: \n - " + "\n - ".join(commands)

                # Quit
                elif cmd in ('quit', 'exit'):
                    break

                elif cmd == 'publish':
                    preview_lines[0] = f"Publishing {current_file_name} to notion"
                    blog_editor.publish_notion_draft(current_file_name)
                
                elif cmd in ['generate', 'edit', 'reset'] and current_file is None:
                    content_text = "Set a file first using 'get <file>!'"

                elif cmd in ['generate', 'view', 'edit', 'overwrite', 'reset'] and current_file is not None:
                    # Assert param is not None
                    if param is None:
                        preview_lines[0] = f"Parameter is required for this command! Use '{cmd} <param>'"

                    # Generating content for the first time
                    if cmd == 'generate':
                        preview_scroll = 0

                        if param == 'all':
                            # Generate all content
                            blog_editor.generate_all(current_file_name, llm_stream=llm_stream, callback=cli_callback)
                        
                        elif param in ['thumbnail', 'thumbnails']:                            
                            # Maybe need a task scheduler here?
                            blog_editor.generate_thumbnails(current_file_name)

                        else:
                            if param not in Blog.__annotations__.keys():
                                preview_lines[0] = f"Parameter '{param}' is not present in {current_file_name}"
                            else:
                                blog_editor.generate(current_file_name, param, llm_stream=llm_stream, callback=cli_callback)

                    # Editing content
                    elif cmd == 'edit':
                        if param not in Blog.__annotations__.keys():
                            preview_lines[0] = f"Parameter '{param}' is not present in {current_file_name}"
                        else:
                            blog_editor.edit(current_file_name, param, extra, llm_stream=llm_stream, callback=cli_callback)

                    elif cmd == 'view':
                        # Get the latest version of the file
                        current_file = blog_editor.get(current_file_name)
                        
                        # Metadata params
                        if param in Metadata.__annotations__.keys():
                            preview_scroll = 0
                            param_value = getattr(current_file.metadata, param, f"Attribute '{param}' not found")
                            if param_value:
                                preview_lines[0] = param_value.__str__()
                            else:
                                preview_lines[0] = f"'{param}' is not present in {current_file_name}"

                        elif param in Blog.__annotations__.keys():
                            preview_scroll = 0
                            param_value = getattr(current_file.blog, param, f"Attribute '{param}' not found")
                            if param_value:
                                preview_lines[0] = param_value
                            else:
                                preview_lines[0] = f"'{param}' is not present in {current_file_name}"

                    elif cmd == 'overwrite':
                        # E.g. overwrite title <extra> will set title = <extra>
                        preview_lines[0] = f"Not yet implemented: \ncmd: {cmd}, param: {param}, extra: {extra}"

                    elif cmd == 'reset':
                        preview_lines[0] = f"Not yet implemented: \ncmd: {cmd}, param: {param}, extra: {extra}"
                        
                        if param == 'all':
                            # blog_editor.reset_all(current_file)
                            pass
                        else:
                            # blog_editor.reset("param")
                            pass

            input_buffer = ""
        elif 32 <= key <= 126:
            try:
                input_buffer += chr(key)
            except Exception as e:
                logging.error(f"Character input error: {str(e)}")


if __name__ == '__main__':
    # Redirect stdout and stderr before starting curses
    logging.getLogger().setLevel(logging.ERROR)  # Or use logging.CRITICAL for even less output

    # sys.stdout = open(os.devnull, 'w')
    # sys.stderr = open(os.devnull, 'w')
    error = "no error hmm?"
    try:
        curses.wrapper(main)
    except Exception as e:
        logging.error(f"Curses wrapper error: {str(e)}")
        error = str(e)

    print(f"Exiting... due to error: {error}")
    