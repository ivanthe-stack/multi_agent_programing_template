import tkinter as tk
from tkinter import ttk, messagebox, simpledialog, filedialog
import threading
import time
import os
from task_database import TaskDatabase
from datetime import datetime

class TaskDatabaseUI:
    def __init__(self, root, db_path=None):
        self.root = root
        self.root.title("Multi-Agent Task Database")
        self.root.geometry("1200x600")
        
        self.db_path = db_path or "tasks.db"
        self.db = TaskDatabase(self.db_path)
        self.auto_refresh = True
        self.recent_files = self.load_recent_files()
        
        self.setup_ui()
        self.refresh_data()
        self.start_auto_refresh()
    
    def setup_ui(self):
        # Main frame
        main_frame = ttk.Frame(self.root, padding="10")
        main_frame.grid(row=0, column=0, sticky=(tk.W, tk.E, tk.N, tk.S))
        
        # Configure grid weights
        self.root.columnconfigure(0, weight=1)
        self.root.rowconfigure(0, weight=1)
        main_frame.columnconfigure(1, weight=1)
        main_frame.rowconfigure(2, weight=1)
        
        # Title and menu
        title_frame = ttk.Frame(main_frame)
        title_frame.grid(row=0, column=0, columnspan=3, sticky=(tk.W, tk.E), pady=(0, 20))
        title_frame.columnconfigure(1, weight=1)
        
        title_label = ttk.Label(title_frame, text="Multi-Agent Task Database", 
                               font=('Arial', 16, 'bold'))
        title_label.grid(row=0, column=0, sticky=tk.W)
        
        # Database file info and controls
        db_frame = ttk.Frame(title_frame)
        db_frame.grid(row=0, column=2, sticky=tk.E)
        
        self.db_info_label = ttk.Label(db_frame, text=f"DB: {self.db_path}", 
                                      font=('Arial', 9), foreground='gray')
        self.db_info_label.pack(side=tk.TOP, anchor=tk.E)
        
        db_buttons = ttk.Frame(db_frame)
        db_buttons.pack(side=tk.TOP, anchor=tk.E)
        
        ttk.Button(db_buttons, text="Open Database", 
                  command=self.open_database).pack(side=tk.LEFT, padx=(0, 5))
        ttk.Button(db_buttons, text="New Database", 
                  command=self.new_database).pack(side=tk.LEFT, padx=(0, 5))
        
        # Recent files dropdown
        if self.recent_files:
            self.recent_var = tk.StringVar()
            recent_menu = ttk.Combobox(db_buttons, textvariable=self.recent_var, 
                                     values=[os.path.basename(f) for f in self.recent_files],
                                     state="readonly", width=15)
            recent_menu.set("Recent Files")
            recent_menu.pack(side=tk.LEFT)
            recent_menu.bind('<<ComboboxSelected>>', self.open_recent_file)
        
        # Current goal section
        goal_frame = ttk.LabelFrame(main_frame, text="Current Goal", padding="10")
        goal_frame.grid(row=1, column=0, columnspan=3, sticky=(tk.W, tk.E), pady=(0, 10))
        goal_frame.columnconfigure(1, weight=1)
        
        self.goal_label = ttk.Label(goal_frame, text="Loading...", 
                                   font=('Arial', 10), wraplength=800)
        self.goal_label.grid(row=0, column=0, sticky=(tk.W, tk.E))
        
        # Control buttons
        button_frame = ttk.Frame(main_frame)
        button_frame.grid(row=2, column=0, sticky=(tk.W, tk.N), padx=(0, 10))
        
        ttk.Button(button_frame, text="Add Task", 
                  command=self.add_task_dialog).pack(pady=2, fill=tk.X)
        ttk.Button(button_frame, text="Update Status", 
                  command=self.update_status_dialog).pack(pady=2, fill=tk.X)
        ttk.Button(button_frame, text="Delete Task", 
                  command=self.delete_task_dialog).pack(pady=2, fill=tk.X)
        ttk.Button(button_frame, text="Refresh", 
                  command=self.refresh_data).pack(pady=2, fill=tk.X)
        
        # Auto-refresh toggle
        self.auto_refresh_var = tk.BooleanVar(value=True)
        ttk.Checkbutton(button_frame, text="Auto Refresh", 
                       variable=self.auto_refresh_var,
                       command=self.toggle_auto_refresh).pack(pady=5, fill=tk.X)
        
        # Filters
        ttk.Label(button_frame, text="Filter by Status:").pack(pady=(10, 2))
        self.status_filter = ttk.Combobox(button_frame, values=["All", "Not Started", "In Progress", "Done"])
        self.status_filter.set("All")
        self.status_filter.pack(pady=2, fill=tk.X)
        self.status_filter.bind('<<ComboboxSelected>>', lambda e: self.refresh_data())
        
        ttk.Label(button_frame, text="Filter by Agent:").pack(pady=(10, 2))
        self.agent_filter = ttk.Combobox(button_frame, values=["All"])
        self.agent_filter.set("All")
        self.agent_filter.pack(pady=2, fill=tk.X)
        self.agent_filter.bind('<<ComboboxSelected>>', lambda e: self.refresh_data())
        
        # Sorting
        ttk.Label(button_frame, text="Sort by:").pack(pady=(10, 2))
        self.sort_by = ttk.Combobox(button_frame, values=["ID", "Agent", "Date", "Status", "Description"], state="readonly")
        self.sort_by.set("ID")
        self.sort_by.pack(pady=2, fill=tk.X)
        self.sort_by.bind('<<ComboboxSelected>>', lambda e: self.refresh_data())
        
        self.sort_order = ttk.Combobox(button_frame, values=["Ascending", "Descending"], state="readonly")
        self.sort_order.set("Descending")
        self.sort_order.pack(pady=2, fill=tk.X)
        self.sort_order.bind('<<ComboboxSelected>>', lambda e: self.refresh_data())
        
        # Tasks table
        table_frame = ttk.Frame(main_frame)
        table_frame.grid(row=2, column=1, columnspan=2, sticky=(tk.W, tk.E, tk.N, tk.S))
        table_frame.columnconfigure(0, weight=1)
        table_frame.rowconfigure(0, weight=1)
        
        # Treeview with scrollbars (Notion-style)
        style = ttk.Style()
        style.configure("Treeview", rowheight=25, font=('Arial', 9))
        style.configure("Treeview.Heading", font=('Arial', 10, 'bold'))
        # Remove selection highlighting for true Notion-style
        style.map("Treeview", 
                 background=[('selected', 'white')],
                 foreground=[('selected', 'black')])
        
        self.tree = ttk.Treeview(table_frame, columns=('ID', 'Agent', 'Date', 'Status', 'Description'), 
                                show='headings', height=20)
        
        # Define columns with better styling and click sorting
        self.tree.heading('ID', text='ID ↓', anchor='center', command=lambda: self.sort_by_column('ID'))
        self.tree.heading('Agent', text='Agent', anchor='w', command=lambda: self.sort_by_column('Agent'))
        self.tree.heading('Date', text='Date', anchor='center', command=lambda: self.sort_by_column('Date'))
        self.tree.heading('Status', text='Status', anchor='center', command=lambda: self.sort_by_column('Status'))
        self.tree.heading('Description', text='Description', anchor='w', command=lambda: self.sort_by_column('Description'))
        
        # Configure column widths and alignment
        self.tree.column('ID', width=50, minwidth=40, anchor='center')
        self.tree.column('Agent', width=120, minwidth=80, anchor='w')
        self.tree.column('Date', width=100, minwidth=80, anchor='center')
        self.tree.column('Status', width=120, minwidth=100, anchor='center')
        self.tree.column('Description', width=450, minwidth=200, anchor='w')
        
        # Scrollbars
        v_scrollbar = ttk.Scrollbar(table_frame, orient=tk.VERTICAL, command=self.tree.yview)
        h_scrollbar = ttk.Scrollbar(table_frame, orient=tk.HORIZONTAL, command=self.tree.xview)
        self.tree.configure(yscrollcommand=v_scrollbar.set, xscrollcommand=h_scrollbar.set)
        
        # Grid layout for table and scrollbars
        self.tree.grid(row=0, column=0, sticky=(tk.W, tk.E, tk.N, tk.S))
        v_scrollbar.grid(row=0, column=1, sticky=(tk.N, tk.S))
        h_scrollbar.grid(row=1, column=0, sticky=(tk.W, tk.E))
        
        # Status bar
        self.status_bar = ttk.Label(main_frame, text="Ready", relief=tk.SUNKEN)
        self.status_bar.grid(row=3, column=0, columnspan=3, sticky=(tk.W, tk.E), pady=(10, 0))
        
        # Bind single click to cell editing (Notion-style)
        self.tree.bind('<Button-1>', self.on_item_click)
        # Prevent default row selection behavior
        self.tree.bind('<ButtonRelease-1>', self.on_button_release)
        # Add hover effects
        self.tree.bind('<Motion>', self.on_mouse_motion)
        self.tree.bind('<Leave>', self.on_mouse_leave)
        
        # Variables for inline editing
        self.current_editor = None
        self.editing_item = None
        self.editing_column = None
        self.click_handled = False
        self.hover_item = None
    
    def refresh_data(self):
        # Clear existing data
        for item in self.tree.get_children():
            self.tree.delete(item)
        
        # Get current goal
        goal = self.db.get_current_goal()
        self.goal_label.config(text=goal or "No goal set")
        
        # Get all tasks first
        all_tasks = self.db.get_all_tasks()
        
        # Update agent filter options
        agents = sorted(set(task['agent'] for task in all_tasks))
        current_agent_filter = self.agent_filter.get()
        self.agent_filter['values'] = ["All"] + agents
        if current_agent_filter not in self.agent_filter['values']:
            self.agent_filter.set("All")
        
        # Apply filters
        tasks = all_tasks
        
        # Filter by status
        filter_status = self.status_filter.get()
        if filter_status != "All":
            tasks = [task for task in tasks if task['status'] == filter_status]
        
        # Filter by agent
        filter_agent = self.agent_filter.get()
        if filter_agent != "All":
            tasks = [task for task in tasks if task['agent'] == filter_agent]
        
        # Apply sorting
        sort_by = self.sort_by.get()
        sort_order = self.sort_order.get()
        reverse = (sort_order == "Descending")
        
        if sort_by == "ID":
            tasks.sort(key=lambda x: x['id'], reverse=reverse)
        elif sort_by == "Agent":
            tasks.sort(key=lambda x: x['agent'].lower(), reverse=reverse)
        elif sort_by == "Date":
            tasks.sort(key=lambda x: x['timestamp'], reverse=reverse)
        elif sort_by == "Status":
            # Custom status order: Not Started, In Progress, Done
            status_order = {"Not Started": 0, "In Progress": 1, "Done": 2}
            tasks.sort(key=lambda x: status_order.get(x['status'], 3), reverse=reverse)
        elif sort_by == "Description":
            tasks.sort(key=lambda x: x['description'].lower(), reverse=reverse)
        
        # Populate table
        for task in tasks:
            # Color coding based on status
            tags = []
            if task['status'] == 'Done':
                tags = ['done']
            elif task['status'] == 'In Progress':
                tags = ['in_progress']
            elif task['status'] == 'Not Started':
                tags = ['not_started']
            
            self.tree.insert('', tk.END, values=(
                task['id'], 
                task['agent'], 
                task['timestamp'], 
                task['status'], 
                task['description'][:100] + "..." if len(task['description']) > 100 else task['description']
            ), tags=tags)
        
        # Configure tag colors (Notion-style)
        self.tree.tag_configure('done', background='#e8f5e8', foreground='#2d5a2d')
        self.tree.tag_configure('in_progress', background='#fff8e1', foreground='#8b6914')
        self.tree.tag_configure('not_started', background='#ffebee', foreground='#8b3a3a')
        
        # Update column headers with sort indicators
        self.update_column_headers()
        
        # Update status bar
        self.status_bar.config(text=f"Last updated: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')} | Total tasks: {len(tasks)}")
    
    def start_auto_refresh(self):
        def auto_refresh_worker():
            while True:
                if self.auto_refresh and self.auto_refresh_var.get():
                    try:
                        self.root.after(0, self.refresh_data)
                    except tk.TclError:
                        break  # Window was closed
                time.sleep(2)  # Refresh every 2 seconds
        
        refresh_thread = threading.Thread(target=auto_refresh_worker, daemon=True)
        refresh_thread.start()
    
    def toggle_auto_refresh(self):
        self.auto_refresh = self.auto_refresh_var.get()
    
    def sort_by_column(self, column):
        """Sort by column header click"""
        current_sort = self.sort_by.get()
        current_order = self.sort_order.get()
        
        if current_sort == column:
            # Toggle order if same column
            new_order = "Ascending" if current_order == "Descending" else "Descending"
            self.sort_order.set(new_order)
        else:
            # New column, default to ascending
            self.sort_by.set(column)
            self.sort_order.set("Ascending")
        
        self.refresh_data()
    
    def update_column_headers(self):
        """Update column headers with sort indicators"""
        sort_by = self.sort_by.get()
        sort_order = self.sort_order.get()
        arrow = " ↓" if sort_order == "Descending" else " ↑"
        
        # Reset all headers
        self.tree.heading('ID', text='ID')
        self.tree.heading('Agent', text='Agent')
        self.tree.heading('Date', text='Date')
        self.tree.heading('Status', text='Status')
        self.tree.heading('Description', text='Description')
        
        # Add arrow to current sort column
        current_text = self.tree.heading(sort_by.lower() if sort_by != 'ID' else 'ID')['text']
        if sort_by == 'ID':
            self.tree.heading('ID', text=f'ID{arrow}')
        elif sort_by == 'Agent':
            self.tree.heading('Agent', text=f'Agent{arrow}')
        elif sort_by == 'Date':
            self.tree.heading('Date', text=f'Date{arrow}')
        elif sort_by == 'Status':
            self.tree.heading('Status', text=f'Status{arrow}')
        elif sort_by == 'Description':
            self.tree.heading('Description', text=f'Description{arrow}')
    
    def add_task_dialog(self):
        dialog = AddTaskDialog(self.root, self.db)
        if dialog.result:
            self.refresh_data()
    
    def update_status_dialog(self):
        selection = self.tree.selection()
        if not selection:
            messagebox.showwarning("No Selection", "Please select a task to update.")
            return
        
        item = self.tree.item(selection[0])
        task_id = item['values'][0]
        current_status = item['values'][3]
        
        new_status = simpledialog.askstring(
            "Update Status", 
            f"Current status: {current_status}\nEnter new status:",
            initialvalue=current_status
        )
        
        if new_status:
            success = self.db.update_task_status(task_id, new_status)
            if success:
                self.refresh_data()
                messagebox.showinfo("Success", f"Task {task_id} updated to '{new_status}'")
            else:
                messagebox.showerror("Error", f"Failed to update task {task_id}")
    
    def delete_task_dialog(self):
        selection = self.tree.selection()
        if not selection:
            messagebox.showwarning("No Selection", "Please select a task to delete.")
            return
        
        item = self.tree.item(selection[0])
        task_id = item['values'][0]
        task_desc = item['values'][4]
        
        if messagebox.askyesno("Confirm Delete", f"Delete task {task_id}: {task_desc}?"):
            success = self.db.delete_task(task_id)
            if success:
                self.refresh_data()
                messagebox.showinfo("Success", f"Task {task_id} deleted")
            else:
                messagebox.showerror("Error", f"Failed to delete task {task_id}")
    
    def on_item_click(self, event):
        """Handle single click on tree items for Notion-style inline editing"""
        # Destroy any existing editor first
        self.destroy_current_editor()
        
        region = self.tree.identify("region", event.x, event.y)
        if region == "cell":
            column = self.tree.identify_column(event.x, event.y)
            item = self.tree.identify_row(event.y)
            
            if item and column:
                # Prevent row selection by clearing selection immediately
                self.tree.selection_remove(self.tree.selection())
                
                self.editing_item = item
                self.editing_column = column
                self.click_handled = True
                
                # Get column name
                col_name = self.tree.heading(column)['text']
                
                # Schedule editing to happen after click processing
                self.root.after(1, lambda: self.start_cell_editing(item, column, col_name))
                
                # Prevent default selection behavior
                return "break"
    
    def on_button_release(self, event):
        """Handle button release to prevent row selection"""
        if self.click_handled:
            self.click_handled = False
            # Clear any selection that might have occurred
            self.tree.selection_remove(self.tree.selection())
            return "break"
    
    def start_cell_editing(self, item, column, col_name):
        """Start editing a cell"""
        if col_name == 'Status':
            self.edit_status_notion_style(item, column)
        elif col_name in ['Description', 'Agent']:
            self.edit_text_notion_style(item, column)
    
    def destroy_current_editor(self):
        """Destroy the current inline editor if it exists"""
        if self.current_editor:
            try:
                self.current_editor.destroy()
            except:
                pass
            self.current_editor = None
            self.editing_item = None
            self.editing_column = None
    
    def edit_status_notion_style(self, item, column):
        """Create Notion-style inline dropdown for status editing"""
        try:
            bbox = self.tree.bbox(item, column)
            if not bbox:
                return
            x, y, width, height = bbox
        except:
            return
        
        # Get current values
        values = self.tree.item(item)['values']
        task_id = values[0]
        current_status = values[3]
        
        # Create styled combobox
        self.current_editor = ttk.Combobox(
            self.tree, 
            values=["Not Started", "In Progress", "Done"],
            state="readonly",
            font=('Arial', 9)
        )
        self.current_editor.set(current_status)
        self.current_editor.place(x=x+1, y=y+1, width=width-2, height=height-2)
        
        def on_status_change(event=None):
            new_status = self.current_editor.get()
            if new_status != current_status:
                success = self.db.update_task_status(task_id, new_status)
                if success:
                    self.status_bar.config(text=f"✓ Updated task {task_id} status to '{new_status}'")
                    # Update the tree item immediately for smooth UX
                    current_values = list(self.tree.item(item)['values'])
                    current_values[3] = new_status
                    self.tree.item(item, values=current_values)
                    # Apply color coding
                    if new_status == 'Done':
                        self.tree.item(item, tags=['done'])
                    elif new_status == 'In Progress':
                        self.tree.item(item, tags=['in_progress'])
                    else:
                        self.tree.item(item, tags=['not_started'])
                else:
                    messagebox.showerror("Error", f"Failed to update task {task_id}")
            self.destroy_current_editor()
        
        def on_escape(event):
            self.destroy_current_editor()
        
        # Bind events
        self.current_editor.bind('<<ComboboxSelected>>', on_status_change)
        self.current_editor.bind('<Escape>', on_escape)
        self.current_editor.bind('<FocusOut>', lambda e: self.destroy_current_editor())
        
        # Show dropdown immediately
        self.current_editor.focus()
        self.current_editor.event_generate('<Button-1>')
    
    def edit_text_notion_style(self, item, column):
        """Create Notion-style inline text editor"""
        try:
            bbox = self.tree.bbox(item, column)
            if not bbox:
                return
            x, y, width, height = bbox
        except:
            return
        
        # Get current values
        values = self.tree.item(item)['values']
        task_id = values[0]
        col_name = self.tree.heading(column)['text']
        
        if col_name == 'Description':
            # Get full description from database
            tasks = self.db.get_all_tasks()
            current_text = ""
            for task in tasks:
                if task['id'] == task_id:
                    current_text = task['description']
                    break
        elif col_name == 'Agent':
            current_text = values[1]
        else:
            return
        
        # Create text entry
        self.current_editor = tk.Text(
            self.tree,
            font=('Arial', 9),
            wrap=tk.WORD,
            relief=tk.FLAT,
            borderwidth=1,
            highlightthickness=1,
            highlightcolor='#0078d4'
        )
        
        # Position and size the editor
        self.current_editor.place(x=x+1, y=y+1, width=width-2, height=height-2)
        
        # Insert current text
        self.current_editor.insert("1.0", current_text)
        self.current_editor.focus()
        self.current_editor.select_range("1.0", tk.END)
        
        def save_text():
            new_text = self.current_editor.get("1.0", tk.END).strip()
            if new_text and new_text != current_text:
                if col_name == 'Description':
                    success = self.db.update_task_description(task_id, new_text)
                    if success:
                        self.status_bar.config(text=f"✓ Updated task {task_id} description")
                        # Update display text (truncated)
                        display_text = new_text[:100] + "..." if len(new_text) > 100 else new_text
                        current_values = list(self.tree.item(item)['values'])
                        current_values[4] = display_text
                        self.tree.item(item, values=current_values)
                    else:
                        messagebox.showerror("Error", f"Failed to update task {task_id}")
                elif col_name == 'Agent':
                    success = self.db.update_task_agent(task_id, new_text)
                    if success:
                        self.status_bar.config(text=f"✓ Updated task {task_id} agent")
                        current_values = list(self.tree.item(item)['values'])
                        current_values[1] = new_text
                        self.tree.item(item, values=current_values)
                    else:
                        messagebox.showerror("Error", f"Failed to update task {task_id}")
            
            self.destroy_current_editor()
        
        def on_key(event):
            if event.keysym == 'Escape':
                self.destroy_current_editor()
            elif event.keysym == 'Return' and event.state & 0x4:  # Ctrl+Enter
                save_text()
        
        # Bind events
        self.current_editor.bind('<FocusOut>', lambda e: save_text())
        self.current_editor.bind('<KeyPress>', on_key)
        
        # Auto-resize height for multi-line text
        def on_text_change(event=None):
            lines = self.current_editor.get("1.0", tk.END).count('\n')
            new_height = max(height, min(lines * 20 + 10, 150))
            self.current_editor.place(height=new_height)
        
        self.current_editor.bind('<KeyRelease>', on_text_change)
    
    def on_mouse_motion(self, event):
        """Handle mouse motion for hover effects"""
        item = self.tree.identify_row(event.y)
        if item != self.hover_item:
            # Remove old hover
            if self.hover_item:
                self.tree.set(self.hover_item, '', '')
            
            # Add new hover
            self.hover_item = item
            if item and not self.current_editor:
                # Subtle hover effect by changing cursor
                self.tree.configure(cursor="hand2")
    
    def on_mouse_leave(self, event):
        """Handle mouse leaving the tree"""
        if self.hover_item:
            self.hover_item = None
        self.tree.configure(cursor="")
    
    def open_database(self):
        """Open an existing database file"""
        file_path = filedialog.askopenfilename(
            title="Open Task Database",
            filetypes=[
                ("Database files", "*.db"),
                ("SQLite files", "*.sqlite"),
                ("All files", "*.*")
            ],
            defaultextension=".db"
        )
        
        if file_path:
            try:
                # Test if the file is a valid database
                test_db = TaskDatabase(file_path)
                test_tasks = test_db.get_all_tasks()  # Try to read tasks
                
                # If successful, switch to new database
                self.db_path = file_path
                self.db = test_db
                self.db_info_label.config(text=f"DB: {os.path.basename(self.db_path)}")
                self.root.title(f"Multi-Agent Task Database - {os.path.basename(self.db_path)}")
                
                # Add to recent files
                self.add_to_recent_files(file_path)
                
                # Refresh the display
                self.refresh_data()
                self.status_bar.config(text=f"✓ Opened database: {os.path.basename(self.db_path)}")
                
            except Exception as e:
                messagebox.showerror("Error", f"Failed to open database:\n{str(e)}")
    
    def new_database(self):
        """Create a new database file"""
        file_path = filedialog.asksaveasfilename(
            title="Create New Task Database",
            filetypes=[
                ("Database files", "*.db"),
                ("SQLite files", "*.sqlite"),
                ("All files", "*.*")
            ],
            defaultextension=".db"
        )
        
        if file_path:
            try:
                # Create new database
                if os.path.exists(file_path):
                    if not messagebox.askyesno("File Exists", 
                                             f"File {os.path.basename(file_path)} already exists. Overwrite?"):
                        return
                    os.remove(file_path)
                
                # Create new database
                self.db_path = file_path
                self.db = TaskDatabase(file_path)
                self.db_info_label.config(text=f"DB: {os.path.basename(self.db_path)}")
                self.root.title(f"Multi-Agent Task Database - {os.path.basename(self.db_path)}")
                
                # Add to recent files
                self.add_to_recent_files(file_path)
                
                # Refresh the display
                self.refresh_data()
                self.status_bar.config(text=f"✓ Created new database: {os.path.basename(self.db_path)}")
                
            except Exception as e:
                messagebox.showerror("Error", f"Failed to create database:\n{str(e)}")
    
    def load_recent_files(self):
        """Load recent files from settings"""
        try:
            recent_file = ".task_ui_recent.txt"
            if os.path.exists(recent_file):
                with open(recent_file, 'r') as f:
                    files = [line.strip() for line in f.readlines() if line.strip()]
                    # Filter existing files only
                    return [f for f in files if os.path.exists(f)][:5]  # Max 5 recent files
        except:
            pass
        return []
    
    def save_recent_files(self):
        """Save recent files to settings"""
        try:
            recent_file = ".task_ui_recent.txt"
            with open(recent_file, 'w') as f:
                for file_path in self.recent_files:
                    f.write(f"{file_path}\n")
        except:
            pass
    
    def add_to_recent_files(self, file_path):
        """Add a file to recent files list"""
        abs_path = os.path.abspath(file_path)
        if abs_path in self.recent_files:
            self.recent_files.remove(abs_path)
        self.recent_files.insert(0, abs_path)
        self.recent_files = self.recent_files[:5]  # Keep only 5 most recent
        self.save_recent_files()
    
    def open_recent_file(self, event=None):
        """Open a file from recent files"""
        selected = self.recent_var.get()
        if selected and selected != "Recent Files":
            # Find the full path
            for file_path in self.recent_files:
                if os.path.basename(file_path) == selected:
                    try:
                        # Test if the file is a valid database
                        test_db = TaskDatabase(file_path)
                        test_tasks = test_db.get_all_tasks()
                        
                        # If successful, switch to new database
                        self.db_path = file_path
                        self.db = test_db
                        self.db_info_label.config(text=f"DB: {os.path.basename(self.db_path)}")
                        self.root.title(f"Multi-Agent Task Database - {os.path.basename(self.db_path)}")
                        
                        # Move to top of recent files
                        self.add_to_recent_files(file_path)
                        
                        # Refresh the display
                        self.refresh_data()
                        self.status_bar.config(text=f"✓ Opened database: {os.path.basename(self.db_path)}")
                        
                    except Exception as e:
                        messagebox.showerror("Error", f"Failed to open database:\n{str(e)}")
                    break

class AddTaskDialog:
    def __init__(self, parent, db):
        self.db = db
        self.result = None
        
        # Create dialog window
        self.dialog = tk.Toplevel(parent)
        self.dialog.title("Add New Task")
        self.dialog.geometry("600x500")
        self.dialog.transient(parent)
        self.dialog.grab_set()
        
        # Center the dialog
        self.dialog.geometry("+%d+%d" % (parent.winfo_rootx() + 50, parent.winfo_rooty() + 50))
        
        self.setup_dialog()
    
    def setup_dialog(self):
        # Create scrollable frame
        canvas = tk.Canvas(self.dialog)
        scrollbar = ttk.Scrollbar(self.dialog, orient="vertical", command=canvas.yview)
        scrollable_frame = ttk.Frame(canvas)
        
        scrollable_frame.bind(
            "<Configure>",
            lambda e: canvas.configure(scrollregion=canvas.bbox("all"))
        )
        
        canvas.create_window((0, 0), window=scrollable_frame, anchor="nw")
        canvas.configure(yscrollcommand=scrollbar.set)
        
        main_frame = ttk.Frame(scrollable_frame, padding="20")
        main_frame.pack(fill=tk.BOTH, expand=True)
        
        # Agent field
        ttk.Label(main_frame, text="Agent:").pack(anchor=tk.W, pady=(0, 5))
        self.agent_entry = ttk.Entry(main_frame, width=50)
        self.agent_entry.pack(fill=tk.X, pady=(0, 10))
        
        # Description field
        ttk.Label(main_frame, text="Description:").pack(anchor=tk.W, pady=(0, 5))
        desc_frame = ttk.Frame(main_frame)
        desc_frame.pack(fill=tk.BOTH, expand=True, pady=(0, 10))
        
        self.desc_text = tk.Text(desc_frame, width=50, height=12, wrap=tk.WORD)
        desc_scrollbar = ttk.Scrollbar(desc_frame, orient="vertical", command=self.desc_text.yview)
        self.desc_text.configure(yscrollcommand=desc_scrollbar.set)
        
        self.desc_text.pack(side=tk.LEFT, fill=tk.BOTH, expand=True)
        desc_scrollbar.pack(side=tk.RIGHT, fill=tk.Y)
        
        # Status field
        ttk.Label(main_frame, text="Status:").pack(anchor=tk.W, pady=(0, 5))
        self.status_combo = ttk.Combobox(main_frame, values=["Not Started", "In Progress", "Done"])
        self.status_combo.set("Not Started")
        self.status_combo.pack(fill=tk.X, pady=(0, 10))
        
        # Buttons
        button_frame = ttk.Frame(main_frame)
        button_frame.pack(fill=tk.X, pady=(10, 0))
        
        ttk.Button(button_frame, text="Add Task", command=self.add_task).pack(side=tk.RIGHT, padx=(5, 0))
        ttk.Button(button_frame, text="Cancel", command=self.dialog.destroy).pack(side=tk.RIGHT)
        
        # Pack canvas and scrollbar
        canvas.pack(side="left", fill="both", expand=True)
        scrollbar.pack(side="right", fill="y")
        
        # Focus on agent entry
        self.agent_entry.focus()
        
        # Bind mousewheel to canvas
        def on_mousewheel(event):
            canvas.yview_scroll(int(-1*(event.delta/120)), "units")
        canvas.bind_all("<MouseWheel>", on_mousewheel)
    
    def add_task(self):
        agent = self.agent_entry.get().strip()
        description = self.desc_text.get("1.0", tk.END).strip()
        status = self.status_combo.get()
        
        if not agent or not description:
            messagebox.showerror("Error", "Please fill in all fields.")
            return
        
        task_id = self.db.add_task(agent, description, status)
        self.result = task_id
        messagebox.showinfo("Success", f"Task added with ID: {task_id}")
        self.dialog.destroy()

class TextEditorDialog:
    def __init__(self, parent, task_id, current_text, db, refresh_callback):
        self.db = db
        self.task_id = task_id
        self.refresh_callback = refresh_callback
        
        # Create dialog window
        self.dialog = tk.Toplevel(parent)
        self.dialog.title(f"Edit Task {task_id} Description")
        self.dialog.geometry("700x500")
        self.dialog.transient(parent)
        self.dialog.grab_set()
        
        # Center the dialog
        self.dialog.geometry("+%d+%d" % (parent.winfo_rootx() + 100, parent.winfo_rooty() + 100))
        
        self.setup_editor(current_text)
    
    def setup_editor(self, current_text):
        main_frame = ttk.Frame(self.dialog, padding="20")
        main_frame.pack(fill=tk.BOTH, expand=True)
        
        # Title
        title_label = ttk.Label(main_frame, text=f"Editing Task {self.task_id} Description", 
                               font=('Arial', 12, 'bold'))
        title_label.pack(anchor=tk.W, pady=(0, 10))
        
        # Text editor with scrollbar
        text_frame = ttk.Frame(main_frame)
        text_frame.pack(fill=tk.BOTH, expand=True, pady=(0, 10))
        
        self.text_editor = tk.Text(text_frame, wrap=tk.WORD, font=('Consolas', 10))
        scrollbar = ttk.Scrollbar(text_frame, orient="vertical", command=self.text_editor.yview)
        self.text_editor.configure(yscrollcommand=scrollbar.set)
        
        self.text_editor.pack(side=tk.LEFT, fill=tk.BOTH, expand=True)
        scrollbar.pack(side=tk.RIGHT, fill=tk.Y)
        
        # Insert current text
        self.text_editor.insert("1.0", current_text)
        
        # Character count label
        self.char_count = ttk.Label(main_frame, text="")
        self.char_count.pack(anchor=tk.W, pady=(0, 10))
        self.update_char_count()
        
        # Bind text change event
        self.text_editor.bind('<KeyRelease>', lambda e: self.update_char_count())
        
        # Buttons
        button_frame = ttk.Frame(main_frame)
        button_frame.pack(fill=tk.X)
        
        ttk.Button(button_frame, text="Save", command=self.save_text).pack(side=tk.RIGHT, padx=(5, 0))
        ttk.Button(button_frame, text="Cancel", command=self.dialog.destroy).pack(side=tk.RIGHT)
        
        # Focus on text editor
        self.text_editor.focus()
        
        # Keyboard shortcuts
        self.dialog.bind('<Control-s>', lambda e: self.save_text())
        self.dialog.bind('<Escape>', lambda e: self.dialog.destroy())
    
    def update_char_count(self):
        content = self.text_editor.get("1.0", tk.END)
        char_count = len(content) - 1  # Subtract 1 for the trailing newline
        word_count = len(content.split())
        self.char_count.config(text=f"Characters: {char_count}, Words: {word_count}")
    
    def save_text(self):
        new_text = self.text_editor.get("1.0", tk.END).strip()
        
        if not new_text:
            messagebox.showerror("Error", "Description cannot be empty.")
            return
        
        success = self.db.update_task_description(self.task_id, new_text)
        if success:
            self.refresh_callback()
            messagebox.showinfo("Success", f"Task {self.task_id} description updated")
            self.dialog.destroy()
        else:
            messagebox.showerror("Error", f"Failed to update task {self.task_id}")

def main():
    import sys
    
    # Check for command line arguments
    db_path = None
    if len(sys.argv) > 1:
        db_path = sys.argv[1]
        if not os.path.exists(db_path):
            print(f"Warning: Database file '{db_path}' does not exist. Will create new database.")
    
    root = tk.Tk()
    app = TaskDatabaseUI(root, db_path)
    
    # Handle window closing
    def on_closing():
        app.auto_refresh = False
        root.destroy()
    
    root.protocol("WM_DELETE_WINDOW", on_closing)
    root.mainloop()

if __name__ == "__main__":
    main()