import streamlit as st
import sqlite3
from datetime import datetime, timedelta

# --- BADGE GENERATOR (SVG) ---
def get_badge_svg(status, created_at_str):
    size = 40
    radius = 15
    center = size / 2
    
    try:
        created_at = datetime.strptime(created_at_str, "%Y-%m-%d %H:%M:%S")
    except:
        created_at = datetime.now()
        
    now = datetime.now()
    diff_hours = (now - created_at).total_seconds() / 3600
    diff_days = diff_hours / 24
    
    if status in ['Completed Successfully', 'Unachievable/Incomplete', 'completed']:
        return f'''<svg width="{size}" height="{size}" viewBox="0 0 {size} {size}">
            <circle cx="{center}" cy="{center}" r="{radius}" fill="#28a745" />
            <path d="M12 20 L18 26 L28 14" stroke="white" stroke-width="3" fill="none" stroke-linecap="round" stroke-linejoin="round"/>
        </svg>'''
    elif diff_days > 30:
        return f'''<svg width="{size}" height="{size}" viewBox="0 0 {size} {size}">
            <circle cx="{center}" cy="{center}" r="{radius}" fill="#dc3545" />
            <text x="{center}" y="{center+5}" fill="white" font-size="10" font-weight="bold" text-anchor="middle">{int(diff_days)}d</text>
        </svg>'''
    elif diff_days >= 1:
        progress = min(diff_days / 30.0, 1.0)
        circumference = 2 * 3.14159 * radius
        offset = circumference - (progress * circumference)
        return f'''<svg width="{size}" height="{size}" viewBox="0 0 {size} {size}">
            <circle cx="{center}" cy="{center}" r="{radius}" fill="white" stroke="#f0f0f0" stroke-width="2" />
            <circle cx="{center}" cy="{center}" r="{radius}" fill="none" stroke="#dc3545" stroke-width="4" 
                    stroke-dasharray="{circumference}" stroke-dashoffset="{offset}" transform="rotate(-90 {center} {center})" />
            <text x="{center}" y="{center+4}" fill="#dc3545" font-size="10" font-weight="bold" text-anchor="middle">{int(diff_days)}d</text>
        </svg>'''
    else:
        return f'''<svg width="{size}" height="{size}" viewBox="0 0 {size} {size}">
            <circle cx="{center}" cy="{center}" r="{radius}" fill="white" stroke="#dc3545" stroke-width="3" />
            <text x="{center}" y="{center+4}" fill="#dc3545" font-size="10" font-weight="bold" text-anchor="middle">{int(diff_hours)}h</text>
        </svg>'''


def init_db():
    conn = sqlite3.connect('sjg_tasks.db')
    c = conn.cursor()
    c.execute('''CREATE TABLE IF NOT EXISTS tasks 
                 (id INTEGER PRIMARY KEY AUTOINCREMENT, 
                  title TEXT NOT NULL, 
                  parent_id INTEGER, 
                  created_by TEXT DEFAULT 'Admin',
                  status TEXT DEFAULT 'Active', 
                  closure_reason TEXT, 
                  created_at TEXT)''')
    conn.commit()
    conn.close()

def get_db():
    conn = sqlite3.connect('sjg_tasks.db')
    conn.row_factory = sqlite3.Row
    return conn

# --- APP UI ---
st.set_page_config(page_title="SJG TASKS", layout="wide", page_icon="✅")
init_db()

st.title("✅ SJG TASKS - Enterprise Portal")
st.markdown("---")

# Fixed the menu names to match exactly
menu = st.sidebar.selectbox("Navigation", ["📊 Dashboard", "📋 All Tasks", "➕ Add New Task", "🔧 Fix Database"])

# --- PAGE 1: DASHBOARD ---
if menu == "📊 Dashboard":
    st.header(" Dashboard Overview")
    conn = get_db()
    total_tasks = conn.execute("SELECT COUNT(*) FROM tasks").fetchone()[0]
    active_tasks = conn.execute("SELECT COUNT(*) FROM tasks WHERE status IN ('Active', 'open')").fetchone()[0]
    completed_tasks = conn.execute("SELECT COUNT(*) FROM tasks WHERE status IN ('Completed Successfully', 'Unachievable/Incomplete', 'completed')").fetchone()[0]
    
    completion_rate = 0
    if total_tasks > 0:
        completion_rate = round((completed_tasks / total_tasks) * 100, 1)
    
    recent_tasks = conn.execute("SELECT * FROM tasks ORDER BY created_at DESC LIMIT 5").fetchall()
    status_breakdown = conn.execute("SELECT status, COUNT(*) as count FROM tasks GROUP BY status").fetchall()
    conn.close()
    
    col1, col2, col3, col4 = st.columns(4)
    with col1: st.metric(label="📋 Total Tasks", value=total_tasks)
    with col2: st.metric(label="🔴 Active Tasks", value=active_tasks, delta=f"{active_tasks} pending")
    with col3: st.metric(label="✅ Completed", value=completed_tasks, delta=f"{completion_rate}% rate")
    with col4: st.metric(label="📊 Completion Rate", value=f"{completion_rate}%", delta="Overall progress")
    
    st.markdown("### 📈 Overall Progress")
    if total_tasks > 0:
        st.progress(completion_rate / 100)
        st.caption(f"{completed_tasks} of {total_tasks} tasks completed")
    else:
        st.info("No tasks yet. Create your first task to see progress!")
    
    st.markdown("---")
    col_left, col_right = st.columns([2, 1])
    with col_left:
        st.markdown("### 🕐 Recent Tasks")
        if recent_tasks:
            for task in recent_tasks:
                badge_svg = get_badge_svg(task['status'], task['created_at'])
                status_emoji = "✅" if task['status'] in ['Completed Successfully', 'completed'] else "🔴"
                st.markdown(f"""
                <div style="display: flex; align-items: center; gap: 10px; padding: 10px; background-color: #1e1e1e; border-radius: 8px; margin-bottom: 8px;">
                    {badge_svg}
                    <div>
                        <div style="font-weight: bold;">{task['title']}</div>
                        <div style="font-size: 0.8em; color: #888;">
                            {status_emoji} {task['status']} • {task['created_at'][:10]}
                        </div>
                    </div>
                </div>
                """, unsafe_allow_html=True)
        else: st.info("No tasks yet.")
    with col_right:
        st.markdown("### 📊 Status Breakdown")
        if status_breakdown:
            status_data = {s[0]: s[1] for s in status_breakdown}
            st.bar_chart(status_data)
        else: st.info("No data yet.")

# --- PAGE 2: ALL TASKS (Fixed the menu name match) ---
elif menu == "📋 All Tasks":
    st.header("Task Management")
    conn = get_db()
    tasks = conn.execute("SELECT * FROM tasks ORDER BY id DESC").fetchall()
    conn.close()

    if not tasks:
        st.info("No tasks yet. Go to '➕ Add New Task' to create one.")
    else:
        st.write(f"**Found {len(tasks)} task(s)**")
        st.markdown("---")
        
        for task in tasks:
            task_container = st.container()
            with task_container:
                col_badge, col_content = st.columns([0.1, 0.9])
                with col_badge:
                    badge_svg = get_badge_svg(task['status'], task['created_at'])
                    st.markdown(badge_svg, unsafe_allow_html=True)
                with col_content:
                    st.markdown(f"### Task #{task['id']}: {task['title']}")
                    st.caption(f"Status: **{task['status']}** | Created: {task['created_at']} | By: {task['created_by']}")
                    if task['parent_id']:
                        st.caption(f"Parent Task ID: {task['parent_id']}")
                    
                    st.markdown("---")
                    
                    # --- EDIT TASK SECTION ---
                    st.markdown("#### ✏️ Edit Task Details")
                    conn_loop = get_db()
                    all_tasks_list = conn_loop.execute("SELECT id, title FROM tasks").fetchall()
                    
                    parent_options = [None] + [f"#{t['id']} - {t['title']}" for t in all_tasks_list if t['id'] != task['id']]
                    current_parent_str = None
                    if task['parent_id']:
                        current_parent_str = f"#{task['parent_id']} - {next((t['title'] for t in all_tasks_list if t['id'] == task['parent_id']), 'Unknown')}"

                    with st.form(key=f"edit_form_{task['id']}"):
                        new_title = st.text_input("Task Title", value=task['title'], key=f"edit_title_{task['id']}")
                        idx = parent_options.index(current_parent_str) if current_parent_str in parent_options else 0
                        new_parent = st.selectbox("Parent Task (Optional)", parent_options, index=idx, key=f"edit_parent_{task['id']}")
                        
                        col_btn1, col_btn2 = st.columns(2)
                        with col_btn1:
                            edit_submitted = st.form_submit_button("💾 Save Changes", use_container_width=True)
                        
                        if edit_submitted:
                            new_parent_id = None
                            if new_parent:
                                new_parent_id = int(new_parent.split(" - ")[0].replace("#", ""))
                            
                            conn_loop.execute("UPDATE tasks SET title=?, parent_id=? WHERE id=?", (new_title, new_parent_id, task['id']))
                            conn_loop.commit()
                            conn_loop.close()
                            st.success(f"✅ Task #{task['id']} updated successfully!")
                            st.rerun()

                    st.markdown("---")

                    # --- CLOSE / RE-OPEN SECTION ---
                    if task['status'] not in ['Completed Successfully', 'Unachievable/Incomplete', 'completed']:
                        st.warning("⚠️ This task is currently Active/Open.")
                        with st.form(key=f"close_form_{task['id']}"):
                            st.markdown("**Strict Closure Protocol**")
                            reason = st.text_area("Mandatory Reason for Closure (Min 10 chars):", key=f"reason_{task['id']}")
                            status_choice = st.selectbox("Final Status:", ["Completed Successfully", "Unachievable/Incomplete"], key=f"status_{task['id']}")
                            close_submitted = st.form_submit_button("🔒 Close Task", use_container_width=True)
                            
                            if close_submitted:
                                if len(reason.strip()) < 10:
                                    st.error("❌ Error: Reason must be at least 10 characters.")
                                else:
                                    conn_loop.execute("UPDATE tasks SET status=?, closure_reason=? WHERE id=?", (status_choice, reason, task['id']))
                                    conn_loop.commit()
                                    conn_loop.close()
                                    st.success(f"✅ Task closed as: {status_choice}")
                                    st.rerun()
                    else:
                        st.success(f" Task is Closed: {task['status']}")
                        if task['closure_reason']:
                            st.info(f"**Closure Reason:** {task['closure_reason']}")
                        
                        # Re-open button
                        if st.button("🔄 Re-open Task", key=f"reopen_{task['id']}"):
                            conn_loop.execute("UPDATE tasks SET status='Active', closure_reason=NULL WHERE id=?", (task['id'],))
                            conn_loop.commit()
                            conn_loop.close()
                            st.success("Task re-opened successfully!")
                            st.rerun()
                    
                    conn_loop.close()
                st.markdown("---")

# --- PAGE 3: ADD NEW TASK ---
elif menu == " Add New Task":
    st.header("Create New Task")
    conn = get_db()
    all_tasks = conn.execute("SELECT id, title FROM tasks").fetchall()
    conn.close()
    
    parent_options = [None] + [f"#{t['id']} - {t['title']}" for t in all_tasks]
    
    with st.form(key="add_task_form"):
        title = st.text_input("Task Title", placeholder="e.g., Q3 Marketing Campaign")
        parent_choice = st.selectbox("Is this a Sub-task? (Optional)", parent_options)
        submitted = st.form_submit_button("Create Task")
        
        if submitted:
            if not title.strip():
                st.error("❌ Task title cannot be empty.")
            else:
                parent_id = int(parent_choice.split(" - ")[0].replace("#", "")) if parent_choice else None
                conn = get_db()
                conn.execute("INSERT INTO tasks (title, parent_id, created_by, created_at, status) VALUES (?, ?, ?, ?, ?)",
                             (title, parent_id, 'Admin', datetime.now().strftime("%Y-%m-%d %H:%M:%S"), 'Active'))
                conn.commit()
                conn.close()
                st.success(f"✅ Task '{title}' created successfully!")
                st.rerun()

# --- PAGE 4: FIX DATABASE ---
elif menu == " Fix Database":
    st.header("Database Diagnostics & Fix")
    conn = get_db()
    st.subheader("Current Status Values in Database:")
    status_check = conn.execute("SELECT DISTINCT status FROM tasks").fetchall()
    if status_check:
        for s in status_check: st.write(f"- '{s[0]}'")
    else: st.write("No tasks in database yet.")
    
    st.markdown("---")
    if st.button("🔧 Fix All Tasks to 'Active' Status"):
        conn.execute("UPDATE tasks SET status = 'Active' WHERE status IS NULL OR status = '' OR status = 'open'")
        conn.commit()
        st.success("✅ All tasks have been set to 'Active' status!")
        st.rerun()
    
    st.markdown("---")
    st.warning("⚠️ Dangerous Zone")
    if st.button("🗑️ Delete ALL Tasks (Start Fresh)"):
        conn.execute("DELETE FROM tasks")
        conn.commit()
        st.success("✅ All tasks deleted.")
        st.rerun()
    conn.close()