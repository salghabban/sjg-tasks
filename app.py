import streamlit as st
import sqlite3
from supabase import create_client, Client
from datetime import datetime, timedelta
import os

# --- BADGE GENERATOR (SVG) ---
def get_badge_svg(status, created_at_str):
    size = 40
    radius = 15
    center = size / 2
    
    try:
        # Handle both string and datetime formats
        if isinstance(created_at_str, str):
            created_at = datetime.fromisoformat(created_at_str.replace('Z', '+00:00'))
        else:
            created_at = created_at
    except:
        created_at = datetime.now()
        
    now = datetime.now()
    diff_hours = (now - created_at.replace(tzinfo=None)).total_seconds() / 3600
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

# --- SUPABASE CONNECTION ---
@st.cache_resource
def init_supabase():
    """Initialize Supabase client"""
    try:
        supabase_url = st.secrets["supabase"]["url"]
        supabase_key = st.secrets["supabase"]["key"]
        supabase: Client = create_client(supabase_url, supabase_key)
        return supabase
    except Exception as e:
        st.error(f"Error connecting to Supabase: {e}")
        return None

def get_all_tasks(supabase):
    """Fetch all tasks from Supabase"""
    try:
        response = supabase.table("tasks").select("*").order("id", desc=True).execute()
        return response.data
    except Exception as e:
        st.error(f"Error fetching tasks: {e}")
        return []

def add_task(supabase, title, parent_id, created_by):
    """Add a new task to Supabase"""
    try:
        data = {
            "title": title,
            "parent_id": parent_id,
            "created_by": created_by,
            "status": "Active",
            "created_at": datetime.now().isoformat()
        }
        response = supabase.table("tasks").insert(data).execute()
        return response.data
    except Exception as e:
        st.error(f"Error adding task: {e}")
        return None

def update_task(supabase, task_id, updates):
    """Update a task in Supabase"""
    try:
        response = supabase.table("tasks").update(updates).eq("id", task_id).execute()
        return response.data
    except Exception as e:
        st.error(f"Error updating task: {e}")
        return None

def close_task(supabase, task_id, status, reason):
    """Close a task with strict protocol"""
    try:
        updates = {
            "status": status,
            "closure_reason": reason
        }
        response = supabase.table("tasks").update(updates).eq("id", task_id).execute()
        return response.data
    except Exception as e:
        st.error(f"Error closing task: {e}")
        return None

# --- APP UI ---
st.set_page_config(page_title="SJG TASKS", layout="wide", page_icon="✅")

# Initialize Supabase
supabase = init_supabase()

if supabase is None:
    st.error("❌ Cannot connect to database. Please check your Streamlit Secrets configuration.")
    st.stop()

st.title("✅ SJG TASKS - Enterprise Portal")
st.markdown("---")

menu = st.sidebar.selectbox("Navigation", [" Dashboard", "📋 All Tasks", " Add New Task"])

# --- PAGE 1: DASHBOARD ---
if menu == "📊 Dashboard":
    st.header("📊 Dashboard Overview")
    
    tasks = get_all_tasks(supabase)
    
    total_tasks = len(tasks)
    active_tasks = len([t for t in tasks if t['status'] in ['Active', 'open']])
    completed_tasks = len([t for t in tasks if t['status'] in ['Completed Successfully', 'Unachievable/Incomplete', 'completed']])
    
    completion_rate = 0
    if total_tasks > 0:
        completion_rate = round((completed_tasks / total_tasks) * 100, 1)
    
    recent_tasks = tasks[:5] if tasks else []
    
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
                            {status_emoji} {task['status']} • {task['created_at'][:10] if task['created_at'] else 'N/A'}
                        </div>
                    </div>
                </div>
                """, unsafe_allow_html=True)
        else: st.info("No tasks yet.")
    with col_right:
        st.markdown("### 📊 Status Breakdown")
        if tasks:
            status_counts = {}
            for task in tasks:
                status = task['status']
                status_counts[status] = status_counts.get(status, 0) + 1
            st.bar_chart(status_counts)
        else: st.info("No data yet.")

# --- PAGE 2: ALL TASKS ---
elif menu == " All Tasks":
    st.header("Task Management")
    tasks = get_all_tasks(supabase)

    if not tasks:
        st.info("No tasks yet. Go to '➕ Add New Task' to create one.")
    else:
        st.write(f"**Found {len(tasks)} task(s)**")
        st.markdown("---")
        
        for task in tasks:
            with st.container():
                col_badge, col_content = st.columns([0.1, 0.9])
                with col_badge:
                    badge_svg = get_badge_svg(task['status'], task['created_at'])
                    st.markdown(badge_svg, unsafe_allow_html=True)
                with col_content:
                    st.markdown(f"### Task #{task['id']}: {task['title']}")
                    st.caption(f"Status: **{task['status']}** | Created: {task['created_at'][:10] if task['created_at'] else 'N/A'} | By: {task['created_by']}")
                    if task['parent_id']:
                        st.caption(f"Parent Task ID: {task['parent_id']}")
                    
                    st.markdown("---")
                    
                    # EDIT TASK
                    st.markdown("#### ✏️ Edit Task Details")
                    all_tasks = get_all_tasks(supabase)
                    parent_options = [None] + [f"#{t['id']} - {t['title']}" for t in all_tasks if t['id'] != task['id']]
                    
                    current_parent_str = None
                    if task['parent_id']:
                        parent_task = next((t for t in all_tasks if t['id'] == task['parent_id']), None)
                        if parent_task:
                            current_parent_str = f"#{task['parent_id']} - {parent_task['title']}"
                    
                    with st.form(key=f"edit_form_{task['id']}"):
                        new_title = st.text_input("Task Title", value=task['title'], key=f"edit_title_{task['id']}")
                        idx = parent_options.index(current_parent_str) if current_parent_str in parent_options else 0
                        new_parent = st.selectbox("Parent Task (Optional)", parent_options, index=idx, key=f"edit_parent_{task['id']}")
                        
                        if st.form_submit_button("💾 Save Changes", use_container_width=True):
                            new_parent_id = int(new_parent.split(" - ")[0].replace("#", "")) if new_parent else None
                            update_task(supabase, task['id'], {"title": new_title, "parent_id": new_parent_id})
                            st.success(f"✅ Task #{task['id']} updated successfully!")
                            st.rerun()

                    st.markdown("---")

                    # CLOSE / RE-OPEN
                    if task['status'] not in ['Completed Successfully', 'Unachievable/Incomplete', 'completed']:
                        st.warning("⚠️ This task is currently Active/Open.")
                        with st.form(key=f"close_form_{task['id']}"):
                            st.markdown("**Strict Closure Protocol**")
                            reason = st.text_area("Mandatory Reason for Closure (Min 10 chars):", key=f"reason_{task['id']}")
                            status_choice = st.selectbox("Final Status:", ["Completed Successfully", "Unachievable/Incomplete"], key=f"status_{task['id']}")
                            
                            if st.form_submit_button(" Close Task", use_container_width=True):
                                if len(reason.strip()) < 10:
                                    st.error("❌ Error: Reason must be at least 10 characters.")
                                else:
                                    close_task(supabase, task['id'], status_choice, reason)
                                    st.success(f"✅ Task closed as: {status_choice}")
                                    st.rerun()
                    else:
                        st.success(f"🟢 Task is Closed: {task['status']}")
                        if task.get('closure_reason'):
                            st.info(f"**Closure Reason:** {task['closure_reason']}")
                        
                        if st.button(" Re-open Task", key=f"reopen_{task['id']}"):
                            update_task(supabase, task['id'], {"status": "Active", "closure_reason": None})
                            st.success("Task re-opened successfully!")
                            st.rerun()
                    
                st.markdown("---")

# --- PAGE 3: ADD NEW TASK ---
elif menu == "➕ Add New Task":
    st.header("Create New Task")
    all_tasks = get_all_tasks(supabase)
    
    parent_options = [None] + [f"#{t['id']} - {t['title']}" for t in all_tasks]
    
    with st.form(key="add_task_form"):
        title = st.text_input("Task Title", placeholder="e.g., Q3 Marketing Campaign")
        parent_choice = st.selectbox("Is this a Sub-task? (Optional)", parent_options)
        
        if st.form_submit_button("Create Task"):
            if not title.strip():
                st.error("❌ Task title cannot be empty.")
            else:
                parent_id = int(parent_choice.split(" - ")[0].replace("#", "")) if parent_choice else None
                result = add_task(supabase, title, parent_id, 'Admin')
                if result:
                    st.success(f"✅ Task '{title}' created successfully!")
                    st.rerun()
