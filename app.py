import streamlit as st
import pandas as pd
import pymysql

st.set_page_config(
    page_title="Beyond Diagnosis — HIV Support System",
    page_icon="❤️",
    layout="wide"
)

def run_query(sql):
    try:
        conn = pymysql.connect(
            host="shortline.proxy.rlwy.net",
            port=36258,
            user="root",
            password="ZJPPtOprIWCdIcLrwSTYcynzzbJLRXQR",
            database="railway"
        )
        df = pd.read_sql(sql, conn)
        conn.close()
        return df
    except Exception as e:
        st.error(f"Query error: {e}")
        return pd.DataFrame()

STAGE_DEFS = [
    {"id": 1, "short": "Acute",       "cd4": "> 500 cells/mm³",      "emoji": "🔵"},
    {"id": 2, "short": "Chronic",     "cd4": "200–499 cells/mm³",    "emoji": "🟡"},
    {"id": 3, "short": "Symptomatic", "cd4": "100–199 cells/mm³",    "emoji": "🟠"},
    {"id": 4, "short": "AIDS",        "cd4": "< 200 cells/mm³",      "emoji": "🔴"},
    {"id": 5, "short": "Suppressed",  "cd4": "> 200 (Undetectable)", "emoji": "🟢"},
]

def render_stage_tracker(current_stage_id, stage_name):
    st.markdown(f"### 🗺️ HIV Care Journey — Currently at **{stage_name}**")
    cols = st.columns(9)  # 5 stages + 4 arrows
    col_positions = [0, 2, 4, 6, 8]

    for i, stage in enumerate(STAGE_DEFS):
        sid = stage["id"]
        col = cols[col_positions[i]]

        if sid == current_stage_id:
            icon = "📍"
            label = f"{stage['short']} ← You are here"
        elif sid < current_stage_id or (current_stage_id == 5):
            icon = "✅"
            label = stage["short"]
        else:
            icon = "⬜"
            label = stage["short"]

        col.markdown(f"<div style='text-align:center'>{icon}<br><b>{label}</b><br><small>{stage['cd4']}</small></div>", unsafe_allow_html=True)

        # Arrow between stages
        if i < 4:
            cols[col_positions[i] + 1].markdown("<div style='text-align:center;font-size:24px;padding-top:8px'>→</div>", unsafe_allow_html=True)

    st.markdown("---")


if "logged_in" not in st.session_state:
    st.session_state.logged_in = False
    st.session_state.role      = None
    st.session_state.user_id   = None

def login_screen():
    col1, col2, col3 = st.columns([1, 2, 1])
    with col2:
        st.markdown("## ❤️ Beyond Diagnosis")
        st.markdown("#### HIV Patient Support System")
        st.markdown("---")
        role    = st.selectbox("I am a:", ["Patient", "Doctor", "Therapist"])
        user_id = st.number_input("Enter your ID:", min_value=1, max_value=500, value=1, step=1)
        if st.button("🔐 Login", use_container_width=True):
            if role == "Patient":
                df = run_query(f"SELECT patient_id FROM patient WHERE patient_id = {user_id}")
            elif role == "Doctor":
                df = run_query(f"SELECT doctor_id FROM doctor WHERE doctor_id = {user_id}")
            else:
                df = run_query(f"SELECT therapist_id FROM therapist WHERE therapist_id = {user_id}")
            if not df.empty:
                st.session_state.logged_in = True
                st.session_state.role      = role
                st.session_state.user_id   = int(user_id)
                st.rerun()
            else:
                st.error(f"❌ {role} ID {user_id} not found.")

def patient_dashboard(patient_id):
    df_patient = run_query(f"""
        SELECT p.patient_id, p.anon_alias, p.age_range, p.gender_identity,
               p.registration_date, cs.care_stage_id, cs.stage_name, cs.cd4_range,
               cs.intervention_level, cs.description
        FROM patient p
        JOIN care_stage cs ON p.current_stage_id = cs.care_stage_id
        WHERE p.patient_id = {patient_id}
    """)
    if df_patient.empty:
        st.error("Patient not found.")
        return
    row = df_patient.iloc[0]
    st.markdown(f"## 👤 Welcome, {row['anon_alias']}")
    st.markdown("---")

    # ── Metrics
    c1, c2, c3, c4 = st.columns(4)
    c1.metric("Age Range",  row['age_range'])
    c2.metric("Gender",     row['gender_identity'])
    c3.metric("Care Stage", row['stage_name'])
    c4.metric("CD4 Range",  row['cd4_range'])

    # ── Care Stage Tracker
    render_stage_tracker(int(row['care_stage_id']), row['stage_name'])

    st.info(f"🏥 Intervention Level: {row['intervention_level']}")
    st.markdown(f"📋 {str(row['description'])}")
    st.markdown("---")

    # ── Positive Wellness Card
    st.markdown("### 💚 Your Progress — You Are Doing Amazing!")

    df_fu_all = run_query(f"SELECT status FROM followup_instance WHERE patient_id = {patient_id}")
    df_ts_all = run_query(f"SELECT session_date FROM therapy_session WHERE patient_id = {patient_id}")
    df_ep_all = run_query(f"SELECT completion_status FROM education_progress WHERE patient_id = {patient_id}")
    df_reg    = run_query(f"SELECT registration_date FROM patient WHERE patient_id = {patient_id}")

    total_visits  = len(df_fu_all)
    kept_visits   = len(df_fu_all[df_fu_all['status'] == 'Completed']) if not df_fu_all.empty else 0
    therapy_count = len(df_ts_all)
    total_modules = len(df_ep_all)
    done_modules  = len(df_ep_all[df_ep_all['completion_status'] == 'Completed']) if not df_ep_all.empty else 0

    days_in_care = 0
    if not df_reg.empty:
        import datetime
        reg = pd.to_datetime(df_reg.iloc[0]['registration_date'])
        days_in_care = (datetime.datetime.today() - reg).days

    visit_pct = int((kept_visits / total_visits * 100)) if total_visits > 0 else 0
    edu_pct   = int((done_modules / total_modules * 100)) if total_modules > 0 else 0

    if visit_pct >= 75:
        visit_msg = f"Outstanding! You attended {kept_visits} of {total_visits} appointments."
    elif visit_pct >= 50:
        visit_msg = f"Great effort! You attended {kept_visits} of {total_visits} appointments."
    else:
        visit_msg = f"Keep going! You attended {kept_visits} of {total_visits} appointments."

    if done_modules >= 5:
        edu_msg = f"Incredible! You completed {done_modules} education modules — knowledge is power!"
    elif done_modules >= 2:
        edu_msg = f"Nice work! You completed {done_modules} modules — keep learning!"
    else:
        edu_msg = f"Great start! You completed {done_modules} modules so far."

    if therapy_count >= 10:
        therapy_msg = f"Fantastic! You attended {therapy_count} therapy sessions — investing in your wellbeing!"
    elif therapy_count >= 5:
        therapy_msg = f"Well done! You attended {therapy_count} therapy sessions."
    else:
        therapy_msg = f"You attended {therapy_count} therapy sessions — every session counts!"

    w1, w2, w3, w4 = st.columns(4)
    w1.success(f"🎯 Appointments\n\n{visit_msg}\n\n{visit_pct}% kept")
    w2.success(f"📚 Learning Journey\n\n{edu_msg}\n\n{edu_pct}% complete")
    w3.success(f"🧠 Therapy\n\n{therapy_msg}")
    w4.success(f"❤️ Days in Care\n\nYou have been actively managing your health for {days_in_care} days. That takes real strength!")

    st.markdown("---")

    col1, col2 = st.columns(2)
    with col1:
        st.markdown("### 📅 Follow-Up History")
        df_fu = run_query(f"""
            SELECT followup_date, visit_type, status, notes
            FROM followup_instance
            WHERE patient_id = {patient_id}
            ORDER BY followup_date DESC LIMIT 10
        """)
        if not df_fu.empty:
            def highlight_status(row):
                if row['status'] == 'Completed':
                    return ['background-color: #EAFAF1'] * len(row)
                elif row['status'] == 'Missed':
                    return ['background-color: #FDEDEC'] * len(row)
                else:
                    return ['background-color: #FEF9E7'] * len(row)
            st.dataframe(df_fu.style.apply(highlight_status, axis=1), use_container_width=True, height=280)
        else:
            st.info("No follow-up records found.")

    with col2:
        st.markdown("### 🧠 Therapy Sessions")
        df_ts = run_query(f"""
            SELECT session_date, modality, outcome, session_notes
            FROM therapy_session
            WHERE patient_id = {patient_id}
            ORDER BY session_date DESC LIMIT 10
        """)
        if not df_ts.empty:
            st.dataframe(df_ts, use_container_width=True, height=280)
        else:
            st.info("No therapy sessions found.")

    st.markdown("---")
    st.markdown("### 📚 Education Progress")
    df_ep = run_query(f"""
        SELECT er.title, er.category, er.format,
               ep.completion_status, ep.self_rating, ep.access_date
        FROM education_progress ep
        JOIN education_resource er ON ep.resource_id = er.resource_id
        WHERE ep.patient_id = {patient_id}
        ORDER BY ep.access_date DESC
    """)
    if not df_ep.empty:
        total     = len(df_ep)
        completed = len(df_ep[df_ep['completion_status'] == 'Completed'])
        pct       = completed / total if total > 0 else 0
        st.progress(pct, text=f"✅ {completed} of {total} modules completed ({pct*100:.0f}%)")
        st.dataframe(df_ep, use_container_width=True, height=250)
    else:
        st.info("No education records found.")

    st.markdown("---")
    st.markdown("### 🛡️ My Prevention Strategies")
    df_pp = run_query(f"""
        SELECT ps.strategy_name, ps.target_population,
               pp.enrollment_date, pp.adherence_status
        FROM patient_prevention pp
        JOIN prevention_strategy ps ON pp.strategy_id = ps.strategy_id
        WHERE pp.patient_id = {patient_id}
        ORDER BY pp.enrollment_date DESC
    """)
    if not df_pp.empty:
        st.dataframe(df_pp, use_container_width=True)
    else:
        st.info("No prevention strategies enrolled.")

def clinician_dashboard(doctor_id):
    st.markdown("## 🏥 Clinician Dashboard")
    df_doc = run_query(f"SELECT specialization, organization, years_experience FROM doctor WHERE doctor_id = {doctor_id}")
    if not df_doc.empty:
        d = df_doc.iloc[0]
        st.markdown(f"**Specialization:** {d['specialization']}  |  **Organization:** {d['organization']}  |  **Experience:** {d['years_experience']} years")
    st.markdown("---")
    c1, c2, c3, c4 = st.columns(4)
    c1.metric("👥 Total Patients",   run_query("SELECT COUNT(*) AS n FROM patient").iloc[0]['n'])
    c2.metric("⚠️ Missed Visits",    run_query("SELECT COUNT(*) AS n FROM followup_instance WHERE status = 'Missed'").iloc[0]['n'])
    c3.metric("✅ Completed Visits", run_query("SELECT COUNT(*) AS n FROM followup_instance WHERE status = 'Completed'").iloc[0]['n'])
    c4.metric("🧠 Therapy Sessions", run_query("SELECT COUNT(*) AS n FROM therapy_session").iloc[0]['n'])
    st.markdown("---")
    st.markdown("### ⚠️ Missed Visit Alerts — Top 10 Patients")
    df_missed = run_query("""
        SELECT p.patient_id, p.anon_alias, p.age_range,
               cs.stage_name, COUNT(*) AS missed_visits
        FROM followup_instance fi
        JOIN patient p     ON fi.patient_id      = p.patient_id
        JOIN care_stage cs ON p.current_stage_id = cs.care_stage_id
        WHERE fi.status = 'Missed'
        GROUP BY p.patient_id, p.anon_alias, p.age_range, cs.stage_name
        ORDER BY missed_visits DESC LIMIT 10
    """)
    if not df_missed.empty:
        st.dataframe(df_missed, use_container_width=True, height=280)
    st.markdown("---")
    st.markdown("### 👥 All Patients Overview")
    search = st.text_input("🔍 Search by alias or care stage:", "")
    df_all = run_query("""
        SELECT p.patient_id, p.anon_alias, p.age_range, p.gender_identity,
               cs.stage_name,
               COUNT(DISTINCT fi.followup_date) AS total_visits,
               SUM(CASE WHEN fi.status = 'Missed'    THEN 1 ELSE 0 END) AS missed,
               SUM(CASE WHEN fi.status = 'Completed' THEN 1 ELSE 0 END) AS completed
        FROM patient p
        LEFT JOIN care_stage cs        ON p.current_stage_id = cs.care_stage_id
        LEFT JOIN followup_instance fi ON p.patient_id       = fi.patient_id
        GROUP BY p.patient_id, p.anon_alias, p.age_range, p.gender_identity, cs.stage_name
        ORDER BY missed DESC
    """)
    if search:
        df_all = df_all[
            df_all['anon_alias'].str.contains(search, case=False, na=False) |
            df_all['stage_name'].str.contains(search, case=False, na=False)
        ]
    st.dataframe(df_all, use_container_width=True, height=350)
    st.markdown("---")
    st.markdown("### 📊 Care Stage Distribution")
    df_stages = run_query("""
        SELECT cs.stage_name, COUNT(*) AS patient_count
        FROM patient p
        JOIN care_stage cs ON p.current_stage_id = cs.care_stage_id
        GROUP BY cs.stage_name ORDER BY patient_count DESC
    """)
    if not df_stages.empty:
        st.bar_chart(df_stages.set_index('stage_name')['patient_count'])

def therapist_dashboard(therapist_id):
    st.markdown("## 🧠 Therapist Dashboard")
    df_th = run_query(f"SELECT therapy_type, organization, license_type FROM therapist WHERE therapist_id = {therapist_id}")
    if not df_th.empty:
        t = df_th.iloc[0]
        st.markdown(f"**Therapy Type:** {t['therapy_type']}  |  **Organization:** {t['organization']}  |  **License:** {t['license_type']}")
    st.markdown("---")
    c1, c2, c3 = st.columns(3)
    c1.metric("📋 Total Sessions",    run_query(f"SELECT COUNT(*) AS n FROM therapy_session WHERE therapist_id = {therapist_id}").iloc[0]['n'])
    c2.metric("✅ Improved Outcomes", run_query(f"SELECT COUNT(*) AS n FROM therapy_session WHERE therapist_id = {therapist_id} AND outcome = 'Improved'").iloc[0]['n'])
    c3.metric("👥 Patients Seen",     run_query(f"SELECT COUNT(DISTINCT patient_id) AS n FROM therapy_session WHERE therapist_id = {therapist_id}").iloc[0]['n'])
    st.markdown("---")
    st.markdown("### 📋 My Sessions")
    df_sessions = run_query(f"""
        SELECT ts.session_date, p.anon_alias, ts.modality, ts.outcome, ts.session_notes
        FROM therapy_session ts
        JOIN patient p ON ts.patient_id = p.patient_id
        WHERE ts.therapist_id = {therapist_id}
        ORDER BY ts.session_date DESC LIMIT 20
    """)
    if not df_sessions.empty:
        st.dataframe(df_sessions, use_container_width=True, height=350)
    else:
        st.info("No sessions found.")
    st.markdown("---")
    st.markdown("### 📊 Outcome Distribution")
    df_outcomes = run_query(f"""
        SELECT outcome, COUNT(*) AS count FROM therapy_session
        WHERE therapist_id = {therapist_id}
        GROUP BY outcome ORDER BY count DESC
    """)
    if not df_outcomes.empty:
        st.bar_chart(df_outcomes.set_index('outcome')['count'])

def education_hub():
    st.markdown("## 📚 Education & Prevention Hub")
    st.markdown("---")
    st.markdown("### 🔍 Browse Education Resources")
    df_res = run_query("SELECT resource_id, title, category, format, stage_target, source_url FROM education_resource ORDER BY category, title")
    if not df_res.empty:
        categories = ["All"] + sorted(df_res['category'].dropna().unique().tolist())
        selected   = st.selectbox("Filter by category:", categories)
        df_show    = df_res if selected == "All" else df_res[df_res['category'] == selected]
        st.dataframe(df_show, use_container_width=True, height=300)
    st.markdown("---")
    st.markdown("### 🛡️ Prevention Strategies")
    df_prev = run_query("SELECT strategy_name, target_population, source_guideline FROM prevention_strategy ORDER BY strategy_name")
    st.dataframe(df_prev, use_container_width=True)
    st.markdown("---")
    st.markdown("### 🔬 Opportunistic Infection Reference (CDC/NIH Guidelines)")
    df_oi = run_query("SELECT oi_name, cd4_threshold, prophylaxis_rec, first_line_drug, monitoring_interval FROM oi_reference ORDER BY cd4_threshold")
    st.dataframe(df_oi, use_container_width=True)

if not st.session_state.logged_in:
    login_screen()
else:
    with st.sidebar:
        st.markdown("## ❤️ Beyond Diagnosis")
        st.markdown(f"**Role:** {st.session_state.role}")
        st.markdown(f"**ID:** {st.session_state.user_id}")
        st.markdown("---")
        if st.session_state.role == "Patient":
            page = st.radio("Navigate:", ["🏠 My Dashboard", "📚 Education Hub"])
        elif st.session_state.role == "Doctor":
            page = st.radio("Navigate:", ["🏥 Clinician Dashboard", "📚 Education Hub"])
        else:
            page = st.radio("Navigate:", ["🧠 My Sessions", "📚 Education Hub"])
        st.markdown("---")
        if st.button("🚪 Logout", use_container_width=True):
            st.session_state.logged_in = False
            st.session_state.role      = None
            st.session_state.user_id   = None
            st.rerun()

    if st.session_state.role == "Patient":
        if page == "🏠 My Dashboard":
            patient_dashboard(st.session_state.user_id)
        else:
            education_hub()
    elif st.session_state.role == "Doctor":
        if page == "🏥 Clinician Dashboard":
            clinician_dashboard(st.session_state.user_id)
        else:
            education_hub()
    else:
        if page == "🧠 My Sessions":
            therapist_dashboard(st.session_state.user_id)
        else:
            education_hub()
