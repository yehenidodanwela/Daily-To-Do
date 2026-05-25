import sqlite3, os, json
src=r'D:\\Uni\\My Projects\\16. To Do\\todo_app.db'
dst=r'C:\\Users\\Acer\\AppData\\Roaming\\DailyTodo\\todo_app.db'
print('src exists', os.path.exists(src))
print('dst exists', os.path.exists(dst))
if not os.path.exists(src):
    raise SystemExit('no src')
s=sqlite3.connect(src)
s.row_factory=sqlite3.Row
rows=s.execute('SELECT id,title,reminder_time,start_date,completed_today,reminded_today,created_at FROM tasks').fetchall()
print('found', len(rows), 'rows in src')
if not os.path.exists(dst):
    open(dst,'wb').close()
d=sqlite3.connect(dst)
d.row_factory=None
for r in rows:
    title=r['title']
    reminder_time=r['reminder_time']
    next_due=r['start_date'] or '2026-01-01'
    completed=int(r['completed_today'] or 0)
    reminded=int(r['reminded_today'] or 0)
    created_at=r['created_at'] or None
    # avoid duplicates
    exists=d.execute('SELECT COUNT(1) FROM tasks WHERE title=? AND reminder_time=?',(title,reminder_time)).fetchone()[0]
    if not exists:
        d.execute('INSERT INTO tasks (title,reminder_time,repeat_rule,next_due_date,completed_today,reminded_today,last_reminded_date,created_at) VALUES (?,?,?,?,?,?,NULL,?)', (title,reminder_time,'daily', next_due, completed, reminded, created_at))
        print('inserted', title)
    else:
        print('skipped dup', title)
d.commit()
print('dst count', d.execute('SELECT COUNT(1) FROM tasks').fetchone()[0])
drows=d.execute('SELECT id,title,reminder_time,repeat_rule,next_due_date,completed_today,reminded_today FROM tasks').fetchall()
print(json.dumps(drows))
s.close(); d.close()
